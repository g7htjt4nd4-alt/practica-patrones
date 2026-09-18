"""
Genera diagramas idealizados (no ruidosos) de los 6 tipos de canal para
el glosario visual de la Fase 2 — mismo espíritu que
data/glosario/generate_glosario.py (Fase 1), pero para canales.
"""
import json
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

OUT_DIR = "glosario_fase2"
os.makedirs(OUT_DIR, exist_ok=True)

VERDE = "#1f9d55"
ROJO = "#d64545"
AZUL = "#2563eb"
GRIS = "#555555"


def vela(ax, x, o, h, l, c, ancho=0.55):
    color = VERDE if c >= o else ROJO
    ax.plot([x, x], [l, h], color=color, linewidth=2, solid_capstyle="round")
    bottom = min(o, c)
    height = abs(c - o) if abs(c - o) > 0.01 else 0.01
    ax.bar(x, height, bottom=bottom, width=ancho, color=color, zorder=3)


def base_fig():
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.set_facecolor("#fafafa")
    fig.patch.set_facecolor("#fafafa")
    return fig, ax


def finalizar(fig, ax, titulo, archivo, xlim, ylim):
    ax.set_title(titulo, fontsize=14, fontweight="bold", pad=12)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, archivo), dpi=130)
    plt.close(fig)


def gen_canal_bajista(con_ruptura):
    fig, ax = base_fig()
    xs_line = [0, 8]
    ys_line = [110, 100]
    ax.plot(xs_line, ys_line, "--", color=AZUL, linewidth=1.6)
    # velas respetando la línea
    puntos = [(0, 108, 110, 106, 107), (2, 106.5, 107.5, 104, 105),
              (4, 104.5, 105.3, 102, 103.2), (6, 102.8, 103.3, 100.5, 101.5)]
    for x, o, h, l, c in puntos:
        vela(ax, x, o, h, l, c)
    ax.scatter([0, 6], [110, 101.3], color=AZUL, zorder=5, s=60)
    ax.annotate("Toque 1", (0, 110), (-0.3, 112.5), fontsize=9, color=AZUL, ha="center")
    ax.annotate("Toque 2", (6, 101.3), (6, 112.5), fontsize=9, color=AZUL, ha="center")
    if con_ruptura:
        vela(ax, 8, 100.5, 104.5, 100.2, 104)
        ax.annotate("Ruptura ↑\n(verde, cierra sobre la línea)", (8, 104), (8, 96),
                    fontsize=9.5, color=GRIS, ha="center",
                    arrowprops=dict(arrowstyle="-", color=GRIS, lw=1))
        titulo, archivo = "Canal bajista válido — con ruptura", "canal_bajista_con_ruptura.png"
    else:
        vela(ax, 8, 100.8, 100.9, 99, 100)
        ax.annotate("Sigue debajo de la línea\n(sin ruptura todavía)", (8, 100), (8, 96),
                    fontsize=9.5, color=GRIS, ha="center",
                    arrowprops=dict(arrowstyle="-", color=GRIS, lw=1))
        titulo, archivo = "Canal bajista válido — sin ruptura", "canal_bajista_sin_ruptura.png"
    finalizar(fig, ax, titulo, archivo, (-1, 9), (94, 115))


def gen_canal_alcista(con_ruptura):
    fig, ax = base_fig()
    xs_line = [0, 8]
    ys_line = [100, 110]
    ax.plot(xs_line, ys_line, "--", color=AZUL, linewidth=1.6)
    puntos = [(0, 102, 104, 100, 103), (2, 103.5, 106, 102.8, 105),
              (4, 105.5, 107.8, 104.5, 107), (6, 107.5, 109.5, 106.5, 109)]
    for x, o, h, l, c in puntos:
        vela(ax, x, o, h, l, c)
    ax.scatter([0, 6], [100, 108.7], color=AZUL, zorder=5, s=60)
    ax.annotate("Toque 1", (0, 100), (-0.3, 96), fontsize=9, color=AZUL, ha="center")
    ax.annotate("Toque 2", (6, 108.7), (6, 96), fontsize=9, color=AZUL, ha="center")
    if con_ruptura:
        vela(ax, 8, 109.5, 109.8, 105.5, 106)
        ax.annotate("Ruptura ↓\n(roja, cierra bajo la línea)", (8, 106), (8, 115),
                    fontsize=9.5, color=GRIS, ha="center",
                    arrowprops=dict(arrowstyle="-", color=GRIS, lw=1))
        titulo, archivo = "Canal alcista válido — con ruptura", "canal_alcista_con_ruptura.png"
    else:
        vela(ax, 8, 109.5, 111.5, 109.3, 111)
        ax.annotate("Sigue sobre la línea\n(sin ruptura todavía)", (8, 111), (8, 115),
                    fontsize=9.5, color=GRIS, ha="center",
                    arrowprops=dict(arrowstyle="-", color=GRIS, lw=1))
        titulo, archivo = "Canal alcista válido — sin ruptura", "canal_alcista_sin_ruptura.png"
    finalizar(fig, ax, titulo, archivo, (-1, 9), (94, 118))


def gen_canal_invalido():
    fig, ax = base_fig()
    puntos = [(0, 103, 104, 101.5, 102), (2, 101.8, 102.3, 100, 100.5),
              (4, 100.3, 108, 99.8, 107), (6, 106.5, 107, 104, 104.5),
              (8, 104.2, 104.6, 102, 102.5)]
    for x, o, h, l, c in puntos:
        vela(ax, x, o, h, l, c)
    ax.scatter([4], [108], color=AZUL, zorder=5, s=60)
    ax.annotate("Solo 1 toque real\n(no hay segunda confirmación)", (4, 108), (4, 111.5),
                fontsize=9.5, color=GRIS, ha="center",
                arrowprops=dict(arrowstyle="-", color=GRIS, lw=1))
    ax.annotate("Sin línea trazable todavía", (4, 99), (4, 96), fontsize=10,
                color=AZUL, ha="center", fontweight="bold")
    finalizar(fig, ax, "Canal inválido (1 solo toque)", "canal_invalido.png", (-1, 9), (94, 113))


def gen_ninguno():
    fig, ax = base_fig()
    puntos = [(0, 100, 101.5, 98.5, 99.5), (2, 99.7, 101, 98.8, 100.3),
              (4, 100.2, 101.8, 99, 99.8), (6, 99.6, 101.2, 98.5, 100.5),
              (8, 100.3, 101.5, 99, 99.7)]
    for x, o, h, l, c in puntos:
        vela(ax, x, o, h, l, c)
    ax.annotate("Rango lateral, sin tendencia\nni línea clara que trazar", (4, 103.5), (4, 103.5),
                fontsize=10.5, color=AZUL, ha="center", fontweight="bold")
    finalizar(fig, ax, "Ninguno / rango lateral", "ninguno_canal.png", (-1, 9), (96, 106))


gen_canal_bajista(con_ruptura=True)
gen_canal_bajista(con_ruptura=False)
gen_canal_alcista(con_ruptura=True)
gen_canal_alcista(con_ruptura=False)
gen_canal_invalido()
gen_ninguno()

manifest = [
    {"patron": "canal_bajista_valido_con_ruptura", "archivo": "canal_bajista_con_ruptura.png",
     "titulo": "Canal bajista válido — con ruptura",
     "definicion": "La línea de caída toca 2 veces los máximos (regla de validación mínima) y una vela verde la rompe con fuerza: ruptura alcista confirmada."},
    {"patron": "canal_bajista_valido_sin_ruptura", "archivo": "canal_bajista_sin_ruptura.png",
     "titulo": "Canal bajista válido — sin ruptura",
     "definicion": "La línea de caída toca 2 veces los máximos — canal bajista válido — pero el precio todavía la respeta, sin ruptura."},
    {"patron": "canal_alcista_valido_con_ruptura", "archivo": "canal_alcista_con_ruptura.png",
     "titulo": "Canal alcista válido — con ruptura",
     "definicion": "La línea de soporte toca 2 veces los mínimos: canal alcista válido, y una vela roja la rompe hacia abajo: ruptura bajista confirmada."},
    {"patron": "canal_alcista_valido_sin_ruptura", "archivo": "canal_alcista_sin_ruptura.png",
     "titulo": "Canal alcista válido — sin ruptura",
     "definicion": "La línea de soporte toca 2 veces los mínimos: canal alcista válido, y el precio todavía la respeta — sin ruptura."},
    {"patron": "canal_invalido", "archivo": "canal_invalido.png",
     "titulo": "Canal inválido (1 solo toque)",
     "definicion": "La recta solo toca el precio una vez. Según la regla de validación (mínimo 2 toques), no es un canal confiable todavía."},
    {"patron": "ninguno", "archivo": "ninguno_canal.png",
     "titulo": "Ninguno / rango lateral",
     "definicion": "Movimiento lateral sin una línea de tendencia clara que conecte máximos o mínimos. No hay canal que trazar."},
]

with open(os.path.join(OUT_DIR, "glosario_fase2.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

print("Generadas", len(manifest), "imágenes de referencia de canales en", OUT_DIR)
