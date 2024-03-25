import requests
from bs4 import BeautifulSoup
import csv
import re
from google.oauth2 import service_account
from googleapiclient.discovery import build
from urllib.parse import urljoin

# API credentials & spreadsheet details
SERVICE_ACCOUNT_FILE = 'auth.json'  # Replace with the path to your service account credentials file
SPREADSHEET_ID = '1NxhQ6ct9p5PkWc-r09wk5FgVS2IB8ZwqUpSdlGeKXQU'  # Replace with your actual spreadsheet ID

# Authenticate API access
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=['https://www.googleapis.com/auth/spreadsheets'])

service = build('sheets', 'v4', credentials=credentials)

# Set the base URL
base_url = "https://www.dice.com/jobs/q-recruiter-jobs?page={}"

# Create a set to store unique job links
unique_job_links = set()

# Create a list to store the extracted job details
job_details = []

# Function to scrape job details from a given job link
def scrape_job_details(job_link):
    # Send a GET request to the job link with headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(job_link, headers=headers)

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")

    # Check if the job link contains the word "redirect"
    if "apply-redirect" in job_link:
        return None

    # Parse the desired fields from the HTML
    job_title = soup.find("h1", {"data-cy": "jobTitle"}).text.strip() if soup.find("h1", {"data-cy": "jobTitle"}) else "N/A"
    job_location = soup.find("li", {"data-cy": "location"}).text.strip() if soup.find("li", {"data-cy": "location"}) else "N/A"
    company_name = soup.find("a", {"data-cy": "companyNameLink"}).text.strip() if soup.find("a", {"data-cy": "companyNameLink"}) else "N/A"
    posted_date = soup.find("li", {"data-cy": "postedDate"}).text.strip() if soup.find("li", {"data-cy": "postedDate"}) else "N/A"
    job_description = soup.find("div", {"data-cy": "jobDescription"}).text.strip() if soup.find("div", {"data-cy": "jobDescription"}) else "N/A"
    skills_container = soup.find("div", {"data-cy": "skillsList"})
    skills = [skill_span.text.strip() for skill_span in skills_container.find_all("span")] if skills_container else []
    location = soup.select_one("div[data-cy='locationDetails'] span").text.strip() if soup.select_one("div[data-cy='locationDetails'] span") else "N/A"
    pay_details = soup.select_one("div[data-cy='payDetails'] span").text.strip() if soup.select_one("div[data-cy='payDetails'] span") else "N/A"
    employment_details = [detail_span.text.strip() for detail_span in soup.find_all("span", {"id": lambda x: x and x.startswith('employmentDetailChip:')})] if soup.find_all("span", {"id": lambda x: x and x.startswith('employmentDetailChip:')}) else []
    poster_name = soup.find("p", class_="font-bold").text.strip() if soup.find("p", class_="font-bold") else "N/A"
    email_pattern = re.compile(r'applicationDetail":{"email":"(.*?)"')
    poster_email_match = email_pattern.search(str(soup))
    poster_email = poster_email_match.group(1) if poster_email_match else "N/A"

    # Store the job details in a dictionary
    job_detail = {
        "Job Title": job_title,
        "Job Location": job_location,
        "Company Name": company_name,
        "Posted Date": posted_date,
        "Job Description": job_description,
        "Skills": skills,
        "Location": location,
        "Pay Details": pay_details,
        "Employment Details": employment_details,
        "Poster Name": poster_name,
        "Poster Email": poster_email
    }

    return job_detail

# Send a GET request to the base URL with headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
response = requests.get(base_url.format(1), headers=headers)

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(response.content, "html.parser")

# Find the maximum page range
pagination_span = soup.select_one("nav > div > span:nth-child(2)")
max_pages = int(pagination_span.text.split()[-1])

# Scrape job links from each page
for page in range(1, max_pages + 1):
    # Send a GET request to the page URL with headers
    page_url = base_url.format(page)
    response = requests.get(page_url, headers=headers)

       # Print scraping page X of max_pages
    print(f"Scraping page {page} of {max_pages}")

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")

    # Find all the job cards on the page
    job_cards = soup.find_all("dhi-job-search-job-card")

    # Iterate over the job cards and extract the job links
    job_links = [job_card.find("a", role="link")["href"] for job_card in job_cards]

    # Add the job links to the set of unique job links
    unique_job_links.update(job_links)

# Scrape job details from each unique job link
for job_link in unique_job_links:

    # Print the URL before scraping
    print(f"Scraping URL: {job_link}")

    job_detail = scrape_job_details(job_link)
    if job_detail:
        job_details.append(job_detail)

# Check if there is any data to push
if job_details:
    # Prepare the data to be pushed to the Google Sheet
    data_to_push = []
    for job_detail in job_details:
    # Convert each value to a string before appending to the list
     values = [str(value) for value in job_detail.values()]
     data_to_push.append(values)

# Push the data to the Google Sheet
body = {'values': data_to_push}
result = service.spreadsheets().values().append(
    spreadsheetId=SPREADSHEET_ID, range='Sheet1!A1', valueInputOption='USER_ENTERED', body=body).execute()

print('Data pushed to Google Sheet')

