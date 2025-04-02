import os
from mistralai import Mistral
import time

import base64
import requests
import json
import pandas as pd


from dotenv import load_dotenv
load_dotenv()
Api_key= os.environ["mistral_jd"]

IMAGE_FOLDER="../dataset/receipts/"
all_dataframes = []


def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')




def extract(image_path):
    # api_url = 'https://api.mistral.ai/v1/chat/completions'

    client= Mistral(api_key=Api_key)
    base64_image = image_to_base64(image_path)

    model= "pixtral-12b-2409"
    messages= [
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": "You are a chartered accountant, and the information must be in the following format: Date: YYYY-MM-DD , Amount: return example (20.8 if the amount contains commas),Merchant: in lowercase, Currency(if it exist and null if not exist)"
                } 
            ],

            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Décris cette image sous forme de fichier JSON structuré avec les clés : 'document_type', 'description', 'fields', et 'summary',le format de date: YYYY-MM-DD et le format de l'heure: HH:MM:SS. Le champ 'fields' doit être un tableau d'objets avec les clés 'name' et 'value'. Le champ 'summary' doit être un résumé de la description et format des prixs : 123,45 € ou 123,45 $.Required fields:date: The payment due date,total_amount: The total amount due,name: Supplier name, items: description: Description of the item or service,quantity: Quantity of the item,total_price: Total price for the item,tax: Tax amount"
                },
                {
                    "type": "image_url", 
                    "image_url": f"data:image/jpeg;base64,{base64_image}"}
            ]
        }
    ]
    response = client.chat.complete(
        model=model, 
        messages=messages,
        response_format={"type": "json_object"}
    )
    content = response.choices[0].message.content
    try:
        json_data = json.loads(content)
        return json.dumps(json_data, indent=2)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON response", "raw_response": content})
    


def process_images():
    if not os.path.exists(IMAGE_FOLDER):
        raise ValueError(f"Le dossier {IMAGE_FOLDER} n'existe pas.")

    for filename in os.listdir(IMAGE_FOLDER):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            image_path = os.path.join(IMAGE_FOLDER, filename)
            print(f"📷 Traitement de : {filename}")

            result = extract(image_path)
            try:
                result = json.loads(result)
            except json.JSONDecodeError:
                print(f"⚠️ Erreur de décodage JSON pour {filename}")
                continue
            if "error" in result:
                print(f"⚠️ Erreur dans la réponse pour {filename}: {result['error']}")
                continue
            if "fields" not in result:
                print(f"⚠️ Aucune donnée trouvée pour {filename}")
                continue
            if "fields" in result and isinstance(result["fields"], list):
                general_info = {field["name"]: field["value"] for field in result["fields"] if field["name"] != "Items"}
            if general_info:
                df_general = pd.DataFrame([general_info])
                df_general["filename"] = image_path
                all_dataframes.append(df_general)
            else:
                print(f"⚠️ Données invalides ou manquantes pour {filename}")
                all_dataframes.append(df_general)
    if all_dataframes:
        final_df = pd.concat(all_dataframes, ignore_index=True)
        return final_df
    else:
        print(" Aucun fichier n'a été extrait avec succès.")
        return None
    

if __name__ == "__main__":
    start_time = time.time()
    
    try:
        df = process_images()
        if not df.empty:
            print("\n🎉 Résultats finaux:")
            print(df.to_markdown(index=False))
            
            # Sauvegarde des résultats
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            df.to_csv(f"resultats_extraction_{timestamp}.csv", index=False)
            print(f"\n💾 Résultats sauvegardés dans resultats_extraction_{timestamp}.csv")
        else:
            print("\n⚠️ Aucun résultat valide obtenu.")
            
    except Exception as e:
        print(f"\n🔥 Erreur critique: {str(e)}")
    
    print(f"\n⏱ Durée totale: {time.time() - start_time:.2f} secondes")