"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/components/auth-provider";
import { ApiError, apiFetch, listFrom } from "@/lib/api-client";
import type {
  Candidature,
  Competence,
  Metier,
  Opportunite,
  Organisation,
  Page,
} from "@/lib/types";

const etapesParStatut: Record<string, string[]> = {
  envoyee: ["en_cours", "retenue", "entretien", "offre", "refusee"],
  en_cours: ["retenue", "entretien", "offre", "refusee"],
  retenue: ["entretien", "offre", "refusee"],
  entretien: ["offre", "refusee"],
  offre: ["acceptee", "refusee"],
};
const labelsStatut: Record<string, string> = {
  envoyee: "Envoyée",
  en_cours: "En cours",
  retenue: "Présélectionnée",
  entretien: "Entretien",
  offre: "Offre",
  acceptee: "Acceptée",
  refusee: "Refusée",
  retiree: "Retirée",
};
const labelsType: Record<string, string> = { emploi: "Emploi", stage: "Stage", mission: "Mission" };

function PageData<T>(payload: T[] | Page<T>) {
  return listFrom(payload);
}

export default function RecruiterPage() {
  const { user, loading: authLoading } = useAuth();
  const [organisations, setOrganisations] = useState<Organisation[]>([]);
  const [opportunities, setOpportunities] = useState<Opportunite[]>([]);
  const [applications, setApplications] = useState<Candidature[]>([]);
  const [name, setName] = useState("");
  const [organizationDescription, setOrganizationDescription] = useState("");
  const [organizationCity, setOrganizationCity] = useState("");
  const [organizationCountry, setOrganizationCountry] = useState("CI");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [city, setCity] = useState("");
  const [country, setCountry] = useState("CI");
  const [type, setType] = useState("emploi");
  const [contract, setContract] = useState("");
  const [budgetMinimum, setBudgetMinimum] = useState("");
  const [budgetMaximum, setBudgetMaximum] = useState("");
  const [currency, setCurrency] = useState("XOF");
  const [studyLevel, setStudyLevel] = useState("");
  const [duration, setDuration] = useState("");
  const [deadline, setDeadline] = useState("");
  const [urgency, setUrgency] = useState("normale");
  const [urgencyReason, setUrgencyReason] = useState("");
  const [jobId, setJobId] = useState("");
  const [selectedSkills, setSelectedSkills] = useState<number[]>([]);
  const [jobs, setJobs] = useState<Metier[]>([]);
  const [skills, setSkills] = useState<Competence[]>([]);
  const [organizationId, setOrganizationId] = useState("");
  const [loading, setLoading] = useState(true);
  const [savingOrganization, setSavingOrganization] = useState(false);
  const [savingOpportunity, setSavingOpportunity] = useState(false);
  const [busyApplication, setBusyApplication] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const canRecruit = Boolean(
    user?.roles_professionnels.some((role) => ["recruteur", "organisation"].includes(role)),
  );
  const canCreateOrganization = Boolean(user?.roles_professionnels.includes("organisation"));
  const load = useCallback(async () => {
    if (!user || !canRecruit) return;
    try {
      const [orgPayload, opportunityPayload, applicationPayload, jobPayload, skillPayload] = await Promise.all([
        apiFetch<Organisation[] | Page<Organisation>>("organisations/"),
        apiFetch<Opportunite[] | Page<Opportunite>>("opportunites/"),
        apiFetch<Candidature[] | Page<Candidature>>("opportunites/candidatures/recues/"),
        apiFetch<Metier[] | Page<Metier>>("referentiel/metiers/"),
        apiFetch<Competence[] | Page<Competence>>("referentiel/competences/"),
      ]);
      const orgs = PageData(orgPayload);
      setOrganisations(orgs);
      setOrganizationId((current) => current && orgs.some((item) => String(item.id) === current) ? current : "");
      const allOpportunities = PageData(opportunityPayload);
      setOpportunities(allOpportunities.filter((item) =>
        item.createur === user.id || (item.organisation != null && orgs.some((org) => org.id === item.organisation)),
      ));
      setApplications(PageData(applicationPayload));
      setJobs(PageData(jobPayload));
      setSkills(PageData(skillPayload));
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : "Impossible de charger votre espace recruteur.");
    } finally {
      setLoading(false);
    }
  }, [canRecruit, user]);

  useEffect(() => {
    const timer = window.setTimeout(() => { void load(); }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  async function createOrganization(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSavingOrganization(true);
    setError("");
    setNotice("");
    try {
      const organization = await apiFetch<Organisation>("organisations/", {
        method: "POST",
        body: JSON.stringify({
          nom: name,
          description: organizationDescription,
          ville: organizationCity,
          pays: organizationCountry.toUpperCase(),
        }),
      });
      setOrganisations((current) => [...current, organization]);
      setOrganizationId(String(organization.id));
      setName("");
      setOrganizationDescription("");
      setNotice("Votre organisation a été créée. Elle est visible uniquement dans votre espace membre.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Création de l’organisation impossible.");
    } finally {
      setSavingOrganization(false);
    }
  }

  async function createOpportunity(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (
      budgetMinimum &&
      budgetMaximum &&
      Number(budgetMinimum) > Number(budgetMaximum)
    ) {
      setError("Le budget maximum doit être supérieur ou égal au minimum.");
      return;
    }
    setSavingOpportunity(true);
    setError("");
    setNotice("");
    try {
      if (!organizationId && !user?.roles_professionnels.includes("recruteur")) {
        throw new Error("Choisissez une organisation dont vous êtes membre, ou ajoutez le rôle recruteur.");
      }
      const created = await apiFetch<Opportunite>("opportunites/", {
        method: "POST",
        body: JSON.stringify({
          titre: title,
          description,
          type,
          ville: city,
          pays: country.toUpperCase(),
          organisation: organizationId ? Number(organizationId) : null,
          contrat: contract,
          budget_minimum: budgetMinimum ? Number(budgetMinimum) : null,
          budget_maximum: budgetMaximum ? Number(budgetMaximum) : null,
          devise: currency,
          niveau_etudes: studyLevel,
          duree: duration,
          date_limite_candidature: deadline || null,
          urgence: urgency,
          motif_urgence: urgencyReason,
          metier: jobId ? Number(jobId) : null,
          competences: selectedSkills,
        }),
      });
      setOpportunities((current) => [created, ...current]);
      setTitle("");
      setDescription("");
      setContract("");
      setBudgetMinimum("");
      setBudgetMaximum("");
      setStudyLevel("");
      setDuration("");
      setDeadline("");
      setUrgency("normale");
      setUrgencyReason("");
      setJobId("");
      setSelectedSkills([]);
      setNotice("Votre offre a été enregistrée en brouillon. Vous pouvez la publier après vérification.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Création de l’opportunité impossible.");
    } finally {
      setSavingOpportunity(false);
    }
  }

  function toggleSkill(id: number) {
    setSelectedSkills((current) =>
      current.includes(id)
        ? current.filter((value) => value !== id)
        : [...current, id],
    );
  }

  async function publish(id: number) {
    setError("");
    setNotice("");
    try {
      const updated = await apiFetch<Opportunite>(`opportunites/${id}/publier/`, {
        method: "POST",
        body: JSON.stringify({}),
      });
      setOpportunities((current) => current.map((item) => item.id === id ? updated : item));
      setNotice("L’opportunité est publiée.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Publication impossible.");
    }
  }

  async function updateApplication(application: Candidature, statut: string) {
    setBusyApplication(application.id);
    setError("");
    setNotice("");
    try {
      const updated = await apiFetch<Candidature>(
        `opportunites/candidatures/${application.id}/transition/`,
        {
          method: "POST",
          body: JSON.stringify({ statut, expected_version: application.version }),
        },
      );
      setApplications((current) => current.map((item) => item.id === updated.id ? updated : item));
      setNotice("Le statut de la candidature a été mis à jour.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Mise à jour impossible.");
      if (reason instanceof ApiError && reason.status === 409) void load();
    } finally {
      setBusyApplication(null);
    }
  }

  if (authLoading) return <main className="container"><p className="loading">Chargement de votre espace…</p></main>;
  if (!user) {
    return (
      <main className="container"><section className="empty-state">
        <h1>Connectez-vous pour accéder à l’espace recruteur.</h1>
        <p>Les organisations, offres et candidatures sont accessibles aux membres autorisés.</p>
        <Link className="button" href="/connexion">Se connecter</Link>
      </section></main>
    );
  }
  if (!canRecruit) {
    return (
      <main className="container"><section className="notice">
        <h1>Un espace recruteur ou organisation est nécessaire.</h1>
        <p>Ajoutez le rôle correspondant à votre activité pour gérer des offres.</p>
        <Link className="button" href="/bienvenue">Configurer mes espaces</Link>
      </section></main>
    );
  }
  if (!user.onboarding_termine) {
    return (
      <main className="container"><section className="notice">
        <h1>Terminez la configuration de votre espace.</h1>
        <p>Validez vos rôles avant de gérer des opportunités.</p>
        <Link className="button" href="/bienvenue">Continuer</Link>
      </section></main>
    );
  }

  return (
    <main className="container">
      <header className="page-heading">
        <p className="eyebrow" style={{ color: "var(--primary)" }}>Votre espace de recrutement</p>
        <h1>Recruter sur Akasha</h1>
        <p>Gérez vos organisations, publiez des offres et suivez les candidatures reçues.</p>
      </header>
      {loading && <p aria-live="polite" className="loading"><span className="spinner" />Chargement de votre espace…</p>}
      {error && <p className="alert" role="alert">{error}</p>}
      {notice && <p className="alert success" role="status">{notice}</p>}
      {!loading && error && (
        <button className="button button-secondary" onClick={() => { setLoading(true); setError(""); void load(); }} type="button">Réessayer</button>
      )}

      <div className="card-grid section" style={{ alignItems: "start" }}>
        {canCreateOrganization && (
          <section aria-labelledby="create-org-heading" className="panel">
            <h2 id="create-org-heading">Créer une organisation</h2>
            <p className="field-hint">Les organisations listées ici sont celles dont vous êtes membre.</p>
            <form onSubmit={createOrganization}>
              <div className="field"><label htmlFor="org-name">Nom</label><input id="org-name" maxLength={180} onChange={(event) => setName(event.target.value)} required value={name} /></div>
              <div className="field"><label htmlFor="org-description">Présentation</label><textarea id="org-description" onChange={(event) => setOrganizationDescription(event.target.value)} value={organizationDescription} /></div>
              <div className="form-grid">
                <div className="field"><label htmlFor="org-city">Ville</label><input id="org-city" onChange={(event) => setOrganizationCity(event.target.value)} value={organizationCity} /></div>
                <div className="field"><label htmlFor="org-country">Pays (ISO)</label><input id="org-country" maxLength={2} onChange={(event) => setOrganizationCountry(event.target.value)} required value={organizationCountry} /></div>
              </div>
              <button className="button" disabled={savingOrganization} type="submit">{savingOrganization ? "Création…" : "Créer l’organisation"}</button>
            </form>
          </section>
        )}

        <section aria-labelledby="create-job-heading" className="panel">
          <h2 id="create-job-heading">Créer une opportunité</h2>
          <p className="field-hint">Une nouvelle offre est d’abord enregistrée en brouillon.</p>
          <form onSubmit={createOpportunity}>
            <div className="field"><label htmlFor="job-title">Titre</label><input id="job-title" maxLength={180} onChange={(event) => setTitle(event.target.value)} required value={title} /></div>
            <div className="field"><label htmlFor="job-description">Description</label><textarea id="job-description" onChange={(event) => setDescription(event.target.value)} required value={description} /></div>
            <div className="form-grid">
              <div className="field">
                <label htmlFor="job-type">Type</label>
                <select id="job-type" onChange={(event) => setType(event.target.value)} value={type}>
                  <option value="emploi">Emploi</option><option value="stage">Stage</option><option value="mission">Mission</option>
                </select>
              </div>
              <div className="field"><label htmlFor="job-city">Ville</label><input id="job-city" onChange={(event) => setCity(event.target.value)} value={city} /></div>
            </div>
            <div className="form-grid">
              <div className="field">
                <label htmlFor="job-contract">Contrat</label>
                <select id="job-contract" onChange={(event) => setContract(event.target.value)} value={contract}>
                  <option value="">À préciser</option>
                  <option value="cdi">CDI</option>
                  <option value="cdd">CDD</option>
                  <option value="interim">Intérim</option>
                  <option value="alternance">Alternance</option>
                  <option value="autre">Autre</option>
                </select>
              </div>
              <div className="field">
                <label htmlFor="job-deadline">Date limite de candidature</label>
                <input id="job-deadline" min={new Date().toISOString().slice(0, 10)} onChange={(event) => setDeadline(event.target.value)} type="date" value={deadline} />
              </div>
            </div>
            <div className="form-grid">
              <div className="field"><label htmlFor="job-budget-min">Budget minimum</label><input id="job-budget-min" min="0" onChange={(event) => setBudgetMinimum(event.target.value)} type="number" value={budgetMinimum} /></div>
              <div className="field"><label htmlFor="job-budget-max">Budget maximum</label><input id="job-budget-max" min="0" onChange={(event) => setBudgetMaximum(event.target.value)} type="number" value={budgetMaximum} /></div>
              <div className="field">
                <label htmlFor="job-currency">Devise</label>
                <select id="job-currency" onChange={(event) => setCurrency(event.target.value)} value={currency}>
                  <option value="XOF">XOF</option><option value="EUR">EUR</option><option value="USD">USD</option>
                </select>
              </div>
            </div>
            <div className="form-grid">
              <div className="field"><label htmlFor="job-study-level">Niveau d’études souhaité</label><input id="job-study-level" onChange={(event) => setStudyLevel(event.target.value)} value={studyLevel} /></div>
              <div className="field"><label htmlFor="job-duration">Durée</label><input id="job-duration" onChange={(event) => setDuration(event.target.value)} placeholder="Ex. 6 mois" value={duration} /></div>
            </div>
            <div className="form-grid">
              <div className="field">
                <label htmlFor="job-urgency">Priorité</label>
                <select id="job-urgency" onChange={(event) => setUrgency(event.target.value)} value={urgency}>
                  <option value="normale">Normale</option><option value="urgente">Urgente</option>
                </select>
              </div>
              <div className="field">
                <label htmlFor="job-reason">Motif de l’urgence</label>
                <input id="job-reason" maxLength={500} onChange={(event) => setUrgencyReason(event.target.value)} required={urgency === "urgente"} value={urgencyReason} />
              </div>
            </div>
            <div className="form-grid">
              <div className="field">
                <label htmlFor="job-profession">Métier</label>
                <select id="job-profession" onChange={(event) => setJobId(event.target.value)} value={jobId}>
                  <option value="">Tous les métiers</option>
                  {jobs.map((item) => <option key={item.id} value={item.id}>{item.nom}</option>)}
                </select>
              </div>
            </div>
            <fieldset className="skill-fieldset">
              <legend className="field-label">Compétences recherchées</legend>
              <div className="skill-choice-grid">
                {skills.map((item) => (
                  <label className="choice-row" key={item.id}>
                    <input checked={selectedSkills.includes(item.id)} onChange={() => toggleSkill(item.id)} type="checkbox" />
                    <span>{item.nom}</span>
                  </label>
                ))}
              </div>
            </fieldset>
            <div className="form-grid">
              <div className="field"><label htmlFor="job-country">Pays (ISO)</label><input id="job-country" maxLength={2} onChange={(event) => setCountry(event.target.value)} required value={country} /></div>
              <div className="field">
                <label htmlFor="job-organization">Organisation</label>
                <select id="job-organization" onChange={(event) => setOrganizationId(event.target.value)} value={organizationId}>
                  <option disabled={!user.roles_professionnels.includes("recruteur")} value="">
                    {user.roles_professionnels.includes("recruteur") ? "Publier en tant que recruteur" : "Choisir une organisation"}
                  </option>
                  {organisations.map((organization) => <option key={organization.id} value={organization.id}>{organization.nom}</option>)}
                </select>
              </div>
            </div>
            <button className="button" disabled={savingOpportunity || (!user.roles_professionnels.includes("recruteur") && !organizationId)} type="submit">{savingOpportunity ? "Enregistrement…" : "Enregistrer en brouillon"}</button>
          </form>
        </section>
      </div>

      <section aria-labelledby="organizations-heading" className="section">
        <div className="section-heading">
          <div><h2 id="organizations-heading">Mes organisations</h2><p>Accès limité aux organisations dont vous êtes membre.</p></div>
        </div>
        {organisations.length === 0 ? (
          <div className="empty-state">
            <h2>Aucune organisation associée.</h2>
            <p>{canCreateOrganization ? "Créez une organisation pour rattacher vos offres." : "Demandez à rejoindre une organisation existante."}</p>
          </div>
        ) : (
          <div className="feature-grid">
            {organisations.map((organization) => (
              <article className="feature-card" key={organization.id}>
                <h3>{organization.nom}</h3>
                <p>{organization.ville}{organization.pays ? ` · ${organization.pays}` : ""}</p>
                <span className={`badge ${organization.est_verifiee ? "badge-success" : "badge-muted"}`} style={{ marginTop: 12 }}>
                  {organization.est_verifiee ? "Vérifiée" : "Vérification en attente"}
                </span>
              </article>
            ))}
          </div>
        )}
      </section>

      <section aria-labelledby="offers-heading" className="section">
        <div className="section-heading"><div><h2 id="offers-heading">Mes opportunités</h2><p>Brouillons et offres publiées par vous ou vos organisations.</p></div></div>
        {opportunities.length === 0 ? (
          <div className="empty-state"><h2>Aucune offre à afficher.</h2><p>Créez votre première opportunité pour commencer.</p></div>
        ) : (
          <div className="stack">
            {opportunities.map((opportunity) => (
              <article className="list-row card" key={opportunity.id}>
                <div>
                  <h3><Link className="text-link" href={`/opportunites/${opportunity.id}`}>{opportunity.titre}</Link></h3>
                  <p>{opportunity.organisation_nom || "Sans organisation"} · {labelsType[opportunity.type] ?? opportunity.type} · {opportunity.ville || opportunity.pays}</p>
                  {opportunity.competences_detail.length > 0 && (
                    <p className="field-hint">
                      Compétences : {opportunity.competences_detail.map((item) => item.nom).join(" · ")}
                    </p>
                  )}
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span className={`badge ${opportunity.statut === "publiee" ? "badge-success" : "badge-muted"}`}>{opportunity.statut}</span>
                  {opportunity.statut === "brouillon" && (
                    <button className="button button-secondary" onClick={() => void publish(opportunity.id)} type="button">Publier</button>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      <section aria-labelledby="applications-heading" className="section">
        <div className="section-heading"><div><h2 id="applications-heading">Candidatures reçues</h2><p>Les informations personnelles restent limitées aux dossiers qui vous sont accessibles.</p></div></div>
        {applications.length === 0 ? (
          <div className="empty-state"><h2>Aucune candidature reçue.</h2><p>Les candidatures envoyées à vos offres apparaîtront ici.</p></div>
        ) : (
          <div className="stack">
            {applications.map((application) => {
              const choices = etapesParStatut[application.statut] ?? [];
              const opportunity = opportunities.find((item) => item.id === application.opportunite);
              return (
                <article className="card" key={application.id}>
                  <div className="page-heading-row">
                    <div>
                      <h3>{application.candidat_nom || "Candidat·e"}</h3>
                      <p>{opportunity?.titre ?? `Opportunité #${application.opportunite}`} · {new Date(application.cree_le).toLocaleDateString("fr-FR")}</p>
                    </div>
                    <span className="badge badge-muted">{labelsStatut[application.statut] ?? application.statut}</span>
                  </div>
                  <p style={{ whiteSpace: "pre-wrap", marginTop: 16 }}>{application.message}</p>
                  {application.profil_partage && (
                    <details className="shared-profile">
                      <summary>Consulter le profil partagé avec le consentement du candidat</summary>
                      <div className="shared-profile-content">
                        <strong>{application.profil_partage.nom}</strong>
                        {application.profil_partage.titre && <p>{application.profil_partage.titre}</p>}
                        <p>{[
                          application.profil_partage.metier_nom,
                          application.profil_partage.ville,
                        ].filter(Boolean).join(" · ")}</p>
                        {application.profil_partage.biographie && <p>{application.profil_partage.biographie}</p>}
                        {application.profil_partage.competences.length > 0 && (
                          <p>
                            Compétences : {application.profil_partage.competences
                              .map((item) => item.competence_nom)
                              .join(" · ")}
                          </p>
                        )}
                        <p className="field-hint">Le partage est limité aux informations incluses dans le consentement de candidature.</p>
                      </div>
                    </details>
                  )}
                  {choices.length > 0 && (
                    <div className="toolbar" style={{ marginTop: 14, marginBottom: 0 }}>
                      <label className="field-label" htmlFor={`application-${application.id}-status`}>Mettre à jour le statut</label>
                      <select
                        aria-label={`Nouveau statut pour la candidature de ${application.candidat_nom}`}
                        className="status-select"
                        disabled={busyApplication === application.id}
                        id={`application-${application.id}-status`}
                        onChange={(event) => {
                          const nextStatus = event.target.value;
                          if (nextStatus) void updateApplication(application, nextStatus);
                        }}
                        value=""
                      >
                        <option value="">Choisir…</option>
                        {choices.map((status) => <option key={status} value={status}>{labelsStatut[status] ?? status}</option>)}
                      </select>
                    </div>
                  )}
                </article>
              );
            })}
          </div>
        )}
      </section>
    </main>
  );
}
