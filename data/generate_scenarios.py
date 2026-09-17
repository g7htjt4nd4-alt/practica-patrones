"""
Generador de escenarios para la Fase 3: aplicar el checklist completo de
las 5 estrategias formalizadas (playbook FPalacios LLC) y decidir cuál
aplica, o si ninguna aplica todavía.

A diferencia de las Fases 1 y 2 (reconocimiento visual puro), aquí el
usuario debe combinar: contexto (bloque horario, tendencia previa,
relación entre SMAs), la vela gatillo (color/dirección) y el volumen
(% del promedio) — exactamente como exige cada checklist de
notas-curso-bolsa-newlife.md, sección 9.

Categorías (6):
- VV11        -> gap + ruptura de canal en V10/V11, volumen > 50% avg
- SMA_hora    -> rebote en SMA40 (1h) + ruptura, volumen > 50% avg
- SMA_dia     -> rebote en SMA100/200 (día) confirmado en hora
- V10_roja    -> V10 roja dentro de canal bajista ya establecido
- Falso_Gap   -> V10 verde + ruptura posterior de su propio piso
- ninguna     -> distractor: casi cumple una de las 5, pero falla 1 condición
                 (volumen insuficiente, dirección equivocada, sin ruptura, etc.)

Formato de salida:
{
  "id", "patron_correcto", "opciones",
  "contexto": string (narrativa con los datos del checklist),
  "vela_gatillo": {o,h,l,c},
  "volumen": {"actual_pct_avg": number, "umbral_pct_avg": 50},
  "explicacion": string
}

Uso:
    python3 generate_scenarios.py --n-por-patron 8 --seed 11 --out patterns_fase3.json
"""
import argparse
import json
import random

CATEGORIAS = ["VV11", "SMA_hora", "SMA_dia", "V10_roja", "Falso_Gap", "ninguna"]

EXPLICACIONES = {
    "VV11": "Se cumplen las 3 condiciones de la Formación 3 (VV11): la vela V11 es verde alcista, rompe el canal/línea de caída, y su volumen supera el 50% del promedio.",
    "SMA_hora": "Se cumple la Formación 4: la corrección frenó milimétricamente en el SMA 40 (con SMA 20 > SMA 40), y la vela de ruptura es verde con volumen > 50% del promedio.",
    "SMA_dia": "Se cumple la Formación 5: la corrección frenó en el SMA 100/200 (vista diaria) y la ruptura horaria posterior confirma con vela verde y volumen suficiente.",
    "V10_roja": "Se cumple la Estrategia V10 Roja: la acción ya operaba dentro de un canal bajista validado, y la vela V10 (9:30-10:00) se formó roja y bajista — gatillo para put.",
    "Falso_Gap": "Se cumple la Estrategia de Falso Gap: la V10 abrió con gap y cerró verde (el 'engaño'), pero una vela posterior rompió el piso de esa V10 con una vela roja — gatillo para put.",
    "ninguna": "Casi calza con una de las estrategias, pero falla una condición obligatoria del checklist — no es un gatillo válido todavía.",
}

BLOQUES = ["V10 (9:30-10:00)", "V11 (10:00-11:00)", "V12 (11:00-12:00)", "V1 (12:00-13:00)", "V2 (13:00-14:00)"]
ACTIVOS = ["SPY", "QQQ", "BAC", "AAPL", "NVDA"]


def vela(direccion, cuerpo_pct, rng, base=100.0):
    o = base
    body = base * cuerpo_pct
    if direccion == "verde":
        c = o + body
    else:
        c = o - body
    hw = abs(rng.gauss(0.003, 0.001)) * base
    lw = abs(rng.gauss(0.003, 0.001)) * base
    h = max(o, c) + hw
    l = min(o, c) - lw
    return {"o": round(o, 2), "h": round(h, 2), "l": round(l, 2), "c": round(c, 2)}


def gen_vv11(rng, valido=True):
    activo = rng.choice(ACTIVOS)
    gap = rng.choice(["alcista", "bajista"])
    if valido:
        vol_pct = rng.randint(55, 95)
        v = vela("verde", rng.uniform(0.006, 0.014), rng)
        ctx = (f"{activo}: la vela V10 (9:30-10:00) abrió con gap {gap} y cerró verde alcista. "
               f"Ahora estás en la vela V11 (10:00-11:00): es verde alcista y acaba de romper "
               f"el canal bajista que traía el precio.")
        return "VV11", ctx, v, vol_pct
    else:
        # distractor: rompe canal pero con volumen insuficiente
        vol_pct = rng.randint(15, 45)
        v = vela("verde", rng.uniform(0.006, 0.014), rng)
        ctx = (f"{activo}: la vela V10 abrió con gap {gap} y cerró verde. La vela V11 es verde "
               f"alcista y rompe el canal bajista, pero su volumen se ve bajo comparado con el "
               f"promedio del día.")
        return "ninguna", ctx, v, vol_pct


def gen_sma_hora(rng, valido=True):
    activo = rng.choice(ACTIVOS)
    if valido:
        vol_pct = rng.randint(55, 95)
        v = vela("verde", rng.uniform(0.005, 0.012), rng)
        ctx = (f"{activo}, gráfico de 1 hora: el SMA 20 está por encima del SMA 40. El precio "
               f"corrigió y frenó milimétricamente justo en el SMA 40. La vela actual es verde "
               f"alcista y rompe la línea de caída trazada sobre los pabilos de la corrección.")
        return "SMA_hora", ctx, v, vol_pct
    else:
        vol_pct = rng.randint(50, 90)
        v = vela("verde", rng.uniform(0.005, 0.012), rng)
        ctx = (f"{activo}, gráfico de 1 hora: el SMA 20 está por encima del SMA 40. El precio "
               f"corrigió, pero se detuvo bastante antes de tocar el SMA 40 — no llegó a la zona "
               f"de rebote. La vela actual es verde y rompe una línea de caída de todas formas.")
        return "ninguna", ctx, v, vol_pct


def gen_sma_dia(rng, valido=True):
    activo = rng.choice(ACTIVOS)
    sma = rng.choice(["100", "200"])
    if valido:
        vol_pct = rng.randint(55, 90)
        v = vela("verde", rng.uniform(0.005, 0.012), rng)
        ctx = (f"{activo}, vista diaria: la acción corrigió tras superar el SMA 20 y frenó "
               f"justo sobre el SMA {sma}. Al cierre del día se mantuvo sobre ese nivel. "
               f"En el gráfico horario, la vela actual rompe la línea de caída trazada sobre "
               f"los pabilos de la corrección, en verde.")
        return "SMA_dia", ctx, v, vol_pct
    else:
        vol_pct = rng.randint(55, 90)
        v = vela("verde", rng.uniform(0.005, 0.012), rng)
        ctx = (f"{activo}, vista diaria: la acción corrigió y ya perforó el SMA {sma} — cerró "
               f"el día por debajo de ese nivel, no sobre él. En el gráfico horario aparece una "
               f"vela verde que rompe una línea de caída de corto plazo.")
        return "ninguna", ctx, v, vol_pct


def gen_v10_roja(rng, valido=True):
    activo = rng.choice(ACTIVOS)
    if valido:
        v = vela("roja", rng.uniform(0.006, 0.014), rng)
        ctx = (f"{activo}: el precio ya viene operando claramente dentro de un canal bajista "
               f"validado (la línea toca 2 veces los máximos). La vela V10 (9:30-10:00) se "
               f"acaba de formar roja y con dirección bajista.")
        return "V10_roja", ctx, v, None
    else:
        v = vela("roja", rng.uniform(0.006, 0.014), rng)
        ctx = (f"{activo}: el precio viene en un rango lateral sin una línea bajista clara que "
               f"conecte al menos 2 máximos. La vela V10 (9:30-10:00) se formó roja.")
        return "ninguna", ctx, v, None


def gen_falso_gap(rng, valido=True):
    activo = rng.choice(ACTIVOS)
    gap = rng.choice(["alcista", "bajista"])
    if valido:
        v = vela("roja", rng.uniform(0.005, 0.011), rng)
        ctx = (f"{activo}: la V10 abrió con gap {gap} y cerró verde (el 'engaño'). Se trazó la "
               f"línea de control en el piso exacto de esa vela V10. La vela actual, unas horas "
               f"después, acaba de romper esa línea de control hacia abajo, en rojo.")
        return "Falso_Gap", ctx, v, None
    else:
        v = vela("roja", rng.uniform(0.005, 0.011), rng)
        ctx = (f"{activo}: la V10 abrió con gap {gap} y cerró verde. Ya pasaron varias horas y "
               f"el precio sigue por encima del piso de esa V10 — la línea de control todavía no "
               f"se ha roto. Aun así, apareció una vela roja en el camino.")
        return "ninguna", ctx, v, None


GENERADORES = {
    "VV11": gen_vv11,
    "SMA_hora": gen_sma_hora,
    "SMA_dia": gen_sma_dia,
    "V10_roja": gen_v10_roja,
    "Falso_Gap": gen_falso_gap,
}


def generar_ejemplo(categoria_objetivo, idx, rng):
    if categoria_objetivo == "ninguna":
        base_cat = rng.choice(list(GENERADORES.keys()))
        etiqueta, ctx, v, vol_pct = GENERADORES[base_cat](rng, valido=False)
    else:
        etiqueta, ctx, v, vol_pct = GENERADORES[categoria_objetivo](rng, valido=True)

    volumen = None
    if vol_pct is not None:
        volumen = {"actual_pct_avg": vol_pct, "umbral_pct_avg": 50}

    return {
        "id": f"{categoria_objetivo[:8]}-{idx:03d}",
        "patron_correcto": etiqueta,
        "opciones": CATEGORIAS,
        "contexto": ctx,
        "vela_gatillo": v,
        "volumen": volumen,
        "explicacion": EXPLICACIONES[etiqueta],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-por-patron", type=int, default=8)
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--out", type=str, default="patterns_fase3.json")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    dataset = []
    for categoria in CATEGORIAS:
        for i in range(args.n_por_patron):
            dataset.append(generar_ejemplo(categoria, i, rng))
    rng.shuffle(dataset)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print(f"Generados {len(dataset)} ejemplos ({args.n_por_patron} por categoría x {len(CATEGORIAS)}) -> {args.out}")
    from collections import Counter
    print(Counter(e["patron_correcto"] for e in dataset))


if __name__ == "__main__":
    main()
