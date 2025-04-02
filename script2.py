import os
import base64
import json
from mistralai import Mistral
from dotenv import load_dotenv

# Chargement de la configuration d'environnement
load_dotenv()
api_key = os.environ["MISTRAL_KEY"]

# Initialisation du client
client = Mistral(api_key=api_key)
model = "pixtral-12b-2409"

output_directory = "invoice"
os.makedirs(output_directory, exist_ok=True)
receipts_folder = "C:/Users/Solangia Ngueke/Documents/MD5/ProjectML/dataset/receipts"
context_file = "C:/Users/Solangia Ngueke/Documents/MD5/ProjectML/context.txt"

# Optimized prompt for invoice extraction
prompt_facture = """Extract these key fields from the invoice:
- invoice_number: Unique invoice identifier.
- device: The currency used in the invoice.
- invoice_date: The date of the invoice.
- due_date: The payment due date.
- total_amount: The total amount due.
- Supplier name
- Customer name


Return the data in JSON format. If a field is missing, use null.
"""

def load_context(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return content


context_text = load_context(context_file)

# Iterate over each file in the receipts folder
for fichier in os.listdir(receipts_folder):
    if fichier.lower().endswith('.jpg'):
        chemin_image = os.path.join(receipts_folder, fichier)
        
        # Read the image and convert to base64
        with open(chemin_image, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        # Define the messages structure
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        # 1) Contexte récupéré du fichier texte
                        "type": "text",
                        "text": context_text
                    },
                    {
                        # 2) Prompt d’extraction
                        "type": "text",
                        "text": prompt_facture
                    },
                    {
                        # 3) L’image encodée
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]

        try:
            # Get the chat response (with JSON output structure)
            chat_response = client.chat.complete(
                model=model,
                messages=messages,
                response_format={"type": "json_object"}
            )
            
            # Print the content of the response
            print(chat_response.choices[0].message.content)

            
            nom_sortie = os.path.join(output_directory, f"resultat_{os.path.splitext(fichier)[0]}.json")
            with open(nom_sortie, 'w', encoding='utf-8') as f:
                f.write(chat_response.choices[0].message.content)
            
            print(f"Traitement réussi: {fichier}")

        except Exception as e:
            print(f"Erreur sur {fichier}: {str(e)}")
