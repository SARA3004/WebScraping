import requests
from bs4 import BeautifulSoup
import csv
import pandas as pd
import os
from urllib.parse import urljoin
import re

url="http://books.toscrape.com/"
response = requests.get(url)
response
page_content = response.text
page_content

doc=BeautifulSoup(page_content, 'html.parser')
doc

def get_book_titles(doc, base_url):
    book_title_tags= doc.find_all('h3')
    book_titles=[]
    for tag in book_title_tags:
       a_tag = tag.find('a')
       title = a_tag['title'].strip()  # titre complet
       url = urljoin(base_url, a_tag['href'])  # URL complète
       book_titles.append({'title': title, 'url': url})
    return book_titles
get_book_titles(doc, url)

def get_book_prices(doc):
    book_price_tags= doc.find_all('p', class_='price_color')
    book_prices=[]
    for tag in book_price_tags:
        price_text = tag.text
        price = float(price_text.replace('£', '').replace('Â', ''))
        book_prices.append(price)
    return book_prices
get_book_prices(doc)    

#books_data = get_book_titles(doc, url)

# 3Notes sur 5
def get_book_ratings(doc):
    star_map = {'One':1, 'Two':2, 'Three':3, 'Four':4, 'Five':5}
    ratings = []
    for tag in doc.find_all('p', class_='star-rating'):
        rating_class = tag['class'][1]
        rating = star_map.get(rating_class, 0)
        ratings.append(rating)
    return ratings
#récupération des infos de la page détail
def get_book_details(book):
    resp = requests.get(book['url'])
    detail_doc = BeautifulSoup(resp.text, 'html.parser')

    # Catégorie principale et secondaire
    breadcrumb = detail_doc.find('ul', class_='breadcrumb').find_all('li')
    main_category = breadcrumb[2].text.strip() if len(breadcrumb)>2 else ""
    sub_category = breadcrumb[3].text.strip() if len(breadcrumb)>3 else ""

    # Description
    desc_tag = detail_doc.find('meta', attrs={'name':'description'})
    description = desc_tag['content'].strip() if desc_tag else ""

    # Stock disponible
    stock_text = detail_doc.find('p', class_='instock availability').text.strip()
    stock_match = re.search(r'\d+', stock_text)
    stock = int(stock_match.group()) if stock_match else 0

    # Image HD
    img_tag = detail_doc.find('div', class_='item active').find('img')
    img_url = urljoin(book['url'], img_tag['src']) if img_tag else ""

    return {
        'main_category': main_category,
        'sub_category': sub_category,
        'description': description,
        'stock': stock,
        'img_url': img_url
    }

# ----- Extraction -----
books = get_book_titles(doc, url)
prices = get_book_prices(doc)
ratings = get_book_ratings(doc)

# Ajouter prix et notes aux livres
for i, book in enumerate(books):
    book['price'] = prices[i]
    book['rating'] = ratings[i]
    details = get_book_details(book)
    book.update(details)

# Convertir en DataFrame
df = pd.DataFrame(books)
df.to_csv('books_full_info.csv', index=False)
print(df.head())




df.to_csv('books_scraped1.csv', index=False)