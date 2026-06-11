import http from 'k6/http';
import { check, sleep, group } from 'k6';

// ====================================================================
// CONFIGURACIÓN DE ESCENARIOS (K6)
// ====================================================================
// Para ejecutar un escenario específico desde la terminal usa:
// k6 run -e API_URL=http://127.0.0.1:8000 -e SCENARIO=smoke load_test.js
// ====================================================================

const BASE_URL = __ENV.API_URL || 'http://127.0.0.1:8000';
const SCENARIO_TYPE = __ENV.SCENARIO || 'smoke';

// Opciones de configuración dinámica según el escenario elegido
const scenariosConfig = {
    smoke: {
        executor: 'ramping-vus',
        startVUs: 0,
        stages: [
            { duration: '30s', target: 10 },
            { duration: '30s', target: 0 },
        ],
    },
    load: {
        executor: 'ramping-vus',
        startVUs: 0,
        stages: [
            { duration: '1m', target: 100 },
            { duration: '3m', target: 100 },
            { duration: '1m', target: 0 },
        ],
    },
    stress: {
        executor: 'ramping-vus',
        startVUs: 0,
        stages: [
            { duration: '2m', target: 500 },
            { duration: '2m', target: 1000 },
            { duration: '4m', target: 1000 },
            { duration: '2m', target: 0 },
        ],
    },
    spike: {
        executor: 'ramping-vus',
        startVUs: 0,
        stages: [
            { duration: '10s', target: 100 },
            { duration: '1m', target: 10000 }, // El pico brutal
            { duration: '10s', target: 100 },
            { duration: '40s', target: 0 },
        ],
    }
};

export const options = {
    scenarios: {
        [SCENARIO_TYPE]: scenariosConfig[SCENARIO_TYPE]
    },
    thresholds: {
        http_req_duration: ['p(95)<200', 'p(99)<500'], // 95% de las requests deben durar < 200ms
        http_req_failed: ['rate<0.01'], // Tasa de error < 1%
    },
};

// ====================================================================
// FLUJO DE USUARIO (User Journey)
// ====================================================================

export default function () {
    let headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    };

    // 1. Navegación Anónima (Lectura / Búsqueda)
    group('1. Lectura y Búsqueda Anónima', function () {
        // Cargar el Home
        let resHome = http.get(`${BASE_URL}/api/home`, { headers });
        check(resHome, { 'Home carga 200': (r) => r.status === 200 });
        sleep(1);

        // Buscar en Catálogo
        let resCatalog = http.get(`${BASE_URL}/api/mangas?search=Naruto&page=1`, { headers });
        check(resCatalog, { 'Catálogo busca 200': (r) => r.status === 200 });
        sleep(2);
    });

    // 2. Autenticación (Login)
    let token = null;
    group('2. Inicio de Sesión', function () {
        // FastAPI OAuth2PasswordRequestForm requiere x-www-form-urlencoded
        let loginPayload = {
            username: 'testuser',
            password: 'TestPassword123!'
        };
        
        let loginHeaders = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        };
        
        let resLogin = http.post(`${BASE_URL}/api/auth/token`, loginPayload, { headers: loginHeaders });
        check(resLogin, { 'Login 200 o 401': (r) => r.status === 200 || r.status === 401 });
        
        if (resLogin.status === 200) {
            token = resLogin.json('access_token');
        }
        sleep(1);
    });

    // 3. Acciones Autenticadas (Si el login fue exitoso)
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
        
        group('3. Acciones de Usuario', function () {
            // Ver detalles de un manga (Manga ID = 1 para la prueba)
            let resManga = http.get(`${BASE_URL}/api/mangas/1`, { headers });
            check(resManga, { 'Ver Manga 200': (r) => r.status === 200 });
            sleep(1);

            // Agregar a Favoritos
            let favPayload = JSON.stringify({ manga_id: 1 });
            let resFav = http.post(`${BASE_URL}/api/favorites`, favPayload, { headers });
            check(resFav, { 'Favorito 201/200': (r) => r.status === 201 || r.status === 200 });
            sleep(1);

            // Calificar Manga
            let ratingPayload = JSON.stringify({ manga_id: 1, score: 5 });
            let resRate = http.post(`${BASE_URL}/api/ratings`, ratingPayload, { headers });
            check(resRate, { 'Rating 201/200': (r) => r.status === 201 || r.status === 200 });
            sleep(1);
        });
    }
}
