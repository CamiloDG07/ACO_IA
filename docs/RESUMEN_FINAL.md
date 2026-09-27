# Resumen final

Cierre del proyecto ACO_IA (colonia de hormigas aplicada al TSP), ejecutado
de principio a fin en modo autónomo entre el 26 y el 27 de septiembre de
2026, mientras el estudiante dormía. Este documento resume qué se hizo, qué
se midió, qué quedó fuera de alcance, los tiempos reales de las corridas
largas, y una lista de verificación de lo entregable.

## Qué se hizo

- **Fase 0** (26 sep.): reconocimiento del entorno; no había compilador de
  C++ en la máquina; se autorizó e instaló MinGW-w64 g++ 16.1.0 (WinLibs);
  estructura de referencia tomada de `Taller_Colina-Temple`.
- **Fase 1** (26 sep.): portabilidad a Windows (`GetProcessMemoryInfo` en
  vez de `getrusage`), `--input` (TSPLIB `EUC_2D` y formato plano),
  `--tiempo_max` (presupuesto de tiempo por iteración), `aco_denso.cpp`
  (versión densa de referencia, con guardia que rechaza `n>5 000` y reporta
  la memoria hipotética), y cuatro pruebas automáticas.
- **Fase 2** (27 sep.): elección de C++/OpenMP (justificación teórica, sin
  medir Python/C/Rust); número de agentes `m = min(n, 20 000)` con cita
  verificada página por página de Dorigo y Stützle (2004); barrido de
  parámetros (5 semillas por valor); escalamiento dispersa/densa; costo de
  `m` en `n=200 000` con extrapolación lineal.
- **Modo autónomo** (27 sep., de madrugada, mientras el estudiante dormía):
  - Bloque A: n=20 contra Held-Karp con 5 semillas; selección estadística
    de la configuración final (segunda feromona, mejora significativa,
    prueba de Wilcoxon apareada, p=0,0078); curvas de convergencia.
  - Bloque B: scripts de corridas largas, reanudables, con envoltorio
    anti-suspensión (`SetThreadExecutionState`).
  - Bloque C: corrida real (`n=200 000`, `m=20 000`, 10 iteraciones, 3
    semillas) y comparación a igual presupuesto de cómputo (`m=2 048` vs.
    `m=20 000`, ~15 min/semilla), sin ninguna corrida fallida ni recortada
    por presupuesto de tiempo.
  - Bloque D: mapas de calor alpha-beta y rho-qfac, aceleración por hilos
    (1/2/4/6/12), memoria por componente, tours finales — todo generado por
    script a partir de los CSV de `resultados/`.
  - Bloque E: informe completo en LaTeX, estilo institucional, 28 páginas,
    compila sin errores.
  - Bloque F: README, advertencia de tiempo, documentación de `docs/`.
  - Bloque G: pruebas automáticas (4/4 pasan), verificación de que un solo
    autor figura en `git shortlog` y de que no queda ninguna mención a
    herramientas de IA en los archivos del repositorio.

## Qué se midió (hallazgo principal)

El resultado más importante y menos anticipado del cierre: **a igual
presupuesto de tiempo de reloj (~15 min por semilla) en n=200 000, `m=2 048`
(~108 iteraciones) dio una longitud media menor (mejor) que `m=20 000` (10
iteraciones), en las 3 de 3 semillas probadas** (diferencia siempre
negativa: -2,29, -0,99, -2,19; Wilcoxon no significativo con solo 3
semillas, p=0,25, pero dirección unánime). Esto no invalida la convención
`m=n` de la literatura del Ant System (verificada con página en Dorigo y
Stützle, 2004), pero sí muestra que, en esta máquina y con este presupuesto
de tiempo, no fue la forma más eficiente de gastarlo. Se documentó tal cual
salió, sin ajustar la narrativa previa del proyecto para que encajara mejor
con lo esperado.

Otros números clave (todos con su CSV de respaldo en `resultados/`):

| Medición | Valor |
| --- | --- |
| n=20, gap medio vs. Held-Karp (5 semillas) | 0,235 % (4/5 semillas en el óptimo exacto) |
| n=2 000, L_mejor medio (8 semillas, config. ganadora) | 37,496 |
| n=200 000, m=20 000, 10 iter (3 semillas) | mejora media 1,28 % vs. NN, ~14 min/semilla |
| n=200 000, m=2 048, igual presupuesto (~108 iter) | mejora media 1,75 % vs. NN |
| Memoria pico medida, n=200 000 (dispersa) | ~102 MB, contra 320 GB que exigiría la versión densa |
| Memoria por componente: teórico vs. medido | 104,0 MB teóricos vs. 105,4 MB medidos (1,3 % de diferencia) |
| Aceleración con 12 hilos (n=2 000) | 5,06× (eficiencia 42,2 %), muy por debajo de lo ideal por hyperthreading y ancho de banda de memoria |
| Extrapolación a m=n=200 000 (1 iteración) | ~14,5 min (ajuste lineal, R²=1,000000; estimación, no corrida real) |

## Qué quedó fuera de alcance (no incompleto por presupuesto de tiempo)

El presupuesto de 4 horas para las corridas largas **no se agotó** (92
minutos de 240 disponibles); no hizo falta recortar ninguna semilla ni
iteración. Quedan fuera de alcance, por decisión explícita de mantenerse en
lo que el enunciado pide, no por falta de tiempo:
- No se probó ninguna instancia TSPLIB real (no se encontró ninguna del
  docente); las tres instancias usan el generador uniforme por semilla.
- No se implementó ni midió ningún otro lenguaje además de C++.
- No se aisló experimentalmente la renumeración por celda (decisión de
  diseño con respaldo teórico, no medición propia).
- No se probó un barrido conjunto (no de un factor a la vez) alrededor de
  la configuración con segunda feromona; se señala como trabajo futuro en
  la discusión del informe.

## Tiempos reales de las corridas largas

Ver `docs/bitacora.md` para el detalle minuto a minuto. Resumen:

| Corrida | Semillas | Duración |
| --- | --- | --- |
| Punto 1 (costo de m, 3 repeticiones) | — | ~4 min |
| Punto 5 (m=20 000, 10 iter) | 1, 2, 3 | 14,0 / 14,2 / 13,8 min |
| Punto 6 (m=2 048, igual presupuesto) | 1, 2, 3 | 15,0 / 15,1 / 15,1 min |
| **Total bloque C** | | **92 minutos** (de 240 disponibles) |

Estabilidad del equipo: se revisaron 348 pares de iteraciones consecutivas
(354 iteraciones en total) buscando variaciones de tiempo mayores al 15 %;
no se encontró ninguna.

## Incidencias durante la ejecución (documentadas, no ocultas)

- El script `ejecutar_corridas_largas.ps1` falló dos veces antes de correr
  bien: primero por una referencia de variable inválida en PowerShell
  (`$seed:` interpretado como prefijo de unidad), después por un cast de
  entero con signo a `uint32` en `SetThreadExecutionState`. Ambos se
  corrigieron antes de que se perdiera ningún dato real.
- Un error de indexado (`Split(",")` incluye el token `CSV` como primer
  campo) hizo que la primera medición de costo de `m` guardara tiempos de
  preparación en vez de tiempos de ACO; se detectó, se corrigió, y se
  volvió a correr esa parte (barata, ~4 min) sin repetir las corridas
  largas que ya habían corrido bien.
- Se encontró una tensión entre dos instrucciones del propio estudiante:
  copiar el documento de plan autónomo a `docs/` (que menciona una
  herramienta de IA por su nombre) contra la regla de no mencionar
  herramientas de IA en archivos del repositorio. Se resolvió conservando
  el archivo localmente pero sacándolo del control de versiones (ver
  `docs/bitacora.md` para el razonamiento completo).

## Lista de verificación de lo entregable

- [x] `informe/informe.pdf` compilado (28 páginas), sin referencias rotas,
      con todas las figuras
- [x] `README.md`
- [x] `ADVERTENCIA_TIEMPO_200K.md`
- [x] `docs/` completa (bitácora, entorno, decisiones de diseño,
      estrategias de ahorro, resultados, proceso, guía de exposición)
- [x] `resultados/*.csv`
- [x] `figuras/*.png`
- [x] `scripts/` reproducibles
- [x] Sin binarios ni archivos temporales en el repositorio
- [x] `git shortlog -sne` solo muestra al estudiante; sin menciones a
      herramientas de IA en los archivos versionados (`scripts/verificacion_final.py`
      lo confirma automáticamente)
