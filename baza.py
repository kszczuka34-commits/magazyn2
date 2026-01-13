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
