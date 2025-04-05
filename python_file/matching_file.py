import pandas as pd
import glob
import os
import re
import unidecode
from datetime import datetime
from sentence_transformers import SentenceTransformer, util
from pretretment_file import clean_text,clean_and_format_dates

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

folder_path ="C:/Users/Solangia Ngueke/Documents/MD5/ProjectML/dataset/bank_statements"
receipt_path= "C:/Users/Solangia Ngueke/Documents/MD5/ProjectML/dataset/invoice_df.csv"
receipt_df=pd.read_csv(receipt_path)
all_files = glob.glob(os.path.join(folder_path, "releve_*.csv"))

dfs = []
for file in all_files:
    df_temp = pd.read_csv(file)
    dfs.append(df_temp)

releve_df = pd.concat(dfs, ignore_index=True)

releve_data = releve_df.copy()
receipt_data = receipt_df.copy()
releve_data["vendor_clean"] = releve_df["vendor"].apply(clean_text)
receipt_data["vendor_clean"] = receipt_df["vendor"].apply(clean_text)
releve_data["date_clean"] = clean_and_format_dates(releve_df["date"])
receipt_data["invoice_date_clean"] = clean_and_format_dates(receipt_df["invoice_date"])
releve_data["date"] = pd.to_datetime(releve_df["date"], errors='coerce')
receipt_data["invoice_date"] = pd.to_datetime(receipt_df["invoice_date"], errors='coerce')




model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

date_tolerance_days = 2         
similarity_threshold = 0.75       

import pandas as pd
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

date_tolerance_days = 2         
similarity_threshold = 0.75       

def match_releve_receipt(releve_df, receipt_df, date_tolerance_days, similarity_threshold):
    if 'vendor_emb' not in receipt_df.columns:
        receipt_df = receipt_df.copy()
        receipt_df['vendor_emb'] = receipt_df['vendor_clean'].apply(
            lambda x: model.encode(x, convert_to_tensor=True)
        )
    
    invoice_ids = []
    similarity_percentages = []
    
    for idx, row in releve_df.iterrows():
        montant = row['amount']
        date_releve = pd.to_datetime(row['date'], errors='coerce')
        vendor_text = row['vendor_clean']
        
        candidats = receipt_df[receipt_df['amount'] == montant].copy()
        
        if len(candidats) == 1:
            best_match = candidats.iloc[0]
            try:
                invoice_id = best_match['invoice_name']
            except:
                invoice_id = None
            invoice_ids.append(invoice_id)
            similarity_percentages.append(100.0)
        
        elif len(candidats) > 1:
            candidats_date = candidats[
                (candidats['invoice_date'] >= date_releve) &
                (candidats['invoice_date'] <= date_releve + pd.Timedelta(days=date_tolerance_days))
            ]
            
            if len(candidats_date) == 1:
                best_match = candidats_date.iloc[0]
                try:
                    invoice_id = best_match['invoice_name']
                except:
                    invoice_id = None
                invoice_ids.append(invoice_id)
                similarity_percentages.append(100.0)
            
            elif len(candidats_date) > 1:
                vendor_emb = model.encode(vendor_text, convert_to_tensor=True)
                candidats_date['similarity'] = candidats_date['vendor_emb'].apply(
                    lambda emb: util.cos_sim(vendor_emb, emb).item()
                )
                max_similarity = candidats_date['similarity'].max()
                best_candidate = candidats_date.loc[candidats_date['similarity'].idxmax()]
                sim_percentage = max_similarity * 100
                if max_similarity > similarity_threshold:
                    try:
                        invoice_id = best_candidate['invoice__name']
                    except:
                        invoice_id = None
                    invoice_ids.append(invoice_id)
                    similarity_percentages.append(sim_percentage)
                else:
                    invoice_ids.append(None)
                    similarity_percentages.append(sim_percentage)
            else:
                invoice_ids.append(None)
                similarity_percentages.append(None)
        else:
            invoice_ids.append(None)
            similarity_percentages.append(None)
    
    result_df = releve_df.copy()
    result_df['invoice'] = invoice_ids
    result_df['similarity'] = similarity_percentages
    
    # Supprimer la colonne 'similarity' et toutes les colonnes contenant 'clean'
    cols_to_drop = [col for col in result_df.columns if col == 'similarity' or 'clean' in col]
    result_df.drop(columns=cols_to_drop, inplace=True)
    
    return result_df


resultats = match_releve_receipt(releve_data, receipt_data, date_tolerance_days, similarity_threshold)
resultats.to_csv("resultats_matching.csv", index=False)
