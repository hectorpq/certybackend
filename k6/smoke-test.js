import http from 'k6/http';
import { sleep, check } from 'k6';

http.setResponseCallback(http.expectedStatuses({ min: 200, max: 599 }));

export const options = {
  vus: 5,
  duration: '30s',
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.1'],
  },
};

const BASE_URL = 'http://localhost:8000/api';

// Credenciales de prueba
const testUser = {
  email: 'testuser@example.com',
  password: 'testpass123',
};

export default function () {
  // Prueba 1: GET Health check - Verificar que el servidor responde
  let healthRes = http.get(`${BASE_URL}/certificates/`, {
    headers: { 'Content-Type': 'application/json' },
  });

  check(healthRes, {
    'Health check status 200/401': (r) => r.status === 200 || r.status === 401,
  });

  // Prueba 2: GET Lista de eventos
  let eventsRes = http.get(`${BASE_URL}/events/`, {
    headers: { 'Content-Type': 'application/json' },
  });

  check(eventsRes, {
    'Events list status 200/401': (r) => r.status === 200 || r.status === 401,
    'Events response is JSON': (r) => r.headers['Content-Type'].includes('application/json'),
  });

  // Prueba 3: GET Lista de participantes
  let participantsRes = http.get(`${BASE_URL}/participants/`, {
    headers: { 'Content-Type': 'application/json' },
  });

  check(participantsRes, {
    'Participants list status 200/401': (r) => r.status === 200 || r.status === 401,
  });

  // Prueba 4: GET Lista de certificados
  let certificatesRes = http.get(`${BASE_URL}/certificates/`, {
    headers: { 'Content-Type': 'application/json' },
  });

  check(certificatesRes, {
    'Certificates list status 200/401': (r) => r.status === 200 || r.status === 401,
    'Certificates response time < 1s': (r) => r.timings.duration < 1000,
  });

  // Prueba 5: GET Lista de instructores
  let instructorsRes = http.get(`${BASE_URL}/instructors/`, {
    headers: { 'Content-Type': 'application/json' },
  });

  check(instructorsRes, {
    'Instructors list status 200/401': (r) => r.status === 200 || r.status === 401,
  });

  // Prueba 6: POST Login (opcional - comentado si el servidor no requiere)
  // let loginRes = http.post(`${BASE_URL}/login/`, JSON.stringify(testUser), {
  //   headers: { 'Content-Type': 'application/json' },
  // });

  // check(loginRes, {
  //   'Login status 200/400': (r) => r.status === 200 || r.status === 400,
  // });

  sleep(1);
}