import os
import glob
import re
import json
import pandas as pd

dossier = "C:/Users/Solangia Ngueke/Documents/MD5/ProjectML/dataset/results"

donnees = []

for chemin_fichier in glob.glob(os.path.join(dossier, "*.json")):
    nom_fichier = os.path.basename(chemin_fichier)
    
    # Extraction de l'ID à partir du nom de fichier
    match = re.search(r"resultat_(\d+)-receipt", nom_fichier)
    if match:
        identifiant = match.group(1)
    else:
        identifiant = None  # Vous pouvez gérer différemment si l'identifiant n'est pas trouvé
    
    # Lecture du fichier JSON
    with open(chemin_fichier, "r", encoding="utf-8") as f:
        contenu = json.load(f)
    
    # Si contenu est une liste, on prend le premier élément, sinon on prend le dict tel quel
    if isinstance(contenu, list):
        invoice_data = contenu[0]
    else:
        invoice_data = contenu
    
    invoice_number = invoice_data.get("invoice_number")
    invoice_date = invoice_data.get("invoice_date")
    due_date = invoice_data.get("due_date")  # si vous souhaitez l'ajouter
    total_amount = invoice_data.get("total_amount")
    
    # Récupération de l'objet supplier
    supplier_info = invoice_data.get("supplier", {})
    # Concaténer nom et adresse dans la même colonne "supplier"
    supplier_name = supplier_info.get("name", "")
    supplier_address = supplier_info.get("address", "")
    supplier_combined = f"{supplier_name} | {supplier_address}".strip(" |")
    
    # Récupération de l'objet customer (si vous en avez besoin pour plus tard)
    # Récupération de l'objet customer
    customer_info = invoice_data.get("customer", {})
    if customer_info is None:  # Si le fichier JSON contient "customer": null
        customer_info = {}

    # Maintenant customer_info est toujours un dict même si c'était None avant.
    customer_name = customer_info.get("name", "")

    # Récupération de la devise (dans le JSON, la clé semble être 'device', à vérifier)
    currency = invoice_data.get("device")
    
    # On ajoute dans la liste un dict représentant la ligne
    donnees.append({
        "id_invoice": identifiant,
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "due_date": due_date,                 # à commenter si non utilisé
        "total_amount": total_amount,
        "supplier": supplier_combined,        # On remplace "supplier_name" par "supplier"
        "customer_name": customer_name,
        "currency": currency
    })

# Création du DataFrame pandas
df = pd.DataFrame(donnees)

# Export CSV (sans la colonne 'id' si vous gardez set_index, alors changez index=True)
df.to_csv("invoice_df.csv", index=False)

# Affichage du DataFrame
print(df)
