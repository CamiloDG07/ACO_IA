# Resumen final

*(Documento vivo: se completa al cerrar el bloque H del modo autónomo. Esta
versión refleja el estado a mitad del bloque C — corridas largas en curso —
y se reescribe al terminar.)*

## Qué se hizo

- Fase 0: reconocimiento del entorno, instalación autorizada de MinGW-w64
  g++ 16.1.0 (WinLibs), estructura de referencia.
- Fase 1: portabilidad a Windows, `--input` (TSPLIB/plano), `--tiempo_max`,
  `aco_denso.cpp` (versión densa de referencia con guardia de memoria),
  cuatro pruebas automáticas.
- Fase 2: elección de lenguaje (C++/OpenMP, justificación teórica sin medir
  otros lenguajes), número de agentes `m = min(n, 20000)` con cita
  verificada de Dorigo y Stützle (2004), barrido de parámetros (5-8
  semillas), selección estadística de la configuración ganadora (segunda
  feromona, mejora significativa por prueba de Wilcoxon), escalamiento
  dispersa/densa, costo de `m` en `n=200000` con extrapolación lineal.
- Modo autónomo (este cierre): bloque A completado (n=20 contra Held-Karp
  con 5 semillas, curvas de convergencia); bloque B (scripts de corridas
  largas con envoltorio anti-suspensión, reanudables); bloque C en curso o
  cerrado (ver más abajo).

## Qué se midió

Ver `docs/resultados.md`, `docs/decisiones_diseno.md` y los CSV de
`resultados/` para cada cifra con su respaldo. Nada en este proyecto se
reporta sin una corrida guardada detrás.

## Qué quedó incompleto o recortado, y por qué

*(se completa al cerrar el bloque C; si el presupuesto de 4 horas obligó a
reducir semillas o iteraciones de alguna corrida larga, se documenta aquí
con el motivo exacto)*

## Tiempos reales de las corridas largas

*(se completa con las horas de inicio y fin registradas en
`docs/bitacora.md` para cada semilla de los puntos 5 y 6)*

## Lista de verificación de lo entregable

- [ ] `informe/informe.pdf` compilado, sin referencias rotas, con todas las
      figuras
- [ ] `README.md`
- [ ] `ADVERTENCIA_TIEMPO_200K.md`
- [ ] `docs/` completa (bitácora, entorno, decisiones de diseño,
      estrategias de ahorro, resultados, proceso, guía de exposición)
- [ ] `resultados/*.csv`
- [ ] `figuras/*.png`
- [ ] `scripts/` reproducibles
- [ ] Sin binarios ni archivos temporales en el repositorio
- [ ] `git shortlog -sne` solo muestra al estudiante; sin menciones a IA en
      commits ni archivos
