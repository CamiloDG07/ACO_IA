# Estructura de referencia: Taller_Colina-Temple

Resumen de qué se replica y qué cambia respecto al taller anterior
(`D:\camilo\Documentos\Taller_Colina-Temple`, 8-puzzle: ascenso de colinas
contra temple simulado), tomado como modelo de completitud.

## Qué tiene el taller de referencia

```
Taller_Colina-Temple/
  README.md              contexto, contenido del repo, cómo reproducir
  requirements.txt        dependencias de Python
  src/                     módulos: formulación, algoritmos, visualización, pipeline de experimentos
  notebook/                notebook que solo reporta resultados ya calculados (no recalcula)
  resultados/
    datos/                 CSV de métricas
    figuras/                PNG referenciadas desde el informe
  informe/
    informe.tex             LaTeX con estilo institucional (logo, portada, encabezado, tabla de contenido)
    informe.pdf
    sergio_logo.png
    figuras_codigo/          capturas de código citadas en el informe
  entregable/                copia autosuficiente para entrega: README propio, notebook, requirements,
                              resultados y src, sin el historial de git ni el .tex fuente
```

No tiene `docs/` ni archivos de bitácora o de decisiones de diseño
independientes: el proceso y las decisiones quedan documentados dentro del
propio informe y del notebook, no en archivos aparte. El historial de `git`
es corto (dos commits).

## Qué se replica en ACO_IA

- Carpetas `src/`, `resultados/` (con subcarpetas `datos`/`figuras` o
  equivalente), `informe/` con el mismo estilo institucional (logo de la
  Universidad Sergio Arboleda, portada, encabezado, tabla de contenido) y
  `requirements.txt` para las dependencias de Python.
- Un `README.md` en la raíz que explica cómo compilar, ejecutar y reproducir
  cada tabla y figura, igual que el del taller de referencia.
- Carpeta `scripts/` para los lanzadores de experimentos y de gráficas,
  equivalente a lo que allá vive dentro de `src/experimentos.py` y
  `src/visualizacion.py` (aquí se separa porque el núcleo del algoritmo está
  en C++ y el pipeline de experimentos en Python son programas aparte).
- El principio de "no recalcular en la revisión": los resultados en
  `resultados/` y las figuras en `figuras/` quedan guardados de antemano;
  cualquier notebook o documento de revisión los lee, no los regenera.

## Qué cambia en ACO_IA

- **Sí lleva `docs/`** con bitácora (`docs/bitacora.md`), decisiones de diseño
  (`docs/decisiones_diseno.md`), estrategias de ahorro
  (`docs/estrategias_ahorro.md`), proceso (`docs/proceso.md`), resultados
  (`docs/resultados.md`), entorno (este mismo `docs/entorno.md`) y guía de
  exposición (`docs/guia_exposicion.md`). El enunciado de este taller pide
  explícitamente ese nivel de trazabilidad del proceso, que el taller de
  colina y temple no necesitó documentar aparte.
- El núcleo del algoritmo es C++ (no Python), por el volumen de cómputo
  (200 000 ciudades, potencialmente 200 000 hormigas); Python queda para
  orquestar experimentos y graficar, no para el algoritmo en sí.
- No se prevé por ahora una carpeta `entregable/` separada: se decidirá al
  cerrar la Fase 5 si hace falta una copia autosuficiente para la entrega,
  siguiendo el mismo patrón si el equipo lo pide.
