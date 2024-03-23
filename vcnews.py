import requests
from bs4 import BeautifulSoup
import re
import pyperclip

def scrape_vcnews():
    url = "https://vcnewsdaily.com/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    articles = soup.find_all('div', class_='article-box bg-light px-2 py-3')

    data = []
    for article in articles:
        a_tag = article.find('a', class_='d-block')
        name = a_tag.find('h5').text
        trimmed_name = re.search(r'([^\s]+)', name).group(0)  # Trimming the name selector using regex
        highlights = re.search(r'\s(.*)', name).group(1)  # Duplicating the name selector as highlights and trimming using regex
        link = a_tag['href']
        data.append({'name': trimmed_name, 'highlights': highlights, 'link': link})  # Adding highlights to the data dictionary
    
    return data

data = scrape_vcnews()

# Format the data for clipboard
clipboard_data = ""
for item in data:
    clipboard_data += f"{item['name']}\t{item['highlights']}\t{item['link']}\n"

# Copy the data to clipboard
pyperclip.copy(clipboard_data)
print("Data has been copied to the clipboard. You can now paste it into Google Sheets.")
