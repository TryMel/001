"use client";

import Link from "next/link";
import { useState } from "react";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/components/auth-provider";
import type { Utilisateur } from "@/lib/types";

const nomsRoles: Record<string, string> = {
  professionnel: "Professionnel",
  client: "Client",
  candidat: "Candidat",
  recruteur: "Recruteur",
  etudiant: "Étudiant",
  organisation: "Organisation",
  etablissement: "Établissement",
};

export function AppHeader() {
  const { user, loading, setUser, signOut } = useAuth();
  const [roleError, setRoleError] = useState("");
  const roles = user?.roles_professionnels ?? [];
  const isCandidate = roles.some((role) => ["candidat", "etudiant"].includes(role));
  const canManageProfile = roles.some((role) => ["professionnel", "candidat", "etudiant"].includes(role));
  const isRecruiter = roles.some((role) => ["recruteur", "organisation"].includes(role));

  async function changeRole(role_actif: string) {
    setRoleError("");
    try {
      const updated = await apiFetch<Utilisateur>("comptes/moi/role-actif/", {
        method: "PATCH",
        body: JSON.stringify({ role_actif }),
      });
      setUser(updated);
    } catch (error) {
      setRoleError(error instanceof Error ? error.message : "Espace indisponible.");
    }
  }

  return (
    <header className="site-header">
      <div className="header-inner">
        <Link aria-label="Akasha, accueil" className="brand" href="/">
          <span aria-hidden="true" className="brand-mark">A</span>
          <span>AKASHA</span>
        </Link>
        <nav aria-label="Navigation principale" className="main-nav">
          <Link href="/opportunites">Opportunités</Link>
          {isCandidate && <Link href="/espace/candidatures">Mes candidatures</Link>}
          {canManageProfile && <Link href="/espace/profil">Mon profil</Link>}
          {isRecruiter && <Link href="/espace/recruteur">Espace recruteur</Link>}
          {user && !user.onboarding_termine && <Link href="/bienvenue">Configurer mon espace</Link>}
        </nav>
        <div className="header-actions">
          {loading ? (
            <span aria-label="Chargement du compte" className="field-hint">…</span>
          ) : user ? (
            <>
              {roles.length > 1 && (
                <label className="field-hint">
                  <span className="sr-only">Espace actif</span>
                  <select
                    aria-label="Espace actif"
                    className="role-picker"
                    onChange={(event) => void changeRole(event.target.value)}
                    value={user.role_actif}
                  >
                    {roles.map((role) => (
                      <option key={role} value={role}>
                        {nomsRoles[role] ?? role}
                      </option>
                    ))}
                  </select>
                </label>
              )}
              <button className="button button-secondary" onClick={() => void signOut()} type="button">
                Déconnexion
              </button>
            </>
          ) : (
            <>
              <Link className="text-link" href="/connexion">Connexion</Link>
              <Link className="button" href="/inscription">Créer un compte</Link>
            </>
          )}
        </div>
      </div>
      {roleError && <p className="field-hint" role="status">{roleError}</p>}
    </header>
  );
}
