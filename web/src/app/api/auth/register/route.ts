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

  const account = await request.json().catch(() => null);
  if (!account || typeof account !== "object") {
    return NextResponse.json({ detail: "Vérifiez les informations saisies." }, { status: 400 });
  }
  const form = account as Record<string, unknown>;

  try {
    const upstream = await fetch(backendUrl("api/v2/comptes/inscription/"), {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({
        first_name: form.first_name,
        last_name: form.last_name,
        email: form.email,
        username: form.email,
        password: form.password,
        conditions_acceptees: form.conditions_acceptees,
      }),
      cache: "no-store",
      redirect: "manual",
    });
    const data = await readJson(upstream);
    if (!upstream.ok) {
      return NextResponse.json(
        { detail: data?.detail ?? "Création du compte impossible.", errors: data?.erreurs ?? data },
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
      { status: 201, headers: { "Cache-Control": "no-store" } },
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
