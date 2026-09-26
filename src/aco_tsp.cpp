// ACO (Ant Colony Optimization) para el TSP euclidiano, pensado para instancias enormes
// (20, 2 000 y 200 000 ciudades) midiendo TIEMPO y MEMORIA.
//
// Ideas para ahorrar recursos (el "cascaron" del ejercicio):
//   * Nunca se construye la matriz n x n (200k^2 * 4 B = 160 GB). Cada ciudad solo conoce a sus
//     K vecinas mas cercanas (lista de candidatos) => tau, eta y pesos son arreglos de tamano n*K.
//   * Vecinas por rejilla espacial (grid) => O(n) en vez de O(n^2). Ciudades renumeradas por celda
//     para que la memoria sea local (cache).
//   * Si a una hormiga se le acaban las candidatas sin visitar, busca la mas cercana no visitada
//     en la rejilla (anillos de celdas, saltando celdas vacias).
//   * Las hormigas NO guardan su tour: cada hilo reutiliza un unico buffer, y el deposito de
//     feromona se hace al terminar cada hormiga (atomicos) => memoria O(n) sin importar m.
//   * w_ij = tau_ij^alpha * tau2_ij^alpha2 * eta_ij^beta se precalcula UNA vez por iteracion
//     (la feromona es constante durante la construccion) => cada paso de hormiga es una suma y
//     una ruleta de K terminos.
//   * Segunda feromona (opcional, --two 1): capa "elite" reforzada solo por el mejor tour global,
//     con exponente alpha2 < alpha (menor magnitud de influencia que la feromona principal).
//
// Formulas (diapositivas 14-19):  eta=1/d ; p_ij = tau^a * eta^b / sum ; tau <- (1-rho) tau + sum dtau ;
//   dtau = Q/L_k si la hormiga k uso (i,j).  Aqui Q se normaliza como Q = qfac * L_nn / m.
//
// Compilar (Linux):    g++ -O3 -march=native -std=c++20 -fopenmp aco_tsp.cpp -o aco_tsp
// Compilar (Windows, MinGW-w64):
//   g++ -O3 -march=native -std=c++20 -fopenmp aco_tsp.cpp -o aco_tsp.exe -lpsapi

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <numeric>
#include <queue>
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
    return (double)pmc.PeakWorkingSetSize / (1024.0 * 1024.0);  // Windows: bytes
#else
    rusage ru{};
    getrusage(RUSAGE_SELF, &ru);
    return ru.ru_maxrss / 1024.0;  // Linux: KB
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
    int m = 2048;          // hormigas por iteracion
    int iters = 50;        // maximo de iteraciones
    double timeBudget = 1e18;  // segundos (criterio de parada por presupuesto computacional)
    int stall = 1 << 30;   // iteraciones sin mejora
    int K = 10;            // tamano de lista de candidatos
    float alpha = 1.0f, beta = 3.0f, rho = 0.1f;
    float qfac = 1.0f;     // Q normalizado
    int two = 0;           // segunda feromona
    float alpha2 = 0.3f;   // peso de la segunda feromona (< alpha)
    u64 seed = 1;
    int exact = 0;         // Held-Karp (solo n <= 20)
    std::string tourOut;
    std::string inputFile;     // --input: coordenadas desde archivo (TSPLIB EUC_2D o "x y" plano)
    double tiempoMaxIter = 1e18;  // --tiempo_max: presupuesto de tiempo POR ITERACION (segundos)
};

// ---------------------------------------------------------------- instancia + rejilla
struct Instance {
    int n = 0, G = 1, K = 0;
    float cs = 1.f;                 // tamano de celda
    float scale = 1.f;              // factor de escala aplicado al normalizar a [0,1]^2 (--input)
    float offX = 0.f, offY = 0.f;   // esquina inferior izquierda del bounding box original (--input)
    std::vector<float> x, y;        // coordenadas (renumeradas por celda)
    std::vector<u32> cellStart;     // CSR de celdas (G*G+1)
    std::vector<u32> cellOf;        // celda de cada ciudad
    std::vector<int> baseCnt;       // #ciudades por celda
    std::vector<int> nbr;           // n*K vecinas
    std::vector<float> dst;         // n*K distancias

    inline int key(int cx, int cy) const { return cy * G + ((cy & 1) ? G - 1 - cx : cx); }
    inline int cxOf(float px) const { int c = (int)(px * G); return c >= G ? G - 1 : c; }
    inline float dist(int a, int b) const {
        float dx = x[a] - x[b], dy = y[a] - y[b];
        return std::sqrt(dx * dx + dy * dy);
    }
};

// Lectura basica de coordenadas: TSPLIB EUC_2D (NODE_COORD_SECTION ... EOF) o
// formato plano "x y" por linea (sin encabezados). Devuelve coordenadas en las
// unidades originales del archivo (sin normalizar).
static bool loadPointsFromFile(const std::string& path, std::vector<double>& xs,
                                std::vector<double>& ys, std::string& formato) {
    FILE* f = fopen(path.c_str(), "r");
    if (!f) return false;
    char line[1024];
    bool tsplib = false, inCoord = false;
    std::string edgeType = "EUC_2D";
    while (fgets(line, sizeof(line), f)) {
        std::string s(line);
        size_t a = s.find_first_not_of(" \t\r\n");
        if (a == std::string::npos) continue;
        size_t b = s.find_last_not_of(" \t\r\n");
        s = s.substr(a, b - a + 1);
        if (s.empty()) continue;
        if (!tsplib && !inCoord) {
            if (s.rfind("NAME", 0) == 0 || s.rfind("TYPE", 0) == 0 || s.rfind("COMMENT", 0) == 0 ||
                s.rfind("DIMENSION", 0) == 0 || s.rfind("EDGE_WEIGHT_TYPE", 0) == 0 ||
                s.rfind("NODE_COORD_SECTION", 0) == 0) {
                tsplib = true;
            }
        }
        if (tsplib) {
            if (s.rfind("EDGE_WEIGHT_TYPE", 0) == 0) {
                size_t p = s.find(':');
                if (p != std::string::npos) edgeType = s.substr(p + 1);
            }
            if (s.rfind("NODE_COORD_SECTION", 0) == 0) { inCoord = true; continue; }
            if (!inCoord) continue;                 // todavia en encabezados
            if (s.rfind("EOF", 0) == 0) break;
            double idx, x, y;
            if (sscanf(s.c_str(), "%lf %lf %lf", &idx, &x, &y) == 3) { xs.push_back(x); ys.push_back(y); }
        } else {
            double x, y;
            if (sscanf(s.c_str(), "%lf %lf", &x, &y) == 2) { xs.push_back(x); ys.push_back(y); }
        }
    }
    fclose(f);
    if (tsplib && edgeType.find("EUC_2D") == std::string::npos)
        fprintf(stderr, "# aviso: EDGE_WEIGHT_TYPE=%s no es EUC_2D; se leen las coordenadas de todas formas (lectura basica)\n",
                edgeType.c_str());
    formato = tsplib ? "TSPLIB" : "plano (x y)";
    return !xs.empty();
}

static void buildInstance(Instance& I, Params& P) {
    std::vector<float> rx, ry;
    if (!P.inputFile.empty()) {
        std::vector<double> xs, ys; std::string formato;
        if (!loadPointsFromFile(P.inputFile, xs, ys, formato)) {
            fprintf(stderr, "no se pudo leer --input %s (o no tiene coordenadas)\n", P.inputFile.c_str());
            exit(1);
        }
        const int nf = (int)xs.size();
        P.n = nf;
        double minx = xs[0], maxx = xs[0], miny = ys[0], maxy = ys[0];
        for (int i = 1; i < nf; i++) {
            minx = std::min(minx, xs[i]); maxx = std::max(maxx, xs[i]);
            miny = std::min(miny, ys[i]); maxy = std::max(maxy, ys[i]);
        }
        double rangeX = maxx - minx, rangeY = maxy - miny;
        double scale = std::max(rangeX, rangeY); if (scale <= 0) scale = 1.0;
        I.scale = (float)scale; I.offX = (float)minx; I.offY = (float)miny;
        rx.resize(nf); ry.resize(nf);
        for (int i = 0; i < nf; i++) {
            rx[i] = (float)((xs[i] - minx) / scale);
            ry[i] = (float)((ys[i] - miny) / scale);
        }
        fprintf(stderr, "# --input %s: %d ciudades leidas (formato %s), escala=%.6f\n",
                P.inputFile.c_str(), nf, formato.c_str(), scale);
    } else {
        const int n0 = P.n;
        rx.resize(n0); ry.resize(n0);
        Rng rng(P.seed * 7919 + 13);
        for (int i = 0; i < n0; i++) { rx[i] = rng.uni(); ry[i] = rng.uni(); }
        I.scale = 1.f; I.offX = 0.f; I.offY = 0.f;
    }
    const int n = P.n;
    I.n = n;
    I.G = std::max(1, (int)std::sqrt(n / 2.0));
    I.cs = 1.0f / I.G;
    I.K = std::min(P.K, n - 1);
    // ordenar por celda (serpiente) => localidad de memoria
    std::vector<u32> ord(n), k(n);
    for (int i = 0; i < n; i++) k[i] = I.key(I.cxOf(rx[i]), I.cxOf(ry[i]));
    std::iota(ord.begin(), ord.end(), 0);
    std::sort(ord.begin(), ord.end(), [&](u32 a, u32 b) { return k[a] < k[b]; });
    I.x.resize(n); I.y.resize(n); I.cellOf.resize(n);
    const int cells = I.G * I.G;
    I.cellStart.assign(cells + 1, 0);
    I.baseCnt.assign(cells, 0);
    for (int i = 0; i < n; i++) {
        I.x[i] = rx[ord[i]]; I.y[i] = ry[ord[i]];
        I.cellOf[i] = k[ord[i]];
        I.baseCnt[I.cellOf[i]]++;
    }
    for (int c = 0; c < cells; c++) I.cellStart[c + 1] = I.cellStart[c] + I.baseCnt[c];

    // K vecinas mas cercanas por anillos de celdas
    const int K = I.K;
    I.nbr.assign((size_t)n * K, 0);
    I.dst.assign((size_t)n * K, 0.f);
#pragma omp parallel
    {
        std::vector<std::pair<float, int>> heap;
        heap.reserve(K + 1);
#pragma omp for schedule(static)
        for (int i = 0; i < n; i++) {
            heap.clear();
            int cx0 = I.cxOf(I.x[i]), cy0 = I.cxOf(I.y[i]);
            auto scanCell = [&](int cx, int cy) {
                int c = I.key(cx, cy);
                for (u32 p = I.cellStart[c]; p < I.cellStart[c + 1]; p++) {
                    if ((int)p == i) continue;
                    float dx = I.x[p] - I.x[i], dy = I.y[p] - I.y[i];
                    float d2 = dx * dx + dy * dy;
                    if ((int)heap.size() < K) { heap.emplace_back(d2, (int)p); std::push_heap(heap.begin(), heap.end()); }
                    else if (d2 < heap.front().first) {
                        std::pop_heap(heap.begin(), heap.end()); heap.back() = {d2, (int)p};
                        std::push_heap(heap.begin(), heap.end());
                    }
                }
            };
            for (int r = 0; r <= I.G; r++) {
                if (r >= 1 && (int)heap.size() == K) {
                    float lim = (r - 1) * I.cs;
                    if (heap.front().first <= lim * lim) break;
                }
                for (int dy = -r; dy <= r; dy++) {
                    int cy = cy0 + dy;
                    if (cy < 0 || cy >= I.G) continue;
                    if (std::abs(dy) == r) {
                        for (int dx = -r; dx <= r; dx++) { int cx = cx0 + dx; if (cx >= 0 && cx < I.G) scanCell(cx, cy); }
                    } else {
                        int cx = cx0 - r; if (cx >= 0) scanCell(cx, cy);
                        cx = cx0 + r; if (r > 0 && cx < I.G) scanCell(cx, cy);
                    }
                }
            }
            std::sort_heap(heap.begin(), heap.end());  // ascendente por distancia
            for (int s = 0; s < K; s++) {
                I.nbr[(size_t)i * K + s] = heap[s].second;
                I.dst[(size_t)i * K + s] = std::sqrt(heap[s].first);
            }
        }
    }
}

// ---------------------------------------------------------------- estado por hilo (reutilizado)
struct ThreadState {
    std::vector<u32> vis;      // sello de visitado
    u32 stamp = 0;
    std::vector<int> cnt;      // no visitadas por celda
    std::vector<int> tourC;    // ciudades del tour actual
    std::vector<int> tourE;    // indice de arista candidata usada (o -1)
    std::vector<int> bestC;    // mejor tour visto por este hilo en la iteracion
    std::vector<int> bestE;
    double bestL = 1e300;
    Rng rng{1};
    void init(const Instance& I, u64 seed) {
        vis.assign(I.n, 0); cnt = I.baseCnt;
        tourC.assign(I.n, 0); tourE.assign(I.n, -1);
        bestC.assign(I.n, 0); bestE.assign(I.n, -1);
        rng = Rng(seed);
    }
};

static inline void markVisited(const Instance& I, ThreadState& T, int c) {
    T.vis[c] = T.stamp;
    T.cnt[I.cellOf[c]]--;
}

static int nearestUnvisited(const Instance& I, ThreadState& T, int c, float& outD) {
    int cx0 = I.cxOf(I.x[c]), cy0 = I.cxOf(I.y[c]);
    int best = -1; float bd2 = 1e30f;
    auto scanCell = [&](int cx, int cy) {
        int k = I.key(cx, cy);
        if (T.cnt[k] <= 0) return;
        for (u32 p = I.cellStart[k]; p < I.cellStart[k + 1]; p++) {
            if (T.vis[p] == T.stamp) continue;
            float dx = I.x[p] - I.x[c], dy = I.y[p] - I.y[c];
            float d2 = dx * dx + dy * dy;
            if (d2 < bd2) { bd2 = d2; best = (int)p; }
        }
    };
    for (int r = 0; r <= I.G; r++) {
        if (best >= 0 && r >= 1) { float lim = (r - 1) * I.cs; if (bd2 <= lim * lim) break; }
        for (int dy = -r; dy <= r; dy++) {
            int cy = cy0 + dy;
            if (cy < 0 || cy >= I.G) continue;
            if (std::abs(dy) == r) {
                int a = std::max(0, cx0 - r), b = std::min(I.G - 1, cx0 + r);
                for (int cx = a; cx <= b; cx++) scanCell(cx, cy);
            } else {
                int cx = cx0 - r; if (cx >= 0) scanCell(cx, cy);
                cx = cx0 + r; if (r > 0 && cx < I.G) scanCell(cx, cy);
            }
        }
    }
    outD = std::sqrt(bd2);
    return best;
}

// Construye un tour. Si w == nullptr hace el vecino mas cercano (greedy, para L_nn).
static double buildTour(const Instance& I, ThreadState& T, const float* w, int start) {
    const int n = I.n, K = I.K;
    T.stamp++;
    std::memcpy(T.cnt.data(), I.baseCnt.data(), I.baseCnt.size() * sizeof(int));
    int cur = start;
    markVisited(I, T, cur);
    T.tourC[0] = cur;
    double L = 0;
    float tmp[64];
    for (int step = 1; step < n; step++) {
        const size_t base = (size_t)cur * K;
        int nxt = -1, e = -1; float d = 0;
        float sum = 0;
        int first = -1;
        for (int k = 0; k < K; k++) {
            int j = I.nbr[base + k];
            if (T.vis[j] != T.stamp) {
                float wk = w ? w[base + k] : 1.0f;
                tmp[k] = wk; sum += wk;
                if (first < 0) first = k;
            } else tmp[k] = 0.f;
        }
        if (first >= 0) {
            int pick = first;
            if (w) {
                float r = T.rng.uni() * sum, acc = 0; pick = -1;
                for (int k = 0; k < K; k++) {
                    if (tmp[k] <= 0.f) continue;
                    acc += tmp[k]; pick = k;
                    if (r < acc) break;          // ruleta (diapositiva 17)
                }
            }
            e = (int)(base + pick); nxt = I.nbr[e]; d = I.dst[e];
        } else {
            nxt = nearestUnvisited(I, T, cur, d);
            e = -1;
        }
        L += d;
        T.tourC[step] = nxt; T.tourE[step - 1] = e;
        markVisited(I, T, nxt);
        cur = nxt;
    }
    // arista de cierre
    int e = -1; const size_t base = (size_t)cur * K;
    for (int k = 0; k < K; k++) if (I.nbr[base + k] == start) { e = (int)(base + k); break; }
    T.tourE[n - 1] = e;
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
        else if (a == "--K") P.K = std::stoi(nx());
        else if (a == "--alpha") P.alpha = std::stof(nx());
        else if (a == "--beta") P.beta = std::stof(nx());
        else if (a == "--rho") P.rho = std::stof(nx());
        else if (a == "--qfac") P.qfac = std::stof(nx());
        else if (a == "--two") P.two = std::stoi(nx());
        else if (a == "--alpha2") P.alpha2 = std::stof(nx());
        else if (a == "--seed") P.seed = std::stoull(nx());
        else if (a == "--exact") P.exact = std::stoi(nx());
        else if (a == "--tour") P.tourOut = nx();
        else if (a == "--input") P.inputFile = nx();
        else if (a == "--tiempo_max") P.tiempoMaxIter = std::stod(nx());
        else { fprintf(stderr, "arg desconocido: %s\n", a.c_str()); return 1; }
    }
    const int nth = omp_get_max_threads();
    auto t0 = Clock::now();

    Instance I;
    buildInstance(I, P);
    const int n = I.n, K = I.K, m = P.m;
    auto t1 = Clock::now();
    double rssAfterBuild = peakRssMB();

    // feromonas y pesos: solo sobre aristas candidatas (n*K)
    std::vector<ThreadState> TS(nth);
    for (int t = 0; t < nth; t++) TS[t].init(I, P.seed * 1000 + t);

    // L_nn (vecino mas cercano desde una ciudad al azar)
    double Lnn = buildTour(I, TS[0], nullptr, (int)(P.seed % n));
    const size_t E = (size_t)n * K;
    std::vector<float> tau(E, 1.0f), tau2, delta(E, 0.f), w(E), etaB(E);
    if (P.two) tau2.assign(E, 1.0f);
    for (size_t e = 0; e < E; e++) etaB[e] = std::pow(1.0f / I.dst[e], P.beta);  // eta^beta fijo
    const float Qn = P.qfac * (float)Lnn / (float)m;      // Q normalizado: si TODAS usan una arista, delta = qfac
    const float tmin = 0.01f, tmax = 100.f;

    std::vector<int> gbC(n, 0), gbE(n, -1);
    double gbL = 1e300;
    int stallCnt = 0, itDone = 0;

    printf("# n=%d m=%d K=%d alpha=%.2f beta=%.2f rho=%.2f two=%d alpha2=%.2f hilos=%d semilla=%llu\n",
           n, m, K, P.alpha, P.beta, P.rho, P.two, P.alpha2, nth, (unsigned long long)P.seed);
    printf("# preparacion (puntos+rejilla+KNN): %.3f s | L_nn=%.4f\n", secs(t0, t1), Lnn);
    printf("# iter  mejor_iter  mejor_global  media_hormigas  t_iter(s)  t_total(s)\n");

    auto tLoop = Clock::now();
    for (int it = 0; it < P.iters; it++) {
        auto ti = Clock::now();
        // pesos w = tau^a * tau2^a2 * eta^b (constantes durante la iteracion)
#pragma omp parallel for schedule(static)
        for (long e = 0; e < (long)E; e++) {
            float v = (P.alpha == 1.0f) ? tau[e] : std::pow(tau[e], P.alpha);
            if (P.two) v *= std::pow(tau2[e], P.alpha2);
            w[e] = v * etaB[e];
        }
        std::fill(delta.begin(), delta.end(), 0.f);
        for (auto& T : TS) T.bestL = 1e300;
        double sumL = 0;
        long antsRun = 0;
        auto tIterStart = Clock::now();
#pragma omp parallel reduction(+ : sumL) reduction(+ : antsRun)
        {
            ThreadState& T = TS[omp_get_thread_num()];
#pragma omp for schedule(dynamic, 1)
            for (int a = 0; a < m; a++) {
                // --tiempo_max: presupuesto por iteracion. Al agotarse, las hormigas que ya
                // estaban en curso terminan normalmente (no se interrumpen a medio tour); las
                // que aun no arrancaban simplemente no se construyen, y la iteracion se cierra
                // (evaporacion + deposito) con las que si corrieron.
                if (secs(tIterStart, Clock::now()) >= P.tiempoMaxIter) continue;
                int start = (int)(T.rng.next() % (u64)n);
                double L = buildTour(I, T, w.data(), start);
                antsRun++;
                sumL += L;
                if (L < T.bestL) { T.bestL = L; T.bestC = T.tourC; T.bestE = T.tourE; }
                // deposito Q/L_k sobre las aristas usadas (en ambos sentidos, TSP simetrico)
                float dep = Qn / (float)L;
                for (int s = 0; s < n; s++) {
                    int e = T.tourE[s];
                    if (e < 0) continue;
                    atomicAdd(delta[e], dep);
                    int i = e / K, j = I.nbr[e];
                    const size_t bj = (size_t)j * K;
                    for (int k = 0; k < K; k++) if (I.nbr[bj + k] == i) { atomicAdd(delta[bj + k], dep); break; }
                }
            }
        }
        // mejor de la iteracion / global
        double itBest = 1e300; int bt = -1;
        for (int t = 0; t < nth; t++) if (TS[t].bestL < itBest) { itBest = TS[t].bestL; bt = t; }
        bool improved = false;
        if (itBest < gbL) { gbL = itBest; gbC = TS[bt].bestC; gbE = TS[bt].bestE; improved = true; }
        stallCnt = improved ? 0 : stallCnt + 1;

        // evaporacion + deposito (capa 1)
        const float keep = 1.0f - P.rho;
#pragma omp parallel for schedule(static)
        for (long e = 0; e < (long)E; e++) tau[e] = std::min(tmax, std::max(tmin, keep * tau[e] + delta[e]));
        // capa 2 (elite): solo el mejor tour global refuerza
        if (P.two) {
            std::fill(delta.begin(), delta.end(), 0.f);
            float dep = P.qfac * (float)(Lnn / gbL);
            for (int s = 0; s < n; s++) {
                int e = gbE[s]; if (e < 0) continue;
                delta[e] += dep;
                int i = e / K, j = I.nbr[e]; const size_t bj = (size_t)j * K;
                for (int k = 0; k < K; k++) if (I.nbr[bj + k] == i) { delta[bj + k] += dep; break; }
            }
#pragma omp parallel for schedule(static)
            for (long e = 0; e < (long)E; e++) tau2[e] = std::min(tmax, std::max(tmin, keep * tau2[e] + delta[e]));
        }
        itDone = it + 1;
        double dt = secs(ti, Clock::now()), tot = secs(tLoop, Clock::now());
        printf("%5d  %10.4f  %12.4f  %14.4f  %9.3f  %10.3f\n", it + 1, itBest, gbL,
               sumL / (double)std::max(1L, antsRun), dt, tot);
        if (antsRun < m)
            printf("# aviso: --tiempo_max=%.3fs agotado en la iteracion %d; se completaron %ld/%d hormigas\n",
                   P.tiempoMaxIter, it + 1, antsRun, m);
        fflush(stdout);
        if (tot >= P.timeBudget || stallCnt >= P.stall) break;
    }
    auto t2 = Clock::now();

    // verificacion del mejor tour (permutacion valida + longitud recalculada en double)
    std::vector<char> seen(n, 0); bool ok = true; double Lchk = 0;
    for (int s = 0; s < n; s++) {
        int c = gbC[s]; if (c < 0 || c >= n || seen[c]) { ok = false; break; }
        seen[c] = 1;
        int d = gbC[(s + 1) % n];
        double dx = (double)I.x[c] - I.x[d], dy = (double)I.y[c] - I.y[d];
        Lchk += std::sqrt(dx * dx + dy * dy);
    }
    double rss = peakRssMB();
    double denseGB = 2.0 * (double)n * n * 4 / 1e9;   // matriz D + matriz T (float) si fuera densa
    printf("# ---- resumen ----\n");
    printf("n=%d m=%d iters=%d tour_valido=%s L_mejor=%.5f (verificado %.5f) L_nn=%.5f mejora_vs_nn=%.2f%%\n",
           n, m, itDone, ok ? "SI" : "NO", gbL, Lchk, Lnn, 100.0 * (Lnn - gbL) / Lnn);
    if (n >= 1000 && P.inputFile.empty()) {
        // BHH asume puntos uniformes en el cuadrado unidad; no aplica a instancias
        // cargadas con --input (TSPLIB u otras), que no son necesariamente uniformes.
        double est = 0.7124 * std::sqrt((double)n) * (1.0 + 0.33 / std::sqrt((double)n) * 1.0);
        printf("aprox_optimo(BHH)=%.3f  L_mejor/aprox=%.3f\n", est, gbL / est);
    }
    if (P.exact && n <= 20) {
        double opt = heldKarp(I);
        printf("optimo_exacto(Held-Karp)=%.5f  gap=%.3f%%\n", opt, 100.0 * (gbL - opt) / opt);
    }
    if (!P.inputFile.empty()) {
        // factor de escala guardado al normalizar --input a [0,1]^2 (ver buildInstance)
        printf("unidades_originales: factor_escala=%.6f L_mejor=%.5f L_nn=%.5f\n",
               I.scale, gbL * I.scale, Lnn * I.scale);
    }
    printf("tiempo: preparacion=%.3f s  ACO=%.3f s  total=%.3f s  (%.4f s/iter)\n",
           secs(t0, t1), secs(tLoop, t2), secs(t0, t2), secs(tLoop, t2) / std::max(1, itDone));
    printf("memoria: pico RSS=%.1f MB (tras KNN %.1f MB) | matrices densas D+T serian %.3f GB\n", rss, rssAfterBuild, denseGB);
    if (!P.tourOut.empty()) {
        FILE* f = fopen(P.tourOut.c_str(), "w");
        for (int s = 0; s < n; s++) fprintf(f, "%d %.6f %.6f\n", gbC[s], I.x[gbC[s]], I.y[gbC[s]]);
        fclose(f);
    }
    printf("CSV,%d,%d,%d,%d,%d,%.6f,%.6f,%.3f,%.3f,%.1f\n", n, m, K, P.two, itDone, gbL, Lnn,
           secs(t0, t1), secs(tLoop, t2), rss);
    return ok ? 0 : 2;
}
