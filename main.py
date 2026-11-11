import os, time, requests, yfinance as yf
import pandas as pd

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = None

def get_chat_id():
    global CHAT_ID
    try:
        r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates").json()
        for u in r.get("result", []):
            if "message" in u:
                CHAT_ID = u["message"]["chat"]["id"]
                return CHAT_ID
    except: pass
    return None

def send(msg):
    if CHAT_ID:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

def get_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = -delta.where(delta < 0, 0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def check():
    df = yf.download("EURUSD=X", period="1d", interval="5m", progress=False)
    if df.empty: return
    close = df['Close'].flatten()
    ema9 = close.ewm(span=9).mean()
    ema21 = close.ewm(span=21).mean()
    rsi = get_rsi(close)
    price = float(close.iloc[-1])
    e9 = float(ema9.iloc[-1]); e21 = float(ema21.iloc[-1])
    e9_prev = float(ema9.iloc[-2]); e21_prev = float(ema21.iloc[-2])
    r = float(rsi.iloc[-1])
    if e9_prev < e21_prev and e9 > e21 and r > 50:
        send(f"🟢 *COMPRA EUR/USD - 5m*\nPrecio: {price:.5f}\nRSI: {r:.1f} - Cruce alcista EMA 9/21\nGestión: Arriesgar 1% - TP 1.5x - SL 1x")
    elif e9_prev > e21_prev and e9 < e21 and r < 50:
        send(f"🔴 *VENTA EUR/USD - 5m*\nPrecio: {price:.5f}\nRSI: {r:.1f} - Cruce bajista EMA 9/21\nGestión: Arriesgar 1% - TP 1.5x - SL 1x")

print("Bot iniciado...")
get_chat_id()
send("✅ Bot de Señales Libertex activado. Analizando EUR/USD en 5m cada 1 min.")
last_signal = 0
while True:
    try:
        if time.time() - last_signal > 900:
            check()
            last_signal = time.time()
    except Exception as e:
        print(e)
    time.sleep(60)
