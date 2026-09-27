#!/usr/bin/env python3
"""Captura la curva de convergencia (mejor de la iteracion, mejor global,
media de las hormigas, tiempo) corrida completa, parseando la salida
linea a linea del programa. Genera un CSV por instancia en resultados/.
"""
import csv
import os
import re
import subprocess

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(RAIZ, "src", "aco_tsp.exe")
RESULTADOS = os.path.join(RAIZ, "resultados")

PATRON_ITER = re.compile(
    r"^\s*(\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*$")


def correr_convergencia(nombre_csv, args, seed):
    args_completos = [*args, "--seed", str(seed)]
    r = subprocess.run([EXE, *args_completos], capture_output=True, text=True)
    filas = []
    for linea in r.stdout.splitlines():
        m = PATRON_ITER.match(linea)
        if m:
            filas.append({
                "seed": seed,
                "iter": int(m.group(1)),
                "mejor_iter": float(m.group(2)),
                "mejor_global": float(m.group(3)),
                "media_hormigas": float(m.group(4)),
                "t_iter_s": float(m.group(5)),
                "t_total_s": float(m.group(6)),
            })
    ruta = os.path.join(RESULTADOS, nombre_csv)
    existe = os.path.exists(ruta)
    with open(ruta, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["seed", "iter", "mejor_iter", "mejor_global",
                                           "media_hormigas", "t_iter_s", "t_total_s"])
        if not existe:
            w.writeheader()
        for fila in filas:
            w.writerow(fila)
    print(f"{nombre_csv} (semilla {seed}): {len(filas)} iteraciones guardadas")


def main():
    # n=20: m=20, K=19, configuracion ganadora (segunda feromona)
    args20 = ["--n", "20", "--ants", "20", "--iters", "100", "--K", "19",
              "--alpha", "1.5", "--beta", "5", "--rho", "0.1", "--qfac", "3",
              "--two", "1", "--alpha2", "1.0", "--exact", "1"]
    ruta20 = os.path.join(RESULTADOS, "convergencia_n20.csv")
    if os.path.exists(ruta20):
        os.remove(ruta20)
    for s in [1, 2, 3]:
        correr_convergencia("convergencia_n20.csv", args20, s)

    # n=2000: m=2000, K=8, configuracion ganadora
    args2000 = ["--n", "2000", "--ants", "2000", "--iters", "80", "--K", "8",
                "--alpha", "1.5", "--beta", "5", "--rho", "0.1", "--qfac", "3",
                "--two", "1", "--alpha2", "1.0"]
    ruta2000 = os.path.join(RESULTADOS, "convergencia_n2000.csv")
    if os.path.exists(ruta2000):
        os.remove(ruta2000)
    for s in [1, 2, 3]:
        correr_convergencia("convergencia_n2000.csv", args2000, s)


if __name__ == "__main__":
    main()
