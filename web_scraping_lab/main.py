from serpapi import GoogleSearch
import pandas as pd
import json

params = {
  "engine": "amazon",
  "k": "iphone",
  "amazon_domain": "amazon.com",
  "api_key": "0f611661c340886b7a704bcbe84a3d21d17c31c020e3f8780268780dc9a5b54f"
}

search = GoogleSearch(params)
results = search.get_dict()


if "apps" in results:
    df = pd.DataFrame(results["apps"])
    df.to_csv("google_play_data.csv", index=False, encoding="utf-8")
    df.to_json("google_play_data.json", orient="records", force_ascii=False, indent=4)
    print("Données enregistrées en CSV et JSON")
else:
    # Si la clé "apps" est absente, on sauvegarde le JSON brut pour inspection
    with open("google_play_data_raw.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    print("JSON brut enregistré dans 'google_play_data_raw.json'")


#Nettoyage de dataFrame
  # Supprimer les doublons basés sur le nom de l'application
df = df.drop_duplicates(subset="title")  


    
  
    
