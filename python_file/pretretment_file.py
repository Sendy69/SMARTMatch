import pandas as pd
import glob
import os
import re
import unidecode
from datetime import datetime

def clean_text(text: str) -> str:

    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    text = text.lower()
    text = unidecode.unidecode(text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    return text



def clean_and_format_dates(date_series: pd.Series) -> pd.Series:
    def process_date(x):
        if pd.isnull(x):
            return pd.NaT
        return str(x).strip().replace("/", "-")
    
    cleaned = date_series.apply(process_date)
    return pd.to_datetime(cleaned, errors='coerce')

