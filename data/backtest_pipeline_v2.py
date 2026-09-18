"""
Pipeline de backtesting v2 -- fuentes de datos mixtas por estrategia.

CAMBIOS vs. la v1 (backtest_pipeline.py):
1. Fix de raíz: antes, cada bloque de 1 hora (V11, V12...) se leía como
   DOS velas de 30 min sueltas, así que un mismo quiebre se podía contar
   varias veces (esto era la causa del Falso_Gap con n=108 inflado, y
   afectaba potencialmente a VV11 también). Ahora se agregan las 2 velas
   de 30 min de cada bloque en 1 sola vela horaria antes de detectar nada
   -- una fila por bloque por día, como el curso realmente lo define.
2. Tres fuentes de datos en vez de una, cada estrategia usa la que le
   corresponde (ver tabla en CLAUDE_BACKTESTING_V2.md):
   - 30 min (60 días, límite gratis de Yahoo) -> VV11, V10_roja, Falso_Gap
   - 1 hora (730 días, límite gratis de Yahoo) -> SMA_hora
   - Diaria (varios años, sin límite práctico)  -> SMA_dia

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

# --- horizontes de evaluación de resultado, por fuente de datos ---
HORIZON_BLOQUES = 3      # ~3 bloques hacia adelante para VV11/V10_roja/Falso_Gap
HORIZON_HORAS_1H = 3     # ~3 horas hacia adelante para SMA_hora
HORIZON_HORAS_DIA = 4    # ~4 horas hacia adelante (mismo día) para SMA_dia

WIN_ATR_MULT = 0.4
LOOKBACK_CANAL = 8           # bloques/velas hacia atrás para buscar canal (30min agregado a bloques, y 1h)
TOLERANCIA_LINEA = 0.0015

BLOQUES_DEF = [
    ("V10", time(9, 30), time(10, 0)),
    ("V11", time(10, 0), time(11, 0)),
    ("V12", time(11, 0), time(12, 0)),
    ("V1", time(12, 0), time(13, 0)),
    ("V2", time(13, 0), time(14, 0)),
    ("V3", time(14, 0), time(15, 0)),
    ("V4", time(15, 0), time(16, 0)),
]
ORDEN_BLOQUES = [b[0] for b in BLOQUES_DEF]


def asignar_bloque(ts):
    t = ts.time()
    for nombre, ini, fin in BLOQUES_DEF:
        if ini <= t < fin:
            return nombre
    return None


def _normalizar(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    df.index = pd.to_datetime(df.index)
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    df.index = df.index.tz_convert("America/New_York")
    return df.rename(columns={"Open": "o", "High": "h", "Low": "l", "Close": "c", "Volume": "v"})


def fetch_30m(ticker):
    print(f"[{ticker}] Descargando 30m (60d)...")
    df = yf.download(ticker, period="60d", interval="30m", prepost=False, progress=False, auto_adjust=False)
    if df.empty:
        raise RuntimeError(f"Sin datos 30m para {ticker}")
    df = _normalizar(df)
    df["bloque"] = [asignar_bloque(ts) for ts in df.index]
    df = df[df["bloque"].notna()].copy()
    print(f"  {len(df)} velas de 30 min.")
    return df


def fetch_1h(ticker):
    print(f"[{ticker}] Descargando 1h (730d)...")
    df = yf.download(ticker, period="730d", interval="60m", prepost=False, progress=False, auto_adjust=False)
    if df.empty:
        raise RuntimeError(f"Sin datos 1h para {ticker}")
    df = _normalizar(df)
    print(f"  {len(df)} velas de 1 hora.")
    return df


def fetch_daily(ticker):
    print(f"[{ticker}] Descargando diario (5y)...")
    df = yf.download(ticker, period="5y", interval="1d", progress=False, auto_adjust=False)
    if df.empty:
        raise RuntimeError(f"Sin datos diarios para {ticker}")
    df = _normalizar(df)
    print(f"  {len(df)} velas diarias.")
    return df


def construir_velas_bloque(df30):
    """Agrega las velas de 30 min en UNA vela por bloque por día (V10 queda
    igual, de 30 min; V11-V4 se arman juntando sus 2 sub-velas de 30 min)."""
    filas = []
    df30 = df30.copy()
    df30["fecha_dia"] = df30.index.date
    for (dia, bloque), grupo in df30.groupby(["fecha_dia", "bloque"]):
        grupo = grupo.sort_index()
        filas.append({
            "ts": grupo.index[0],
            "fecha_dia": dia,
            "bloque": bloque,
            "o": grupo["o"].iloc[0],
            "h": grupo["h"].max(),
            "l": grupo["l"].min(),
            "c": grupo["c"].iloc[-1],
            "v": grupo["v"].sum(),
        })
    out = pd.DataFrame(filas).set_index("ts").sort_index()
    out["orden_bloque"] = out["bloque"].map({b: i for i, b in enumerate(ORDEN_BLOQUES)})
    return out


def compute_atr(df, periodo=14):
    tr = pd.concat([
        df["h"] - df["l"],
        (df["h"] - df["c"].shift()).abs(),
        (df["l"] - df["c"].shift()).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(periodo).mean()


def compute_vol_avg_por_bloque(df_bloques):
    df_bloques = df_bloques.copy()
    df_bloques["vol_avg_bloque"] = np.nan
    for bloque in df_bloques["bloque"].unique():
        mask = df_bloques["bloque"] == bloque
        df_bloques.loc[mask, "vol_avg_bloque"] = df_bloques.loc[mask, "v"].expanding().mean().shift(1)
    df_bloques["vol_pct_avg"] = (df_bloques["v"] / df_bloques["vol_avg_bloque"]) * 100
    return df_bloques


def buscar_linea(vals, tipo):
    """vals: array de máximos (resistencia) o mínimos (soporte), en orden
    cronológico. Devuelve (valido, valor_linea_extrapolado_al_siguiente_punto)."""
    if len(vals) < 5:
        return False, None
    extremos = []
    for j in range(1, len(vals) - 1):
        if tipo == "resistencia" and vals[j] >= vals[j - 1] and vals[j] >= vals[j + 1]:
            extremos.append(j)
        elif tipo == "soporte" and vals[j] <= vals[j - 1] and vals[j] <= vals[j + 1]:
            extremos.append(j)
    if len(extremos) < 2:
        return False, None
    j1, j2 = extremos[0], extremos[-1]
    if j2 <= j1:
        return False, None
    v1, v2 = vals[j1], vals[j2]
    slope = (v2 - v1) / (j2 - j1)

    def linea(j):
        return v1 + slope * (j - j1)

    for j in range(j1, j2 + 1):
        limite = linea(j) * (1 + TOLERANCIA_LINEA if tipo == "resistencia" else 1 - TOLERANCIA_LINEA)
        if tipo == "resistencia" and vals[j] > limite:
            return False, None
        if tipo == "soporte" and vals[j] < limite:
            return False, None

    return True, v1 + slope * ((len(vals) - 1) - j1)


# ---------------------------------------------------------------------
# Detección sobre VELAS DE BLOQUE (30 min agregado) -> VV11, V10_roja, Falso_Gap
# ---------------------------------------------------------------------

def detectar_por_dia_bloques(df_bloques):
    """Recorre día por día (una sola pasada, evita el doble conteo de raíz
    porque cada bloque ya es único) y devuelve la lista de casos crudos
    (sin evaluar resultado todavía) para VV11, V10_roja y Falso_Gap."""
    casos = []
    for dia, grupo in df_bloques.groupby("fecha_dia"):
        grupo = grupo.sort_values("orden_bloque")
        filas = list(grupo.itertuples())
        v10 = next((r for r in filas if r.bloque == "V10"), None)
        v11 = next((r for r in filas if r.bloque == "V11"), None)

        # --- VV11 ---
        if v10 is not None and v11 is not None:
            v10_verde = v10.c > v10.o
            v11_verde = v11.c > v11.o
            if v10_verde and v11_verde:
                idx_v11 = df_bloques.index.get_loc(v11.Index)
                hist_max = df_bloques["h"].iloc[max(0, idx_v11 - LOOKBACK_CANAL):idx_v11].values
                valido, linea_val = buscar_linea(hist_max, "resistencia")
                if valido and v11.c > linea_val and not pd.isna(v11.vol_pct_avg) and v11.vol_pct_avg > 50:
                    casos.append({"estrategia": "VV11", "direccion": "CALL",
                                  "idx": idx_v11, "ts": v11.Index})

        # --- V10_roja --- (canal bajista ya vigente ANTES de V10, y V10 roja)
        if v10 is not None:
            idx_v10 = df_bloques.index.get_loc(v10.Index)
            hist_max = df_bloques["h"].iloc[max(0, idx_v10 - LOOKBACK_CANAL):idx_v10].values
            valido, _ = buscar_linea(hist_max, "resistencia")
            if valido and v10.c < v10.o:
                casos.append({"estrategia": "V10_roja", "direccion": "PUT",
                              "idx": idx_v10, "ts": v10.Index})

        # --- Falso_Gap --- (solo el PRIMER bloque del día que rompe el piso de V10)
        if v10 is not None and v10.c > v10.o:
            piso = v10.l
            for r in filas:
                if r.bloque == "V10":
                    continue
                if r.c < r.o and r.c < piso:
                    idx_r = df_bloques.index.get_loc(r.Index)
                    casos.append({"estrategia": "Falso_Gap", "direccion": "PUT",
                                  "idx": idx_r, "ts": r.Index})
                    break  # una sola vez por día, la primera ruptura

    return casos


def evaluar_resultado_bloques(df_bloques, idx, direccion):
    if idx + HORIZON_BLOQUES >= len(df_bloques):
        return None
    entry = df_bloques["c"].iloc[idx]
    futuro = df_bloques["c"].iloc[idx + HORIZON_BLOQUES]
    atr = compute_atr(df_bloques).iloc[idx]
    if pd.isna(atr) or atr == 0:
        return None
    return _clasificar(entry, futuro, atr, direccion)


def _clasificar(entry, futuro, atr, direccion):
    move_pct = (futuro / entry - 1) * 100
    umbral_pct = (atr / entry) * 100 * WIN_ATR_MULT
    if direccion == "CALL":
        resultado = "gana" if move_pct > umbral_pct else ("pierde" if move_pct < -umbral_pct else "neutral")
    else:
        resultado = "gana" if move_pct < -umbral_pct else ("pierde" if move_pct > umbral_pct else "neutral")
    return {"move_pct": round(float(move_pct), 3), "resultado": resultado}


def velas_contexto_df(df, idx, n=10):
    ini = max(0, idx - n + 1)
    sub = df.iloc[ini:idx + 1]
    return [
        {"o": round(float(r.o), 2), "h": round(float(r.h), 2),
         "l": round(float(r.l), 2), "c": round(float(r.c), 2)}
        for r in sub.itertuples()
    ], idx - ini


# ---------------------------------------------------------------------
# Detección sobre VELAS DE 1 HORA (730 días) -> SMA_hora
# ---------------------------------------------------------------------

def detectar_sma_hora_serie(df1h):
    df1h = df1h.copy()
    df1h["sma20"] = df1h["c"].rolling(20).mean()
    df1h["sma40"] = df1h["c"].rolling(40).mean()
    df1h["atr14"] = compute_atr(df1h)
    df1h["vol_avg20"] = df1h["v"].rolling(20).mean().shift(1)
    df1h["vol_pct_avg"] = (df1h["v"] / df1h["vol_avg20"]) * 100

    casos = []
    for i in range(45, len(df1h) - HORIZON_HORAS_1H):
        sma20, sma40 = df1h["sma20"].iloc[i], df1h["sma40"].iloc[i]
        if pd.isna(sma20) or pd.isna(sma40) or not (sma20 > sma40):
            continue
        cerca_sma40 = (abs(df1h["l"].iloc[i] - sma40) / sma40 < 0.003 or
                       abs(df1h["l"].iloc[i - 1] - sma40) / sma40 < 0.003)
        if not cerca_sma40:
            continue
        if not (df1h["c"].iloc[i] > df1h["o"].iloc[i]):
            continue
        hist_max = df1h["h"].iloc[max(0, i - LOOKBACK_CANAL):i].values
        valido, linea_val = buscar_linea(hist_max, "resistencia")
        if not valido or df1h["c"].iloc[i] <= linea_val:
            continue
        if pd.isna(df1h["vol_pct_avg"].iloc[i]) or df1h["vol_pct_avg"].iloc[i] <= 50:
            continue
        resultado = evaluar_resultado_bloques(df1h.rename(columns={}), i, "CALL") \
            if False else _clasificar(df1h["c"].iloc[i], df1h["c"].iloc[i + HORIZON_HORAS_1H],
                                       df1h["atr14"].iloc[i], "CALL") if not pd.isna(df1h["atr14"].iloc[i]) and df1h["atr14"].iloc[i] != 0 else None
        if resultado is None:
            continue
        velas, idx_g = velas_contexto_df(df1h, i)
        casos.append({
            "estrategia": "SMA_hora", "direccion": "CALL", "ts": df1h.index[i],
            "velas": velas, "vela_gatillo_idx": idx_g,
            "volumen_pct_avg": round(float(df1h["vol_pct_avg"].iloc[i]), 1),
            **resultado,
        })
    return casos


# ---------------------------------------------------------------------
# Detección SMA_dia: SMA100/200 DIARIO real + confirmación horaria
# ---------------------------------------------------------------------

def detectar_sma_dia_serie(df_diario, df1h):
    df_diario = df_diario.copy()
    df_diario["sma100"] = df_diario["c"].rolling(100).mean()
    df_diario["sma200"] = df_diario["c"].rolling(200).mean()
    map100 = {d.date(): v for d, v in df_diario["sma100"].items()}
    map200 = {d.date(): v for d, v in df_diario["sma200"].items()}

    df1h = df1h.copy()
    df1h["atr14"] = compute_atr(df1h)
    df1h["vol_avg20"] = df1h["v"].rolling(20).mean().shift(1)
    df1h["vol_pct_avg"] = (df1h["v"] / df1h["vol_avg20"]) * 100
    df1h["fecha_dia"] = df1h.index.date

    casos = []
    for i in range(45, len(df1h) - HORIZON_HORAS_DIA):
        dia = df1h["fecha_dia"].iloc[i]
        sma100, sma200 = map100.get(dia), map200.get(dia)
        if (sma100 is None or pd.isna(sma100)) and (sma200 is None or pd.isna(sma200)):
            continue
        precio = df1h["c"].iloc[i]
        cerca = False
        for sma in [sma100, sma200]:
            if sma is not None and not pd.isna(sma) and precio >= sma * 0.995 and abs(precio - sma) / sma < 0.01:
                cerca = True
        if not cerca or not (df1h["c"].iloc[i] > df1h["o"].iloc[i]):
            continue
        hist_max = df1h["h"].iloc[max(0, i - LOOKBACK_CANAL):i].values
        valido, linea_val = buscar_linea(hist_max, "resistencia")
        if not valido or df1h["c"].iloc[i] <= linea_val:
            continue
        atr = df1h["atr14"].iloc[i]
        if pd.isna(atr) or atr == 0:
            continue
        resultado = _clasificar(precio, df1h["c"].iloc[i + HORIZON_HORAS_DIA], atr, "CALL")
        velas, idx_g = velas_contexto_df(df1h, i)
        casos.append({
            "estrategia": "SMA_dia", "direccion": "CALL", "ts": df1h.index[i],
            "velas": velas, "vela_gatillo_idx": idx_g,
            "volumen_pct_avg": None if pd.isna(df1h["vol_pct_avg"].iloc[i]) else round(float(df1h["vol_pct_avg"].iloc[i]), 1),
            **resultado,
        })
    return casos


def main():
    todos = []

    for ticker in TICKERS:
        # --- fuente 30 min -> VV11, V10_roja, Falso_Gap ---
        df30 = fetch_30m(ticker)
        df_bloques = construir_velas_bloque(df30)
        df_bloques = compute_vol_avg_por_bloque(df_bloques)
        crudos = detectar_por_dia_bloques(df_bloques)
        for caso in crudos:
            resultado = evaluar_resultado_bloques(df_bloques, caso["idx"], caso["direccion"])
            if resultado is None:
                continue
            velas, idx_g = velas_contexto_df(df_bloques, caso["idx"])
            fila = df_bloques.iloc[caso["idx"]]
            todos.append({
                "id": f"{ticker}-{caso['estrategia']}-{caso['idx']}",
                "ticker": ticker, "estrategia": caso["estrategia"], "direccion": caso["direccion"],
                "fecha": str(caso["ts"]), "velas": velas, "vela_gatillo_idx": idx_g,
                "volumen_pct_avg": None if pd.isna(fila.get("vol_pct_avg", np.nan)) else round(float(fila["vol_pct_avg"]), 1),
                **resultado,
            })

        # --- fuente 1h -> SMA_hora ---
        df1h = fetch_1h(ticker)
        for c in detectar_sma_hora_serie(df1h):
            todos.append({"id": f"{ticker}-SMA_hora-{len(todos)}", "ticker": ticker,
                           "fecha": str(c["ts"]), **{k: v for k, v in c.items() if k != "ts"}})

        # --- fuente diaria + 1h -> SMA_dia ---
        df_diario = fetch_daily(ticker)
        for c in detectar_sma_dia_serie(df_diario, df1h):
            todos.append({"id": f"{ticker}-SMA_dia-{len(todos)}", "ticker": ticker,
                           "fecha": str(c["ts"]), **{k: v for k, v in c.items() if k != "ts"}})

    print(f"\nTotal de casos detectados: {len(todos)}")

    ESTRATEGIAS_DIR = {"VV11": "CALL", "SMA_hora": "CALL", "SMA_dia": "CALL",
                        "V10_roja": "PUT", "Falso_Gap": "PUT"}
    stats = {}
    for nombre, direccion in ESTRATEGIAS_DIR.items():
        casos = [c for c in todos if c["estrategia"] == nombre]
        n_casos = len(casos)
        if n_casos == 0:
            stats[nombre] = {"n": 0, "aviso": "Sin casos detectados en el período."}
            continue
        ganan = sum(1 for c in casos if c["resultado"] == "gana")
        pierden = sum(1 for c in casos if c["resultado"] == "pierde")
        neutral = n_casos - ganan - pierden
        avg_move = float(np.mean([c["move_pct"] for c in casos]))
        stats[nombre] = {
            "n": n_casos, "direccion": direccion,
            "pct_gana": round(100 * ganan / n_casos, 1),
            "pct_pierde": round(100 * pierden / n_casos, 1),
            "pct_neutral": round(100 * neutral / n_casos, 1),
            "movimiento_promedio_pct": round(avg_move, 2),
            "confiabilidad": "baja (n<20, orientativo, no concluyente)" if n_casos < 20 else "moderada (sigue siendo un período relativamente corto)",
        }
        print(f"  {nombre}: n={n_casos}  gana={stats[nombre]['pct_gana']}%  "
              f"pierde={stats[nombre]['pct_pierde']}%  neutral={stats[nombre]['pct_neutral']}%")

    with open("backtest_stats.json", "w", encoding="utf-8") as f:
        json.dump({"generado": pd.Timestamp.now(tz="America/New_York").isoformat(),
                    "fuentes": {"VV11": "30min (60d)", "V10_roja": "30min (60d)",
                                 "Falso_Gap": "30min (60d)", "SMA_hora": "1h (730d)",
                                 "SMA_dia": "diario (5y) + 1h para confirmación"},
                    "tickers": TICKERS, "estrategias": stats}, f, ensure_ascii=False, indent=2)

    casos_finales = []
    for nombre in ESTRATEGIAS_DIR:
        casos_finales.extend([c for c in todos if c["estrategia"] == nombre][:60])

    with open("backtest_cases.json", "w", encoding="utf-8") as f:
        json.dump(casos_finales, f, ensure_ascii=False, indent=2)

    print(f"\nGuardado: backtest_stats.json, backtest_cases.json ({len(casos_finales)} casos)")


if __name__ == "__main__":
    main()
