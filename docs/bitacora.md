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

## 2026-09-26 — Fase 2: ajuste de plan (lenguaje, número de agentes, corridas largas)

El estudiante dio un ajuste final para la Fase 2, que reemplaza cualquier
indicación previa sobre lenguaje, número de hormigas y corridas largas:

- **Lenguaje**: solo C++ con OpenMP. No se implementó nada en Python, C ni
  Rust, y no se hicieron comparaciones de lenguaje. Justificación breve y
  teórica en `docs/decisiones_diseno.md`: sobrecarga del intérprete de
  Python, acceso irregular a memoria, y GIL (sin paralelismo real de hilos).
- **Número de agentes**: `m = min(n, 20000)` en vez de `m` fijo. Antes de
  citar la convención de la literatura ("m = n" para Ant System) se verificó
  la fuente primaria: se descargó el libro completo *Ant Colony Optimization*
  (Dorigo y Stützle, 2004, MIT Press) y se localizó el texto exacto con
  número de página (p. 71, Box 3.1; pp. 103–104; p. 112; p. 217). No se citó
  ninguna página de los artículos originales de 1991/1996 por no haberlos
  verificado directamente (se cita solo lo verificado).
- **Ejecutables recompilados estáticamente** (`-static`, además de `-O3
  -march=native -std=c++20 -fopenmp -lpsapi`) para que corran sin depender
  de que el PATH tenga las DLL de MinGW-w64 en cada proceso (necesario para
  automatizar experimentos y para que el entregable corra en cualquier
  Windows sin instalar el compilador). Confirmado: corren igual desde Git
  Bash sin refrescar el PATH.
- **`scripts/experimentos_fase2.py`**: automatiza el barrido de parámetros
  (alpha, beta, rho, qfac, K, segunda feromona, 5 semillas cada uno, m=2000
  fijo en n=2000), el barrido de m (10, 100, 1000, 2000, 20000 en n=2000, 5
  semillas), el criterio de parada (iteraciones/tiempo/stall), la serie de
  escalamiento (m=2048 fijo, n en {20,200,2000,20000,200000}, dispersa y
  densa donde n≤5000) y el costo de m en n=200000 (m=200,2000,20000, una
  iteración cada uno). Corrido en segundo plano, ~35 min reales, sin errores;
  resultados en `resultados/*.csv`.
- **Extrapolación de m=n en n=200000**: tiempo medido de una iteración con
  K=8, alpha=1.5, beta=5, rho=0.1, qfac=3, semilla 1: 1,099 s (m=200), 13,056
  s (m=2000), 144,850 s (m=20000). Ajuste lineal por mínimos cuadrados:
  `t(m) ≈ 0,007285·m − 0,909` s, R²=0,999947 (prácticamente lineal, como
  predice la teoría a n y K fijos). Extrapolación a m=n=200000 ≈ 1456 s ≈
  24,3 min por iteración, coherente con la estimación independiente de la
  Fase 1 (24,5 min) obtenida por otro método (tasa efectiva medida con
  m=2048). Marcada explícitamente como estimación por extrapolación, no como
  corrida real.
- **Calidad contra m** (n=2000, K=10, alpha=1, beta=3, rho=0.1, qfac=1, 50
  iteraciones fijas, 5 semillas): la longitud media mejora solo 2,4 % al
  subir m de 10 a 20000 (39,84 → 38,89), mientras el tiempo de cómputo sube
  ~1080 veces (0,058 s → 62,7 s). Rendimientos claramente decrecientes a
  partir de m≈1000-2000, consistente con lo que Dorigo y Stützle (2004, pp.
  96–97) reportan para MMAS con búsqueda local en instancias medianas.
- Con estos datos (número de iteraciones fijo, no tiempo de reloj fijo), la
  saturación de calidad sugiere que el tope m=20000 responde al presupuesto
  de tiempo y no a una necesidad de calidad — pero esta conclusión queda
  sujeta a confirmarse con la comparación a igual presupuesto de cómputo en
  n=200000 (m=2048 vs m=20000, 3 semillas), que es una de las corridas
  largas **todavía no lanzada**.
- Documentación actualizada: `docs/decisiones_diseno.md` (lenguaje y número
  de agentes, secciones (a)-(e) completas salvo la comparación a igual
  presupuesto), `informe/informe.tex` (mismo contenido resumido en la
  sección "Diseño de la solución", compila a PDF de 6 páginas sin errores),
  `docs/guia_exposicion.md` (respuesta corta a "por qué esa cantidad de
  hormigas").
- **Pendiente, con confirmación del estudiante antes de lanzar** (corridas
  largas, al final, cuando no esté usando el PC):
  1. Corrida real n=200000, m=20000, 10 iteraciones, K=8/alpha1.5/beta5/
     rho0.1/Q3, hasta 3 semillas si el tiempo alcanza. Estimado ~24,5
     min/semilla ⇒ ~1 h 14 min con 3 semillas.
  2. Comparación a igual presupuesto de cómputo en n=200000: m=2048 contra
     m=20000, mismo tiempo de reloj (propuesto 15 min por corrida), 3
     semillas. Estimado ~1 h 30 min.

## 2026-09-27 — Modo autónomo: cierre completo del proyecto

El estudiante entregó `docs/PROMPT_FINAL_AUTONOMO.md` y pidió ejecutarlo de
principio a fin sin preguntar, porque estará dormido. Se sigue ese modo:
ninguna decisión no cubierta se deja sin anotar aquí, ningún dato se inventa,
y cualquier error se documenta y no detiene el resto del trabajo.

**Reorientación (bloque 1):** se leyeron `docs/PROMPT_UNICO_CLAUDE_CODE.md`,
`docs/bitacora.md`, `docs/entorno.md`, `git log --oneline` y `resultados/`.
Confirmado: Fases 0 y 1 cerradas; Fase 2 con barrido de parámetros, barrido
de m, criterio de parada, escalamiento (dispersa+densa) y costo de m en
n=200000 ya completos (commit `3c222cb`). No se encontró ningún archivo de
instancias del docente en `ACO_IA` ni en `Descargas`; se continúa con el
generador uniforme por semilla, como estaba decidido.

**Bloque A — cerrar corridas cortas:**
- `resultados/instancia_n20.csv`: n=20, m=20 (regla m=min(n,20000)), K=19,
  5 semillas, contra Held-Karp. 4 de 5 semillas llegan al óptimo exacto; la
  semilla 1 queda a 1,176 % (mismo orden que la nota preliminar del
  enunciado: "2 de 3 semillas... y una quedó en 1,18 %").
- **Selección de configuración para las corridas grandes**
  (`scripts/seleccion_configuracion.py`,
  `resultados/seleccion_configuracion.csv` y
  `resultados/seleccion_configuracion_veredicto.txt`): se comparó la
  configuración de referencia (K=8, alpha=1.5, beta=5, rho=0.1, qfac=3,
  sin segunda feromona) contra dos candidatas construidas con los mejores
  valores individuales del barrido de parámetros, con las mismas 8 semillas
  (comparación apareada) y prueba de Wilcoxon:
  - Candidata con los mejores valores individuales de cada parámetro
    (K=5, alpha=2.0, beta=8, rho=0.5, qfac=10): media 38,15 contra 37,94 de
    la referencia, **peor** (p=0,055, no significativo de todas formas).
    Confirma que optimizar cada parámetro por separado, manteniendo los
    demás en su valor por defecto, no garantiza una mejor combinación
    conjunta (posible interacción entre parámetros).
  - Candidata con segunda feromona activada (misma referencia, `two=1`,
    `alpha2=1.0`, que cumple `alpha2 < alpha` como pide el diseño): media
    37,50 contra 37,94, **mejor**, con p=0,0078 (Wilcoxon apareado,
    n=8 semillas) — diferencia estadísticamente significativa.
  - **Veredicto: se adopta la configuración con segunda feromona** (K=8,
    alpha=1.5, beta=5, rho=0.1, qfac=3, two=1, alpha2=1.0) para el resultado
    oficial de n=2000 y para las corridas grandes de n=200000 en vez de la
    configuración de referencia original del prompt base, siguiendo la regla
    de "usar la mejor y explicarlo" cuando el barrido muestra una diferencia
    clara.
- **Curvas de convergencia** (`scripts/convergencia.py`,
  `resultados/convergencia_n20.csv`, `resultados/convergencia_n2000.csv`):
  3 semillas cada una, con la configuración ganadora, capturando cada línea
  de iteración (mejor de la iteración, mejor global, media de las hormigas,
  tiempo) para la Figura 2 del informe.
- Ya estaban completos de antes (commit `3c222cb`): barrido de alpha, beta,
  rho, qfac, K (5 semillas cada valor), barrido de m, segunda feromona con
  alpha2 en 0,1/0,3/0,5/1,0, criterios de parada, y escalamiento dispersa y
  densa. No se relanzó nada de eso.
- Confirmado (`Get-Process` sin `aco_tsp`/`aco_denso` activos) que no queda
  ningún proceso de ACO corriendo antes de pasar al bloque B/C.

### Corridas largas: inicio 2026-09-27 04:41:37
Punto 1 (costo por iteracion, 3 repeticiones) terminado: 2026-09-27 04:46:23

**Error detectado (bloque B/C, punto 1):** el script
`scripts/ejecutar_corridas_largas.ps1` tenía un error de indexado al extraer
`t_aco` de la línea `CSV,...`: `Split(",")` sobre la línea completa incluye
el token `CSV` como primer elemento, corriendo el índice de todos los campos
en uno; el script leía `campos[8]` (que en realidad es `t_preparacion`) en
vez de `campos[9]` (`t_aco`). Por eso `costo_m_n200000_3reps.csv` quedó con
tiempos de preparación (~0,05 s) en vez de tiempos de ACO, para las tres
`m`. Se corrigió el índice en el script y se borró el CSV incorrecto (no se
había commiteado). Punto 5 (la corrida real) no se vio afectado, porque mide
sus tiempos con `Get-Date` directamente, no parseando el CSV. Se vuelve a
correr el punto 1 (barato, ~8 min) después de que terminen los puntos 5 y 6,
sin relanzar nada de lo que ya corrió bien.
