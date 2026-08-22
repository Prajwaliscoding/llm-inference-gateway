import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '15s', target: 1 },
    { duration: '30s', target: 1 },
    { duration: '15s', target: 0 },
  ],
};

const API_KEY = __ENV.API_KEY;
const BASE_URL = 'https://gateway.prajwalkhatiwada.com';

export default function () {
  const uniqueMsg = `What is ${Math.floor(Math.random() * 1000000)} + 1?`;

  const payload = JSON.stringify({
    model: 'gpt-4o-mini',
    messages: [{ role: 'user', content: uniqueMsg }],
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${API_KEY}`,
    },
  };

  const res = http.post(`${BASE_URL}/v1/chat/completions`, payload, params);

  check(res, {
    'status is 200': (r) => r.status === 200,
  });

  sleep(1);
}