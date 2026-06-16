import streamlit as st
import requests
import json
import pandas as pd
import urllib3

urllib3.disable_warnings()

# ==============================================================
# 1. ANALİZ MOTORU (Senin orijinal algoritman korundu)
# ==============================================================
class AtlasBrain:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.tradingview.com/"
        })
        # AI ağırlıkları varsayılan olarak eklendi
        self.ai_weights = {"RSI_W": 1.0, "MACD_W": 1.0, "VOL_W": 1.0, "MOM_W": 1.0}

    def fetch_market_data(self, tf="D", range_limit=100):
        url = "https://scanner.tradingview.com/turkey/scan"
        payload = {
            "filter": [{"left": "volume", "operation": "greater", "right": 10000}],
            "columns": ["name", "close", "change", "volume", "RSI", "CCI20", "P.SAR", "relative_volume_10d_calc", "EMA10", "EMA20", "ATR", "ADX", "high", "low", "Recommend.All", "open", "High.1M", "Low.1M", "MACD.macd", "MACD.signal", "Mom"],
            "sort": {"sortBy": "change", "sortOrder": "desc"}, "range": [0, range_limit], "resolution": tf
        }
        try:
            r = self.session.post(url, json=payload, timeout=12)
            return r.json().get("data", [])
        except: 
            return []

    def calculate_ai_score(self, d):
        try:
            rsi, macd, msig, rvol = d[4], d[18], d[19], d[7]
            score = 0.0
            w = self.ai_weights
            if 50 < rsi < 70: score += 25 * w['RSI_W']
            if macd > msig: score += 25 * w['MACD_W']
            if rvol > 1.1: score += 25 * w['VOL_W']
            if d[8] > d[9]: score += 25
            return round(score, 1)
        except: 
            return 0.0

    def generate_smart_analysis(self, sym):
        try:
            sym_upper = sym.upper().strip()
            if not ".IS" in sym_upper and len(sym_upper) <= 5: 
                sym_upper = f"{sym_upper}.IS"
            
            data = self.fetch_market_data("D", 200)
            d = next((i['d'] for i in data if str(i['d'][0]).split(":")[-1] == sym_upper.replace(".IS","")), None)
            
            if not d: 
                return f"❌ {sym_upper} bulunamadı veya veri çekilemedi.", False
            
            close, score = d[1], self.calculate_ai_score(d)
            atr = d[10]
            karar = "GÜÇLÜ AL 🚀" if score > 75 else "AL 👍" if score > 50 else "BEKLE ⏳"
            
            report = f"""
### ATLAS AI ANALİZ: {sym_upper}
---
* **FIYAT:** {close:.2f} ₺ (%{d[2]:.2f})
* **AI SKORU:** {score}/100
* **KARAR:** **{karar}**
* **HEDEF:** {close+atr*2:.2f} ₺
* **STOP:** {close-atr*1.5:.2f} ₺
            """
            return report, True
        except Exception as e: 
            return f"Hata: {str(e)}", False

# ==============================================================
# 2. STREAMLIT MOBİL UYUMLU ARAYÜZ
# ==============================================================
st.set_page_config(page_title="Atlas Pro iOS", page_icon="📈", layout="centered")

st.title("📈 ATLAS PRO v58")
st.markdown("*iOS ve Safari için optimize edilmiş Web Sürümü*")

# AtlasBrain sınıfını bellekte tut (hızı artırır)
@st.cache_resource
def get_brain():
    return AtlasBrain()

brain = get_brain()

# Tıpkı orijinal kodundaki gibi sekmeler oluşturduk
tab1, tab2 = st.tabs(["📊 Taramalar", "💬 Chat & Analiz"])

with tab1:
    st.subheader("Günün Fırsatları (AI > 60)")
    if st.button("Piyasayı Tara 🔄", use_container_width=True):
        with st.spinner("TradingView verileri çekiliyor..."):
            data = brain.fetch_market_data()
            results = []
            for item in data:
                d = item['d']
                score = brain.calculate_ai_score(d)
                if score >= 60:
                    results.append({
                        "Sembol": d[0].split(":")[-1],
                        "Fiyat": f"{d[1]:.2f}",
                        "Değişim (%)": f"{d[2]:.1f}",
                        "Skor": score
                    })
            
            if results:
                df = pd.DataFrame(results)
                # Tabloyu iOS ekranına tam sığacak şekilde çizdir
                st.dataframe(df.sort_values(by="Skor", ascending=False), use_container_width=True, hide_index=True)
            else:
                st.info("Şu an kriterlere uyan hisse bulunamadı.")

with tab2:
    st.subheader("Hızlı Hisse Analizi")
    hisse_kodu = st.text_input("Hisse Kodunu Girin (Örn: THYAO):")
    
    if st.button("Analiz Et 🔍", use_container_width=True):
        if hisse_kodu:
            with st.spinner(f"{hisse_kodu.upper()} analiz ediliyor..."):
                report, success = brain.generate_smart_analysis(hisse_kodu)
                if success:
                    st.success("Analiz Tamamlandı!")
                    st.markdown(report)
                else:
                    st.error(report)
        else:
            st.warning("Lütfen bir hisse kodu yazın.")
