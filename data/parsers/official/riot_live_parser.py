# Spectator v5 & Live Client : État de la game en temps réel
# test

from core.schema.Champion import Champion
import requests

url = "https://ddragon.leagueoflegends.com/cdn/14.1.1/data/en_US/champion/Aatrox.json"

response = requests.get(url)

if response.status_code == 200:
    raw_data = response.json()
    
    # retrieve data of champ
    champion_key = list(raw_data['data'].keys())[0]
    data = raw_data['data'][champion_key]
    
    # retrieve data of the champ's spells
    spells_list = []
    for s in data['spells']:
        spells_list.append({
            "name":s['name'],
            "description":s['description']
        })
        
    # cast data to pydantic class
    
    mon_champion = Champion(
        name=data['name'],
        title=data['title'],
        roles=data['tags'],
        difficulty=data['info']['difficulty'],
        spells=spells_list,
        metadata={
            "allytips": data['allytips'],
            "enemytips": data['enemytips']
        }
    )
    print("Données récupérées avec succès !")
else:
    print(f"Erreur : {response.status_code}")