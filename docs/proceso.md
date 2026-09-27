# Proceso del taller

Relato ordenado del proceso real del taller, con fechas y evidencia de
`docs/bitacora.md`, para la exposición y el informe.

## 1. Lectura del enunciado y de las diapositivas

El enunciado del docente (transcrito por el estudiante) pide aplicar
colonia de hormigas al TSP en instancias de 20, 2 000 y 200 000 ciudades,
medir tiempo y memoria, usar como mínimo 200 000 agentes según la
recomendación del docente (sin poder confirmar cuán estricta es esa
recomendación), y explicar el espacio factorial de recorridos. Las
diapositivas `07_IA_2026_2.pdf` fijan las fórmulas (heurística, transición,
evaporación, depósito) y el pseudocódigo que el código y el informe deben
respetar (ver `informe/informe.tex`, sección "Marco teórico").

## 2. Cuenta del espacio factorial y decisión de no usar matriz densa

Antes de escribir una sola línea de código del proyecto, la Fase 0 (26 de
septiembre de 2026) reconoció el entorno de la máquina y confirmó que
`aco_tsp.cpp` (el prototipo ya validado en Linux, entregado por el
estudiante) evita deliberadamente la matriz $n \times n$: con
$n=200\,000$, esa matriz exigiría 320 GB, muy por encima de los 15,88 GB de
RAM de la máquina del estudiante (`docs/entorno.md`). Esa cuenta, y no una
preferencia de estilo, es la razón de que el diseño use una lista de $K$
vecinas por ciudad en vez de una matriz completa.

## 3. Elección de C++ y OpenMP frente a Python

El prototipo ya venía en C++ con OpenMP cuando el estudiante lo entregó; el
enunciado del docente ya advertía que "Python puede no alcanzar". La
Fase 2 (27 de septiembre de 2026) formalizó esa elección con una
justificación breve y teórica (sobrecarga del intérprete, acceso irregular a
memoria, GIL sin paralelismo real), sin implementar ni medir Python, C ni
Rust (`docs/decisiones_diseno.md`, sección "Elección de lenguaje").

## 4. Diseño de estructuras y prototipo inicial ya validado

El prototipo entregado por el estudiante (antes de este repositorio) ya
pasaba, en Linux, las pruebas de: tour válido (permutación), longitud
recalculada igual a la reportada, y $n=20$ contra Held-Karp. La Fase 1
(26 de septiembre de 2026) portó ese prototipo a Windows sin cambiar su
diseño de fondo (`docs/bitacora.md`), reemplazando solo la medición de
memoria (`GetProcessMemoryInfo` en vez de `getrusage`) y agregando
`--input`, `--tiempo_max` y la versión densa de referencia
(`aco_denso.cpp`).

## 5. Primeras mediciones y hallazgos

En la Fase 1 se midió, por primera vez en la máquina del estudiante (no en
el sandbox donde se validó el prototipo original), que:
- $n=20$ alcanza el óptimo exacto de Held-Karp con la configuración de
  partida.
- $n=2\,000$ da una longitud del mismo orden que la nota preliminar del
  enunciado (37,82 contra 38,20 de referencia, en otra máquina y con una
  sola semilla).
- Con $n=200\,000$ y solo 5 iteraciones, la calidad apenas supera al vecino
  más cercano (mejora del 0,02 %), confirmando la advertencia del enunciado
  sobre pocas iteraciones en instancias grandes.
- El costo por hormiga medido (~7,36 ms efectivos, 12 hilos) hace que la
  recomendación del docente de $m \geq n$ sea costosa en $n=200\,000$: una
  sola iteración con $m=n=200\,000$ tomaría del orden de 24 minutos.

## 6. Barrido de parámetros con semillas múltiples

La Fase 2 corrió el barrido de alpha, beta, rho, qfac, K y segunda
feromona (5 semillas cada valor) y encontró, con una comparación apareada y
prueba de Wilcoxon (`scripts/seleccion_configuracion.py`), que activar la
segunda feromona (`two=1`, `alpha2=1.0`) sobre la configuración de
referencia mejora la longitud media de forma estadísticamente significativa
(p=0,0078); combinar los mejores valores individuales de cada parámetro, en
cambio, no mejoró la combinación de referencia (p=0,055, sin diferencia
significativa, y de hecho una media peor). Esa configuración con segunda
feromona se adoptó para todas las corridas grandes posteriores
(`docs/decisiones_diseno.md`).

## 7. Portabilidad a Windows

Cubierta en el punto 4: Fase 1, 26 de septiembre de 2026. Compilador
elegido: MinGW-w64 g++ 16.1.0 (WinLibs), instalado con autorización del
estudiante tras confirmar que la máquina no tenía ningún compilador de C++
al iniciar la Fase 0. Los ejecutables finales se compilan con `-static` para
no depender del PATH del sistema.

## 8. Escalamiento, gráficas e informe

*(Se completa al cerrar el bloque de corridas largas y de gráficas; ver
`docs/RESUMEN_FINAL.md` para el estado definitivo y las fechas exactas de
esta parte, ejecutada en modo autónomo mientras el estudiante dormía.)*

## 9. Limitaciones

Ver `informe/informe.tex`, sección "Limitaciones", para el listado
completo y honesto de lo que este trabajo no cubre o no puede garantizar.
