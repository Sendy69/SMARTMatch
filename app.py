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


# Configuration de la page
st.set_page_config(layout="wide", page_title="SMARTMatch", page_icon=":moneybag:")

# CSS pour améliorer l'interface
st.markdown("""
<style>
    .main .block-container {padding-top: 2rem;}
    .stButton button {background-color: #c7f0d2; color: #000000;}
    .stButton button:hover {background-color: #95e3a9;}
    div[data-testid="stFileUploader"] {padding: 1rem; border: 1px dashed #888888; border-radius: 10px;}
    .receipt-viewer {border: 1px solid #cccccc; border-radius: 5px; padding: 10px;}
    .file-list {max-height: 200px; overflow-y: auto; border: 1px solid #e0e0e0; padding: 8px; border-radius: 5px;}
</style>
""", unsafe_allow_html=True)

# Fonction pour créer un aperçu d'image en base64
def get_image_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Fonction pour créer un lien cliquable vers une image
def get_image_link(image_path, idx):
    if not image_path or not os.path.exists(image_path):
        return "Pas d'image"
    
    # Créer un ID unique pour cette image
    image_id = f"img_{idx}"
    
    # Retourner un lien formaté pour Streamlit
    filename = os.path.basename(image_path)
    # Tronquer le nom de fichier si trop long
    if len(filename) > 20:
        filename = filename[:17] + "..."
    
    return f"[{filename}](#{image_id})"

# Création de dossiers temporaires pour stocker les fichiers
if "temp_dir" not in st.session_state:
    st.session_state.temp_dir = tempfile.mkdtemp()
    st.session_state.receipts_dir = os.path.join(st.session_state.temp_dir, "receipts")
    os.makedirs(st.session_state.receipts_dir, exist_ok=True)

# Initialisation des variables de session
if "bank_data" not in st.session_state:
    st.session_state.bank_data = pd.DataFrame(columns=["date", "amount", "currency", "vendor", "Receive"])
if "receipts_files" not in st.session_state:
    st.session_state.receipts_files = []
if "selected_image" not in st.session_state:
    st.session_state.selected_image = None
if "receipt_mapping" not in st.session_state:
    st.session_state.receipt_mapping = {}  # Dictionnaire pour stocker les associations

# Fonction pour traiter une archive ZIP contenant des images
def process_zip_directory(zip_file):
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        # Extraire uniquement les fichiers images
        image_files = [f for f in zip_ref.namelist() if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        # Extraire les images
        for img_file in image_files:
            zip_ref.extract(img_file, st.session_state.receipts_dir)
        
        # Retourner les chemins complets des images extraites
        return [os.path.join(st.session_state.receipts_dir, img_file) for img_file in image_files]

# Fonction pour exécuter le mapping
def execute_mapping():
    if not st.session_state.receipts_files:
        st.error("Aucun reçu n'a été chargé.")
        return False
    if st.session_state.bank_data.empty:
        st.error("Aucun relevé bancaire n'a été chargé.")
        return False
    
    # Afficher la barre de progression
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Simuler le processus de mapping avec des étapes progressives
    total_steps = len(st.session_state.bank_data)
    receipt_links = []
    receipt_paths = []
    
    for i in range(total_steps):
        # Mise à jour de la progression
        progress = (i + 1) / total_steps
        progress_bar.progress(progress)
        status_text.text(f"Traitement de la transaction {i+1}/{total_steps}...")
        
        # Simuler un traitement qui prend du temps
        time.sleep(0.1)
        
        # Dans un cas réel, vous utiliseriez un algorithme de correspondance
        # Pour cette démo, nous assignons des reçus aléatoirement s'il y en a
        if st.session_state.receipts_files:
            receipt_path = random.choice(st.session_state.receipts_files)
            receipt_paths.append(receipt_path)
            receipt_links.append(get_image_link(receipt_path, i))
        else:
            receipt_paths.append("")
            receipt_links.append("Pas d'image")
    
    # Mise à jour des données avec les liens vers les reçus
    st.session_state.bank_data["Receive"] = receipt_links
    st.session_state.bank_data["receipt_path"] = receipt_paths  # Colonne cachée pour le chemin réel
    
    # Stockage du mapping dans session_state
    for i, row in st.session_state.bank_data.iterrows():
        st.session_state.receipt_mapping[i] = row["receipt_path"]
    
    # Nettoyage
    status_text.text("Mapping terminé avec succès!")
    time.sleep(1)
    status_text.empty()
    progress_bar.empty()
    
    return True

# Fonction pour exporter les résultats en CSV
def export_to_csv():
    if st.session_state.bank_data.empty:
        st.error("Pas de données à exporter.")
        return None
    
    # Créer une copie des données sans la colonne des chemins internes
    export_df = st.session_state.bank_data.copy()
    if "receipt_path" in export_df.columns:
        export_df = export_df.drop(columns=["receipt_path"])
    
    # Remplacer les liens par des noms de fichiers
    export_df["Receive"] = export_df["Receive"].apply(lambda x: 
        os.path.basename(re.search(r'#img_(\d+)', x).group(0)) if isinstance(x, str) and '#img_' in x else "Pas d'image")
    
    # Préparer le CSV
    csv = export_df.to_csv(index=False)
    return csv

# Layout principal en deux colonnes
col1, col2 = st.columns([1, 2])

with col1:
    # Zone 1: Relevé bancaire
    with st.container():
        st.subheader("Relevé bancaire")
        uploaded_csv = st.file_uploader("Déposer votre relevé bancaire (CSV)", type="csv", key="bank_statement")
        if uploaded_csv:
            # Enregistrer dans un dossier temporaire
            path = os.path.join("temp", uploaded_csv.name) # path à recuperer pour la fonction de matching
            os.makedirs("temp", exist_ok=True)

            with open(path, "wb") as f:
                f.write(uploaded_csv.getbuffer())

            #st.write("📁 Chemin local du fichier :", path)
        
        if uploaded_csv is not None:
            try:
                # Lecture du fichier CSV
                bank_data = get_bank_statement(uploaded_csv)
                
                # Vérification des colonnes requises
                required_cols = ["date", "amount", "currency", "vendor"]
                missing_cols = [col for col in required_cols if col not in bank_data.columns]
                
                if missing_cols:
                    st.error(f"Colonnes manquantes dans le CSV: {', '.join(missing_cols)}")
                else:
                    # Ajout de la colonne Receive vide
                    if "Receive" not in bank_data.columns:
                        bank_data["Receive"] = "Aucune Facture Associée"
                    
                    st.session_state.bank_data = bank_data
                    st.success(f"Relevé bancaire chargé avec succès! ({len(bank_data)} transactions)")
            except Exception as e:
                st.error(f"Erreur lors du chargement du CSV: {e}")
    
    # Zone 2: Dépôt des reçus
    with st.container():
        st.subheader("Déposer vos reçus")
        
        # Option pour télécharger des fichiers individuels
        uploaded_files = st.file_uploader("Déposer des images de reçus", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="receipts")
        
        # Option pour télécharger un répertoire via un fichier zip
        st.markdown("**OU**")
        uploaded_zip = st.file_uploader("Déposer un dossier de reçus compressé (ZIP)", type="zip", key="receipts_zip")
        
        # Traitement des fichiers individuels
        if uploaded_files:
            receipt_files = []
            for file in uploaded_files:
                # Sauvegarder le fichier
                file_path = os.path.join(st.session_state.receipts_dir, file.name)
                with open(file_path, "wb") as f:
                    f.write(file.getbuffer())
                receipt_files.append(file_path) # recupérer receipts_file pour l'extraction de données
                st.write("📁 Chemin local du fichier :", receipt_files)
            
            # Ajouter à la liste existante
            st.session_state.receipts_files.extend(receipt_files)
            st.success(f"{len(receipt_files)} reçus chargés!")
            receipts_df = pd.DataFrame(receipt_files, columns=["Fichiers de reçus"])
        
        # Traitement du zip
        if uploaded_zip:
            with st.spinner("Traitement du fichier ZIP..."):
                # Sauvegarder le fichier zip temporairement
                zip_path = os.path.join(st.session_state.temp_dir, "receipts.zip")
                with open(zip_path, "wb") as f:
                    f.write(uploaded_zip.getbuffer())
                
                # Extraire les images
                try:
                    extracted_files = process_zip_directory(zip_path)
                    st.session_state.receipts_files.extend(extracted_files)
                    st.success(f"{len(extracted_files)} reçus extraits du dossier!")
                    st.write("📁 Chemin local du fichier :", extracted_files)
                except Exception as e:
                    st.error(f"Erreur lors de l'extraction du ZIP: {e}")
        
        # Afficher la liste des reçus chargés
        if st.session_state.receipts_files:
            with st.expander(f"Reçus chargés ({len(st.session_state.receipts_files)})"):
                st.markdown('<div class="file-list">', unsafe_allow_html=True)
                for i, file_path in enumerate(st.session_state.receipts_files):
                    st.write(f"{i+1}. {os.path.basename(file_path)}")
                st.markdown('</div>', unsafe_allow_html=True)
    
    # Bouton pour exécuter le mapping
    with st.container():
        st.markdown("##")  # Espacement
        if st.button("Exécuter mapping de reçu", key="execute_mapping", type="primary", use_container_width=True):
            results = analyzed_receipts(IMAGES_PATH, CONTEXT_PATH, PROMPT_PATH, MODEL, CLIENT)

            receipts = parse_json_to_dataframe(results)
            success = matching_func(path, receipts)
            print(success)
            
                    # Zone pour l'exportation CSV uniquement
    with st.container():
        st.subheader("Exporter les résultats")
        if st.button("Exporter en CSV", use_container_width=True):
            if st.session_state.bank_data.empty:
                st.error("Pas de données à exporter.")
            else:
                csv_data = export_to_csv()
                if csv_data:
                    st.download_button(
                        label="Télécharger CSV",
                        data=csv_data,
                        file_name="mapping_reçus.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

with col2:
    # Affichage du tableau des transactions avec liens vers les reçus
    st.subheader("Transactions")
    
    # Affichage du tableau
    if not st.session_state.bank_data.empty:
        # Créer une version pour l'affichage (sans la colonne des chemins si elle existe)
        display_df = st.session_state.bank_data.copy()
        if "receipt_path" in display_df.columns:
            display_df = display_df.drop(columns=["receipt_path"])
        
        st.dataframe(display_df, use_container_width=True)
        
        # Zone pour afficher l'image sélectionnée
        st.markdown("### Aperçu du reçu sélectionné")
        
        # Sélectionner une transaction pour voir le reçu
        transaction_options = [f"Transaction {i+1}: {row['date']} - {row['vendor']} ({row['amount']} {row['currency']})" 
                              for i, row in st.session_state.bank_data.iterrows()]
        
        col_select, col_preview = st.columns([1, 1])
        
        with col_select:
            selected_idx = st.selectbox("Sélectionner une transaction", 
                                      range(len(transaction_options)),
                                      format_func=lambda i: transaction_options[i])
            
            # Vérifier si un reçu est associé à cette transaction
            if selected_idx is not None and selected_idx in st.session_state.receipt_mapping:
                receipt_path = st.session_state.receipt_mapping[selected_idx]
                if receipt_path and os.path.exists(receipt_path):
                    st.session_state.selected_image = receipt_path
                else:
                    st.session_state.selected_image = None
                    st.info("Pas de reçu associé à cette transaction.")
        
        # Afficher l'image sélectionnée
        if st.session_state.selected_image and os.path.exists(st.session_state.selected_image):
            try:
                st.markdown('<div class="receipt-viewer">', unsafe_allow_html=True)
                st.image(st.session_state.selected_image, 
                         caption=f"Reçu pour {st.session_state.bank_data.iloc[selected_idx]['vendor']}",
                         use_column_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Erreur lors de l'affichage du reçu: {e}")
        else:
            st.info("Sélectionnez une transaction pour voir le reçu associé.")
    else:
        st.info("Aucune transaction bancaire n'a été chargée.")

# Nettoyage des fichiers temporaires à la fermeture de l'application
def cleanup():
    if hasattr(st.session_state, 'temp_dir') and os.path.exists(st.session_state.temp_dir):
        shutil.rmtree(st.session_state.temp_dir)

# Enregistrer la fonction de nettoyage pour qu'elle s'exécute à la fermeture
import atexit
atexit.register(cleanup)