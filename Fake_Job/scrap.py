import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
from datetime import datetime
from urllib.parse import urlparse
import re
import pandas as pd

BASE_URL = "https://realpython.github.io/fake-jobs/"


def get_job_cards(doc):
    """Récupère tous les blocs d'offres sur la page"""
    return doc.find_all('div', class_='card-content')

def parse_job_card(card):
    #xtrait les infos d'une offre
    title = card.find('h2', class_='title').text.strip() if card.find('h2', class_='title') else ""
    company = card.find('h3', class_='company').text.strip() if card.find('h3', class_='company') else ""
    location = card.find('p', class_='location').text.strip() if card.find('p', class_='location') else ""
    date_posted = card.find('time').text.strip() if card.find('time') else ""
    apply_tag = card.find('a', string='Apply')
    apply_url = urljoin(BASE_URL, apply_tag['href']) if apply_tag else ""
    description_tag = card.find('p', class_='description')
    description = description_tag.text.strip() if description_tag else ""
    return {
        'title': title,
        'company': company,
        'location': location,
        'date_posted': date_posted,
        'apply_url': apply_url,
        'description': description
    }

# Scraping avec filtre "Python" 
all_jobs = []
next_page = BASE_URL

while next_page:
    resp = requests.get(next_page)
    if resp.status_code != 200:
        break
    doc = BeautifulSoup(resp.text, 'html.parser')
    cards = get_job_cards(doc)

    for card in cards:
        job = parse_job_card(card)
        # Filtre uniquement les jobs contenant "Python"
        if "python" in job['title'].lower() or "python" in job['description'].lower():
            all_jobs.append(job)

    # Pagination : chercher <li class="next">
    next_tag = doc.find('li', class_='next')
    next_page = urljoin(BASE_URL, next_tag.find('a')['href']) if next_tag else None
# Sauvegarde JSON avec timestamp
"""timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"python_jobs_{timestamp}.json"
with open(filename, 'w', encoding='utf-8') as f:
    json.dump(all_jobs, f, ensure_ascii=False, indent=4)

print(f"Scraping terminé. {len(all_jobs)} offres contenant 'Python' sauvegardées dans {filename}.")"""

#  Nettoyer et standardiser les dates
def standardize_date(date_str):
   
    #Convertit les dates en format YYYY-MM-DD si possible.
    if not date_str:
        return None
    # regex simple pour YYYY-MM-DD
    match = re.search(r'\d{4}-\d{2}-\d{2}', date_str)
    return match.group(0) if match else None

for job in all_jobs:
    job['date_posted'] = standardize_date(job['date_posted'])

# 2-Classer par type de contrat et localisation 
def detect_contract_type(description):
    desc = description.lower()
    if 'full-time' in desc:
        return 'Full-Time'
    elif 'part-time' in desc:
        return 'Part-Time'
    elif 'contract' in desc:
        return 'Contract'
    else:
        return 'Unknown'

for job in all_jobs:
    job['contract_type'] = detect_contract_type(job['description'])
    job['location'] = job.get('location', 'Unknown')

# 3) Extraire et valider les URLs d’application 
def validate_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

for job in all_jobs:
    job['apply_url'] = job.get('apply_url', '')
    if not validate_url(job['apply_url']):
        job['apply_url'] = None

#4) Détection de doublons
# Doublons basés sur (title + company + location)
unique_jobs = []
seen = set()
for job in all_jobs:
    key = (job['title'], job['company'], job['location'])
    if key not in seen:
        seen.add(key)
        unique_jobs.append(job)
all_jobs = unique_jobs

#  5) Générer des statistiques par ville et type de contrat 
df = pd.DataFrame(all_jobs)
print("Statistiques par ville :")
print(df['location'].value_counts())
print("\nStatistiques par type de contrat :")
print(df['contract_type'].value_counts())

# 6) Sauvegarder en CSV avec encodage UTF-8
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_file = f"python_jobs_clean_{timestamp}.csv"
df.to_csv(csv_file, index=False, encoding='utf-8')
print(f"CSV sauvegardé : {csv_file}")

# 7) Système de filtres dynamiques en ligne de commande 

import argparse

parser = argparse.ArgumentParser(description="Filtrer les offres d'emploi Python.")
parser.add_argument('--city', type=str, help="Filtrer par ville")
parser.add_argument('--contract', type=str, help="Filtrer par type de contrat (Full-Time/Part-Time/Contract)")
args = parser.parse_args()

filtered_df = df
if args.city:
    filtered_df = filtered_df[filtered_df['location'].str.contains(args.city, case=False)]
if args.contract:
    filtered_df = filtered_df[filtered_df['contract_type'].str.contains(args.contract, case=False)]

print(f"\nNombre d'offres après filtrage : {len(filtered_df)}")
print(filtered_df[['title','company','location','contract_type','date_posted']].head(10))

