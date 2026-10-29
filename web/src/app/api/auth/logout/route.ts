import { NextRequest, NextResponse } from "next/server";
import {
  REFRESH_COOKIE,
  backendUrl,
  clearTokenCookies,
  isSameOrigin,
} from "@/lib/server-api";

export async function POST(request: NextRequest) {
  if (!isSameOrigin(request)) {
    return NextResponse.json({ detail: "Origine de requête non autorisée." }, { status: 403 });
  }

  const refresh = request.cookies.get(REFRESH_COOKIE)?.value;
  if (refresh) {
    try {
      await fetch(backendUrl("api/v2/comptes/deconnexion/"), {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ refresh }),
        cache: "no-store",
        redirect: "manual",
      });
    } catch {
      // The local session is still cleared if the API is unreachable.
    }
  }
  const response = new NextResponse(null, { status: 204 });
  clearTokenCookies(response);
  clearTokenCookies(response);
  return response;
}
