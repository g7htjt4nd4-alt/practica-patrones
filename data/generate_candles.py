"""
Generador de datasets sintéticos de velas japonesas para la app de práctica.

Por qué sintético y no datos reales:
- Control total sobre la etiqueta correcta (una vela real es ambigua incluso
  para expertos; aquí construimos la vela para que cumpla la definición).
- Sin dependencias de red ni licencias de datos de mercado.
- Reproducible: mismo seed -> mismo dataset -> puedes regenerar si cambias reglas.

Uso:
    python3 generate_candles.py --fase 1 --n-por-patron 10 --seed 42 --out patterns_fase1.json

Formato de salida (patterns_fase1.json):
[
  {
    "id": "m-000",
    "patron_correcto": "martillo",
    "opciones": ["martillo","gancho","doji","marubozu","envolvente_alcista","envolvente_bajista","ninguno"],
    "velas": [ {"o":100.2,"h":100.5,"l":99.1,"c":100.4}, ... ],  # última vela = la vela a identificar
    "vela_objetivo_idx": 4,
    "explicacion": "Mechón largo abajo, cuerpo pequeño arriba: rechazo alcista tras una caída."
  },
  ...
]

Las primeras N-1 velas son "contexto" (una mini-tendencia previa realista);
la última vela (vela_objetivo_idx) es la que ilustra el patrón.
"""
import argparse
import json
import random

PATRONES = [
    "martillo",
    "gancho",
    "marubozu",
    "doji",
    "envolvente_alcista",
    "envolvente_bajista",
    "ninguno",
]

EXPLICACIONES = {
    "martillo": "Mechón largo abajo, cuerpo pequeño arriba, poca o ninguna mecha superior: los vendedores dominaban pero los compradores retomaron el control antes del cierre. Más significativo tras una caída.",
    "gancho": "Mechón largo arriba, cuerpo pequeño abajo: los compradores intentaron subir el precio pero fallaron en sostenerlo. Más significativo tras una subida (zona alta del gráfico).",
    "marubozu": "Cuerpo grande, casi sin mechas: dominio absoluto de una dirección durante todo el período.",
    "doji": "Apertura y cierre casi idénticos: equilibrio total entre compradores y vendedores, máxima incertidumbre.",
    "envolvente_alcista": "El cuerpo de la vela verde 'envuelve' por completo el cuerpo de la vela roja anterior: señal fuerte de reversión al alza.",
    "envolvente_bajista": "El cuerpo de la vela roja 'envuelve' por completo el cuerpo de la vela verde anterior: señal fuerte de reversión a la baja.",
    "ninguno": "Vela normal sin ningún patrón especial de los que estás practicando: cuerpo y mechas moderados, sin dominio claro de ninguna de las partes.",
}


def random_walk_context(n, start_price, vol, rng, drift=0.0):
    """Genera n velas de contexto (mini-tendencia previa) con OHLC realista."""
    velas = []
    price = start_price
    for _ in range(n):
        o = price
        step = rng.gauss(drift, vol)
        c = max(0.5, o * (1 + step))
        high_wick = abs(rng.gauss(0, vol * 0.6))
        low_wick = abs(rng.gauss(0, vol * 0.6))
        h = max(o, c) * (1 + high_wick)
        l = min(o, c) * (1 - low_wick)
        velas.append({"o": round(o, 2), "h": round(h, 2), "l": round(l, 2), "c": round(c, 2)})
        price = c
    return velas


def make_martillo(open_price, vol, rng):
    o = open_price
    body = abs(rng.gauss(vol * 0.3, vol * 0.1)) * o
    c = o + body  # cuerpo pequeño, ligeramente alcista (también válido si es levemente bajista)
    low_wick = abs(rng.gauss(vol * 2.2, vol * 0.4)) * o
    l = min(o, c) - low_wick
    high_wick = abs(rng.gauss(vol * 0.15, vol * 0.05)) * o
    h = max(o, c) + high_wick
    return {"o": round(o, 2), "h": round(h, 2), "l": round(l, 2), "c": round(c, 2)}


def make_gancho(open_price, vol, rng):
    o = open_price
    body = abs(rng.gauss(vol * 0.3, vol * 0.1)) * o
    c = o - body  # cuerpo pequeño, ligeramente bajista
    high_wick = abs(rng.gauss(vol * 2.2, vol * 0.4)) * o
    h = max(o, c) + high_wick
    low_wick = abs(rng.gauss(vol * 0.15, vol * 0.05)) * o
    l = min(o, c) - low_wick
    return {"o": round(o, 2), "h": round(h, 2), "l": round(l, 2), "c": round(c, 2)}


def make_marubozu(open_price, vol, rng):
    o = open_price
    direction = rng.choice([1, -1])
    body = abs(rng.gauss(vol * 2.5, vol * 0.5)) * o
    c = o + direction * body
    tiny = abs(rng.gauss(vol * 0.03, vol * 0.01)) * o
    h = max(o, c) + tiny
    l = min(o, c) - tiny
    return {"o": round(o, 2), "h": round(h, 2), "l": round(l, 2), "c": round(c, 2)}


def make_doji(open_price, vol, rng):
    o = open_price
    c = o + rng.gauss(0, vol * 0.05) * o  # apertura ~= cierre
    wick = abs(rng.gauss(vol * 1.5, vol * 0.4)) * o
    h = max(o, c) + wick
    l = min(o, c) - wick
    return {"o": round(o, 2), "h": round(h, 2), "l": round(l, 2), "c": round(c, 2)}


def make_neutral(open_price, vol, rng):
    o = open_price
    step = rng.gauss(0, vol)
    c = o * (1 + step)
    hw = abs(rng.gauss(0, vol * 0.5))
    lw = abs(rng.gauss(0, vol * 0.5))
    h = max(o, c) * (1 + hw)
    l = min(o, c) * (1 - lw)
    return {"o": round(o, 2), "h": round(h, 2), "l": round(l, 2), "c": round(c, 2)}


def make_envolvente(open_price, vol, rng, alcista=True):
    """Devuelve DOS velas: la previa y la envolvente."""
    o1 = open_price
    body1 = abs(rng.gauss(vol * 1.0, vol * 0.2)) * o1
    if alcista:
        c1 = o1 - body1  # vela previa roja
    else:
        c1 = o1 + body1  # vela previa verde

    # la segunda vela abre dentro/cerca del cuerpo anterior y cierra fuera de él
    o2 = c1 + rng.gauss(0, vol * 0.1) * c1
    extra = abs(rng.gauss(vol * 1.2, vol * 0.2)) * o2
    if alcista:
        c2 = max(o1, c1) + extra  # verde, envuelve la roja anterior
    else:
        c2 = min(o1, c1) - extra  # roja, envuelve la verde anterior

    tiny = abs(rng.gauss(vol * 0.1, vol * 0.03))
    vela1 = {"o": round(o1, 2), "h": round(max(o1, c1) * (1 + tiny), 2),
             "l": round(min(o1, c1) * (1 - tiny), 2), "c": round(c1, 2)}
    vela2 = {"o": round(o2, 2), "h": round(max(o2, c2) * (1 + tiny), 2),
             "l": round(min(o2, c2) * (1 - tiny), 2), "c": round(c2, 2)}
    return vela1, vela2


def generar_ejemplo(patron, idx, base_price_range, vol_range, rng):
    base_price = rng.uniform(*base_price_range)
    vol = rng.uniform(*vol_range)
    n_contexto = rng.randint(3, 5)

    if patron == "envolvente_alcista":
        contexto = random_walk_context(n_contexto, base_price, vol, rng, drift=-vol * 0.3)
        precio_actual = contexto[-1]["c"]
        v1, v2 = make_envolvente(precio_actual, vol, rng, alcista=True)
        velas = contexto[:-1] + [v1, v2] if len(contexto) > 1 else [v1, v2]
        objetivo_idx = len(velas) - 1
    elif patron == "envolvente_bajista":
        contexto = random_walk_context(n_contexto, base_price, vol, rng, drift=vol * 0.3)
        precio_actual = contexto[-1]["c"]
        v1, v2 = make_envolvente(precio_actual, vol, rng, alcista=False)
        velas = contexto[:-1] + [v1, v2] if len(contexto) > 1 else [v1, v2]
        objetivo_idx = len(velas) - 1
    else:
        drift = -vol * 0.3 if patron == "martillo" else (vol * 0.3 if patron == "gancho" else 0.0)
        contexto = random_walk_context(n_contexto, base_price, vol, rng, drift=drift)
        precio_actual = contexto[-1]["c"]
        builder = {
            "martillo": make_martillo,
            "gancho": make_gancho,
            "marubozu": make_marubozu,
            "doji": make_doji,
            "ninguno": make_neutral,
        }[patron]
        objetivo = builder(precio_actual, vol, rng)
        velas = contexto + [objetivo]
        objetivo_idx = len(velas) - 1

    return {
        "id": f"{patron[:3]}-{idx:03d}",
        "patron_correcto": patron,
        "opciones": PATRONES,
        "velas": velas,
        "vela_objetivo_idx": objetivo_idx,
        "explicacion": EXPLICACIONES[patron],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-por-patron", type=int, default=10)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=str, default="patterns_fase1.json")
    ap.add_argument("--base-price-min", type=float, default=80.0)
    ap.add_argument("--base-price-max", type=float, default=650.0)
    ap.add_argument("--vol-min", type=float, default=0.003)
    ap.add_argument("--vol-max", type=float, default=0.012)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    dataset = []
    for patron in PATRONES:
        for i in range(args.n_por_patron):
            ej = generar_ejemplo(
                patron, i,
                (args.base_price_min, args.base_price_max),
                (args.vol_min, args.vol_max),
                rng,
            )
            dataset.append(ej)
    rng.shuffle(dataset)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print(f"Generados {len(dataset)} ejemplos ({args.n_por_patron} por patrón x {len(PATRONES)} patrones) -> {args.out}")


if __name__ == "__main__":
    main()
