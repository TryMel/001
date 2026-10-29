"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { apiFetch } from "@/lib/api-client";
import { destinationEspace } from "@/lib/espaces";
import { useAuth } from "@/components/auth-provider";
import type { Utilisateur } from "@/lib/types";

const espaces = [
  { role: "candidat", titre: "Candidat·e", texte: "Trouver un emploi et suivre mes candidatures." },
  { role: "etudiant", titre: "Étudiant·e", texte: "Découvrir stages et premières expériences." },
  { role: "recruteur", titre: "Recruteur·se", texte: "Publier des opportunités et traiter les candidatures." },
  { role: "organisation", titre: "Organisation", texte: "Créer et gérer l’espace de mon organisation." },
  { role: "professionnel", titre: "Professionnel·le", texte: "Présenter mon profil et mes compétences." },
  { role: "client", titre: "Client·e", texte: "Explorer les parcours de services Akasha." },
];

export default function BienvenuePage() {
  const router = useRouter();
  const { user, loading, setUser } = useAuth();
  const [selected, setSelected] = useState<string[]>([]);
  const [active, setActive] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  function toggle(role: string) {
    setSelected((current) => {
      const next = current.includes(role) ? current.filter((value) => value !== role) : [...current, role];
      if (!next.includes(active)) setActive(next[0] ?? "");
      else if (!active && next.length) setActive(next[0]);
      return next;
    });
  }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected.length || !active) {
      setError("Choisissez au moins un espace et votre espace de départ.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      const updated = await apiFetch<Utilisateur>("comptes/moi/onboarding/", {
        method: "POST",
        body: JSON.stringify({ roles_professionnels: selected, role_actif: active }),
      });
      setUser(updated);
      router.push(destinationEspace(updated));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Configuration impossible.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <main className="container"><p className="loading">Chargement de votre compte…</p></main>;
  if (!user) {
    return (
      <main className="container">
        <section className="empty-state">
          <h1>Connectez-vous pour choisir vos espaces.</h1>
          <p>Vous pourrez cumuler plusieurs parcours avec un seul compte.</p>
          <Link className="button" href="/connexion">Se connecter</Link>
        </section>
      </main>
    );
  }

  return (
    <main className="container">
      <section aria-labelledby="welcome-title" className="form-card">
        <p className="eyebrow" style={{ color: "var(--primary)" }}>Bienvenue sur Akasha</p>
        <h1 id="welcome-title">Quels sont vos objectifs&nbsp;?</h1>
        <p>Choisissez un ou plusieurs espaces. Vous pourrez les changer plus tard.</p>
        <form onSubmit={submit}>
          {espaces.map((espace) => (
            <label className="choice-row" key={espace.role}>
              <input checked={selected.includes(espace.role)} onChange={() => toggle(espace.role)} type="checkbox" />
              <span><strong>{espace.titre}</strong><br /><span className="field-hint">{espace.texte}</span></span>
            </label>
          ))}
          {selected.length > 0 && (
            <div className="field">
              <label htmlFor="role-actif">Espace à ouvrir en premier</label>
              <select id="role-actif" onChange={(event) => setActive(event.target.value)} value={active}>
                {selected.map((role) => (
                  <option key={role} value={role}>
                    {espaces.find((item) => item.role === role)?.titre ?? role}
                  </option>
                ))}
              </select>
            </div>
          )}
          {error && <p className="alert" role="alert">{error}</p>}
          <button className="button" disabled={saving || !selected.length} type="submit">
            {saving ? "Enregistrement…" : "Continuer"}
          </button>
        </form>
      </section>
    </main>
  );
}
