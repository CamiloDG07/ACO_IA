# Corridas largas de la Fase 2 (bloque B/C del modo autonomo). Reanudable:
# si un archivo de salida ya existe y quedo completo, no se relanza esa
# corrida. Nunca corre mas de una corrida de ACO a la vez. Evita que Windows
# suspenda el equipo mientras corre (SetThreadExecutionState) y la libera al
# terminar, sin cambiar ningun plan de energia del sistema.

$ErrorActionPreference = "Stop"
$raiz = "D:\camilo\Documentos\ACO_IA"
$exe = Join-Path $raiz "src\aco_tsp.exe"
$resultados = Join-Path $raiz "resultados"
$bitacora = Join-Path $raiz "docs\bitacora.md"
New-Item -ItemType Directory -Force -Path $resultados | Out-Null

# --- evitar suspension mientras corre (no cambia planes de energia) ---
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class NoSuspender {
    [DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    public static extern uint SetThreadExecutionState(uint esFlags);
}
'@
[uint32]$ES_CONTINUOUS       = [Convert]::ToUInt32("80000000", 16)
[uint32]$ES_SYSTEM_REQUIRED  = [Convert]::ToUInt32("00000001", 16)
[NoSuspender]::SetThreadExecutionState([uint32]($ES_CONTINUOUS -bor $ES_SYSTEM_REQUIRED)) | Out-Null

function Log-Bitacora($linea) {
    Add-Content -Path $bitacora -Value $linea -Encoding UTF8
}

$inicioTotal = Get-Date
Log-Bitacora ""
Log-Bitacora "### Corridas largas: inicio $($inicioTotal.ToString('yyyy-MM-dd HH:mm:ss'))"

# Configuracion ganadora del bloque A (ver docs/decisiones_diseno.md):
# K=8, alpha=1.5, beta=5, rho=0.1, qfac=3, segunda feromona (alpha2=1.0)
$paramsBase = @("--K","8","--alpha","1.5","--beta","5","--rho","0.1","--qfac","3","--two","1","--alpha2","1.0")

function Completo($rutaLog) {
    if (-not (Test-Path $rutaLog)) { return $false }
    return (Select-String -Path $rutaLog -Pattern "^CSV," -Quiet)
}

# ---------------------------------------------------------------- Punto 1
# Costo por iteracion en n=200000, m=200/2000/20000, 3 repeticiones de 1 iteracion.
$rutaCosto = Join-Path $resultados "costo_m_n200000_3reps.csv"
if (-not (Test-Path $rutaCosto)) {
    "m,repeticion,t_aco_s" | Out-File -FilePath $rutaCosto -Encoding UTF8
}
$yaHechas = @{}
if (Test-Path $rutaCosto) {
    Import-Csv $rutaCosto | ForEach-Object { $yaHechas["$($_.m)_$($_.repeticion)"] = $true }
}
foreach ($m in 200,2000,20000) {
    for ($rep = 1; $rep -le 3; $rep++) {
        $clave = "${m}_${rep}"
        if ($yaHechas.ContainsKey($clave)) { continue }
        $log = Join-Path $resultados "log_costo_m${m}_rep${rep}.txt"
        & $exe --n 200000 --ants $m --iters 1 @paramsBase --seed $rep *> $log
        $linea = Select-String -Path $log -Pattern "^CSV," | Select-Object -First 1
        if ($linea) {
            $campos = $linea.Line.Split(",")
            # campos[0]="CSV"; 1=n 2=m 3=K 4=two 5=iters 6=L_mejor 7=L_nn 8=t_prep 9=t_aco 10=rss
            $tAco = $campos[9]
            "$m,$rep,$tAco" | Add-Content -Path $rutaCosto -Encoding UTF8
        }
        Remove-Item $log -ErrorAction SilentlyContinue
    }
}
Log-Bitacora "Punto 1 (costo por iteracion, 3 repeticiones) terminado: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

# ---------------------------------------------------------------- Punto 5
# n=200000, m=20000, 10 iteraciones, semillas 1,2,3.
$presupuestoLimite = (Get-Date).AddHours(3.5)
foreach ($seed in 1,2,3) {
    if ((Get-Date) -gt $presupuestoLimite) {
        Log-Bitacora "Punto 5: se agoto el presupuesto de tiempo antes de la semilla $seed; se detiene aqui."
        break
    }
    $log = Join-Path $resultados "log_punto5_m20000_seed${seed}.txt"
    if (Completo $log) { continue }
    $t0 = Get-Date
    & $exe --n 200000 --ants 20000 --iters 10 @paramsBase --seed $seed *> $log
    $t1 = Get-Date
    Log-Bitacora "Punto 5, semilla ${seed}: inicio $($t0.ToString('HH:mm:ss')), fin $($t1.ToString('HH:mm:ss')), duracion $([math]::Round(($t1-$t0).TotalMinutes,1)) min"
}

# ---------------------------------------------------------------- Punto 6
# n=200000, m=2048, presupuesto de 15 min de reloj por semilla.
foreach ($seed in 1,2,3) {
    if ((Get-Date) -gt $presupuestoLimite) {
        Log-Bitacora "Punto 6: se agoto el presupuesto de tiempo antes de la semilla $seed; se detiene aqui."
        break
    }
    $log = Join-Path $resultados "log_punto6_m2048_seed${seed}.txt"
    if (Completo $log) { continue }
    $t0 = Get-Date
    & $exe --n 200000 --ants 2048 --iters 100000 --time 900 @paramsBase --seed $seed *> $log
    $t1 = Get-Date
    Log-Bitacora "Punto 6, semilla ${seed}: inicio $($t0.ToString('HH:mm:ss')), fin $($t1.ToString('HH:mm:ss')), duracion $([math]::Round(($t1-$t0).TotalMinutes,1)) min"
}

$finTotal = Get-Date
Log-Bitacora "### Corridas largas: fin $($finTotal.ToString('yyyy-MM-dd HH:mm:ss')), duracion total $([math]::Round(($finTotal-$inicioTotal).TotalMinutes,1)) min"

[NoSuspender]::SetThreadExecutionState([uint32]$ES_CONTINUOUS) | Out-Null
Write-Host "CORRIDAS_LARGAS_COMPLETO"
