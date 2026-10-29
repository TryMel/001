"use client";

import Link from "next/link";
import Image from "next/image";
import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/components/auth-provider";
import { ApiError, apiFetch, listFrom } from "@/lib/api-client";
import type { Candidature, Opportunite, Page } from "@/lib/types";

const statutLabels: Record<string, string> = {
  envoyee: "Envoyée",
  en_cours: "En cours",
  retenue: "Présélectionnée",
  entretien: "Entretien",
  offre: "Offre reçue",
  acceptee: "Acceptée",
  refusee: "Refusée",
  retiree: "Retirée",
};

export function OpportunityDetail({ id }: { id: string }) {
  const { user, loading: authLoading } = useAuth();
  const [opportunity, setOpportunity] = useState<Opportunite | null>(null);
  const [application, setApplication] = useState<Candidature | null>(null);
  const [message, setMessage] = useState("");
  const [consent, setConsent] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const load = useCallback(async () => {
    try {
      const result = await apiFetch<Opportunite>(`opportunites/${encodeURIComponent(id)}/`);
      setOpportunity(result);
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : "Impossible de charger cette offre.");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    const timer = window.setTimeout(() => { void load(); }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  useEffect(() => {
    if (!user || !user.roles_professionnels.some((role) => ["candidat", "etudiant"].includes(role))) {
      return;
    }
    let active = true;
    void apiFetch<Page<Candidature> | Candidature[]>("opportunites/candidatures/")
      .then((payload) => {
        const found = listFrom(payload).find((item) => item.opportunite === Number(id));
        if (active) setApplication(found ?? null);
      })
      .catch(() => {});
    return () => { active = false; };
  }, [id, user]);

  async function apply(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const created = await apiFetch<Candidature>("opportunites/candidatures/", {
        method: "POST",
        body: JSON.stringify({
          opportunite: Number(id),
          message,
          consentement_partage_profil: consent,
        }),
      });
      setApplication(created);
      setSuccess("Votre candidature a bien été envoyée.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Envoi de la candidature impossible.");
    } finally {
      setSaving(false);
    }
  }

  const hasCandidateRole = Boolean(
    user?.roles_professionnels.some((role) => ["candidat", "etudiant"].includes(role)),
  );
  const currentApplication =
    user && hasCandidateRole && application?.opportunite === Number(id) ? application : null;
  const isPublished = opportunity?.statut === "publiee";

  return (
    <main className="container">
      {loading && <p aria-live="polite" className="loading"><span className="spinner" />Chargement de l’opportunité…</p>}
      {!loading && error && !opportunity && (
        <section className="empty-state" role="alert">
          <h1>Cette opportunité n’est pas disponible.</h1>
          <p>{error}</p>
          <Link className="button button-secondary" href="/opportunites">Retour aux opportunités</Link>
        </section>
      )}
      {!loading && opportunity && (
        <>
          <Link className="text-link" href="/opportunites">← Toutes les opportunités</Link>
          <section className="panel" style={{ marginTop: 18 }}>
            <div className="meta-row" style={{ marginBottom: 12 }}>
              <span className="badge">{opportunity.type}</span>
              {opportunity.contrat && <span className="badge badge-muted">{opportunity.contrat.toUpperCase()}</span>}
            </div>
            <h1 style={{ fontSize: "clamp(2rem, 5vw, 3rem)", lineHeight: 1.15, margin: "0 0 8px" }}>{opportunity.titre}</h1>
            <p style={{ color: "var(--muted)", marginTop: 0 }}>
              {opportunity.organisation_nom || opportunity.createur_nom}
              {opportunity.ville ? ` · ${opportunity.ville}` : ""}
              {opportunity.pays ? ` · ${opportunity.pays}` : ""}
            </p>
            <div className="meta-row" style={{ marginBlock: 20 }}>
              {opportunity.budget_minimum != null && (
                <span>
                  Budget : {opportunity.budget_minimum.toLocaleString("fr-FR")}
                  {opportunity.budget_maximum != null && ` – ${opportunity.budget_maximum.toLocaleString("fr-FR")}`}
                  {" "}{opportunity.devise}
                </span>
              )}
              {opportunity.date_limite_candidature && (
                <span>Date limite : {new Date(opportunity.date_limite_candidature).toLocaleDateString("fr-FR")}</span>
              )}
            </div>
            <div style={{ borderTop: "1px solid var(--border)", paddingTop: 18 }}>
              <h2>Description</h2>
              <p style={{ whiteSpace: "pre-wrap" }}>{opportunity.description}</p>
              {opportunity.niveau_etudes && <p><strong>Niveau d’études :</strong> {opportunity.niveau_etudes}</p>}
              {opportunity.duree && <p><strong>Durée :</strong> {opportunity.duree}</p>}
              {opportunity.metier_nom && <p><strong>Métier :</strong> {opportunity.metier_nom}</p>}
              {opportunity.competences_detail.length > 0 && (
                <div className="job-skills">
                  <strong>Compétences recherchées</strong>
                  <div className="meta-row">
                    {opportunity.competences_detail.map((competence) => (
                      <span className="badge badge-muted" key={competence.id}>{competence.nom}</span>
                    ))}
                  </div>
                </div>
              )}
              {opportunity.images_url.map((url, index) => (
                <Image
                  alt={`Illustration ${index + 1} de ${opportunity.titre}`}
                  className="opportunity-detail-image"
                  height={540}
                  key={`${url}-${index}`}
                  src={url}
                  unoptimized
                  width={960}
                />
              ))}
            </div>
          </section>

          <section aria-labelledby="apply-heading" className="section">
            {currentApplication ? (
              <div className="notice">
                <h2 id="apply-heading">Votre candidature</h2>
                {success && <p className="alert success" role="status">{success}</p>}
                <p>Votre candidature est <strong>{statutLabels[currentApplication.statut] ?? currentApplication.statut}</strong>.</p>
                <Link className="text-link" href="/espace/candidatures">Suivre mes candidatures →</Link>
              </div>
            ) : authLoading ? (
              <p aria-live="polite" className="loading"><span className="spinner" />Vérification de votre espace…</p>
            ) : !user && !authLoading ? (
              <div className="notice">
                <h2 id="apply-heading">Cette offre vous intéresse&nbsp;?</h2>
                <p>Connectez-vous avec un espace candidat ou étudiant pour postuler et suivre votre dossier.</p>
                <Link className="button" href="/connexion">Se connecter</Link>
              </div>
            ) : user && !user.onboarding_termine ? (
              <div className="notice">
                <h2 id="apply-heading">Configurez votre espace candidat.</h2>
                <p>Choisissez l’espace candidat ou étudiant pour envoyer une candidature.</p>
                <Link className="button" href="/bienvenue">Choisir mes espaces</Link>
              </div>
            ) : user && !hasCandidateRole ? (
              <div className="notice">
                <h2 id="apply-heading">Votre compte n’a pas d’espace candidat.</h2>
                <p>L’accès à la candidature est réservé aux rôles candidat et étudiant.</p>
                <Link className="button" href="/bienvenue">Ajouter un espace candidat</Link>
              </div>
            ) : !isPublished ? (
              <div className="notice">
                <h2 id="apply-heading">Les candidatures ne sont pas ouvertes.</h2>
                <p>Cette opportunité n’accepte pas de nouvelles candidatures.</p>
              </div>
            ) : (
              <div className="form-card" style={{ marginInline: 0 }}>
                <h2 id="apply-heading">Postuler à cette opportunité</h2>
                <p>Présentez brièvement votre motivation. Votre profil sera partagé avec l’organisation après votre accord.</p>
                <form onSubmit={apply}>
                  <div className="field">
                    <label htmlFor="application-message">Message de candidature</label>
                    <textarea id="application-message" maxLength={2000} onChange={(event) => setMessage(event.target.value)} required value={message} />
                  </div>
                  <label className="checkbox-row">
                    <input checked={consent} onChange={(event) => setConsent(event.target.checked)} required type="checkbox" />
                    <span>J’accepte de partager mon profil professionnel avec le recruteur pour cette candidature.</span>
                  </label>
                  {error && <p className="alert" role="alert">{error}</p>}
                  {success && <p className="alert success" role="status">{success}</p>}
                  <button className="button" disabled={saving || !consent} type="submit">
                    {saving ? "Envoi…" : "Envoyer ma candidature"}
                  </button>
                </form>
              </div>
            )}
          </section>
        </>
      )}
    </main>
  );
}
