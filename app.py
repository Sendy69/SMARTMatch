import streamlit as st
import pandas as pd
import os
import glob
from PIL import Image
import io
import base64
from pathlib import Path
import shutil
import tempfile
import time
import random
import zipfile
import re
import sys
import uuid
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from package.utils.mistral_model import *
from package.utils.backend import *
from package.utils.config import *
from package.utils.file_operations import *


st.set_page_config(layout="wide", page_title="SMARTMatch", page_icon=":moneybag:")

with st.container():
    st.markdown("""
    <div style='text-align: center; padding: 2rem 1rem; background-color: #f0f4f7; border-radius: 10px;'>
        <h1 style='color: #2c7be5; font-size: 3em;'> SMARTMatch</h1>
        <p style='font-size: 1.2em; max-width: 800px; margin: auto;'>
            <b>SMARTMatch</b> est une application conçue pour simplifier le quotidien des comptables 📊.
            Elle permet de <b>lier automatiquement les lignes d’un relevé bancaire à leurs reçus correspondants</b>,
            grâce à l’analyse intelligente de documents et à des modèles d’IA.
        </p>
        
    </div>
    """, unsafe_allow_html=True)

def get_image_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

def get_image_link(image_path, idx):
    if not image_path or not os.path.exists(image_path):
        return "Pas d'image"
    image_id = f"img_{idx}"
    filename = os.path.basename(image_path)
    if len(filename) > 20:
        filename = filename[:17] + "..."
    return f"[{filename}](#{image_id})"

if "temp_dir" not in st.session_state:
    st.session_state.temp_dir = tempfile.mkdtemp()
    st.session_state.receipts_dir = os.path.join(st.session_state.temp_dir, "receipts")
    os.makedirs(st.session_state.receipts_dir, exist_ok=True)

if "bank_data" not in st.session_state:
    st.session_state.bank_data = pd.DataFrame()
if "receipts_files" not in st.session_state:
    st.session_state.receipts_files = []
if "selected_image" not in st.session_state:
    st.session_state.selected_image = None
if "receipt_mapping" not in st.session_state:
    st.session_state.receipt_mapping = {}


def process_zip_directory(zip_file):
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        image_files = [f for f in zip_ref.namelist() if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        for img_file in image_files:
            zip_ref.extract(img_file, st.session_state.receipts_dir)
        extracted_files = [os.path.join(st.session_state.receipts_dir, img_file) for img_file in image_files]
    return extracted_files

def execute_matching(extracted_files):
    if not st.session_state.receipts_files:
        st.error("Aucun reçu n'a été chargé.")
        return False
    if st.session_state.bank_data.empty:
        st.error("Aucun relevé bancaire n'a été chargé.")
        return False

    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        receipts_df = extract_receipt_data(
            extracted_files,
            context_path=CONTEXT_PATH,     # à adapter
            prompt_path=PROMPT_PATH,        # à adapter
            model=MODEL,                       # ou ton modèle réel
            client=CLIENT                                # instance de ton client Mistral
)
        #### Test avec un dataFrame de recus
        # receipts_df = pd.read_csv("../../receipts/data_cleaned.csv")
        
        print(receipts_df.info())
        bank_path = st.session_state.bank_path

        ## Appel de la fonction de matching
        matching_result_df = matching_func_1(bank_path, receipts_df)
        progress_bar.progress(0.5, text="Matching en cours...")
        time.sleep(2)
        progress_bar.progress(1.0, text="Matching terminé!")
        time.sleep(1)

        print(matching_result_df.head())
        if matching_result_df.empty:
            st.error("Aucun match trouvé entre le relevé bancaire et les reçus.")
            return False
        
        receipt_links = []
        for i, row in matching_result_df.iterrows():
            receipt_path = row["receipt_matched"]
            if receipt_path and os.path.exists(receipt_path):
                receipt_links.append(get_image_link(receipt_path, i))
            else:
                receipt_links.append("Pas d'image")

        # matching_result_df["receipt"] = receipt_links
        # matching_result_df["receipt_path"] = matching_result_df["receipt_matched"]

        st.session_state.bank_data = matching_result_df

        # for i, row in st.session_state.bank_data.iterrows():
        #     st.session_state.receipt_mapping[i] = row["receipt_path"]

        status_text.text("Matching terminé avec succès!")
        time.sleep(1)
    finally:
        progress_bar.empty()
        status_text.empty()

    return True

def export_to_csv():
    if st.session_state.bank_data.empty:
        st.error("Pas de données à exporter.")
        return None

    export_df = st.session_state.bank_data.copy()
    if "receipt_path" in export_df.columns:
        export_df = export_df.drop(columns=["receipt_path"])

    export_df["Receipt_matched"] = export_df["Receipt_matched"].apply(lambda x:
        os.path.basename(re.search(r'#img_(\d+)', x).group(0)) if isinstance(x, str) and '#img_' in x else "Pas d'image")

    return export_df.to_csv(index=False)

col1, col2 = st.columns([1, 2])

### Gestion du stockage et de la recuperation du releve bancaire
with col1:
    st.subheader("Relevé bancaire")
    uploaded_csv = st.file_uploader("Déposer votre relevé bancaire (CSV)", type="csv")
    if uploaded_csv:
        path = os.path.join("temp", uploaded_csv.name)
        os.makedirs("temp", exist_ok=True)
        with open(path, "wb") as f:
            f.write(uploaded_csv.getbuffer())
        st.session_state.bank_path = path
        try:
            bank_data = get_bank_statement(uploaded_csv)
            if "Receipt_matched" not in bank_data.columns:
                bank_data["Receipt_matched"] = "Aucune Facture Associée"
            st.session_state.bank_data = bank_data
            st.success(f"Relevé bancaire chargé avec succès! ({len(bank_data)} transactions)")
        except Exception as e:
            st.error(f"Erreur lors du chargement du CSV: {e}")

    st.subheader("Déposer vos reçus")
    uploaded_files = st.file_uploader("Images de reçus", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    uploaded_zip = st.file_uploader("Ou un ZIP de reçus", type="zip")

    if uploaded_files:
        receipt_files = []
        for file in uploaded_files:
            file_path = os.path.join(st.session_state.receipts_dir, file.name)
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
            receipt_files.append(file_path)
        st.session_state.receipts_files.extend(receipt_files)
        st.success(f"{len(receipt_files)} reçus chargés!")

    if uploaded_zip:
        with st.spinner("Extraction des reçus..."):
            zip_path = os.path.join(st.session_state.temp_dir, "receipts.zip")
            with open(zip_path, "wb") as f:
                f.write(uploaded_zip.getbuffer())
            extracted_files = process_zip_directory(zip_path)
            st.session_state.receipts_files.extend(extracted_files)
            st.success(f"{len(extracted_files)} reçus extraits!")

    if st.session_state.receipts_files:
        with st.expander(f"Reçus chargés ({len(st.session_state.receipts_files)})"):
            for i, file_path in enumerate(st.session_state.receipts_files):
                st.write(f"{i+1}. {os.path.basename(file_path)}")

    if st.button("Exécuter le matching"):
        if uploaded_zip:
            execute_matching(extracted_files)
        if uploaded_files:
            execute_matching(st.session_state.receipts_files)

    st.subheader("Exporter les résultats")
    if st.button("Exporter en CSV"):
        csv_data = export_to_csv()
        if csv_data:
            st.download_button("Télécharger CSV", data=csv_data, file_name="mapping_reçus.csv", mime="text/csv")

with col2:
    st.subheader("Transactions")
    if not st.session_state.bank_data.empty:
        display_df = st.session_state.bank_data.copy()
        if "receipt_path" in display_df.columns:
            display_df = display_df.drop(columns=["receipt_path"])
        st.dataframe(display_df, use_container_width=True)

        st.markdown("### Aperçu du reçu sélectionné")
        transaction_options = [f"Transaction {i+1}: {row['date']} - {row['vendor']} ({row['amount']} {row['currency']})"
                              for i, row in st.session_state.bank_data.iterrows()]
        selected_idx = st.selectbox("Sélectionner une transaction", range(len(transaction_options)),
                                    format_func=lambda i: transaction_options[i])
        if selected_idx in st.session_state.receipt_mapping:
            receipt_path = st.session_state.receipt_mapping[selected_idx]
            if receipt_path and os.path.exists(receipt_path):
                st.image(receipt_path, caption=f"Reçu pour {st.session_state.bank_data.iloc[selected_idx]['vendor']}",
                         use_column_width=True)
            else:
                st.info("Pas de reçu associé à cette transaction.")

import atexit

def cleanup():
    if hasattr(st.session_state, 'temp_dir') and os.path.exists(st.session_state.temp_dir):
        shutil.rmtree(st.session_state.temp_dir)

atexit.register(cleanup)
