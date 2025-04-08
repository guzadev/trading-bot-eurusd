import requests
import pandas as pd
import time
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os

load_dotenv()

# === CONFIGURACION ===
API_KEY = os.getenv("API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_IDS = os.getenv("TELEGRAM_CHAT_IDS").split(",")
SYMBOL = 'EURUSD'

# === FUNCIONES DE UTILIDAD ===
def send_telegram_message(message):
    print(f"[TELEGRAM] Enviando mensaje: {message}")
    for chat_id in TELEGRAM_CHAT_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message
        }
        try:
            response = requests.post(url, data=payload)
            print(f"[TELEGRAM] Mensaje enviado a {chat_id} (estado: {response.status_code})")
        except Exception as e:
            print(f"[ERROR] No se pudo enviar mensaje a {chat_id}: {e}")

def get_hourly_data():
    print("[API] Solicitando datos horarios (1h)...")
    now = datetime.now(timezone.utc)
    today = now.date()

    start = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc) + timedelta(hours=0)  # 00:00 UTC
    four_am = start + timedelta(hours=4)  # 04:00 UTC exacto
    end = four_am

    url = f"https://marketdata.tradermade.com/api/v1/timeseries?currency={SYMBOL}&api_key={API_KEY}&start_date={start.strftime('%Y-%m-%dT%H:%M:%S')}Z&end_date={end.strftime('%Y-%m-%dT%H:%M:%S')}Z&interval=hourly"
    response = requests.get(url)
    print(f"[API] Código de respuesta: {response.status_code}")
    try:
        data = response.json()
        if 'quotes' not in data:
            raise ValueError("No se encontraron 'quotes' en la respuesta de la API.")
        df = pd.DataFrame(data['quotes'])
        df['date'] = pd.to_datetime(df['date'])
        df = df[df['date'].dt.hour < 4]  #filtro final
        print("[INFO] Velas utilizadas para el rango asiático:")
        print(df[['date', 'open', 'high', 'low', 'close']])
        return df
    except Exception as e:
        print(f"[ERROR] Error al parsear JSON de datos horarios: {e}")
        print(f"[DEBUG] Contenido de respuesta: {response.text}")
        raise

def get_minute_data():
    print("[API] Solicitando datos de 1 minuto...")
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0) - timedelta(minutes=1)
    past = now - timedelta(minutes=5)

    url = f"https://marketdata.tradermade.com/api/v1/timeseries?currency={SYMBOL}&api_key={API_KEY}&start_date={past.strftime('%Y-%m-%dT%H:%M:%S')}Z&end_date={now.strftime('%Y-%m-%dT%H:%M:%S')}Z&interval=minute"
    response = requests.get(url)
    print(f"[API] Código de respuesta: {response.status_code}")
    try:
        data = response.json()
        if 'quotes' not in data:
            raise ValueError("No se encontraron 'quotes' en la respuesta de la API de 1m.")
        df = pd.DataFrame(data['quotes'])
        df['date'] = pd.to_datetime(df['date'])
        return df
    except Exception as e:
        print(f"[ERROR] Error al parsear JSON de datos de 1 minuto: {e}")
        print(f"[DEBUG] Contenido de respuesta: {response.text}")
        raise

def consolidate_to_5m(df):
    print("[DATA] Consolidando datos a velas de 5 minutos...")
    df.set_index('date', inplace=True)
    df_5m = pd.DataFrame()
    df_5m['open'] = df['open'].resample('5min').first()
    df_5m['high'] = df['high'].resample('5min').max()
    df_5m['low'] = df['low'].resample('5min').min()
    df_5m['close'] = df['close'].resample('5min').last()
    df_5m.dropna(inplace=True)
    return df_5m

# === OBTENER RANGO ASIATICO ===
def get_asian_range():
    df = get_hourly_data()
    max_high = df['high'].max()
    min_low = df['low'].min()
    print(f"[00-04 UTC] Rango Asiatico - MAX: {max_high} / MIN: {min_low}")
    return max_high, min_low

# === MAIN LOOP ===
def run_bot():
    print("[BOT] Iniciando bot de trading EUR/USD...")

    while datetime.now(timezone.utc).hour < 4:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Esperando a que termine sesión asiática...")
        time.sleep(60)

    try:
        max_high, min_low = get_asian_range()
    except Exception as e:
        print(f"[ERROR] No se pudo obtener rango asiático: {e}")
        return

    breakout_notified = False
    last_breakout = None

    while True:
        now = datetime.now(timezone.utc)

        if now.hour >= 9:
            print(f"[{now.strftime('%H:%M:%S')}] Fin del monitoreo. Hora límite alcanzada (09:00 UTC). Cerrando bot.")
            break

        try:
            df_min = get_minute_data()
            df_5m = consolidate_to_5m(df_min)
            if df_5m.empty:
                print("[WARNING] No se pudo generar vela 5m, esperando próxima...")
                time.sleep(300)
                continue

            last_close = df_5m.iloc[-1]['close']
            last_high = df_5m.iloc[-1]['high']
            last_low = df_5m.iloc[-1]['low']

            if last_high > max_high and not breakout_notified :
                msg = f"Ruptura ALCISTA detectada: {last_high} > {max_high}"
                send_telegram_message(msg)
                print(msg)
                breakout_notified = True
                last_breakout = "up"

            elif last_low < min_low and not breakout_notified:
                msg = f"Ruptura BAJISTA detectada: {last_low} < {min_low}"
                send_telegram_message(msg)
                print(msg)
                breakout_notified = True
                last_breakout = "down"

            elif min_low <= last_close <= max_high and last_breakout:
                msg = f"[REINGRESO] Precio {last_close} dentro de ({min_low}, {max_high}) tras ruptura {last_breakout}"
                send_telegram_message(msg)
                print(msg)
                print("[BOT] Reingreso detectado. Finalizando ejecución del bot.")
                break

        except Exception as e:
            print(f"[ERROR] Error en el bucle principal: {e}")

        time.sleep(300)

if __name__ == '__main__':
    run_bot()
