"""
Generador de datasets sintéticos para la Fase 2: canales de tendencia y
rupturas, aplicando la regla de validación del profesor (FPalacios LLC):
una línea de caída/soporte es válida solo si toca como mínimo 2 veces los
puntos donde el precio intentó romperla sin lograrlo.

A diferencia de la Fase 1 (patrones de una vela), aquí el "patrón" es
geométrico: una recta trazada sobre los máximos (canal bajista) o los
mínimos (canal alcista) de al menos 2 puntos, que el resto de las velas
respeta.

Categorías (6), balanceadas:
- canal_bajista_valido_con_ruptura   -> resistencia descendente, 2+ toques, rota al alza
- canal_bajista_valido_sin_ruptura   -> resistencia descendente, 2+ toques, sigue vigente
- canal_alcista_valido_con_ruptura   -> soporte ascendente, 2+ toques, rota a la baja
- canal_alcista_valido_sin_ruptura   -> soporte ascendente, 2+ toques, sigue vigente
- canal_invalido                     -> solo 1 toque real (no se puede trazar canal confiable)
- ninguno                            -> rango lateral, sin canal claro

Formato de salida: mismo esquema conceptual que Fase 1, pero además incluye
"linea" (los 2 puntos de anclaje, para dibujar la recta) e "indices_toque".

Uso:
    python3 generate_channels.py --n-por-patron 8 --seed 7 --out patterns_fase2.json
"""
import argparse
import json
import random

CATEGORIAS = [
    "canal_bajista_valido_con_ruptura",
    "canal_bajista_valido_sin_ruptura",
    "canal_alcista_valido_con_ruptura",
    "canal_alcista_valido_sin_ruptura",
    "canal_invalido",
    "ninguno",
]

EXPLICACIONES = {
    "canal_bajista_valido_con_ruptura": "La línea de caída toca 2 veces los máximos (mínimo requerido por la regla de validación) y la última vela verde la rompe con fuerza: ruptura alcista confirmada.",
    "canal_bajista_valido_sin_ruptura": "La línea de caída toca 2 veces los máximos — es un canal bajista válido — pero el precio sigue respetándola, todavía no hay ruptura.",
    "canal_alcista_valido_con_ruptura": "La línea de soporte toca 2 veces los mínimos: canal alcista válido. La última vela roja la rompe hacia abajo: ruptura bajista confirmada.",
    "canal_alcista_valido_sin_ruptura": "La línea de soporte toca 2 veces los mínimos: canal alcista válido, y el precio todavía la respeta — sin ruptura.",
    "canal_invalido": "La recta solo toca el precio una vez. Según la regla de validación (mínimo 2 toques), esta línea NO es un canal confiable todavía — es una opinión, no un patrón confirmado.",
    "ninguno": "Movimiento lateral sin una línea de tendencia clara que conecte máximos o mínimos. No hay canal que trazar.",
}


def _candle_between(o, target_c, vol, rng, upper_bound=None, lower_bound=None, margin_frac=0.15):
    """Genera una vela desde 'o' hacia 'target_c', respetando (si se da) un
    techo o piso que no debe traspasar (salvo el margen del toque)."""
    c = target_c
    hw = abs(rng.gauss(vol * 1.1, vol * 0.3)) * o
    lw = abs(rng.gauss(vol * 1.1, vol * 0.3)) * o
    h = max(o, c) + hw
    l = min(o, c) - lw
    if upper_bound is not None:
        cap = upper_bound - margin_frac * vol * o
        if h > cap:
            h = cap
        if c > h:
            c = h - 0.01
        if o > h:
            o = h - 0.01
    if lower_bound is not None:
        floor = lower_bound + margin_frac * vol * o
        if l < floor:
            l = floor
        if c < l:
            c = l + 0.01
        if o < l:
            o = l + 0.01
    return {"o": round(o, 2), "h": round(h, 2), "l": round(l, 2), "c": round(c, 2)}


def gen_canal(direccion, con_ruptura, base_price, vol, rng):
    """direccion: 'bajista' (línea sobre máximos) o 'alcista' (línea sobre mínimos)."""
    n_pre = rng.randint(2, 3)
    n_mid = rng.randint(3, 5)
    n_post = rng.randint(2, 3)
    n_total = n_pre + 1 + n_mid + 1 + n_post  # +1 en cada punto de toque

    t1 = n_pre
    t2 = n_pre + 1 + n_mid

    if direccion == "bajista":
        v1 = base_price * (1 + rng.uniform(0.01, 0.02))
        v2 = v1 * (1 - rng.uniform(0.02, 0.05))
    else:
        v1 = base_price * (1 - rng.uniform(0.01, 0.02))
        v2 = v1 * (1 + rng.uniform(0.02, 0.05))
    slope = (v2 - v1) / (t2 - t1)

    def linea(x):
        return v1 + slope * (x - t1)

    velas = []
    price = base_price * (1 + rng.uniform(-0.01, 0.01))

    for i in range(n_total):
        is_touch = i in (t1, t2)
        line_val = linea(i)
        if is_touch:
            # la vela toca la línea casi exactamente
            if direccion == "bajista":
                o = price
                c = o * (1 - abs(rng.gauss(vol * 0.3, vol * 0.1)))
                h = max(o, c, line_val)
                l = min(o, c) - abs(rng.gauss(vol * 0.5, vol * 0.2)) * o
            else:
                o = price
                c = o * (1 + abs(rng.gauss(vol * 0.3, vol * 0.1)))
                l = min(o, c, line_val)
                h = max(o, c) + abs(rng.gauss(vol * 0.5, vol * 0.2)) * o
            vela = {"o": round(o, 2), "h": round(h, 2), "l": round(l, 2), "c": round(c, 2)}
        elif i > t2 and i == n_total - 1 and con_ruptura:
            # vela de ruptura
            o = price
            if direccion == "bajista":
                extra = abs(rng.gauss(vol * 1.5, vol * 0.3)) * o
                c = max(o, line_val) + extra
                h = c + abs(rng.gauss(vol * 0.2, vol * 0.05)) * o
                l = min(o, c) - abs(rng.gauss(vol * 0.3, vol * 0.1)) * o
            else:
                extra = abs(rng.gauss(vol * 1.5, vol * 0.3)) * o
                c = min(o, line_val) - extra
                l = c - abs(rng.gauss(vol * 0.2, vol * 0.05)) * o
                h = max(o, c) + abs(rng.gauss(vol * 0.3, vol * 0.1)) * o
            vela = {"o": round(o, 2), "h": round(h, 2), "l": round(l, 2), "c": round(c, 2)}
        else:
            step = rng.gauss(0, vol * 0.6)
            target_c = price * (1 + step)
            if direccion == "bajista":
                vela = _candle_between(price, target_c, vol, rng, upper_bound=line_val)
            else:
                vela = _candle_between(price, target_c, vol, rng, lower_bound=line_val)
        velas.append(vela)
        price = vela["c"]

    return velas, [t1, t2], round(v1, 2), round(v2, 2)


def gen_invalido(base_price, vol, rng):
    """Una sola vela extrema (1 toque), sin segunda confirmación: no hay
    canal trazable todavía."""
    n = rng.randint(8, 11)
    extremo_idx = rng.randint(3, n - 3)
    velas = []
    price = base_price
    direccion = rng.choice(["alza_rechazada", "baja_rechazada"])
    for i in range(n):
        if i == extremo_idx:
            o = price
            if direccion == "alza_rechazada":
                c = o * (1 + abs(rng.gauss(vol * 0.4, vol * 0.1)))
                h = max(o, c) + abs(rng.gauss(vol * 2.0, vol * 0.4)) * o
                l = min(o, c) - abs(rng.gauss(vol * 0.3, vol * 0.1)) * o
            else:
                c = o * (1 - abs(rng.gauss(vol * 0.4, vol * 0.1)))
                l = min(o, c) - abs(rng.gauss(vol * 2.0, vol * 0.4)) * o
                h = max(o, c) + abs(rng.gauss(vol * 0.3, vol * 0.1)) * o
            vela = {"o": round(o, 2), "h": round(h, 2), "l": round(l, 2), "c": round(c, 2)}
        else:
            step = rng.gauss(0, vol * 0.6)
            c = price * (1 + step)
            hw = abs(rng.gauss(vol * 0.5, vol * 0.15)) * price
            lw = abs(rng.gauss(vol * 0.5, vol * 0.15)) * price
            vela = {"o": round(price, 2), "h": round(max(price, c) + hw, 2),
                     "l": round(min(price, c) - lw, 2), "c": round(c, 2)}
        velas.append(vela)
        price = vela["c"]
    return velas


def gen_ninguno(base_price, vol, rng):
    """Rango lateral sin tendencia ni canal trazable."""
    n = rng.randint(9, 12)
    velas = []
    price = base_price
    for _ in range(n):
        step = rng.gauss(0, vol * 0.5)
        c = price * (1 + step)
        # mantiene el precio cerca de la base (reversión a la media, sin drift)
        c = c + (base_price - c) * 0.3
        hw = abs(rng.gauss(vol * 0.5, vol * 0.15)) * price
        lw = abs(rng.gauss(vol * 0.5, vol * 0.15)) * price
        vela = {"o": round(price, 2), "h": round(max(price, c) + hw, 2),
                 "l": round(min(price, c) - lw, 2), "c": round(c, 2)}
        velas.append(vela)
        price = vela["c"]
    return velas


def generar_ejemplo(categoria, idx, base_price_range, vol_range, rng):
    base_price = rng.uniform(*base_price_range)
    vol = rng.uniform(*vol_range)

    if categoria.startswith("canal_bajista"):
        con_ruptura = categoria.endswith("con_ruptura")
        velas, toques, v1, v2 = gen_canal("bajista", con_ruptura, base_price, vol, rng)
        linea = {"tipo": "bajista", "punto_inicio": {"idx": toques[0], "valor": v1},
                  "punto_fin": {"idx": toques[1], "valor": v2}}
    elif categoria.startswith("canal_alcista"):
        con_ruptura = categoria.endswith("con_ruptura")
        velas, toques, v1, v2 = gen_canal("alcista", con_ruptura, base_price, vol, rng)
        linea = {"tipo": "alcista", "punto_inicio": {"idx": toques[0], "valor": v1},
                  "punto_fin": {"idx": toques[1], "valor": v2}}
    elif categoria == "canal_invalido":
        velas = gen_invalido(base_price, vol, rng)
        toques = []
        linea = None
    else:
        velas = gen_ninguno(base_price, vol, rng)
        toques = []
        linea = None

    return {
        "id": f"{categoria[:12]}-{idx:03d}",
        "patron_correcto": categoria,
        "opciones": CATEGORIAS,
        "velas": velas,
        "indices_toque": toques,
        "linea": linea,
        "explicacion": EXPLICACIONES[categoria],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-por-patron", type=int, default=8)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", type=str, default="patterns_fase2.json")
    ap.add_argument("--base-price-min", type=float, default=80.0)
    ap.add_argument("--base-price-max", type=float, default=650.0)
    ap.add_argument("--vol-min", type=float, default=0.006)
    ap.add_argument("--vol-max", type=float, default=0.016)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    dataset = []
    for categoria in CATEGORIAS:
        for i in range(args.n_por_patron):
            ej = generar_ejemplo(
                categoria, i,
                (args.base_price_min, args.base_price_max),
                (args.vol_min, args.vol_max),
                rng,
            )
            dataset.append(ej)
    rng.shuffle(dataset)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print(f"Generados {len(dataset)} ejemplos ({args.n_por_patron} por categoría x {len(CATEGORIAS)}) -> {args.out}")


if __name__ == "__main__":
    main()
