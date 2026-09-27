# ACO_IA — Colonia de hormigas aplicada al TSP

**Antes de ejecutar la instancia de 200 000 ciudades con muchas hormigas,
leer [`ADVERTENCIA_TIEMPO_200K.md`](ADVERTENCIA_TIEMPO_200K.md): algunas
corridas de este proyecto toman horas.**

Taller del curso de Inteligencia Artificial (Universidad Sergio Arboleda,
SIST5036). Aplica la optimización por colonia de hormigas (ACO) al problema
del viajante (TSP) en tres instancias: 20, 2 000 y 200 000 ciudades, con
énfasis en medir y ahorrar tiempo y memoria.

Equipo: Mario Jiménez, Juan David Andrade y Camilo Andrés Díaz García.

## Estructura del repositorio

```
ACO_IA/
  README.md                    este archivo
  ADVERTENCIA_TIEMPO_200K.md    tiempos y memoria esperados en n=200000
  src/                          aco_tsp.cpp (dispersa) y aco_denso.cpp (densa, referencia)
  scripts/                      lanzadores de experimentos, figuras y pruebas (Python/PowerShell)
  resultados/                   CSV crudos por corrida y logs
  figuras/                      PNG usados en el informe
  docs/                         bitácora, entorno, decisiones de diseño, guía de exposición
  informe/                      informe.tex, tablas/ generadas y el PDF compilado
```

## Cómo compilar

Compilador: MinGW-w64 g++ 16.1.0 o superior (WinLibs), con soporte de
C++20 y OpenMP. Instalación usada en este proyecto:

```
winget install --id BrechtSanders.WinLibs.POSIX.UCRT --accept-source-agreements --accept-package-agreements -e
```

Compilación (Windows, `-static` para no depender del PATH en tiempo de
ejecución):

```
cd src
g++ -O3 -march=native -std=c++20 -fopenmp -static aco_tsp.cpp -o aco_tsp.exe -lpsapi
g++ -O3 -march=native -std=c++20 -fopenmp -static aco_denso.cpp -o aco_denso.exe -lpsapi
```

En Linux (sin `-static` ni `-lpsapi`, usa `getrusage`):

```
g++ -O3 -march=native -std=c++20 -fopenmp aco_tsp.cpp -o aco_tsp
```

## Cómo ejecutar cada instancia

Configuración adoptada tras el barrido de parámetros (ver
`docs/decisiones_diseno.md`): `K=8 --alpha 1.5 --beta 5 --rho 0.1 --qfac 3
--two 1 --alpha2 1.0`, y número de hormigas `m = min(n, 20000)`.

```
# n = 20, contra Held-Karp
src\aco_tsp.exe --n 20 --ants 20 --iters 100 --K 19 --alpha 1.5 --beta 5 --rho 0.1 --qfac 3 --two 1 --alpha2 1.0 --seed 1 --exact 1

# n = 2 000
src\aco_tsp.exe --n 2000 --ants 2000 --iters 50 --K 8 --alpha 1.5 --beta 5 --rho 0.1 --qfac 3 --two 1 --alpha2 1.0 --seed 1

# n = 200 000 (ver la advertencia antes de correr con m = 20 000)
src\aco_tsp.exe --n 200000 --ants 20000 --iters 10 --K 8 --alpha 1.5 --beta 5 --rho 0.1 --qfac 3 --two 1 --alpha2 1.0 --seed 1
```

Modo rápido para ver el programa correr en n=200 000 sin esperar horas
(`m=2 048`, 2 iteraciones, ~17 s medidos en la máquina del estudiante):

```
powershell -File scripts\ejecutar_modo_rapido.ps1
```

## Cómo reproducir las pruebas, las figuras y el informe

```
python scripts\pruebas_aco.py                   # 4 pruebas automaticas
python scripts\experimentos_fase2.py todos      # barridos cortos (parametros, m, escalamiento)
python scripts\seleccion_configuracion.py       # comparacion estadistica de configuraciones
python scripts\convergencia.py                  # curvas de convergencia (n=20, n=2000)
powershell -File scripts\ejecutar_corridas_largas.ps1   # corridas largas de n=200000 (ver advertencia)
python scripts\generar_figuras.py               # figuras (figuras/) y tablas del informe (informe/tablas/)
cd informe && latexmk -pdf informe.tex          # compila informe.pdf
```

## Resumen de resultados

*(pendiente: se completa en `docs/RESUMEN_FINAL.md` al cerrar el proyecto,
con enlaces a las tablas y figuras definitivas)*
