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
import streamlit as st
from supabase import create_client, Client
import pandas as pd

# --- KONFIGURACJA POŁĄCZENIA ---
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Błąd konfiguracji: Sprawdź Secrets.")
    st.stop()

# --- FUNKCJE ---
def get_products():
    res = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
    return res.data

# --- BOCZNY PANEL ---
menu = st.sidebar.radio("Menu", ["📦 Produkty", "📂 Kategorie", "📊 Stan Magazynowy"])

# ... (Sekcje Produkty i Kategorie pozostają bez zmian z poprzedniego kroku) ...

# ==========================================
# SEKCJA: STAN MAGAZYNOWY (NOWA)
# ==========================================
if menu == "📊 Stan Magazynowy":
    st.title("📊 Analityka i Stan Magazynowy")
    
    data = get_products()
    if not data:
        st.info("Brak danych do analizy.")
    else:
        df = pd.DataFrame(data)
        
        # Obliczenia finansowe
        df['wartosc_brutto'] = df['liczba'] * df['cena']
        calkowita_wartosc = df['wartosc_brutto'].sum()
        laczna_ilosc = df['liczba'].sum()

        # Metryki na górze strony
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Łączna wartość magazynu", f"{calkowita_wartosc:,.2f} zł")
        col_m2.metric("Liczba wszystkich sztuk", laczna_ilosc)
        col_m3.metric("Liczba asortymentu", len(df))

        st.divider()

        # --- SZYBKA AKTUALIZACJA ILOŚCI ---
        st.subheader("🔄 Szybka korekta stanów")
        col_a, col_b = st.columns(2)
        
        selected_p = col_a.selectbox("Wybierz produkt", options=data, format_func=lambda x: f"{x['nazwa']} (Obecnie: {x['liczba']})")
        new_qty = col_b.number_input("Nowa ilość", value=int(selected_p['liczba']), min_value=0)
        
        if st.button("Aktualizuj stan"):
            supabase.table("produkty").update({"liczba": new_qty}).eq("id", selected_p['id']).execute()
            st.success(f"Zaktualizowano {selected_p['nazwa']} na {new_qty} szt.")
            st.rerun()

        st.divider()

        # --- TABELA ALARMOWA (NISKI STAN) ---
        st.subheader("⚠️ Alerty magazynowe")
        progiem_alarmowy = st.slider("Pokaż produkty z ilością poniżej:", 0, 50, 5)
        low_stock = df[df['liczba'] < progiem_alarmowy][['nazwa', 'liczba', 'cena']]
        
        if not low_stock.empty:
            st.warning(f"Znaleziono {len(low_stock)} produktów wymagających zamówienia!")
            st.table(low_stock)
        else:
            st.success("Wszystkie stany magazynowe są w normie.")

        # --- WYKRES STRUKTURY ---
        st.subheader("📈 Udział kategorii w magazynie")
        # Wyciągamy nazwę kategorii z zagnieżdżonego słownika
        df['kat_nazwa'] = df['kategorie'].apply(lambda x: x['nazwa'] if x else "Brak")
        chart_data = df.groupby('kat_nazwa')['wartosc_brutto'].sum()
        st.bar_chart(chart_data)
