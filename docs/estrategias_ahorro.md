# Estrategias de ahorro de tiempo y memoria

Cada estrategia con su motivo, el costo asintótico antes y después, y la
medición que la respalda. Corresponden a decisiones ya presentes en
`src/aco_tsp.cpp` desde el prototipo original (validado en Linux antes de
este repositorio, Fase 0) y verificadas de nuevo al portarlo a Windows
(Fase 1).

| Estrategia | Recurso que ahorra | Costo antes | Costo después | Medición que lo respalda |
| --- | --- | --- | --- | --- |
| No construir la matriz $n \times n$; lista de $K$ vecinas por ciudad | Memoria | $O(n^2)$ | $O(nK)$ | Con $n=200\,000$, la guardia de `aco_denso.cpp` calcula que la matriz densa (distancia + feromona, `float`) exigiría $2 \cdot 4n^2 = 320$ GB; la versión dispersa mide un pico real de 96,8 MB (`docs/bitacora.md`, Fase 1) |
| Vecinas por rejilla espacial (grid) | Tiempo de preparación | $O(n^2)$ (comparar cada par de ciudades) | $O(nK)$ (solo se revisan celdas cercanas) | Preparación medida en 0,149 s para $n=200\,000$ (`docs/bitacora.md`, Fase 1), frente a lo que tomaría comparar $200\,000^2 \approx 4 \times 10^{10}$ pares |
| Ciudades renumeradas por celda (recorrido en serpiente) | Tiempo (localidad de caché) | Accesos a `x[i]`, `y[i]`, vecinas dispersos en memoria | Ciudades cercanas en el espacio quedan contiguas en memoria | No se aisló por separado (activarla/desactivarla exigiría una segunda compilación); se documenta como decisión de diseño heredada del prototipo validado, con la justificación teórica de localidad espacial-temporal de caché |
| Búsqueda de reserva por anillos de celdas, saltando celdas vacías | Tiempo y memoria | Ordenar u guardar listas de ciudades no visitadas por hormiga | Solo se activa cuando las $K$ candidatas ya están visitadas, y explora celdas en anillos crecientes hasta encontrar una libre | Ver sección de complejidad: el costo de esta búsqueda de reserva crece hacia el final del tour, cuando más ciudades ya están visitadas |
| Las hormigas no guardan su tour; buffer por hilo y depósito inmediato con atómicos | Memoria: independiente de $m$ | Guardar $m$ tours completos costaría $O(m \cdot n)$ | $O(n)$ por hilo, sin importar $m$ | Con $m=20\,000$ en $n=200\,000$, guardar todos los tours simultáneamente costaría del orden de $4 \cdot 20\,000 \cdot 200\,000$ bytes $\approx 16$ GB; el pico medido (96,8 MB con $m=2\,048$, orden similar con $m=20\,000$ porque el estado es por hilo, no por hormiga) confirma que la memoria no escala con $m$ |
| Pesos $\tau^{\alpha}\tau_2^{\alpha_2}\eta^{\beta}$ precalculados una vez por iteración | Tiempo | Recalcular la potencia en cada paso de cada hormiga | Un solo recorrido de $O(nK)$ por iteración, antes de lanzar las $m$ hormigas | La feromona es constante durante la construcción de una iteración; cada paso de una hormiga se reduce a una suma y una ruleta de $K$ términos ya pesados |
| $\eta^{\beta}$ precalculado al inicio (`etaB`) | Tiempo | Recalcular `pow(1/d, beta)` en cada iteración | Se calcula una sola vez, al principio, porque la distancia no cambia | Mismo razonamiento que el punto anterior, aplicado a la parte que nunca cambia entre iteraciones |
| Paralelismo por hormiga (OpenMP, `schedule(dynamic,1)`) | Tiempo | Construcción secuencial de $m$ tours | Hasta 12 hormigas construyéndose a la vez en esta máquina (12 hilos lógicos) | La construcción de una hormiga es independiente de las demás durante una iteración; el límite de la ley de Amdahl es la parte secuencial (evaporación, cálculo de pesos, actualización del mejor global), ver sección de complejidad |
| Tipos `float` y arreglos contiguos (`std::vector`) | Memoria y caché | `double` duplicaría el tamaño de cada arreglo de tamaño $nK$ | La precisión de `float` alcanza para distancias y feromonas; la longitud final del tour se recalcula en `double` para la verificación | La verificación interna del programa (`L_mejor` contra la longitud recalculada) coincide en todas las corridas, confirmando que la pérdida de precisión de `float` no afecta la validez del resultado reportado |
| Segunda feromona solo sobre aristas candidatas | Memoria | Una matriz $n \times n$ adicional si fuera densa | Un arreglo más de tamaño $nK$, no $n^2$ | Mismo argumento que la primera fila: con `two=1`, el costo adicional es otro arreglo de $nK$ floats, no de $n^2$ |
| `--tiempo_max` (presupuesto de tiempo por iteración) | Tiempo (control de presupuesto) | Sin él, una iteración con muchas hormigas puede tardar más de lo disponible | Las hormigas que no alcanzan a construirse antes del presupuesto simplemente no corren esa iteración; la iteración cierra igual (evaporación y depósito con las que sí corrieron) | Probado en la Fase 1: con `--tiempo_max 0.01` en $n=2\,000$, $m=2\,048$, solo 90-92 de 2\,048 hormigas se construyen por iteración, y la calidad empeora de forma consistente con el trueque esperado |

## Nota sobre la renumeración por celda

A diferencia de las demás estrategias, la renumeración por celda no se aisló
con una comparación "activada contra desactivada" porque el código no tiene
una bandera para desactivarla sin reescribir la construcción de la rejilla;
hacerlo exigiría una segunda variante del programa solo para esta prueba, lo
que el enunciado no pide ("implementar solo lo que el enunciado pide"). Se
documenta como una decisión de diseño con respaldo teórico (localidad de
caché), no como una medición propia de este trabajo.
