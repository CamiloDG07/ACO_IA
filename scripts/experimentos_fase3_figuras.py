#!/usr/bin/env python3
"""Datos adicionales para las figuras del bloque D que no salen del barrido
de parametros ya guardado: mapas de calor alpha-beta y rho-qfac (n=2000), y
aceleracion/eficiencia contra numero de hilos (n=2000). Se corre DESPUES de
que terminen las corridas largas (bloque C), nunca en paralelo con ellas.
"""
import csv
import os
import re
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(RAIZ, "src", "aco_tsp.exe")
RESULTADOS = os.path.join(RAIZ, "resultados")

# Configuracion ganadora del bloque A (ver docs/decisiones_diseno.md)
BASE = dict(n=2000, ants=2000, iters=50, K=8, alpha=1.5, beta=5, rho=0.1, qfac=3, two=1, alpha2=1.0)
SEMILLAS_GRID = [1, 2, 3]


def ejecutar(args, env=None):
    r = subprocess.run([EXE, *args], capture_output=True, text=True, env=env)
    m = re.search(r"L_mejor=([\d.]+)", r.stdout)
    if not m:
        raise RuntimeError(f"sin L_mejor: {args}\n{r.stdout}\n{r.stderr}")
    t = re.search(r"ACO=([\d.]+) s", r.stdout)
    return float(m.group(1)), (float(t.group(1)) if t else None)


def args_desde(cfg, seed):
    args = []
    for k, v in cfg.items():
        args += [f"--{k}", str(v)]
    args += ["--seed", str(seed)]
    return args


def heatmap_alpha_beta():
    alphas = [0.5, 1, 1.5, 2]
    betas = [1, 2, 3, 5, 8]
    filas = []
    for a in alphas:
        for b in betas:
            for s in SEMILLAS_GRID:
                cfg = dict(BASE); cfg["alpha"] = a; cfg["beta"] = b
                L, _ = ejecutar(args_desde(cfg, s))
                filas.append({"alpha": a, "beta": b, "seed": s, "L_mejor": L})
                print(f"alpha={a} beta={b} seed={s} L={L:.4f}")
    ruta = os.path.join(RESULTADOS, "heatmap_alpha_beta.csv")
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["alpha", "beta", "seed", "L_mejor"])
        w.writeheader()
        for fila in filas:
            w.writerow(fila)
    print("guardado:", ruta)


def heatmap_rho_qfac():
    rhos = [0.05, 0.1, 0.3, 0.5]
    qfacs = [0.5, 1, 3, 10]
    filas = []
    for r_ in rhos:
        for q in qfacs:
            for s in SEMILLAS_GRID:
                cfg = dict(BASE); cfg["rho"] = r_; cfg["qfac"] = q
                L, _ = ejecutar(args_desde(cfg, s))
                filas.append({"rho": r_, "qfac": q, "seed": s, "L_mejor": L})
                print(f"rho={r_} qfac={q} seed={s} L={L:.4f}")
    ruta = os.path.join(RESULTADOS, "heatmap_rho_qfac.csv")
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["rho", "qfac", "seed", "L_mejor"])
        w.writeheader()
        for fila in filas:
            w.writerow(fila)
    print("guardado:", ruta)


def aceleracion_hilos():
    hilos_lista = [1, 2, 4, 6, 12]
    filas = []
    for hilos in hilos_lista:
        env = os.environ.copy()
        env["OMP_NUM_THREADS"] = str(hilos)
        for s in [1, 2, 3]:
            cfg = dict(BASE); cfg["iters"] = 20
            _, t_aco = ejecutar(args_desde(cfg, s), env=env)
            filas.append({"hilos": hilos, "seed": s, "t_aco_s": t_aco})
            print(f"hilos={hilos} seed={s} t_aco={t_aco}")
    ruta = os.path.join(RESULTADOS, "aceleracion_hilos.csv")
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["hilos", "seed", "t_aco_s"])
        w.writeheader()
        for fila in filas:
            w.writerow(fila)
    print("guardado:", ruta)


FUNCIONES = {
    "heatmap_alpha_beta": heatmap_alpha_beta,
    "heatmap_rho_qfac": heatmap_rho_qfac,
    "aceleracion_hilos": aceleracion_hilos,
}


def main():
    args = sys.argv[1:] or ["todos"]
    if "todos" in args:
        args = list(FUNCIONES.keys())
    for nombre in args:
        print(f"=== {nombre} ===")
        FUNCIONES[nombre]()


if __name__ == "__main__":
    main()
