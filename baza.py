import streamlit as st
from supabase import create_client, Client

# --- KONFIGURACJA POŁĄCZENIA ---
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Błąd konfiguracji: Sprawdź Secrets w Streamlit Cloud.")
    st.stop()

st.set_page_config(page_title="System Magazynowy", layout="wide")

# --- FUNKCJE POBIERANIA DANYCH ---
def get_categories():
    res = supabase.table("kategorie").select("id, nazwa").execute()
    return res.data

def get_products_with_categories():
    # Pobieramy produkty wraz z nazwami ich kategorii (JOIN)
    res = supabase.table("produkty").select("id, nazwa, liczba, cena, kategoria_id, kategorie(nazwa)").execute()
    return res.data

# --- BOCZNY PANEL NAWIGACYJNY ---
menu = st.sidebar.radio("Menu", ["📦 Produkty", "📂 Kategorie"])

# ==========================================
# SEKCJA: KATEGORIE
# ==========================================
if menu == "📂 Kategorie":
    st.title("Zarządzanie Kategoriami")
    
    col1, col2 = st.columns([1, 1])
    
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
            cat_to_del = st.selectbox("Wybierz do usunięcia", options=cats, format_func=lambda x: x['nazwa'])
            if st.button("Usuń", type="primary"):
                try:
                    supabase.table("kategorie").delete().eq("id", cat_to_del['id']).execute()
                    st.success("Usunięto!")
                    st.rerun()
                except:
                    st.error("Nie można usunąć – kategoria zawiera produkty!")

    st.divider()
    st.subheader("Lista kategorii")
    st.dataframe(get_categories(), use_container_width=True)

# ==========================================
# SEKCJA: PRODUKTY
# ==========================================
elif menu == "📦 Produkty":
    st.title("Zarządzanie Produktami")
    
    # --- FORMULARZ DODAWANIA PRODUKTU ---
    with st.expander("➕ Dodaj nowy produkt"):
        categories = get_categories()
        if not categories:
            st.warning("Najpierw dodaj przynajmniej jedną kategorię!")
        else:
            with st.form("add_prod", clear_on_submit=True):
                c1, c2 = st.columns(2)
                p_name = c1.text_input("Nazwa produktu")
                p_cat = c2.selectbox("Kategoria", options=categories, format_func=lambda x: x['nazwa'])
                
                p_qty = c1.number_input("Liczba (szt.)", min_value=0, step=1)
                p_price = c2.number_input("Cena", min_value=0.0, format="%.2f")
                
                if st.form_submit_button("Dodaj produkt do magazynu"):
                    if p_name:
                        new_prod = {
                            "nazwa": p_name,
                            "liczba": p_qty,
                            "cena": p_price,
                            "kategoria_id": p_cat['id']
                        }
                        supabase.table("produkty").insert(new_prod).execute()
                        st.success(f"Dodano produkt: {p_name}")
                        st.rerun()

    st.divider()

    # --- WYŚWIETLANIE PRODUKTÓW ---
    st.subheader("Aktualny stan magazynowy")
    products_data = get_products_with_categories()
    
    if products_data:
        # Przekształcenie danych do ładnej tabeli
        display_data = []
        for p in products_data:
            display_data.append({
                "ID": p['id'],
                "Nazwa": p['nazwa'],
                "Ilość": p['liczba'],
                "Cena": f"{p['cena']} zł",
                "Kategoria": p['kategorie']['nazwa'] if p['kategorie'] else "Brak"
            })
        st.table(display_data)
        
        # --- USUWANIE PRODUKTU ---
        st.subheader("🗑️ Usuń produkt")
        prod_to_del = st.selectbox("Wybierz produkt", options=products_data, format_func=lambda x: x['nazwa'])
        if st.button("Usuń wybrany produkt"):
            supabase.table("produkty").delete().eq("id", prod_to_del['id']).execute()
            st.success("Produkt usunięty.")
            st.rerun()
    else:
        st.info("Brak produktów w magazynie.")
