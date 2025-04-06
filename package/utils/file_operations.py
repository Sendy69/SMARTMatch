import os
import base64
import pandas as pd
import sys
import zipfile
import streamlit as st


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))


#### Fonction pour encoder une image en base64
def encode_image(image_path):
    """Encode the image to base64."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"Error: The file {image_path} was not found.")
        return None
    except Exception as e:  # Added general exception handling
        print(f"Error: {e}")
        return None

### Fonction pour lire et encoder toutes les images d'un repertoire
def get_encoded_images(list_of_path_images):
    images_encoded = []
    for path in list_of_path_images:
        if path.lower().endswith(('.jpeg', '.jpg', '.png')) and os.path.isfile(path):
            try:
                encoded = encode_image(path)
                images_encoded.append({
                    "filename": os.path.basename(path),
                    "content_base64": encoded
                })
            except Exception as e:
                print(f"Erreur d'encodage pour {path} : {e}")
    return images_encoded



### Fonction pour recupérer un relevé de compte et le convertir en csv
def get_bank_statement(bank_statement_path):
    df = pd.read_csv(bank_statement_path)
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors='coerce')
    
    return df

def get_context(context_path):
    with open(context_path, 'r', encoding='utf-8') as file:
        context = file.read()
    return context

def get_prompt(prompt_path):
    with open(prompt_path, 'r', encoding='utf-8') as file:
        context = file.read()
    return context

#Fonction pour traiter une archive ZIP contenant des images
def process_zip_directory(zip_file):
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        # Extraire uniquement les fichiers images
        image_files = [f for f in zip_ref.namelist() if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        # Extraire les images
        for img_file in image_files:
            zip_ref.extract(img_file, st.session_state.receipts_dir)
        
        # Retourner les chemins complets des images extraites
        return [os.path.join(st.session_state.receipts_dir, img_file) for img_file in image_files]

# list_of_path_images = "../../receipts"
# context_path = "../../context.txt"

#print(get_context(context_path))
#print(get_bank_statement("../../releve_04.csv"))
#print(get_encoded_images(folder_path))

# df = get_bank_statement("../../releve_04.csv")
# df.info()