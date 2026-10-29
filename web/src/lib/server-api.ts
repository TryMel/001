import { NextResponse, type NextRequest } from "next/server";

export const ACCESS_COOKIE = "akasha_access";
export const REFRESH_COOKIE = "akasha_refresh";

const ACCESS_MAX_AGE = 15 * 60;
const REFRESH_MAX_AGE = 14 * 24 * 60 * 60;
const API_COOKIE_PATH = "/api";

type Jetons = { access: string; refresh: string };

function cookieOptions(maxAge: number) {
  return {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax" as const,
    path: API_COOKIE_PATH,
    maxAge,
  };
}

export function setTokenCookies(response: NextResponse, tokens: Jetons) {
  response.cookies.set(ACCESS_COOKIE, tokens.access, cookieOptions(ACCESS_MAX_AGE));
  response.cookies.set(REFRESH_COOKIE, tokens.refresh, cookieOptions(REFRESH_MAX_AGE));
}

export function clearTokenCookies(response: NextResponse) {
  response.cookies.set(ACCESS_COOKIE, "", cookieOptions(0));
  response.cookies.set(REFRESH_COOKIE, "", cookieOptions(0));
}

export function isSameOrigin(request: NextRequest) {
  return request.headers.get("origin") === request.nextUrl.origin;
}

export function backendUrl(path: string) {
  const configuredOrigin =
    process.env.AKASHA_API_BASE_URL?.trim() ||
    (process.env.NODE_ENV === "development" ? "http://127.0.0.1:8000" : "");
  if (!configuredOrigin) throw new Error("AKASHA_API_BASE_URL n’est pas configurée.");

  const origin = new URL(configuredOrigin);
  if (
    !["http:", "https:"].includes(origin.protocol) ||
    origin.username ||
    origin.password ||
    origin.pathname !== "/" ||
    origin.search ||
    origin.hash
  ) {
    throw new Error("AKASHA_API_BASE_URL doit être une origine HTTP(S) sans identifiants.");
  }
  return new URL(path.replace(/^\/+/, ""), origin);
}

export async function readJson(response: Response) {
  return (await response.json().catch(() => null)) as Record<string, unknown> | null;
}

export async function obtenirJetons(
  refresh: string,
): Promise<Jetons | null> {
  try {
    const response = await fetch(backendUrl("api/v2/comptes/rafraichir/"), {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ refresh }),
      cache: "no-store",
      redirect: "manual",
    });
    if (!response.ok) return null;
    const data = await readJson(response);
    if (typeof data?.access !== "string" || typeof data?.refresh !== "string") {
      return null;
    }
    return { access: data.access, refresh: data.refresh };
  } catch {
    return null;
  }
}

function responseFromUpstream(response: Response) {
  const headers = new Headers({ "Cache-Control": "no-store" });
  const contentType = response.headers.get("content-type");
  if (contentType) headers.set("Content-Type", contentType);
  return response.text().then((body) =>
    new NextResponse(body || null, { status: response.status, headers }),
  );
}

export async function proxyApiRequest(
  request: NextRequest,
  apiPath: string,
) {
  if (!["GET", "HEAD"].includes(request.method) && !isSameOrigin(request)) {
    return NextResponse.json({ detail: "Origine de requête non autorisée." }, { status: 403 });
  }

  const access = request.cookies.get(ACCESS_COOKIE)?.value;
  const refresh = request.cookies.get(REFRESH_COOKIE)?.value;
  const body =
    request.method === "GET" || request.method === "HEAD"
      ? undefined
      : await request.arrayBuffer();
  const query = request.nextUrl.search;

  const send = (accessToken?: string) => {
    const headers = new Headers({ Accept: "application/json" });
    if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
    const contentType = request.headers.get("content-type");
    if (body?.byteLength && contentType) headers.set("Content-Type", contentType);
    return fetch(backendUrl(`api/${apiPath}${query}`), {
      method: request.method,
      headers,
      body: body?.byteLength ? body : undefined,
      cache: "no-store",
      redirect: "manual",
    });
  };

  let upstream: Response;
  try {
    upstream = await send(access);
  } catch {
    return NextResponse.json(
      { detail: "Le service Akasha est momentanément indisponible." },
      { status: 502 },
    );
  }

  let rotatedTokens: Jetons | null = null;
  if (upstream.status === 401 && refresh) {
    rotatedTokens = await obtenirJetons(refresh);
    if (rotatedTokens) {
      try {
        upstream = await send(rotatedTokens.access);
      } catch {
        return NextResponse.json(
          { detail: "Le service Akasha est momentanément indisponible." },
          { status: 502 },
        );
      }
    }
  }

  const response = await responseFromUpstream(upstream);
  if (rotatedTokens) {
    setTokenCookies(response, rotatedTokens);
  } else if (upstream.status === 401 && refresh) {
    clearTokenCookies(response);
  }
  return response;
}
