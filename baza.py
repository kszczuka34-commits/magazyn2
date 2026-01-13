import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# --- 1. KONFIGURACJA ---
st.set_page_config(page_title="System Magazynowy Pro", layout="wide")

try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Błąd konfiguracji: Sprawdź Secrets.")
    st.stop()

# --- 2. FUNKCJE ---
def get_categories():
    return supabase.table("kategorie").select("*").execute().data

def get_products():
    return supabase.table("produkty").select("*, kategorie(nazwa)").execute().data

def log_movement(product_id, operation_type, qty, note=""):
    # Funkcja zapisująca ruch w magazynie (wymaga tabeli 'historia')
    try:
        supabase.table("historia").insert({
            "produkt_id": product_id,
            "typ_operacji": operation_type,
            "ilosc": qty,
            "notatka": note
        }).execute()
    except:
        pass # Jeśli nie stworzyłeś tabeli historia, aplikacja pominie ten krok

# --- 3. MENU ---
menu = st.sidebar.radio("Menu", ["📦 Magazyn", "📂 Kategorie", "📊 Raporty", "📜 Historia Ruchów"])

# ==========================================
# SEKCJA: MAGAZYN (Z WYSZUKIWARKĄ)
# ==========================================
if menu == "📦 Magazyn":
    st.title("📦 Stan Magazynowy i Produkty")
    
    # Wyszukiwarka
    search_query = st.text_input("🔍 Szukaj produktu po nazwie...", "").lower()
    
    products_data = get_products()
    if products_data:
        df = pd.DataFrame(products_data)
        df['kat_nazwa'] = df['kategorie'].apply(lambda x: x['nazwa'] if x else "Brak")
        
        # Filtrowanie
        if search_query:
            df = df[df['nazwa'].str.lower().contains(search_query)]
        
        st.dataframe(df[['id', 'nazwa', 'kat_nazwa', 'liczba', 'cena']], use_container_width=True)

        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("➕ Dodaj nowy produkt")
            with st.expander("Otwórz formularz"):
                cats = get_categories()
                with st.form("add_prod", clear_on_submit=True):
                    name = st.text_input("Nazwa")
                    cat = st.selectbox("Kategoria", cats, format_func=lambda x: x['nazwa'])
                    qty = st.number_input("Ilość", min_value=0)
                    price = st.number_input("Cena", min_value=0.0)
                    if st.form_submit_button("Dodaj"):
                        res = supabase.table("produkty").insert({"nazwa": name, "kategoria_id": cat['id'], "liczba": qty, "cena": price}).execute()
                        log_movement(res.data[0]['id'], "PRZYJĘCIE (NOWY)", qty, "Inicjalizacja produktu")
                        st.rerun()
        
        with col2:
            st.subheader("🔄 Szybka zmiana stanu")
            with st.expander("Zmień ilość"):
                selected_p = st.selectbox("Wybierz produkt", products_data, format_func=lambda x: x['nazwa'])
                mod_type = st.radio("Typ operacji", ["Dostawa (+)", "Wydanie (-)"], horizontal=True)
                mod_qty = st.number_input("Ilość", min_value=1)
                reason = st.text_input("Notatka (np. Faktura nr 123)")
                
                if st.button("Zatwierdź zmianę"):
                    current_qty = selected_p['liczba']
                    final_qty = current_qty + mod_qty if "Dostawa" in mod_type else current_qty - mod_qty
                    
                    if final_qty < 0:
                        st.error("Błąd: Stan nie może być ujemny!")
                    else:
                        supabase.table("produkty").update({"liczba": final_qty}).eq("id", selected_p['id']).execute()
                        log_movement(selected_p['id'], "DOSTAWA" if "Dostawa" in mod_type else "WYDANIE", mod_qty, reason)
                        st.success("Zmieniono stan!")
                        st.rerun()

# ==========================================
# SEKCJA: HISTORIA RUCHÓW (LOGI)
# ==========================================
elif menu == "📜 Historia Ruchów":
    st.title("📜 Historia Ruchów Magazynowych")
    try:
        # Pobieramy historię wraz z nazwami produktów
        history = supabase.table("historia").select("*, produkty(nazwa)").execute().data
        if history:
            h_df = pd.DataFrame(history)
            h_df['produkt'] = h_df['produkty'].apply(lambda x: x['nazwa'] if x else "Usunięty")
            h_df = h_df[['created_at', 'produkt', 'typ_operacji', 'ilosc', 'notatka']]
            h_df['created_at'] = pd.to_datetime(h_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
            st.table(h_df.sort_values(by='created_at', ascending=False))
        else:
            st.info("Brak wpisów w historii.")
    except:
        st.warning("Aby korzystać z tej funkcji, utwórz tabelę 'historia' w swojej bazie Supabase.")
        st.code("""
        CREATE TABLE historia (
            id int8 PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
            created_at timestamptz DEFAULT now(),
            produkt_id int8 REFERENCES produkty(id),
            typ_operacji text,
            ilosc int8,
            notatka text
        );
        """)

# ... (Sekcje Kategorie i Raporty pozostają jak w poprzednim kodzie) ...
