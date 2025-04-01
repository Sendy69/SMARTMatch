import base64
from dotenv import load_dotenv
import os
from mistralai import Mistral
import requests

load_dotenv()
api_key = os.environ["MISTRAL_KEY"]


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



def create_list_of_receipts(folder_path):
    for fichier in os.listdir(folder_path):
        if fichier.lower().endswith('.jpg'):
            chemin_image = os.path.join(folder_path, fichier)
            
            # Encodage base64
            with open(chemin_image, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
    return base64_image

# Exemple d'utilisation
folder = "./receipts"
base64_images = create_list_of_receipts(folder)




#def get_context()

# def get_prompt()


# Path to your image
#image_path = "./receipts/1195-receipt.jpg"

# Getting the base64 string
#base64_images = create_list_of_receipts(folder)



#def get_informations_on_receipts()
# Specify model
model = "pixtral-12b-2409"

# Initialize the Mistral client
client = Mistral(api_key=api_key)

# Define the messages for the chat
messages = [
    {
        "role": "system",
        "content": """You are a chartered accountant, and the information must be in the following format: Date: YYYY-MM-DD , Amount: return example (20.8 if the amount contains commas),Merchant: in lowercase, Currency"""},
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "Extract for each images the information such as the date, the invoice amount, currency and the vendor's name, and return these details for each images in JSON format"
            },
            {
                "type": "image_url",
                "image_url": f"data:image/jpeg;base64,{base64_images}" 
            }
        ]
    }
]

# Get the chat response
chat_response = client.chat.complete(
    model=model,
    messages=messages
)

# Print the content of the response
print(chat_response.choices[0].message.content.strip())