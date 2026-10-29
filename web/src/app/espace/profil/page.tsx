"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/components/auth-provider";
import { ApiError, apiFetch, listFrom } from "@/lib/api-client";
import type { Competence, Metier, Profil, Utilisateur } from "@/lib/types";
import { PortfolioEditor } from "./portfolio-editor";

export default function ProfilPage() {
  const { user, loading: authLoading, setUser } = useAuth();
  const [profile, setProfile] = useState<Profil | null>(null);
  const [metiers, setMetiers] = useState<Metier[]>([]);
  const [competences, setCompetences] = useState<Competence[]>([]);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [telephone, setTelephone] = useState("");
  const [pays, setPays] = useState("CI");
  const [titre, setTitre] = useState("");
  const [biographie, setBiographie] = useState("");
  const [ville, setVille] = useState("");
  const [metier, setMetier] = useState("");
  const [selectedCompetences, setSelectedCompetences] = useState<number[]>([]);
  const [customCompetences, setCustomCompetences] = useState("");
  const [skillLevels, setSkillLevels] = useState<Record<string, string>>({});
  const [disponible, setDisponible] = useState(true);
  const [visible, setVisible] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);

  const load = useCallback(async () => {
    if (!user) return;
    try {
      const [account, currentProfile, jobPayload, skillPayload] = await Promise.all([
        apiFetch<Utilisateur>("comptes/moi/"),
        apiFetch<Profil>("profils/moi/"),
        apiFetch<Metier[] | { results?: Metier[] }>("referentiel/metiers/"),
        apiFetch<Competence[] | { results?: Competence[] }>("referentiel/competences/"),
      ]);
      setProfile(currentProfile);
      setMetiers(listFrom(jobPayload));
      setCompetences(listFrom(skillPayload));
      setFirstName(account.first_name);
      setLastName(account.last_name);
      setTelephone(account.telephone);
      setPays(account.pays);
      setTitre(currentProfile.titre);
      setBiographie(currentProfile.biographie);
      setVille(currentProfile.ville);
      setMetier(currentProfile.metier == null ? "" : String(currentProfile.metier));
      setDisponible(currentProfile.disponible);
      setVisible(currentProfile.visible_publiquement);
      const existing = currentProfile.competences_detail ?? [];
      setSelectedCompetences(existing.flatMap((item) => item.competence == null ? [] : [item.competence]));
      setCustomCompetences(existing.filter((item) => item.competence == null).map((item) => item.competence_personnalisee || item.competence_nom).join(", "));
      setSkillLevels(Object.fromEntries(existing.map((item) => [
        item.competence == null ? `custom:${(item.competence_personnalisee || item.competence_nom).toLocaleLowerCase()}` : String(item.competence),
        item.niveau,
      ])));
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : "Impossible de charger votre profil.");
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    const timer = window.setTimeout(() => { void load(); }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  function toggleCompetence(id: number) {
    setSelectedCompetences((current) => current.includes(id) ? current.filter((value) => value !== id) : [...current, id]);
  }

  async function save(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!profile) return;
    setSaving(true);
    setSaved(false);
    setError("");
    try {
      const account = await apiFetch<Utilisateur>("comptes/moi/", {
        method: "PATCH",
        body: JSON.stringify({
          first_name: firstName,
          last_name: lastName,
          telephone,
          pays: pays.toUpperCase(),
        }),
      });
      setUser(account);
      const skills = [
        ...selectedCompetences.map((id) => ({
          competence: id,
          niveau: skillLevels[String(id)] ?? "autonome",
        })),
        ...customCompetences.split(",").map((name) => name.trim()).filter(Boolean).map((name) => ({
          competence_personnalisee: name,
          niveau: skillLevels[`custom:${name.toLocaleLowerCase()}`] ?? "autonome",
        })),
      ];
      const updatedProfile = await apiFetch<Profil>("profils/moi/", {
        method: "PATCH",
        body: JSON.stringify({
          titre,
          biographie,
          ville,
          disponible,
          visible_publiquement: visible,
          metier: metier ? Number(metier) : null,
          competences: skills,
        }),
      });
      setProfile(updatedProfile);
      setSaved(true);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Enregistrement impossible.");
    } finally {
      setSaving(false);
    }
  }

  if (authLoading) return <main className="container"><p className="loading">Chargement de votre espace…</p></main>;
  if (!user) {
    return (
      <main className="container"><section className="empty-state">
        <h1>Connectez-vous pour gérer votre profil.</h1>
        <p>Votre passeport professionnel reste privé jusqu’à ce que vous décidiez de le rendre visible.</p>
        <Link className="button" href="/connexion">Se connecter</Link>
      </section></main>
    );
  }
  if (!user.roles_professionnels.some((role) => ["professionnel", "candidat", "etudiant"].includes(role))) {
    return (
      <main className="container"><section className="notice">
        <h1>Un espace professionnel est nécessaire.</h1>
        <p>Ajoutez un espace professionnel, candidat ou étudiant pour gérer votre profil.</p>
        <Link className="button" href="/bienvenue">Configurer mes espaces</Link>
      </section></main>
    );
  }

  return (
    <main className="container">
      <header className="page-heading">
        <p className="eyebrow" style={{ color: "var(--primary)" }}>Votre passeport professionnel</p>
        <h1>Mon profil</h1>
        <p>Présentez les informations que vous souhaitez partager dans vos parcours Akasha.</p>
      </header>
      {loading && <p className="loading"><span className="spinner" />Chargement de votre profil…</p>}
      {!loading && error && !profile && (
        <section className="empty-state" role="alert">
          <h2>Le profil ne peut pas être chargé.</h2><p>{error}</p>
          <button className="button button-secondary" onClick={() => { setLoading(true); setError(""); void load(); }} type="button">Réessayer</button>
        </section>
      )}
      {!loading && profile && (
        <div className="stack">
          <form className="stack" onSubmit={save}>
            <section className="panel">
              <h2>Identité</h2>
              <div className="form-grid">
                <div className="field"><label htmlFor="profile-first-name">Prénom</label><input id="profile-first-name" onChange={(event) => setFirstName(event.target.value)} required value={firstName} /></div>
                <div className="field"><label htmlFor="profile-last-name">Nom</label><input id="profile-last-name" onChange={(event) => setLastName(event.target.value)} required value={lastName} /></div>
                <div className="field"><label htmlFor="profile-phone">Téléphone</label><input autoComplete="tel" id="profile-phone" onChange={(event) => setTelephone(event.target.value)} value={telephone} /></div>
                <div className="field"><label htmlFor="profile-country">Pays (code ISO)</label><input id="profile-country" maxLength={2} onChange={(event) => setPays(event.target.value)} required value={pays} /></div>
              </div>
            </section>
            <section className="panel">
              <h2>Profil professionnel</h2>
              <div className="field">
                <label htmlFor="profile-title">Titre professionnel</label>
                <input id="profile-title" maxLength={180} onChange={(event) => setTitre(event.target.value)} placeholder="Ex. Développeuse web" value={titre} />
              </div>
              <div className="field">
                <label htmlFor="profile-bio">À propos</label>
                <textarea id="profile-bio" onChange={(event) => setBiographie(event.target.value)} value={biographie} />
              </div>
              <div className="form-grid">
                <div className="field"><label htmlFor="profile-city">Ville</label><input id="profile-city" onChange={(event) => setVille(event.target.value)} value={ville} /></div>
                <div className="field">
                  <label htmlFor="profile-job">Métier</label>
                  <select id="profile-job" onChange={(event) => setMetier(event.target.value)} value={metier}>
                    <option value="">Choisir un métier</option>
                    {metiers.map((item) => <option key={item.id} value={item.id}>{item.nom}</option>)}
                  </select>
                </div>
              </div>
              <fieldset style={{ border: 0, margin: "8px 0 0", padding: 0 }}>
                <legend className="field-label">Compétences du référentiel</legend>
                <div className="form-grid" style={{ marginTop: 10 }}>
                  {competences.map((item) => (
                    <label className="choice-row" key={item.id} style={{ margin: 0 }}>
                      <input checked={selectedCompetences.includes(item.id)} onChange={() => toggleCompetence(item.id)} type="checkbox" />
                      <span>{item.nom}</span>
                    </label>
                  ))}
                </div>
                {competences.length === 0 && <p className="field-hint">Aucune compétence n’est actuellement disponible dans le référentiel.</p>}
              </fieldset>
              <div className="field" style={{ marginTop: 20 }}>
                <label htmlFor="custom-skills">Autres compétences (séparées par des virgules)</label>
                <input id="custom-skills" onChange={(event) => setCustomCompetences(event.target.value)} value={customCompetences} />
              </div>
              <label className="checkbox-row">
                <input checked={disponible} onChange={(event) => setDisponible(event.target.checked)} type="checkbox" />
                <span>Je suis disponible pour de nouvelles opportunités.</span>
              </label>
              <label className="checkbox-row">
                <input checked={visible} onChange={(event) => setVisible(event.target.checked)} type="checkbox" />
                <span>Rendre mon profil visible publiquement.</span>
              </label>
              <p className="field-hint">Vos coordonnées ne sont pas publiées avec votre profil professionnel.</p>
              {visible && profile.id > 0 && (
                <Link className="text-link" href={`/profil/${profile.id}`} target="_blank" rel="noreferrer">
                  Prévisualiser mon profil public
                </Link>
              )}
            </section>
            {error && <p className="alert" role="alert">{error}</p>}
            {saved && <p className="alert success" role="status">Votre profil a été enregistré.</p>}
            <button className="button" disabled={saving} type="submit">{saving ? "Enregistrement…" : "Enregistrer mon profil"}</button>
          </form>
          <PortfolioEditor />
        </div>
      )}
    </main>
  );
}
