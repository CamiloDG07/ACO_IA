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

    def _fila_factorial(n, v):
        # (n-1)!/2 = exp(lgamma(n) - log(2)); para v grande, exp(...) tambien
        # desborda un float de 64 bits (por eso se calcula v = log10(...) con
        # lgamma en primer lugar). Solo se materializa el valor exacto cuando
        # es representable; si no, se reporta el orden de magnitud.
        if v <= 300:  # 10**300 esta bien dentro del rango de un float de 64 bits
            valor = f"{10 ** v:.3e}"
        else:
            valor = f"$>10^{{{v:.0f}}}$ ({v:.0f} dígitos)"
        return f"{n} & {valor} & {v:.2f} \\\\"

    filas = "\n".join(_fila_factorial(n, v) for n, v in zip(ns, log10_val))
    tabla = (
        "\\begin{table}[H]\\centering\n"
        "\\caption{Recorridos posibles $(n-1)!/2$, calculado con \\texttt{lgamma}.}\n"
        "\\label{tab:factorial}\n"
        "\\begin{tabular}{|r|r|r|}\\toprule\n"
        "\\rowcolor{gray!25}\n"
        "\\textbf{$n$} & \\textbf{$(n-1)!/2$} & \\textbf{$\\log_{10}$} \\\\\\midrule\n"
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
        f"Media {_fmt(df.gap_pct.mean())}, desviación {_fmt(df.gap_pct.std())}, "
        f"mínimo {_fmt(df.gap_pct.min())}, máximo {_fmt(df.gap_pct.max())} "
        "(puntos porcentuales de gap)."
    )
    tabla = (
        "\\begin{table}[H]\\centering\n"
        "\\caption{n=20 contra Held-Karp, m=20, K=19, 5 semillas.}\n"
        "\\label{tab:n20}\n"
        "\\begin{tabular}{rrrrc}\\toprule\n"
        "\\rowcolor{gray!25}\n"
        "\\textbf{Semilla} & \\textbf{$L_{mejor}$} & \\textbf{Óptimo exacto} & \\textbf{Gap (\\%)} & \\textbf{Tour válido} \\\\\\midrule\n"
        f"{filas}\n\\bottomrule\\end{{tabular}}\\\\[0.3em]\n"
        f"{{\\footnotesize {resumen}}}\n"
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
        "\\rowcolor{gray!25}\n"
        "\\textbf{Media $L_{mejor}$} & \\textbf{Desv. estándar} & \\textbf{Mínimo} & \\textbf{Máximo} \\\\\\midrule\n"
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
        "\\rowcolor{gray!25}\n"
        "\\textbf{$m$} & \\textbf{Tiempo medio (s)} & \\textbf{Desv. estándar (s)} \\\\\\midrule\n"
        + "\n".join(f"{int(r.m)} & {_fmt(r.mean)} & {_fmt(r.std)} \\\\" for r in g.itertuples()) +
        f"\n\\bottomrule\\end{{tabular}}\\\\[0.3em]\n"
        f"\\footnotesize Ajuste: $t(m)\\approx {_fmt(a, 6)}\\,m {'+' if b>=0 else '-'} {_fmt(abs(b), 3)}$ s, "
        f"$R^2={_fmt(r2, 6)}$. Extrapolación a $m=n=200\\,000$: {_fmt(t_ext, 1)} s "
        f"($\\approx${_fmt(t_ext/60, 1)} min), \\textbf{{estimación por extrapolación, no corrida real}}.\n"
        "\\end{table}\n"
    )
    _guardar_tabla("costo_m_n200000.tex", tabla)


# ---------------------------------------------------------------- Figura 2: convergencia
def fig_convergencia():
    for n_val, nombre in [(20, "convergencia_n20.csv"), (2000, "convergencia_n2000.csv")]:
        ruta = _ruta_r(nombre)
        if not os.path.exists(ruta):
            continue
        df = pd.read_csv(ruta)
        fig, ax = plt.subplots(figsize=(6, 4))
        for i, s in enumerate(sorted(df["seed"].unique())):
            sub = df[df["seed"] == s]
            ax.plot(sub["iter"], sub["mejor_global"], color=PALETA[i % len(PALETA)], label=f"semilla {s}")
        ax.set_xlabel("Iteración")
        ax.set_ylabel("Mejor global")
        ax.set_title(f"Convergencia, n={n_val}")
        ax.legend(fontsize=8)
        _guardar_fig(fig, f"02_convergencia_n{n_val}.png")

    ruta200k = _ruta_r("convergencia_n200000_punto5.csv")
    if os.path.exists(ruta200k):
        df = pd.read_csv(ruta200k)
        fig, ax = plt.subplots(figsize=(6, 4))
        for i, s in enumerate(sorted(df["seed"].unique())):
            sub = df[df["seed"] == s]
            ax.plot(sub["iter"], sub["mejor_global"], color=PALETA[i % len(PALETA)], label=f"semilla {s}")
        ax.set_xlabel("Iteración")
        ax.set_ylabel("Mejor global")
        ax.set_title("Convergencia, n=200\\,000 (m=20\\,000)".replace("\\,", " "))
        ax.legend(fontsize=8)
        _guardar_fig(fig, "02_convergencia_n200000.png")


# ---------------------------------------------------------------- Figura 4: mapas de calor
def _heatmap(ruta_csv, col_x, col_y, nombre_png, titulo):
    if not os.path.exists(ruta_csv):
        print(f"{ruta_csv} no existe todavia; se omite {nombre_png}")
        return
    df = pd.read_csv(ruta_csv)
    piv = df.groupby([col_y, col_x])["L_mejor"].mean().unstack()
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(piv.values, cmap="viridis_r", aspect="auto")
    ax.set_xticks(range(len(piv.columns))); ax.set_xticklabels(piv.columns)
    ax.set_yticks(range(len(piv.index))); ax.set_yticklabels(piv.index)
    ax.set_xlabel(col_x); ax.set_ylabel(col_y)
    ax.set_title(titulo)
    for i in range(len(piv.index)):
        for j in range(len(piv.columns)):
            ax.text(j, i, f"{piv.values[i,j]:.1f}", ha="center", va="center", color="white", fontsize=7)
    fig.colorbar(im, ax=ax, label="Longitud media del mejor tour")
    _guardar_fig(fig, nombre_png)


def fig_heatmaps():
    _heatmap(_ruta_r("heatmap_alpha_beta.csv"), "alpha", "beta",
              "04_heatmap_alpha_beta.png", "Calidad media: alpha x beta (n=2\\,000)".replace("\\,", " "))
    _heatmap(_ruta_r("heatmap_rho_qfac.csv"), "rho", "qfac",
              "04_heatmap_rho_qfac.png", "Calidad media: rho x qfac (n=2\\,000)".replace("\\,", " "))


# ---------------------------------------------------------------- Figura 5: efecto de K y segunda feromona
def fig_efecto_k_y_segunda_feromona():
    df = pd.read_csv(_ruta_r("barrido_parametros.csv"))
    sub = df[df["parametro_barrido"] == "K"]
    g = sub.groupby("valor_barrido")["L_mejor"].agg(["mean", "std"]).reset_index()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.errorbar(g["valor_barrido"], g["mean"], yerr=g["std"], fmt="o-", color=PALETA[0])
    ax.set_xlabel("K (tamaño de la lista de candidatas)")
    ax.set_ylabel("Longitud media del mejor tour")
    ax.set_title("Efecto de K (n=2\\,000)".replace("\\,", " "))
    _guardar_fig(fig, "05_efecto_K.png")

    sc = pd.read_csv(_ruta_r("seleccion_configuracion.csv"))
    ref = sc[sc["configuracion"] == "referencia"]["L_mejor"].astype(float)
    con2 = sc[sc["configuracion"] == "candidata_b_segunda_feromona"]["L_mejor"].astype(float)
    fig, ax = plt.subplots(figsize=(5, 4))
    bp = ax.boxplot([ref, con2], tick_labels=["sin segunda\nferomona", "con segunda\nferomona"],
                     patch_artist=True)
    for patch, color in zip(bp["boxes"], [PALETA[1], PALETA[2]]):
        patch.set_facecolor(color); patch.set_alpha(0.5)
    ax.set_ylabel("Longitud del mejor tour")
    ax.set_title("Efecto de la segunda feromona (n=2\\,000, 8 semillas)".replace("\\,", " "))
    _guardar_fig(fig, "05_efecto_segunda_feromona.png")


# ---------------------------------------------------------------- Figura 7: aceleracion y eficiencia
def fig_aceleracion_hilos():
    ruta = _ruta_r("aceleracion_hilos.csv")
    if not os.path.exists(ruta):
        print("aceleracion_hilos.csv no existe todavia; se omite fig_aceleracion_hilos")
        return
    df = pd.read_csv(ruta)
    g = df.groupby("hilos")["t_aco_s"].mean().reset_index()
    t1 = g.loc[g["hilos"] == 1, "t_aco_s"].values[0]
    g["aceleracion"] = t1 / g["t_aco_s"]
    g["eficiencia"] = g["aceleracion"] / g["hilos"]

    fig, ax1 = plt.subplots(figsize=(6, 4))
    ax1.plot(g["hilos"], g["aceleracion"], "o-", color=PALETA[0], label="aceleración medida")
    ax1.plot(g["hilos"], g["hilos"], "--", color="gray", label="aceleración ideal")
    ax1.set_xlabel("Número de hilos")
    ax1.set_ylabel("Aceleración (t$_1$/t$_p$)")
    ax2 = ax1.twinx()
    ax2.plot(g["hilos"], g["eficiencia"], "s-", color=PALETA[1], label="eficiencia")
    ax2.set_ylabel("Eficiencia (aceleración/hilos)")
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, fontsize=8, loc="upper left")
    ax1.set_title("Aceleración y eficiencia vs. número de hilos (n=2\\,000)".replace("\\,", " "))
    _guardar_fig(fig, "07_aceleracion_hilos.png")

    tabla = (
        "\\begin{table}[H]\\centering\n"
        "\\caption{Aceleración y eficiencia vs. número de hilos, n=2\\,000, 3 semillas.}\n"
        "\\label{tab:aceleracion}\n"
        "\\begin{tabular}{rrrr}\\toprule\n"
        "\\rowcolor{gray!25}\n"
        "\\textbf{Hilos} & \\textbf{Tiempo medio (s)} & \\textbf{Aceleración} & \\textbf{Eficiencia} \\\\\\midrule\n"
        + "\n".join(f"{int(r.hilos)} & {_fmt(r.t_aco_s)} & {_fmt(r.aceleracion)} & {_fmt(r.eficiencia)} \\\\"
                     for r in g.itertuples()) +
        "\n\\bottomrule\\end{tabular}\\end{table}\n"
    )
    _guardar_tabla("aceleracion_hilos.tex", tabla)


# ---------------------------------------------------------------- Figura 6b: tiempo vs n (escalamiento)
def fig_tiempo_vs_n():
    disp = pd.read_csv(_ruta_r("escalamiento_disperso.csv"))
    dens = pd.read_csv(_ruta_r("escalamiento_denso.csv"))
    gd = disp.groupby("n_meta")["t_aco"].mean().reset_index()
    ge = dens.groupby("n_meta")["t_aco"].mean().reset_index()
    # tiempo por iteracion (los CSV traen tiempo total de las iteraciones corridas)
    iters_disp = disp.groupby("n_meta")["iters"].mean()
    iters_dens = dens.groupby("n_meta")["iters"].mean()
    gd["t_iter"] = gd["t_aco"] / gd["n_meta"].map(iters_disp)
    ge["t_iter"] = ge["t_aco"] / ge["n_meta"].map(iters_dens)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(gd["n_meta"], gd["t_iter"], "o-", color=PALETA[0], label="dispersa (medida)")
    ax.plot(ge["n_meta"], ge["t_iter"], "s-", color=PALETA[1], label="densa (medida, n≤5\\,000)".replace("\\,", " "))
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("n (ciudades)")
    ax.set_ylabel("Tiempo por iteración (s)")
    ax.set_title("Tiempo por iteración vs. n, m=2\\,048 fijo".replace("\\,", " "))
    ax.legend(fontsize=8)
    _guardar_fig(fig, "06b_tiempo_vs_n.png")


# ---------------------------------------------------------------- Figura 8: memoria densa vs dispersa
def fig_memoria_densa_dispersa():
    disp = pd.read_csv(_ruta_r("escalamiento_disperso.csv"))
    dens = pd.read_csv(_ruta_r("escalamiento_denso.csv"))
    gd = disp.groupby("n_meta")["pico_mem_mb"].mean()
    ge = dens.groupby("n_meta")["pico_mem_mb"].mean()

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(gd.index, gd.values, "o-", color=PALETA[0], label="dispersa (medida)")
    ax.plot(ge.index, ge.values, "s-", color=PALETA[1], label="densa (medida, n≤5\\,000)".replace("\\,", " "))
    ns_teoria = np.array(sorted(set(gd.index) | {200000}))
    mem_densa_teorica = 2 * 4 * ns_teoria.astype(float) ** 2 / 1e6  # MB
    ax.plot(ns_teoria, mem_densa_teorica, "--", color=PALETA[1], alpha=0.6, label="densa (calculada, $2\\cdot4n^2$)")
    ax.axhline(15.88 * 1024, color="red", linestyle=":", label="RAM de la máquina (15,88 GB)")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("n (ciudades)")
    ax.set_ylabel("Memoria pico (MB)")
    ax.set_title("Memoria: densa vs. dispersa (log-log)")
    ax.legend(fontsize=7)
    _guardar_fig(fig, "08_memoria_densa_dispersa.png")


# ---------------------------------------------------------------- Figura 9: memoria por componente
def fig_memoria_por_componente(n=200000, K=8, hilos=12):
    # Tamanos teoricos en bytes, floats de 4 bytes salvo donde se indique.
    componentes = {
        "coordenadas (x,y)": 2 * n * 4,
        "vecinas (nbr, u32)": n * K * 4,
        "distancias (dst)": n * K * 4,
        "tau": n * K * 4,
        "tau2 (segunda feromona)": n * K * 4,
        "pesos (w, etaB, delta)": 3 * n * K * 4,
        "estado por hilo (vis,cnt,tourC,tourE,bestC,bestE)": hilos * 6 * n * 4,
    }
    nombres = list(componentes.keys())
    valores_mb = [v / 1e6 for v in componentes.values()]
    total = sum(valores_mb)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(nombres, valores_mb, color=PALETA[0])
    ax.set_xlabel("Memoria estimada (MB)")
    ax.set_title(f"Memoria por componente (n={n}, K={K}, {hilos} hilos); total teórico ≈ {total:.1f} MB")
    _guardar_fig(fig, "09_memoria_por_componente.png")
    print(f"memoria teorica total: {total:.1f} MB (comparar con el pico medido en escalamiento_disperso.csv)")


# ---------------------------------------------------------------- Figura 12: longitud vs NN y BHH
def fig_longitud_vs_referencias():
    filas = []
    n20 = pd.read_csv(_ruta_r("instancia_n20.csv"))
    filas.append(("n=20", n20["L_mejor"].mean(), n20["optimo_exacto"].mean(), None))
    sc = pd.read_csv(_ruta_r("seleccion_configuracion.csv"))
    ref2000 = sc[sc["configuracion"] == "candidata_b_segunda_feromona"]
    bhh2000 = 0.7124 * math.sqrt(2000) * 1.033  # misma formula del programa (factor asintotico)
    filas.append(("n=2\\,000", ref2000["L_mejor"].astype(float).mean(), None, bhh2000))

    ruta200k = _ruta_r("resultado_n200000_punto5.csv")
    if os.path.exists(ruta200k):
        d = pd.read_csv(ruta200k)
        bhh200k = 0.7124 * math.sqrt(200000) * 1.033
        filas.append(("n=200\\,000", d["L_mejor"].astype(float).mean(), None, bhh200k))

    print("Comparacion longitud vs referencias (ver tabla generada en informe/tablas/longitud_referencias.tex):")
    lineas = []
    for nombre, l_aco, opt, bhh in filas:
        opt_s = f"{opt:.3f}" if opt is not None else "--"
        bhh_s = f"{bhh:.3f}" if bhh is not None else "--"
        lineas.append(f"{nombre} & {l_aco:.3f} & {opt_s} & {bhh_s} \\\\")
        print(nombre, l_aco, opt, bhh)
    tabla = (
        "\\begin{table}[H]\\centering\n"
        "\\caption{Longitud del mejor tour contra óptimo exacto (n=20) y aproximación BHH (n grande).}\n"
        "\\label{tab:longitud_referencias}\n"
        "\\begin{tabular}{lrrr}\\toprule\n"
        "\\rowcolor{gray!25}\n"
        "\\textbf{Instancia} & \\textbf{$L_{ACO}$} & \\textbf{Óptimo exacto} & \\textbf{Aprox. BHH} \\\\\\midrule\n"
        + "\n".join(lineas) +
        "\n\\bottomrule\\end{tabular}\\end{table}\n"
    )
    _guardar_tabla("longitud_referencias.tex", tabla)


# ---------------------------------------------------------------- Figura 11: tours finales
def fig_tours_finales():
    for nombre_csv, titulo, archivo in [
        ("tour_n20.csv", "Tour final, n=20", "11_tour_n20.png"),
        ("tour_n2000.csv", "Tour final, n=2\\,000".replace("\\,", " "), "11_tour_n2000.png"),
    ]:
        ruta = _ruta_r(nombre_csv)
        if not os.path.exists(ruta):
            print(f"{ruta} no existe todavia; correr aco_tsp.exe con --tour antes de esta figura")
            continue
        df = pd.read_csv(ruta, sep=r"\s+", header=None, names=["ciudad", "x", "y"])
        xs = list(df["x"]) + [df["x"].iloc[0]]
        ys = list(df["y"]) + [df["y"].iloc[0]]
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.plot(xs, ys, "-o", color=PALETA[0], markersize=3, linewidth=1)
        ax.set_title(titulo)
        ax.set_aspect("equal")
        _guardar_fig(fig, archivo)

    ruta200k = _ruta_r("tour_n200000.csv")
    if os.path.exists(ruta200k):
        df = pd.read_csv(ruta200k, sep=r"\s+", header=None, names=["ciudad", "x", "y"])
        # fragmento ampliado: recorte central del 2% del area
        cx, cy = df["x"].median(), df["y"].median()
        r = 0.05
        frag = df[(df["x"].between(cx - r, cx + r)) & (df["y"].between(cy - r, cy + r))]
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.plot(frag["x"], frag["y"], "-o", color=PALETA[0], markersize=2, linewidth=0.8)
        ax.set_title("Fragmento ampliado del tour, n=200\\,000".replace("\\,", " "))
        ax.set_aspect("equal")
        _guardar_fig(fig, "11_tour_n200000_fragmento.png")
    else:
        print("tour_n200000.csv no existe todavia; se omite el fragmento de n=200000")


FUNCIONES = {
    "factorial": fig_factorial,
    "tabla_n20": tabla_resultados_n20,
    "tabla_n2000": tabla_resultados_n2000,
    "boxplots": fig_boxplots_configuracion,
    "tiempo_vs_m": fig_tiempo_vs_m,
    "tiempo_vs_n": fig_tiempo_vs_n,
    "convergencia": fig_convergencia,
    "heatmaps": fig_heatmaps,
    "efecto_k_segunda_feromona": fig_efecto_k_y_segunda_feromona,
    "aceleracion_hilos": fig_aceleracion_hilos,
    "memoria_densa_dispersa": fig_memoria_densa_dispersa,
    "memoria_por_componente": fig_memoria_por_componente,
    "longitud_vs_referencias": fig_longitud_vs_referencias,
    "tours_finales": fig_tours_finales,
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
