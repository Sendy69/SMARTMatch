import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from package.utils.file_operations import *
from dotenv import load_dotenv
import os
from mistralai import Mistral
import requests


load_dotenv()
api_key = os.environ["MISTRAL_KEY"]
model = "pixtral-12b-2409"
client = Mistral(api_key=api_key)
context_path = "../../context.txt"
prompt_path = "../../prompt.txt"
images_path = "../../receipts"


def analyzed_receipts(images_path, context_path, prompt_path, model, client):
    results = []

    encoded_images = get_encoded_images(images_path)
    context = get_context(context_path)
    prompt = get_prompt(prompt_path)

    for image in encoded_images:
        messages = [
            {
                "role": "system",
                "content": context
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": f"data:image/jpeg;base64,{image['content_base64']}"
                    }
                ]
            }
        ]

        try:
            chat_response = client.chat.complete(
                model=model,
                messages=messages,
                response_format={
                    "type": "json_object"
                }
            )

            # Récupérer le contenu JSON du message
            json_data = json.loads(chat_response.choices[0].message.content)

            result = {
                "filename": image["filename"],
                "date": json_data.get("date"),
                "amount": json_data.get("amount"),
                "currency": json_data.get("currency"),
                "merchant_name": json_data.get("merchant_name"),
                "merchant_address": json_data.get("merchant_address")
            }

        except Exception as e:
            result = {
                "filename": image["filename"],
                "error": str(e)
            }

        results.append(result)

    return results

def parse_json_to_dataframe(results_of_mistral):
    list_of_result = []
    for result in results_of_mistral :  
        list_of_result.append({
            "filename": result.get("filename"),
            "date": result.get("date"),
            "amount": result.get("amount"),
            "currency": result.get("currency"),
            "merchant_name": result.get("merchant_name"),
            "merchant_address": result.get("merchant_address"),
            
        })
    
    return pd.DataFrame(list_of_result)


results = analyzed_receipts(images_path, context_path, prompt_path, model, client )

print(parse_json_to_dataframe(results))