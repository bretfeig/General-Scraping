import requests
from bs4 import BeautifulSoup
import csv
import warnings
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

warnings.filterwarnings("ignore", category=FutureWarning)

# List of company types
company_types = [
    '3d-printing-companies', '3pl-third-party-logistics-companies', 'adtech-companies',
    'aerospace-companies', 'agency-companies', 'agriculture-companies',
    'analytics-industry-companies', 'angel-vcfirm-companies', 'app-development-companies',
    'appliances-companies', 'artificial-intelligence-companies', 'automation-companies',
    'automotive-companies', 'beauty-companies', 'big-data-companies',
    'big-data-analytics-companies', 'biotech-companies', 'blockchain-companies',
    'business-intelligence-industry-companies', 'cannabis-companies', 'chemical-companies',
    'cloud-companies', 'co-working-space-incubator-companies', 'computer-vision-companies',
    'consulting-companies', 'consumer-web-companies', 'conversational-ai-companies',
    'coupons-companies', 'cryptocurrency-companies', 'cybersecurity-companies',
    'data-privacy-companies', 'database-companies', 'defense-companies', 'design-companies',
    'digital-media-companies', 'ecommerce-companies', 'edtech-companies', 'energy-companies',
    'enterprise-web-companies', 'esports-companies', 'events-companies', 'fashion-companies',
    'financial-services-companies', 'fintech-companies', 'fitness-companies', 'food-companies',
    'gaming-companies', 'generative-ai-companies', 'greentech-companies',
    'hardware-industry-companies', 'healthtech-companies', 'hospitality-companies',
    'hr-tech-companies', 'industrial-companies', 'information-technology-companies',
    'infrastructure-as-a-service-iaas-companies', 'insurance-companies', 'iot-companies',
    'kids-family-companies', 'legal-tech-companies', 'logistics-companies',
    'machine-learning-industry-companies', 'manufacturing-companies', 'marketing-tech-companies',
    'metaverse-companies', 'mobile-companies', 'music-companies', 'nanotechnology-companies',
    'natural-language-processing-companies', 'news-entertainment-companies', 'nft-companies',
    'on-demand-companies', 'other-industry-companies', 'payments-companies', 'pet-companies',
    'pharmaceutical-companies', 'productivity-companies', 'professional-services-companies',
    'proptech-companies', 'quantum-computing-companies', 'real-estate-companies',
    'renewable-energy-companies', 'retail-companies', 'robotics-companies',
    'sales-industry-companies', 'security-industry-companies', 'semiconductor-companies',
    'seo-companies', 'sharing-economy-companies', 'social-impact-companies',
    'social-media-companies', 'software-companies', 'solar-companies', 'sports-companies',
    'telehealth-companies', 'transportation-companies', 'travel-companies',
    'utilities-companies', 'virtual-reality-companies', 'wearables-companies', 'web3-companies'
]

def make_request(url, max_retries=5, delay=5):
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
            return response
        except requests.exceptions.RequestException as e:
            if e.response is not None and e.response.status_code >= 400:
                print(f"Received {e.response.status_code} status code. Retrying in {delay} seconds...")
                time.sleep(delay)
                retries += 1
                delay *= 2  # Double the delay for each retry
            else:
                raise e
    print(f"Failed to make a successful request after {max_retries} retries. Skipping...")
    return None

def scrape_company(company_url):
    try:
        company_response = make_request(company_url)
        if company_response is None:
            return None, None, None, None, None, None, None, None

        company_soup = BeautifulSoup(company_response.text, 'html.parser')

        # Extract total employees
        employees_element = company_soup.select_one('span:-soup-contains("Total Employees")')
        employees = employees_element.text.strip().split()[0] if employees_element else None

        # Extract website
        website_element = company_soup.select_one('a[href]:-soup-contains("View Website")')
        website = website_element['href'] if website_element else None

        # Extract location
        location_element = company_soup.select_one('div.ms-sm.fw-medium')
        location = location_element.text.strip() if location_element else None

        # Extract jobs
        jobs_element = company_soup.select_one('.nav-tabs li:-soup-contains("Jobs")')
        jobs = jobs_element.text.strip() if jobs_element else None

        # Extract hybrid icon
        hybrid_icon_element = company_soup.select_one('i.fa.fa-house-building + span')
        hybrid_icon = hybrid_icon_element.text.strip() if hybrid_icon_element else None

        # Extract hybrid timing
        hybrid_timing_element = company_soup.select_one('div.office-timing')
        hybrid_timing = ' '.join(hybrid_timing_element.text.strip().split()) if hybrid_timing_element else None

        # Extract year founded
        year_founded_element = company_soup.select_one('div.d-flex.align-items-center span.font-barlow:-soup-contains("Year Founded")')
        if year_founded_element:
            year_founded_text = year_founded_element.text.strip()
            year_founded_match = re.search(r'\b(\d{4})\b', year_founded_text)
            year_founded = year_founded_match.group(1) if year_founded_match else None
        else:
            year_founded = None

        # Extract industry types
        industry_elements = company_soup.select('div.tag-hover.py-xs.px-sm.d-inline-block.rounded-3.fs-sm.text-nowrap.bg-pretty-blue-highlight.industry.bg-gray-01-highlight-hover')
        industries = ', '.join([industry.text.strip() for industry in industry_elements])

        return employees, website, location, jobs, hybrid_icon, hybrid_timing, year_founded, industries

    except (requests.exceptions.RequestException, requests.exceptions.HTTPError):
        return None, None, None, None, None, None, None, None

# Open a CSV file for writing
with open('company_data.csv', 'a', newline='', encoding='utf-8') as csvfile:
    # Create a CSV writer
    csv_writer = csv.writer(csvfile)

    # Write the header row
    if csvfile.tell() == 0:
        csv_writer.writerow(['Company Name', 'Company URL', 'Total Employees', 'Website', 'Location', 'Jobs', 'Hybrid Icon', 'Hybrid Timing', 'Company Type', 'Year Founded', 'Industries'])

    # Iterate over each company type
    for company_type in company_types:
        page = 1
        while True:
            # Print the current company type and page number being scraped
            print(f"Scraping company type: {company_type}, Page: {page}")

            # Make a request to the specified URL with the current company type and page number
            url = f"https://builtin.com/companies/type/{company_type}?country=USA&page={page}"
            response = make_request(url)

            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all company card elements
            company_cards = soup.select('#main-container div.company-unbounded-responsive')

            # If no company cards are found, break the loop and move to the next company type
            if not company_cards:
                break

            # Create a thread pool executor with the desired number of threads
            with ThreadPoolExecutor(max_workers=20) as executor:
                # Submit scraping tasks for each company URL
                futures = []
                for card in company_cards:
                    company_name = card.select_one('.company-title-clamp').text.strip()
                    view_profile_button = card.select_one('a[data-track-id="photo"]')
                    if view_profile_button:
                        company_url = "https://builtin.com" + view_profile_button['href']
                        future = executor.submit(scrape_company, company_url)
                        futures.append((company_name, company_url, future))
                    else:
                        csv_writer.writerow([company_name, None, None, None, None, None, None, None, company_type, None, None])
                        print("Company Name:", company_name)
                        print("Company URL: None")
                        print("Total Employees: None")
                        print("Website: None")
                        print("Location: None")
                        print("Jobs: None")
                        print("Hybrid Icon: None")
                        print("Hybrid Timing: None")
                        print("Company Type:", company_type)
                        print("Year Founded: None")
                        print("Industries: None")
                        print("---")

                # Process the results as they become available
                for company_name, company_url, future in futures:
                    employees, website, location, jobs, hybrid_icon, hybrid_timing, year_founded, industries = future.result()
                    csv_writer.writerow([company_name, company_url, employees, website, location, jobs, hybrid_icon, hybrid_timing, company_type, year_founded, industries])
                    print("Company Name:", company_name)
                    print("Company URL:", company_url)
                    print("Total Employees:", employees)
                    print("Website:", website)
                    print("Location:", location)
                    print("Jobs:", jobs)
                    print("Hybrid Icon:", hybrid_icon)
                    print("Hybrid Timing:", hybrid_timing)
                    print("Company Type:", company_type)
                    print("Year Founded:", year_founded)
                    print("Industries:", industries)
                    print("---")

            # Increment the page number
            page += 1

print("Data has been exported to company_data.csv.")