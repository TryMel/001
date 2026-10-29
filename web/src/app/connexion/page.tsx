"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/components/auth-provider";
import { destinationEspace } from "@/lib/espaces";
import type { Utilisateur } from "@/lib/types";

export default function ConnexionPage() {
  const router = useRouter();
  const { setUser } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSaving(true);
    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify({ email, password }),
      });
      const payload = (await response.json().catch(() => null)) as
        | { user: Utilisateur; detail?: string }
        | null;
      if (!response.ok || !payload?.user) {
        throw new Error(payload?.detail ?? "Connexion impossible.");
      }
      setUser(payload.user);
      router.push(destinationEspace(payload.user));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Connexion impossible.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="container">
      <section aria-labelledby="login-title" className="form-card">
        <p className="eyebrow" style={{ color: "var(--primary)" }}>Ravi·e de vous revoir</p>
        <h1 id="login-title">Connexion</h1>
        <p>Retrouvez votre profil, vos candidatures et vos espaces Akasha.</p>
        <form onSubmit={submit}>
          <div className="field">
            <label htmlFor="email">Adresse e-mail</label>
            <input
              autoComplete="email"
              id="email"
              onChange={(event) => setEmail(event.target.value)}
              required
              type="email"
              value={email}
            />
          </div>
          <div className="field">
            <label htmlFor="password">Mot de passe</label>
            <input
              autoComplete="current-password"
              id="password"
              onChange={(event) => setPassword(event.target.value)}
              required
              type="password"
              value={password}
            />
          </div>
          {error && <p className="alert" role="alert">{error}</p>}
          <button className="button" disabled={saving} type="submit">
            {saving ? "Connexion…" : "Se connecter"}
          </button>
        </form>
        <p style={{ marginBottom: 0, marginTop: 20 }}>
          Pas encore de compte ? <Link className="text-link" href="/inscription">Créer un compte</Link>
        </p>
      </section>
    </main>
  );
}
