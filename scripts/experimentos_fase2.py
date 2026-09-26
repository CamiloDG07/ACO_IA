#!/usr/bin/env python3
"""Fase 2: barrido de parametros, barrido de m (numero de agentes), serie de
escalamiento (n variable, m fija) y costo de m en n=200000 (para extrapolar a
m=n). Guarda cada bloque como un CSV en resultados/. No lanza las corridas
largas (m=20000 real de 10 iteraciones x 3 semillas, ni la comparacion a
igual presupuesto): esas se lanzan aparte, con confirmacion del estudiante.

Uso:
    python scripts/experimentos_fase2.py <bloque>

Bloques: barrido_parametros | barrido_m | escalamiento | costo_m_n200000 | todos
"""
import csv
import os
import re
import subprocess
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(RAIZ, "src")
RESULTADOS = os.path.join(RAIZ, "resultados")
EXE_DISPERSO = os.path.join(SRC, "aco_tsp.exe")
EXE_DENSO = os.path.join(SRC, "aco_denso.exe")

os.makedirs(RESULTADOS, exist_ok=True)

CAMPOS_CSV = ["n", "m_csv", "K_csv", "two_csv", "iters_hechas", "L_mejor", "L_nn",
              "t_preparacion", "t_aco", "pico_mem_mb"]


def ejecutar(exe, args):
    r = subprocess.run([exe, *args], capture_output=True, text=True)
    if r.returncode not in (0, 2, 3):
        raise RuntimeError(f"{exe} {args} termino con codigo {r.returncode}\nSTDERR:\n{r.stderr}\nSTDOUT:\n{r.stdout}")
    return r.stdout, r.returncode


def parsear_csv_linea(stdout):
    m = re.search(r"^CSV,(.+)$", stdout, re.MULTILINE)
    if not m:
        return None
    vals = m.group(1).split(",")
    row = {}
    for campo, v in zip(CAMPOS_CSV, vals):
        row[campo] = v
    return row


def args_desde_config(cfg):
    args = []
    for k, v in cfg.items():
        args += [f"--{k}", str(v)]
    return args


def correr_y_guardar(nombre_csv, filas_config, exe=EXE_DISPERSO, columnas_extra=None):
    """filas_config: lista de (dict_config, dict_meta) donde dict_config son los
    argumentos CLI y dict_meta son columnas extra a guardar (p.ej. 'parametro_barrido')."""
    ruta = os.path.join(RESULTADOS, nombre_csv)
    columnas_meta = list(columnas_extra) if columnas_extra else []
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = None
        for i, (cfg, meta) in enumerate(filas_config):
            t0 = time.time()
            stdout, code = ejecutar(exe, args_desde_config(cfg))
            dt_real = time.time() - t0
            row = parsear_csv_linea(stdout)
            if row is None:
                row = {c: "" for c in CAMPOS_CSV}
                row["nota"] = f"sin linea CSV (codigo {code})"
            fila = {**meta, **cfg, **row, "t_reloj_total_s": f"{dt_real:.3f}"}
            if w is None:
                encabezados = columnas_meta + list(cfg.keys()) + CAMPOS_CSV + ["t_reloj_total_s"]
                w = csv.DictWriter(f, fieldnames=encabezados, extrasaction="ignore")
                w.writeheader()
            w.writerow(fila)
            f.flush()
            print(f"  [{i+1}/{len(filas_config)}] {meta} {cfg} -> L_mejor={row.get('L_mejor')} t_aco={row.get('t_aco')}")
    print(f"guardado: {ruta}")


# ---------------------------------------------------------------- barrido de parametros
def barrido_parametros():
    SEMILLAS = [1, 2, 3, 4, 5]
    base = dict(n=2000, ants=2000, iters=50, K=10, alpha=1, beta=3, rho=0.1, qfac=1, two=0, alpha2=0.3)

    filas = []

    def variar(parametro, valores, extra=None):
        for val in valores:
            for s in SEMILLAS:
                cfg = dict(base)
                if extra:
                    cfg.update(extra)
                cfg[parametro] = val
                cfg["seed"] = s
                filas.append((cfg, {"parametro_barrido": parametro, "valor_barrido": val, "seed_meta": s}))

    variar("alpha", [0.5, 1, 1.5, 2])
    variar("beta", [1, 2, 3, 5, 8])
    variar("rho", [0.05, 0.1, 0.3, 0.5])
    variar("qfac", [0.5, 1, 3, 10])
    variar("K", [5, 8, 10, 16, 20])
    # el barrido de m (numero de agentes) se corre y guarda aparte, en barrido_m()
    # segunda feromona: apagada (ya cubierta por el baseline two=0) y encendida con distintos alpha2
    variar("alpha2", [0.1, 0.3, 0.5, 1.0], extra={"two": 1})

    correr_y_guardar("barrido_parametros.csv", filas,
                      columnas_extra=["parametro_barrido", "valor_barrido", "seed_meta"])


def barrido_m():
    """Subconjunto del barrido de parametros (variar 'ants'), guardado aparte
    para la figura de 'calidad vs m' que respalda el tope m=min(n,20000)."""
    SEMILLAS = [1, 2, 3, 4, 5]
    base = dict(n=2000, iters=50, K=10, alpha=1, beta=3, rho=0.1, qfac=1, two=0)
    filas = []
    for m in [10, 100, 1000, 2000, 20000]:
        for s in SEMILLAS:
            cfg = dict(base); cfg["ants"] = m; cfg["seed"] = s
            filas.append((cfg, {"parametro_barrido": "m", "valor_barrido": m, "seed_meta": s}))
    correr_y_guardar("barrido_m.csv", filas, columnas_extra=["parametro_barrido", "valor_barrido", "seed_meta"])


def criterio_de_parada():
    SEMILLAS = [1, 2, 3, 4, 5]
    base = dict(n=2000, ants=2000, K=10, alpha=1, beta=3, rho=0.1, qfac=1, two=0)
    filas = []
    for s in SEMILLAS:
        cfg = dict(base); cfg["iters"] = 50; cfg["seed"] = s
        filas.append((cfg, {"parametro_barrido": "criterio_parada", "valor_barrido": "iteraciones=50", "seed_meta": s}))
    for s in SEMILLAS:
        cfg = dict(base); cfg["iters"] = 1000; cfg["time"] = 5.0; cfg["seed"] = s
        filas.append((cfg, {"parametro_barrido": "criterio_parada", "valor_barrido": "tiempo=5s", "seed_meta": s}))
    for s in SEMILLAS:
        cfg = dict(base); cfg["iters"] = 1000; cfg["stall"] = 10; cfg["seed"] = s
        filas.append((cfg, {"parametro_barrido": "criterio_parada", "valor_barrido": "stall=10", "seed_meta": s}))
    correr_y_guardar("barrido_criterio_parada.csv", filas,
                      columnas_extra=["parametro_barrido", "valor_barrido", "seed_meta"])


# ---------------------------------------------------------------- escalamiento (m fija, n variable)
def escalamiento():
    # Objetivo: tiempo por iteracion y pico de memoria en funcion de n, con m fija.
    # No se busca convergencia (eso ya se mide en el barrido de parametros e instancias
    # dedicadas), asi que bastan pocas iteraciones.
    SEMILLAS = [1, 2, 3]
    M_FIJA = 2048
    ITERS = 5
    NS = [20, 200, 2000, 20000, 200000]
    filas_disp = []
    for n in NS:
        K = min(10, n - 1)
        for s in SEMILLAS:
            cfg = dict(n=n, ants=M_FIJA, iters=ITERS, K=K, alpha=1, beta=3, rho=0.1, qfac=1, two=0, seed=s)
            filas_disp.append((cfg, {"version": "dispersa", "n_meta": n, "seed_meta": s}))
    correr_y_guardar("escalamiento_disperso.csv", filas_disp,
                      exe=EXE_DISPERSO, columnas_extra=["version", "n_meta", "seed_meta"])

    filas_densa = []
    for n in [20, 200, 2000]:  # n=20000 y n=200000 quedan fuera del limite (n<=5000) de aco_denso
        for s in SEMILLAS:
            cfg = dict(n=n, ants=M_FIJA, iters=ITERS, alpha=1, beta=3, rho=0.1, qfac=1, seed=s)
            filas_densa.append((cfg, {"version": "densa", "n_meta": n, "seed_meta": s}))
    correr_y_guardar("escalamiento_denso.csv", filas_densa,
                      exe=EXE_DENSO, columnas_extra=["version", "n_meta", "seed_meta"])


# ---------------------------------------------------------------- costo de m en n=200000 (extrapolacion a m=n)
def costo_m_n200000():
    filas = []
    for m in [200, 2000, 20000]:
        cfg = dict(n=200000, ants=m, iters=1, K=8, alpha=1.5, beta=5, rho=0.1, qfac=3, seed=1)
        filas.append((cfg, {"n_meta": 200000, "m_meta": m}))
    correr_y_guardar("costo_m_n200000.csv", filas, columnas_extra=["n_meta", "m_meta"])


BLOQUES = {
    "barrido_parametros": barrido_parametros,
    "barrido_m": barrido_m,
    "criterio_de_parada": criterio_de_parada,
    "escalamiento": escalamiento,
    "costo_m_n200000": costo_m_n200000,
}


def main():
    if len(sys.argv) < 2:
        print(f"uso: python {sys.argv[0]} <bloque>  (bloques: {', '.join(BLOQUES)}, todos)")
        sys.exit(1)
    bloque = sys.argv[1]
    if bloque == "todos":
        for nombre, fn in BLOQUES.items():
            print(f"=== {nombre} ===")
            fn()
        return
    if bloque not in BLOQUES:
        print(f"bloque desconocido: {bloque}")
        sys.exit(1)
    BLOQUES[bloque]()


if __name__ == "__main__":
    main()
