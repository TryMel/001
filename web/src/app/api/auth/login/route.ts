import { NextRequest, NextResponse } from "next/server";
import {
  backendUrl,
  isSameOrigin,
  readJson,
  setTokenCookies,
} from "@/lib/server-api";

export async function POST(request: NextRequest) {
  if (!isSameOrigin(request)) {
    return NextResponse.json({ detail: "Origine de requête non autorisée." }, { status: 403 });
  }

  const credentials = await request.json().catch(() => null);
  if (
    !credentials ||
    typeof credentials.email !== "string" ||
    typeof credentials.password !== "string"
  ) {
    return NextResponse.json({ detail: "Adresse e-mail ou mot de passe invalide." }, { status: 400 });
  }

  try {
    const upstream = await fetch(backendUrl("api/v2/comptes/connexion/"), {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({
        email: credentials.email,
        password: credentials.password,
      }),
      cache: "no-store",
      redirect: "manual",
    });
    const data = await readJson(upstream);
    if (!upstream.ok) {
      return NextResponse.json(
        { detail: data?.detail ?? "Connexion impossible. Vérifiez vos identifiants." },
        { status: upstream.status, headers: { "Cache-Control": "no-store" } },
      );
    }
    if (
      typeof data?.access !== "string" ||
      typeof data?.refresh !== "string" ||
      !data.utilisateur
    ) {
      return NextResponse.json({ detail: "Réponse d’authentification invalide." }, { status: 502 });
    }

    const response = NextResponse.json(
      { user: data.utilisateur },
      { headers: { "Cache-Control": "no-store" } },
    );
    setTokenCookies(response, {
      access: data.access,
      refresh: data.refresh,
    });
    return response;
  } catch {
    return NextResponse.json(
      { detail: "Le service Akasha est momentanément indisponible." },
      { status: 502 },
    );
  }
}
