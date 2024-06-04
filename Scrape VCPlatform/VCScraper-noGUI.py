#VCP NON-GUI - Duplicate check 

import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from google.oauth2 import service_account
import gspread
from googleapiclient.discovery import build
from datetime import datetime
from pyvirtualdisplay import Display
from tqdm import tqdm  # Progress bar library

# Start virtual display
display = Display(visible=0, size=(1920, 1080))
display.start()

# Set up Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = service_account.Credentials.from_service_account_file("credentials.json", scopes=scope)
client = gspread.authorize(creds)

# Open the Google Sheet
sheet = client.open("2024 - Job Tracker /w Sequence ").worksheet('vc_platform')

# Set up Chrome options to disable image loading
chrome_options = Options()
chrome_options.add_argument("--blink-settings=imagesEnabled=false")
chrome_options.add_argument("--headless")  # Run Chrome in headless mode
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Set up the webdriver with the Chrome options
driver = webdriver.Chrome(options=chrome_options)

# Navigate to the directory page
driver.get("https://www.vcplatform.com/directory")

# Function to get the total number of profiles from the element
def get_total_profiles():
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.jetboost-total-results-46m5"))
        )
        total_profiles_element = driver.find_element(By.CSS_SELECTOR, "div.jetboost-total-results-46m5")
        total_profiles = int(total_profiles_element.text.strip())
    except (NoSuchElementException, TimeoutException, ValueError):
        print("Unable to retrieve the total number of profiles. Using a default value of 2000.")
        total_profiles = 2000  # Set a default value if the element is not found or the text format is unexpected
    return total_profiles

# Simplified scroll down function with progress bar
def scroll_down(expected_profiles):
    last_height = driver.execute_script("return document.body.scrollHeight")
    with tqdm(total=expected_profiles, desc="Loading profiles") as pbar:
        loaded_profiles = 0
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Wait to load the page
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            loaded_profiles = len(driver.find_elements(By.CSS_SELECTOR, "div.div-block-11.member-list[data-ix='open-lightbox']"))
            pbar.update(loaded_profiles - pbar.n)  # Update the progress bar

# Get the total number of profiles
total_profiles = get_total_profiles()
print(f"Total profiles expected: {total_profiles}")

# Scroll down to load all profiles
scroll_down(total_profiles)

# Find all the profile cards
profile_cards = driver.find_elements(By.CSS_SELECTOR, "div.div-block-11.member-list[data-ix='open-lightbox']")

# Function to check if the profile link exists in the Google Sheet
def is_profile_link_exists(profile_link):
    profile_links = sheet.col_values(8)  # Assuming 'Profile_Link' is in column H (index 8)
    return profile_link in profile_links

# Iterate over each profile card
for index, card in enumerate(profile_cards, start=1):
    # Scroll the profile card into view before clicking
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)

    # Click on the profile card
    card.click()

    # Wait for the iframe to be present
    try:
        iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe"))
        )
    except TimeoutException:
        print(f"Iframe not found for profile {index}. Skipping...")
        continue

    # Capture the iframe URL
    iframe_url = iframe.get_attribute("src")

    # Check if the profile link already exists in the Google Sheet
    if is_profile_link_exists(iframe_url):
        print(f"Profile {index} already exists in the Google Sheet. Skipping...")
        # Close the iframe
        try:
            close_button = driver.find_element(By.CSS_SELECTOR, "a.close-btn")
            close_button.click()
        except NoSuchElementException:
            print(f"Close button not found for profile {index}")
        time.sleep(1)  # Wait for a short duration to allow the iframe to close
        continue

    # Switch to the iframe
    driver.switch_to.frame(iframe)

    # Wait for 2 seconds after switching to the iframe
    time.sleep(1)

    # Capture the desired information from within the iframe with error handling
    name = ""
    title = ""
    company = ""
    location = ""
    summary = ""
    linkedin_url = ""
    twitter_url = ""

    try:
        name_element = driver.find_element(By.CSS_SELECTOR, "h1")
        name = name_element.text
    except NoSuchElementException:
        print(f"Name not found for profile {index}")

    try:
        title_element = driver.find_element(By.CSS_SELECTOR, "h4")
        title = title_element.text
    except NoSuchElementException:
        print(f"Title not found for profile {index}")

    try:
        company_element = driver.find_element(By.CSS_SELECTOR, "h3")
        company = company_element.text
    except NoSuchElementException:
        print(f"Company not found for profile {index}")

    try:
        location_element = driver.find_element(By.CSS_SELECTOR, "div.text-block-22")
        location = location_element.text
    except NoSuchElementException:
        print(f"Location not found for profile {index}")

    try:
        summary_element = driver.find_element(By.CSS_SELECTOR, "div.text-block-40")
        summary = summary_element.text
    except NoSuchElementException:
        print(f"Summary not found for profile {index}")

    try:
        link_elements = driver.find_elements(By.CSS_SELECTOR, "a")
        for link in link_elements:
            url = link.get_attribute("href")
            if url is not None:
                if "linkedin.com" in url:
                    linkedin_url = url
                elif "twitter.com" in url:
                    twitter_url = url
    except NoSuchElementException:
        print(f"Links not found for profile {index}")

    # Print the captured data to the screen
    print(f"Profile {index}:")
    print(f"Name: {name}")
    print(f"Title: {title}")
    print(f"Company: {company}")
    print(f"Location: {location}")
    print(f"Summary: {summary}")
    print(f"LinkedIn URL: {linkedin_url}")
    print(f"Twitter URL: {twitter_url}")
    print(f"Iframe URL: {iframe_url}")
    print("---")

    # Append the captured data to the Google Sheet
    row = [name, title, company, location, summary, linkedin_url, twitter_url, iframe_url]
    sheet.append_row(row)

    # Switch back to the main content
    driver.switch_to.default_content()

    # Click the close button to close the iframe
    try:
        close_button = driver.find_element(By.CSS_SELECTOR, "a.close-btn")
        close_button.click()
    except NoSuchElementException:
        print(f"Close button not found for profile {index}")

    # Wait for a short duration to allow the iframe to close
    time.sleep(1)  # Adjust the sleep time as needed

# Close the webdriver
driver.quit()

# Stop the virtual display
display.stop()
