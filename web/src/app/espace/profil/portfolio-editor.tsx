"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError, apiFetch, listFrom } from "@/lib/api-client";
import type {
  PortfolioExperience,
  PortfolioFormation,
  PortfolioQualification,
  PortfolioRealisation,
} from "@/lib/types";

type SectionPortfolio =
  | "experiences"
  | "formations"
  | "realisations"
  | "qualifications";

type EntreePortfolio =
  | PortfolioExperience
  | PortfolioFormation
  | PortfolioRealisation
  | PortfolioQualification;

type DonneesPortfolio = Record<SectionPortfolio, EntreePortfolio[]>;
type Champ = {
  nom: string;
  libelle: string;
  type?: "text" | "date" | "url" | "textarea";
  required?: boolean;
};

const sections: { cle: SectionPortfolio; titre: string }[] = [
  { cle: "experiences", titre: "Expériences professionnelles" },
  { cle: "formations", titre: "Formations" },
  { cle: "realisations", titre: "Réalisations" },
  { cle: "qualifications", titre: "Qualifications" },
];

const champs: Record<SectionPortfolio, Champ[]> = {
  experiences: [
    { nom: "poste", libelle: "Poste", required: true },
    { nom: "organisation", libelle: "Organisation", required: true },
    { nom: "description", libelle: "Description", type: "textarea" },
    { nom: "debut", libelle: "Date de début", type: "date", required: true },
    { nom: "fin", libelle: "Date de fin", type: "date" },
  ],
  formations: [
    { nom: "intitule", libelle: "Intitulé", required: true },
    { nom: "etablissement", libelle: "Établissement", required: true },
    { nom: "debut", libelle: "Date de début", type: "date", required: true },
    { nom: "fin", libelle: "Date de fin", type: "date" },
  ],
  realisations: [
    { nom: "titre", libelle: "Titre", required: true },
    { nom: "description", libelle: "Description", type: "textarea", required: true },
    { nom: "lien", libelle: "Lien du projet", type: "url" },
    { nom: "date_realisation", libelle: "Date", type: "date" },
  ],
  qualifications: [
    { nom: "nom", libelle: "Qualification", required: true },
    { nom: "organisme", libelle: "Organisme", required: true },
    { nom: "reference", libelle: "Référence (privée)", type: "text" },
    { nom: "expiration", libelle: "Date d’expiration", type: "date" },
  ],
};

const vide: DonneesPortfolio = {
  experiences: [],
  formations: [],
  realisations: [],
  qualifications: [],
};

function titreEntree(section: SectionPortfolio, entree: EntreePortfolio) {
  if (section === "experiences") return (entree as PortfolioExperience).poste;
  if (section === "formations") return (entree as PortfolioFormation).intitule;
  if (section === "realisations") return (entree as PortfolioRealisation).titre;
  return (entree as PortfolioQualification).nom;
}

function sousTitreEntree(section: SectionPortfolio, entree: EntreePortfolio) {
  if (section === "experiences") return (entree as PortfolioExperience).organisation;
  if (section === "formations") return (entree as PortfolioFormation).etablissement;
  if (section === "realisations") return (entree as PortfolioRealisation).description;
  return (entree as PortfolioQualification).organisme;
}

function statutEntree(section: SectionPortfolio, entree: EntreePortfolio) {
  const verifiee =
    section === "experiences"
      ? (entree as PortfolioExperience).est_attestee
      : section === "formations"
        ? (entree as PortfolioFormation).est_verifiee
        : section === "realisations"
          ? (entree as PortfolioRealisation).est_verifiee
          : (entree as PortfolioQualification).est_confirmee;
  return verifiee ? "Vérifiée par Akasha" : "Déclarée · non vérifiée";
}

function datesEnValeurs(section: SectionPortfolio, entree: EntreePortfolio) {
  const valeur = entree as unknown as Record<string, string | number | boolean | null>;
  return Object.fromEntries(
    champs[section].map(({ nom }) => [
      nom,
      valeur[nom] == null ? "" : String(valeur[nom]),
    ]),
  );
}

export function PortfolioEditor() {
  const [portfolio, setPortfolio] = useState<DonneesPortfolio>(vide);
  const [sectionActive, setSectionActive] = useState<SectionPortfolio | null>(null);
  const [identifiantModifie, setIdentifiantModifie] = useState<number | null>(null);
  const [brouillon, setBrouillon] = useState<Record<string, string>>({});
  const [images, setImages] = useState<File[]>([]);
  const [chargement, setChargement] = useState(true);
  const [enregistrement, setEnregistrement] = useState(false);
  const [erreur, setErreur] = useState("");
  const [message, setMessage] = useState("");

  const charger = useCallback(async () => {
    setChargement(true);
    setErreur("");
    try {
      const [experiences, formations, realisations, qualifications] =
        await Promise.all([
          apiFetch<PortfolioExperience[] | { results?: PortfolioExperience[] }>(
            "portfolios/experiences/",
          ),
          apiFetch<PortfolioFormation[] | { results?: PortfolioFormation[] }>(
            "portfolios/formations/",
          ),
          apiFetch<PortfolioRealisation[] | { results?: PortfolioRealisation[] }>(
            "portfolios/realisations/",
          ),
          apiFetch<PortfolioQualification[] | { results?: PortfolioQualification[] }>(
            "portfolios/qualifications/",
          ),
        ]);
      setPortfolio({
        experiences: listFrom(experiences),
        formations: listFrom(formations),
        realisations: listFrom(realisations),
        qualifications: listFrom(qualifications),
      });
    } catch (reason) {
      setErreur(
        reason instanceof ApiError
          ? reason.message
          : "Impossible de charger votre portfolio.",
      );
    } finally {
      setChargement(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void charger(), 0);
    return () => window.clearTimeout(timer);
  }, [charger]);

  function ouvrirFormulaire(section: SectionPortfolio, entree?: EntreePortfolio) {
    setSectionActive(section);
    setIdentifiantModifie(entree?.id ?? null);
    setBrouillon(entree ? datesEnValeurs(section, entree) : {});
    setImages([]);
    setErreur("");
    setMessage("");
  }

  function fermerFormulaire() {
    setSectionActive(null);
    setIdentifiantModifie(null);
    setBrouillon({});
    setImages([]);
  }

  function payloadPour(section: SectionPortfolio): Record<string, string | null> {
    const valeur = (nom: string) => brouillon[nom]?.trim() ?? "";
    if (section === "experiences") {
      return {
        poste: valeur("poste"),
        organisation: valeur("organisation"),
        description: valeur("description"),
        debut: valeur("debut"),
        fin: valeur("fin") || null,
      };
    }
    if (section === "formations") {
      return {
        intitule: valeur("intitule"),
        etablissement: valeur("etablissement"),
        debut: valeur("debut"),
        fin: valeur("fin") || null,
      };
    }
    if (section === "realisations") {
      return {
        titre: valeur("titre"),
        description: valeur("description"),
        lien: valeur("lien"),
        date_realisation: valeur("date_realisation") || null,
      };
    }
    return {
      nom: valeur("nom"),
      organisme: valeur("organisme"),
      reference: valeur("reference"),
      expiration: valeur("expiration") || null,
    };
  }

  async function enregistrer(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!sectionActive) return;
    setEnregistrement(true);
    setErreur("");
    setMessage("");
    try {
      const payload = payloadPour(sectionActive);
      let corps: BodyInit;
      if (sectionActive === "realisations" && images.length > 0) {
        const formulaire = new FormData();
        Object.entries(payload).forEach(([nom, valeur]) => {
          if (valeur !== null) formulaire.append(nom, valeur);
        });
        images.forEach((image) => formulaire.append("images", image));
        corps = formulaire;
      } else {
        corps = JSON.stringify(payload);
      }
      const detail = identifiantModifie ? `${identifiantModifie}/` : "";
      await apiFetch<EntreePortfolio>(
        `portfolios/${sectionActive}/${detail}`,
        {
          method: identifiantModifie ? "PATCH" : "POST",
          body: corps,
        },
      );
      await charger();
      fermerFormulaire();
      setMessage("Votre portfolio a été enregistré.");
    } catch (reason) {
      setErreur(
        reason instanceof Error ? reason.message : "Enregistrement impossible.",
      );
    } finally {
      setEnregistrement(false);
    }
  }

  async function supprimer(section: SectionPortfolio, id: number) {
    if (!window.confirm("Supprimer définitivement cet élément du portfolio ?")) return;
    setErreur("");
    setMessage("");
    try {
      await apiFetch<void>(`portfolios/${section}/${id}/`, { method: "DELETE" });
      await charger();
      if (sectionActive === section && identifiantModifie === id) fermerFormulaire();
      setMessage("Élément supprimé.");
    } catch (reason) {
      setErreur(reason instanceof Error ? reason.message : "Suppression impossible.");
    }
  }

  return (
    <section className="portfolio-editor panel" aria-labelledby="portfolio-heading">
      <header className="portfolio-editor-heading">
        <div>
          <h2 id="portfolio-heading">Portfolio</h2>
          <p>Ajoutez votre parcours et vos réalisations. Les statuts de vérification restent gérés par Akasha.</p>
        </div>
        {chargement && <span className="field-hint">Chargement…</span>}
      </header>

      {erreur && <p className="alert" role="alert">{erreur}</p>}
      {message && <p className="alert success" role="status">{message}</p>}

      {sections.map(({ cle, titre }) => (
        <section className="portfolio-section" key={cle} aria-labelledby={`portfolio-${cle}`}>
          <header className="portfolio-section-heading">
            <h3 id={`portfolio-${cle}`}>{titre}</h3>
            <button
              className="button button-secondary"
              onClick={() => ouvrirFormulaire(cle)}
              type="button"
            >
              Ajouter
            </button>
          </header>

          {!chargement && portfolio[cle].length === 0 && (
            <p className="field-hint">Aucun élément ajouté.</p>
          )}
          <div className="portfolio-item-list">
            {portfolio[cle].map((entree) => (
              <article className="portfolio-item" key={entree.id}>
                <div>
                  <h4>{titreEntree(cle, entree)}</h4>
                  <p>{sousTitreEntree(cle, entree)}</p>
                  <span className="field-hint">{statutEntree(cle, entree)}</span>
                  {cle === "realisations" &&
                    (entree as PortfolioRealisation).images_url.map((url, index) => (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        alt={`Image ${index + 1} de ${(entree as PortfolioRealisation).titre}`}
                        className="portfolio-item-image"
                        key={`${url}-${index}`}
                        src={url}
                      />
                    ))}
                </div>
                <div className="portfolio-item-actions">
                  <button
                    className="text-link"
                    onClick={() => ouvrirFormulaire(cle, entree)}
                    type="button"
                  >
                    Modifier
                  </button>
                  <button
                    className="text-link danger-link"
                    onClick={() => void supprimer(cle, entree.id)}
                    type="button"
                  >
                    Supprimer
                  </button>
                </div>
              </article>
            ))}
          </div>

          {sectionActive === cle && (
            <form className="portfolio-form" onSubmit={(event) => void enregistrer(event)}>
              <h4>{identifiantModifie ? "Modifier" : "Ajouter"} · {titre}</h4>
              <div className="form-grid">
                {champs[cle].map((champ) => (
                  <div className="field" key={champ.nom}>
                    <label htmlFor={`portfolio-${cle}-${champ.nom}`}>{champ.libelle}</label>
                    {champ.type === "textarea" ? (
                      <textarea
                        id={`portfolio-${cle}-${champ.nom}`}
                        onChange={(event) =>
                          setBrouillon((valeur) => ({ ...valeur, [champ.nom]: event.target.value }))
                        }
                        required={champ.required}
                        value={brouillon[champ.nom] ?? ""}
                      />
                    ) : (
                      <input
                        id={`portfolio-${cle}-${champ.nom}`}
                        onChange={(event) =>
                          setBrouillon((valeur) => ({ ...valeur, [champ.nom]: event.target.value }))
                        }
                        required={champ.required}
                        type={champ.type ?? "text"}
                        value={brouillon[champ.nom] ?? ""}
                      />
                    )}
                  </div>
                ))}
              </div>
              {cle === "realisations" && (
                <div className="field">
                  <label htmlFor="portfolio-realisation-images">Images de réalisation (5 maximum)</label>
                  <input
                    accept="image/*"
                    id="portfolio-realisation-images"
                    multiple
                    onChange={(event) => {
                      const selection = Array.from(event.target.files ?? []);
                      setImages(selection.slice(0, 5));
                      if (selection.length > 5) {
                        setErreur("Sélectionnez au maximum cinq images.");
                      }
                    }}
                    type="file"
                  />
                  <span className="field-hint">
                    {images.length
                      ? `${images.length} image${images.length > 1 ? "s" : ""} sélectionnée${images.length > 1 ? "s" : ""}. L’ajout remplace la galerie actuelle.`
                      : "Laissez ce champ vide pour conserver les images déjà ajoutées."}
                  </span>
                </div>
              )}
              {cle === "qualifications" && (
                <p className="field-hint">
                  La référence saisie reste privée et n’apparaît pas sur le profil public.
                </p>
              )}
              <div className="portfolio-form-actions">
                <button className="button" disabled={enregistrement} type="submit">
                  {enregistrement ? "Enregistrement…" : "Enregistrer"}
                </button>
                <button className="button button-secondary" onClick={fermerFormulaire} type="button">
                  Annuler
                </button>
              </div>
            </form>
          )}
        </section>
      ))}
    </section>
  );
}
