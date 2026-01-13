import streamlit as st
from supabase import create_client, Client

# --- KONFIGURACJA POŁĄCZENIA ---
# Upewnij się, że w Streamlit Cloud masz ustawione Secrets:
# [Secrets] -> SUPABASE_URL i SUPABASE_KEY
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Nie znaleziono danych uwierzytelniających Supabase w Secrets.")
    st.stop()

st.set_page_config(page_title="Zarządzanie Sklepem", layout="centered")
st.title("📦 Zarządzanie Kategoriami")

# --- FUNKCJE POMOCNICZE ---
def get_categories():
    # Pobieranie danych z bazy
    response = supabase.table("kategorie").select("*").execute()
    return response.data

# Pobieramy dane na starcie
categories = get_categories()

# --- SEKCJA 1: WYŚWIETLANIE ---
st.header("📋 Lista Kategorii")
if categories:
    st.dataframe(categories, use_container_width=True)
else:
    st.info("Baza kategorii jest obecnie pusta.")

st.divider() # Estetyczna linia oddzielająca

# --- SEKCJA 2: DODAWANIE ---
st.header("➕ Dodaj nową kategorię")
with st.form("add_category_form", clear_on_submit=True):
    new_name = st.text_input("Nazwa kategorii")
    new_description = st.text_area("Opis (opcjonalnie)")
    submit_button = st.form_submit_button("Zapisz w bazie")

    if submit_button:
        if new_name.strip():
            try:
                # Wstawianie danych
                supabase.table("kategorie").insert({
                    "nazwa": new_name, 
                    "opis": new_description
                }).execute()
                
                st.success(f"Pomyślnie dodano: {new_name}")
                st.rerun()
            except Exception as e:
                st.error(f"Błąd zapisu: {e}")
        else:
            st.warning("Musisz podać nazwę kategorii!")

st.divider()

# --- SEKCJA 3: USUWANIE ---
st.header("🗑️ Usuń kategorię")
if categories:
    # Mapowanie nazwy na ID dla wygody użytkownika
    cat_options = {c['nazwa']: c['id'] for c in categories}
    selected_cat_name = st.selectbox("Wybierz kategorię do usunięcia", options=list(cat_options.keys()))
    
    if st.button("Usuń trwale", type="primary"):
        cat_id = cat_options[selected_cat_name]
        try:
            # Próba usunięcia
            supabase.table("kategorie").delete().eq("id", cat_id).execute()
            st.success(f"Usunięto kategorię: {selected_cat_name}")
            st.rerun()
        except Exception as e:
            # Obsługa błędu więzów integralności (Foreign Key Constraint)
            st.error("Nie można usunąć! Ta kategoria jest prawdopodobnie przypisana do produktów w tabeli 'Produkty'.")
            st.info("Najpierw usuń lub przesuń produkty z tej kategorii.")
else:
    st.write("Brak danych do usunięcia.")
