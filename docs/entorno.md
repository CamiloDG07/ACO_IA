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
| g++ (MinGW-w64, WinLibs) | Sí (instalado en esta fase) | 16.1.0 (x86_64-ucrt-posix-seh) | Sí. Pasa la prueba de C++20 + `std::atomic_ref<float>` + OpenMP (`omp_get_max_threads()=12`) |
| MSVC (`cl.exe`, Visual Studio) | No | — (no existe `vswhere.exe`; Visual Studio no está instalado) | No hizo falta: MinGW-w64 ya sirvió (orden a) |
| clang | No | — | No hizo falta |
| WSL | No | — (`wsl --status`: "El Subsistema de Windows para Linux no está instalado") | No hizo falta |
| cmake | Sí (vino con el paquete WinLibs) | — | No es imprescindible; el proyecto compila con una sola línea de `g++` |
| ninja | Sí (vino con el paquete WinLibs) | — | No es imprescindible |
| make | Sí (`mingw32-make`, vino con el paquete WinLibs) | — | No es imprescindible |
| git | Sí | 2.53.0.windows.2 | Sí. Identidad configurada: Camilo Diaz Garcia <camilodgarcia23@gmail.com> |
| Credential manager de git | Sí | `credential.helper=manager` (Git Credential Manager) | Sí. Confirmado con dos `git push origin main` reales, sin pedir contraseña ni bloquear de forma interactiva |
| Acceso de lectura/escritura al remoto `https://github.com/CamiloDG07/ACO_IA.git` | Sí | `git ls-remote` y `git push` responden con éxito | Sí |
| Python | Sí | 3.14.3 | Sí |
| numpy | Sí | 2.5.2 | Sí |
| pandas | Sí | 3.0.5 | Sí |
| matplotlib | Sí | 3.11.1 | Sí |
| LaTeX (MiKTeX `pdflatex`) | Sí | MiKTeX-pdfTeX 4.27 (MiKTeX 26.5) | Sí |
| `latexmk` | Sí | 4.88 | Sí |
| `gh` (GitHub CLI) | No | — | No es imprescindible (se usa `git` directamente) |
| `winget` | Sí | — | Disponible para instalar el compilador si se autoriza |

## Compilador elegido

Al iniciar la Fase 0 no había ningún compilador de C++ utilizable en la
máquina (ni MinGW-w64, ni MSVC, ni clang, ni WSL con g++). Se presentaron las
opciones al estudiante (ver historial de la conversación) y se autorizó
instalar **WinLibs GCC (MinGW-w64)** vía `winget`:

```
winget install --id BrechtSanders.WinLibs.POSIX.UCRT --accept-source-agreements --accept-package-agreements -e
```

Quedó instalado GCC/G++ **16.1.0** (`x86_64-ucrt-posix-seh`), con `cmake`,
`ninja` y `mingw32-make` incluidos de regalo en el mismo paquete. El
instalador ya agrega su carpeta `bin\` al PATH de usuario (se necesita una
terminal nueva para que el cambio de PATH surta efecto).

**Compilador elegido, siguiendo el orden (a) MinGW-w64 → (b) MSVC → (c) WSL:
(a) MinGW-w64 g++ 16.1.0**, porque fue la primera opción del orden y pasó la
prueba mínima sin problema; no hizo falta evaluar MSVC ni WSL.

Prueba mínima (C++20 + `std::atomic_ref<float>` + `#pragma omp parallel`):

```cpp
#include <atomic>
#include <cstdio>
#include <omp.h>
int main() {
    float x = 0.0f;
    std::atomic_ref<float> a(x);
    a.fetch_add(1.0f, std::memory_order_relaxed);
    printf("atomic_ref OK, x=%.1f\n", x);
#pragma omp parallel
    { #pragma omp single
      printf("omp_get_max_threads()=%d\n", omp_get_max_threads()); }
}
```

Comando: `g++ -std=c++20 -fopenmp -O2 _prueba_min.cpp -o _prueba_min.exe`.
Resultado: compila y corre sin errores, `atomic_ref OK, x=1.0` y
`omp_get_max_threads()=12` (coincide con los 12 hilos lógicos de la máquina).

Comandos de compilación del proyecto con este compilador:

```
g++ -O3 -march=native -std=c++20 -fopenmp aco_tsp.cpp -o aco_tsp.exe
```

## Compilación de diagnóstico (paso 7 de la Fase 0)

Se compiló `src/aco_tsp.cpp` tal cual, sin modificarlo, con el comando de
arriba. Como se esperaba, falla en la inclusión de una cabecera exclusiva de
Linux:

```
aco_tsp.cpp:37:10: fatal error: sys/resource.h: No such file or directory
   37 | #include <sys/resource.h>
      |          ^~~~~~~~~~~~~~~~
compilation terminated.
```

Se corrige en la Fase 1, reemplazando la medición de pico de memoria
(`getrusage`/`ru_maxrss`) por `GetProcessMemoryInfo`/`PeakWorkingSetSize`
bajo `#ifdef _WIN32`.
