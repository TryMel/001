export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function messageFromPayload(payload: unknown): string {
  if (payload && typeof payload === "object") {
    const record = payload as Record<string, unknown>;
    const errors = record.erreurs ?? record.errors;
    if (errors && typeof errors === "object") {
      const firstError = Object.values(errors as Record<string, unknown>).find(
        (value) => Array.isArray(value) && typeof value[0] === "string",
      );
      if (Array.isArray(firstError)) return String(firstError[0]);
    }
    if (typeof record.detail === "string") return record.detail;
    if (typeof record.message === "string") return record.message;

    const firstField = Object.values(record).find(
      (value) => Array.isArray(value) && typeof value[0] === "string",
    );
    if (Array.isArray(firstField)) return String(firstField[0]);
  }
  return "Une erreur est survenue. Veuillez réessayer.";
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  const isFormData =
    typeof FormData !== "undefined" && init.body instanceof FormData;
  if (init.body && !isFormData && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  headers.set("Accept", "application/json");

  const response = await fetch(
    `/api/backend/v2/${path.replace(/^\/+/, "")}`,
    {
    ...init,
    headers,
    credentials: "same-origin",
    cache: "no-store",
    },
  );

  const payload = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(messageFromPayload(payload), response.status);
  }
  return payload as T;
}

export function listFrom<T>(payload: T[] | { results?: T[] } | null): T[] {
  if (Array.isArray(payload)) return payload;
  return payload?.results ?? [];
}

export function asJson(value: unknown): string {
  return JSON.stringify(value);
}
