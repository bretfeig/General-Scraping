from zenrows import ZenRowsClient
import random
import time
from bs4 import BeautifulSoup
import pandas as pd
import os
import datetime
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from multiprocessing.pool import ThreadPool  # Import ThreadPool for multithreading
import httpx


# API credentials & spreadsheet details
SERVICE_ACCOUNT_FILE = '/mnt/c/output/credentials.json'  # Replace with the path to your service account credentials file
SPREADSHEET_ID = '1T8AL0VQlb4-83ZzlSYwkS13or3eX1AqCcuFdd1gWqTA'  # Replace with your actual spreadsheet ID

# Authenticate API access
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=['https://www.googleapis.com/auth/spreadsheets'])

service = build('sheets', 'v4', credentials=credentials)

# Initialize loop counter and data list
loop_counter = 0
accumulated_data = []

# Function to extract data from each URL and write to a CSV file
def extract_data(url):
    try:
        client = ZenRowsClient("INSERT-API-KEY-HERE", concurrency=10, retries=1)
        response = client.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Function to extract text or return empty string if element is not found
        def extract_or_empty(selector):
            element = soup.select_one(selector)
            return element.text if element else ''

        # Extracting data bits
        first_name = extract_or_empty('span.user-name-first')
        maiden_name = extract_or_empty('span.user-name-maiden')
        last_name = extract_or_empty('span.user-name-last')
        creds = extract_or_empty('span.user-name-credentials')
        ctype = extract_or_empty('a.profile-head-subtitle')
        location = extract_or_empty('span[itemprop="addressLocality"]')
        office_address = extract_or_empty('span.black.profile-contact-labels-wrap')
        phone = phone = "'" + extract_or_empty('div.profile-contact-labels-wrap span.black') + "'"
        job_title = extract_or_empty('p[itemprop="jobTitle"]')
        summary = extract_or_empty('div.profile-summary-content')

        # Extracting Education data
        education_info = soup.find('section', class_='education-info')
        education_items = education_info.find_all('li', itemprop='alumniOf') if education_info else []
        education_data = '\n'.join([f"{item.find('span', itemprop='name').text} ({item.find('span', class_='br').text})" for item in education_items])

        # Extracting Certification data
        certification_info = soup.find('section', class_='certification-info')
        certification_items = certification_info.find_all('li', class_='show_more_hidden') if certification_info else []
        certification_data = '\n'.join([f"{item.find('span', class_='black').text} ({item.find('span', class_='br').text})" for item in certification_items])

        # Creating the data dictionary
        data = {
            'First Name': [first_name],
            'Maiden Name': [maiden_name],
            'Last Name': [last_name],
            'Credentials': [creds],
            'Type': [ctype],
            'Location': [location],
            'Office Address': [office_address],
            'Phone': [phone],
            'Job Title': [job_title],
            'Summary': [summary],
            'Education': [education_data],  # Concatenated education data
            'Certification': [certification_data],  # Concatenated certification data
            'Page URL': [url]  # Use the provided URL
        }

        # Print the data dictionary to the screen
        print("Data Dictionary:")
        print(data)

          # Creating a DataFrame
        # Creating a DataFrame
        df = pd.DataFrame(data)

        # Append the data to the accumulated data list
        accumulated_data.append(list(map(lambda x: x[0] if x else '', data.values())))

        # Increment the loop counter
        global loop_counter
        loop_counter += 1

        # Push the accumulated data to the Google Sheet every 50 loops
        if loop_counter % 50 == 0:
            result = service.spreadsheets().values().append(
                spreadsheetId=SPREADSHEET_ID,
                range='doxy!A1',
                valueInputOption='USER_ENTERED',
                body={'values': accumulated_data}
            ).execute()
            print('Data pushed to Google Sheet')
            # Clear the accumulated data list
            accumulated_data.clear()

    except Exception as e:
        print(f"An error occurred while processing URL: {url}. Error: {e}")

    # Print the current URL to the screen
    print(f"Processed URL: {url}")

# Fetch existing URLs from the Google Sheet
def fetch_existing_urls():
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='doxy!M2:M'
    ).execute()
    return [row[0] for row in result.get('values', [])]

# Read URLs from the file and extract data
with open(r'/mnt/c/output/publicprofiles.txt', 'r') as file:
    urls = file.readlines()
    existing_urls = fetch_existing_urls()  # Fetch existing URLs
    for url in urls:
        url = url.strip()
        if url in existing_urls:  # Skip URL if it's already in the Google Sheet
            print(f"Skipped URL: {url} - Already scraped")
            continue  # Skip processing the URL
    with ThreadPool(15) as pool:
        pool.map(extract_data, urls)