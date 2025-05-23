import requests
import pandas as pd
import time
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from pathlib import Path
import os


# === INTENTA CARGAR VARIABLES DESDE UN ARCHIVO .ENV ESTANDO EN LOCAL ===
try:
    from dotenv import load_dotenv
    if Path(".env").exists():
        load_dotenv()
        print("[INFO] dotenv cargado (modo local)", flush=True)
    else:
        print("[INFO] No se encontró archivo .env, se usan variables de entorno del sistema", flush=True)
except Exception as e:
    print(f"[INFO] dotenv no disponible: {e}", flush=True)


# === FUNCION SEGURA PARA OBTENER VARIABLES OBLIGATORIAS ===
def get_env_var(name):
    value = os.getenv(name)
    if value is None:
        raise ValueError(f"La variable de entorno '{name}' no está definida.")
    return value


# === CONFIGURACION: VARIABLES DE ENTORNO Y SIMBOLO ===
try:
    print("Cargando las variables de entorno", flush=True)
    API_KEY = get_env_var("API_KEY")
    TELEGRAM_TOKEN = get_env_var("TELEGRAM_TOKEN")
    raw_chat_ids = get_env_var("TELEGRAM_CHAT_IDS")
    print("[DEBUG] raw_chat_ids repr:", repr(raw_chat_ids), flush=True)
    TELEGRAM_CHAT_IDS = [chat_id.strip() for chat_id in raw_chat_ids.split(",")]
except Exception as e:
    print(f"[ERROR] Fallo al cargar variables: {e}", flush=True)
    exit(1)
SYMBOL = 'EURUSD'


# === ENVIO DE MENSAJES DE TELEGRAM ===
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


# === OBTENCION DE VELAS DE 1 HORA ===
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


# === OBTENCION DE VELAS DE 1 MINUTO ===
def get_minute_data():
    print("[API] Solicitando datos de 1 minuto...")
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0) - timedelta(minutes=1)
    past = now - timedelta(minutes=105)

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


# === ARMANDO VELAS DE 5 MINUTOS ===
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

    # Esperar hasta que termine sesión asiática (04:00 UTC)
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
    reentry_detected = False
    ema_alert_sent = False

    while True:
        now = datetime.now(timezone.utc)

        if now.hour >= 7:
            print(f"[{now.strftime('%H:%M:%S')}] Fin del monitoreo. Hora límite alcanzada (07:00 UTC). Cerrando bot.")
            break

        try:
            df_min = get_minute_data()
            df_5m = consolidate_to_5m(df_min)
            if df_5m.empty:
                print("[WARNING] No se pudo generar vela 5m, esperando próxima...")
                time.sleep(300)
                continue

            # Calcular EMA 21
            df_5m['ema21'] = df_5m['close'].ewm(span=21, adjust=False).mean()
            
            last_close = df_5m.iloc[-1]['close']
            # last_high = df_5m.iloc[-1]['high']
            # last_low = df_5m.iloc[-1]['low']

            # Evaluar ruptura
            if last_close > max_high and not breakout_notified:
                msg = f"📈 [RUPTURA] ALCISTA detectada: {last_close} > {max_high} ⬆️"
                send_telegram_message(msg)
                print(msg)
                breakout_notified = True
                last_breakout = "alcista"
                print(f"Ruptura {last_breakout}")

            elif last_close < min_low and not breakout_notified:
                msg = f"📉 [RUPTURA] BAJISTA detectada: {last_close} < {min_low} ⬇️"
                send_telegram_message(msg)
                print(msg)
                breakout_notified = True
                last_breakout = "bajista"
                print(f"Ruptura {last_breakout}")

            # Evaluar reingreso
            if min_low < last_close < max_high and last_breakout and not reentry_detected:
                msg = f"🔁 [REINGRESO] Precio {last_close} dentro de ({min_low}, {max_high}) tras ruptura {last_breakout} 👨🏻‍💻"
                send_telegram_message(msg)
                print(msg)
                reentry_detected = True

            # Evaluar cruce de EMA 21
            if len(df_5m) < 2:
                print("[DEBUG] No hay suficientes velas para evaluar cruce de EMA.")
                continue

            if breakout_notified and reentry_detected and not ema_alert_sent:
                previous_close = df_5m.iloc[-2]['close']
                previous_ema = df_5m.iloc[-2]['ema21']
                current_close = df_5m.iloc[-1]['close']
                current_ema21 = df_5m.iloc[-1]['ema21']
                
                if previous_close < previous_ema and current_close > current_ema21:
                    msg = f"🟢 [EMA 21] Cruce ALCISTA de EMA 21: {previous_close} → {current_close}, cruzando {current_ema21:.5f} 🔀"
                    send_telegram_message(msg)
                    print(msg)
                    ema_alert_sent = True
                    print("[BOT] Cruce de EMA detectado. Finalizando ejecución del bot.")
                    break  # Cierra el bot

                elif previous_close > previous_ema and current_close < current_ema21:
                    msg = f"🔴 [EMA 21] Cruce BAJISTA de EMA 21: {previous_close} → {current_close}, cruzando {current_ema21:.5f} 🔀"
                    send_telegram_message(msg)
                    print(msg)
                    ema_alert_sent = True
                    print("[BOT] Cruce de EMA detectado. Finalizando ejecución del bot.")
                    break  # Cierra el bot

        except Exception as e:
            print(f"[ERROR] Error en el bucle principal: {e}")

        time.sleep(300)


# === EJECUCION ===
# Ejecutar siempre, sin depender de __name__ (ideal para Render)
print("Iniciando el main loop principal", flush=True)
run_bot()

