export type Utilisateur = {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  telephone: string;
  pays: string;
  roles_professionnels: string[];
  role_actif: string;
  onboarding_termine: boolean;
};

export type Opportunite = {
  id: number;
  titre: string;
  description: string;
  organisation: number | null;
  organisation_nom: string | null;
  type: string;
  statut: string;
  ville: string;
  pays: string;
  budget_minimum: number | null;
  budget_maximum: number | null;
  devise: string;
  contrat: string;
  niveau_etudes: string;
  duree: string;
  livrables: string;
  urgence: string;
  motif_urgence: string;
  metier_nom: string | null;
  competences_detail: { id: number; nom: string }[];
  metier: number | null;
  competences: number[];
  images_url: string[];
  createur: number;
  createur_nom: string;
  cree_le: string;
  date_limite_candidature: string | null;
};

export type Candidature = {
  id: number;
  opportunite: number;
  candidat: number;
  candidat_nom: string;
  message: string;
  statut: string;
  version: number;
  cree_le: string;
  profil_partage: (Omit<ProfilPublic, "id"> & { id: number | null }) | null;
  historique: {
    statut_precedent: string;
    nouveau_statut: string;
    cree_le: string;
  }[];
};

export type Organisation = {
  id: number;
  nom: string;
  description: string;
  pays: string;
  ville: string;
  site_web: string;
  est_verifiee: boolean;
  cree_le: string;
};

export type Profil = {
  id: number;
  titre: string;
  biographie: string;
  ville: string;
  disponible: boolean;
  visible_publiquement: boolean;
  metier: number | null;
  metier_nom: string | null;
  competences_detail: {
    competence: number | null;
    competence_nom: string;
    competence_personnalisee?: string;
    niveau: string;
  }[];
};

export type ProfilPublic = {
  id: number;
  nom: string;
  photo_url: string | null;
  titre: string;
  biographie: string;
  ville: string;
  disponible: boolean;
  metier_nom: string | null;
  competences: {
    competence_nom: string;
    est_personnalisee: boolean;
    niveau: string;
  }[];
  experiences: {
    organisation: string;
    poste: string;
    description: string;
    debut: string;
    fin: string | null;
    est_attestee: boolean;
    entreprise_reference_statut_verification: string | null;
  }[];
  formations: {
    etablissement: string;
    intitule: string;
    debut: string;
    fin: string | null;
    est_verifiee: boolean;
    etablissement_reference_statut_verification: string | null;
    programme_reference_statut_verification: string | null;
  }[];
  realisations: {
    titre: string;
    description: string;
    lien: string;
    date_realisation: string | null;
    est_verifiee: boolean;
    images_url: string[];
  }[];
  qualifications: {
    nom: string;
    organisme: string;
    expiration: string | null;
    est_confirmee: boolean;
  }[];
};

export type ResultatEvaluationsPubliques = {
  nombre: number;
  moyenne: number | null;
  message: string | null;
  seuil: number;
  periode: {
    debut: string | null;
    fin: string | null;
  };
};

export type PortfolioExperience = {
  id: number;
  organisation: string;
  poste: string;
  description: string;
  debut: string;
  fin: string | null;
  est_attestee: boolean;
};

export type PortfolioFormation = {
  id: number;
  etablissement: string;
  intitule: string;
  debut: string;
  fin: string | null;
  est_verifiee: boolean;
};

export type PortfolioRealisation = {
  id: number;
  titre: string;
  description: string;
  lien: string;
  date_realisation: string | null;
  est_verifiee: boolean;
  images_url: string[];
};

export type PortfolioQualification = {
  id: number;
  nom: string;
  organisme: string;
  reference: string;
  expiration: string | null;
  est_confirmee: boolean;
};

export type Metier = { id: number; nom: string };
export type Competence = { id: number; nom: string; metiers?: number[] };

export type Page<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};
