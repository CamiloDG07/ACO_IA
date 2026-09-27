# Advertencia: tiempo y memoria en n = 200 000

Este proyecto incluye corridas que toman **horas**, no minutos, si se piden
muchas hormigas en la instancia de 200 000 ciudades. Este archivo explica
cuáles, por qué, y cómo evitarlas si solo se quiere ver el programa
funcionar.

## Por qué es costoso

El costo de una iteración crece de forma lineal en el número de hormigas
`m` (a `n` y `K` fijos): construir una hormiga cuesta `O(nK)`, y una
iteración corre `m` hormigas. Con `n = 200 000`, cada hormiga cuesta del
orden de milisegundos, y la recomendación de la literatura del Ant System
(`m = n`, ver `docs/decisiones_diseno.md`) implicaría 200 000 hormigas por
iteración.

## Tiempos medidos en la máquina del estudiante

Máquina: Intel Core i7-8750H, 6 núcleos / 12 hilos, 15,88 GB de RAM
(`docs/entorno.md`).

| Medición | Valor |
| --- | --- |
| Tiempo por hormiga (efectivo, ya paralelo, 12 hilos) | ~7,36 ms |
| Tiempo por iteración, `m = 2 048` | ~15 s (medido en la Fase 1); ~8,5 s en una corrida posterior con la configuración final (ver nota¹) |
| Tiempo por iteración, `m = 20 000` | *(pendiente: se completa con el punto 1 de `scripts/ejecutar_corridas_largas.ps1`, repetido 3 veces)* |
| Corrida real, `n=200 000`, `m=20 000`, 10 iteraciones | *(pendiente: se completa al cerrar las corridas largas; ver `docs/resultados.md`)* |
| Extrapolación a una iteración con `m = n = 200 000` | ~24,3–24,5 minutos (dos métodos independientes de estimación; **extrapolación, no corrida real**, ver `docs/decisiones_diseno.md`) |
| Memoria pico medida, `n = 200 000`, versión dispersa | ~97 MB (`m=2 048`) |
| Memoria que exigirían las matrices densas, `n = 200 000` | 320 GB (calculado, no ejecutado; `aco_denso.cpp` se niega a correr con `n > 5 000`) |

¹ La variación entre 15 s y 8,5 s para la misma `m=2 048` corresponde a
corridas medidas en momentos distintos del proyecto, con configuraciones de
parámetros ligeramente distintas (`K`, si `two=1`, etc.); ambas son del
mismo orden de magnitud y confirman que el tiempo por iteración con
`m=2 048` es de segundos, no de minutos.

## Qué esperar en equipos con menos núcleos

El tiempo de construcción de las hormigas paraleliza casi sin coordinación
entre hilos (ver `informe/informe.tex`, sección "Análisis de complejidad");
en un equipo con la mitad de hilos, el tiempo por iteración con la misma
`m` debería ser, de forma aproximada, el doble (la parte secuencial de cada
iteración — evaporación, recálculo de pesos — es pequeña frente a la
construcción, así que la ley de Amdahl no cambia mucho esta estimación para
un número moderado de hilos). En un equipo de un solo hilo, esperar del
orden de 12 veces más tiempo que lo medido aquí.

## Recomendaciones para ejecutar las corridas grandes

- Conectar el equipo a la corriente (no depender de la batería).
- No dejar el equipo suspenderse: `scripts/ejecutar_corridas_largas.ps1` ya
  llama a `SetThreadExecutionState` para evitarlo mientras corre, sin
  cambiar ningún plan de energía del sistema.
- No correr otras tareas pesadas (compilar, otro barrido, otro programa que
  use muchos hilos) al mismo tiempo: contamina las mediciones de tiempo.
- Si el tiempo disponible es corto, usar `--tiempo_max` (presupuesto de
  tiempo por iteración) o reducir `--iters`, y decirlo con claridad en el
  informe como una corrida recortada, no como un resultado final.

## Modo rápido

Para ver el programa correr en `n=200 000` sin esperar horas: `m=2 048` (no
`m=20 000` ni `m=n`), 2 iteraciones. Medido en ~17 s en la máquina del
estudiante.

```
powershell -File scripts\ejecutar_modo_rapido.ps1
```
