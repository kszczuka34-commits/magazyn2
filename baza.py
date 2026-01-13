import streamlit as st
from supabase import create_client, Client
import pandas as pd

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="System Magazynowy", layout="wide")

# --- KONFIGURACJA POŁĄCZENIA ---
@st.cache_resource # Cache połączenia, by nie tworzyć klienta przy każdym odświeżeniu
def init_connection():
    try:
        url: str = st.secrets["SUPABASE_URL"]
        key: str = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error("Błąd konfiguracji: Sprawdź Secrets w Streamlit Cloud.")
        st.stop()

supabase = init_connection()

# --- FUNKCJE POBIERANIA DANYCH ---
def get_categories():
    res = supabase.table("kategorie").select("id, nazwa, opis").execute()
    return res.data

def get_products():
    # Pobieramy produkty z JOINem do kategorii
    res = supabase.table("produkty").select("id, nazwa, liczba, cena, kategoria_id, kategorie(nazwa)").execute()
    return res.data

# --- BOCZNY PANEL NAWIGACYJNY ---
st.sidebar.title("📦 Magazyn v1.0")
menu = st.sidebar.radio("Menu", ["📦 Produkty", "📂 Kategorie", "📊 Stan Magazynowy"])

# ==========================================
# SEKCJA: KATEGORIE
# ==========================================
if menu == "📂 Kategorie":
    st.title("📂 Zarządzanie Kategoriami")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st
