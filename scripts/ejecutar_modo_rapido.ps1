# Modo rapido: para quien quiera ver el programa correr en n=200000 sin
# esperar horas. Usa m=2048 (no m=20000) y solo 2 iteraciones: medido en
# ~17 s en total en un i7-8750H de 12 hilos (~8,5 s por iteracion con esta
# configuracion). No reemplaza las corridas completas de
# docs/decisiones_diseno.md ni de resultados/.
$raiz = "D:\camilo\Documentos\ACO_IA"
$exe = Join-Path $raiz "src\aco_tsp.exe"
& $exe --n 200000 --ants 2048 --iters 2 --K 8 --alpha 1.5 --beta 5 --rho 0.1 --qfac 3 --two 1 --alpha2 1.0 --seed 1
