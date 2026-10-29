import type { Utilisateur } from "@/lib/types";

export function destinationEspace(utilisateur: Utilisateur) {
  if (!utilisateur.onboarding_termine) return "/bienvenue";

  const espaceActif =
    utilisateur.role_actif || utilisateur.roles_professionnels[0] || "";
  if (["candidat", "etudiant"].includes(espaceActif)) {
    return "/espace/candidatures";
  }
  if (["recruteur", "organisation"].includes(espaceActif)) {
    return "/espace/recruteur";
  }
  if (espaceActif === "professionnel") return "/espace/profil";
  return "/opportunites";
}
