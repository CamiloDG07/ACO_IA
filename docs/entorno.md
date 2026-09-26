# Entorno de trabajo (Fase 0)

Registro del reconocimiento del entorno para el proyecto ACO_IA (colonia de
hormigas aplicada al TSP). Todos los tiempos que se reporten en el resto del
proyecto deben citar esta máquina.

## Hardware y sistema operativo

| Ítem | Valor |
| --- | --- |
| CPU | Intel(R) Core(TM) i7-8750H @ 2.20GHz |
| Núcleos físicos | 6 |
| Núcleos lógicos (hilos) | 12 |
| RAM total | 15,88 GB |
| RAM libre al momento del reconocimiento | 5,03 GB |
| Sistema operativo | Windows 11 Home, build 26200 |

## Herramientas revisadas

| Herramienta | Instalada | Versión | Sirve para el proyecto |
| --- | --- | --- | --- |
| g++ (MinGW-w64 / MSYS2) | No | — | Bloqueante: es el compilador de primera elección (orden a) |
| MSVC (`cl.exe`, Visual Studio) | No | — (no existe `vswhere.exe`; Visual Studio no está instalado) | Segunda opción (orden b); soporta C++20 pero solo OpenMP 2.0 |
| clang | No | — | No contemplado en el orden de elección salvo caso especial |
| WSL | No | — (`wsl --status`: "El Subsistema de Windows para Linux no está instalado") | Tercera opción (orden c) si trae `g++` |
| cmake | No | — | No es imprescindible; el proyecto compila con una sola línea de `g++`/`cl` |
| ninja | No | — | No es imprescindible |
| make | No | — | No es imprescindible |
| git | Sí | 2.53.0.windows.2 | Sí. Identidad configurada: Camilo Diaz Garcia <camilodgarcia23@gmail.com> |
| Credential manager de git | Sí | `credential.helper=manager` (Git Credential Manager) | Sí, en principio; no pide contraseña en texto plano. Falta confirmar con un push real que no bloquee de forma interactiva |
| Acceso de lectura al remoto `https://github.com/CamiloDG07/ACO_IA.git` | Sí | `git ls-remote` responde con éxito (repositorio vacío, sin refs) | Sí |
| Python | Sí | 3.14.3 | Sí |
| numpy | Sí | 2.5.2 | Sí |
| pandas | Sí | 3.0.5 | Sí |
| matplotlib | Sí | 3.11.1 | Sí |
| LaTeX (MiKTeX `pdflatex`) | Sí | MiKTeX-pdfTeX 4.27 (MiKTeX 26.5) | Sí |
| `latexmk` | Sí | 4.88 | Sí |
| `gh` (GitHub CLI) | No | — | No es imprescindible (se usa `git` directamente) |
| `winget` | Sí | — | Disponible para instalar el compilador si se autoriza |

## Compilador elegido

**Ninguno todavía.** No hay ningún compilador de C++ utilizable en la máquina
(ni MinGW-w64, ni MSVC, ni clang, ni WSL con g++), así que no se pudo aplicar
el orden de elección automática (a) MinGW-w64, (b) MSVC, (c) WSL, ni compilar
la prueba mínima de C++20 + `std::atomic_ref<float>` + OpenMP.

Según la regla de la Fase 0, punto 4, el proceso se detiene aquí: no se
instala nada sin confirmación. Opciones evaluadas con `winget` (ambas
existen en el catálogo y no requieren licencia):

| Opción | Comando | Ventajas | Desventajas |
| --- | --- | --- | --- |
| WinLibs GCC 16.1.0 (POSIX threads, UCRT) — MinGW-w64 independiente | `winget install BrechtSanders.WinLibs.POSIX.UCRT` | Un solo paquete, ya trae `g++` con soporte de C++20 y OpenMP (`libgomp`), coincide con el compilador (GCC) con el que ya se validó el código en Linux; solo falta agregar su `bin\` al PATH | Hay que agregar el PATH a mano (el instalador de winget no siempre lo hace) |
| MSYS2 | `winget install MSYS2.MSYS2` y luego, dentro de la terminal MSYS2 UCRT64: `pacman -S mingw-w64-ucrt-x86_64-gcc` | Gestor de paquetes más flexible a futuro | Más pasos (abrir la terminal MSYS2, instalar el subpaquete, agregar `ucrt64\bin` al PATH) |
| Visual Studio Build Tools (carga "Desarrollo de escritorio con C++") | `winget install Microsoft.VisualStudio.2022.BuildTools --override "--add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"` | Necesario de todas formas si más adelante se quiere probar MSVC | Descarga de varios GB; solo OpenMP 2.0 (el código no usa características más nuevas, así que probablemente alcance, pero no se ha confirmado) |
| WSL + g++ | `wsl --install` (reinicio requerido) y luego `sudo apt install g++` dentro de la distribución | Réplica más fiel del entorno Linux donde se validó el código | Requiere reiniciar Windows para activar WSL; una capa adicional |

Recomendación: **WinLibs GCC (MinGW-w64)** por ser la opción más liviana y
la que respeta el orden (a) del enunciado. Queda pendiente de autorización
del estudiante antes de ejecutar cualquier instalación.

## Compilación de diagnóstico (paso 7 de la Fase 0)

Pendiente: no se puede compilar `src/aco_tsp.cpp` tal cual sin un compilador
de C++ disponible. Se ejecutará en cuanto se instale alguno; se espera que
falle por `<sys/resource.h>` y `getrusage`, que no existen en Windows (se
corrige en la Fase 1).
