"use client";

import Image from "next/image";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { ApiError, apiFetch } from "@/lib/api-client";
import type { ProfilPublic, ResultatEvaluationsPubliques } from "@/lib/types";

type Onglet = "profil" | "realisations" | "references";

const nomsOnglets: Record<Onglet, string> = {
  profil: "Profil",
  realisations: "Réalisations",
  references: "Références",
};

const libellesVerification: Record<string, string> = {
  declaree: "Déclarée · non vérifiée",
  a_verifier: "Vérification en cours",
  source_listee: "Source identifiée · à confirmer",
  document_verifie: "Document examiné",
  registre_confirme: "Confirmée par un registre",
  introuvable: "Non retrouvée dans la source",
  contestee: "Information contestée",
  perimee: "Vérification à renouveler",
};

function statutReference(statut: string | null | undefined) {
  return statut
    ? libellesVerification[statut] ?? "Statut de référence à confirmer"
    : "Déclarée · non vérifiée";
}

function periode(debut: string, fin: string | null) {
  const format = (date: string | null) =>
    date
      ? new Date(`${date}T00:00:00`).toLocaleDateString("fr-FR", {
          month: "short",
          year: "numeric",
        })
      : "En cours";
  return `${format(debut)} – ${format(fin)}`;
}

export function ProfilPublicView({ identifiant }: { identifiant: string }) {
  const [profil, setProfil] = useState<ProfilPublic | null>(null);
  const [avis, setAvis] = useState<ResultatEvaluationsPubliques | null>(null);
  const [erreurAvis, setErreurAvis] = useState("");
  const [onglet, setOnglet] = useState<Onglet>("profil");
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState("");
  const [partage, setPartage] = useState("");
  const [tentative, setTentative] = useState(0);
  const id = Number(identifiant);

  const charger = useCallback(async () => {
    if (!Number.isSafeInteger(id) || id < 1) {
      setErreur("Ce lien ne correspond pas à un profil valide.");
      setChargement(false);
      return;
    }
    setChargement(true);
    setErreur("");
    setAvis(null);
    setErreurAvis("");
    try {
      setProfil(await apiFetch<ProfilPublic>(`profils/${id}/`));
      try {
        setAvis(
          await apiFetch<ResultatEvaluationsPubliques>(
            `confiance/professionnels/${id}/evaluations/`,
          ),
        );
      } catch {
        setErreurAvis("Les avis vérifiés ne sont pas disponibles pour le moment.");
      }
    } catch (reason) {
      setProfil(null);
      setErreur(
        reason instanceof ApiError
          ? reason.message
          : "Ce profil n’a pas pu être chargé. Réessayez dans un instant.",
      );
    } finally {
      setChargement(false);
    }
  }, [id]);

  useEffect(() => {
    const timer = window.setTimeout(() => void charger(), 0);
    return () => window.clearTimeout(timer);
  }, [charger, tentative]);

  async function copierLien() {
    setPartage("");
    try {
      await navigator.clipboard.writeText(window.location.href);
      setPartage("Lien du profil copié.");
    } catch {
      setPartage("Copiez l’adresse de cette page pour partager le profil.");
    }
  }

  if (chargement) {
    return <main className="container"><p aria-live="polite" className="loading">Chargement du profil…</p></main>;
  }
  if (erreur || !profil) {
    return (
      <main className="container">
        <section className="empty-state" role="alert">
          <h1>Profil indisponible</h1>
          <p>{erreur || "Ce profil public n’est pas disponible."}</p>
          <button
            className="button button-secondary"
            onClick={() => setTentative((value) => value + 1)}
            type="button"
          >
            Réessayer
          </button>
        </section>
      </main>
    );
  }

  const initiale = profil.nom.trim().slice(0, 1).toLocaleUpperCase() || "A";

  return (
    <main className="container public-profile">
      <Link className="text-link" href="/opportunites">← Retour aux opportunités</Link>
      <header className="public-profile-cover">
        <span aria-hidden="true" className="public-profile-orbit" />
        <span aria-hidden="true" className="public-profile-orbit public-profile-orbit-secondary" />
        <div className="public-profile-avatar">
          {profil.photo_url ? (
            <Image
              alt={`Portrait de ${profil.nom}`}
              className="public-profile-photo"
              height={104}
              src={profil.photo_url}
              unoptimized
              width={104}
            />
          ) : (
            <span aria-hidden="true">{initiale}</span>
          )}
        </div>
      </header>

      <section className="public-profile-summary">
        <div className="public-profile-heading">
          <div>
            <h1>{profil.nom}</h1>
            {profil.titre && <p className="public-profile-title">{profil.titre}</p>}
            <p className="public-profile-meta">
              {[profil.metier_nom, profil.ville].filter(Boolean).join(" · ")}
            </p>
          </div>
          <button className="button button-secondary" onClick={() => void copierLien()} type="button">
            Partager le profil
          </button>
        </div>
        <p className={`public-availability ${profil.disponible ? "is-available" : ""}`}>
          <span aria-hidden="true" />
          {profil.disponible
            ? "Disponible pour de nouvelles opportunités"
            : "Pas disponible actuellement"}
        </p>
        {partage && <p aria-live="polite" className="field-hint">{partage}</p>}
      </section>

      <div aria-label="Contenu du profil" className="public-profile-tabs" role="tablist">
        {(Object.keys(nomsOnglets) as Onglet[]).map((cle) => (
          <button
            aria-selected={onglet === cle}
            className={onglet === cle ? "public-profile-tab active" : "public-profile-tab"}
            id={`tab-${cle}`}
            key={cle}
            onClick={() => setOnglet(cle)}
            role="tab"
            type="button"
          >
            {nomsOnglets[cle]}
          </button>
        ))}
      </div>

      <section aria-labelledby={`tab-${onglet}`} className="public-profile-content" role="tabpanel">
        {onglet === "profil" && (
          <div className="public-profile-columns">
            <article className="panel">
              <h2>À propos</h2>
              <p>{profil.biographie || "Cette personne n’a pas encore ajouté de présentation."}</p>
              <p className="privacy-note">
                Les coordonnées privées et les documents justificatifs ne sont pas publiés.
              </p>
            </article>
            <article className="panel">
              <h2>Compétences</h2>
              {profil.competences.length ? (
                <ul className="public-skill-list">
                  {profil.competences.map((competence, index) => (
                    <li key={`${competence.competence_nom}-${index}`}>
                      <strong>{competence.competence_nom}</strong>
                      <span>{competence.niveau}</span>
                      <small>
                        {competence.est_personnalisee
                          ? "Déclarée par le profil · non vérifiée"
                          : "Issue du référentiel · non attestée"}
                      </small>
                    </li>
                  ))}
                </ul>
              ) : <p>Aucune compétence renseignée.</p>}
            </article>
          </div>
        )}

        {onglet === "realisations" && (
          profil.realisations.length ? (
            <div className="public-project-grid">
              {profil.realisations.map((realisation, index) => (
                <article className="panel public-project" key={`${realisation.titre}-${index}`}>
                  <h2>{realisation.titre}</h2>
                  <p>{realisation.description}</p>
                  <p className={realisation.est_verifiee ? "verification verified" : "verification declared"}>
                    {realisation.est_verifiee
                      ? "Réalisation vérifiée par Akasha"
                      : "Déclarée · non vérifiée"}
                  </p>
                  {realisation.date_realisation && (
                    <p className="field-hint">
                      {new Date(`${realisation.date_realisation}T00:00:00`).toLocaleDateString("fr-FR", {
                        month: "long",
                        year: "numeric",
                      })}
                    </p>
                  )}
                  {realisation.images_url.map((url, imageIndex) => (
                    <Image
                      alt={`Image ${imageIndex + 1} de ${realisation.titre}`}
                      className="public-project-image"
                      height={500}
                      key={`${url}-${imageIndex}`}
                      src={url}
                      unoptimized
                      width={800}
                    />
                  ))}
                  {realisation.lien && (
                    <a href={realisation.lien} rel="noreferrer" target="_blank">
                      Consulter le projet
                    </a>
                  )}
                </article>
              ))}
            </div>
          ) : <p className="empty-state">Aucune réalisation publiée pour le moment.</p>
        )}

        {onglet === "references" && (
          <div className="public-reference-list">
            <article className="panel">
              <h2>Avis vérifiés</h2>
              {erreurAvis ? (
                <p role="status">{erreurAvis}</p>
              ) : avis?.moyenne !== null && avis?.moyenne !== undefined ? (
                <p>
                  <strong>
                    {avis.moyenne.toLocaleString("fr-FR", {
                      minimumFractionDigits: 1,
                      maximumFractionDigits: 1,
                    })}{" "}
                    / 5
                  </strong>
                </p>
              ) : (
                <p>{avis?.message ?? "Pas encore assez d’avis"}</p>
              )}
              {avis && (
                <>
                  <p>{avis.nombre} avis · seuil d’affichage : {avis.seuil}</p>
                  {avis.periode.debut && avis.periode.fin && (
                    <p className="field-hint">
                      Période : {periode(avis.periode.debut, avis.periode.fin)}
                    </p>
                  )}
                  <p className="privacy-note">
                    Seuls les avis liés à des collaborations terminées sont pris en compte.
                  </p>
                </>
              )}
            </article>
            {profil.experiences.map((experience, index) => (
              <article className="panel public-reference" key={`${experience.poste}-${index}`}>
                <div>
                  <h2>{experience.poste}</h2>
                  <p>{experience.organisation} · {periode(experience.debut, experience.fin)}</p>
                  {experience.description && <p>{experience.description}</p>}
                </div>
                <span className={experience.est_attestee ? "verification verified" : "verification declared"}>
                  {experience.est_attestee
                    ? "Attestée par Akasha"
                    : statutReference(experience.entreprise_reference_statut_verification)}
                </span>
              </article>
            ))}
            {profil.formations.map((formation, index) => (
              <article className="panel public-reference" key={`${formation.intitule}-${index}`}>
                <div>
                  <h2>{formation.intitule}</h2>
                  <p>{formation.etablissement} · {periode(formation.debut, formation.fin)}</p>
                </div>
                <span className={formation.est_verifiee ? "verification verified" : "verification declared"}>
                  {formation.est_verifiee
                    ? "Formation vérifiée par Akasha"
                    : [
                        statutReference(formation.etablissement_reference_statut_verification),
                        statutReference(formation.programme_reference_statut_verification),
                      ].filter((label) => label !== "Déclarée · non vérifiée").join(" · ") ||
                      "Déclarée · non vérifiée"}
                </span>
              </article>
            ))}
            {profil.qualifications.map((qualification, index) => (
              <article className="panel public-reference" key={`${qualification.nom}-${index}`}>
                <div>
                  <h2>{qualification.nom}</h2>
                  <p>{qualification.organisme}</p>
                  {qualification.expiration && (
                    <p className="field-hint">
                      Expire le {new Date(`${qualification.expiration}T00:00:00`).toLocaleDateString("fr-FR")}
                    </p>
                  )}
                </div>
                <span className={qualification.est_confirmee ? "verification verified" : "verification declared"}>
                  {qualification.est_confirmee
                    ? "Confirmée par Akasha"
                    : "Déclarée · non vérifiée"}
                </span>
              </article>
            ))}
            {!profil.experiences.length && !profil.formations.length && !profil.qualifications.length && (
              <p className="empty-state">Aucune référence publiée pour le moment.</p>
            )}
          </div>
        )}
      </section>
    </main>
  );
}
