import json
from model import PasserelleNetilion


def fetch_all_units():
    """ Récupère toutes les unités de Netilion et les actualise le fichier units.json
        Cette fonction n'est pas faite pour être exécutée régulièrement, mais plutôt
        pour réactualise la base de donnée en cas de rajout d'unités par Endress Hauser
    """
    units = []
    page = 1
    per_page = 300  # Nombre maximum d'éléments par page (max imposé par Netilion)
    
    while True:
        endpoint = f"units?page={page}&per_page={per_page}"
        
        # Utilise le premier compte enregistré pour faire la requête
        # (si ce compte n'est pas valide cela ne fonctionnera pas)
        response = PasserelleNetilion().to_dict()["accounts"]["1"].send_request("GET", endpoint)
        # print(response)

        if response.status_code != 200:
            print(f"Erreur {response.status_code} lors de la récupération des unités : {response.text}")
            break

        data = response.json()
        units.extend(data["units"])

        # Vérifie s'il y a encore des pages à récupérer
        if "pagination" in data and data["pagination"].get("next"):
            page += 1
        else:
            break

    # Sauvegarde dans un fichier JSON
    with open("units.json", "w", encoding="utf-8") as f:
        json.dump(units, f, indent=4, ensure_ascii=False)

    print(f"✅ {len(units)} unités enregistrées dans {"units.json"}")

        
        






if __name__ == '__main__':
    
    # load_dotenv()

    from services.config_utils import load_config
    load_config(False)
    

    # save_accounts_to_file()
    
    # print ("Après chargement")
    # for account in accounts.values():
    #     print(str(account))