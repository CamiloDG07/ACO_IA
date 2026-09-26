#!/usr/bin/env python3
"""Pruebas automaticas de aco_tsp (Fase 1).

Verifica cuatro propiedades sobre el ejecutable compilado:
  1) el mejor tour reportado es una permutacion valida de las n ciudades;
  2) la longitud reportada coincide con la longitud recalculada en doble
     precision (verificacion interna del propio programa);
  3) con semilla fija y un solo hilo (OMP_NUM_THREADS=1), dos corridas
     identicas producen exactamente la misma longitud (reproducibilidad);
  4) para n=20, el resultado del ACO no puede ser mejor que el optimo
     exacto de Held-Karp (gap >= 0).

Uso:
    python scripts/pruebas_aco.py [ruta_al_ejecutable]

Por defecto usa src/aco_tsp.exe (o src/aco_tsp en Linux) relativo a la raiz
del repositorio.
"""
import os
import re
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ejecutar(exe, args, hilos=None):
    env = os.environ.copy()
    if hilos is not None:
        env["OMP_NUM_THREADS"] = str(hilos)
    r = subprocess.run([exe, *args], capture_output=True, text=True, env=env)
    if r.returncode not in (0, 2):
        raise RuntimeError(f"{exe} {args} termino con codigo {r.returncode}\n{r.stderr}")
    return r.stdout


def parsear_resumen(texto):
    m = re.search(r"tour_valido=(\w+)", texto)
    if not m:
        raise RuntimeError(f"no se encontro 'tour_valido=' en la salida:\n{texto}")
    valido = m.group(1) == "SI"
    m = re.search(r"L_mejor=([\d.]+) \(verificado ([\d.]+)\)", texto)
    if not m:
        raise RuntimeError(f"no se encontro 'L_mejor=...' en la salida:\n{texto}")
    l_mejor, l_verificado = float(m.group(1)), float(m.group(2))
    m = re.search(r"optimo_exacto\(Held-Karp\)=([\d.]+)\s+gap=(-?[\d.]+)%", texto)
    gap = float(m.group(2)) if m else None
    return valido, l_mejor, l_verificado, gap


def main():
    exe = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, "src", "aco_tsp.exe")
    if not os.path.exists(exe):
        exe_alt = os.path.join(RAIZ, "src", "aco_tsp")
        if os.path.exists(exe_alt):
            exe = exe_alt
    if not os.path.exists(exe):
        print(f"no se encontro el ejecutable: {exe}")
        sys.exit(2)

    fallas = []

    # 1) y 2): tour valido + longitud recalculada, instancia mediana
    out = ejecutar(exe, ["--n", "500", "--ants", "256", "--iters", "10", "--seed", "7"])
    valido, l_mejor, l_verif, _ = parsear_resumen(out)
    if not valido:
        fallas.append("n=500: el tour reportado no es una permutacion valida")
    if abs(l_mejor - l_verif) > 1e-3:
        fallas.append(f"n=500: L_mejor={l_mejor} no coincide con la longitud recalculada {l_verif}")

    # 3) reproducibilidad: misma semilla, un solo hilo, dos corridas identicas
    args_repro = ["--n", "300", "--ants", "128", "--iters", "8", "--seed", "42"]
    out1 = ejecutar(exe, args_repro, hilos=1)
    out2 = ejecutar(exe, args_repro, hilos=1)
    _, l1, _, _ = parsear_resumen(out1)
    _, l2, _, _ = parsear_resumen(out2)
    if l1 != l2:
        fallas.append(f"reproducibilidad (1 hilo, semilla 42): {l1} != {l2}")

    # 4) n=20 contra Held-Karp: el ACO no puede superar al optimo exacto
    out = ejecutar(exe, ["--n", "20", "--ants", "2048", "--iters", "50", "--K", "19",
                         "--seed", "1", "--exact", "1"])
    valido, l_mejor, l_verif, gap = parsear_resumen(out)
    if not valido:
        fallas.append("n=20: el tour reportado no es una permutacion valida")
    if gap is None:
        fallas.append("n=20: no se encontro el resultado de Held-Karp en la salida")
    elif gap < -1e-6:
        fallas.append(f"n=20: el ACO reporto una longitud menor que el optimo exacto (gap={gap}%), imposible")

    if fallas:
        print("FALLARON pruebas:")
        for f in fallas:
            print(" -", f)
        sys.exit(1)

    print("Todas las pruebas pasaron:")
    print(" - tour valido (permutacion)")
    print(" - longitud reportada == longitud recalculada")
    print(" - reproducibilidad con semilla fija y un solo hilo")
    print(" - n=20 no supera al optimo exacto de Held-Karp")


if __name__ == "__main__":
    main()
