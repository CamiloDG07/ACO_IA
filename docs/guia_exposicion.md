# Guía de exposición

Guion corto por integrante y respuestas breves a las preguntas probables de
la sustentación. Se completa a lo largo de las Fases 2 a 5; por ahora solo
tiene las preguntas ya respondidas con datos reales.

## Preguntas probables

### ¿Por qué C++ y no Python?

Python se descarta por tres razones estructurales, no por una medición de
desempeño: la sobrecarga del intérprete de CPython en cada operación
aritmética, el acceso irregular a memoria que no permite el control fino de
un arreglo contiguo de $n \cdot K$ elementos, y el GIL, que impide
paralelismo real de hilos justo en la parte más costosa del algoritmo (la
construcción de tours de las hormigas). C++ da control de memoria, OpenMP
para paralelismo real, y ya había un código base validado. Ver
`docs/decisiones_diseno.md`.

### ¿Por qué esa cantidad de hormigas (m = min(n, 20 000))?

La literatura del Ant System (Dorigo y Stützle, 2004, p. 71 y p. 112,
verificado en el libro) recomienda `m = n` para las variantes sin búsqueda
local. Con lista de candidatos de tamaño K, eso hace el costo por iteración
`O(n²K)`: medimos una iteración con m = 200, 2 000 y 20 000 en n = 200 000
(1,1 s, 13,1 s, 144,9 s; ajuste lineal con R² = 0,9999) y extrapolamos que
m = n = 200 000 tomaría ~24 minutos **por iteración** — inviable para varias
iteraciones y semillas en el tiempo que tenemos. Con m = 20 000 (10 % de n)
una iteración toma ~2,4 minutos, medido directamente: eso es lo que fija el
tope, no una propiedad del algoritmo. Además, en n = 2 000 la calidad ya
satura mucho antes de m = 20 000 (2 000 veces más hormigas solo mejora la
longitud un 2,4 %), así que el tope no responde a una necesidad de calidad,
sino al presupuesto de tiempo de esta máquina. 20 000 es una decisión de
ingeniería para este equipo, no un óptimo teórico.

### ¿Qué pasa con alpha = 0 o beta = 0?

Con alpha = 0, la regla de transición (ecuación de la sección "Marco
teórico" del informe) ignora la feromona: cada hormiga elige entre sus
candidatas con probabilidad proporcional solo a $\eta^\beta = (1/d)^\beta$,
es decir, un vecino más cercano estocástico con puntos de partida
aleatorios, sin memoria de lo que hicieron las hormigas anteriores. Con
beta = 0, ocurre lo contrario: solo importa $\tau^\alpha$, sin heurística de
distancia; como la feromona inicial es uniforme, las primeras iteraciones
son casi aleatorias, y una vez que una arista se refuerza un poco, con
alpha > 1 esa ventaja se amplifica rápido y casi todas las hormigas
convergen al mismo camino (estancamiento), que en general es un tour
notablemente peor que con beta > 0, porque no hay ninguna guía hacia
ciudades cercanas.

### ¿Por qué la selección determinista empeora la calidad?

Elegir siempre la candidata de mayor peso (en vez de la ruleta
probabilística) elimina la exploración: en la primera iteración, con
feromona uniforme, todas las hormigas eligen la misma arista de menor
distancia en cada paso, así que casi todas terminan construyendo el mismo
tour (o uno muy parecido) desde su ciudad de partida. Sin variedad entre las
hormigas de una iteración no hay comparación real entre alternativas, y la
feromona termina reforzando el primer óptimo local que el algoritmo
encontró, sin ninguna posibilidad de escapar de él en iteraciones
posteriores.

### ¿Cómo cambiaría con un costo multiobjetivo?

Se necesitaría una segunda medida de costo por arista (por ejemplo, tiempo
de viaje o riesgo, además de la distancia), y una forma de combinarla en la
regla de transición: la más simple es una suma ponderada de las dos medidas
en el cálculo de $\eta_{ij}$; una alternativa más completa es mantener un
frente de Pareto de soluciones no dominadas en vez de un único mejor global,
lo que exigiría rehacer la parte de "mejor de la iteración/mejor global" del
algoritmo (`aco_tsp.cpp`, bucle principal) para comparar tours por
dominancia en vez de por un solo número.

### ¿Para qué sirven 200 000 hormigas?

*(se completa con los datos de la comparación a igual presupuesto de
cómputo en n = 200 000: m = 2 048 contra m = 20 000, mismo tiempo de reloj,
ver `docs/decisiones_diseno.md` y `docs/resultados.md` una vez cerradas las
corridas largas)*

### ¿Habría sido más rápido usar C, Rust u otro lenguaje?

Cualitativamente, no de forma apreciable: se espera que C, C++ y Rust den un
rendimiento del mismo orden en este problema (pocas diferencias
porcentuales), porque el tiempo lo dominan los accesos a memoria, el número
de hilos y el algoritmo, no el lenguaje. No se midió ningún otro lenguaje en
este trabajo. Rust habría sido una alternativa igualmente válida si el
criterio principal hubiera sido la seguridad de memoria (su compilador
garantiza en tiempo de compilación errores que en C++ solo aparecen en
tiempo de ejecución); C habría sido igual de rápido, con más código para
lograr lo que la librería estándar de C++ da de fábrica. Ver
`docs/decisiones_diseno.md`, sección "Elección de lenguaje", para la tabla
completa.

## Guion por integrante

*(pendiente: cada integrante completa su parte antes de la sustentación;
la estructura sugerida es introducción y objetivo (integrante 1), diseño de
la solución y estrategias de ahorro (integrante 2), resultados y
limitaciones (integrante 3), con las preguntas de arriba repartidas según
quién presente esa sección)*
