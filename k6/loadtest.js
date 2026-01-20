import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    // 1. Browsing Normal (Baseline)
    normal_browsing: {
      executor: 'constant-vus',
      vus: 50,
      duration: '10s', // Kita pendekin biar cepet demo-nya
      exec: 'browsing',
    },

    // 2. Flash Sale Spike (Database Bottleneck)
    flash_sale_spike: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '5s', target: 200 },
        { duration: '10s', target: 500 }, // Database bakal kewalahan disini
        { duration: '5s', target: 0 },
      ],
      startTime: '10s', // Jalan setelah browsing selesai
      exec: 'war_ticket_v1',
    },

    // 3. SKENARIO BARU: BACKEND CPU BOTTLENECK (CPU Stress)
    // Ini menyerang endpoint validasi berat
    cpu_stress_test: {
      executor: 'constant-vus',
      vus: 50, // Cuma 50 user, tapi karena requestnya berat, CPU bakal 100%
      duration: '15s',
      startTime: '30s', // Jalan setelah Spike selesai
      exec: 'validate_heavy',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<2000'],
  },
};

const BASE_URL = 'http://host.docker.internal:8000';

// FUNGSI 1: Browsing
export function browsing() {
  http.get(`${BASE_URL}/matches`);
  sleep(1);
}

// FUNGSI 2: War Tiket (DB Heavy)
export function war_ticket_v1() {
  http.post(`${BASE_URL}/buy/v1/5`);
  sleep(0.1);
}

// FUNGSI 3: Validasi Berat (CPU Heavy)
export function validate_heavy() {
  // Nembak endpoint penghancur CPU
  const res = http.get(`${BASE_URL}/validate-ticket/999`);
  
  check(res, { 
    'status 200': (r) => r.status === 200 
  });
  // Gak pake sleep, biar CPU disiksa terus menerus
}