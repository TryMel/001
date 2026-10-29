import http from "k6/http";
import { check, sleep } from "k6";

// Test progressif et borne : les volumes doivent etre valides avec l'equipe
// infrastructure avant toute execution contre un environnement partage.
const baseUrl = __ENV.TARGET_URL || "http://127.0.0.1:8000";
const maxVus = Number(__ENV.MAX_VUS || 25);

export const options = {
  scenarios: {
    consultation_publique: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "20s", target: Math.max(1, Math.floor(maxVus * 0.4)) },
        { duration: "40s", target: maxVus },
        { duration: "20s", target: 0 },
      ],
      gracefulRampDown: "10s",
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<800", "p(99)<1500"],
  },
};

const params = { headers: { Accept: "application/json" }, tags: { surface: "public-api" } };

export default function () {
  const responses = http.batch([
    ["GET", `${baseUrl}/api/opportunites/?page=1`, null, params],
    ["GET", `${baseUrl}/api/collaborations/services/?page=1`, null, params],
  ]);

  for (const response of responses) {
    check(response, {
      "reponse publique reussie": (r) => r.status === 200,
      "contenu JSON": (r) => (r.headers["Content-Type"] || "").includes("application/json"),
    });
  }
  sleep(1);
}
