import os 
import pandas 
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from package.utils.mistral_model import *
from package.utils.file_operations import get_bank_statement
from package.utils.config import *
from sentence_transformers import SentenceTransformer, util
from datetime import timedelta
import openpyxl

MODEL_EMBEDED = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# receipts = pd.read_csv("../../receipts/data_cleaned.csv")


def matching_func_1(bank_statement_path, receipts):
    df_bank_statement = get_bank_statement(bank_statement_path)
    df_bank_statement_copy = df_bank_statement.copy()
    df_bank_statement_copy["receipt"] = None  # Colonne pour lier les reçus
    tolerance_days = 2
    similarities = 0.75
    

    for i, receipt in receipts.iterrows():
        #  Filtrer les lignes avec le même montant
        matches_amount = df_bank_statement_copy[df_bank_statement_copy["amount"] == receipt["total_amount"]]

        if not matches_amount.empty:
            if len(matches_amount) == 1:
                index = matches_amount.index[0]
                df_bank_statement_copy.at[index, "receipt"] = receipt["id_invoice"]
                continue

            #  Affiner avec la date
            matches_date = matches_amount[matches_amount["date"] == receipt["invoice_date_clean"]] or matches_amount[matches_amount["date"] + timedelta(tolerance_days) == receipt["invoice_date_clean"]]

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
 


##### TEST #####



# results = extracted_data_receipt(IMAGES_PATH, CONTEXT_PATH, PROMPT_PATH, MODEL, CLIENT)

# receipts = parse_json_to_dataframe(results)

# # print(type(receipts))
# # print(receipts.info())

# df_matched = matching_func(BANK_STATEMENT_PATH, receipts)


# print(df_matched)
# print(df_matched.info())
# print("##########################")
# print("##########################")
# print(df_matched.head(10))


#print(df_bank_statement)