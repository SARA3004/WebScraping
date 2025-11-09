import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import plotly.express as px  # pour visualisations interactives
import numpy as np

BASE_URL = "http://books.toscrape.com/"

# Fonction pour extraire les livres sur une page
def get_books_from_page(url):
    resp = requests.get(url)
    if resp.status_code != 200:
        return []
    doc = BeautifulSoup(resp.text, 'html.parser')
    books = []
    for article in doc.find_all('article', class_='product_pod'):
        title = article.h3.a['title']
        detail_url = urljoin(BASE_URL, article.h3.a['href'])
        price = float(article.find('p', class_='price_color').text.replace('£','').replace('Â',''))
        rating_class = article.p['class'][1]  
        rating_map = {'One':1,'Two':2,'Three':3,'Four':4,'Five':5}
        rating = rating_map.get(rating_class, 0)
        stock_text = article.find('p', class_='instock availability').text.strip()
        stock = int(''.join(filter(str.isdigit, stock_text))) if any(c.isdigit() for c in stock_text) else 0
        category = None  # On peut remplir avec page détail si nécessaire
        books.append({
            'title': title,
            'price': price,
            'rating': rating,
            'stock': stock,
            'category': category,
            'detail_url': detail_url
        })
    return books

# Pagination automatique 
all_books = []
next_page = BASE_URL
while next_page:
    books = get_books_from_page(next_page)
    all_books.extend(books)
    # Cherche le lien de la page suivante
    resp = requests.get(next_page)
    doc = BeautifulSoup(resp.text, 'html.parser')
    next_tag = doc.find('li', class_='next')
    next_page = urljoin(BASE_URL, next_tag.a['href']) if next_tag else None

# Créer le DataFrame 
df = pd.DataFrame(all_books)

# Analyses
avg_price_by_rating = df.groupby('rating')['price'].mean()
print("Prix moyen par note :")
print(avg_price_by_rating)

avg_price_by_category = df.groupby('category')['price'].mean()
print("\nPrix moyen par catégorie :")
print(avg_price_by_category)
# Vérifier si la variable n’est pas vide avant de tracer
if not avg_price_by_category.empty:
    avg_price_by_category.plot(kind='bar', color='lightgreen', figsize=(8, 4))
    plt.title("Prix moyen par catégorie")
    plt.xlabel("Catégorie")
    plt.ylabel("Prix moyen (£)")
    pdf.savefig()
    plt.close()
else:
    print("Aucune donnée de catégorie disponible pour afficher le graphique.")



price_stats_by_category = df.groupby('category')['price'].agg(['min','max','mean','median'])
print("\nTendances de prix par catégorie :")
print(price_stats_by_category)

out_of_stock = df[df['stock'] == 0]
print(f"\nNombre de livres en rupture de stock : {len(out_of_stock)}")

rating_counts = df['rating'].value_counts().sort_index()
print("\nDistribution des ratings :")
print(rating_counts)

plt.figure(figsize=(6,4))
rating_counts.plot(kind='bar', color='skyblue')
plt.title("Distribution des ratings")
plt.xlabel("Rating")
plt.ylabel("Nombre de livres")
plt.show()

# Sauvegarde CSV
# Nom fixe sans timestamp
"""df.to_csv('books_full_info.csv', index=False, encoding='utf-8')
avg_price_by_rating.to_csv('avg_price_by_rating.csv')
avg_price_by_category.to_csv('avg_price_by_category.csv')
price_stats_by_category.to_csv('price_stats_by_category.csv')
out_of_stock.to_csv('out_of_stock_books.csv', index=False)
"""


# challange
# Corrélation entre note et prix
correlation = df['rating'].corr(df['price'])
print(f"\nCorrélation entre la note et le prix : {correlation:.2f}")

# Alertes prix
PRICE_ALERT_THRESHOLD = 50.0 
alerts = df[df['price'] > PRICE_ALERT_THRESHOLD]

if not alerts.empty:
    print(f"\n {len(alerts)} livres dépassent {PRICE_ALERT_THRESHOLD} £ !")
    print(alerts[['title', 'price', 'rating']].head(10))
else:
    print(f"\n Aucun livre ne dépasse {PRICE_ALERT_THRESHOLD} £")


# Génération d’un rapport PDF avec matplotlib

pdf_filename = "books_report.pdf"
with PdfPages(pdf_filename) as pdf:
    # Graphique 1 : distribution des prix
    plt.figure(figsize=(6, 4))
    plt.hist(df['price'], bins=20)
    plt.title("Distribution des prix")
    plt.xlabel("Prix (£)")
    plt.ylabel("Nombre de livres")
    pdf.savefig()
    plt.close()

    # Graphique 2 : prix moyen par note
    avg_price_by_rating.plot(kind='bar', color='lightblue', figsize=(6, 4))
    plt.title("Prix moyen par note")
    plt.xlabel("Note")
    plt.ylabel("Prix moyen (£)")
    pdf.savefig()
    plt.close()

    # Graphique 3 : prix moyen par catégorie
   if not avg_price_by_category.empty:
    avg_price_by_category.plot(kind='bar', color='lightgreen', figsize=(8, 4))
    plt.title("Prix moyen par catégorie")
    plt.xlabel("Catégorie")
    plt.ylabel("Prix moyen (£)")
    pdf.savefig()
    plt.close()
else:
    print(" Aucune donnée de catégorie disponible pour ce graphique.")

    # Graphique 4 : relation note/prix
    plt.figure(figsize=(6, 4))
    plt.scatter(df['rating'], df['price'], alpha=0.6)
    plt.title(f"Corrélation note/prix (r={correlation:.2f})")
    plt.xlabel("Note")
    plt.ylabel("Prix (£)")
    pdf.savefig()
    plt.close()

print(f"Rapport PDF généré : {pdf_filename}")


# Visualisations interactives (Plotly)
# Graphique interactif : prix en fonction des notes
fig = px.scatter(df, x='rating', y='price', color='main_category',
                 title='Relation entre note et prix par catégorie',
                 hover_data=['title'])
fig.show()

# Graphique interactif : prix moyen par catégorie
fig2 = px.bar(avg_price_by_category, title="Prix moyen par catégorie",
              labels={'value': 'Prix moyen (£)', 'index': 'Catégorie'})
fig2.show()
