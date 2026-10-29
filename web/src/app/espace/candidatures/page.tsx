"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/components/auth-provider";
import { ApiError, apiFetch, listFrom } from "@/lib/api-client";
import type { Candidature, Opportunite, Page } from "@/lib/types";

const statuts: Record<string, string> = {
  envoyee: "Envoyée",
  en_cours: "En cours",
  retenue: "Présélectionnée",
  entretien: "Entretien",
  offre: "Offre reçue",
  acceptee: "Acceptée",
  refusee: "Refusée",
  retiree: "Retirée",
};

function isCandidate(roles: string[]) {
  return roles.some((role) => ["candidat", "etudiant"].includes(role));
}

export default function CandidaturesPage() {
  const { user, loading: authLoading } = useAuth();
  const [applications, setApplications] = useState<Candidature[]>([]);
  const [opportunities, setOpportunities] = useState<Map<number, Opportunite>>(new Map());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [actionError, setActionError] = useState("");
  const [busyApplication, setBusyApplication] = useState<number | null>(null);

  const load = useCallback(async () => {
    if (!user || !isCandidate(user.roles_professionnels)) return;
    setError("");
    try {
      const [applicationPayload, opportunityPayload] = await Promise.all([
        apiFetch<Page<Candidature> | Candidature[]>("opportunites/candidatures/"),
        apiFetch<Page<Opportunite> | Opportunite[]>("opportunites/?statut=publiee"),
      ]);
      setApplications(listFrom(applicationPayload));
      setOpportunities(new Map(listFrom(opportunityPayload).map((item) => [item.id, item])));
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : "Impossible de charger vos candidatures.");
    } finally {
      setLoading(false);
    }
  }, [user]);

  async function retirer(application: Candidature) {
    if (!window.confirm("Retirer définitivement cette candidature ?")) return;
    setBusyApplication(application.id);
    setActionError("");
    setNotice("");
    try {
      const updated = await apiFetch<Candidature>(
        `opportunites/candidatures/${application.id}/retirer/`,
        { method: "POST", body: JSON.stringify({}) },
      );
      setApplications((current) =>
        current.map((item) => item.id === updated.id ? updated : item),
      );
      setNotice("Votre candidature a été retirée.");
    } catch (reason) {
      setActionError(reason instanceof Error ? reason.message : "Retrait impossible.");
    } finally {
      setBusyApplication(null);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => { void load(); }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  if (authLoading) return <main className="container"><p className="loading">Chargement de votre espace…</p></main>;
  if (!user) {
    return (
      <main className="container">
        <section className="empty-state">
          <h1>Connectez-vous pour suivre vos candidatures.</h1>
          <p>Votre suivi reste privé et lié à votre compte.</p>
          <Link className="button" href="/connexion">Se connecter</Link>
        </section>
      </main>
    );
  }
  if (!isCandidate(user.roles_professionnels)) {
    return (
      <main className="container">
        <section className="notice">
          <h1>Un espace candidat est nécessaire.</h1>
          <p>Les candidatures sont réservées aux comptes candidat et étudiant.</p>
          <Link className="button" href="/bienvenue">Configurer mes espaces</Link>
        </section>
      </main>
    );
  }

  return (
    <main className="container">
      <header className="page-heading">
        <p className="eyebrow" style={{ color: "var(--primary)" }}>Votre parcours</p>
        <h1>Mes candidatures</h1>
        <p>Retrouvez les dossiers envoyés et leur état actuel.</p>
      </header>
      {loading && <p aria-live="polite" className="loading"><span className="spinner" />Chargement de vos candidatures…</p>}
      {notice && <p aria-live="polite" className="alert success" role="status">{notice}</p>}
      {actionError && <p role="alert" className="alert">{actionError}</p>}
      {!loading && error && (
        <section className="empty-state" role="alert">
          <h2>Le suivi est indisponible.</h2>
          <p>{error}</p>
          <button className="button button-secondary" onClick={() => { setLoading(true); setError(""); void load(); }} type="button">Réessayer</button>
        </section>
      )}
      {!loading && !error && applications.length === 0 && (
        <section className="empty-state">
          <h2>Pas encore de candidature envoyée.</h2>
          <p>Découvrez les offres publiées et postulez à celles qui vous correspondent.</p>
          <Link className="button" href="/opportunites">Découvrir les opportunités</Link>
        </section>
      )}
      {!loading && !error && applications.length > 0 && (
        <div className="stack">
          {applications.map((application) => {
            const opportunity = opportunities.get(application.opportunite);
            return (
              <article className="card" key={application.id}>
                <div className="page-heading-row">
                  <div>
                    <h2>
                      {opportunity ? (
                        <Link className="text-link" href={`/opportunites/${opportunity.id}`}>{opportunity.titre}</Link>
                      ) : `Opportunité #${application.opportunite}`}
                    </h2>
                    <p>{opportunity?.organisation_nom || opportunity?.ville || "Candidature Akasha"}</p>
                  </div>
                  <span className={`badge ${["acceptee", "offre"].includes(application.statut) ? "badge-success" : "badge-muted"}`}>
                    {statuts[application.statut] ?? application.statut}
                  </span>
                </div>
                <p className="field-hint">Envoyée le {new Date(application.cree_le).toLocaleDateString("fr-FR")}</p>
                {application.historique.length > 0 && (
                  <div aria-label="Historique du dossier" className="meta-row" style={{ marginTop: 10 }}>
                    {application.historique.map((step, index) => (
                      <span key={`${step.nouveau_statut}-${index}`}>
                        {statuts[step.nouveau_statut] ?? step.nouveau_statut}
                        {index < application.historique.length - 1 ? " ·" : ""}
                      </span>
                    ))}
                  </div>
                )}
                {!["acceptee", "refusee", "retiree"].includes(application.statut) && (
                  <button
                    className="button button-secondary"
                    disabled={busyApplication === application.id}
                    onClick={() => void retirer(application)}
                    type="button"
                  >
                    {busyApplication === application.id ? "Retrait…" : "Retirer ma candidature"}
                  </button>
                )}
              </article>
            );
          })}
        </div>
      )}
    </main>
  );
}
