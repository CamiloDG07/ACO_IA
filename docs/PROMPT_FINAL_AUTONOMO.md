# Prompt final autónomo para Claude Code: cierre completo del proyecto ACO_IA

Uso: guardar este archivo en `D:\camilo\Documentos\ACO_IA\docs\PROMPT_FINAL_AUTONOMO.md`, abrir Claude Code en `D:\camilo\Documentos\ACO_IA` (en la misma sesión donde ya se cerró la Fase 1, o en una nueva) y escribir:

`Lee completo docs\PROMPT_FINAL_AUTONOMO.md y ejecútalo de principio a fin sin detenerte a preguntar nada. Estoy dormido y no responderé.`

---

## 0. Modo de operación autónomo (regla superior a todo lo demás)

El estudiante no estará disponible durante horas. Por eso:

1. **No preguntar nunca.** No usar herramientas de pregunta al usuario ni esperar confirmaciones. Toda decisión se toma con las reglas de este documento y, si algo no está cubierto, con el criterio más conservador y reproducible. Cada decisión no cubierta se anota en `docs\bitacora.md` con su motivo.
2. **No detenerse por un error.** Ante un fallo: diagnosticar, reintentar una vez con un cambio razonable y, si persiste, registrar el problema en la bitácora, seguir con lo demás y reportar la limitación de forma honesta en el informe. Nunca inventar ni completar datos que no se midieron.
3. **Procesos largos en segundo plano.** Ningún comando debe quedar en primer plano más de 9 minutos. Las corridas largas se lanzan desacopladas (por ejemplo con `Start-Process` de PowerShell), escriben su avance en `resultados\` y se consultan leyendo los logs a intervalos de 5 a 10 minutos. Si la sesión se interrumpe, el script debe poder relanzarse y saltar las corridas ya completas.
4. **Evitar que Windows suspenda el equipo mientras corre.** Los procesos largos se ejecutan bajo un envoltorio de PowerShell que llame a `SetThreadExecutionState` con `ES_CONTINUOUS | ES_SYSTEM_REQUIRED` (vía `Add-Type` con `kernel32.dll`) y lo libere al terminar. No cambiar planes de energía ni configuraciones del sistema.
5. **Presupuesto de tiempo total.** Las corridas largas ocupan, como máximo, 4 horas de reloj en total. Si algo se sale de ese presupuesto, se reduce el número de semillas o iteraciones de esa corrida, se documenta y se continúa.
6. **Mientras corren las largas, solo trabajo ligero** (redacción de documentos y de LaTeX). No lanzar otras tareas pesadas ni compilaciones paralelas, para no contaminar los tiempos. Las gráficas y la compilación del PDF se hacen cuando no haya una corrida larga activa.
7. **Git.** Commit y push al cerrar cada bloque. Solo el estudiante figura como autor y colaborador: no cambiar `user.name` ni `user.email`, no añadir líneas `Co-Authored-By` ni pies de página de generación automática, y no mencionar a Claude ni a ninguna IA en commits, README, informe o archivos del repositorio. Mensajes de commit en español, en tiempo presente. Nunca usar `push --force` ni reescribir historia; si se detecta un commit previo con autoría ajena, se reporta en la bitácora y en el resumen final, sin corregirlo. Antes de cada commit revisar `git status` y no subir binarios, archivos temporales ni archivos de más de 5 MB.

## 1. Reorientación al iniciar

Leer `docs\PROMPT_UNICO_CLAUDE_CODE.md` (plan base y tablas de variables), `docs\bitacora.md`, `docs\entorno.md`, `git log --oneline`, el contenido de `resultados\` y `scripts\`. Determinar qué ya está hecho y continuar desde ahí sin repetir trabajo. Tomar como estado de partida: la Fase 0 y la Fase 1 están cerradas (código portado a Windows con MinGW-w64 g++ 16.1.0, `--input`, `--tiempo_max`, `aco_denso.cpp` y pruebas automáticas), las corridas cortas de la Fase 2 pueden estar en curso o terminadas, y la máquina es un i7-8750H de 6 núcleos y 12 hilos con 15,88 GB de RAM.

## 2. Decisiones ya tomadas (consolidadas, no reabrir)

| Tema | Decisión |
| --- | --- |
| Lenguaje | C++ con OpenMP. No implementar nada en Python, C ni Rust ni comparar lenguajes. Justificar en el informe con la subsección "Elección del lenguaje de programación" del bloque E (comparación cualitativa con C, Rust y otras alternativas, sin medir otros lenguajes): Python se descarta por la sobrecarga del intérprete, el acceso irregular a memoria y la falta de paralelismo real (GIL); C++ ofrece control de memoria, OpenMP y código base validado. Se reconoce que C y Rust también serían aptos |
| Instancias | 20, 2 000 y 200 000 ciudades; las de 200 000 se ejecutan siempre completas. Puntos aleatorios uniformes en el cuadrado unidad por semilla (las diapositivas no fijan instancias); si en `D:\camilo\Documentos\ACO_IA` o en `docs\` aparece un archivo de instancias del docente, usarlo con `--input` y anotarlo |
| Agentes | `m = min(n, 20 000)`: n = 20 con m = 20; n = 2 000 con m = 2 000; n = 200 000 con m = 20 000 |
| Serie de escalamiento | m fija (2 048) y n en 20, 200, 2 000, 20 000 y 200 000, para aislar el efecto de n en tiempo y memoria, incluyendo la versión densa donde sea viable (n <= 5 000) |
| Costo de m = n en 200 000 ciudades | No se ejecuta completo. Se mide una iteración con m = 200, 2 000 y 20 000, se ajusta tiempo vs m y se extrapola a 200 000 (~24,5 min por iteración según la medición previa). Se marca siempre como estimación por extrapolación lineal, con el coeficiente de determinación |
| Parámetros de referencia para las corridas grandes | K = 8, alpha 1,5, beta 5, rho 0,1, Q 3, salvo que el barrido en 2 000 ciudades, con 5 semillas, muestre una configuración claramente mejor; en ese caso usar la mejor y explicarlo |

## 3. Plan de trabajo por bloques

### Bloque A: cerrar las corridas cortas
Verificar en `resultados\` qué falta del plan de la Fase 2 (barrido de alpha, beta, rho, Q, K y m en 2 000 ciudades con al menos 5 semillas por configuración; segunda feromona apagada y con alpha2 en 0,1, 0,3, 0,5 y 1,0; criterios de parada; n = 20 contra Held-Karp con 5 semillas; serie de escalamiento con la versión dispersa y la densa) y completarlo. Un CSV por corrida con las columnas de la Fase 2 del prompt base (en español). Comparar configuraciones con media, desviación estándar, mínimo y máximo, y un criterio estadístico simple (intervalos de confianza del 95 % o prueba de Wilcoxon) antes de afirmar que una es mejor. Esperar a que no queden procesos de ACO activos antes de pasar al bloque C.

### Bloque B: automatización de las corridas largas
Crear `scripts\ejecutar_corridas_largas.ps1` que, con el envoltorio de no suspensión, ejecute en orden y de forma reanudable:
1. Costo por iteración con n = 200 000 y m = 200, 2 000 y 20 000 (3 repeticiones de una iteración cada una).
2. Punto 5: n = 200 000, m = 20 000, 10 iteraciones, semillas 1, 2 y 3, con los parámetros de referencia, registrando en cada iteración el tiempo acumulado de reloj y el mejor global; un CSV por semilla escrito iteración a iteración.
3. Punto 6: n = 200 000, m = 2 048 con presupuesto de 15 minutos de reloj por semilla (semillas 1, 2 y 3). El lado m = 20 000 de la comparación a igual presupuesto se lee de los logs del punto 5 tomando el mejor global al cumplirse 15 minutos de reloj (aprox. 6 iteraciones); no se vuelve a correr, y el informe lo aclara.
Ejecutarlas una detrás de otra, nunca en paralelo. Crear también `scripts\ejecutar_modo_rapido.ps1` para quien reproduzca el proyecto en poco tiempo (ver la advertencia del bloque F).

### Bloque C: ejecutar las corridas largas
Lanzar el script del bloque B desacoplado y vigilarlo leyendo los logs. Registrar en la bitácora la hora de inicio y fin de cada corrida y toda señal de reducción de velocidad del equipo (tiempo por iteración que varíe más de 15 % entre iteraciones consecutivas). Si una corrida falla, relanzarla una vez. Mientras corren, trabajar solo en redacción (bloque F y estructura del informe).

### Bloque D: análisis y gráficas
Un script `scripts\generar_figuras.py` (Python, matplotlib, pandas) que lea únicamente los CSV de `resultados\` y genere las figuras en `figuras\` (PNG a 200 dpi) y las tablas del informe como archivos `.tex` en `informe\tablas\`. Así ningún número del informe se copia a mano. Cumplir el estilo del bloque 4 y estas condiciones de claridad para todas las figuras:
- Título corto que diga qué se compara, ejes con nombre y unidad en español, leyenda solo si hay más de una serie, paleta apta para daltonismo, escala logarítmica solo cuando se explique en el pie, y anotaciones directas del dato clave (por ejemplo "10 000 veces menos memoria").
- Cada figura lleva en el informe un pie breve y un párrafo "Cómo leer esta figura" con tres partes: qué muestra, por qué se espera ese comportamiento (con su base teórica) y qué se concluye con los datos.

Figuras mínimas:
1. Crecimiento factorial (n-1)!/2 para n = 6, 10, 15, 20, 2 000 y 200 000, en escala logarítmica, calculado con `lgamma` (mostrar el número de dígitos).
2. Convergencia (mejor global y media de las hormigas contra la iteración) para 20, 2 000 y 200 000 ciudades.
3. Diagramas de caja por configuración y semilla (varianza de un algoritmo estocástico).
4. Mapas de calor alpha-beta y rho-Q en 2 000 ciudades.
5. Efecto de K y efecto de la segunda feromona.
6. Tiempo por iteración contra m (con la recta ajustada y la extrapolación a 200 000 marcada como estimación) y contra n.
7. Aceleración y eficiencia contra número de hilos (1, 2, 4, 6, 12) en 2 000 ciudades.
8. Memoria contra n, versión densa contra dispersa, en escala log-log, con la línea de 16 GB de RAM de la máquina y la memoria hipotética de 320 GB para 200 000 ciudades.
9. Memoria por componente (coordenadas, vecinas, distancias, tau, tau2, pesos, estado por hilo) contra el pico medido.
10. Calidad contra m (2 000 ciudades: m = 10, 100, 1 000, 2 000, 20 000) y comparación a igual presupuesto de cómputo en 200 000 ciudades (m = 2 048 contra m = 20 000) contra el tiempo acumulado.
11. Tour final de 20 y de 2 000 ciudades, y un fragmento ampliado del de 200 000.
12. Longitud contra el vecino más cercano y contra la aproximación asintótica de Beardwood-Halton-Hammersley (aclarando que es una referencia y no el óptimo).

### Bloque E: informe en LaTeX
Crear `informe\informe.tex` y compilarlo a `informe\informe.pdf` (con `latexmk`; MiKTeX está instalado). Estilo institucional de la Universidad Sergio Arboleda: `article` 12 pt, `a4paper`, `geometry` (superior e inferior 2,5 cm, izquierda y derecha 3 cm), `mathptmx`, `xurl`, `fancyhdr` (encabezado con la sección a la izquierda y el número de página a la derecha, filete de 0,4 pt), portada con el logo institucional (buscar `sergio_logo.png` en `D:\camilo\Documentos` y en trabajos previos de LaTeX del estudiante, por ejemplo las carpetas de ciberseguridad; si no aparece, usar una portada sin logo y anotarlo en la bitácora), nombre de la universidad en negrita 13 pt, título en negrita 14 pt, asignatura (Inteligencia Artificial, SIST5036) en negrita 12 pt, integrantes: Mario Jiménez, Juan David Andrade y Camilo Díaz, pie en cursiva con la facultad y el año (2026), y luego tabla de contenido. Figuras y tablas centradas, con numeración y descripción debajo, en letra más pequeña que el cuerpo.

Contenido, con lenguaje claro para un estudiante de pregrado (primero la idea en palabras, luego el término técnico):
1. Introducción y objetivo, con el enunciado del docente.
2. Marco teórico, cada concepto con su porqué: estigmergia y comportamiento emergente; representación del problema (grafo, distancias, feromonas); regla de transición y ruleta (con el ejemplo numérico de las diapositivas); evaporación y depósito; exploración y explotación (papel de alpha, beta, rho); criterios de parada.
3. Espacio de búsqueda factorial: derivación de (n-1)!/2 y la Figura 1; por qué es inviable la fuerza bruta y comparación con Held-Karp (O(n^2 2^n), solo viable para n = 20) y con ACO.
4. Diseño de la solución: estrategias de ahorro de tiempo y espacio (la tabla de diez estrategias del prompt base, cada una con su motivo, costo antes y después y la medición que la respalda), decisiones de diseño (tabla), la subsección "Número de agentes" (por qué m = n: convención del Ant System, cobertura de puntos de partida, regla que escala; por qué el tope de 20 000: presupuesto de cómputo medido, la feromona se actualiza una vez por iteración; aclarar que es una decisión de ingeniería para este equipo y no un óptimo teórico; concluir solo lo que los datos muestren), y la subsección "Elección del lenguaje de programación" (ver más abajo).

   **Subsección "Elección del lenguaje de programación".** Es una comparación cualitativa y no se mide ningún otro lenguaje. Dejar explícito que las diferencias de rendimiento entre C, C++ y Rust en este problema se esperan pequeñas (del orden de pocos puntos porcentuales) porque el tiempo lo dominan los accesos irregulares a memoria, el número de hilos y el algoritmo, y que esto es una expectativa y no un resultado medido en este trabajo. Contenido:
   - Criterio: el ejercicio exige ahorrar memoria y tiempo, por lo que interesan los lenguajes que dan control sobre ambos (C, C++, Rust y Zig), y se descarta el ensamblador por indicación del docente y porque no mejora lo que ya optimiza el compilador.
   - Tabla comparativa de C++, Rust y C con los criterios: velocidad final, paralelismo (OpenMP con una directiva por bucle en C++; `rayon` en Rust; OpenMP con más código manual en C), estructuras de datos disponibles (vectores, atómicos y ordenación en la librería estándar de C++ y en Rust; a mano en C), seguridad de memoria (el compilador de Rust la garantiza; en C y C++ depende del programador), instalación en Windows (un solo paquete con g++ o gcc; Rust requiere `rustup` y un enlazador que a veces exige las herramientas de Visual Studio) y curva de aprendizaje y depuración.
   - Tabla de otras alternativas y por qué no se eligieron: Zig (rápido como C, pero joven y con poca documentación), Go (paralelismo sencillo, pero el recolector de basura suele dejarlo por debajo en cálculo intensivo), Julia (cercano a C++ en cálculo científico, pero con tiempo de compilación inicial y mayor uso de memoria), Java o C# (buen rendimiento tras el calentamiento, pero más memoria y menos control, justo lo que el ejercicio pretende ahorrar), Fortran (excelente con matrices, poco natural para grafos, listas y rejillas espaciales) y Python con Numba o Cython (el código de alto nivel sigue en Python, pero el docente advirtió que Python puede no bastar y habría que aclarar qué parte corre realmente compilada).
   - Justificación de Python descartado: sobrecarga del intérprete por cada paso del bucle interno, acceso irregular a memoria sin vectorización posible y ausencia de paralelismo real por el GIL.
   - Conclusión: se elige C++ por tres razones prácticas (OpenMP casi sin código adicional, compilador de instalación sencilla en Windows y código base ya validado con pruebas), y se reconoce que Rust habría sido una alternativa igualmente válida si el criterio principal hubiera sido la seguridad de memoria, y que C habría sido igual de rápido con más código para lo mismo.
6. Análisis de complejidad con derivación y comprobación empírica: espacio O(nK) más O(n) por hilo, independiente de m; una hormiga O(nK) más búsquedas de reserva; una iteración O(m n K); con m = n, O(n^2 K); versión densa O(m n^2) en tiempo y O(n^2) en memoria; paralelismo por hormiga y límite de Amdahl con la parte secuencial (actualización de feromona y mejor global).
7. Metodología experimental: máquina (tomada de `docs\entorno.md`), instancias y semillas, parámetros, métricas, y cómo se mide el tiempo y la memoria (pico de memoria del proceso).
8. Resultados por instancia (20, 2 000 y 200 000 ciudades), con una tabla por métrica (longitud, tiempo, memoria) con media, desviación, mínimo y máximo, y la comparación con el vecino más cercano, el óptimo exacto (n = 20) y la aproximación asintótica (n grande).
9. Análisis de tiempo y memoria: escalamiento, densa contra dispersa, aceleración por hilos, costo de m = n (extrapolación marcada como estimación) y comparación a igual presupuesto de cómputo.
10. Discusión y limitaciones honestas: ACO no garantiza el óptimo; en 200 000 ciudades con pocas iteraciones la mejora sobre el vecino más cercano es pequeña y por qué (costo lineal en m, pocas actualizaciones de feromona); la lista de candidatos restringe el espacio de búsqueda; instancias aleatorias uniformes no son instancias TSPLIB reales; la extrapolación no es una corrida real; cualquier corrida que haya fallado o se haya recortado.
11. Conclusiones ligadas a los objetivos.
12. Referencias en APA, verificando autor, año y capítulo o página: Hurbans (2020, cap. 6); Dorigo, Birattari y Stützle (2006); Dorigo y Stützle (2004). Si algún dato no se puede verificar, no citarlo.
13. Anexo: cómo reproducir cada tabla y figura (comandos exactos) y glosario corto de términos.

Compilar dos veces y revisar que no queden referencias rotas, advertencias de figuras fuera de página ni cifras que no coincidan con los CSV.

### Bloque F: documentación del repositorio
1. `README.md`: qué es el proyecto, integrantes, estructura de carpetas, cómo compilar (MinGW-w64 y la línea exacta), cómo ejecutar cada instancia, cómo reproducir figuras y tablas, y un resumen de resultados con enlaces a los archivos. En las primeras líneas, un aviso visible que remita a `ADVERTENCIA_TIEMPO_200K.md`.
2. `ADVERTENCIA_TIEMPO_200K.md` en la raíz del repositorio: qué instancias son costosas y por qué; tiempos medidos en la máquina del estudiante (i7-8750H, 12 hilos): tiempo por hormiga, por iteración con m = 2 048 y con m = 20 000, la corrida completa del punto 5 y la estimación por extrapolación de una iteración con m = 200 000 (~24,5 min, marcada como estimación); memoria pico medida (~97 MB con 200 000 ciudades) contra los 320 GB que exigirían las matrices densas; qué esperar en equipos con menos núcleos (el tiempo crece de forma inversamente proporcional al número de hilos); recomendaciones para ejecutar (equipo enchufado, sin suspensión, sin otras tareas pesadas); y cómo lanzar el modo rápido (200 000 ciudades con m = 2 048 y 2 iteraciones, aprox. 1 minuto) con `scripts\ejecutar_modo_rapido.ps1`, además de cómo reducir iteraciones o usar `--tiempo_max`.
3. `docs\estrategias_ahorro.md`, `docs\decisiones_diseno.md`, `docs\resultados.md` y `docs\proceso.md` con el contenido descrito en el prompt base, y `docs\guia_exposicion.md` con un guion corto por integrante y respuestas a las preguntas probables (por qué C++, por qué no matriz, qué pasa con alpha = 0 o beta = 0, por qué una selección determinista empeora la calidad, cómo cambiaría con un costo multiobjetivo, por qué esa cantidad de hormigas, por qué m = n y por qué el tope de 20 000, qué significan las 200 000 ciudades para el tiempo y la memoria, y si C, Rust u otro lenguaje habría sido más rápido, con la respuesta cualitativa de la subsección "Elección del lenguaje de programación").
4. `docs\bitacora.md` actualizada de forma cronológica con cada decisión, prueba, error y resultado, incluidos los intentos que no funcionaron.

### Bloque G: verificación final (automática, sin preguntar)
1. Ejecutar las pruebas automáticas y confirmar que pasan.
2. Comprobar que cada número de las tablas del informe procede de los CSV (las tablas se generan por script) y que cada cifra citada en el texto coincide con `docs\resultados.md`.
3. Compilar el informe sin errores y abrir el PDF de forma programática para comprobar el número de páginas y que todas las figuras aparezcan.
4. Revisar `git shortlog -sne` (debe figurar solo el estudiante) y buscar en todo el repositorio, con `git log` y `grep`, cualquier mención a Claude, IA o `Co-Authored-By`; si aparece en archivos, corregirlo con un commit nuevo.
5. Revisar que el repositorio no contenga binarios ni archivos temporales, y que el `.gitignore` los cubra.

### Bloque H: cierre
Commit y push final. Escribir `docs\RESUMEN_FINAL.md` con: qué se hizo, qué se midió, qué quedó incompleto o recortado y por qué, tiempos reales de las corridas largas, y una lista de verificación de lo entregable (informe, figuras, README, advertencia, guía de exposición, CSV). Terminar con un resumen breve en la conversación.

## 4. Reglas de estilo (obligatorias en todo documento y código)

- Español académico en tercera persona, sin tuteo, sin primera persona, sin emojis y sin rayas largas.
- Explicaciones rigurosas pero naturales: frases cortas, primero la idea y luego el término técnico.
- Tablas en lugar de párrafos densos para decisiones de diseño y métricas; una tabla por métrica.
- Nombres de columnas, variables y ejes en español en los documentos (semilla, conteo, tiempo, memoria).
- Notación matemática en LaTeX.
- Código en Python compatible con PEP8, líneas de máximo 79 caracteres, verificado con `pycodestyle`.
- Alcance: implementar solo lo que el enunciado pide.
- Ningún dato sin respaldo: todo número sale de una corrida guardada; lo que se estima se rotula como estimación.
- Figuras centradas, con numeración y descripción debajo, en letra más pequeña que el cuerpo del texto.

## 5. Criterio de finalización

El trabajo termina cuando existan y estén subidos al repositorio: el informe PDF con figuras claras, el `README.md`, `ADVERTENCIA_TIEMPO_200K.md`, la documentación de `docs\`, los CSV de `resultados\`, las figuras, los scripts reproducibles y `docs\RESUMEN_FINAL.md`. Si el presupuesto de tiempo se agota antes, finalizar con lo disponible, marcar claramente lo que falte en `RESUMEN_FINAL.md` y subirlo igualmente.
