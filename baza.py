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
