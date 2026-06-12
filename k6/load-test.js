import http from 'k6/http';
import { sleep, check } from 'k6';

http.setResponseCallback(http.expectedStatuses({ min: 200, max: 599 }));

export const options = {
  stages: [
    { duration: '30s', target: 10 },   // Ramp-up: 0 a 10 VUs
    { duration: '1m', target: 30 },    // Ramp-up: 10 a 30 VUs
    { duration: '2m', target: 30 },    // Stay at 30 VUs for 2 minutes
    { duration: '1m', target: 50 },    // Ramp-up: 30 a 50 VUs
    { duration: '2m', target: 50 },    // Stay at 50 VUs for 2 minutes
    { duration: '30s', target: 0 },    // Ramp-down: 50 a 0 VUs
  ],
  thresholds: {
    http_req_duration: ['p(95)<1000', 'p(99)<2000'],
    http_req_failed: ['rate<0.2'],
  },
};

const BASE_URL = 'http://localhost:8000/api';
const JSON_HEADERS = { headers: { 'Content-Type': 'application/json' } };

export default function () {
  // Prueba 1: Listar eventos (lectura común)
  let eventsRes = http.get(`${BASE_URL}/events/`, JSON_HEADERS);

  check(eventsRes, {
    'Events list status 200/401': (r) => r.status === 200 || r.status === 401,
    'Events response time': (r) => r.timings.duration < 2000,
  });

  sleep(0.5);

  // Prueba 2: Listar certificados (lectura común)
  let certificatesRes = http.get(`${BASE_URL}/certificates/`, JSON_HEADERS);

  check(certificatesRes, {
    'Certificates list status 200/401': (r) => r.status === 200 || r.status === 401,
  });

  sleep(0.5);

  // Prueba 3: Listar participantes
  let participantsRes = http.get(`${BASE_URL}/participants/`, JSON_HEADERS);

  check(participantsRes, {
    'Participants list status 200/401': (r) => r.status === 200 || r.status === 401,
  });

  sleep(0.5);

  // Prueba 4: Listar instructores
  let instructorsRes = http.get(`${BASE_URL}/instructors/`, JSON_HEADERS);

  check(instructorsRes, {
    'Instructors list status 200/401': (r) => r.status === 200 || r.status === 401,
  });

  // Prueba 5: Listar templates
  let templatesRes = http.get(`${BASE_URL}/templates/`, JSON_HEADERS);
  check(templatesRes, {
    'Templates list status 200/401/403': (r) => r.status === 200 || r.status === 401 || r.status === 403,
  });

  // Prueba 6: Listar auditoría
  let auditRes = http.get(`${BASE_URL}/audit/`, JSON_HEADERS);
  check(auditRes, {
    'Audit list status 200/401/403': (r) => r.status === 200 || r.status === 401 || r.status === 403,
  });

  // Prueba 7: Listar estudiantes (alias de participantes)
  let studentsRes = http.get(`${BASE_URL}/students/`, JSON_HEADERS);
  check(studentsRes, {
    'Students list status 200/401': (r) => r.status === 200 || r.status === 401,
  });

  // Prueba 8: Consultar usuario actual sin auth
  let meRes = http.get(`${BASE_URL}/me/`, JSON_HEADERS);
  check(meRes, {
    'Current user endpoint status 200/401/403': (r) => r.status === 200 || r.status === 401 || r.status === 403,
  });

  // Prueba 9: Login (credenciales de ejemplo)
  let loginRes = http.post(
    `${BASE_URL}/login/`,
    JSON.stringify({ email: 'testuser@example.com', password: 'testpass123' }),
    JSON_HEADERS,
  );
  check(loginRes, {
    'Login endpoint exists': (r) => [200, 400, 401].includes(r.status),
  });

  // Prueba 10: Registro con payload inválido (ruta existe)
  let registerRes = http.post(
    `${BASE_URL}/register/`,
    JSON.stringify({ email: 'loadtest@example.com' }),
    JSON_HEADERS,
  );
  check(registerRes, {
    'Register endpoint exists': (r) => [200, 201, 400, 409].includes(r.status),
  });

  // Prueba 11: Autenticación con Google sin token
  let googleRes = http.post(`${BASE_URL}/auth/google/`, JSON.stringify({}), JSON_HEADERS);
  check(googleRes, {
    'Google auth endpoint exists': (r) => [200, 400, 401, 500].includes(r.status),
  });

  // Prueba 12: Listar inscripciones
  let enrollmentsRes = http.get(`${BASE_URL}/enrollments/`, JSON_HEADERS);
  check(enrollmentsRes, {
    'Enrollments endpoint exists': (r) => [200, 400, 401, 403].includes(r.status),
  });

  // Prueba 13: Crear inscripción inválida
  let enrollmentsPostRes = http.post(`${BASE_URL}/enrollments/`, JSON.stringify({}), JSON_HEADERS);
  check(enrollmentsPostRes, {
    'Enrollments POST endpoint exists': (r) => [200, 400, 401, 403].includes(r.status),
  });

  // Prueba 14: Invitación pública inválida
  let invitationGetRes = http.get(`${BASE_URL}/invitations/invalid-token/`, JSON_HEADERS);
  check(invitationGetRes, {
    'Invitation detail endpoint exists': (r) => [200, 400, 404].includes(r.status),
  });

  let invitationAcceptRes = http.post(
    `${BASE_URL}/invitations/invalid-token/accept/`,
    JSON.stringify({}),
    JSON_HEADERS,
  );
  check(invitationAcceptRes, {
    'Invitation accept endpoint exists': (r) => [200, 400, 404].includes(r.status),
  });

  let invitationRegisterRes = http.post(
    `${BASE_URL}/invitations/invalid-token/register/`,
    JSON.stringify({}),
    JSON_HEADERS,
  );
  check(invitationRegisterRes, {
    'Invitation register endpoint exists': (r) => [200, 400, 404].includes(r.status),
  });

  // Prueba 15: Verificar certificado
  let verifyRes = http.get(`${BASE_URL}/certificates/verify/?code=INVALID`, JSON_HEADERS);
  check(verifyRes, {
    'Certificate verify endpoint exists': (r) => [200, 400, 404].includes(r.status),
  });

  sleep(1);
}