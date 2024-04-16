import csv
import requests
from bs4 import BeautifulSoup

# Open the file containing the URLs
with open("jobsage.txt", "r") as f:
    urls = [line.strip() for line in f]

# Initialize an empty list to hold the data
data = []

# Define the list of filtered titles
filtered_titles = ["people", "talent", "human", "chro", "HR", "recruitment", "recruiting"]

# Loop through each URL
for url in urls:
    try:
        # Make a request to the website
        r = requests.get(url)
        r.raise_for_status()

        # Parse the HTML
        soup = BeautifulSoup(r.text, "html.parser")

        # Get the company name
        company_name = soup.find("h1").text.strip()

        # Find all the cards
        cards = soup.find_all("div", class_="col")

        # Loop through each card
        for card in cards:
            # Try to get the name, title, and LinkedIn URL
            try:
                name = card.find("h3", class_="card-text company-name").text.strip()
                title = card.find("p").text.strip()
                linkedin_url = card.find("a", href=lambda x: x and "linkedin" in x)["href"]
            except Exception:
                # If any of these are missing, continue to the next card
                continue

            # Check if the title contains one of the filtered words
            if any(word in title.lower() for word in filtered_titles):
                # Add the data to the list
                data.append({
                    "name": name,
                    "title": title,
                    "linkedin_url": linkedin_url
                })

        # Write the data to a CSV file
        with open("output.csv", "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Company Name", "Name", "Title", "LinkedIn"])
            for d in data:
                writer.writerow({
                    "Company Name": company_name,
                    "Name": d["name"],
                    "Title": d["title"],
                    "LinkedIn": d["linkedin_url"]
                })

        # Clear the data list for the next iteration
        data.clear()

    except requests.exceptions.RequestException as e:
        # Print the error message
        print(f"Error {e.response.status_code}: {e.message} for {url}")