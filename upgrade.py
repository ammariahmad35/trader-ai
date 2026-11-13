S = chr(47)
H = "https:" + S * 2

s = open("app.py").read()
old_news = f'    news_u = H + "min-api." + "cryptocompare.com" + S + "data" + S + "v2" + S + "news" + S + "?lang=EN"\n    try:\n        news = requests.get(news_u, timeout=10).json().get("Data", [])\n        for n in news[:5]:\n            t = n.get("title", "")\n            u = n.get("url", "")'
new_news = f'    news_u = H + "cointelegraph.com" + S + "rss"\n    try:\n        import xml.etree.ElementTree as ET\n        xml_data = requests.get(news_u, headers={{"User-Agent": "Mozilla/5.0"}}, timeout=10).text\n        items = ET.fromstring(xml_data).findall(".//item")[:6]\n        for n in items:\n            t = n.findtext("title", "")\n            u = n.findtext("link", "")'
s = s.replace(old_news, new_news).replace('str(n.get("id"))', 't[:30]')
open("app.py", "w").write(s)

dash = """import streamlit as st
import sqlite3, pandas as pd

st.set_page_config(page_title="منظومة الملك للذكاء الاصطناعي", layout="wide")
st.title("👑 لوحة تحكم منظومة الذكاء الاصطناعي للعملات الرقمية")

conn = sqlite3.connect("crypto_system.db")
bal = pd.read_sql_query("SELECT bal FROM wallet WHERE id=1", conn).iloc[0, 0]
alerts_cnt = pd.read_sql_query("SELECT COUNT(*) FROM alerts", conn).iloc[0, 0]
trades_cnt = pd.read_sql_query("SELECT COUNT(*) FROM trades", conn).iloc[0, 0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("💰 الرصيد التجريبي", f"${bal:.2f} USDT")
c2.metric("🤖 حالة البوتات الخمسة", "نشط 24/7 ✅")
c3.metric("🔔 الفرص والتنبيهات", f"{alerts_cnt}")
c4.metric("📈 الصفقات التجريبية", f"{trades_cnt}")

st.divider()
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("🚀 آخر العملات والأخبار المكتشفة")
    df_a = pd.read_sql_query("SELECT bot AS البوت, sym AS الرمز, dt AS الوقت FROM alerts ORDER BY id DESC LIMIT 20", conn)
    st.dataframe(df_a, use_container_width=True)
with col_b:
    st.subheader("💼 سجل التداول التجريبي (رأس مال 1000$)")
    df_t = pd.read_sql_query("SELECT sym AS العملة, side AS النوع, price AS السعر, usd AS المبلغ, status AS الحالة, dt AS الوقت FROM trades ORDER BY id DESC LIMIT 20", conn)
    st.dataframe(df_t, use_container_width=True)
conn.close()
"""
open("dashboard.py", "w").write(dash)
print("READY!")
