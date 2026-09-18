"""
Pipeline de backtesting real para las 5 estrategias del playbook (FPalacios LLC).

QUÉ HACE:
1. Descarga velas de 30 minutos de SPY y QQQ (máximo permitido gratis por
   Yahoo Finance: 60 días atrás).
2. Reconstruye los bloques del curso (V10=9:30-10:00, V11=10:00-11:00, ...)
   a partir de las velas de 30 min.
3. Calcula SMA20/40 (hora) y SMA100/200 (día), volumen promedio por bloque.
4. Recorre el histórico y detecta, para cada barra, si se cumplió el
   checklist COMPLETO de alguna de las 5 estrategias (misma lógica que
   notas-curso-bolsa-newlife.md sección 9).
5. Por cada caso detectado, mide qué pasó con el precio en las siguientes
   horas y lo clasifica en gana/pierde/neutral.
6. Guarda dos archivos:
   - backtest_stats.json    -> probabilidades agregadas por estrategia
   - backtest_cases.json    -> casos individuales (velas + resultado real),
                               para el modo interactivo de revisión

LIMITACIÓN A TENER EN CUENTA (léela antes de confiar en los resultados):
Con ~60 días de historia, el número de casos por estrategia puede ser
bajo (a veces menos de 15-20). Con muestras así de chicas, un "63% de
acierto" puede ser ruido estadístico, no una ventaja real. Los stats
incluyen el tamaño de muestra (n) para que se lea con esa cautela --
NO tomar ninguna probabilidad en serio con n < 20, como regla general.

INSTALACIÓN (una sola vez):
    pip3 install yfinance pandas numpy --break-system-packages

USO:
    python3 backtest_pipeline.py
"""
import json
import warnings
from datetime import time

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

try:
    import yfinance as yf
except ImportError:
    raise SystemExit(
        "Falta yfinance. Instálalo con:\n"
        "  pip3 install yfinance pandas numpy --break-system-packages"
    )

TICKERS = ["SPY", "QQQ"]
INTERVAL = "30m"
PERIOD = "60d"          # máximo gratis de Yahoo para intervalos de 30 min
HORIZON_BARS = 6        # ~3 horas hacia adelante (6 x 30 min) para medir el resultado
WIN_ATR_MULT = 0.4      # gana si el movimiento supera 0.4x el ATR en la dirección esperada
LOOKBACK_CANAL = 16     # barras hacia atrás para buscar el canal/línea de tendencia
TOLERANCIA_LINEA = 0.0015  # 0.15% de tolerancia al validar que las velas respetan la línea

BLOQUES = [
    ("V10", time(9, 30), time(10, 0)),
    ("V11", time(10, 0), time(11, 0)),
    ("V12", time(11, 0), time(12, 0)),
    ("V1", time(12, 0), time(13, 0)),
    ("V2", time(13, 0), time(14, 0)),
    ("V3", time(14, 0), time(15, 0)),
    ("V4", time(15, 0), time(16, 0)),
]


def asignar_bloque(ts):
    t = ts.time()
    for nombre, ini, fin in BLOQUES:
        if ini <= t < fin:
            return nombre
    return None


def fetch_data(ticker):
    print(f"Descargando {ticker} ({INTERVAL}, {PERIOD})...")
    df = yf.download(ticker, period=PERIOD, interval=INTERVAL,
                      prepost=False, progress=False, auto_adjust=False)
    if df.empty:
        raise RuntimeError(f"Yahoo Finance no devolvió datos para {ticker}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    df.index = pd.to_datetime(df.index)
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    df.index = df.index.tz_convert("America/New_York")
    df = df.rename(columns={"Open": "o", "High": "h", "Low": "l", "Close": "c", "Volume": "v"})
    df["bloque"] = [asignar_bloque(ts) for ts in df.index]
    df = df[df["bloque"].notna()].copy()
    print(f"  {len(df)} velas de 30 min obtenidas.")
    return df


def compute_indicators(df):
    df["sma20"] = df["c"].rolling(20).mean()
    df["sma40"] = df["c"].rolling(40).mean()

    tr = pd.concat([
        df["h"] - df["l"],
        (df["h"] - df["c"].shift()).abs(),
        (df["l"] - df["c"].shift()).abs(),
    ], axis=1).max(axis=1)
    df["atr14"] = tr.rolling(14).mean()

    # SMA diaria (100/200) calculada sobre cierres diarios, reindexada a intradía
    diario = df["c"].resample("1D").last().dropna()
    sma100_d = diario.rolling(100).mean()
    sma200_d = diario.rolling(200).mean()
    df["fecha_dia"] = df.index.date
    map100 = {d.date(): v for d, v in sma100_d.items()}
    map200 = {d.date(): v for d, v in sma200_d.items()}
    df["sma100_dia"] = df["fecha_dia"].map(map100)
    df["sma200_dia"] = df["fecha_dia"].map(map200)

    # volumen promedio histórico por bloque (V10 se compara solo con otros V10, etc.)
    df["vol_avg_bloque"] = np.nan
    for bloque in df["bloque"].unique():
        mask = df["bloque"] == bloque
        df.loc[mask, "vol_avg_bloque"] = df.loc[mask, "v"].expanding().mean().shift(1)
    df["vol_pct_avg"] = (df["v"] / df["vol_avg_bloque"]) * 100
    return df


def cierre_dia_anterior(df, i):
    dia_actual = df["fecha_dia"].iloc[i]
    prev = df[df["fecha_dia"] < dia_actual]
    if prev.empty:
        return None
    return prev["c"].iloc[-1]


def es_primera_barra_del_dia(df, i):
    return df["bloque"].iloc[i] == "V10" and (
        i == 0 or df["fecha_dia"].iloc[i] != df["fecha_dia"].iloc[i - 1]
    )


def buscar_linea(df, i, tipo):
    """Busca una línea de tendencia válida (2+ toques) en las LOOKBACK_CANAL
    barras previas al índice i. tipo='resistencia' (sobre máximos) o
    'soporte' (sobre mínimos). Devuelve (valido, valor_linea_en_i) o (False, None)."""
    ini = max(0, i - LOOKBACK_CANAL)
    ventana = df.iloc[ini:i]
    if len(ventana) < 5:
        return False, None

    col = "h" if tipo == "resistencia" else "l"
    vals = ventana[col].values
    idxs = ventana.index

    # picos/valles locales dentro de la ventana
    extremos = []
    for j in range(1, len(vals) - 1):
        if tipo == "resistencia" and vals[j] >= vals[j - 1] and vals[j] >= vals[j + 1]:
            extremos.append(j)
        elif tipo == "soporte" and vals[j] <= vals[j - 1] and vals[j] <= vals[j + 1]:
            extremos.append(j)

    if len(extremos) < 2:
        return False, None

    # probar la línea que conecta el primer y último extremo válido
    j1, j2 = extremos[0], extremos[-1]
    if j2 <= j1:
        return False, None
    v1, v2 = vals[j1], vals[j2]
    slope = (v2 - v1) / (j2 - j1)

    def linea(j):
        return v1 + slope * (j - j1)

    # validar: ninguna barra debe traspasar la línea de forma relevante
    for j in range(j1, j2 + 1):
        limite = linea(j) * (1 + TOLERANCIA_LINEA if tipo == "resistencia" else 1 - TOLERANCIA_LINEA)
        if tipo == "resistencia" and vals[j] > limite:
            return False, None
        if tipo == "soporte" and vals[j] < limite:
            return False, None

    valor_en_i = v1 + slope * ((len(vals) - 1) - j1)
    return True, valor_en_i


def detectar_vv11(df, i):
    if df["bloque"].iloc[i] != "V11":
        return False
    idx_v10 = i - 1
    if idx_v10 < 0 or df["bloque"].iloc[idx_v10] != "V10":
        return False
    v10_verde = df["c"].iloc[idx_v10] > df["o"].iloc[idx_v10]
    v11_verde = df["c"].iloc[i] > df["o"].iloc[i]
    if not (v10_verde and v11_verde):
        return False
    valido, linea_val = buscar_linea(df, i, "resistencia")
    if not valido:
        return False
    ruptura = df["c"].iloc[i] > linea_val
    vol_ok = df["vol_pct_avg"].iloc[i] > 50
    return ruptura and vol_ok


def detectar_sma_hora(df, i):
    if pd.isna(df["sma20"].iloc[i]) or pd.isna(df["sma40"].iloc[i]):
        return False
    if not (df["sma20"].iloc[i] > df["sma40"].iloc[i]):
        return False
    sma40 = df["sma40"].iloc[i]
    cerca_sma40 = abs(df["l"].iloc[i] - sma40) / sma40 < 0.003 or abs(df["l"].iloc[i - 1] - sma40) / sma40 < 0.003
    if not cerca_sma40:
        return False
    verde = df["c"].iloc[i] > df["o"].iloc[i]
    if not verde:
        return False
    valido, linea_val = buscar_linea(df, i, "resistencia")
    if not valido:
        return False
    ruptura = df["c"].iloc[i] > linea_val
    vol_ok = df["vol_pct_avg"].iloc[i] > 50
    return ruptura and vol_ok


def detectar_sma_dia(df, i):
    sma100, sma200 = df["sma100_dia"].iloc[i], df["sma200_dia"].iloc[i]
    if pd.isna(sma100) and pd.isna(sma200):
        return False
    precio = df["c"].iloc[i]
    cerca_soporte_dia = False
    for sma in [sma100, sma200]:
        if not pd.isna(sma) and abs(precio - sma) / sma < 0.01 and precio >= sma * 0.995:
            cerca_soporte_dia = True
    if not cerca_soporte_dia:
        return False
    verde = df["c"].iloc[i] > df["o"].iloc[i]
    if not verde:
        return False
    valido, linea_val = buscar_linea(df, i, "resistencia")
    if not valido:
        return False
    return df["c"].iloc[i] > linea_val


def detectar_v10_roja(df, i):
    if df["bloque"].iloc[i] != "V10":
        return False
    valido, linea_val = buscar_linea(df, i - 1, "resistencia") if i > 0 else (False, None)
    if not valido:
        return False
    roja = df["c"].iloc[i] < df["o"].iloc[i]
    return roja


def detectar_falso_gap(df, i):
    # busca, dentro del mismo día, si hubo una V10 verde y la barra actual
    # (posterior, roja) rompe el piso (low) de esa V10. Solo cuenta la
    # PRIMERA barra que rompe ese piso ese día -- sin este resguardo, cada
    # barra subsiguiente que sigue cerrando por debajo también calificaba,
    # contando el mismo quiebre varias veces (hasta 8 en un día).
    dia = df["fecha_dia"].iloc[i]
    del_dia = df[df["fecha_dia"] == dia]
    v10s = del_dia[del_dia["bloque"] == "V10"]
    if v10s.empty:
        return False
    v10 = v10s.iloc[0]
    if not (v10["c"] > v10["o"]):
        return False
    idx_v10_pos = df.index.get_loc(v10s.index[0])
    if i <= idx_v10_pos:
        return False
    roja = df["c"].iloc[i] < df["o"].iloc[i]
    rompe_piso = df["c"].iloc[i] < v10["l"]
    if not (roja and rompe_piso):
        return False
    # la barra anterior debe seguir sobre el piso (o ser la propia V10):
    # así solo se detecta la primera ruptura, no las que la siguen.
    anterior_sobre_piso = df["c"].iloc[i - 1] >= v10["l"]
    return anterior_sobre_piso


def evaluar_resultado(df, i, direccion):
    if i + HORIZON_BARS >= len(df):
        return None
    entry = df["c"].iloc[i]
    futuro = df["c"].iloc[i + HORIZON_BARS]
    atr = df["atr14"].iloc[i]
    if pd.isna(atr) or atr == 0:
        return None
    move_pct = (futuro / entry - 1) * 100
    umbral_pct = (atr / entry) * 100 * WIN_ATR_MULT
    if direccion == "CALL":
        resultado = "gana" if move_pct > umbral_pct else ("pierde" if move_pct < -umbral_pct else "neutral")
    else:
        resultado = "gana" if move_pct < -umbral_pct else ("pierde" if move_pct > umbral_pct else "neutral")
    return {"move_pct": round(float(move_pct), 3), "resultado": resultado}


def velas_contexto(df, i, n=10):
    ini = max(0, i - n + 1)
    sub = df.iloc[ini:i + 1]
    return [
        {"o": round(float(r.o), 2), "h": round(float(r.h), 2),
         "l": round(float(r.l), 2), "c": round(float(r.c), 2)}
        for r in sub.itertuples()
    ], i - ini


ESTRATEGIAS = [
    ("VV11", detectar_vv11, "CALL"),
    ("SMA_hora", detectar_sma_hora, "CALL"),
    ("SMA_dia", detectar_sma_dia, "CALL"),
    ("V10_roja", detectar_v10_roja, "PUT"),
    ("Falso_Gap", detectar_falso_gap, "PUT"),
]


def main():
    todos_los_casos = []
    for ticker in TICKERS:
        df = fetch_data(ticker)
        df = compute_indicators(df)
        n = len(df)
        for i in range(30, n):
            for nombre, detector, direccion in ESTRATEGIAS:
                try:
                    ok = detector(df, i)
                except Exception:
                    ok = False
                if not ok:
                    continue
                resultado = evaluar_resultado(df, i, direccion)
                if resultado is None:
                    continue
                velas, idx_gatillo = velas_contexto(df, i, n=10)
                todos_los_casos.append({
                    "id": f"{ticker}-{nombre}-{i}",
                    "ticker": ticker,
                    "estrategia": nombre,
                    "direccion": direccion,
                    "fecha": str(df.index[i]),
                    "velas": velas,
                    "vela_gatillo_idx": idx_gatillo,
                    "volumen_pct_avg": None if pd.isna(df["vol_pct_avg"].iloc[i]) else round(float(df["vol_pct_avg"].iloc[i]), 1),
                    **resultado,
                })

    print(f"\nTotal de casos detectados: {len(todos_los_casos)}")

    stats = {}
    for nombre, _, direccion in ESTRATEGIAS:
        casos = [c for c in todos_los_casos if c["estrategia"] == nombre]
        n_casos = len(casos)
        if n_casos == 0:
            stats[nombre] = {"n": 0, "aviso": "Sin casos detectados en el período — revisar umbrales."}
            continue
        ganan = sum(1 for c in casos if c["resultado"] == "gana")
        pierden = sum(1 for c in casos if c["resultado"] == "pierde")
        neutral = n_casos - ganan - pierden
        avg_move = float(np.mean([c["move_pct"] for c in casos]))
        stats[nombre] = {
            "n": n_casos,
            "direccion": direccion,
            "pct_gana": round(100 * ganan / n_casos, 1),
            "pct_pierde": round(100 * pierden / n_casos, 1),
            "pct_neutral": round(100 * neutral / n_casos, 1),
            "movimiento_promedio_pct": round(avg_move, 2),
            "confiabilidad": "baja (n<20, tratar como orientativo, no concluyente)" if n_casos < 20 else "moderada (sigue siendo un período corto)",
        }
        print(f"  {nombre}: n={n_casos}  gana={stats[nombre]['pct_gana']}%  "
              f"pierde={stats[nombre]['pct_pierde']}%  neutral={stats[nombre]['pct_neutral']}%")

    with open("backtest_stats.json", "w", encoding="utf-8") as f:
        json.dump({"generado": pd.Timestamp.now(tz="America/New_York").isoformat(),
                    "periodo_datos": PERIOD, "tickers": TICKERS, "estrategias": stats}, f,
                   ensure_ascii=False, indent=2)

    # limitar casos por estrategia para no disparar el tamaño del archivo
    casos_finales = []
    for nombre, _, _ in ESTRATEGIAS:
        casos_estrategia = [c for c in todos_los_casos if c["estrategia"] == nombre]
        casos_finales.extend(casos_estrategia[:60])

    with open("backtest_cases.json", "w", encoding="utf-8") as f:
        json.dump(casos_finales, f, ensure_ascii=False, indent=2)

    print(f"\nGuardado: backtest_stats.json, backtest_cases.json ({len(casos_finales)} casos)")


if __name__ == "__main__":
    main()
