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
    # Pobieramy produkty wraz z zagnieżdżoną nazwą kategorii
    res = supabase.table("produkty").select("id, nazwa, liczba, cena, kategoria_id, kategorie(nazwa)").execute()
    return res.data

# --- 3. MENU BOCZNE ---
st.sidebar.title("Nawigacja")
menu = st.sidebar.radio("Wybierz sekcję:", ["📦 Produkty", "📂 Kategorie", "📊 Stan Magazynowy"])

# --- 4. SEKCJA: KATEGORIE ---
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

# --- 5. SEKCJA: PRODUKTY ---
elif menu == "📦 Produkty":
    st.title("Zarządzanie Produktami")
    
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
                        new_prod = {"nazwa": p_name, "liczba": p_qty, "cena": p_price, "kategoria_id": p_cat['id']}
                        supabase.table("produkty").insert(new_prod).execute()
                        st.success(f"Dodano produkt: {p_name}")
                        st.rerun()

    st.divider()
    st.subheader("Aktualny spis produktów")
    products_data = get_products()
    
    if products_data:
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
        
        st.subheader("🗑️ Usuń produkt")
        prod_to_del = st.selectbox("Wybierz produkt", options=products_data, format_func=lambda x: x['nazwa'])
        if st.button("Usuń wybrany produkt"):
            supabase.table("produkty").delete().eq("id", prod_to_del['id']).execute()
            st.rerun()
    else:
        st.info("Brak produktów w magazynie.")

# --- 6. SEKCJA: STAN MAGAZYNOWY (RAPORTY) ---
elif menu == "📊 Stan Magazynowy":
    st.title("📊 Analityka i Stan Magazynowy")
    
    data = get_products()
    if not data:
        st.info("Brak produktów do analizy.")
    else:
        df = pd.DataFrame(data)
        df['wartosc_brutto'] = df['liczba'] * df['cena']
        
        # Statystyki
        m1, m2, m3 = st.columns(3)
        m1.metric("Wartość magazynu", f"{df['wartosc_brutto'].sum():,.2f} zł")
        m2.metric("Łączna ilość sztuk", int(df['liczba'].sum()))
        m3.metric("Liczba pozycji (SKU)", len(df))

        st.divider()
        
        # Szybka aktualizacja
        st.subheader("🔄 Szybka korekta ilości")
        col_a, col_b = st.columns(2)
        selected_p = col_a.selectbox("Produkt", options=data, format_func=lambda x: f"{x['nazwa']} (Stan: {x['liczba']})")
        new_qty = col_b.number_input("Nowy stan", value=int(selected_p['liczba']), min_value=0)
        
        if st.button("Zapisz zmianę"):
            supabase.table("produkty").update({"liczba": new_qty}).eq("id", selected_p['id']).execute()
            st.success("Zaktualizowano!")
            st.rerun()

        st.divider()
        
        # Wykres i Alerty
        c_left, c_right = st.columns(2)
        with c_left:
            st.subheader("📈 Wartość wg kategorii")
            df['kat_nazwa'] = df['kategorie'].apply(lambda x: x['nazwa'] if x else "Brak")
            chart_data = df.groupby('kat_nazwa')['wartosc_brutto'].sum()
            st.bar_chart(chart_data)
            
        with c_right:
            st.subheader("⚠️ Niskie stany")
            prog = st.slider("Próg (szt.)", 0, 20, 5)
            low_stock = df[df['liczba'] < prog][['nazwa', 'liczba']]
            if not low_stock.empty:
                st.dataframe(low_stock, use_container_width=True)
            else:
                st.success("Wszystko pod kontrolą.")
