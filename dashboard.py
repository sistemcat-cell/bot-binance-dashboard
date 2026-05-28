import streamlit as st
import pandas as pd
import os
import subprocess
import psutil
import requests
import plotly.graph_objects as go

from streamlit_autorefresh import st_autorefresh
from config import INTERVAL

# CONFIGURACION PAGINA
st.set_page_config(
    page_title="Dashboard Bot Binance",
    page_icon="📊",
    layout="wide"
)

# ESTILO BINANCE
st.markdown("""
<style>

.stApp {
    background-color: #0e1117;
    color: white;
}

[data-testid="stMetricValue"] {
    color: #00ff99;
    font-size: 38px;
    font-weight: bold;
}

[data-testid="stMetricLabel"] {
    color: white;
    font-size: 18px;
    font-weight: bold;
}

h1, h2, h3 {
    color: #f0b90b;
}

</style>
""", unsafe_allow_html=True)

st.title("📊 Dashboard Bot Binance")
st_autorefresh(
    interval=60000,
    key="dashboardrefresh"
)
col_start, col_stop = st.columns(2)

with col_start:

    if st.button("🚀 Iniciar Bot"):

        subprocess.Popen(
            ["python", "main.py"]
        )

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

# PAR
symbol = "bitcoin"

url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"

params = {
    "vs_currency": "usd",
    "days": "1",
    "interval": "daily"
}

response = requests.get(
    url,
    params=params,
    timeout=10
)

data = response.json()

if "prices" not in data:
    st.error("CoinGecko no devolvió precios en este momento.")
    st.write(data)
    st.stop()

prices = data["prices"]

df = pd.DataFrame(
    prices,
    columns=["time", "close"]
)

df["close"] = df["close"].astype(float)

df["open"] = df["close"]
df["high"] = df["close"]
df["low"] = df["close"]

# COLUMNAS
columnas = [
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "quote_asset_volume",
    "trades",
    "taker_buy_base",
    "taker_buy_quote",
    "ignore"
]

# DATAFRAME
df = pd.DataFrame(data, columns=columnas)

# PRECIO NUMERICO
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

# PRECIO ACTUAL
precio_actual = round(df["close"].iloc[-1], 2)

st.metric("BTCUSDT", precio_actual)
# PNL
archivo = "historial.csv"

ganancia_total = 0
balance_inicial = 1000
balance_actual = balance_inicial

if os.path.exists(archivo):

    historial = pd.read_csv(
        archivo,
        names=["Fecha", "Par", "Precio", "RSI", "Señal"]
    )

    compras = historial[
        historial["Señal"] == "COMPRA"
    ]

    ventas = historial[
        historial["Señal"] == "VENTA"
    ]

    total_operaciones = min(
        len(compras),
        len(ventas)
    )

    for i in range(total_operaciones):

        compra = compras.iloc[i]["Precio"]
        venta = ventas.iloc[i]["Precio"]

        ganancia_total += venta - compra

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Operaciones",
            total_operaciones
        )

    with col2:

        st.metric(
            "PnL Total",
            round(ganancia_total, 2)
        )

    with col3:

        st.metric(
             "Balance",
            round(balance_actual, 2)
        )

# GRAFICO
# GRAFICO
fig = go.Figure()

# VELAS JAPONESAS
fig.add_trace(go.Candlestick(
    x=df.index,
    open=df["open"].astype(float),
    high=df["high"].astype(float),
    low=df["low"].astype(float),
    close=df["close"].astype(float),
    name="Velas"
))

# EMA 9
fig.add_trace(go.Scatter(
    x=df.index,
    y=df["EMA9"],
    mode="lines",
    name="EMA 9"
))

# EMA 21
fig.add_trace(go.Scatter(
    x=df.index,
    y=df["EMA21"],
    mode="lines",
    name="EMA 21"
))

# ESTILO
fig.update_layout(
    template="plotly_dark",
    xaxis_rangeslider_visible=False,
    height=700
)
# HISTORIAL
archivo = "historial.csv"

if os.path.exists(archivo):

    historial = pd.read_csv(
        archivo,
        names=["Fecha", "Par", "Precio", "RSI", "Señal"]
    )

    # COMPRAS
    compras = historial[
        historial["Señal"] == "COMPRA"
    ]

    # VENTAS
    ventas = historial[
        historial["Señal"] == "VENTA"
    ]

    # PUNTOS COMPRA
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

    # PUNTOS VENTA
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

# MOSTRAR GRAFICO
st.plotly_chart(
    fig,
    use_container_width=True
)

# RSI
st.subheader("📈 RSI")

st.line_chart(df["RSI"])

# TABLA HISTORIAL
if os.path.exists(archivo):

    st.subheader("📋 Historial")

    st.dataframe(
        historial,
        use_container_width=True
    )
