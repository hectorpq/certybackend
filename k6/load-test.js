import http from 'k6/http';
import { sleep, check } from 'k6';

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

export default function () {
  // Prueba 1: Listar eventos (lectura común)
  let eventsRes = http.get(`${BASE_URL}/events/`, {
    headers: { 'Content-Type': 'application/json' },
  });

  check(eventsRes, {
    'Events list status 200/401': (r) => r.status === 200 || r.status === 401,
    'Events response time': (r) => r.timings.duration < 2000,
  });

  sleep(0.5);

  // Prueba 2: Listar certificados (lectura común)
  let certificatesRes = http.get(`${BASE_URL}/certificates/`, {
    headers: { 'Content-Type': 'application/json' },
  });

  check(certificatesRes, {
    'Certificates list status 200/401': (r) => r.status === 200 || r.status === 401,
  });

  sleep(0.5);

  // Prueba 3: Listar participantes
  let participantsRes = http.get(`${BASE_URL}/participants/`, {
    headers: { 'Content-Type': 'application/json' },
  });

  check(participantsRes, {
    'Participants list status 200/401': (r) => r.status === 200 || r.status === 401,
  });

  sleep(0.5);

  // Prueba 4: Listar instructores
  let instructorsRes = http.get(`${BASE_URL}/instructors/`, {
    headers: { 'Content-Type': 'application/json' },
  });

  check(instructorsRes, {
    'Instructors list status 200/401': (r) => r.status === 200 || r.status === 401,
  });

  sleep(1);
}