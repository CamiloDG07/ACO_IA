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

*(pendiente, Fase 2/4: con alpha = 0 la búsqueda es un vecino más cercano
estocástico con puntos de partida aleatorios, sin memoria de feromona; con
beta = 0 solo la feromona guía la búsqueda, sin heurística de distancia, lo
que favorece la convergencia prematura a un tour subóptimo)*

### ¿Por qué la selección determinista empeora la calidad?

*(pendiente, Fase 2: elegir siempre la candidata de mayor peso, en vez de la
ruleta probabilística, elimina la exploración; todas las hormigas de una
iteración terminan siguiendo el mismo camino y el algoritmo se estanca en el
primer óptimo local que encuentra)*

### ¿Cómo cambiaría con un costo multiobjetivo?

*(pendiente, Fase 4/5: se necesitaría una segunda medida de costo por arista
—por ejemplo tiempo o riesgo, además de distancia—, y una forma de combinar
ambas en la regla de transición o de mantener un frente de Pareto en vez de
un único mejor global)*

### ¿Para qué sirven 200 000 hormigas?

*(pendiente: se completa con los datos de la comparación a igual presupuesto
de cómputo en n = 200 000, Fase 2)*

## Guion por integrante

*(pendiente, Fase 5)*
