# Bitácora

Registro cronológico de decisiones, pruebas, errores y resultados del taller
ACO_IA. Incluye los intentos que no funcionaron, no solo el resultado final.

## 2026-09-26 — Fase 0: entorno y reconocimiento

- Se copió `D:\camilo\Descargas\aco_tsp.cpp` a `src/aco_tsp.cpp` y se leyó
  completo: usa `getrusage`/`sys/resource.h` (solo Linux), OpenMP y
  `std::atomic_ref<float>` (C++20).
- No había ningún compilador de C++ en la máquina (ni MinGW-w64, ni MSVC —
  no existe `vswhere.exe`, Visual Studio no está instalado —, ni clang, ni
  WSL). Se presentaron cuatro opciones al estudiante (WinLibs/MinGW-w64,
  MSYS2, Visual Studio Build Tools, WSL) y se autorizó instalar **WinLibs
  GCC 16.1.0 (MinGW-w64, UCRT)** vía `winget`.
- Prueba mínima de C++20 + `std::atomic_ref<float>` + OpenMP: compila y
  corre sin problemas (`omp_get_max_threads()=12`). No hizo falta sustituir
  `atomic_ref` por ninguna alternativa.
- Compilación de diagnóstico de `aco_tsp.cpp` tal cual: falla, como se
  esperaba, en `#include <sys/resource.h>` (no existe en Windows).
- Se documentó todo en `docs/entorno.md` y la comparación con el taller de
  referencia en `docs/estructura_referencia.md`. Repositorio inicializado,
  conectado a `https://github.com/CamiloDG07/ACO_IA.git`, primeros commits
  y push a `main` sin pedir credenciales (Git Credential Manager).

## 2026-09-26 — Fase 1: base de código

- **Portar a Windows**: se reemplazó `peakRssMB()` (que usaba `getrusage`)
  por una versión con `#ifdef _WIN32` que llama a `GetProcessMemoryInfo` y
  reporta `PeakWorkingSetSize`. Requiere enlazar con `-lpsapi`. Compila y
  corre sin errores ni advertencias con
  `g++ -O3 -march=native -std=c++20 -fopenmp aco_tsp.cpp -o aco_tsp.exe -lpsapi`.
- **`--input`**: se añadió lectura básica de TSPLIB `EUC_2D`
  (`NODE_COORD_SECTION` ... `EOF`) y de un formato plano de dos columnas
  `x y` por línea, autodetectado por la presencia de palabras clave de
  TSPLIB al inicio del archivo. Las coordenadas originales se normalizan a
  `[0,1]^2` guardando el factor de escala (`I.scale`) y el desplazamiento
  del bounding box (`I.offX`, `I.offY`); al final se reporta
  `L_mejor`/`L_nn` también en las unidades originales
  (`L_normalizada * escala`). El generador uniforme por semilla sigue
  siendo el comportamiento por defecto cuando no se pasa `--input`.
  Probado con un archivo TSPLIB de 5 ciudades (cuadrado de lado 10) y con
  el mismo caso en formato plano: ambos detectan el formato correctamente,
  dan el mismo óptimo exacto por Held-Karp y reportan
  `factor_escala=10.000000` con las longitudes reescaladas.
- **`--tiempo_max`** (presupuesto de tiempo por iteración, distinto de
  `--time`, que es el presupuesto total): dentro del bucle paralelo de
  hormigas de cada iteración se mide el tiempo transcurrido desde el
  inicio de esa iteración; al superarse `--tiempo_max`, las hormigas que
  ya estaban en curso terminan normalmente (no se interrumpen a medio
  tour) y las que aún no habían arrancado simplemente no se construyen
  (`continue` dentro del `#pragma omp for`). La iteración se cierra de
  forma consistente: evaporación y depósito de feromona ocurren igual,
  usando solo las hormigas que sí corrieron; el promedio de longitud por
  hormiga (`media_hormigas`) se calcula sobre esas mismas hormigas
  (`antsRun`), no sobre `m`, para no sesgar la estadística. Se imprime un
  aviso por iteración cuando `antsRun < m`. Efecto observado en la prueba
  (`n=2000`, `m=2048`, `--tiempo_max 0.01`): solo 90-92 de 2048 hormigas
  llegan a construirse por iteración; la calidad del tour empeora respecto
  a no usar el corte (`L_mejor` sube de ~38 a ~46 en 3 iteraciones), lo
  cual es el trueque esperado entre presupuesto de tiempo y calidad.
- **`src/aco_denso.cpp`**: versión de referencia con matrices completas
  `n x n` de distancia y feromona, ruleta sobre todas las ciudades no
  visitadas (sin lista de candidatas). Tiene una guardia explícita: si
  `n > 5000`, no construye nada y solo calcula y reporta la memoria que
  exigirían las matrices densas (`2 * 4 * n^2` bytes). Probado con
  `n=20` (mismo Held-Karp, gap=1.176% con semilla 1, dentro del rango
  0-1,2 % que reporta el enunciado para el prototipo original) y con
  `n=200000` (la guardia respondió `320.000 GB` y terminó sin ejecutar,
  como pide el enunciado).
- **Pruebas automáticas** (`scripts/pruebas_aco.py`): valida (1) que el
  tour reportado es una permutación válida, (2) que la longitud reportada
  coincide con la recalculada en doble precisión, (3) reproducibilidad
  exacta con la misma semilla y un solo hilo (`OMP_NUM_THREADS=1`, dos
  corridas idénticas), y (4) que en `n=20` el ACO nunca reporta una
  longitud menor que el óptimo exacto de Held-Karp. Las cuatro pasan.
- **Compilación final y corridas de verificación** (`-O3 -march=native
  -std=c++20 -fopenmp`, 12 hilos lógicos):
  - `n=20`, `K=19`, `m=2048`, 50 iteraciones, semilla 1: óptimo exacto
    (`gap=0.000%`), dentro de lo esperado por el enunciado (hasta 1,2 %).
  - `n=2000`, `K=8`, `alpha=1.5`, `beta=5`, `rho=0.1`, `qfac=3`,
    `two=1`, `alpha2=0.3`, `m=2048`, 40 iteraciones, semilla 1:
    `L_mejor=37.82` (la nota preliminar del enunciado, con otra máquina y
    semilla, reportaba 38.20 para una configuración parecida; misma
    magnitud, diferencia esperable por semilla y por 12 hilos en vez de 2).
  - `n=200000`, `K=8`, mismos hiperparámetros, `m=2048`: pico de memoria
    96,8 MB (orden de decenas de MB, coherente con lo esperado). Con 5
    iteraciones, `L_mejor=392,88` prácticamente iguala a `L_nn=392,95`
    (`mejora_vs_nn=0.02%`), confirmando el aviso del enunciado de que con
    pocas iteraciones la calidad apenas supera al vecino más cercano.
  - Tiempo medido por iteración con `m=2048` en esta máquina (12 hilos):
    ~15,07 s/iteración ⇒ ~7,36 ms/hormiga (tasa efectiva ya paralela,
    igual que el cálculo del enunciado). Estimación para una iteración con
    `m=n=200000`: `200000 * 0,00736 s ≈ 1472 s ≈ 24,5 minutos` en esta
    máquina (más rápido que los ~43 minutos del sandbox de 2 núcleos del
    enunciado, por tener más hilos). **No se lanzó** esa corrida completa;
    queda pendiente de que el estudiante decida cuántas iteraciones caben
    en el tiempo disponible antes de ejecutarla (Fase 2).
