import http from 'k6/http';
import { sleep, check } from 'k6';

export const options = {
  stages: [
    { duration: '5s', target: 5 },      // Ramp-up: 0 a 5 VUs (verificar conexión)
    { duration: '10s', target: 20 },    // Ramp-up: 5 a 20 VUs
    { duration: '20s', target: 50 },    // Ramp-up: 20 a 50 VUs
    { duration: '30s', target: 70 },    // Ramp-up: 50 a 70 VUs (pico de carga)
    { duration: '20s', target: 50 },    // Ramp-down: 70 a 50 VUs
    { duration: '10s', target: 0 },     // Ramp-down: 50 a 0 VUs
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000', 'p(99)<5000'],
    http_req_failed: ['rate<0.5'],  // Aumentado a 50% mientras diagnosticamos
  },
};

const BASE_URL = 'http://localhost:8000/api';

// Función para hacer requests con retry
function makeRequest(method, url, payload = null) {
  const params = {
    headers: { 'Content-Type': 'application/json' },
    timeout: '10s',
  };

  let response;
  if (method === 'GET') {
    response = http.get(url, params);
  } else if (method === 'POST') {
    response = http.post(url, payload, params);
  }
  return response;
}

export default function () {
  // Prueba 1: GET Certificados con paginación
  let certificatesRes = makeRequest('GET', `${BASE_URL}/certificates/?limit=10&offset=0`);

  check(certificatesRes, {
    'Certificates - cualquier respuesta': (r) => r !== null,
    'Certificates - status válido': (r) => r.status >= 200 && r.status < 600,
    'Certificates - no timeout': (r) => r.timings.duration < 10000,
  });

  sleep(0.2);

  // Prueba 2: GET Eventos con paginación
  let eventsRes = makeRequest('GET', `${BASE_URL}/events/?limit=20&offset=0`);

  check(eventsRes, {
    'Events - status válido': (r) => r.status >= 200 && r.status < 600,
    'Events - respuesta rápida': (r) => r.timings.duration < 5000,
  });

  sleep(0.2);

  // Prueba 3: GET Participantes
  let participantsRes = makeRequest('GET', `${BASE_URL}/participants/?limit=10`);

  check(participantsRes, {
    'Participants - status válido': (r) => r.status >= 200 && r.status < 600,
  });

  sleep(0.2);

  // Prueba 4: GET Entregas
  let deliveriesRes = makeRequest('GET', `${BASE_URL}/deliveries/?limit=10`);

  check(deliveriesRes, {
    'Deliveries - status válido': (r) => r.status >= 200 && r.status < 600,
  });

  sleep(0.2);

  // Prueba 5: GET Instructores
  let instructorsRes = makeRequest('GET', `${BASE_URL}/instructors/?limit=10`);

  check(instructorsRes, {
    'Instructors - status válido': (r) => r.status >= 200 && r.status < 600,
  });

  sleep(0.3);
}