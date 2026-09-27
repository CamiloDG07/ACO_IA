# Resultados

Una tabla por métrica (longitud, tiempo, memoria) por instancia, con media,
desviación, mínimo y máximo, la configuración usada y la comparación con
vecino más cercano, óptimo exacto (n = 20) y aproximación asintótica
(n grande). Configuración usada en todas las instancias, salvo donde se
indique lo contrario (ver `docs/decisiones_diseno.md`): K=8, alpha=1.5,
beta=5, rho=0.1, qfac=3, segunda feromona activada (alpha2=1.0), m =
min(n, 20 000).

## n = 20 (`resultados/instancia_n20.csv`, 5 semillas, m=20, K=19)

| Semilla | L\_mejor | Óptimo exacto (Held-Karp) | Gap (%) | Tour válido |
| ---: | ---: | ---: | ---: | :---: |
| 1 | 4,154 | 4,106 | 1,176 | sí |
| 2 | 4,270 | 4,270 | 0,000 | sí |
| 3 | 3,537 | 3,537 | 0,000 | sí |
| 4 | 4,075 | 4,075 | 0,000 | sí |
| 5 | 4,266 | 4,266 | 0,000 | sí |

Gap medio: 0,235 %; desviación estándar: 0,526 puntos porcentuales; mínimo:
0,000 %; máximo: 1,176 %. 4 de 5 semillas llegan al óptimo exacto. Todas las
corridas dan un tour válido (permutación) verificado internamente.

## n = 2 000 (`resultados/seleccion_configuracion.csv`, configuración ganadora, 8 semillas, m=2 000, K=8, iters=50)

| Métrica | Media | Desv. estándar | Mínimo | Máximo |
| --- | ---: | ---: | ---: | ---: |
| L\_mejor | 37,496 | 0,352 | 36,939 | 38,005 |

Comparación: la nota preliminar del enunciado (otra máquina, una sola
semilla, configuración sin segunda feromona) reportaba 38,20 para una
configuración parecida; la longitud media de 8 semillas con la
configuración ganadora (37,50) es consistente con ese orden de magnitud y
ligeramente mejor, coherente con la mejora estadísticamente significativa de
la segunda feromona encontrada en el barrido (`docs/decisiones_diseno.md`).

*(Tiempo y memoria para n=2 000, y toda la tabla de n=200 000, se completan
con `scripts/generar_figuras.py` una vez cerradas las corridas largas —
bloque C — y generadas las tablas automáticas en `informe/tablas/`.)*

## n = 200 000

*(pendiente: se completa al cerrar el bloque C — corrida real con
m=20 000, 10 iteraciones, hasta 3 semillas, y la comparación a igual
presupuesto de cómputo contra m=2 048. Ver `docs/bitacora.md` para el
registro cronológico de esas corridas y `docs/RESUMEN_FINAL.md` para el
estado definitivo.)*
