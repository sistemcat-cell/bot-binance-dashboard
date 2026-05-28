import streamlit as st
import pandas as pd
import os
import requests
import plotly.graph_objects as go


from streamlit_autorefresh import st_autorefresh
from config import BASE_URL, INTERVAL

st.set_page_config(
    page_title="Dashboard Bot Binance",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>

.stApp {
    background-color: #0e1117;
    color: white;
}

[data-testid="stMetricValue"] {
    color: #00ff99;
}

h1, h2, h3 {
    color: #f0b90b;
}

</style>
""", unsafe_allow_html=True)



col_start, col_stop = st.columns(2)

with col_start:
    if st.button("🚀 Iniciar Bot"):
        subprocess.Popen(["python", "main.py"])
        st.success("Bot iniciado")

with col_stop:
    if st.button("🛑 Detener Bot"):
        for process in psutil.process_iter():
            try:
                cmdline = process.cmdline()
                if "main.py" in " ".join(cmdline):
                    process.kill()
            except:
                pass

        st.warning("Bot detenido")

st_autorefresh(
    interval=5000,
    key="dashboardrefresh"
)

symbol = "BTCUSDT"

url = f"{BASE_URL}/api/v3/klines"

params = {
    "symbol": symbol,
    "interval": INTERVAL,
    "limit": 100
}

response = requests.get(url, params=params)

data = response.json()



df["close"] = df["close"].astype(float)

# EMA
df["EMA9"] = df["close"].ewm(span=9).mean()
df["EMA21"] = df["close"].ewm(span=21).mean()

# RSI
delta = df["close"].diff()

gain = delta.where(delta > 0, 0)
loss = -delta.where(delta < 0, 0)

avg_gain = gain.rolling(window=14).mean()
avg_loss = loss.rolling(window=14).mean()

rs = avg_gain / avg_loss

df["RSI"] = 100 - (100 / (1 + rs))

# PRECIO
precio_actual = round(df["close"].iloc[-1], 2)

st.metric("BTCUSDT", precio_actual)

# GRAFICO
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df.index,
    y=df["close"],
    mode="lines",
    name="Precio"
))

fig.add_trace(go.Scatter(
    x=df.index,
    y=df["EMA9"],
    mode="lines",
    name="EMA 9"
))

fig.add_trace(go.Scatter(
    x=df.index,
    y=df["EMA21"],
    mode="lines",
    name="EMA 21"
))

# HISTORIAL
archivo = "historial.csv"

if os.path.exists(archivo):

    historial = pd.read_csv(
        archivo,
        names=["Fecha", "Par", "Precio", "RSI", "Señal"]
    )

    compras = historial[historial["Señal"] == "COMPRA"]

    ventas = historial[historial["Señal"] == "VENTA"]

    fig.add_trace(go.Scatter(
        x=compras.index,
        y=compras["Precio"],
        mode="markers",
        name="COMPRA",
        marker=dict(
            size=12,
            color="green",
            symbol="triangle-up"
        )
    ))

    fig.add_trace(go.Scatter(
        x=ventas.index,
        y=ventas["Precio"],
        mode="markers",
        name="VENTA",
        marker=dict(
            size=12,
            color="red",
            symbol="triangle-down"
        )
    ))

st.plotly_chart(
    fig,
    use_container_width=True
)

st.subheader("📈 RSI")

st.line_chart(df["RSI"])

if os.path.exists(archivo):

    st.subheader("📋 Historial")

    st.dataframe(
        historial,
        use_container_width=True
    )