import os
import json
import base64
import logging
import time
from pathlib import Path
from dotenv import load_dotenv
from mistralai import Mistral
import pandas as pd
from tqdm import tqdm  # Importation de tqdm pour la barre de progression

# Charger les variables d'environnement depuis un fichier .env
load_dotenv()

# Configuration du système de journalisation
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("receipt_processing.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Définition des chemins utilisés dans le script
RECEIPTS_PATH = Path("C:/Users/ELOUMOU/Documents/MES_TRAVAUX_DE_PROGRAMMATION/ML2/Projet/dataset/receipts")
CONTEXT_FILE = Path("C:/Users/ELOUMOU/Documents/MES_TRAVAUX_DE_PROGRAMMATION/ML2/Projet/projetmlenv/context.txt")
OUTPUT_DIR = Path("C:/Users/ELOUMOU/Documents/MES_TRAVAUX_DE_PROGRAMMATION/ML2/Projet/resultats_extraction")

class PixtralDataExtractor:
    """
    Classe pour gérer l'extraction des données des reçus à l'aide de l'API Pixtral.
    """
    def __init__(self, receipts_path):
        """
        Initialise la classe avec le chemin des reçus et configure l'API Pixtral.
        """
        self.receipts_dir = receipts_path
        self.client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
        self.context = self._load_context(CONTEXT_FILE)
        self.required_fields = [
            "invoice_number", "invoice_date", "total_amount",
            "supplier_name", "customer_name", "currency"
        ]

    def _load_context(self, context_file):
        """Charge le contexte depuis un fichier texte."""
        if context_file.exists():
            try:
                with open(context_file, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except Exception as e:
                logger.warning(f"Erreur lors du chargement du contexte : {e}")
        return ""

    def _encode_image_to_base64(self, image_path):
        """Encode une image en base64 avec vérifications."""
        try:
            file_size_mb = image_path.stat().st_size / (1024 * 1024)
            if file_size_mb > 20:
                logger.warning(f"Fichier trop volumineux : {image_path} ({file_size_mb:.2f} MB)")
                return None

            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode("utf-8")
        except Exception as e:
            logger.error(f"Erreur d'encodage de {image_path} : {e}")
            return None

    def _call_pixtral_api(self, base64_image):
        """Appel à l'API Pixtral pour l'extraction de données."""
        try:
            prompt = f"""
            {self.context}
            
            Analysez cette facture et retournez les données au format JSON avec les champs suivants :
            - invoice_number : numéro de facture
            - invoice_date : date de facture au format YYYY-MM-DD
            - total_amount : montant total
            - supplier_name : nom du fournisseur
            - customer_name : nom du client
            - currency : devise utilisée (ex. EUR, USD)
            """

            messages = [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                ]
            }]

            response = self.client.chat.complete(
                model="pixtral-large-latest",
                messages=messages,
                response_format={"type": "json_object"},
                max_tokens=2000,
                temperature=0.1
            )

            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Erreur API Pixtral : {e}")
            return None

    def _validate_json(self, json_data):
        """Valide et complète la structure JSON."""
        try:
            data = json.loads(json_data)

            for field in self.required_fields:
                data.setdefault(field, None)

            return data
        except json.JSONDecodeError as e:
            logger.error(f"JSON invalide : {e}")
            return None

    def process_all_receipts(self):
        """Traite tous les reçus et retourne un DataFrame contenant toutes les données extraites."""
        if not self.receipts_dir.exists():
            raise FileNotFoundError(f"Dossier introuvable : {self.receipts_dir}")

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        stats = {"succès": 0, "échecs": 0}
        data_list = []

        # Utilisation de tqdm pour la barre de progression
        for img_path in tqdm(sorted(self.receipts_dir.glob("*.jpg")), desc="Traitement des reçus"):
            logger.info(f"Début traitement : {img_path.name}")

            try:
                # Étape 1: Encodage de l'image
                base64_img = self._encode_image_to_base64(img_path)
                if not base64_img:
                    raise ValueError("Encodage image échoué")

                # Étape 2: Appel API Pixtral
                raw_data = self._call_pixtral_api(base64_img)
                if not raw_data:
                    raise ValueError("Appel API échoué")

                # Étape 3: Validation des données extraites
                clean_data = self._validate_json(raw_data)
                if not clean_data:
                    raise ValueError("Validation JSON échouée")

                # Ajouter le nom du reçu aux données extraites
                clean_data["receipt_name"] = img_path.name

                # Ajouter les données au DataFrame temporaire (liste)
                data_list.append(clean_data)

                stats["succès"] += 1
                logger.info(f"Traitement réussi pour : {img_path.name}")

            except Exception as e:
                stats["échecs"] += 1
                logger.error(f"Échec traitement {img_path.name} : {str(e)}")
                continue

            time.sleep(1)  # Limitation du débit API

        logger.info(f"Résumé traitement - Succès : {stats['succès']}, Échecs : {stats['échecs']}")

        return pd.DataFrame(data_list)


if __name__ == "__main__":
    try:
        extractor = PixtralDataExtractor(RECEIPTS_PATH)

        start_time = time.time()  # Temps de début du traitement
        receipt_df = extractor.process_all_receipts()  # Traite tous les fichiers reçus et récupère un DataFrame consolidé
        print(receipt_df)
        end_time = time.time()  # Temps de fin du traitement

        # Calcul de la durée d'exécution
        execution_time = end_time - start_time
        logger.info(f"Durée d'exécution de process_all_receipts : {execution_time:.2f} secondes")

        # Enregistrer le DataFrame dans un fichier CSV unique avec timestamp dans le nom du fichier
        output_csv_path = OUTPUT_DIR / f"data_receipt_{int(time.time())}.csv"
        receipt_df.to_csv(output_csv_path, index=False, encoding="utf-16")  

        logger.info(f"Fichier CSV généré : {output_csv_path}")
    except Exception as e:
        logger.critical(f"Erreur critique lors de l'exécution du script : {str(e)}", exc_info=True)
