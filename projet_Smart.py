import os
import pandas as pd
from mistralai import Mistral
from PIL import Image
import pytesseract
import re
import base64

# Définir la clé d'API directement
os.environ["mistral_api"]="9uSNKnpNNlH88IxO2ELlfGWrLC8iFuRa"

# Accéder à la clé d'API
api_key = os.environ["mistral_api"]
model = "pixtral-12b-2409"
client = Mistral(api_key=api_key)

print("Client Mistral initialisé avec succès.")

# Fonction pour extraire les détails des factures avec Mistral
def extract_invoice_details_with_mistral(image_path):
    print(f"Traitement de l'image : {image_path}")

    # Lire l'image et la convertir en base64
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    # Préparer le message pour Mistral
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Extract the total amount, date, invoice number, and description from this invoice."
                },
                {
                    "type": "image_url",
                    "image_url": f"data:image/jpeg;base64,{base64_image}"
                }
            ]
        }
    ]

    # Appeler l'API de Mistral avec la méthode correcte
    try:
        response = client.chat.complete(model=model, messages=messages)
        print("Réponse de l'API Mistral reçue.")
    except AttributeError as e:
        print(f"Erreur d'attribut : {e}")
        return None

    # Extraire les informations de la réponse
    details = {
        'amount': None,
        'date': None,
        'invoice_number': None,
        'description': None
    }

    # Analyser la réponse pour extraire les informations
    for message in response['choices']:
        content = message['message']['content']
        if "Total Amount" in content:
            details['amount'] = content.split("Total Amount: ")[1]
        if "Date" in content:
            details['date'] = content.split("Date: ")[1]
        if "Invoice Number" in content:
            details['invoice_number'] = content.split("Invoice Number: ")[1]
        if "Description" in content:
            details['description'] = content.split("Description: ")[1]

    return details

# Fonction pour lire un relevé bancaire
def read_bank_statement(file_path):
    print(f"Lecture du relevé bancaire : {file_path}")
    return pd.read_csv(file_path)

# Fonction pour faire correspondre les factures avec un relevé bancaire
def match_invoices_with_bank_statement(bank_statement, invoices):
    matches = []
    for index, transaction in bank_statement.iterrows():
        amount = transaction['Amount']
        date = transaction['Date']
        description = transaction['Description']

        # Recherche de la facture correspondante
        for invoice in invoices:
            if (amount == invoice['amount'] and
                date == invoice['date']):
                matches.append((transaction, invoice))
                break
    return matches

# Fonction pour afficher les résultats sous forme de tableau
def display_matches(matches):
    df = pd.DataFrame(matches, columns=["Transaction", "Invoice"])
    print(df)

# Exemple d'utilisation
invoices_folder = r'D:\COURS\Smartsmatch\dataset-20250401T082817Z-001\dataset\receipts'  # Chemin des factures
invoices = []

# Charger et analyser les images des factures
for filename in os.listdir(invoices_folder):
    if filename.endswith('.jpg'):
        image_path = os.path.join(invoices_folder, filename)
        invoice_details = extract_invoice_details_with_mistral(image_path)
        if invoice_details:
            invoices.append(invoice_details)

# Traiter le relevé bancaire
bank_statement_path = r'D:\COURS\Smartsmatch\dataset-20250401T082817Z-001\dataset\bank_statements\bank_statement.csv'

# Vérifier si le fichier existe
if not os.path.exists(bank_statement_path):
    print(f"Erreur : Le fichier {bank_statement_path} n'existe pas.")
else:
    # Traiter le relevé bancaire
    bank_statement = read_bank_statement(bank_statement_path)
    matches = match_invoices_with_bank_statement(bank_statement, invoices)
    print("Résultats pour le relevé bancaire :")
    display_matches(matches)



