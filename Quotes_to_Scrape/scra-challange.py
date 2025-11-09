import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import networkx as nx
import json
from datetime import datetime
import re
from collections import Counter

base_url = "http://quotes.toscrape.com/"


def get_quote_data(quote_tag):
    """Extrait la citation, l'auteur et les tags depuis un bloc <div class='quote'>"""
    text = quote_tag.find('span', class_='text').text.strip()
    author_tag = quote_tag.find('small', class_='author')
    author_name = author_tag.text.strip() if author_tag else ""
    author_url_tag = quote_tag.find('a')
    author_url = urljoin(base_url, author_url_tag['href']) if author_url_tag else ""
    tags = [t.text.strip() for t in quote_tag.find_all('a', class_='tag')]
    return {'text': text, 'author_name': author_name, 'author_url': author_url, 'tags': tags}

def get_author_details(author_url, authors_cache):
    """Récupère biographie, naissance, lieu et date de décès depuis la page auteur"""
    if author_url in authors_cache:
        return authors_cache[author_url]

    try:
        resp = requests.get(author_url)
        if resp.status_code != 200:
            details = {'bio': '', 'born_date': '', 'born_location': '', 'death_date': ''}
        else:
            doc = BeautifulSoup(resp.text, 'html.parser')
            bio = doc.find('div', class_='author-description').text.strip() if doc.find('div', class_='author-description') else ''
            born_date = doc.find('span', class_='author-born-date').text.strip() if doc.find('span', class_='author-born-date') else ''
            born_location = doc.find('span', class_='author-born-location').text.strip() if doc.find('span', class_='author-born-location') else ''
            death_date_tag = doc.find('span', class_='author-death-date')
            death_date = death_date_tag.text.strip() if death_date_tag else ''
            details = {'bio': bio, 'born_date': born_date, 'born_location': born_location, 'death_date': death_date}
        authors_cache[author_url] = details
        return details
    except Exception as e:
        print(f"Erreur sur la page auteur {author_url}: {e}")
        return {'bio': '', 'born_date': '', 'born_location': '', 'death_date': ''}

# Scraping avec cache
all_quotes = []
authors_cache = {}
next_page = base_url

while next_page:
    response = requests.get(next_page)
    doc = BeautifulSoup(response.text, 'html.parser')

    for quote_tag in doc.find_all('div', class_='quote'):
        quote_info = get_quote_data(quote_tag)

        # Récupération infos auteur avec cache
        author_details = get_author_details(quote_info['author_url'], authors_cache)
        quote_info['author_details'] = author_details

        all_quotes.append(quote_info)

    # Pagination
    next_tag = doc.find('li', class_='next')
    next_page = urljoin(base_url, next_tag.find('a')['href']) if next_tag else None

# Construction du graphe
G = nx.DiGraph()

for quote in all_quotes:
    quote_text = quote['text']
    author = quote['author_name']
    tags = quote['tags']

    # Ajouter noeuds et relations
    G.add_node(author, type='author')
    G.add_node(quote_text, type='quote')
    G.add_edge(author, quote_text, relation='wrote')

    for tag in tags:
        G.add_node(tag, type='tag')
        G.add_edge(quote_text, tag, relation='has_tag')

#  Export GraphML et GEXF 
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
graphml_file = f"quotes_graph_{timestamp}.graphml"
gexf_file = f"quotes_graph_{timestamp}.gexf"

nx.write_graphml(G, graphml_file)
nx.write_gexf(G, gexf_file)
print(f"Graphe exporté en GraphML ({graphml_file}) et GEXF ({gexf_file})")

#  Analyse : auteurs les plus cités 
author_counts = Counter([q['author_name'] for q in all_quotes])
most_cited_authors = author_counts.most_common(10)
print("Top 10 auteurs les plus cités :")
for author, count in most_cited_authors:
    print(f"{author}: {count} citations")

# Sauvegarde JSON 
json_file = f"quotes_full_{timestamp}.json"
with open(json_file, 'w', encoding='utf-8') as f:
    json.dump(all_quotes, f, ensure_ascii=False, indent=4)

print(f"Scraping terminé. {len(all_quotes)} citations sauvegardées dans {json_file}.")
