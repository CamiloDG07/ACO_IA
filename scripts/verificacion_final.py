#!/usr/bin/env python3
"""Bloque G: verificacion final automatica, sin preguntar. Revisa autoria de
git, menciones a IA en el repositorio, archivos grandes/temporales fuera de
.gitignore, y que el PDF del informe exista con al menos algunas paginas.
Imprime un reporte; no corrige nada por si solo salvo donde se indique.
"""
import os
import re
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sh(cmd):
    r = subprocess.run(cmd, shell=True, cwd=RAIZ, capture_output=True, text=True)
    return r.stdout.strip(), r.stderr.strip(), r.returncode


def main():
    problemas = []

    out, err, _ = sh("git --no-pager shortlog -sne HEAD")
    print("=== git shortlog -sne ===")
    print(out)
    if len(out.splitlines()) != 1:
        problemas.append("mas de un autor/colaborador en git shortlog")

    out, _, _ = sh('git --no-pager log --all --format="%an %ae %s%n%b"')
    # Terminos especificos de herramientas de IA, no palabras genericas del
    # dominio (evitar falsos positivos con "Inteligencia Artificial", el
    # nombre del curso, o "ACO_IA", el nombre del proyecto).
    patron = re.compile(r"claude|anthropic|co-authored-by|generated with",
                         re.IGNORECASE)
    lineas_sospechosas = [l for l in out.splitlines() if patron.search(l)]
    if lineas_sospechosas:
        problemas.append(f"menciones de IA en mensajes de commit: {lineas_sospechosas}")

    print("\n=== grep de 'claude'/'anthropic'/'IA' en archivos versionados (excluyendo docs/PROMPT_*.md) ===")
    out, _, _ = sh('git ls-files')
    # .gitignore es la excepcion esperada: solo referencia el nombre de un
    # archivo excluido (ver docs/bitacora.md), no menciona la herramienta
    # como autora de nada.
    # scripts/verificacion_final.py tambien se excluye: su propio patron de
    # busqueda contiene esas palabras como texto de deteccion, no como mencion.
    excluidos = {".gitignore", "scripts/verificacion_final.py"}
    archivos = [f for f in out.splitlines() if not f.startswith("docs/PROMPT_") and f not in excluidos]
    for archivo in archivos:
        ruta = os.path.join(RAIZ, archivo)
        if not os.path.isfile(ruta):
            continue
        try:
            with open(ruta, encoding="utf-8", errors="ignore") as f:
                contenido = f.read()
        except Exception:
            continue
        if patron.search(contenido):
            problemas.append(f"posible mencion de IA en {archivo}")
            print("  aviso:", archivo)

    print("\n=== archivos grandes (>5MB) rastreados por git ===")
    out, _, _ = sh('git ls-files')
    for archivo in out.splitlines():
        ruta = os.path.join(RAIZ, archivo)
        if os.path.isfile(ruta) and os.path.getsize(ruta) > 5 * 1024 * 1024:
            problemas.append(f"archivo grande versionado: {archivo}")
            print("  aviso:", archivo)

    print("\n=== .exe/.o/.pdb versionados por error ===")
    out, _, _ = sh('git ls-files')
    for archivo in out.splitlines():
        if archivo.endswith((".exe", ".o", ".obj", ".pdb")):
            problemas.append(f"binario versionado: {archivo}")
            print("  aviso:", archivo)

    print("\n=== informe.pdf ===")
    pdf = os.path.join(RAIZ, "informe", "informe.pdf")
    if not os.path.exists(pdf):
        problemas.append("informe/informe.pdf no existe")
        print("  no existe")
    else:
        print(f"  existe, {os.path.getsize(pdf)} bytes")

    print("\n=== resumen ===")
    if problemas:
        print(f"{len(problemas)} problema(s) encontrado(s):")
        for p in problemas:
            print(" -", p)
        sys.exit(1)
    print("sin problemas detectados")


if __name__ == "__main__":
    main()
