#!/usr/bin/env python3
"""Lee unicamente los CSV de resultados/ y genera las figuras (figuras/,
PNG a 200 dpi) y las tablas del informe (informe/tablas/*.tex). Ningun
numero del informe se copia a mano: todo sale de aqui.

Uso: python scripts/generar_figuras.py [nombre_de_funcion ...]
     python scripts/generar_figuras.py todos
"""
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTADOS = os.path.join(RAIZ, "resultados")
FIGURAS = os.path.join(RAIZ, "figuras")
TABLAS = os.path.join(RAIZ, "informe", "tablas")
os.makedirs(FIGURAS, exist_ok=True)
os.makedirs(TABLAS, exist_ok=True)

DPI = 200
# Paleta apta para daltonismo (Wong, 2011: https://www.nature.com/articles/nmeth.1618)
PALETA = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442", "#000000"]
plt.rcParams.update({
    "font.size": 11,
    "axes.prop_cycle": plt.cycler(color=PALETA),
    "figure.dpi": DPI,
    "savefig.dpi": DPI,
    "axes.grid": True,
    "grid.alpha": 0.3,
})


def _ruta_r(nombre):
    return os.path.join(RESULTADOS, nombre)


def _guardar_fig(fig, nombre):
    ruta = os.path.join(FIGURAS, nombre)
    fig.savefig(ruta, bbox_inches="tight")
    plt.close(fig)
    print("figura guardada:", ruta)


def _guardar_tabla(nombre, contenido):
    ruta = os.path.join(TABLAS, nombre)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(contenido)
    print("tabla guardada:", ruta)


def _fmt(x, dec=3):
    return f"{x:.{dec}f}".replace(".", ",")


# ---------------------------------------------------------------- Figura 1
def fig_factorial():
    ns = [6, 10, 15, 20, 2000, 200000]
    log10_val = [(math.lgamma(n) - math.log(2)) / math.log(10) for n in ns]  # log10((n-1)!/2)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar([str(n) for n in ns], log10_val, color=PALETA[0])
    for i, v in enumerate(log10_val):
        ax.text(i, v, f"{v:.1f} dígitos" if v > 5 else f"{10**v:.0f}", ha="center", va="bottom", fontsize=8)
    ax.set_ylabel("log10((n-1)!/2)")
    ax.set_xlabel("Número de ciudades (n)")
    ax.set_title("Crecimiento factorial del espacio de recorridos")
    _guardar_fig(fig, "01_crecimiento_factorial.png")

    filas = "\n".join(
        f"{n} & {10**v:.3e} & {v:.1f} \\\\" if v > 6 else f"{n} & {math.exp(math.lgamma(n) - math.log(2)):.3e} & {v:.2f} \\\\"
        for n, v in zip(ns, log10_val)
    )
    tabla = (
        "\\begin{table}[H]\\centering\n"
        "\\caption{Recorridos posibles $(n-1)!/2$, calculado con \\texttt{lgamma}.}\n"
        "\\label{tab:factorial}\n"
        "\\begin{tabular}{rrr}\\toprule\n"
        "$n$ & $(n-1)!/2$ & $\\log_{10}$ \\\\\\midrule\n"
        f"{filas}\n\\bottomrule\\end{{tabular}}\\end{{table}}\n"
    )
    _guardar_tabla("factorial.tex", tabla)


# ---------------------------------------------------------------- Figura resultados n=20 y n=2000 (tablas)
def tabla_resultados_n20():
    df = pd.read_csv(_ruta_r("instancia_n20.csv"))
    filas = "\n".join(
        f"{int(r.seed)} & {_fmt(r.L_mejor,3)} & {_fmt(r.optimo_exacto,3)} & {_fmt(r.gap_pct,3)} & "
        f"{'sí' if r.tour_valido else 'no'} \\\\"
        for r in df.itertuples()
    )
    resumen = (
        f"Media & {_fmt(df.gap_pct.mean())} & Desv. & {_fmt(df.gap_pct.std())} & "
        f"Mín. & {_fmt(df.gap_pct.min())} & Máx. & {_fmt(df.gap_pct.max())}"
    )
    tabla = (
        "\\begin{table}[H]\\centering\n"
        "\\caption{n=20 contra Held-Karp, m=20, K=19, 5 semillas.}\n"
        "\\label{tab:n20}\n"
        "\\begin{tabular}{rrrrc}\\toprule\n"
        "Semilla & $L_{mejor}$ & Óptimo exacto & Gap (\\%) & Tour válido \\\\\\midrule\n"
        f"{filas}\\\\\\bottomrule\\end{{tabular}}\\\\[0.3em]\n"
        f"\\footnotesize {resumen} (puntos porcentuales de gap)\n"
        "\\end{table}\n"
    )
    _guardar_tabla("resultados_n20.tex", tabla)


def tabla_resultados_n2000():
    df = pd.read_csv(_ruta_r("seleccion_configuracion.csv"))
    df = df[df["configuracion"] == "candidata_b_segunda_feromona"]
    L = df["L_mejor"].astype(float)
    tabla = (
        "\\begin{table}[H]\\centering\n"
        "\\caption{n=2\\,000, configuración ganadora, m=2\\,000, K=8, 8 semillas.}\n"
        "\\label{tab:n2000}\n"
        "\\begin{tabular}{rrrr}\\toprule\n"
        "Media $L_{mejor}$ & Desv. estándar & Mínimo & Máximo \\\\\\midrule\n"
        f"{_fmt(L.mean())} & {_fmt(L.std())} & {_fmt(L.min())} & {_fmt(L.max())} \\\\\n"
        "\\bottomrule\\end{tabular}\\end{table}\n"
    )
    _guardar_tabla("resultados_n2000.tex", tabla)


# ---------------------------------------------------------------- Figura 3: boxplots por configuracion
def fig_boxplots_configuracion():
    df = pd.read_csv(_ruta_r("barrido_parametros.csv"))
    for parametro in df["parametro_barrido"].dropna().unique():
        sub = df[df["parametro_barrido"] == parametro].copy()
        valores = sorted(sub["valor_barrido"].unique(), key=lambda v: float(v))
        datos = [sub[sub["valor_barrido"] == v]["L_mejor"].astype(float).values for v in valores]
        fig, ax = plt.subplots(figsize=(6, 4))
        bp = ax.boxplot(datos, tick_labels=[str(v) for v in valores], patch_artist=True)
        for patch in bp["boxes"]:
            patch.set_facecolor(PALETA[0])
            patch.set_alpha(0.5)
        ax.set_xlabel(parametro)
        ax.set_ylabel("Longitud del mejor tour")
        ax.set_title(f"Varianza entre semillas: {parametro} (n=2\\,000)".replace("\\,", " "))
        _guardar_fig(fig, f"03_boxplot_{parametro}.png")


# ---------------------------------------------------------------- Figura 6 (parcial): tiempo vs m, n=200000
def fig_tiempo_vs_m():
    ruta = _ruta_r("costo_m_n200000_3reps.csv")
    if not os.path.exists(ruta):
        print("costo_m_n200000_3reps.csv no existe todavia; se omite fig_tiempo_vs_m")
        return
    df = pd.read_csv(ruta)
    g = df.groupby("m")["t_aco_s"].agg(["mean", "std"]).reset_index()
    m = g["m"].values.astype(float)
    t = g["mean"].values
    A = np.vstack([m, np.ones_like(m)]).T
    (a, b), *_ = np.linalg.lstsq(A, t, rcond=None)
    pred = a * m + b
    r2 = 1 - np.sum((t - pred) ** 2) / np.sum((t - t.mean()) ** 2)
    m_ext = 200000
    t_ext = a * m_ext + b

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.errorbar(m, t, yerr=g["std"].values, fmt="o", color=PALETA[0], label="medido (3 repeticiones)")
    m_recta = np.linspace(0, m_ext, 100)
    ax.plot(m_recta, a * m_recta + b, "--", color=PALETA[1], label=f"ajuste lineal (R²={r2:.4f})")
    ax.scatter([m_ext], [t_ext], marker="*", s=200, color=PALETA[2],
               label=f"extrapolación m=n=200\\,000 ({t_ext/60:.1f} min)".replace("\\,", " "))
    ax.set_xlabel("Número de hormigas (m)")
    ax.set_ylabel("Tiempo de una iteración (s)")
    ax.set_title("Tiempo por iteración vs. m, n=200\\,000 (K=8)".replace("\\,", " "))
    ax.legend(fontsize=8)
    _guardar_fig(fig, "06_tiempo_vs_m_n200000.png")

    tabla = (
        "\\begin{table}[H]\\centering\n"
        "\\caption{Tiempo de una iteración vs. m, n=200\\,000, K=8 (3 repeticiones).}\n"
        "\\label{tab:costo_m}\n"
        "\\begin{tabular}{rrr}\\toprule\n"
        "$m$ & Tiempo medio (s) & Desv. estándar (s) \\\\\\midrule\n"
        + "\n".join(f"{int(r.m)} & {_fmt(r['mean'])} & {_fmt(r['std'])} \\\\" for r in g.itertuples()) +
        f"\n\\bottomrule\\end{{tabular}}\\\\[0.3em]\n"
        f"\\footnotesize Ajuste: $t(m)\\approx {a:.6f}\\,m {'+' if b>=0 else '-'} {abs(b):.3f}$ s, "
        f"$R^2={r2:.6f}$. Extrapolación a $m=n=200\\,000$: {t_ext:.1f} s "
        f"($\\approx${t_ext/60:.1f} min), \\textbf{{estimación por extrapolación, no corrida real}}.\n"
        "\\end{table}\n"
    )
    _guardar_tabla("costo_m_n200000.tex", tabla)


FUNCIONES = {
    "factorial": fig_factorial,
    "tabla_n20": tabla_resultados_n20,
    "tabla_n2000": tabla_resultados_n2000,
    "boxplots": fig_boxplots_configuracion,
    "tiempo_vs_m": fig_tiempo_vs_m,
}


def main():
    args = sys.argv[1:] or ["todos"]
    if "todos" in args:
        args = list(FUNCIONES.keys())
    for nombre in args:
        if nombre not in FUNCIONES:
            print("funcion desconocida:", nombre)
            continue
        print(f"=== {nombre} ===")
        FUNCIONES[nombre]()


if __name__ == "__main__":
    main()
