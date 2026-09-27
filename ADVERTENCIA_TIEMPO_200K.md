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
| Tiempo por hormiga (efectivo, ya paralelo, 12 hilos, config. ganadora) | ~4,3 ms |
| Tiempo por iteración, `m = 2 048` | ~8,7 s medido directamente (3 repeticiones, `resultados/costo_m_n200000_3reps.csv`) |
| Tiempo por iteración, `m = 20 000` | ~86,9 s medido directamente (3 repeticiones) |
| Corrida real, `n=200 000`, `m=20 000`, 10 iteraciones, 3 semillas | 13,8 a 14,2 minutos por semilla (`docs/bitacora.md`); mejora media del 1,28 % sobre el vecino más cercano |
| Igual presupuesto (~15 min/semilla), `m=2 048`, ~108 iteraciones | mejora media del 1,75 % sobre el vecino más cercano — **mejor** que `m=20 000` con 10 iteraciones, en las 3 semillas (ver `docs/decisiones_diseno.md`) |
| Extrapolación a una iteración con `m = n = 200 000` | ~14,5 minutos (ajuste lineal, R²=1,000000; **extrapolación, no corrida real**, ver `docs/decisiones_diseno.md`) |
| Memoria pico medida, `n = 200 000`, versión dispersa | ~102 MB (`m=2 048` o `m=20 000`: la memoria no depende de `m`, ver `docs/estrategias_ahorro.md`) |
| Memoria que exigirían las matrices densas, `n = 200 000` | 320 GB (calculado, no ejecutado; `aco_denso.cpp` se niega a correr con `n > 5 000`) |

Nota: una medición preliminar de la Fase 2 (una sola repetición, sin la
segunda capa de feromona) había dado ~144,85 s para `m=20 000` y una
extrapolación de ~24,3 min/iteración. La medición con 3 repeticiones y la
configuración final (con segunda feromona) dio un tiempo por hormiga menor
y consistente con la corrida real; ambas mediciones quedan documentadas en
`docs/decisiones_diseno.md`, con la diferencia explicada, no oculta.

Se revisó el tiempo por iteración de las 6 corridas del bloque de cierre
(354 iteraciones en total, 348 pares consecutivos) buscando variaciones
mayores al 15 % entre iteraciones consecutivas (señal de que el equipo se
desacelera). No se encontró ninguna: el equipo se mantuvo estable durante
toda la ejecución.

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
