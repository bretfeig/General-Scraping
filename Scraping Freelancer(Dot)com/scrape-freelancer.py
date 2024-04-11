from bs4 import BeautifulSoup
import csv
import requests
import time
import random
from tqdm import tqdm
import os
import unidecode

def normalize_text(text):
    return unidecode.unidecode(text) if text else ''

def scrape_url(url, data_list, error_list, url_counter):
    try:
        response = requests.get(url.strip())
        

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            # Grabbing the fields when data is available
            url = response.request.url
            name = normalize_text(soup.select_one('.Username-displayName h3').text) if soup.select_one('.Username-displayName h3') else None
            title = normalize_text(soup.select_one('.Tagline h2').text) if soup.select_one('.Tagline h2') else None
            rating = soup.select_one('.mat-mdc-tooltip-trigger.fl-bit.ValueBlock').text.strip() if soup.select_one('.mat-mdc-tooltip-trigger.fl-bit.ValueBlock') else None
            earned = soup.select_one('.RightEarningsText div').text if soup.select_one('.RightEarningsText div') else None
            like_accept = soup.select_one('.RightAcceptRateText div').text if soup.select_one('.RightAcceptRateText div') else None
            price = soup.select_one('app-user-profile-summary-information.ng-star-inserted [data-hide-mobile] div.NativeElement').text.strip() if soup.select_one('app-user-profile-summary-information.ng-star-inserted [data-hide-mobile] div.NativeElement') else None
            locations = [location.text for location in soup.select('app-user-profile-summary-information.ng-star-inserted .SupplementaryInfo div')] if soup.select('app-user-profile-summary-information.ng-star-inserted .SupplementaryInfo div') else None
            joined = soup.select_one('fl-grid:nth-of-type(2) fl-text').text if soup.select_one('fl-grid:nth-of-type(2) fl-text') else None
            recommendations = soup.select_one('.RecommendationsText div').text if soup.select_one('.RecommendationsText div') else None
            jobs_completed = soup.select_one('app-user-profile-summary-reputation-item[label="Jobs Completed"] .ReputationItemAmount').text.strip() if soup.select_one('app-user-profile-summary-reputation-item[label="Jobs Completed"] .ReputationItemAmount') else None
            on_time = soup.select_one('app-user-profile-summary-reputation-item[label="On Time"] .ReputationItemAmount').text if soup.select_one('app-user-profile-summary-reputation-item[label="On Time"] .ReputationItemAmount') else None
            on_budget = soup.select_one('app-user-profile-summary-reputation-item[label="On Budget"] .ReputationItemAmount').text if soup.select_one('app-user-profile-summary-reputation-item[label="On Budget"] .ReputationItemAmount') else None
            repeat_hire = soup.select_one('app-user-profile-summary-reputation-item[label="Repeat Hire Rate"] .ReputationItemAmount').text if soup.select_one('app-user-profile-summary-reputation-item[label="Repeat Hire Rate"] .ReputationItemAmount') else None
            summary = normalize_text(soup.select_one('.Content div').text) if soup.select_one('.Content div') else None
            skillset_array = [skill.text for skill in soup.select('.UserProfileSkill-skillName a')] if soup.select('.UserProfileSkill-skillName a') else None
            certificate_array = [certificate.text for certificate in soup.select('.UserProfileExams-name span')] if soup.select('.UserProfileExams-name span') else None
            experience = normalize_text(soup.select_one('app-user-profile-experiences div.CardBody').text) if soup.select_one('app-user-profile-experiences div.CardBody') else None

            # Clean up Skillset Array and Certificate Array to remove white spaces between fields
            if skillset_array:
                skillset_array = [skill.strip() for skill in skillset_array]
            if certificate_array:
                certificate_array = [certificate.strip() for certificate in certificate_array]

            # Adding the scraped data to the data list
            data_list.append([url, name, title, rating, earned, like_accept, price, locations, joined, recommendations, jobs_completed, on_time, on_budget, repeat_hire, skillset_array, certificate_array, experience, summary])

            # Write data to CSV every 100 URLs
            if len(data_list) >= 10:
                print(f'Writing {len(data_list)} records to CSV file after {url_counter[0]} URLs.')
                write_to_csv(data_list)
                data_list.clear()
                url_counter[0] = 0  # Reset the URL counter

            url_counter[0] += 1
        elif response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))  # Default to 5 seconds if no Retry-After header
            print(f'Received 429 status code. Retrying after {retry_after} seconds.')
            time.sleep(retry_after)
            scrape_url(url, data_list, error_list, url_counter)  # Retry the same URL
        else:
            error_message = f'Error scraping {url}: Received status code {response.status_code}'
            print(error_message)
            error_list.append([url.strip(), error_message])

    except Exception as e:
        error_message = f'Error scraping {url}: {str(e)}'
        print(error_message)
        error_list.append([url.strip(), error_message])

    url_counter[0] += 1

if not os.path.exists('freelancer_data.csv'):
    with open('freelancer_data.csv', 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['Url', 'Name', 'Title', 'Rating', 'Earned', 'Like Accept', 'Price', 'Locations', 'Joined', 'Recommendations', 'Jobs Completed', 'On Time', 'On Budget', 'Repeat Hire', 'Skillset', 'Certificate', 'Experience', 'Summary'])

def write_to_csv(data_list):
    with open('freelancer_data.csv', mode='a', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        # Write each row of data
        for row in data_list:
            writer.writerow(row)

with open('links.txt', 'r') as file:
    urls = file.readlines()

total_urls = len(urls)

url_counter = [0]
data_list = []
error_list = []

# Scrape the URLs
for url in tqdm(urls, desc='Scraping URLs', total=total_urls):
    scrape_url(url, data_list, error_list, url_counter)

# Write any remaining data to the CSV file
if data_list:
    print(f'Writing {len(data_list)} records to CSV file after {url_counter[0]} URLs.')
    write_to_csv(data_list)

# Write errors to the errors CSV file
with open('scraping_errors.csv', mode='w', newline='', encoding='utf-8') as csv_error_file:
    csv_error_writer = csv.writer(csv_error_file)
    csv_error_writer.writerow(['URL', 'Error Message'])
    for error in error_list:
        csv_error_writer.writerow(error)