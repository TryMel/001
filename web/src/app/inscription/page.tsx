"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/components/auth-provider";
import type { Utilisateur } from "@/lib/types";

export default function InscriptionPage() {
  const router = useRouter();
  const { setUser } = useAuth();
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    password: "",
    conditions_acceptees: false,
  });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  function update(field: keyof typeof form, value: string | boolean) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSaving(true);
    try {
      const response = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify(form),
      });
      const payload = (await response.json().catch(() => null)) as
        | { user: Utilisateur; detail?: string }
        | null;
      if (!response.ok || !payload?.user) {
        throw new Error(payload?.detail ?? "Création du compte impossible.");
      }
      setUser(payload.user);
      router.push("/bienvenue");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Création du compte impossible.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="container">
      <section aria-labelledby="signup-title" className="form-card">
        <p className="eyebrow" style={{ color: "var(--primary)" }}>Votre parcours commence ici</p>
        <h1 id="signup-title">Créer mon compte</h1>
        <p>Un compte personnel pour accéder aux espaces qui vous correspondent.</p>
        <form onSubmit={submit}>
          <div className="form-grid">
            <div className="field">
              <label htmlFor="first-name">Prénom</label>
              <input autoComplete="given-name" id="first-name" onChange={(event) => update("first_name", event.target.value)} required value={form.first_name} />
            </div>
            <div className="field">
              <label htmlFor="last-name">Nom</label>
              <input autoComplete="family-name" id="last-name" onChange={(event) => update("last_name", event.target.value)} required value={form.last_name} />
            </div>
          </div>
          <div className="field">
            <label htmlFor="signup-email">Adresse e-mail</label>
            <input autoComplete="email" id="signup-email" onChange={(event) => update("email", event.target.value)} required type="email" value={form.email} />
          </div>
          <div className="field">
            <label htmlFor="signup-password">Mot de passe</label>
            <input autoComplete="new-password" id="signup-password" minLength={8} onChange={(event) => update("password", event.target.value)} required type="password" value={form.password} />
            <span className="field-hint">Au moins 8 caractères.</span>
          </div>
          <label className="checkbox-row">
            <input checked={form.conditions_acceptees} onChange={(event) => update("conditions_acceptees", event.target.checked)} required type="checkbox" />
            <span>J’accepte les conditions d’utilisation d’Akasha.</span>
          </label>
          {error && <p className="alert" role="alert">{error}</p>}
          <button className="button" disabled={saving} type="submit">
            {saving ? "Création…" : "Créer mon compte"}
          </button>
        </form>
        <p style={{ marginBottom: 0, marginTop: 20 }}>
          Déjà inscrit·e ? <Link className="text-link" href="/connexion">Se connecter</Link>
        </p>
      </section>
    </main>
  );
}
