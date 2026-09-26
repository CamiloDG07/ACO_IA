# Decisiones de diseño

Tabla y justificación de las decisiones de diseño del proyecto: qué se
eligió, qué alternativas se consideraron, por qué, y su costo.

## Elección de lenguaje

| Decisión | Alternativas consideradas | Por qué | Costo |
| --- | --- | --- | --- |
| C++ (C++20) con OpenMP | Python, C, Rust | Ver justificación abajo | Curva de aprendizaje de memoria manual y de directivas OpenMP; a cambio, control fino de memoria y paralelismo real |

El enunciado permite C++, C o Rust, pero descarta Python de entrada ("Python
puede no alcanzar"). No se implementó nada en Python, C ni Rust, y no se
hicieron comparaciones de lenguaje: la elección de C++ se justifica de forma
breve y teórica, no empírica.

- **Python se descarta** por tres razones estructurales, no por una medición
  de desempeño:
  1. **Sobrecarga del intérprete**: cada operación aritmética en Python pasa
     por el bucle de evaluación de bytecode del intérprete (CPython), con
     verificación de tipos dinámica en cada paso. Para el paso interno de
     una hormiga (evaluar $K$ candidatas, acumular una suma, girar la
     ruleta) esto multiplica por un factor grande el costo de una operación
     que en C++ compilado es una suma y una comparación de punto flotante.
  2. **Acceso irregular a memoria**: la estructura de datos central del
     proyecto (arreglos de $n \cdot K$ vecinas, feromonas y pesos, indexados
     por ciudad) depende de que el compilador y el hardware exploten la
     localidad de caché (ver `docs/estrategias_ahorro.md`). Los objetos de
     Python (incluso `numpy` en operaciones elemento a elemento con lógica
     de control, como la ruleta) no ofrecen ese control fino sobre el
     layout de memoria ni sobre cuándo se materializan copias.
  3. **Falta de paralelismo real (GIL)**: el *Global Interpreter Lock* de
     CPython impide que dos hilos ejecuten bytecode de Python al mismo
     tiempo dentro de un mismo proceso. El paralelismo de este proyecto es
     precisamente sobre hormigas independientes (`#pragma omp parallel for`
     en la construcción de tours), que es la parte costosa del algoritmo;
     en Python, paralelizar eso exigiría procesos separados (`multiprocessing`),
     con costo de serialización y sin memoria compartida, o liberar el GIL
     desde una extensión en C, que en la práctica es reescribir el núcleo
     en C de todas formas.
- **C++ da control de memoria** (arreglos contiguos, sin recolector de
  basura, tipos de tamaño fijo como `float`/`uint32_t`), **OpenMP** como
  forma directa de paralelizar bucles sin la complejidad de gestionar hilos
  a mano, y ya existía **un código base validado** (`aco_tsp.cpp`, corrido
  en Linux con g++ 13 antes de este repositorio) que cumple los requisitos
  de la Fase 0 y la Fase 1.
- C y Rust no se descartan por incapacidad técnica (el enunciado los permite
  igual que C++), sino porque no aportaban nada sobre partir de un código ya
  validado en C++: reescribir en C perdería `std::atomic_ref`, contenedores
  seguros y plantillas sin ganar nada a cambio; reescribir en Rust exigiría
  reescribir desde cero un algoritmo ya probado, sin que el enunciado lo pida.

## Número de agentes (m)

Regla adoptada: **m = min(n, 20 000)**. Es decir, n = 20 con m = 20; n = 2 000
con m = 2 000; n = 200 000 con m = 20 000 (las 200 000 ciudades se ejecutan
siempre completas, nunca con una muestra).

### (a) Por qué m = n: convención de la literatura del Ant System

Antes de citar se verificó la fuente primaria, no solo el recuerdo de la
convención. Se descargó el libro completo y se localizó el texto exacto con
número de página:

> Dorigo, M., & Stützle, T. (2004). *Ant Colony Optimization*. Cambridge,
> MA: MIT Press.

- **p. 71** (Box 3.1, "Parameter Settings for ACO Algorithms without Local
  Search"): en la tabla de parámetros recomendados, la columna `m` (número
  de hormigas) está fijada en `n` para AS (Ant System), Elitist AS, Rank-based
  AS y MAX–MIN AS; solo ACS usa una constante pequeña (`m = 10`).
- **pp. 103–104**: "the number of ants is typically either a small constant
  (this is the case for ACS and Ant-Q or for most ACO algorithms with local
  search) or on the order of n (this is the case for AS variants without use
  of local search), the overall memory requirement is O(n²)"; con
  `m = n` estiman el requisito de memoria en, aproximadamente, `32n²` bytes.
- **p. 112**: "the number of ants m is set to be proportional to n, as
  suggested in the original papers (Dorigo et al., 1991a,b, 1996; Bauer et
  al., 2000)".

Esta última frase atribuye la convención a los artículos originales de
Dorigo, Maniezzo y Colorni (1991, 1996); no se verificó una página específica
de esos artículos originales (no se tuvo acceso directo a ellos), así que
aquí solo se cita a Dorigo y Stützle (2004), que sí se verificó con página.
Siguiendo la instrucción de no citar lo que no se pudo confirmar, no se
atribuye una página al artículo de 1996.

El **Ant System (AS) original con m = n** es exactamente la variante "sin
lista de candidatos, sin búsqueda local" que describe el libro: cobertura de
puntos de partida (cada hormiga arranca de una ciudad distinta cuando
`m = n`) y una regla que escala con el tamaño de la instancia. `aco_tsp.cpp`
sí usa lista de candidatos (K vecinas), así que no es un AS "puro", pero la
convención de escalar `m` con `n` sigue siendo la referencia de partida.

### (b) Costo por iteración: O(m·n·K), y O(n²K) cuando m = n

Con lista de candidatos de tamaño K, cada hormiga cuesta O(nK) en construir
su tour (más el costo, menor, de las búsquedas de reserva); con m hormigas
por iteración, el costo de una iteración es O(m·n·K). Si m = n (como sugiere
la literatura para AS sin búsqueda local), el costo por iteración pasa a ser
O(n²K): la misma razón por la que una matriz de feromona densa (n×n) es
inviable en memoria para n = 200 000 (320 GB, ver `docs/entorno.md` y la
guardia en `aco_denso.cpp`) también hace que "m = n hormigas por iteración"
sea, en tiempo, equivalente a reconstruir del orden de una matriz densa por
iteración.

Tiempo medido por iteración en esta máquina, n = 200 000, K = 8,
alpha=1.5, beta=5, rho=0.1, qfac=3, semilla 1 (una sola iteración por punto,
`resultados/costo_m_n200000.csv`):

| m | tiempo medido (s) | tiempo predicho por el ajuste (s) |
| ---: | ---: | ---: |
| 200 | 1.099 | 0.548 |
| 2 000 | 13.056 | 13.662 |
| 20 000 | 144.850 | 144.795 |

Ajuste lineal (mínimos cuadrados, 3 puntos): `t(m) ≈ 0.007285 · m − 0.909`
segundos, con **R² = 0.999947** (prácticamente lineal en m, como predice la
teoría a n y K fijos). El intercepto negativo no tiene sentido físico (con
m=0 no puede tomar tiempo negativo); es un artefacto de ajustar una recta a
solo 3 puntos con un rango enorme de m, no una medición real en m pequeño.

**Extrapolación a m = n = 200 000** (marcada explícitamente como estimación
por extrapolación lineal, no como corrida real): `0.007285 × 200 000 − 0.909
≈ 1 456 s ≈ 24,3 minutos por iteración`. Esta cifra coincide, dentro del
margen esperado, con la estimación independiente de la Fase 1 (`~7,36
ms/hormiga efectivos × 200 000 ≈ 1 472 s ≈ 24,5 min`), obtenida por un
método distinto (tasa efectiva medida en una corrida de 5 iteraciones con
m = 2 048), lo que da confianza en el orden de magnitud.

### (c) Por qué el tope de 20 000

El tope no es una propiedad del algoritmo: es una decisión de presupuesto de
cómputo medido en esta máquina (Fase 0: i7-8750H, 6 núcleos/12 hilos, 15,88
GB RAM). Con m = n = 200 000, una sola iteración tomaría ~24,3 minutos
(extrapolado); diez iteraciones tomarían más de 4 horas, y el enunciado pide
además múltiples semillas. Con m = 20 000 (10 % de n), una iteración toma
~2,4 minutos medidos directamente: diez iteraciones caben en unos 25
minutos por semilla, un presupuesto compatible con el tiempo disponible para
el taller.

Además, la feromona se actualiza **una sola vez por iteración**,
independientemente de cuántas hormigas hayan corrido esa iteración (ver
`buildTour`/evaporación en `aco_tsp.cpp`): agregar más hormigas por
iteración no agrega más actualizaciones de feromona, solo más muestras
(tours) antes de esa única actualización. Esto es relevante para (d): si el
límite de tiempo es lo que obliga a elegir entre "más hormigas por
iteración" y "más iteraciones", no hay garantía de que más hormigas por
iteración sea la mejor forma de gastar ese tiempo.

### (d) Respaldo empírico

**Calidad contra m** (n = 2 000, K = 10, alpha=1, beta=3, rho=0.1, qfac=1,
50 iteraciones fijas, 5 semillas; `resultados/barrido_m.csv`):

| m | L\_mejor media | desv. estándar | tiempo ACO medio (s) |
| ---: | ---: | ---: | ---: |
| 10 | 39,836 | 0,140 | 0,058 |
| 100 | 39,428 | 0,380 | 0,233 |
| 1 000 | 39,298 | 0,303 | 1,819 |
| 2 000 | 39,034 | 0,239 | 4,014 |
| 20 000 | 38,895 | 0,344 | 62,708 |

Con el **número de iteraciones fijo en 50** (no a igual tiempo de reloj),
subir m de 10 a 20 000 (2 000 veces más hormigas) solo mejora la longitud
media un 2,4 % (39,84 → 38,89), mientras el tiempo de cómputo sube unas
1 080 veces (0,058 s → 62,7 s). El retorno marginal decrece con fuerza: de
m=1 000 a m=2 000 (2 veces más hormigas, 2,2 veces más tiempo) la mejora es
de 0,67 %; de m=2 000 a m=20 000 (10 veces más hormigas, 15,6 veces más
tiempo) la mejora es de solo 0,36 %. Esto es consistente con lo que Dorigo y
Stützle (2004, sección "Number of Ants", pp. 96–97) reportan para MMAS con
búsqueda local: en instancias de hasta 500 ciudades, un número pequeño de
hormigas (2 a 10) ya da el mejor compromiso entre calidad y tiempo, y el
beneficio de una población grande solo se nota en instancias más grandes.

**Comparación a igual presupuesto de cómputo en n = 200 000** (m = 2 048
contra m = 20 000, mismo tiempo de reloj, 3 semillas): **pendiente**. Esta
corrida es de las que se lanzan al final, con confirmación previa del
estudiante (ver `docs/bitacora.md`). Esta subsección se actualiza en cuanto
esa corrida termine.

**Conclusión (solo lo que los datos muestran hasta ahora):** con el número
de iteraciones fijo, la calidad en n = 2 000 satura con fuerza a partir de
m ≈ 1 000–2 000; subir a m = 20 000 cuesta mucho tiempo por muy poca mejora
adicional. Esto sugiere que **el tope de 20 000 no está impulsado por una
necesidad de calidad** (que ya satura mucho antes) **sino por el presupuesto
de tiempo** disponible para correr varias iteraciones y semillas en
n = 200 000 — pero esta conclusión se confirma o se corrige con la
comparación a igual presupuesto de (d), todavía pendiente.

### (e) 20 000 es una decisión de ingeniería, no un óptimo teórico

El valor 20 000 (10 % de 200 000) no se deriva de ninguna fórmula ni de un
óptimo demostrado: es el punto donde, en **esta máquina** y con **el tiempo
disponible para este equipo**, cabe correr varias iteraciones y varias
semillas en la instancia más grande. En otro computador (más núcleos, más
memoria) o con más tiempo disponible, un equipo distinto podría justificar
razonablemente un tope distinto, mayor o menor. La Sección 5.7.6 del mismo
libro (Dorigo y Stützle, 2004, p. 217) lo resume así: "el mejor valor de m
es función del algoritmo ACO particular y de la clase de problemas
atacados, y la mayoría de las veces debe fijarse experimentalmente"; aquí se
fija experimentalmente para esta máquina y este taller, no como un óptimo
universal.
