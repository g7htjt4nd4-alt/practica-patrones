"""
Genera imágenes de referencia limpias (no ruidosas) para el glosario
visual de patrones de velas japonesas. A diferencia de
data/patterns_fase1.json (velas con ruido aleatorio, para practicar
reconocimiento), estas son versiones idealizadas y anotadas — para
aprender el patrón antes o después de fallar una pregunta.
"""
import json
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT_DIR = "glosario"
os.makedirs(OUT_DIR, exist_ok=True)

VERDE = "#1f9d55"
ROJO = "#d64545"
AZUL = "#2563eb"
GRIS = "#555555"


def nueva_figura():
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.set_facecolor("#fafafa")
    fig.patch.set_facecolor("#fafafa")
    return fig, ax


def dibujar_vela(ax, x, o, h, l, c, ancho=0.5):
    color = VERDE if c >= o else ROJO
    ax.plot([x, x], [l, h], color=color, linewidth=2.2, solid_capstyle="round")
    bottom = min(o, c)
    height = abs(c - o) if abs(c - o) > 0.01 else 0.01
    ax.bar(x, height, bottom=bottom, width=ancho, color=color, edgecolor=color, zorder=3)


def anotar(ax, x, y, texto, xytext, color=GRIS, arrow=True):
    ax.annotate(
        texto, xy=(x, y), xytext=xytext, fontsize=10, color=color,
        ha="center",
        arrowprops=dict(arrowstyle="-", color=color, lw=1.1) if arrow else None,
    )


def finalizar(fig, ax, titulo, archivo, ylim=None, xlim=(-1, 1)):
    ax.set_title(titulo, fontsize=15, fontweight="bold", pad=14)
    ax.set_xlim(*xlim)
    if ylim:
        ax.set_ylim(*ylim)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, archivo), dpi=130)
    plt.close(fig)


def gen_martillo():
    fig, ax = nueva_figura()
    dibujar_vela(ax, 0, 98, 98.6, 92, 98.5)
    anotar(ax, 0.25, 98.55, "Cuerpo pequeño arriba", (0.7, 100.5))
    anotar(ax, 0, 94, "Mechón largo abajo\n(rechazo de los vendedores)", (0, 89.5), arrow=False)
    ax.annotate("", xy=(0, 92.2), xytext=(0, 96.5),
                arrowprops=dict(arrowstyle="-", color=GRIS, lw=1))
    finalizar(fig, ax, "Martillo (Hammer)", "martillo.png", ylim=(88, 102))


def gen_gancho():
    fig, ax = nueva_figura()
    dibujar_vela(ax, 0, 102, 108, 101.5, 101.2)
    anotar(ax, 0.25, 101.35, "Cuerpo pequeño abajo", (0.7, 99.5))
    anotar(ax, 0, 106, "Mechón largo arriba\n(rechazo de los compradores)", (0, 109.5), arrow=False)
    ax.annotate("", xy=(0, 107.5), xytext=(0, 103),
                arrowprops=dict(arrowstyle="-", color=GRIS, lw=1))
    finalizar(fig, ax, "Gancho (Estrella fugaz)", "gancho.png", ylim=(98, 111))


def gen_marubozu():
    fig, ax = nueva_figura()
    dibujar_vela(ax, 0, 95, 101, 95, 101)
    anotar(ax, 0.28, 98, "Sin mechas\n(o casi nada)", (1.0, 98))
    anotar(ax, 0, 101, "Cierre = Máximo", (0.9, 102.3), arrow=False)
    anotar(ax, 0, 95, "Apertura = Mínimo", (0.9, 93.7), arrow=False)
    finalizar(fig, ax, "Marubozu (Vela llena)", "marubozu.png", ylim=(92, 104))


def gen_doji():
    fig, ax = nueva_figura()
    dibujar_vela(ax, 0, 99.9, 103, 97, 100.1)
    anotar(ax, 0.3, 100, "Apertura ≈ Cierre\n(cuerpo casi invisible)", (1.0, 100))
    anotar(ax, 0, 103, "Mecha arriba", (0.6, 104.2), arrow=False)
    anotar(ax, 0, 97, "Mecha abajo", (0.6, 95.8), arrow=False)
    finalizar(fig, ax, "Doji", "doji.png", ylim=(94, 106))


def gen_envolvente(alcista=True):
    fig, ax = nueva_figura()
    if alcista:
        dibujar_vela(ax, -0.35, 100, 100.3, 96.5, 97)   # roja previa
        dibujar_vela(ax, 0.35, 96.7, 101.5, 96.5, 101.2)  # verde envolvente
        anotar(ax, -0.35, 97, "Vela roja\n(cuerpo pequeño)", (-0.9, 94.5))
        anotar(ax, 0.35, 101.2, "Vela verde\nenvuelve el cuerpo anterior", (0.9, 103))
        titulo, archivo = "Envolvente alcista", "envolvente_alcista.png"
    else:
        dibujar_vela(ax, -0.35, 97, 101.5, 96.8, 101)   # verde previa
        dibujar_vela(ax, 0.35, 101.3, 101.5, 95.5, 96)   # roja envolvente
        anotar(ax, -0.35, 101, "Vela verde\n(cuerpo pequeño)", (-0.9, 103))
        anotar(ax, 0.35, 96, "Vela roja\nenvuelve el cuerpo anterior", (0.9, 94))
        titulo, archivo = "Envolvente bajista", "envolvente_bajista.png"
    finalizar(fig, ax, titulo, archivo, ylim=(92, 105), xlim=(-1.3, 1.3))


def gen_ninguno():
    fig, ax = nueva_figura()
    dibujar_vela(ax, 0, 98, 100.2, 96.8, 99.3)
    anotar(ax, 0.28, 98.6, "Cuerpo y mechas\nmoderados", (1.0, 99))
    anotar(ax, 0, 100.2, "Sin dominio claro\nde ninguna de las partes", (0, 102), arrow=False)
    finalizar(fig, ax, "Ninguno (vela normal)", "ninguno.png", ylim=(94, 104))


gen_martillo()
gen_gancho()
gen_marubozu()
gen_doji()
gen_envolvente(alcista=True)
gen_envolvente(alcista=False)
gen_ninguno()

manifest = [
    {"patron": "martillo", "archivo": "martillo.png", "titulo": "Martillo (Hammer)",
     "definicion": "Mechón largo abajo, cuerpo pequeño arriba, poca o ninguna mecha superior: los vendedores dominaban pero los compradores retomaron el control antes del cierre. Más significativo tras una caída."},
    {"patron": "gancho", "archivo": "gancho.png", "titulo": "Gancho (Estrella fugaz)",
     "definicion": "Mechón largo arriba, cuerpo pequeño abajo: los compradores intentaron subir el precio pero fallaron en sostenerlo. Más significativo tras una subida."},
    {"patron": "marubozu", "archivo": "marubozu.png", "titulo": "Marubozu (Vela llena)",
     "definicion": "Cuerpo grande, casi sin mechas: dominio absoluto de una dirección durante todo el período."},
    {"patron": "doji", "archivo": "doji.png", "titulo": "Doji",
     "definicion": "Apertura y cierre casi idénticos: equilibrio total entre compradores y vendedores, máxima incertidumbre."},
    {"patron": "envolvente_alcista", "archivo": "envolvente_alcista.png", "titulo": "Envolvente alcista",
     "definicion": "El cuerpo de la vela verde envuelve por completo el cuerpo de la vela roja anterior: señal fuerte de reversión al alza."},
    {"patron": "envolvente_bajista", "archivo": "envolvente_bajista.png", "titulo": "Envolvente bajista",
     "definicion": "El cuerpo de la vela roja envuelve por completo el cuerpo de la vela verde anterior: señal fuerte de reversión a la baja."},
    {"patron": "ninguno", "archivo": "ninguno.png", "titulo": "Ninguno (vela normal)",
     "definicion": "Vela normal sin ningún patrón especial: cuerpo y mechas moderados, sin dominio claro de ninguna de las partes."},
]

with open(os.path.join(OUT_DIR, "glosario_fase1.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

print("Generadas", len(manifest), "imágenes de referencia en", OUT_DIR)
