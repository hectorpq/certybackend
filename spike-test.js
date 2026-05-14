import http from 'k6/http';
import { check } from 'k6';

export const options = {
  stages: [
    { duration: '5s', target: 0 },
    { duration: '5s', target: 500 },
    { duration: '30s', target: 500 },
    { duration: '5s', target: 0 },
  ],
  thresholds: {
    'http_req_duration': ['p(99)<1000'],
    'http_req_failed': ['rate<0.1'],
  },
};

const TARGET_URL = 'https://test-api.example.com/endpoint';

export default function () {
  const res = http.get(TARGET_URL);
  check(res, { 'status is 200': (r) => r.status === 200 });
}
