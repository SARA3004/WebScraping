import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd
import matplotlib.pyplot as plt

BASE_URL = "https://books.toscrape.com/"

#1. Extraire toutes les catégories 
def get_categories():
    resp = requests.get(BASE_URL)
    resp.raise_for_status()
    doc = BeautifulSoup(resp.text, 'html.parser')
    categories = {}
    for li in doc.select('ul.nav-list ul li a'):
        name = li.text.strip()
        href = li['href']
        url = urljoin(BASE_URL, href)
        categories[name] = url
    return categories

#2. Extraire les livres d’une catégorie 
def get_books_from_category(cat_name, cat_url):
    books = []
    next_page = cat_url

    while next_page:
        resp = requests.get(next_page)
        if resp.status_code != 200:
            print(f" Erreur {resp.status_code} pour {cat_name}")
            break

        doc = BeautifulSoup(resp.text, 'html.parser')
        for article in doc.select('article.product_pod'):
            title = article.h3.a['title']
            price = float(article.find('p', class_='price_color').text.replace('£','').replace('Â',''))
            rating_class = article.p['class'][1]
            rating_map = {'One':1,'Two':2,'Three':3,'Four':4,'Five':5}
            rating = rating_map.get(rating_class, 0)
            books.append({
                'category': cat_name,
                'title': title,
                'price': price,
                'rating': rating
            })

        # Pagination
        next_tag = doc.find('li', class_='next')
        next_page = urljoin(next_page, next_tag.a['href']) if next_tag else None

    return books

# 3. Extraire toutes les données 
all_books = []
categories = get_categories()
print(f"{len(categories)} catégories détectées.")

for cat_name, cat_url in categories.items():
    print(f"Extraction de la catégorie : {cat_name}")
    cat_books = get_books_from_category(cat_name, cat_url)
    all_books.extend(cat_books)

# 4. Créer DataFrame 
df = pd.DataFrame(all_books)
df.to_csv("books_by_category.csv", index=False, encoding="utf-8")
print(f"\n {len(df)} livres extraits au total.")

# 5. Analyses 
stats_by_cat = (
    df.groupby('category')['price']
    .agg(['count', 'mean', 'min', 'max'])
    .rename(columns={'count': 'nb_livres', 'mean': 'prix_moyen', 'min': 'prix_min', 'max': 'prix_max'})
    .sort_values(by='prix_moyen', ascending=False)
)

# Calcul de la moyenne pondérée (prix * rating)
df['pondere'] = df['price'] * df['rating']
weighted_stats = df.groupby('category').apply(
    lambda x: (x['pondere'].sum() / x['rating'].sum()) if x['rating'].sum() > 0 else 0
)
stats_by_cat['prix_moyen_pondere'] = weighted_stats

# 6. Sauvegarde 
stats_by_cat.to_csv("category_ranking.csv", encoding="utf-8")
print("\n Classement des catégories par prix moyen :")
print(stats_by_cat.head(10))

# 7. Visualisation 
plt.figure(figsize=(10, 6))
stats_by_cat['prix_moyen'].plot(kind='bar', color='cornflowerblue')
plt.title("Prix moyen par catégorie")
plt.xlabel("Catégorie")
plt.ylabel("Prix moyen (£)")
plt.xticks(rotation=80)
plt.tight_layout()
plt.show()