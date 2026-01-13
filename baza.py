import streamlit as st
from supabase import create_client, Client
import pandas as pd

# --- 1. KONFIGURACJA STRONY I POŁĄCZENIA ---
st.set_page_config(page_title="System Magazynowy", layout="wide")

try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Błąd konfiguracji: Sprawdź Secrets w Streamlit Cloud.")
    st.stop()

# --- 2. FUNKCJE POBIERANIA DANYCH ---
def get_categories():
    res = supabase.table("kategorie").select("id, nazwa, opis").execute()
    return res.data

def get_products():
    res = supabase.table("produkty").select("id, nazwa, liczba, cena, kategoria_id, kategorie(nazwa)").execute()
    return res.data

# --- 3. MENU BOCZNE ---
st.sidebar.title("Nawigacja")
menu = st.sidebar.radio("Wybierz sekcję:", ["📦 Produkty", "📂 Kategorie", "📊 Stan Magazynowy"])

# --- 4. SEKCJA: KATEGORIE ---
if menu == "📂 Kategorie":
    st.title("📂 Zarządzanie Kategoriami")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("➕ Dodaj kategorię")
        with st.form("add_cat", clear_on_submit=True):
            name = st.text_input("Nazwa")
            desc = st.text_area("Opis")
            if st.form_submit_button("Dodaj"):
                if name:
                    supabase.table("kategorie").insert({"nazwa": name, "opis": desc}).execute()
                    st.success("Dodano!")
                    st.rerun()

    with col2:
        st.subheader("🗑️ Usuń kategorię")
        cats = get_categories()
        if cats:
            cat_to_del
