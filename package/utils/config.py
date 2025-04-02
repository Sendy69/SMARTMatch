from dotenv import load_dotenv
import os
from mistralai import Mistral

load_dotenv()
API_KEY = os.environ["MISTRAL_KEY"]
MODEL = "pixtral-12b-2409"
CLIENT = Mistral(api_key=API_KEY)
CONTEXT_PATH = "../../context.txt"
PROMPT_PATH = "../../prompt.txt"
IMAGES_PATH = "../../receipts"
BANK_STATEMENT_PATH = "../../releve_01.csv"