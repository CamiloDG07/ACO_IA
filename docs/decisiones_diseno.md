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

### Comparación cualitativa con C, Rust y otras alternativas

Comparación **cualitativa**, sin medir ningún otro lenguaje. Se espera que
las diferencias de rendimiento entre C, C++ y Rust en este problema sean
pequeñas (pocos puntos porcentuales), porque el tiempo lo dominan los
accesos irregulares a memoria, el número de hilos y el algoritmo, no el
lenguaje — es una expectativa razonada, no un resultado medido aquí.

| Criterio | C++ | Rust | C |
| --- | --- | --- | --- |
| Velocidad final | Equivalente a C | Equivalente | Equivalente (base de comparación) |
| Paralelismo | OpenMP, una directiva por bucle | `rayon`, expresivo pero otro ecosistema | OpenMP, más código manual |
| Estructuras de datos | Vectores, atómicos, ordenación en la STL | Vectores, atómicos, ordenación en su librería estándar | A mano (arreglos y punteros) |
| Seguridad de memoria | Depende del programador | Garantizada por el compilador (*borrow checker*) | Depende del programador |
| Instalación en Windows | Un paquete (`g++`, aquí WinLibs) | `rustup` + enlazador (a veces exige VS) | Un paquete (`gcc`) |
| Curva de aprendizaje/depuración | Conocida, depuradores maduros | Más empinada (propiedad y préstamos) | Similar a C++, menos abstracciones |

Otras alternativas descartadas y por qué: Zig (tan rápido como C, pero joven
y con poca documentación); Go (paralelismo sencillo, pero su recolector de
basura lo deja por debajo en cálculo intensivo); Julia (cercano a C++ en
cálculo científico, pero con arranque de compilación notable y más memoria
en tiempo de ejecución); Java/C# (buen rendimiento tras el calentamiento de
la VM, pero más memoria y menos control, justo lo que se quiere ahorrar);
Fortran (excelente con matrices densas, poco natural para grafos, listas de
vecinas y rejillas espaciales); Python con Numba o Cython (el código de alto
nivel sigue en Python, y el docente ya advirtió que Python puede no
alcanzar; habría que aclarar además qué parte corre realmente compilada).

Conclusión: se elige C++ por tres razones prácticas (OpenMP casi sin código
adicional, compilador de instalación sencilla en Windows, código base ya
validado con pruebas), reconociendo que Rust habría sido igual de válido si
el criterio principal hubiera sido la seguridad de memoria, y que C habría
sido igual de rápido con más código para lo mismo que la STL de C++ da de
fábrica.

## Configuración elegida para las corridas grandes (n = 2 000 y n = 200 000)

La configuración de partida era K=8, alpha=1.5, beta=5, rho=0.1, qfac=3 (sin
segunda feromona), tomada de la nota preliminar del enunciado. El barrido de
parámetros (`resultados/barrido_parametros.csv`, 5 semillas por valor,
Fase 2) sugería, valor por valor, que alpha=2, beta=8, rho=0.5, qfac=10 y
K=5 daban mejores medias individuales que la configuración de partida. Antes
de adoptar esa combinación se comparó de forma directa y apareada (mismas 8
semillas, prueba de Wilcoxon, `scripts/seleccion_configuracion.py`):

| Configuración | Media L | Desv. estándar | Diferencia vs. referencia | p (Wilcoxon) |
| --- | ---: | ---: | ---: | ---: |
| Referencia (K=8, alpha=1.5, beta=5, rho=0.1, qfac=3) | 37,940 | 0,225 | — | — |
| Mejores valores individuales (K=5, alpha=2.0, beta=8, rho=0.5, qfac=10) | 38,154 | 0,420 | +0,214 (peor) | 0,055 (no significativo) |
| Referencia + segunda feromona (two=1, alpha2=1.0) | 37,496 | 0,352 | −0,444 (mejor) | 0,0078 (significativo) |

Combinar los mejores valores individuales de cada parámetro **no** dio la
mejor combinación conjunta (quedó, de hecho, ligeramente peor que la
referencia, aunque sin diferencia significativa): evidencia de que los
parámetros interactúan entre sí y que optimizarlos uno por uno, con los
demás fijos en un valor por defecto distinto al de la referencia, no es
intercambiable con optimizar la combinación completa.

**Se adopta la configuración con segunda feromona** (K=8, alpha=1.5, beta=5,
rho=0.1, qfac=3, two=1, alpha2=1.0, que cumple alpha2 < alpha) para el
resultado oficial de n=2 000 y para las corridas de n=200 000, por ser la
única candidata con una mejora estadísticamente significativa y de magnitud
apreciable (≈1,2 % más corta) sobre la referencia.

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

Tiempo medido por iteración en esta máquina, n = 200 000, K = 8, con la
**configuración ganadora** (alpha=1.5, beta=5, rho=0.1, qfac=3, segunda
feromona activada), 3 repeticiones por valor de m
(`resultados/costo_m_n200000_3reps.csv`):

| m | tiempo medio (s) | desv. estándar (s) | tiempo predicho por el ajuste (s) |
| ---: | ---: | ---: | ---: |
| 200 | 0,850 | 0,015 | 0,833 |
| 2 000 | 8,681 | 0,066 | 8,679 |
| 20 000 | 86,940 | 0,476 | 86,943 |

Ajuste lineal (mínimos cuadrados, 3 puntos × 3 repeticiones): `t(m) ≈
0,004348 · m − 0,017` segundos, con **R² = 1,000000** (lineal en m dentro
del margen de medición, como predice la teoría a n y K fijos).

**Extrapolación a m = n = 200 000** (marcada explícitamente como estimación
por extrapolación lineal, no como corrida real): `0,004348 × 200 000 − 0,017
≈ 870 s ≈ 14,5 minutos por iteración`.

Nota sobre una medición anterior: una primera medición de un solo punto
(Fase 2, sin repeticiones, con la configuración de partida **sin** segunda
feromona) había dado ~144,85 s para m=20 000 y una extrapolación de ~24,3
min/iteración (`resultados/costo_m_n200000.csv`, conservado sin modificar
como registro histórico). La medición con 3 repeticiones y la configuración
ganadora da un tiempo por hormiga menor (~86,9 s contra ~144,85 s para el
mismo m=20 000): la diferencia es real, no un error de medición (se
comprobó con 3 repeticiones consistentes entre sí, desv. estándar de 0,48 s
sobre una media de 86,94 s), y es coherente con lo observado en la corrida
real del punto 5 (bloque C, ~85 s/iteración medidos directamente, ver más
abajo). La explicación más plausible es que la segunda feromona guía a las
hormigas de forma más decisiva, reduciendo cuánto recurren a la búsqueda de
reserva (la parte más cara de construir un paso, ver la sección de análisis
de complejidad del informe); no se aisló esta hipótesis con
un experimento dedicado, así que se reporta como explicación plausible, no
como hecho verificado.

### (c) Por qué el tope de 20 000

El tope no es una propiedad del algoritmo: es una decisión de presupuesto de
cómputo medido en esta máquina (Fase 0: i7-8750H, 6 núcleos/12 hilos, 15,88
GB RAM). Con m = n = 200 000, una sola iteración tomaría ~14,5 minutos
(extrapolado, ver (b)); diez iteraciones tomarían más de 2 horas por
semilla, y el enunciado pide además múltiples semillas. Con m = 20 000
(10 % de n), una iteración toma ~87 s medidos directamente: diez iteraciones
tomaron, en la corrida real, entre 13,8 y 14,2 minutos por semilla (ver
`docs/bitacora.md`), un presupuesto compatible con el tiempo disponible para
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
contra m = 20 000, mismo tiempo de reloj, 3 semillas; corrida real,
`resultados/resultado_n200000_punto5.csv` y `..._punto6.csv`, ver
`docs/bitacora.md` para las horas de inicio y fin de cada semilla):

| Configuración | Iteraciones hechas | Tiempo de reloj | L\_mejor media | Desv. estándar | Mejora vs. NN media |
| --- | ---: | ---: | ---: | ---: | ---: |
| m = 20 000 (punto 5) | 10 | ~14 min/semilla | 387,308 | 0,190 | 1,28 % |
| m = 2 048 (punto 6) | ~108 | 15 min/semilla | 385,485 | 0,550 | 1,75 % |

Con el **mismo presupuesto de tiempo de reloj** (~15 minutos por semilla),
`m = 2 048` completa unas 108 iteraciones y llega a una longitud media
**menor** (mejor) que `m = 20 000` con solo 10 iteraciones: la diferencia
por semilla (`punto6 - punto5`) es negativa en las **3 de 3** semillas
(-2,29, -0,99 y -2,19), es decir, `m = 2 048` gana en todas las semillas.
Con solo 3 semillas la prueba de Wilcoxon no alcanza significancia
convencional (p = 0,25, el mínimo posible con n = 3 pares), pero la
dirección del efecto es completamente consistente, no mixta.

**Conclusión (lo que los datos muestran, incluida la comparación a igual
presupuesto):** ni la calidad contra $m$ en n = 2 000 (que ya satura mucho
antes de m = 20 000) ni la comparación directa a igual tiempo en
n = 200 000 respaldan que `m = 20 000` sea la forma más eficiente de gastar
un presupuesto de tiempo fijo. Al contrario: con el mismo tiempo de reloj,
correr más iteraciones con menos hormigas (`m = 2 048`) dio una calidad
ligeramente mejor que correr pocas iteraciones con muchas hormigas
(`m = 20 000`), en las tres semillas probadas. Esto no invalida usar
`m = 20 000` para la corrida "oficial" de 10 iteraciones de este trabajo
(que sigue la convención `m = min(n, 20 000)` de la literatura y el
presupuesto de tiempo total del proyecto), pero sí deja claro que el tope
de 20 000 se sostiene por la convención de la literatura y el presupuesto
de tiempo **total** disponible para el taller, no porque más hormigas por
iteración sea, en esta máquina, la forma más eficiente de convertir tiempo
de cómputo en calidad de tour.

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
