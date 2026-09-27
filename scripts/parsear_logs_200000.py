#!/usr/bin/env python3
"""Parsea los logs crudos de las corridas largas (resultados/log_punto5_*.txt
y log_punto6_*.txt) en CSV limpios: una fila por iteracion (para las curvas
de convergencia) y un resumen final por semilla. Los .txt quedan fuera del
repositorio (.gitignore); estos CSV son lo que se versiona.
"""
import csv
import glob
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTADOS = os.path.join(RAIZ, "resultados")

PATRON_ITER = re.compile(
    r"^\s*(\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*$")
PATRON_RESUMEN = re.compile(
    r"^n=(\d+) m=(\d+) iters=(\d+) tour_valido=(\w+) L_mejor=([\d.]+) "
    r"\(verificado ([\d.]+)\) L_nn=([\d.]+) mejora_vs_nn=(-?[\d.]+)%")
PATRON_MEM = re.compile(r"pico RSS=([\d.]+) MB")


def leer_log(ruta):
    # Los logs quedan en UTF-16 porque PowerShell "*>" redirige asi por defecto.
    for enc in ("utf-16", "utf-8"):
        try:
            with open(ruta, encoding=enc) as f:
                return f.read()
        except (UnicodeError, UnicodeDecodeError):
            continue
    raise RuntimeError(f"no se pudo leer {ruta} ni en utf-16 ni en utf-8")


def parsear_punto(prefijo, nombre_conv, nombre_resumen):
    logs = sorted(glob.glob(os.path.join(RESULTADOS, f"{prefijo}_seed*.txt")))
    filas_conv = []
    filas_resumen = []
    for ruta in logs:
        m = re.search(r"seed(\d+)", ruta)
        seed = int(m.group(1))
        texto = leer_log(ruta)
        for linea in texto.splitlines():
            mi = PATRON_ITER.match(linea)
            if mi:
                filas_conv.append({
                    "seed": seed, "iter": int(mi.group(1)), "mejor_iter": float(mi.group(2)),
                    "mejor_global": float(mi.group(3)), "media_hormigas": float(mi.group(4)),
                    "t_iter_s": float(mi.group(5)), "t_total_s": float(mi.group(6)),
                })
        mr = PATRON_RESUMEN.search(texto)
        mm = PATRON_MEM.search(texto)
        if mr:
            filas_resumen.append({
                "seed": seed, "n": int(mr.group(1)), "m": int(mr.group(2)),
                "iters_hechas": int(mr.group(3)), "tour_valido": mr.group(4),
                "L_mejor": float(mr.group(5)), "L_verificado": float(mr.group(6)),
                "L_nn": float(mr.group(7)), "mejora_vs_nn_pct": float(mr.group(8)),
                "pico_mem_mb": float(mm.group(1)) if mm else "",
            })
        else:
            print(f"AVISO: no se encontro linea de resumen en {ruta} (corrida incompleta o fallida)")

    if filas_conv:
        ruta_c = os.path.join(RESULTADOS, nombre_conv)
        with open(ruta_c, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["seed", "iter", "mejor_iter", "mejor_global",
                                               "media_hormigas", "t_iter_s", "t_total_s"])
            w.writeheader()
            for fila in filas_conv:
                w.writerow(fila)
        print("guardado:", ruta_c, f"({len(filas_conv)} filas)")
    if filas_resumen:
        ruta_r = os.path.join(RESULTADOS, nombre_resumen)
        with open(ruta_r, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["seed", "n", "m", "iters_hechas", "tour_valido",
                                               "L_mejor", "L_verificado", "L_nn", "mejora_vs_nn_pct",
                                               "pico_mem_mb"])
            w.writeheader()
            for fila in filas_resumen:
                w.writerow(fila)
        print("guardado:", ruta_r, f"({len(filas_resumen)} semillas)")
    return filas_conv, filas_resumen


def main():
    parsear_punto("log_punto5_m20000", "convergencia_n200000_punto5.csv", "resultado_n200000_punto5.csv")
    parsear_punto("log_punto6_m2048", "convergencia_n200000_punto6.csv", "resultado_n200000_punto6.csv")


if __name__ == "__main__":
    main()
