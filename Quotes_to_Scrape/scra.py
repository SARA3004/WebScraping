import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
from datetime import datetime

url = "http://quotes.toscrape.com/"


def get_quote_data(quote_tag):
    """Extrait la citation, l'auteur et les tags depuis un bloc <div class='quote'>"""
    text = quote_tag.find('span', class_='text').text.strip()
    author_tag = quote_tag.find('small', class_='author')
    author_name = author_tag.text.strip() if author_tag else ""
    author_url_tag = quote_tag.find('a')
    author_url = urljoin(url, author_url_tag['href']) if author_url_tag else ""
    tags = [t.text.strip() for t in quote_tag.find_all('a', class_='tag')]
    return {'text': text, 'author_name': author_name, 'author_url': author_url, 'tags': tags}

def get_author_details(author_url):
    """Récupère biographie, naissance, lieu et date de décès depuis la page auteur"""
    try:
        resp = requests.get(author_url)
        if resp.status_code != 200:
            return {'bio': '', 'born_date': '', 'born_location': '', 'death_date': ''}
        doc = BeautifulSoup(resp.text, 'html.parser')
        bio = doc.find('div', class_='author-description').text.strip() if doc.find('div', class_='author-description') else ''
        born_date = doc.find('span', class_='author-born-date').text.strip() if doc.find('span', class_='author-born-date') else ''
        born_location = doc.find('span', class_='author-born-location').text.strip() if doc.find('span', class_='author-born-location') else ''
        death_date_tag = doc.find('span', class_='author-death-date')
        death_date = death_date_tag.text.strip() if death_date_tag else ''
        return {'bio': bio, 'born_date': born_date, 'born_location': born_location, 'death_date': death_date}
    except Exception as e:
        print(f"Erreur sur la page auteur {author_url}: {e}")
        return {'bio': '', 'born_date': '', 'born_location': '', 'death_date': ''}

# Scraping toutes les pages
all_quotes = []
authors_cache = {}  # pour éviter de scraper plusieurs fois le même auteur
next_page = url

while next_page:
    response = requests.get(next_page)
    doc = BeautifulSoup(response.text, 'html.parser')

    for quote_tag in doc.find_all('div', class_='quote'):
        quote_info = get_quote_data(quote_tag)

        # Si l'auteur n'est pas déjà scrappé
        if quote_info['author_name'] not in authors_cache and quote_info['author_url']:
            author_details = get_author_details(quote_info['author_url'])
            authors_cache[quote_info['author_name']] = author_details
        else:
            author_details = authors_cache.get(quote_info['author_name'], {})

        # Créer structure hiérarchique Citation → Auteur → Tags
        quote_info['author_details'] = author_details

        all_quotes.append(quote_info)

    # Pagination
    next_tag = doc.find('li', class_='next')
    if next_tag:
        next_page = urljoin(url, next_tag.find('a')['href'])
    else:
        next_page = None

# Sauvegarde JSON 
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"quotes_scraped_{timestamp}.json"

with open(filename, 'w', encoding='utf-8') as f:
    json.dump(all_quotes, f, ensure_ascii=False, indent=4)

print(f"Scraping terminé. {len(all_quotes)} citations sauvegardées dans {filename}.")
