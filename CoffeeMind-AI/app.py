import streamlit as st
import pandas as pd
import sqlite3

# --- 1. SIRA: SAYFA AYARLARI ---
st.set_page_config(page_title="CoffeeMind AI ☕", page_icon="☕", layout="wide")

# --- VERİTABANI AYARLARI ---
conn = sqlite3.connect("coffeemind.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS puanlar (id INTEGER PRIMARY KEY AUTOINCREMENT, kahve_adi TEXT, puan INTEGER)")
conn.commit()

# --- CSV VERİSİNİ YÜKLEME ---
@st.cache_data
def veriyi_yukle():
    return pd.read_csv("coffee_data.csv")

df_kahve = veriyi_yukle()

# --- AKILLI FİLTRELEME ALGORİTMASI ---
def kahve_bul(mod, sertlik, tatlilik, sut, hava):
    filtre = (df_kahve['mod'] == mod) | (df_kahve['sertlik'] == sertlik) | (df_kahve['sut'] == sut)
    eslesenler = df_kahve[filtre]
    
    if not eslesenler.empty:
        en_iyi_kahve = eslesenler.iloc[0]
        return en_iyi_kahve.to_dict()
    else:
        return df_kahve.iloc[0].to_dict()

# --- YAN PANEL (SIDEBAR) - VERİ ANALİTİĞİ ---
st.sidebar.title("📊 Topluluk İstatistikleri")
st.sidebar.write("Veritabanından canlı olarak hesaplanan kullanıcı tercihleri.")

# Veritabanından verileri çekip analiz edelim
df_puanlar = pd.read_sql_query("SELECT kahve_adi, puan FROM puanlar", conn)

if not df_puanlar.empty:
    # Toplam oy sayısı
    toplam_oy = len(df_puanlar)
    st.sidebar.metric(label="💬 Toplam Verilen Oy", value=f"{toplam_oy} Kez")
    
    st.sidebar.write("---")
    st.sidebar.subheader("⭐ En Popüler Kahveler")
    
    # Kahve bazında ortalama puanları hesapla ve en yüksekleri sırala
    ortalama_puanlar = df_puanlar.groupby("kahve_adi")["puan"].mean().reset_index()
    ortalama_puanlar = ortalama_puanlar.sort_values(by="puan", ascending=False)
    
    # Grafik verisi
    grafik_verisi = ortalama_puanlar.set_index("kahve_adi")
    st.sidebar.bar_chart(grafik_verisi)
    
    # En yüksek puanlı kahveyi metrik olarak göster
    en_iyi_kahve_adi = ortalama_puanlar.iloc[0]["kahve_adi"]
    en_iyi_puan = round(ortalama_puanlar.iloc[0]["puan"], 1)
    st.sidebar.metric(label="🏆 Favori Kahve", value=en_iyi_kahve_adi, delta=f"{en_iyi_puan} / 5.0 Puan")
else:
    st.sidebar.info("Henüz veritabanında oy bulunmuyor. İlk kahve önerisini alıp puan vererek grafiği canlandırabilirsin! 🚀")

# --- ANA PANEL ---
st.title("☕ CoffeeMind AI")
st.subheader("CSV, SQLite ve Veri Görselleştirme Destekli Akıllı Kahve Önerici")
st.write("---")

# Sorular
mod = st.radio("1. Bugün nasıl hissediyorsun?", ["😊 Mutlu", "😴 Uykulu", "🤯 Yoğun", "🥶 Serin bir şey istiyorum", "📚 Ders çalışacağım", "❤️ Romantik"])
sertlik = st.radio("2. Kahveyi nasıl seversin?", ["Sert", "Orta", "Hafif"], horizontal=True)
tatlilik = st.radio("3. Tatlılık oranı?", ["Şekersiz", "Az Tatlı", "Tatlı"], horizontal=True)
sut = st.radio("4. Süt istiyor musun?", ["Sütlü", "Sütsüz"], horizontal=True)
hava = st.selectbox("5. Bugünkü hava nasıl?", ["☀️ Güneşli", "🌧️ Yağmurlu", "❄️ Soğuk"])

st.write("---")

if st.button("✨ Bana Kahve Öner! ✨", use_container_width=True):
    sonuc = kahve_bul(mod, sertlik, tatlilik, sut, hava)
    st.session_state["onerilen_kahve"] = sonuc["isim"]
    
    st.balloons()
    
    st.markdown(f"## 🎯 Bugünkü Önerimiz: **{sonuc['isim']}**")
    st.markdown(f"### ⭐ Sistem Puanı: {sonuc['puan']}/10")
    st.markdown(f"### 💡 Neden?")
    st.write(sonuc["neden"])
    
    col1, col2, col3 = st.columns(3)
    with col1: st.metric(label="🔥 Kalori", value=sonuc["kalori"])
    with col2: st.metric(label="⚡ Kafein", value=sonuc["kafein"])
    with col3: st.metric(label="⏱️ Süre", value=sonuc["sure"])

# Puanlama Sistemi
if "onerilen_kahve" in st.session_state:
    st.write("---")
    st.markdown(f"### ⭐ **{st.session_state['onerilen_kahve']}** kahvesini beğendin mi?")
    puan = st.slider("Puan Ver:", 1, 5, 5)
    if st.button("Puanı Kaydet"):
        cursor.execute("INSERT INTO puanlar (kahve_adi, puan) VALUES (?, ?)", (st.session_state['onerilen_kahve'], puan))
        conn.commit()
        st.toast("Puanın SQLite veritabanına kaydedildi! 🎉")
        st.rerun()