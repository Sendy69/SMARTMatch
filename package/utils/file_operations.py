import os
import base64
import pandas as pd
import sys


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
def get_encoded_images(folder_path):
    images_encoded = []
    for filename in os.listdir(folder_path):
        if filename.lower().endswith('.jpeg') or filename.lower().endswith('.jpg'):
            path = os.path.join(folder_path, filename)
            with open(path, 'rb') as f:
                encoded = encode_image(path)
                images_encoded.append({
                    "filename": filename,
                    "content_base64": encoded
                })
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

folder_path = "../../receipts"
context_path = "../../context.txt"

#print(get_context(context_path))
#print(get_bank_statement("../../releve_04.csv"))
#print(get_encoded_images(folder_path))

df = get_bank_statement("../../releve_04.csv")
df.info()