// ACO (Ant Colony Optimization) para el TSP euclidiano, version DENSA de referencia.
//
// A diferencia de aco_tsp.cpp (version dispersa, con lista de K vecinas por ciudad),
// aqui se construyen matrices completas n x n de distancia y de feromona, y la ruleta
// de cada hormiga considera TODAS las ciudades no visitadas (no solo K candidatas).
// Sirve como linea base para medir cuanto ahorran en tiempo y memoria las estrategias
// de aco_tsp.cpp (ver docs/estrategias_ahorro.md).
//
// Memoria: 2 matrices n*n en float (distancia + feromona) = 2*4*n^2 bytes. Por eso este
// programa se niega a ejecutarse con n > 5000 (200 000^2 exigiria 320 GB): en ese caso
// solo calcula y reporta la memoria que exigiria, y termina sin construir nada.
//
// Formulas: las mismas de aco_tsp.cpp (diapositivas 14-19), pero sin lista de candidatos
// ni segunda feromona (no hacen falta para el proposito de comparacion de esta version).
//
// Compilar (Linux):    g++ -O3 -march=native -std=c++20 -fopenmp aco_denso.cpp -o aco_denso
// Compilar (Windows, MinGW-w64): -static evita depender de las DLL de MinGW en el PATH.
//   g++ -O3 -march=native -std=c++20 -fopenmp -static aco_denso.cpp -o aco_denso.exe -lpsapi

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#include <omp.h>
#ifdef _WIN32
#include <windows.h>
#include <psapi.h>
#else
#include <sys/resource.h>
#endif

using u32 = uint32_t;
using u64 = uint64_t;
using Clock = std::chrono::steady_clock;

static double secs(Clock::time_point a, Clock::time_point b) {
    return std::chrono::duration<double>(b - a).count();
}
static double peakRssMB() {
#ifdef _WIN32
    PROCESS_MEMORY_COUNTERS pmc;
    pmc.cb = sizeof(pmc);
    if (!GetProcessMemoryInfo(GetCurrentProcess(), &pmc, sizeof(pmc))) return 0.0;
    return (double)pmc.PeakWorkingSetSize / (1024.0 * 1024.0);
#else
    rusage ru{};
    getrusage(RUSAGE_SELF, &ru);
    return ru.ru_maxrss / 1024.0;
#endif
}

struct Rng {
    u64 s;
    explicit Rng(u64 seed) : s(seed * 0x9E3779B97F4A7C15ULL + 0x1234567ULL) { next(); next(); }
    inline u64 next() { s ^= s << 13; s ^= s >> 7; s ^= s << 17; return s; }
    inline float uni() { return (next() >> 40) * (1.0f / 16777216.0f); }  // [0,1)
};

struct Params {
    int n = 2000;
    int m = 2048;
    int iters = 50;
    double timeBudget = 1e18;
    int stall = 1 << 30;
    float alpha = 1.0f, beta = 3.0f, rho = 0.1f;
    float qfac = 1.0f;
    u64 seed = 1;
    int exact = 0;
    std::string tourOut;
};

// ---------------------------------------------------------------- instancia densa
struct Instance {
    int n = 0;
    std::vector<float> x, y;   // coordenadas en el cuadrado unidad
    std::vector<float> D;      // n*n distancias
    inline float dist(int a, int b) const { return D[(size_t)a * n + b]; }
};

static void buildInstance(Instance& I, const Params& P) {
    const int n = P.n;
    I.n = n;
    I.x.resize(n); I.y.resize(n);
    Rng rng(P.seed * 7919 + 13);
    for (int i = 0; i < n; i++) { I.x[i] = rng.uni(); I.y[i] = rng.uni(); }
    I.D.assign((size_t)n * n, 0.f);
#pragma omp parallel for schedule(static)
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            if (i == j) continue;
            float dx = I.x[i] - I.x[j], dy = I.y[i] - I.y[j];
            I.D[(size_t)i * n + j] = std::sqrt(dx * dx + dy * dy);
        }
    }
}

// ---------------------------------------------------------------- estado por hilo
struct ThreadState {
    std::vector<char> vis;
    std::vector<int> tourC;
    std::vector<int> bestC;
    double bestL = 1e300;
    Rng rng{1};
    void init(int n, u64 seed) {
        vis.assign(n, 0);
        tourC.assign(n, 0);
        bestC.assign(n, 0);
        rng = Rng(seed);
    }
};

// Construye un tour por ruleta sobre TODAS las ciudades no visitadas.
// Si w == nullptr hace vecino mas cercano (greedy, para L_nn).
static double buildTour(const Instance& I, ThreadState& T, const std::vector<float>* w, int start) {
    const int n = I.n;
    std::fill(T.vis.begin(), T.vis.end(), 0);
    int cur = start;
    T.vis[cur] = 1;
    T.tourC[0] = cur;
    double L = 0;
    std::vector<float> tmp(n);
    for (int step = 1; step < n; step++) {
        int nxt = -1;
        if (w) {
            float sum = 0;
            for (int j = 0; j < n; j++) {
                if (T.vis[j]) { tmp[j] = 0.f; continue; }
                float wk = (*w)[(size_t)cur * n + j];
                tmp[j] = wk; sum += wk;
            }
            float r = T.rng.uni() * sum, acc = 0;
            for (int j = 0; j < n; j++) {
                if (tmp[j] <= 0.f) continue;
                acc += tmp[j]; nxt = j;
                if (r < acc) break;
            }
        } else {
            float bd = 1e30f;
            for (int j = 0; j < n; j++) {
                if (T.vis[j]) continue;
                float d = I.dist(cur, j);
                if (d < bd) { bd = d; nxt = j; }
            }
        }
        L += I.dist(cur, nxt);
        T.tourC[step] = nxt;
        T.vis[nxt] = 1;
        cur = nxt;
    }
    L += I.dist(cur, start);
    return L;
}

// ---------------------------------------------------------------- Held-Karp (verificacion n<=20)
static double heldKarp(const Instance& I) {
    int n = I.n; int m = n - 1;
    size_t S = (size_t)1 << m;
    std::vector<double> dp(S * m, 1e18);
    for (int j = 0; j < m; j++) dp[((size_t)1 << j) * m + j] = I.dist(0, j + 1);
    for (size_t mask = 1; mask < S; mask++)
        for (int j = 0; j < m; j++) {
            if (!(mask >> j & 1)) continue;
            double cur = dp[mask * m + j]; if (cur >= 1e17) continue;
            for (int t = 0; t < m; t++) {
                if (mask >> t & 1) continue;
                size_t nm = mask | ((size_t)1 << t);
                double v = cur + I.dist(j + 1, t + 1);
                if (v < dp[nm * m + t]) dp[nm * m + t] = v;
            }
        }
    double best = 1e18;
    for (int j = 0; j < m; j++) best = std::min(best, dp[(S - 1) * m + j] + I.dist(j + 1, 0));
    return best;
}

static inline void atomicAdd(float& ref, float v) {
    std::atomic_ref<float> a(ref);
    a.fetch_add(v, std::memory_order_relaxed);
}

int main(int argc, char** argv) {
    Params P;
    for (int i = 1; i < argc; i++) {
        std::string a = argv[i];
        auto nx = [&]() { return std::string(argv[++i]); };
        if (a == "--n") P.n = std::stoi(nx());
        else if (a == "--ants") P.m = std::stoi(nx());
        else if (a == "--iters") P.iters = std::stoi(nx());
        else if (a == "--time") P.timeBudget = std::stod(nx());
        else if (a == "--stall") P.stall = std::stoi(nx());
        else if (a == "--alpha") P.alpha = std::stof(nx());
        else if (a == "--beta") P.beta = std::stof(nx());
        else if (a == "--rho") P.rho = std::stof(nx());
        else if (a == "--qfac") P.qfac = std::stof(nx());
        else if (a == "--seed") P.seed = std::stoull(nx());
        else if (a == "--exact") P.exact = std::stoi(nx());
        else if (a == "--tour") P.tourOut = nx();
        else { fprintf(stderr, "arg desconocido: %s\n", a.c_str()); return 1; }
    }

    // Guardia de memoria: no se construye nada si la matriz densa fuera inviable.
    // 2 matrices n*n en float (distancia + feromona) = 2*4*n^2 bytes.
    const double denseGB = 2.0 * (double)P.n * P.n * 4 / 1e9;
    if (P.n > 5000) {
        printf("# aco_denso: n=%d supera el limite de 5000 previsto para la version densa.\n", P.n);
        printf("# memoria estimada para matrices D + tau (float, 2 * 4 * n^2 bytes) = %.3f GB\n", denseGB);
        printf("# no se ejecuta; usar aco_tsp (version dispersa, K vecinas) para esta instancia.\n");
        return 3;
    }

    const int nth = omp_get_max_threads();
    auto t0 = Clock::now();

    Instance I;
    buildInstance(I, P);
    const int n = I.n, m = P.m;
    auto t1 = Clock::now();
    double rssAfterBuild = peakRssMB();

    std::vector<ThreadState> TS(nth);
    for (int t = 0; t < nth; t++) TS[t].init(n, P.seed * 1000 + t);

    double Lnn = buildTour(I, TS[0], nullptr, (int)(P.seed % n));
    const size_t E = (size_t)n * n;
    std::vector<float> tau(E, 1.0f), delta(E, 0.f), w(E), etaB(E);
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            etaB[(size_t)i * n + j] = (i == j) ? 0.f : std::pow(1.0f / I.dist(i, j), P.beta);
    const float Qn = P.qfac * (float)Lnn / (float)m;
    const float tmin = 0.01f, tmax = 100.f;

    std::vector<int> gbC(n, 0);
    double gbL = 1e300;
    int stallCnt = 0, itDone = 0;

    printf("# aco_denso n=%d m=%d alpha=%.2f beta=%.2f rho=%.2f hilos=%d semilla=%llu\n",
           n, m, P.alpha, P.beta, P.rho, nth, (unsigned long long)P.seed);
    printf("# preparacion (puntos+matriz D): %.3f s | L_nn=%.4f\n", secs(t0, t1), Lnn);
    printf("# iter  mejor_iter  mejor_global  media_hormigas  t_iter(s)  t_total(s)\n");

    auto tLoop = Clock::now();
    for (int it = 0; it < P.iters; it++) {
        auto ti = Clock::now();
#pragma omp parallel for schedule(static)
        for (long e = 0; e < (long)E; e++) {
            float v = (P.alpha == 1.0f) ? tau[e] : std::pow(tau[e], P.alpha);
            w[e] = v * etaB[e];
        }
        std::fill(delta.begin(), delta.end(), 0.f);
        for (auto& T : TS) T.bestL = 1e300;
        double sumL = 0;
#pragma omp parallel reduction(+ : sumL)
        {
            ThreadState& T = TS[omp_get_thread_num()];
#pragma omp for schedule(dynamic, 1)
            for (int a = 0; a < m; a++) {
                int start = (int)(T.rng.next() % (u64)n);
                double L = buildTour(I, T, &w, start);
                sumL += L;
                if (L < T.bestL) { T.bestL = L; T.bestC = T.tourC; }
                float dep = Qn / (float)L;
                for (int s = 0; s < n; s++) {
                    int c1 = T.tourC[s], c2 = T.tourC[(s + 1) % n];
                    atomicAdd(delta[(size_t)c1 * n + c2], dep);
                    atomicAdd(delta[(size_t)c2 * n + c1], dep);
                }
            }
        }
        double itBest = 1e300; int bt = -1;
        for (int t = 0; t < nth; t++) if (TS[t].bestL < itBest) { itBest = TS[t].bestL; bt = t; }
        bool improved = false;
        if (itBest < gbL) { gbL = itBest; gbC = TS[bt].bestC; improved = true; }
        stallCnt = improved ? 0 : stallCnt + 1;

        const float keep = 1.0f - P.rho;
#pragma omp parallel for schedule(static)
        for (long e = 0; e < (long)E; e++) tau[e] = std::min(tmax, std::max(tmin, keep * tau[e] + delta[e]));

        itDone = it + 1;
        double dt = secs(ti, Clock::now()), tot = secs(tLoop, Clock::now());
        printf("%5d  %10.4f  %12.4f  %14.4f  %9.3f  %10.3f\n", it + 1, itBest, gbL, sumL / m, dt, tot);
        fflush(stdout);
        if (tot >= P.timeBudget || stallCnt >= P.stall) break;
    }
    auto t2 = Clock::now();

    std::vector<char> seen(n, 0); bool ok = true; double Lchk = 0;
    for (int s = 0; s < n; s++) {
        int c = gbC[s]; if (c < 0 || c >= n || seen[c]) { ok = false; break; }
        seen[c] = 1;
        int d = gbC[(s + 1) % n];
        Lchk += I.dist(c, d);
    }
    double rss = peakRssMB();
    printf("# ---- resumen ----\n");
    printf("n=%d m=%d iters=%d tour_valido=%s L_mejor=%.5f (verificado %.5f) L_nn=%.5f mejora_vs_nn=%.2f%%\n",
           n, m, itDone, ok ? "SI" : "NO", gbL, Lchk, Lnn, 100.0 * (Lnn - gbL) / Lnn);
    if (n >= 1000) {
        double est = 0.7124 * std::sqrt((double)n) * (1.0 + 0.33 / std::sqrt((double)n) * 1.0);
        printf("aprox_optimo(BHH)=%.3f  L_mejor/aprox=%.3f\n", est, gbL / est);
    }
    if (P.exact && n <= 20) {
        double opt = heldKarp(I);
        printf("optimo_exacto(Held-Karp)=%.5f  gap=%.3f%%\n", opt, 100.0 * (gbL - opt) / opt);
    }
    printf("tiempo: preparacion=%.3f s  ACO=%.3f s  total=%.3f s  (%.4f s/iter)\n",
           secs(t0, t1), secs(tLoop, t2), secs(t0, t2), secs(tLoop, t2) / std::max(1, itDone));
    printf("memoria: pico RSS=%.1f MB (tras matriz D %.1f MB) | matrices densas D+tau reales = %.3f GB\n",
           rss, rssAfterBuild, denseGB);
    if (!P.tourOut.empty()) {
        FILE* f = fopen(P.tourOut.c_str(), "w");
        for (int s = 0; s < n; s++) fprintf(f, "%d %.6f %.6f\n", gbC[s], I.x[gbC[s]], I.y[gbC[s]]);
        fclose(f);
    }
    printf("CSV,%d,%d,0,0,%d,%.6f,%.6f,%.3f,%.3f,%.1f\n", n, m, itDone, gbL, Lnn,
           secs(t0, t1), secs(tLoop, t2), rss);
    return ok ? 0 : 2;
}
