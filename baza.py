import streamlit as st
from supabase import create_client, Client

# --- KONFIGURACJA POŁĄCZENIA ---
# Dane pobierane są ze "Secrets" w Streamlit Cloud (bezpieczniejsze niż kod)
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("Zarządzanie Kategoriami Produktów")

# --- SEKTCJA 1: WYŚWIETLANIE KATEGORII ---
st.header("Aktualne Kategorie")

def get_categories():
    response = supabase.table("kategorie").select("*").execute()
    return response.data

categories = get_categories()

if categories:
    st.table(categories)
else:
    st.info("Brak kategorii w bazie.")

# --- SEKCJA 2: DODAWANIE KATEGORII ---
st.header("Dodaj nową kategorię")
with st.form("add_category_form"):
    new_name = st.text_input("Nazwa kategorii")
    new_description = st.text_area("Opis (opcjonalnie)")
    submit_button = st.form_submit_button("Dodaj")

    if submit_button:
        if new_name:
            data = {"nazwa": new_name, "opis": new_description}
            try:
                supabase.table("kategorie").insert(data).execute()
                st.success(f"Dodano kategorię: {new_name}")
                st.rerun() # Odświeżenie widoku
            except Exception as e:
                st.error(f"Błąd: {e}")
        else:
            st.warning("Nazwa kategorii jest wymagana.")


# --- SEKCJA 3: USUWANIE KATEGORII ---
st.header("Usuń kategorię")
if categories:
    # Tworzymy listę do wyboru dla użytkownika
    cat_options = {c['nazwa']: c['id'] for c in categories}
    selected_cat_name = st.selectbox("Wybierz kategorię do usunięcia", options=list(cat_options.keys()))
    
    if st.button("Usuń", type="primary"):
        cat_id = cat_options[selected_cat_name]
        try:
            # Uwaga: Usunięcie nie zadziała, jeśli produkty są przypisane do tej kategorii (klucz obcy)
            supabase.table("kategorie").delete().eq("id", cat_id).execute()
            st.success(f"Usunięto kategorię: {selected_cat_name}")
            st.rerun()
        except Exception as e:
            st.error(f"Nie można usunąć kategorii. Upewnij się, że nie ma do niej przypisanych produktów.")
