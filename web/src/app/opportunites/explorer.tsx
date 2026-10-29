"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { ApiError, apiFetch, listFrom } from "@/lib/api-client";
import type { Opportunite, Page } from "@/lib/types";

const typeLabels: Record<string, string> = {
  emploi: "Emploi",
  stage: "Stage",
  mission: "Mission",
};

type Filtres = {
  search: string;
  type: string;
  contrat: string;
  ville: string;
  pays: string;
  budget_min: string;
  budget_max: string;
  devise: string;
};

const filtresVides: Filtres = {
  search: "",
  type: "",
  contrat: "",
  ville: "",
  pays: "",
  budget_min: "",
  budget_max: "",
  devise: "XOF",
};

function opportuniteCourte(opportunite: Opportunite) {
  return (
    <article className="opportunity-card" key={opportunite.id}>
      <div>
        <div className="meta-row" style={{ marginBottom: 8 }}>
          <span className="badge">{typeLabels[opportunite.type] ?? opportunite.type}</span>
          {opportunite.contrat && <span className="badge badge-muted">{opportunite.contrat.toUpperCase()}</span>}
        </div>
        <h2><Link href={`/opportunites/${opportunite.id}`}>{opportunite.titre}</Link></h2>
        <p>{opportunite.organisation_nom || opportunite.createur_nom || "Organisation Akasha"}</p>
        <div className="meta-row" style={{ marginTop: 12 }}>
          {opportunite.ville && <span>{opportunite.ville}{opportunite.pays ? ` · ${opportunite.pays}` : ""}</span>}
          <span>{new Date(opportunite.cree_le).toLocaleDateString("fr-FR")}</span>
          {opportunite.budget_minimum != null && (
            <span>
              {opportunite.budget_minimum.toLocaleString("fr-FR")}
              {opportunite.budget_maximum != null && ` – ${opportunite.budget_maximum.toLocaleString("fr-FR")}`}
              {" "}{opportunite.devise}
            </span>
          )}
        </div>
      </div>
      <Link aria-label={`Consulter ${opportunite.titre}`} className="button button-secondary" href={`/opportunites/${opportunite.id}`}>
        Consulter
      </Link>
    </article>
  );
}

export function OpportunitiesExplorer({ initialSearch }: { initialSearch: string }) {
  const [formulaire, setFormulaire] = useState<Filtres>({
    ...filtresVides,
    search: initialSearch,
  });
  const [filtres, setFiltres] = useState<Filtres>({
    ...filtresVides,
    search: initialSearch,
  });
  const [opportunities, setOpportunities] = useState<Opportunite[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState<number | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setError("");
    try {
      const params = new URLSearchParams({ statut: "publiee", page: String(page) });
      if (filtres.search.trim()) params.set("search", filtres.search.trim());
      if (filtres.type) params.set("type", filtres.type);
      if (filtres.contrat) params.set("contrat", filtres.contrat);
      if (filtres.ville.trim()) params.set("ville", filtres.ville.trim());
      if (filtres.pays.trim()) params.set("pays", filtres.pays.trim());
      if (filtres.budget_min || filtres.budget_max) {
        params.set("devise", filtres.devise);
      }
      if (filtres.budget_min) params.set("budget_min", filtres.budget_min);
      if (filtres.budget_max) params.set("budget_max", filtres.budget_max);
      const payload = await apiFetch<Page<Opportunite> | Opportunite[]>(
        `opportunites/?${params.toString()}`,
      );
      const resultats = listFrom(payload);
      setOpportunities((current) =>
        page === 1 ? resultats : [...current, ...resultats],
      );
      if (Array.isArray(payload)) {
        setTotal(resultats.length);
        setHasMore(false);
      } else {
        setTotal(payload.count);
        setHasMore(Boolean(payload.next));
      }
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : "Impossible de charger les opportunités.");
    } finally {
      setLoading(false);
    }
  }, [filtres, page]);

  useEffect(() => {
    const timer = window.setTimeout(() => { void load(); }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (
      formulaire.budget_min &&
      formulaire.budget_max &&
      Number(formulaire.budget_min) > Number(formulaire.budget_max)
    ) {
      setError("Le budget maximum doit être supérieur ou égal au minimum.");
      return;
    }
    setLoading(true);
    setPage(1);
    setFiltres({
      ...formulaire,
      search: formulaire.search.trim(),
      ville: formulaire.ville.trim(),
    });
  }

  function viderFiltres() {
    const vides = { ...filtresVides };
    setFormulaire(vides);
    setFiltres(vides);
    setPage(1);
    setLoading(true);
  }

  return (
    <main className="container">
      <header className="page-heading">
        <p className="eyebrow" style={{ color: "var(--primary)" }}>À découvrir</p>
        <h1>Les opportunités qui font avancer.</h1>
        <p>Emplois, stages et missions publiés par les organisations et recruteurs.</p>
      </header>
      <form aria-label="Rechercher et filtrer les opportunités" className="opportunity-filters panel" onSubmit={submit} role="search">
        <div className="field opportunity-query">
          <label htmlFor="opportunity-search">Métier, compétence ou mot-clé</label>
          <input
            id="opportunity-search"
            onChange={(event) => setFormulaire((current) => ({ ...current, search: event.target.value }))}
            placeholder="Ex. développeuse web"
            type="search"
            value={formulaire.search}
          />
        </div>
        <div className="opportunity-filter-grid">
          <div className="field">
            <label htmlFor="opportunity-type">Type d’opportunité</label>
            <select id="opportunity-type" onChange={(event) => setFormulaire((current) => ({ ...current, type: event.target.value }))} value={formulaire.type}>
              <option value="">Tous les types</option>
              <option value="emploi">Emploi</option>
              <option value="stage">Stage</option>
              <option value="mission">Mission</option>
            </select>
          </div>
          <div className="field">
            <label htmlFor="opportunity-contract">Contrat</label>
            <select id="opportunity-contract" onChange={(event) => setFormulaire((current) => ({ ...current, contrat: event.target.value }))} value={formulaire.contrat}>
              <option value="">Tous les contrats</option>
              <option value="cdi">CDI</option>
              <option value="cdd">CDD</option>
              <option value="interim">Intérim</option>
              <option value="alternance">Alternance</option>
              <option value="autre">Autre</option>
            </select>
          </div>
          <div className="field">
            <label htmlFor="opportunity-city">Ville</label>
            <input id="opportunity-city" onChange={(event) => setFormulaire((current) => ({ ...current, ville: event.target.value }))} placeholder="Abidjan" value={formulaire.ville} />
          </div>
          <div className="field">
            <label htmlFor="opportunity-country">Pays (code ISO)</label>
            <input id="opportunity-country" maxLength={2} onChange={(event) => setFormulaire((current) => ({ ...current, pays: event.target.value.toUpperCase() }))} placeholder="CI" value={formulaire.pays} />
          </div>
          <div className="field">
            <label htmlFor="opportunity-budget-min">Budget minimum</label>
            <input id="opportunity-budget-min" min="0" onChange={(event) => setFormulaire((current) => ({ ...current, budget_min: event.target.value }))} type="number" value={formulaire.budget_min} />
          </div>
          <div className="field">
            <label htmlFor="opportunity-budget-max">Budget maximum</label>
            <input id="opportunity-budget-max" min="0" onChange={(event) => setFormulaire((current) => ({ ...current, budget_max: event.target.value }))} type="number" value={formulaire.budget_max} />
          </div>
          {(formulaire.budget_min || formulaire.budget_max) && (
            <div className="field">
              <label htmlFor="opportunity-currency">Devise du budget</label>
              <select id="opportunity-currency" onChange={(event) => setFormulaire((current) => ({ ...current, devise: event.target.value }))} value={formulaire.devise}>
                <option value="XOF">XOF · Franc CFA</option>
                <option value="EUR">EUR · Euro</option>
                <option value="USD">USD · Dollar américain</option>
              </select>
            </div>
          )}
        </div>
        <div className="opportunity-filter-actions">
          <button className="button" type="submit">Appliquer les filtres</button>
          <button className="button button-secondary" onClick={viderFiltres} type="button">Effacer</button>
        </div>
      </form>

      {loading && opportunities.length === 0 && <p aria-live="polite" className="loading"><span className="spinner" />Chargement des opportunités…</p>}
      {!loading && error && (
        <section className="empty-state" role="alert">
          <h2>Les offres ne sont pas disponibles pour le moment.</h2>
          <p>{error}</p>
          <button className="button button-secondary" onClick={() => { setLoading(true); setError(""); void load(); }} type="button">Réessayer</button>
        </section>
      )}
      {!loading && !error && opportunities.length === 0 && (
        <section className="empty-state">
          <h2>Aucune opportunité pour cette recherche.</h2>
          <p>Essayez un autre mot-clé ou revenez plus tard pour découvrir de nouvelles offres.</p>
        </section>
      )}
      {opportunities.length > 0 && (
        <>
          <p className="field-hint" aria-live="polite">
            {total ?? opportunities.length} résultat{(total ?? opportunities.length) > 1 ? "s" : ""}
            {total != null && opportunities.length < total ? ` · ${opportunities.length} affiché${opportunities.length > 1 ? "s" : ""}` : ""}
          </p>
          {error && <p className="alert" role="alert">{error}</p>}
          <div className="opportunity-list">{opportunities.map(opportuniteCourte)}</div>
          {loading && <p aria-live="polite" className="loading">Chargement…</p>}
          {hasMore && (
            <button
              className="button button-secondary"
              disabled={loading}
              onClick={() => { setLoading(true); setPage((current) => current + 1); }}
              type="button"
            >
              {loading ? "Chargement…" : "Afficher plus d’opportunités"}
            </button>
          )}
        </>
      )}
    </main>
  );
}
