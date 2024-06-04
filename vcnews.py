import requests
from bs4 import BeautifulSoup
import re
import time
import random
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime

# Set up Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)  #change to where your credential file is
client = gspread.authorize(creds)

# Open the Google Sheet
sheet = client.open("2024 - Job Tracker /w Sequence ").worksheet('vc_platform') # Change to the location you want the output

def scrape_vcnews():
    url = "https://vcnewsdaily.com/"
    try:
        response = requests.get(url, timeout=10)  # 10 seconds timeout
        response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')

    articles = soup.find_all('div', class_='article-box bg-light px-2 py-3')

    data = []
    for article in articles:
        a_tag = article.find('a', class_='d-block')
        name = a_tag.find('h5').text
        trimmed_name = re.search(r'([^\s]+)', name).group(0)  # Trimming the name selector using regex
        highlights = re.search(r'\s(.*)', name).group(1)  # Duplicating the name selector as highlights and trimming using regex
        link = a_tag['href']
        print(name)
        # Make a second request to the URL captured in "link"
        company_response = requests.get(link)
        company_response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
        company_soup = BeautifulSoup(company_response.text, 'html.parser')

        # Scrape the company URL
        company_url_tag = company_soup.find('div', class_='fullArticle').find('a')
        company_url = company_url_tag['href'] if company_url_tag else None

        # Make a third request to the company URL
        company_page_response = requests.get(company_url, timeout=10)  # 10 seconds timeout
        company_page_response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
        company_page_soup = BeautifulSoup(company_page_response.text, 'html.parser')

        # Extracting the fields
        fields = company_page_soup.find('h5', string='Key Contact').find_next('div', class_='row').find_all('div', class_='col-md-4')

        # Extracting the data from the fields
        founder_name = ''
        founder_title = ''
        founder_email = ''
        if len(fields) >= 1:
            founder_name = fields[0].get_text(separator=' ', strip=True)  # Retrieve the entire founder name
            if founder_name.lower().startswith('name'):
                founder_name = founder_name[len('name'):].strip()  # Remove the word "Name" from the founder name and strip whitespaces
        if len(fields) >= 2:
            if len(fields) >= 2:
                founder_title_field = fields[1]
                if founder_title_field:
                    founder_title = founder_title_field.get_text(separator=' ', strip=True).split(' ')[1]
        if len(fields) >= 3:
            try:
                founder_email_field = fields[2]
                if founder_email_field:
                    founder_email = founder_email_field.get_text(separator=' ', strip=True).split(' ')[1]
            except IndexError:
                founder_email = 'Email not found'

        # Extracting additional data points
        company_web = company_page_soup.select_one('a.text-border-botton-color')['href'] if company_page_soup.select_one('a.text-border-botton-color') else ''

        # Find the last tbody element
        last_tbody = company_page_soup.find_all('tbody')[-1] if company_page_soup.find_all('tbody') else None

        funding_date = last_tbody.select_one('td:nth-of-type(1) a').text.strip() if last_tbody and last_tbody.select_one('td:nth-of-type(1) a') else ''
        funding_amount = last_tbody.select_one('td:nth-of-type(2) a').text.strip() if last_tbody and last_tbody.select_one('td:nth-of-type(2) a') else ''
        funding_type = last_tbody.select_one('td:nth-of-type(3) a').text.strip() if last_tbody and last_tbody.select_one('td:nth-of-type(3) a') else ''
        investors = ', '.join([span.text.strip() for span in last_tbody.select('span')]) if last_tbody else ''

        # Add all data points to the data dictionary
        data.append({'name': trimmed_name, 'highlights': highlights, 'link': link, 'company_url': company_url, 'founder_name': founder_name, 'founder_title': founder_title, 'founder_email': founder_email, 'company_web': company_web, 'funding_date': funding_date, 'funding_amount': funding_amount, 'funding_type': funding_type, 'investors': investors})
    return data

data = scrape_vcnews()

# Check for duplicates and update the Google Sheet
current_data = sheet.get_all_records()
updated_data = []
for item in data:
    duplicate = False
    for row in current_data:
        if item['company_url'] == row['company_url']:
            duplicate = True
            break
    if not duplicate:
        updated_data.append(item)

# Append new data to the Google Sheet
for item in updated_data:
    item['date'] = datetime.now().strftime("%Y-%m-%d")  # Add the current date to the item
    sheet.append_row(list(item.values()))

print("Data has been updated in the Google Sheet.")