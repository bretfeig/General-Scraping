import csv
import pandas as pd
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Specify the base URL
base_url = 'https://builtin.com/jobs/hr?daysSinceUpdated=1&page='

# Define the output file path
output_file_path = 'G:/My Drive/builtin/todaysjobs.tsv'

# Set headers to mimic a browser request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0;Win64) AppleWebkit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

# Send a GET request to the first page
first_page_response = requests.get(base_url + '1', headers=headers)
if first_page_response.status_code == 200:
    first_page_soup = BeautifulSoup(first_page_response.content, 'html.parser')

    # Find all the pagination links
    pagination_links = first_page_soup.find_all('a', href=True)

    # Extract the highest page number from the href attribute
    highest_page = max([int(link['href'].split('=')[-1]) for link in pagination_links if 'page=' in link['href']])

    # Loop through the range of pages
    for page in range(1, highest_page + 1):
        # Construct the URL for each page
        url = base_url + str(page)

        # Send a GET request to the URL with a delay
        response = requests.get(url, headers=headers)
        time.sleep(2)  # Delay for 2 seconds between requests

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find the job cards
            job_cards = soup.find_all('div', {'data-id': 'job-card'})

            # Append the data to the CSV file
            with open(output_file_path, 'a', newline='', encoding='utf-8') as csvfile:  # Open the file in append mode
                writer = csv.writer(csvfile, delimiter='\t')

                # Extract the data from each job card and write to the CSV file
                for card in job_cards:
                    company_name = card.find('div', {'data-id': 'company-title'}).text.strip()
                    job_title = card.find('a', {'id': 'job-card-alias'}).text.strip()
                    apply_link = urljoin(base_url, card.find('a', {'data-id': 'view-job-button'})['href'])

                    # Extracting additional information
                    date_posted = card.find('i', {'class': 'fa-clock'})
                    date_posted = date_posted.find_next('span', {'class': 'font-barlow text-gray-03'}).text.strip() if date_posted else 'N/A'

                    location = card.find('i', {'class': 'fa-location-dot'})
                    location = location.find_next('span', {'class': 'font-barlow text-gray-03'}).text.strip() if location else 'N/A'

                    work_type = card.find('i', {'class': 'fa-house-building'})
                    work_type = work_type.find_next('span', {'class': 'font-barlow text-gray-03'}).text.strip() if work_type else 'N/A'

                    employees = card.find('i', {'class': 'fa-user-group'})
                    employees = employees.find_next('span', {'class': 'font-barlow text-gray-03'}).text.strip() if employees else 'N/A'

                    salary = card.find('i', {'class': 'fa-sack-dollar'})
                    salary = salary.find_next('span', {'class': 'font-barlow text-gray-03'}).text.strip() if salary else 'N/A'

                    experience = card.find('i', {'class': 'fa-trophy'})
                    experience = experience.find_next('span', {'class': 'font-barlow text-gray-03'}).text.strip() if experience else 'N/A'

                    # Write the data to the CSV file
                    writer.writerow([company_name, job_title, apply_link, date_posted, location, work_type, employees, salary, experience])
                    print(f"Company Name: {company_name}\tJob Title: {job_title}\tApply Link: {apply_link}\tDate Posted: {date_posted}\tLocation: {location}\tWork Type: {work_type}\tEmployees #: {employees}\tSalary: {salary}\tYears of Experience: {experience}")
        else:
            print(f'Failed to retrieve the website for page {page}')

    print('Data extraction complete. The job data has been saved to', output_file_path)
else:
    print('Failed to retrieve the first page')


# Function to remove duplicates based on the "apply_link" column
def remove_duplicates_from_csv(csv_file_path):
    # Read the CSV file into a DataFrame
    df = pd.read_csv(csv_file_path, sep='\t')

    # Remove duplicates based on the "Apply Link" column
    df.drop_duplicates(subset='Apply Link', keep='first', inplace=True)

    # Save the updated data to the CSV file
    df.to_csv(csv_file_path, index=False, sep='\t', encoding='utf-8')
    print('Duplicates removed. The updated data has been saved to', csv_file_path)

# Call the function to remove duplicates from the output file
remove_duplicates_from_csv(output_file_path)




