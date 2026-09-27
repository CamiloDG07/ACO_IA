#!/usr/bin/env python3
"""Compara la configuracion de referencia (K=8, alpha=1.5, beta=5, rho=0.1,
qfac=3) contra candidatas construidas a partir de los mejores valores
individuales del barrido de parametros (resultados/barrido_parametros.csv),
con las mismas semillas (comparacion apareada) y una prueba de Wilcoxon.
Guarda resultados/seleccion_configuracion.csv y el veredicto en
resultados/seleccion_configuracion_veredicto.txt.
"""
import csv
import os
import re
import subprocess

import numpy as np
from scipy.stats import wilcoxon

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(RAIZ, "src", "aco_tsp.exe")
RESULTADOS = os.path.join(RAIZ, "resultados")

SEMILLAS = list(range(1, 9))  # 8 semillas, apareadas entre configuraciones

CONFIGS = {
    "referencia": dict(n=2000, ants=2000, iters=50, K=8, alpha=1.5, beta=5, rho=0.1, qfac=3, two=0),
    "candidata_a_individuales": dict(n=2000, ants=2000, iters=50, K=5, alpha=2.0, beta=8, rho=0.5, qfac=10, two=0),
    "candidata_b_segunda_feromona": dict(n=2000, ants=2000, iters=50, K=8, alpha=1.5, beta=5, rho=0.1, qfac=3,
                                          two=1, alpha2=1.0),
}


def ejecutar(args):
    r = subprocess.run([EXE, *args], capture_output=True, text=True)
    m = re.search(r"L_mejor=([\d.]+)", r.stdout)
    if not m:
        raise RuntimeError(f"sin L_mejor en salida: {args}\n{r.stdout}\n{r.stderr}")
    return float(m.group(1))


def args_desde(cfg, seed):
    args = []
    for k, v in cfg.items():
        args += [f"--{k}", str(v)]
    args += ["--seed", str(seed)]
    return args


def main():
    filas = []
    resultados = {}
    for nombre, cfg in CONFIGS.items():
        vals = []
        for s in SEMILLAS:
            L = ejecutar(args_desde(cfg, s))
            vals.append(L)
            filas.append({"configuracion": nombre, "seed": s, "L_mejor": L, **cfg})
        resultados[nombre] = np.array(vals)
        print(f"{nombre}: media={vals and np.mean(vals):.4f} std={np.std(vals, ddof=1):.4f}")

    ruta = os.path.join(RESULTADOS, "seleccion_configuracion.csv")
    campos = ["configuracion", "seed", "L_mejor", "n", "ants", "iters", "K", "alpha", "beta", "rho", "qfac",
              "two", "alpha2"]
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        for fila in filas:
            w.writerow(fila)
    print("guardado:", ruta)

    ref = resultados["referencia"]
    lineas = []
    lineas.append(f"Referencia: media={ref.mean():.4f} std={ref.std(ddof=1):.4f} (n={len(ref)} semillas)")
    ganador = "referencia"
    mejor_media = ref.mean()
    for nombre, vals in resultados.items():
        if nombre == "referencia":
            continue
        stat, p = wilcoxon(vals, ref)
        diff = vals.mean() - ref.mean()
        lineas.append(
            f"{nombre}: media={vals.mean():.4f} std={vals.std(ddof=1):.4f} "
            f"diff_vs_ref={diff:+.4f} wilcoxon_p={p:.4f} "
            f"{'(mejor, p<0.05)' if (p < 0.05 and diff < 0) else '(sin diferencia significativa o peor)'}"
        )
        if p < 0.05 and vals.mean() < mejor_media:
            ganador = nombre
            mejor_media = vals.mean()
    lineas.append(f"\nVeredicto: configuracion elegida para las corridas grandes = {ganador}")
    veredicto = "\n".join(lineas)
    print(veredicto)
    with open(os.path.join(RESULTADOS, "seleccion_configuracion_veredicto.txt"), "w", encoding="utf-8") as f:
        f.write(veredicto + "\n")


if __name__ == "__main__":
    main()
