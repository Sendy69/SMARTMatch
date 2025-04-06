import os
import json
import pandas as pd
from datetime import datetime
from package.utils.file_operations import get_encoded_images, get_context, get_prompt
import time

import os 
import pandas as pd
import sys
from sentence_transformers import SentenceTransformer, util
from datetime import timedelta
from openpyxl import Workbook

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from package.utils.file_operations import get_bank_statement

def extract_receipt_data(images_path, context_path, prompt_path, model, client):
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
                response_format={"type": "json_object"}
            )

            json_data = json.loads(chat_response.choices[0].message.content)

            result = {
                "id_invoice": image["filename"],
                "invoice_date": json_data.get("date"),
                "total_amount": json_data.get("amount"),
                "currency": json_data.get("currency"),
                "supplier_name_clean": json_data.get("merchant_name"),
                "address": json_data.get("merchant_address")
            }

        except Exception as e:
            result = {
                "id_invoice": image["filename"],
                "currency": None,
                "total_amount": None,
                "invoice_date": None,
                "supplier_name_clean": None,
                "address": None,
                "description": f"Erreur : {str(e)}"
            }
        time.sleep(1) # Pause pour éviter de surcharger le serveur

        results.append(result)

    df = pd.DataFrame(results)

    

    return df

MODEL_EMBEDED = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def matching_func_1(bank_statement_path, receipts):
    df_bank_statement = get_bank_statement(bank_statement_path)
    df_bank_statement_copy = df_bank_statement.copy()
    df_bank_statement_copy["receipt_matched"] = None  # Colonne pour lier les reçus
    tolerance_days = 2
    similarities = 0.75
    

    for i, receipt in receipts.iterrows():
        #  Filtrer les lignes avec le même montant
        receipt["total_amount"] = pd.to_numeric(receipt["total_amount"], errors="coerce")
        matches_amount = df_bank_statement_copy[df_bank_statement_copy["amount"] == receipt["total_amount"]]

        if not matches_amount.empty:
            if len(matches_amount) == 1:
                index = matches_amount.index[0]
                df_bank_statement_copy.at[index, "receipt"] = receipt["id_invoice"]
                continue

            #  Affiner avec la date
            receipt_date = pd.to_datetime(receipt["invoice_date"])

            matches_date = matches_amount[
            matches_amount["date"].between(receipt_date - timedelta(days=tolerance_days),
                                           receipt_date + timedelta(days=tolerance_days))
        ]

            if len(matches_date) == 1:
                index = matches_date.index[0]
                df_bank_statement_copy.at[index, "receipt"] = receipt["id_invoice"]
                continue

            #  Si plusieurs lignes encore : fuzzy matching sur nom du marchand
            subset = matches_date if not matches_date.empty else matches_amount

            receipt_vendor_name = receipt.get("supplier_name_clean", "")
            receipt_vendor_address = receipt.get("address", "")
            vendor_receipt = receipt_vendor_name + " " + receipt_vendor_address if receipt_vendor_address else receipt_vendor_name

            if not vendor_receipt.strip():
                continue  # Pas d'infos pour matcher

            vendor_receipt_embed = MODEL_EMBEDED.encode(vendor_receipt, convert_to_tensor=True)
            similarities = []

            for j, row in subset.iterrows():
                vendor_name = row.get("vendor", "")
                vendor_embed = MODEL_EMBEDED.encode(vendor_name, convert_to_tensor=True)
                score = util.cos_sim(vendor_embed, vendor_receipt_embed).item()
                similarities.append((j, score))

            if similarities:
                best_index, best_score = max(similarities, key=lambda x: x[1])
                if best_score > similarities:
                    df_bank_statement_copy.at[best_index, "receipt"] = receipt["id_invoice"]

    return df_bank_statement_copy


def matching_func_2(bank_statement_path, receipts_df, receipts_folder):
    df_bank_statement = get_bank_statement(bank_statement_path)
    df_bank_statement_copy = df_bank_statement.copy()
    df_bank_statement_copy["receipt_matched"] = None  # Colonne pour chemins vers reçus

    tolerance_days = 2
    similarities = 0.75

    # Création d’un fichier Excel log temporaire pour trace avec openpyxl
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["Transaction Index", "Matched Receipt", "Similarity"])

    for i, receipt in receipts_df.iterrows():
        matches_amount = df_bank_statement_copy[df_bank_statement_copy["amount"] == receipt["total_amount"]]
        if matches_amount.empty:
            continue

        receipt_date = pd.to_datetime(receipt["invoice_date"])
        matches_date = matches_amount[
            matches_amount["date"].between(receipt_date - timedelta(days=tolerance_days),
                                           receipt_date + timedelta(days=tolerance_days))
        ]
        if matches_date.empty:
            continue

        receipt_embedding = MODEL_EMBEDED.encode(receipt["supplier_name"], convert_to_tensor=True)
        for idx, row in matches_date.iterrows():
            bank_embedding = MODEL_EMBEDED.encode(row["supplier_name"], convert_to_tensor=True)
            similarity = util.pytorch_cos_sim(receipt_embedding, bank_embedding).item()
            if similarity > similarities:
                image_filename = receipt.get("file_name", f"{receipt.get('id', i)}.jpg")
                image_path = os.path.join(receipts_folder, image_filename)
                if os.path.exists(image_path):
                    df_bank_statement_copy.at[idx, "receipt"] = image_path
                    sheet.append([idx, image_filename, round(similarity, 2)])
                break

    # Enregistrement du fichier Excel dans le même dossier que le bank_statement
    log_path = os.path.join(os.path.dirname(bank_statement_path), "matching_log.xlsx")
    workbook.save(log_path)

    return df_bank_statement_copy
