# AKASHA v1 — Catalogue API, sécurité, logique métier et parcours UX/CX

**Version : 1.0 — contrat de conception avant implémentation**  
**Préfixe API :** `/api/v1` — les routes ci-dessous sont les suffixes après ce préfixe.  
**Cible technique indicative :** FastAPI + PostgreSQL. Le catalogue inclut la V1 et les routes prévues en V2/V3/V5, clairement étiquetées.

> Ce document constitue un contrat de conception exploitable. Les routes V2/V3/V5 doivent rester désactivées jusqu’à validation de leurs règles commerciales, prestataires externes et obligations du pays ciblé. Les exemples de champs sont le minimum contractuel proposé, pas une permission d’accepter n’importe quel JSON.

## 1. Comment passer de ce catalogue au code

Pour chaque route, crée d’abord le schéma Pydantic strict d’entrée/sortie, puis les tests d’autorisation et de machine d’états, ensuite le service métier, le repository et enfin l’intégration d’écran. Le router HTTP ne doit pas contenir toute la logique métier. Ne mappe jamais tout un body JSON directement vers une entité ORM : liste blanche explicite des champs modifiables.

### Conventions HTTP

- IDs : UUID opaques, non séquentiels. Un UUID n’est jamais un contrôle d’accès.
- Dates : ISO 8601, stockées en UTC; conserver le fuseau demandé pour les entretiens et disponibilités.
- Pagination : `cursor` + `limit`, défaut 20, maximum 100. Filtres et tris en liste blanche; éviter les offsets profonds.
- Argent : `amount` + `currency` ISO 4217. Le montant et la devise viennent du serveur pour les achats/paiements. Pour XOF/FCFA, l’unité usuelle des montants métier est le franc CFA.
- Concurrence : `ETag`/`If-Match` ou `expected_version` pour les opérations pouvant entrer en conflit.
- Idempotence : exiger `Idempotency-Key` pour candidature, acceptation d’une proposition, commande, abonnement, paiement et remboursement; stocker clé, résultat et portée.
- Les notifications partent après commit via une outbox/file de tâches. Un échec SMS/email/push ne doit pas annuler une candidature acceptée en base.

### Format d’erreur commun

```json
{
  "error": {
    "code": "APPLICATION_ALREADY_EXISTS",
    "message": "Vous avez déjà candidaté à cette offre.",
    "details": [{"field": "opportunity_id", "reason": "duplicate"}],
    "request_id": "uuid",
    "retryable": false
  }
}
```

Codes : `200` lecture ou mutation avec représentation, `201` création, `202` opération asynchrone, `204` sans corps, `400` requête mal formée, `401` authentification absente/invalide, `403` permission insuffisante, `404` ressource absente ou masquée pour éviter une fuite, `409` conflit de statut/concurrence, `410` jeton expiré, `422` validation de champs, `429` limite dépassée, `500` erreur inconnue sans détails internes, `503` dépendance temporairement indisponible.

## 2. Sécurité et permissions transversales

### Authentification
- Jeton d’accès court; refresh token rotatif, révocable côté serveur; détecter sa réutilisation et révoquer la famille concernée.
- Mot de passe haché avec Argon2id ou mécanisme recommandé et maintenu. OTP aléatoire, à durée courte, à usage unique, limité en tentatives/renvois, stocké sous forme hashée.
- La vérification d’un contact ne vaut ni vérification d’identité, ni validation d’un diplôme, ni vérification d’entreprise.
- Web : si cookies de session, `HttpOnly`, `Secure`, `SameSite`, protection CSRF, validation stricte d’Origin et rotation de session. Mobile : refresh token dans Keystore/Keychain, pas dans un stockage en clair.
- MFA/réauthentification récente pour les opérateurs, transfert de propriété, actions massives et opérations financières sensibles.

### Autorisation
- Autoriser selon **action + ressource + contexte**. Pour une candidature, vérifier l’adhésion active au bon espace organisationnel et que l’offre appartient réellement à cette organisation.
- Le compte vient de la session validée; un `account_id` reçu du client ne prouve jamais l’identité.
- Revalider compte, organisation, adhésion, permission et état métier à chaque action sensible. Une adhésion révoquée cesse d’autoriser immédiatement.
- Sérialiser une vue distincte pour public, propriétaire, candidat, recruteur, support et modérateur. Ne pas réutiliser une projection publique pour une fiche privée.
- Tester tous les accès objet contre BOLA/IDOR : remplacer un ID dans l’URL, body, fichier ou export ne doit pas permettre d’accéder aux données d’un autre utilisateur.

### Autres contrôles
- TLS, secrets hors Git, CORS limité aux domaines nécessaires, requêtes paramétrées, schémas Pydantic stricts, liste blanche pour tri/filtres et limites de taille.
- Rate limits sur connexion, OTP, recherche intensive, candidatures, invitations, messages, avis et signalements; combiner compte/IP/autres signaux.
- Téléversement : taille/type autorisés, détection du type réel, antivirus, stockage privé par défaut, URL signée courte, quota et révocation. Fichier non scanné = non téléchargeable.
- Logs sans mots de passe, OTP, jetons, données carte, pièces d’identité ni message privé intégral. Tracer avec `request_id` et audit métier.
- Webhook de paiement : signature vérifiée sur le corps brut, timestamp/rejeu vérifiés, ID d’événement dédupliqué, traitement durable avant réponse. Le retour du navigateur ne confirme jamais un paiement.

### Règles d’accès par acteur

| Acteur | Contrôle minimum |
|---|---|
| Public | Lit seulement contenus explicitement publiés et visibles. |
| Propriétaire | Gère ses ressources uniquement après vérification du lien propriétaire-ressource. |
| Candidat | Lit ses candidatures et la timeline qui lui est destinée; jamais les notes internes recruteur. |
| Recruteur | Adhésion active + permission explicite + ressource liée à la même organisation. |
| `OWNER` organisation | Gère adhésions et propriété; ne peut effacer l’audit ni contourner les règles plateforme. |
| `MODERATOR` | Traite les dossiers/contenus autorisés; pas d’accès implicite à la finance. |
| `TAXONOMY_MANAGER` | Gère le référentiel, pas les candidatures. |
| `SUPPORT` | Accès aux tickets et données strictement nécessaires; aucun droit implicite de sanction. |
| `PLATFORM_ADMIN` | Permissions séparées, MFA, audit; aucun compte admin partagé. |
| Worker/service | Identité technique dédiée, scopes minimaux et réseau restreint. |

## 3. Machines d’états à faire respecter côté serveur

- Compte : `PENDING_VERIFICATION → ACTIVE → SUSPENDED/CLOSED`.
- Organisation : `PENDING → ACTIVE → SUSPENDED/CLOSED`; une suspension bloque les nouvelles publications et modifications de contournement.
- Opportunité : `DRAFT → PUBLISHED ↔ PAUSED → CLOSED → ARCHIVED`; réouverture via commande contrôlée. L’état de modération est une dimension indépendante.
- Candidature : `SUBMITTED → IN_REVIEW → SHORTLISTED → INTERVIEW → OFFERED → HIRED`, avec sorties `REJECTED`/`WITHDRAWN`. La liste finale des transitions doit être une machine finie partagée backend/client.
- Demande de prestation V2 : `DRAFT → OPEN → IN_DISCUSSION → AWARDED/CLOSED/EXPIRED`; une seule proposition acceptée si la demande est exclusive.
- Paiement V3 : états autorisés par le PSP (`PENDING`, `AUTHORIZED`, `CAPTURED`, `FAILED`, `CANCELLED`, `REFUNDED`, etc.). Seule une confirmation serveur/webhook fiable détermine l’état final.

Toute transition crée un événement horodaté par le serveur avec acteur, état précédent, nouvel état, motif et corrélation. Les opérations concurrentes utilisent transaction, contrainte unique et verrouillage/version. L’interface ne doit jamais modifier directement un champ `status` pour contourner une commande métier.

## 4. Catalogue détaillé des endpoints

Chaque ligne précise : acteur, autorisation, payload/paramètres, logique et contraintes, écran consommateur, et comportement UX/CX. Les préfixes `/admin` et `/internal` ne sont jamais des permissions à eux seuls : l’autorisation reste vérifiée dans le service.

### 4.1 Santé, version et configuration publique

| Route | Acteur / accès | Champs | Logique et contraintes | Écran / UX-CX | Sortie |
|---|---|---|---|---|---|
| `GET /health/live` | Supervision; public minimal | Aucun | Indique seulement si le processus tourne; pas de dépendances ni secrets. | Aucun écran utilisateur. | `200 {status: ok}` |
| `GET /health/ready` | Supervision/réseau interne | Aucun | Vérifie les dépendances essentielles; ne révèle ni hôte, DSN ni traces. Restreindre en production si nécessaire. | Aucun écran utilisateur. | `200 {status: ready}` |
| `GET /public/config` | Public | Aucun | Retourne uniquement les options publiques : langues, pays actifs, version des conditions, fonctionnalités publiquement activées. | Démarrage, inscription, filtres. Ne pas imposer de mise à jour pour un simple changement de configuration non bloquant. | paramètres publics |

### 4.2 Authentification, compte et préférences

| Route | Acteur / autorisation | Corps / paramètres | Algorithme + contraintes | Écran / UX-CX | Sortie |
|---|---|---|---|---|---|
| `POST /auth/register` | Visiteur; public limité | Contact, mot de passe si activé, nom affiché, langue, versions/acceptation des conditions | Normaliser contact; unicité; créer compte et défi de vérification dans une transaction; déclencher l’envoi via file. Anti-énumération, limite IP/contact/appareil; compte non actif avant vérification. | Inscription. Garder les valeurs valides, erreurs près des champs, dire que la suite est une vérification sans révéler si un contact existe déjà. | compte `PENDING_VERIFICATION` |
| `POST /auth/login` | Visiteur; public limité | Contact + mot de passe ou preuve OTP | Vérifier identifiants et état; throttling adaptatif; créer session; MFA si policy/risque. Même message si contact inconnu ou mot de passe erroné; compte suspendu refusé. | Connexion. Proposer récupération sans confirmer si le compte existe. | jeton court + refresh rotatif |
| `POST /auth/refresh` | Refresh token valide | Refresh token, ou cookie sécurisé | Rotation; invalidation de l’ancien; réutilisation détectée = révocation de la famille. | Renouvellement silencieux; si échec, revenir à la connexion sans perdre brouillon local non sensible. | nouveaux jetons |
| `POST /auth/logout` | Session courante | Session/refresh courant | Révoque côté serveur, puis efface côté client; idempotent. | Menu profil > Déconnexion. | `204` |
| `POST /auth/logout-all` | Compte connecté; réauth/MFA si risque | Confirmation | Révoque toutes les sessions et trace l’action; ne permet pas de révoquer celles d’autrui. | Paramètres > Sécurité > Déconnecter tous les appareils. Afficher l’effet. | `204` |
| `POST /auth/verification-challenges` | Public limité | Contact, canal, contexte | Génère un OTP court, hashé, usage unique; applique limites d’essais/renvois et réponses uniformes. | Vérification de contact; compte à rebours et renvoi activable après délai. | `challenge_id`, `retry_after` |
| `POST /auth/verification-challenges/confirm` | Possesseur du défi | `challenge_id`, code | Vérifie hash, expiration, tentatives et contact; consomme atomiquement; active selon préconditions. | Écran Code. En cas d’expiration, offrir un nouveau code; ne pas effacer le formulaire entier. | contact vérifié/compte activé |
| `POST /auth/password-reset-requests` | Public limité | Email/téléphone | Crée lien/code si applicable, mais réponse identique si le compte n’existe pas; token hashé et limité. | Mot de passe oublié. Message neutre, pas d’énumération. | message générique |
| `POST /auth/password-resets` | Jeton reset valide | jeton, nouveau mot de passe | Consomme le token une fois, met à jour le hash et révoque les sessions selon policy. | Définir nouveau mot de passe; signaler les règles avant l’envoi. | `204` |
| `GET /auth/sessions` | Propriétaire connecté | `cursor`, `limit` | Liste contexte d’appareil approximatif et date d’activité, sans jetons ni données inutiles. | Sécurité > Sessions; différencier session courante. | sessions paginées |
| `DELETE /auth/sessions/{session_id}` | Propriétaire de session | `session_id` | Vérifie l’appartenance, révoque; peut masquer l’existence par `404`. | Sécurité > Sessions > Révoquer. | `204` |
| `GET /me` | Compte connecté | Aucun | Projection minimale du compte courant; exclure hachages, jetons et informations antifraude. | Bootstrap de toute zone authentifiée. | compte minimal |
| `PATCH /me` | Compte connecté | Nom affiché, langue, fuseau, coordonnées modifiables | Liste blanche; changer un contact crée un défi et ne remplace le contact vérifié qu’après confirmation. État/rôle/verification interdits ici. | Paramètres. Prévisualiser les changements nécessitant validation. | compte actualisé |
| `POST /me/close-account` | Propriétaire; réauth récente | Confirmation, motif facultatif | Vérifier obligations et engagements; désactiver accès, planifier anonymisation/rétention. Ne pas cascade-delete preuves, candidatures ou audit. | Sécurité > Fermer mon compte; écran de conséquences et confirmation non ambiguë. | clôture demandée |
| `GET /me/consents` | Compte connecté | Aucun | Historique par type/version/date; consentement marketing séparé des communications essentielles. | Paramètres > Confidentialité. | historique |
| `POST /me/consents` | Compte connecté | Type, décision, version de texte | Ajoute une preuve; n’écrase pas l’historique et utilise l’horodatage serveur. | Inscription/confidentialité; choix marketing non précoché par défaut selon policy. | consentement enregistré |
| `GET /me/notification-preferences` | Compte connecté | Aucun | Valeurs explicites + valeurs par défaut; séparer messages transactionnels et marketing. | Paramètres > Notifications. | préférences |
| `PATCH /me/notification-preferences` | Compte connecté | Canaux/catégories activés | Valide les catégories prises en charge; s’applique aux envois futurs, pas aux droits d’accès. | Interrupteurs simples; résultat enregistré visible immédiatement. | préférences mises à jour |
| `GET /me/privacy-settings` | Compte connecté | Aucun | Retourne uniquement les réglages existants dans la version active. | Profil > Confidentialité. | réglages |
| `PATCH /me/privacy-settings` | Compte connecté | Visibilité du profil, CV, indexation, champs publics supportés | Applique la policy à recherche et caches; les documents privés restent non publics. | Réglage de visibilité avec aperçu de profil public. | réglages mis à jour |

### 4.3 Profils, expériences, compétences, preuves, portfolio et fichiers

| Route | Acteur / autorisation | Corps / paramètres | Algorithme + contraintes | Écran / UX-CX | Sortie |
|---|---|---|---|---|---|
| `GET /me/person-profile` | Propriétaire | Aucun | Lit uniquement les informations personnelles non secrètes. | Profil > Informations personnelles. | profil |
| `PUT /me/person-profile` | Propriétaire | Nom affiché, photo, résumé, localisation publique facultative | Validation stricte; photo limitée et scannée; séparer coordonnées privées. | Assistant de profil; progression enregistrée. | profil actualisé |
| `GET /me/professional-profile` | Propriétaire | Aucun | Retourne valeurs déclarées et état de vérification distincts. | Profil professionnel. | profil + complétude |
| `PUT /me/professional-profile` | Propriétaire | Titre, résumé, métiers, localisation/remote, préférences, visibilité | Un profil professionnel V1 par compte; métiers actifs; calcul de complétude côté serveur. Un profil n’est pas obligatoire pour simplement explorer. | Formulaire par étapes, saisie sauvegardée, champs manquants signalés. | profil actualisé |
| `POST /me/professional-profile/activate` | Propriétaire; compte actif vérifié | Confirmation | Vérifie complétude minimale et statut du compte, active l’indexation selon visibilité. | Profil > Rendre visible; préciser le public qui peut le voir. | profil actif |
| `POST /me/professional-profile/deactivate` | Propriétaire | Confirmation, motif facultatif | Masque des nouveaux résultats; ne modifie pas les candidatures envoyées ni ne ferme le compte. | Profil > Suspendre visibilité. | profil masqué |
| `GET /me/professional-profile/experiences` | Propriétaire | Curseur/limite | Pagination par date décroissante; données du propriétaire seulement. | Profil > Expériences. | liste paginée |
| `POST /me/professional-profile/experiences` | Propriétaire | Titre, description, dates, en cours, employeur facultatif, visibilité | `end_date >= start_date`; si en cours, `end_date=null`; ne pas prétendre que l’expérience est vérifiée. | Ajouter expérience; les erreurs de date pointent le champ concerné. | expérience créée |
| `PATCH /me/professional-profile/experiences/{experience_id}` | Propriétaire de l’expérience | Champs modifiables | Vérifie ownership + dates; impossible de modifier statut de vérification. | Éditer expérience. | expérience |
| `DELETE /me/professional-profile/experiences/{experience_id}` | Propriétaire | Aucun | Retire du profil courant; conserve snapshot si déjà soumis dans une candidature. | Retirer avec confirmation si contenu déjà public. | `204` |
| `GET /me/professional-profile/skills` | Propriétaire | Curseur/limite | Retourne compétence et niveau déclaré. | Profil > Compétences. | liste |
| `POST /me/professional-profile/skills` | Propriétaire | `skill_id`, niveau déclaré, années facultatives | Compétence active; unicité profil+skill; niveau dans échelle contrôlée; aucune auto-vérification. | Sélecteur depuis le référentiel; permettre recherche sans créer de doublon. | association créée |
| `PATCH /me/professional-profile/skills/{skill_id}` | Propriétaire de l’association | Niveau/années | Modifie uniquement les champs déclaratifs. | Ajuster niveau compétence. | association |
| `DELETE /me/professional-profile/skills/{skill_id}` | Propriétaire de l’association | Aucun | Retire l’association, pas la compétence globale ni les snapshots historiques. | Retirer compétence. | `204` |
| `GET /me/professional-profile/credentials` | Propriétaire | Curseur/limite | Distingue déclaration, vérification et expiration; accès restreint aux documents complets. | Profil > Diplômes et certifications. | liste |
| `POST /me/professional-profile/credentials` | Propriétaire | Type, nom, émetteur, pays, dates, `file_id` privé | Fichier appartenant au compte et `READY`; statut initial `DECLARED`; `VERIFIED` interdit depuis le client. | Ajouter preuve; montrer « déclaration reçue » et non « validée ». | preuve déclarée |
| `PATCH /me/professional-profile/credentials/{credential_id}` | Propriétaire | Champs déclaratifs | Si le contenu change après vérification, repasser en revue; décision du vérificateur inaltérable par ce endpoint. | Modifier justificatif; expliquer si une nouvelle vérification est requise. | preuve actualisée |
| `DELETE /me/professional-profile/credentials/{credential_id}` | Propriétaire | Aucun | Masque la preuve et applique la rétention; dossier d’audit gardé si revue en cours. | Retirer justificatif. | `204` |
| `POST /me/professional-profile/credentials/{credential_id}/verification-requests` | Propriétaire | Informations complémentaires | Contrôle les champs par pays/type et ouvre une file de vérification humaine/système habilité. | Certification > Faire vérifier; montrer l’état et les éventuelles pièces manquantes. | dossier ouvert |
| `GET /me/professional-profile/portfolio` | Propriétaire | Curseur/limite | Liste seulement le portfolio du compte courant. | Profil > Portfolio. | liste |
| `POST /me/professional-profile/portfolio` | Propriétaire | Titre, description, URL ou `file_id`, visibilité | Rejette URLs dangereuses; scanne fichier; modération possible. | Ajouter réalisation; prévisualiser le rendu public. | élément créé |
| `PATCH /me/professional-profile/portfolio/{item_id}` | Propriétaire | Titre, description, URL, visibilité | Ownership, revalidation des liens/fichiers, audit lors d’un changement de visibilité. | Modifier réalisation. | élément actualisé |
| `DELETE /me/professional-profile/portfolio/{item_id}` | Propriétaire | Aucun | Retire de la page publique et invalide les caches; conserve preuves d’abus si nécessaire. | Supprimer réalisation. | `204` |
| `GET /professionals/{professional_id}` | Public ou utilisateur | Aucun | Projection publique selon visibilité et statut; jamais de contact privé, CV privé, adresse précise, notes internes ou pièce d’identité. | Résultat > Profil professionnel. | profil public filtré |
| `POST /files/upload-intents` | Utilisateur avec droit sur la ressource | Nom, taille prévue, MIME déclaré, catégorie | Prépare un stockage privé et une URL courte; quota et types limités; MIME déclaré non fiable. | CV, certification, photo, portfolio; progression visible. | `file_id` + URL temporaire |
| `POST /files/{file_id}/complete-upload` | Propriétaire du fichier | Taille réelle, hash facultatif | Vérifie stockage, type réel, hash et antivirus; `SCANNING` jusqu’à résultat; le client ne déclare jamais lui-même `READY`. | Après upload; afficher « vérification en cours » si asynchrone. | `READY`/`REJECTED` |
| `GET /files/{file_id}/download-url` | Utilisateur autorisé sur le parent | Aucun | Vérifie l’autorisation sur candidature/profil/dossier, pas simplement le file_id; URL signée courte. | Télécharger CV ou preuve autorisée. | URL/stream temporaire |

### 4.4 Référentiel métiers, spécialités et compétences

| Route | Acteur / autorisation | Corps / paramètres | Algorithme + contraintes | Écran / UX-CX | Sortie |
|---|---|---|---|---|---|
| `GET /taxonomy/categories` | Public, données actives | Parent, langue, curseur/limite | Hiérarchie stable; catégories désactivées réservées aux gestionnaires. | Filtres métier/inscription/profil. | catégories |
| `GET /taxonomy/professions` | Public | `q`, catégorie, pays, langue, curseur/limite | Recherche normalisée; renvoie identifiants stables et synonymes; zéro résultat explicite. | Autocomplétion métier. | liste métiers |
| `GET /taxonomy/professions/{profession_id}` | Public si actif | Aucun | Définition, parent/enfants, compétences utiles; les règles réglementaires sont localisées, sourcées et datées. | Fiche métier / profil. | fiche métier |
| `GET /taxonomy/skills` | Public | `q`, métier, curseur/limite | Recherche nom/synonymes; seules compétences actives proposées. | Sélection compétences. | compétences |
| `GET /taxonomy/countries/{country_code}/profession-rules` | Public sur données approuvées | `profession_id`, type de qualification | Renvoie uniquement règles revues; si non configuré, l’indiquer clairement au lieu d’inventer une obligation. | Fiche métier / preuve requise. | règles configurées |
| `POST /admin/taxonomy/categories` | Gestionnaire taxonomie | Code, libellés, parent | Code unique, parent existant, absence de cycle, audit. | Back-office > Ajouter catégorie. | catégorie créée |
| `PATCH /admin/taxonomy/categories/{category_id}` | Gestionnaire taxonomie | Libellés, description, parent, statut permis | Valide la hiérarchie; désactiver plutôt que supprimer une catégorie référencée. | Back-office > Catégorie. | catégorie mise à jour |
| `POST /admin/taxonomy/professions` | Gestionnaire taxonomie | Code, libellés, description, parent/catégories, indicateurs pays | Détecte doublons; absence de cycle; n’ajoute pas de règles légales non revues. | Back-office > Ajouter métier. | métier créé |
| `PATCH /admin/taxonomy/professions/{profession_id}` | Gestionnaire taxonomie | Libellés, description, parent/catégories, visibilité | Identifiant stable; préserver références historiques; réindexer la recherche. | Back-office > Métier. | métier mis à jour |
| `POST /admin/taxonomy/professions/{profession_id}/deactivate` | Gestionnaire taxonomie | Motif, confirmation | Empêche les nouvelles sélections, conserve usages historiques, audit. | Back-office > Désactiver métier. | métier inactif |
| `POST /admin/taxonomy/professions/{profession_id}/merge` | Gestionnaire taxonomie habilité | Métier cible, mapping, motif | Prévisualiser puis migrer les associations en transaction; conserver redirection/historique. | Back-office > Fusionner doublon. | rapport de fusion |
| `POST /admin/taxonomy/skills` | Gestionnaire taxonomie | Code, libellés, synonymes, métiers | Normalise synonymes, détecte doublons, code stable. | Back-office > Compétences. | compétence créée |
| `PATCH /admin/taxonomy/skills/{skill_id}` | Gestionnaire taxonomie | Libellés, synonymes, métiers, statut | Valide associations et réindexe; préserver références historiques. | Back-office > Compétence. | compétence mise à jour |
| `POST /admin/taxonomy/skills/{skill_id}/deactivate` | Gestionnaire taxonomie | Motif | Cache aux nouveaux usages; pas de suppression physique si référencée; audit. | Back-office > Désactiver compétence. | compétence inactive |

### 4.5 Organisations, adhésions et invitations

Tout appel réalisé au nom d’une organisation vérifie simultanément : compte actif, adhésion active, permission et appartenance de la ressource à cette organisation.

| Route | Acteur / autorisation | Corps / paramètres | Algorithme + contraintes | Écran / UX-CX | Sortie |
|---|---|---|---|---|---|
| `POST /organizations` | Compte actif | Nom, type, pays, identifiants/description facultatifs | Création organisation + adhésion `OWNER` dans une même transaction; déclenche vérification éventuelle. Pas d’auto-attribution du badge vérifié. | « Créer un espace entreprise »; expliquer la différence entre espace créé et organisation vérifiée. | organisation + adhésion OWNER |
| `GET /me/organizations` | Compte connecté | `cursor`, `limit` | Renvoie seulement les adhésions actives et rôle effectif. | Sélecteur d’organisation. | liste paginée |
| `GET /organizations/{organization_id}` | Public ou membre autorisé | Aucun | Vue publique minimale ou vue interne selon permission. | Page entreprise / paramètres. | organisation filtrée |
| `PATCH /organizations/{organization_id}` | Membre avec `organization.update` | Nom, description, secteur, site, localisation publique, logo | Vérifie scope organisation; changement de raison sociale peut déclencher une revue; logo scanné. | Paramètres organisation; avertir si une donnée doit être revalidée. | organisation |
| `POST /organizations/{organization_id}/verification-requests` | OWNER/ADMIN habilité | Type de preuve, `file_ids`, pays | Crée un dossier de vérification; pièces privées; le client ne choisit pas le statut `VERIFIED`. | Paramètres > Vérification. | dossier `PENDING_REVIEW` |
| `GET /organizations/{organization_id}/members` | Membre avec `organization.members.read` | État, curseur/limite | Liste minimisée des adhérents; ne pas exposer leurs contacts privés. | Paramètres > Membres. | membres paginés |
| `POST /organizations/{organization_id}/invitations` | OWNER/ADMIN avec `members.invite` | Contact, rôle/scopes autorisés, expiration | Jeton imprévisible; date d’expiration; scopes limités à ceux du créateur; aucun OWNER via invitation ordinaire. | Paramètres > Inviter. Afficher statut d’envoi et actions possibles. | invitation `PENDING` |
| `POST /organization-invitations/{invitation_id}/accept` | Contact invité authentifié | Token si nécessaire | Vérifie destinataire, expiration, compte actif et unicité; activation atomique de l’adhésion. | Invitation reçue > Accepter. | adhésion active |
| `POST /organization-invitations/{invitation_id}/decline` | Destinataire | Motif facultatif | Refuse l’invitation sans toucher aux autres invitations; ne révèle pas l’organisation à un non-destinataire. | Invitation reçue > Refuser. | invitation `DECLINED` |
| `PATCH /organizations/{organization_id}/members/{account_id}` | OWNER/ADMIN autorisé | Nouveau rôle/scopes, motif | Empêche auto-escalade, compare privilèges du demandeur et de la cible; révocation immédiate des anciens droits; audit. | Membres > Permissions. | adhésion mise à jour |
| `DELETE /organizations/{organization_id}/members/{account_id}` | OWNER/ADMIN ou départ volontaire | Confirmation, motif facultatif | Désactive l’adhésion; ne supprime pas les annonces/candidatures créées; impossible de retirer le dernier OWNER. | Membres > Retirer. | `204` |
| `POST /organizations/{organization_id}/ownership-transfer` | OWNER actuel; réauth/MFA | `new_owner_account_id`, confirmation | Verrouille l’organisation; nouveau propriétaire doit être actif/habilité; transfert atomique et audit. | Paramètres > Transférer propriété; afficher les conséquences irréversibles. | transfert réalisé |
| `GET /organizations/{organization_id}/invitations` | OWNER/ADMIN habilité | État, curseur/limite | Liste seulement les invitations de l’organisation; jamais renvoyer le token complet. | Paramètres > Invitations. | invitations |
| `POST /organization-invitations/{invitation_id}/resend` | Inviteur habilité | Aucun | Seulement invitation valide; nouvelle preuve ou renvoi après délai; rate limit. | Invitations > Renvoyer. | état d’envoi |
| `DELETE /organization-invitations/{invitation_id}` | Inviteur habilité | Aucun | Annule et invalide le jeton; n’altère pas une adhésion déjà activée. | Invitations > Annuler. | `204` |

### 4.6 Opportunités, offres d’emploi et missions

Les transitions d’état utilisent des commandes dédiées. Le client ne doit jamais pouvoir publier une offre simplement en envoyant `status=PUBLISHED` dans un PATCH.

| Route | Acteur / autorisation | Corps / paramètres | Algorithme + contraintes | Écran / UX-CX | Sortie |
|---|---|---|---|---|---|
| `GET /opportunities` | Public; annonces visibles | `q`, type, métier, skills, pays/ville, remote, contrat, salaire, curseur/limite, tri whitelisté | Filtre `PUBLISHED`, échéance, visibilité puis classe. Salaire inconnu distinct de zéro; résultat vide explicite. | Accueil, résultats et filtres; conserver filtres dans URL et afficher filtres actifs. | `items`, `next_cursor` |
| `GET /opportunities/{opportunity_id}` | Public ou gestionnaire autorisé | Aucun | Projection publique pour annonce publiée; brouillon visible seulement aux autorisés; une annonce clôturée n’est pas candidatable. | Détail offre/partage. | détail filtré |
| `POST /opportunities` | Compte actif, ou membre org autorisé | Type, titre, description, métier/skills, lieu/remote, contrat, salaire/budget, dates, `organization_id` facultatif | Détermine le publieur depuis la session/adhésion; crée un brouillon du type correct; champs conditionnels validés. | Publier une offre > formulaire adapté au type; sauvegarder brouillon avant prévisualisation. | `DRAFT` + ID |
| `PATCH /opportunities/{opportunity_id}` | Auteur ou membre avec permission | Champs modifiables du type | Vérifie ownership/scope et état; valide champs du type; pas de modification du statut, données de paiement ou décisions modération. | Mes offres > Modifier; montrer les champs manquants et garder les valeurs. | annonce |
| `POST /opportunities/{opportunity_id}/publish` | Auteur/recruteur habilité | Confirmation | Vérifie profil et org actifs, complétude, date limite future, modération; transition atomique et indexation. | Prévisualisation > Publier; expliquer si revue avant publication. | `PUBLISHED` |
| `POST /opportunities/{opportunity_id}/pause` | Auteur/recruteur | Motif facultatif | Valide état `PUBLISHED`; retire des résultats, conserve candidatures; distinct d’une sanction plateforme. | Mes offres > Suspendre. | `PAUSED` |
| `POST /opportunities/{opportunity_id}/resume` | Auteur/recruteur | Aucun | Revalide échéance, compte/org, complétude et modération avant réindexation. | Mes offres > Reprendre; afficher la raison d’un refus éventuel. | `PUBLISHED` |
| `POST /opportunities/{opportunity_id}/close` | Auteur/recruteur | Motif, confirmation | Arrête nouvelles candidatures; conserve messages/historique; envoie notifications après commit. | Mes offres > Clôturer avec confirmation. | `CLOSED` |
| `POST /opportunities/{opportunity_id}/reopen` | Auteur/recruteur | Nouvelle date limite éventuelle, confirmation | Revalide toutes les préconditions; jamais de contournement d’une sanction de modération. | Mes offres > Rouvrir; indiquer si le contenu doit être revu. | `PUBLISHED` ou `DRAFT` |
| `POST /opportunities/{opportunity_id}/archive` | Auteur/recruteur | Aucun | Masque des vues courantes mais conserve données et historiques. | Mes offres > Archiver. | `ARCHIVED` |
| `DELETE /opportunities/{opportunity_id}` | Auteur, brouillon non publié seulement | Confirmation | Suppression physique seulement si aucune dépendance historique; sinon archivage obligatoire. | Éditeur > Supprimer brouillon; demander confirmation. | `204` |
| `GET /me/opportunities` | Utilisateur connecté | État, type, curseur/limite | Filtre les annonces individuelles du compte courant; ne remplace pas la liste de l’espace organisation. | Tableau > Mes annonces personnelles. | annonces |
| `GET /organizations/{organization_id}/opportunities` | Public ou membre avec scope | État pour membre, curseur/limite | Vue publique : publiées seulement; vue interne selon permission. | Espace organisation > Offres. | annonces visibles |
| `GET /organizations/{organization_id}/opportunities/{opportunity_id}/stats` | Recruteur avec `opportunity.stats.read` | Période | Agrège vues/candidatures/conversions de l’annonce dans cette organisation. | Tableau recruteur > Statistiques. | statistiques agrégées |
| `POST /opportunities/{opportunity_id}/duplicate` | Auteur/recruteur autorisé | Nouveau titre/dates facultatifs | Copie seulement champs clonables; remet en `DRAFT`; ne copie ni candidats, ni statistiques, ni sanction. | Mes offres > Dupliquer; ouvrir l’éditeur du nouveau brouillon. | nouveau brouillon |

### 4.7 Recherche et recommandations

| Route | Acteur / autorisation | Paramètres | Algorithme + contraintes | Écran / UX-CX | Sortie |
|---|---|---|---|---|---|
| `GET /search` | Public, données visibles | `q`, types, filtres, curseur/limite | Normaliser requête, appliquer visibilité, filtrer, puis classer; ne renvoyer que les champs publics. | Recherche globale; conserver requête et filtres pour retour arrière. | groupes de résultats |
| `GET /search/opportunities` | Public | Métier, skills, pays/ville, remote, contrat, salaire/date, tri et curseur | Index texte + filtres normalisés; aucun tri SQL libre; inconnues non assimilées à zéro. | Recherche d’emploi. | résultats + filtres actifs |
| `GET /search/professionals` | Utilisateur/recruteur selon contexte | `q`, métier, skills, lieu, disponibilité, expérience, curseur | Filtre visibilité avant ranking; recherche candidate privée seulement avec scope recruteur; anti-scraping et quotas. | Annuaire / recherche candidats. | profils visibles |
| `GET /me/recommendations/opportunities` | Compte connecté | Curseur/limite | Score indicatif métier/skills/localisation/préférences/date; filtres d’accès avant classement; raisons de correspondance explicables. | Accueil > Pour vous; proposer ajustement des préférences si vide. | opportunités recommandées |
| `GET /me/recommendations/professionals` | Client/recruteur autorisé; V2 prestataires | Besoin ou `opportunity_id`, curseur/limite | Utilise uniquement données pertinentes et visibles; la pertinence ne donne jamais droit aux coordonnées privées. | Recommandations de candidats/prestataires. | profils classés |

### 4.8 Candidatures et recrutement

Une candidature conserve un snapshot des données envoyées. Modifier le profil après candidature ne réécrit pas ce dossier historique.

| Route | Acteur / autorisation | Corps / paramètres | Algorithme + contraintes | Écran / UX-CX | Sortie |
|---|---|---|---|---|---|
| `POST /opportunities/{opportunity_id}/applications` | Candidat, compte actif et profil minimal | CV/file facultatif si autorisé, lettre, réponses aux questions, consentement | Relire/verrouiller l’offre; vérifier état/délai/postes/profil/doublon; créer snapshot et événement dans transaction; Idempotency-Key. | Détail > Postuler; afficher champs manquants avant envoi; confirmation après commit. | candidature `SUBMITTED` |
| `GET /me/applications` | Candidat propriétaire | État, période, curseur/limite | Filtre uniquement le compte courant; cache les notes internes. | Mes candidatures; afficher progression et prochaine action disponible. | candidatures paginées |
| `GET /me/applications/{application_id}` | Candidat propriétaire | Aucun | Vérifier propriétaire; renvoyer snapshot, état et timeline visible au candidat. | Mes candidatures > Détail. | détail filtré |
| `POST /applications/{application_id}/withdraw` | Candidat propriétaire | Motif facultatif, confirmation | Vérifie que l’état permet retrait; transition historisée; idempotente. | Détail candidature > Retirer; avertir des conséquences avant confirmation. | `WITHDRAWN` |
| `GET /organizations/{organization_id}/applications` | Recruteur habilité | Offre, statut, date, skills, curseur/limite | Vérifie membership + permission + appartenance des offres; filtre côté serveur. | Tableau recruteur > Candidatures; recherche/sort uniquement sur champs autorisés. | liste paginée |
| `GET /organizations/{organization_id}/applications/{application_id}` | Recruteur de l’organisation de l’offre | Aucun | Renvoie données partagées pour cette candidature, jamais le dossier d’un autre employeur. | Candidatures > Détail candidat. | dossier recruteur |
| `POST /organizations/{organization_id}/applications/{application_id}/transitions` | Recruteur avec `application.manage` | `target_status`, `reason_code`, message éventuel, `expected_version` | Vérifie machine d’états et version; inscrit acteur/ancien/nouvel état/motif; notifie après commit. | Boutons Présélectionner/Inviter/Refuser/Offrir; demander confirmation sur action terminale. | nouvel état + timeline |
| `POST /organizations/{organization_id}/applications/{application_id}/notes` | Recruteur avec permission notes | Texte, catégorie | Stocke note interne distincte du message candidat; contrôle longueur et journalise accès. | Détail candidature > Notes internes. | note privée |
| `POST /organizations/{organization_id}/applications/{application_id}/shortlist` | Recruteur autorisé | Liste/lot facultatif | Ajoute à la présélection sans transition implicite vers entretien; idempotente. | Candidatures > Présélection. | statut de présélection |
| `GET /me/applications/{application_id}/timeline` | Candidat propriétaire | Aucun | Vérifie la propriété de la candidature et renvoie uniquement les événements destinés au candidat; exclut notes internes/recruteur et détails antifraude. | Mes candidatures > Détail > Historique. | événements visibles au candidat |
| `GET /organizations/{organization_id}/applications/{application_id}/timeline` | Recruteur de l’organisation | Aucun | Vérifie organisation, adhésion et permission; retourne les événements de recrutement visibles aux membres autorisés, avec les notes internes accessibles séparément selon le scope. | Tableau recruteur > Candidature > Historique. | événements recruteur filtrés |
| `POST /organizations/{organization_id}/applications/{application_id}/interview-invitations` | Recruteur avec `interview.create` | Date/heure, fuseau, durée, canal, instructions | Vérifie état candidature, heure future, participants; stocke UTC + fuseau et notifie après commit. | Détail candidature > Planifier entretien; montrer heure dans le fuseau local et celui de l’invitation. | entretien + invitation |
| `POST /organizations/{organization_id}/applications/{application_id}/export` | Recruteur avec permission export | Format, champs et filtres autorisés | Construit fichier privé, crée audit et URL temporaire; gros exports asynchrones. | Candidatures > Exporter; montrer le périmètre avant lancement. | export temporaire |

### 4.9 Entretiens et calendrier

| Route | Acteur / autorisation | Corps / paramètres | Algorithme + contraintes | Écran / UX-CX | Sortie |
|---|---|---|---|---|---|
| `GET /organizations/{organization_id}/interviews` | Recruteur autorisé | Dates, état, curseur/limite | Filtre les entretiens liés aux candidatures de l’organisation. | Calendrier recrutement. | liste d’entretiens |
| `POST /interviews` | Recruteur habilité sur candidature | `application_id`, participants, `start_at`, fuseau, durée, canal, instructions | Valide candidature, participants et heure; crée entretien/invitations transactionnellement. | Candidature ou calendrier > Planifier. | entretien créé |
| `GET /interviews/{interview_id}` | Candidat participant ou recruteur habilité | Aucun | Vue selon rôle; notes internes exclues côté candidat; vérifier participation. | Calendrier > Détail entretien. | entretien filtré |
| `PATCH /interviews/{interview_id}` | Recruteur habilité | Créneau, durée, canal, instructions, participants permis | Valide état; historique des modifications; notifications de replanification après commit. | Calendrier > Modifier; présenter ancien et nouveau créneau. | entretien modifié |
| `POST /interviews/{interview_id}/cancel` | Participant ou recruteur selon règle | Raison, confirmation | Vérifie rôle/état; annule et notifie; idempotent. | Calendrier > Annuler; confirmation si annulation proche de l’heure. | `CANCELLED` |
| `POST /interviews/{interview_id}/feedback` | Recruteur habilité | Note structurée facultative, note interne, recommandation | Stocke un retour interne distinct du statut de candidature. | Entretien > Évaluation recruteur. | feedback privé |

### 4.10 Messagerie, notifications et blocage

| Route | Acteur / autorisation | Corps / paramètres | Algorithme + contraintes | Écran / UX-CX | Sortie |
|---|---|---|---|---|---|
| `GET /me/conversations` | Participant authentifié | Non lus, contexte, curseur/limite | Retourne uniquement conversations du compte, avec dernier message autorisé. | Boîte de réception; écran vide propose un chemin contextualisé, pas un contact arbitraire. | conversations |
| `POST /conversations` | Utilisateur avec relation métier permise | Participants, type/ID de contexte, message initial facultatif | Vérifie contexte, permissions des deux côtés et blocages; réutilise conversation existante si unicité définie. | Profil/offre/candidature > Contacter. | conversation ID |
| `GET /conversations/{conversation_id}` | Participant actif | Aucun | Vérifie participation et accès au contexte; révocation d’adhésion respectée pour contexte d’entreprise. | Boîte de réception > Conversation. | métadonnées |
| `GET /conversations/{conversation_id}/messages` | Participant actif | Curseur/limite, curseur avant facultatif | Messages de cette conversation uniquement, ordre stable, pièces contrôlées. | Historique de conversation; chargement progressif. | messages paginés |
| `POST /conversations/{conversation_id}/messages` | Participant actif, compte non suspendu | Texte, fichiers autorisés, `client_message_id` | Vérifie participation, blocage, quota et contexte; persist puis notification asynchrone; idempotence client. | Composer/envoyer; état envoyé/échec et reprise sans doublon. | message enregistré |
| `POST /conversations/{conversation_id}/read` | Participant actif | `last_read_message_id` | Avance le curseur de lecture seulement dans cette conversation; idempotent. | Ouverture conversation. | `204`/état lu |
| `POST /conversations/{conversation_id}/attachments` | Participant et propriétaire fichier | `file_id`, message facultatif | Fichier doit être `READY`, appartenir au compte et être lié à la conversation avec accès privé. | Conversation > Joindre. | attachement |
| `GET /me/blocks` | Compte connecté | Curseur/limite | Liste seulement blocages initiés par le compte courant. | Paramètres > Comptes bloqués. | liste |
| `POST /me/blocks` | Compte connecté | `account_id`, motif facultatif | Empêche messages/contacts selon policy; ne peut bloquer soi-même; idempotent; ne détruit pas les preuves d’un litige. | Profil/conversation > Bloquer; expliquer l’effet. | blocage actif |
| `DELETE /me/blocks/{account_id}` | Propriétaire du blocage | Aucun | Désactive le blocage; ne restaure pas automatiquement les échanges retirés. | Comptes bloqués > Débloquer. | `204` |
| `POST /messages/{message_id}/report` | Participant autorisé | Motif, commentaire | Crée un report; ne sanctionne pas automatiquement; protéger l’identité du déclarant selon policy. | Menu message > Signaler. | `report_id` |
| `GET /me/notifications` | Destinataire | Non lus, catégorie, curseur/limite | Notifications du compte courant uniquement; texte ne contient pas de jeton/donnée secrète. | Centre de notifications. | notifications |
| `POST /me/notifications/{notification_id}/read` | Destinataire propriétaire | Aucun | Vérifie le destinataire et marque lue; idempotent. | Notification > Ouvrir/marquer lue. | état lu |
| `POST /me/notifications/read-all` | Compte connecté | Catégorie facultative | Met à jour les notifications de soi seulement; traitement par lots pour grands volumes. | Centre > Tout marquer lu. | nombre modifié |
| `GET /me/activity` | Compte connecté | Curseur/limite | Timeline des événements visibles, distincte des notifications et messages; projection par rôle. | Accueil > Activité. | activités paginées |
| `POST /internal/notification-deliveries/{delivery_id}/retry` | Worker interne uniquement | ID livraison | Relance seulement les livraisons réessayables via file/idempotence; aucun accès navigateur/mobile. | Outil d’exploitation. | état livraison |

### 4.11 Signalements, modération et support

| Route | Acteur / autorisation | Corps / paramètres | Algorithme + contraintes | Écran / UX-CX | Sortie |
|---|---|---|---|---|---|
| `POST /reports` | Utilisateur authentifié | Type/ID cible, motif structuré, commentaire, preuve facultative | Cible signalable et visible; déduplication prudente; signaler n’applique aucune sanction automatiquement. | Menu > Signaler; expliquer que le signalement sera examiné. | report `OPEN` |
| `GET /me/reports` | Déclarant | Curseur/limite | Affiche état et résolution publiable, sans notes ni identité des autres déclarants. | Paramètres > Mes signalements. | rapports |
| `GET /admin/reports` | Modérateur avec permission | État, motif, priorité, date, curseur/limite | File filtrée; données personnelles minimisées; accès audité si nécessaire. | Back-office > File modération. | dossiers paginés |
| `GET /admin/reports/{report_id}` | Modérateur habilité | Aucun | Charge les données indispensables uniquement; respect conflit d’intérêt; documents privés si nécessaire et permis. | Back-office > Dossier. | dossier filtré |
| `POST /admin/reports/{report_id}/claim` | Modérateur habilité | Aucun | Assigne/verrouille le dossier pour éviter deux décisions contradictoires; audit. | Dossier > Prendre en charge. | dossier assigné |
| `POST /admin/reports/{report_id}/decisions` | Modérateur habilité | Décision, motif, note interne, message utilisateur, durée éventuelle | Valide actions possibles; sanction et clôture historisées; notification après commit. | Dossier > Décider; afficher au déclarant/concerné seulement les motifs appropriés. | décision + action |
| `POST /admin/accounts/{account_id}/suspensions` | Modérateur/admin autorisé | Motif, durée, message, confirmation | Invalide sessions et bloque immédiatement les actions métier; motif obligatoire; action auditée. | Back-office > Compte > Suspendre. | compte suspendu |
| `POST /admin/accounts/{account_id}/restore` | Modérateur/admin habilité | Motif, confirmation | Vérifie qu’aucune sanction active ne reste; ne réactive pas les contenus modérés automatiquement. | Compte > Restaurer. | compte restauré |
| `POST /admin/opportunities/{opportunity_id}/moderation-actions` | Modérateur | Action, motif, note interne | Masque/rétablit/retire selon une machine de modération séparée; invalide caches et index; audit. | Annonce signalée > Action. | action tracée |
| `POST /admin/credentials/{credential_id}/verification-decisions` | Vérificateur habilité | Décision, motif, notes preuve, expiration confirmée | Utilise grille pays/type; enregistre décideur et date; la décision ne peut pas être modifiée par le propriétaire du profil. | Back-office > Vérifications. | `VERIFIED/REJECTED/NEEDS_INFO` |
| `GET /support/tickets` | Utilisateur | État, curseur/limite | Tickets du compte courant; notes internes exclues. | Aide > Mes demandes. | tickets |
| `POST /support/tickets` | Utilisateur actif | Sujet, catégorie, message, fichiers | Validation de longueur et pièces; routing vers équipe; anti-spam. | Aide > Contacter support. | ticket `OPEN` |
| `GET /support/tickets/{ticket_id}` | Propriétaire ou support | Aucun | Vue différente selon rôle; pas de notes internes côté client. | Aide > Détail ticket. | ticket filtré |
| `POST /support/tickets/{ticket_id}/messages` | Propriétaire ou agent support | Message, pièces jointes | Vérifie accès, ajoute réponse dans le bon canal et notifie l’autre partie. | Ticket > Répondre. | message ajouté |

### 4.12 Administration, audit et indicateurs

| Route | Acteur / autorisation | Corps / paramètres | Algorithme + contraintes | Écran / UX-CX | Sortie |
|---|---|---|---|---|---|
| `GET /admin/accounts` | Support/admin permissionné | Recherche, état, vérification, période, curseur/limite | Liste blanche filtres; projection minimale; masquage contacts; contrôle d’export. | Back-office > Comptes. | résultats paginés |
| `GET /admin/accounts/{account_id}` | Support/admin permissionné | Aucun | Dossier limité à la mission de l’agent; données sensibles séparées et auditées. | Back-office > Compte. | compte filtré |
| `GET /admin/organizations` | Admin permissionné | Recherche, pays, état, vérification, curseur/limite | Minimise la donnée et sépare accès profil/justificatifs privés. | Back-office > Organisations. | liste |
| `POST /admin/organizations/{organization_id}/status-transitions` | Admin habilité | État cible, motif, confirmation | Machine d’états; suspension bloque publication; historique conservé; audit complet. | Organisation > Suspendre/réactiver/fermer. | organisation + audit |
| `GET /admin/audit-logs` | Auditeur/admin avec `audit.read` | Acteur, action, cible, période, curseur/limite | Lecture seule append-only; jamais de route d’édition/suppression des logs. | Back-office > Audit. | événements paginés |
| `GET /admin/dashboard/overview` | Admin/analyste avec permission | Période, pays, version produit | Indicateurs versionnés; rendre visibles définitions/dénominateurs; minimiser ré-identification. | Back-office > Vue globale. | métriques agrégées |
| `GET /organizations/{organization_id}/analytics/recruitment` | Recruteur autorisé | Période, offre | Agrège uniquement les annonces de l’organisation; événements incomplets identifiés. | Recruteur > Analytics. | statistiques agrégées |
| `GET /admin/feature-flags` | Admin produit | Aucun | Retourne flags autorisés, jamais paramètres secrets ou anti-fraude. | Back-office > Configuration produit. | flags autorisés |
| `PATCH /admin/feature-flags/{flag_key}` | Admin produit avec permission | Activation, audience, motif | Flag prédéfini seulement; invalide caches; conserve avant/après et rollback possible. | Configuration > Activer/désactiver module. | flag modifié |
| `GET /admin/moderation-queue` | Modérateur habilité | Type, état, priorité, ancienneté, curseur/limite | Classe la file; donne accès aux preuves nécessaires à la décision uniquement. | Back-office > Modération. | éléments à traiter |
| `POST /admin/bulk-actions/preview` | Admin habilité | Filtre cible, action, motif | Calcule périmètre sans mutation; donne nombre estimé et échantillon masqué. | Action en masse > Prévisualiser. | preview |
| `POST /admin/bulk-actions/execute` | Admin renforcé + MFA | `preview_id`, confirmation, preuve MFA | Revalide que le scope n’a pas changé; exécute par lots avec rapport; journalise toutes cibles; rollback si disponible. | Confirmer action massive; double confirmation si impact majeur. | job async |

### 4.13 Demandes de prestations, catalogue et propositions — V2

Ne pas activer ce module avant d’avoir testé la qualité des demandes et propositions et défini annulation, devis, responsabilités et règles pays.

| Route | Acteur / autorisation | Corps / paramètres | Algorithme + contraintes | Écran / UX-CX | Sortie |
|---|---|---|---|---|---|
| `GET /service-listings` | Public/client | Recherche, métier/skills, lieu, prix/devise, mode, curseur/limite | Ne renvoie que services publiés et profils visibles; prix absent distinct de zéro. | Catalogue de services / recherche prestataire. | liste paginée |
| `POST /service-listings` | Professionnel avec profil actif | Titre, description, catégories, tarification, prix/devise, zone, délai, conditions | Crée `DRAFT`; valider cohérence type de tarification, prix >= 0 et devise explicite. | Mes services > Ajouter; sauvegarder brouillon. | service `DRAFT` |
| `GET /service-listings/{listing_id}` | Public/propriétaire | Aucun | Projection publique; cacher coordonnées privées; indiquer disponibilité inconnue si non renseignée. | Catalogue > Détail service. | détail service |
| `PATCH /service-listings/{listing_id}` | Propriétaire | Champs autorisés | Vérifie état/ownership et tarif; garder version si une proposition/commande s’appuie déjà sur le service. | Mes services > Modifier. | service modifié |
| `POST /service-listings/{listing_id}/publish` | Propriétaire | Confirmation | Profil actif, contenu complet, contrôle modération et tarification; le statut est changé par commande. | Prévisualiser > Publier. | `PUBLISHED` |
| `POST /service-listings/{listing_id}/close` | Propriétaire | Motif facultatif | Masque aux nouvelles demandes; refuse ou guide vers procédure dédiée si engagements actifs. | Mes services > Fermer. | `CLOSED` |
| `POST /service-requests` | Client particulier ou membre organisation autorisé | Titre, besoin, métier/skills, budget min/max, devise, lieu, mode, date souhaitée, visibilité | Crée un brouillon; sépare champs publics/privés; min <= max; date cohérente; scope org vérifié. | Trouver un prestataire > Décrire mon besoin. | demande `DRAFT` |
| `GET /service-requests` | Professionnel | Recherche, métier, skills, lieu, budget, mode, curseur/limite | Renvoie les demandes ouvertes/visibles correspondant aux filtres; informations privées exclues. | Opportunités de prestation. | demandes |
| `GET /service-requests/{request_id}` | Propriétaire ou professionnel autorisé selon visibilité | Aucun | Retourne les champs publics; dévoile les contacts privés uniquement au stade autorisé par la règle produit. | Détail demande. | demande filtrée |
| `PATCH /service-requests/{request_id}` | Client propriétaire | Champs modifiables | Modifiable avant attribution; changements substantiels après propositions doivent être historisés et signalés. | Mes demandes > Modifier. | demande mise à jour |
| `POST /service-requests/{request_id}/publish` | Client propriétaire | Confirmation | Vérifie complétude, date, budget, visibilité, compte actif et modération. | Demande > Prévisualiser/Publier. | demande `OPEN` |
| `POST /service-requests/{request_id}/close` | Client propriétaire | Motif, confirmation | Interdit une fermeture directe qui contourne une commande/contrat actif; arrête nouvelles propositions. | Mes demandes > Clôturer; montrer les propositions affectées. | `CLOSED` |
| `POST /service-requests/{request_id}/proposals` | Professionnel profil actif | Prix, devise, délai, message, étapes facultatives, validité | La demande doit être ouverte; pas de doublon selon la règle; devise compatible; crée proposition versionnée. | Demande > Proposer mes services; récapitulatif prix/délai/conditions avant envoi. | `SUBMITTED` |
| `GET /service-requests/{request_id}/proposals` | Client propriétaire | État, curseur/limite | Liste les propositions reçues; ne permet pas aux concurrents de lire les prix concurrents. | Mes demandes > Propositions reçues. | propositions |
| `GET /service-proposals/{proposal_id}` | Auteur ou client destinataire | Aucun | Vérifie relation et rôle; affiche version exacte, prix, devise, délai et expiration. | Proposition > Détail. | proposition |
| `PATCH /service-proposals/{proposal_id}` | Auteur professionnel | Prix, délai, message, étapes, validité | Modifiable seulement avant acceptation; conserver les versions déjà consultées/acceptées. | Mes propositions > Modifier. | nouvelle version |
| `POST /service-proposals/{proposal_id}/withdraw` | Auteur professionnel | Motif facultatif | Refus si déjà acceptée/convertie en commande; transition idempotente. | Mes propositions > Retirer. | `WITHDRAWN` |
| `POST /service-proposals/{proposal_id}/accept` | Client destinataire | Confirmation, version, acceptation conditions | Verrouille demande et proposition; vérifie expiration, état, budget; une seule acceptation si demande exclusive. | Comparaison > Accepter; afficher un écran de récapitulatif avant confirmation. | `ACCEPTED` |
| `GET /me/service-proposals` | Parties authentifiées | Rôle, état, curseur/limite | Liste uniquement propositions émises ou reçues par le compte. | Mes propositions. | liste |
| `GET /me/availability` | Professionnel | Plage de dates facultative | Retourne les créneaux selon visibilité; ne pas révéler le calendrier privé. | Profil > Disponibilités. | créneaux |
| `PUT /me/availability` | Professionnel | Fuseau, récurrences, exceptions et indisponibilités | Valide chevauchements; transaction atomique; aucun créneau confirmé ne disparaît sans traitement explicite. | Profil > Disponibilités. | disponibilité actualisée |

### 4.14 Évaluations, avis et réputation — V2

| Route | Acteur / autorisation | Corps / paramètres | Algorithme + contraintes | Écran / UX-CX | Sortie |
|---|---|---|---|---|---|
| `POST /collaborations/{collaboration_id}/reviews` | Partie d’une collaboration terminée | Score, critères, commentaire, choix de publication | Confirme collaboration et participant; unicité partie+collaboration; modération possible. Aucun avis sans collaboration vérifiée. | Commande terminée > Évaluer; rappeler que l’avis sera public si publié. | avis en revue/publié |
| `GET /professionals/{professional_id}/reviews` | Public | Curseur/limite/tri | Avis publiés seulement et agrégat calculé; avis contesté/retiré traité selon policy. | Profil public > Avis. | avis publics |
| `POST /reviews/{review_id}/responses` | Professionnel/organisation évalué(e) | Texte de réponse | Vérifie la cible; une réponse par avis selon policy; modération possible. | Profil > Avis > Répondre. | réponse |
| `POST /reviews/{review_id}/disputes` | Partie éligible | Motif, justification, preuves privées | Vérifie partie, délai et contestations antérieures; garde l’avis en état selon policy jusqu’à décision. | Avis > Contester. | dossier de contestation |
| `POST /admin/reviews/{review_id}/decisions` | Modérateur | Décision, motif, note interne | Décide masquage/maintien/restauration avec audit; décideur distinct des parties. | Back-office > Avis contesté. | décision |

### 4.15 Abonnements, visibilité premium et paiements plateforme — V2

| Route | Acteur / autorisation | Corps / paramètres | Algorithme + contraintes | Écran / UX-CX | Sortie |
|---|---|---|---|---|---|
| `GET /billing/plans` | Public | Pays, devise, type client | Retourne plans actifs, avantages, limites, prix et version des conditions. Prix calculé côté serveur. | Page Tarifs. | plans |
| `GET /me/subscription` | Titulaire ou gestionnaire org autorisé | Aucun | Retourne plan, limites, état et prochain renouvellement; pas de données carte. | Paramètres > Abonnement. | abonnement |
| `POST /subscriptions` | Utilisateur/org habilité | Plan, portée, devise, moyen PSP | Le serveur recalcule le prix et crée l’intention de paiement; jamais conserver carte. Idempotency-Key obligatoire. | Tarifs > Choisir un plan > Checkout. | abonnement `PENDING` + checkout |
| `POST /subscriptions/{subscription_id}/cancel` | Titulaire/gestionnaire autorisé | Effet souhaité, motif facultatif, confirmation | Applique la politique de résiliation immédiate ou fin de période; conserve factures et historique. | Abonnement > Résilier; expliquer la date d’effet. | annulation planifiée/effective |
| `GET /me/invoices` | Titulaire ou comptable org autorisé | Période, curseur/limite | Contrôle le scope facturé; fichiers facture par URL signée courte. | Facturation > Factures. | factures |
| `POST /promotions` | Propriétaire d’annonce/service éligible | Cible, placement, budget, dates, devise | Vérifie ownership, objet publiable et inventaire de placement; promotion marquée visuellement « Sponsorisé ». | Offre/service > Promouvoir; prix et limites visibles avant paiement. | promo en attente paiement/revue |
| `GET /me/promotions` | Créateur/titulaire autorisé | État, curseur/limite | Retourne campagnes appartenant au scope; les dépenses ne sont pas visibles aux concurrents. | Tableau > Promotions. | campagnes |
| `POST /webhooks/payments/{provider}` | Serveur PSP seulement; signature valide | Corps brut signé + en-têtes PSP | Vérifier signature, timestamp, rejeu et ID d’événement; dédupliquer; persister puis répondre. Ne jamais utiliser le retour navigateur comme preuve. | Aucun écran utilisateur. | `200/204` après traitement durable |
| `GET /payments/{payment_id}` | Payeur/org/support finance autorisé | Aucun | Retourne état/montant/devise/référence PSP masquée; contrôle propriété. | Détail paiement/facture. | paiement filtré |

### 4.16 Contrats, commandes, paiements, remboursements et litiges — V3

| Route | Acteur / autorisation | Corps / paramètres | Algorithme + contraintes | Écran / UX-CX | Sortie |
|---|---|---|---|---|---|
| `POST /contracts` | Parties d’une proposition acceptée | Proposition, conditions versionnées, échéances, étapes | Crée contrat brouillon depuis une proposition acceptée; prix/devise figés. | Proposition acceptée > Formaliser le contrat; afficher les conditions complètes. | contrat `DRAFT` |
| `GET /contracts/{contract_id}` | Partie au contrat | Aucun | Retourne la version exacte acceptée par chaque partie, pas une version mutable; pièces privées autorisées. | Mes contrats > Détail. | contrat filtré |
| `POST /contracts/{contract_id}/acceptance` | Partie au contrat; réauth si risque | Version consultée, confirmation | Enregistre acceptation de cette version; contrat actif seulement lorsque toutes les acceptations requises sont présentes. Idempotence et trace. | Contrat > Lire et accepter; aucune case précochée pour l’accord. | acceptation/contrat actif |
| `POST /contracts/{contract_id}/change-requests` | Partie au contrat | Modifications proposées, raison, version actuelle | Crée une demande séparée; contrat actif ne change qu’après accord de l’autre partie; versionnement. | Contrat > Proposer modification. | demande en attente |
| `POST /contracts/{contract_id}/cancel-requests` | Partie au contrat | Motif, description, preuves privées | Applique règles selon étape/paiement; aucun remboursement automatique non autorisé. | Contrat > Demander annulation; expliquer étapes suivantes. | demande d’annulation |
| `GET /me/orders` | Client/prestataire partie | Rôle, état, dates, curseur/limite | Filtre commandes où le compte est partie; prochaine action adaptée au rôle. | Mes commandes/prestations. | commandes |
| `POST /orders` | Parties autorisées | Proposition/service, confirmation des conditions | Vérifie prix et disponibilité côté serveur; fige conditions; idempotence obligatoire. | Proposition > Commander; récapitulatif des conditions. | commande |
| `GET /orders/{order_id}` | Client/prestataire partie | Aucun | Vérifie participation; notes internes masquées; affiche étapes, paiement et historique autorisés. | Commande > Détail. | commande filtrée |
| `POST /orders/{order_id}/milestones` | Parties selon contrat | Titre, description, montant, date, ordre | Vérifie total des étapes contre le montant contrat si elles le répartissent; avenant nécessaire pour modifier après activation. | Commande > Étapes. | étape créée |
| `POST /orders/{order_id}/milestones/{milestone_id}/submit` | Prestataire partie | Message, fichiers de preuve | Fichiers READY/privés; vérifie état; soumission idempotente; notifie client après commit. | Étape > Soumettre livrable. | étape `SUBMITTED` |
| `POST /orders/{order_id}/milestones/{milestone_id}/approve` | Client partie | Commentaire, confirmation | Valide seulement une étape soumise; lance le paiement comme opération distincte et idempotente selon PSP. | Étape > Valider; expliquer si paiement non final. | étape approuvée |
| `POST /orders/{order_id}/completion` | Parties selon règle | Confirmation, commentaire | Vérifie étapes, litiges et validations; termine commande puis permet avis/facturation suivant policy. | Commande > Terminer; demander confirmation explicite. | `COMPLETED`/attente confirmation |
| `POST /orders/{order_id}/cancellation-requests` | Partie à la commande | Motif, description, preuves | Examine état, étapes et paiements; demande accord ou revue; ne rembourse pas automatiquement. | Commande > Annuler. | demande en attente |
| `POST /orders/{order_id}/payment-intents` | Payeur autorisé | PSP/moyen et étape ou intention; montant demandé non autoritatif | Le serveur calcule le montant dû et crée une intention PSP; idempotency key; jamais de carte conservée. | Commande > Payer. | intent/checkout PSP |
| `POST /orders/{order_id}/refund-requests` | Payeur/partie éligible | Paiement, montant demandé, motif, description | Vérifie paiement encaissé et solde remboursable; montant et devise calculés/vérifiés côté serveur. | Paiement > Demander remboursement. | dossier en revue |
| `POST /admin/refunds/{refund_id}/decisions` | Opérateur finance habilité | Décision, motif, montant autorisé | Séparation des fonctions; ordre PSP idempotent; statut final confirmé par webhook/réconciliation. | Back-office > Remboursements. | job/remboursement |
| `POST /orders/{order_id}/disputes` | Partie éligible | Motif, description, preuves | Ouvre litige, fige preuves pertinentes et bloque uniquement les étapes prévues par politique. | Commande > Signaler un problème. | litige `OPEN` |
| `GET /disputes/{dispute_id}` | Parties ou agent habilité | Aucun | Projection selon rôle; notes internes privées; accès aux preuves audité. | Litige > Détail. | litige filtré |
| `POST /disputes/{dispute_id}/evidence` | Partie au litige | `file_id`, description | Vérifie fenêtre de dépôt, appartenance et scan; preuves privées; immutabilité après échéance sauf exception autorisée. | Litige > Ajouter une preuve. | preuve ajoutée |
| `POST /admin/disputes/{dispute_id}/decisions` | Agent résolution habilité | Décision, motif, instruction financière, note interne | Décision et exécution PSP séparées; montants calculés côté serveur; contrôle conflit d’intérêt et audit. | Back-office > Litiges. | décision + actions à exécuter |
| `GET /admin/payments/reconciliation` | Opérateur finance habilité | PSP, période, état, curseur/limite | Compare registre interne et rapport/webhooks PSP; les corrections suivent un workflow distinct et audité. | Back-office > Réconciliation. | écarts |

### 4.17 Communauté, ressources et formation — V5+

| Route | Acteur / autorisation | Corps / paramètres | Algorithme + contraintes | Écran / UX-CX | Sortie |
|---|---|---|---|---|---|
| `GET /community/posts` | Public selon visibilité | Recherche, métier/catégorie, tri, curseur/limite | Filtre visibilité/modération avant classement; pagination; pas de contenus cachés dans le flux. | Communauté > Fil. | posts |
| `POST /community/posts` | Utilisateur actif | Titre, contenu, thèmes, fichiers, visibilité | Vérifie taille, URL, fichiers, anti-spam; publication directe ou revue selon policy. | Communauté > Publier; prévisualiser liens et pièces. | brouillon/revue/publié |
| `GET /community/posts/{post_id}` | Public/utilisateur autorisé | Aucun | Vérifie statut/visibilité; droits d’action calculés pour répondre/signaler. | Publication > Détail. | post filtré |
| `PATCH /community/posts/{post_id}` | Auteur | Titre, contenu, thèmes, visibilité | Ownership, versionnement et nouveau contrôle modération si contenu modifié. | Publication > Modifier. | post modifié |
| `DELETE /community/posts/{post_id}` | Auteur | Confirmation | Masque/retire; garde preuve minimale si signalement actif. | Publication > Retirer. | `204` |
| `GET /community/posts/{post_id}/comments` | Public/utilisateur autorisé | Curseur/limite | Retourne commentaires visibles uniquement, paginés. | Publication > Commentaires. | commentaires |
| `POST /community/posts/{post_id}/comments` | Utilisateur actif | Texte, commentaire parent facultatif | Parent doit appartenir à ce post; limite longueur/fréquence; modération et blocage appliqués. | Publication > Commenter. | commentaire |
| `GET /resources` | Public selon licence | Métier, niveau, langue, format, curseur/limite | Liste uniquement ressources approuvées; la licence contrôle l’accès au téléchargement. | Ressources > Catalogue. | ressources |
| `GET /resources/{resource_id}` | Public ou ayant droit | Aucun | Vérifie publication, licence et permission; pas d’URL permanente pour ressource restreinte. | Ressource > Détail/télécharger. | métadonnées/droit d’accès |
| `POST /admin/resources` | Gestionnaire contenu | Titre, auteur, licence, langue, métier, fichier, résumé | Vérifie les droits de publication et le fichier; reste privé avant validation. | Back-office > Ressources > Créer. | ressource `DRAFT` |
| `POST /admin/resources/{resource_id}/publish` | Gestionnaire habilité | Confirmation licence/revue | Vérifie métadonnées et droits puis indexe; audit. | Back-office > Ressource > Publier. | ressource `PUBLISHED` |

## 5. Parcours UX/CX prioritaires

### A. Inscription → profil
1. Inscription : `POST /auth/register`.
2. Vérification : `POST /auth/verification-challenges` puis `/confirm`.
3. Session : `POST /auth/login`, puis `GET /me` si la vérification n’a pas directement créé de session.
4. Profil : `GET/PUT /me/person-profile`, `GET/PUT /me/professional-profile`, sous-routes d’expérience/compétences/preuves.
5. UX/CX : progression lisible, possibilité de reprendre plus tard, aucune obligation de compléter un profil pour explorer les offres, distinction explicite entre contact vérifié et professionnel vérifié.

### B. Candidat → candidature → suivi
1. Recherche : `GET /opportunities` ou `/search/opportunities`.
2. Détail : `GET /opportunities/{id}`; montrer type de contrat, localisation, rémunération (ou « non renseignée »), échéance et état.
3. Postuler : `POST /opportunities/{id}/applications` avec `Idempotency-Key`.
4. Suivi : `GET /me/applications` puis `GET /me/applications/{id}`.
5. Retrait : `POST /applications/{id}/withdraw` après confirmation.
6. UX/CX : conserver les champs en cas d’erreur, ne pas provoquer des doublons après coupure réseau, afficher uniquement l’historique destiné au candidat et expliquer la prochaine action possible.

### C. Recruteur → publication et gestion
1. Choisir l’organisation via `GET /me/organizations`; ne jamais faire confiance au nom saisi dans le formulaire.
2. Créer un brouillon avec `POST /opportunities`, éditer via `PATCH`, prévisualiser puis publier avec `/publish`.
3. Gérer les candidatures avec les routes `/organizations/{id}/applications`; changer les états via `/transitions` et planifier les entretiens.
4. UX/CX : afficher le statut réel de publication, les champs manquants, une confirmation après commit et un état distinct pour notification en attente/échec de livraison.

### D. Client → prestataire (V2)
1. Rechercher catalogue/profils; créer une demande avec budget, devise, lieu, échéance et visibilité.
2. Comparer les devis selon prix total, délai, conditions et preuves réellement vérifiées.
3. Accepter via une confirmation récapitulative; le serveur bloque une acceptation concurrente incompatible.
4. Contrat/commande/paiement uniquement après activation des modules V3 et validation des règles locales.
5. UX/CX : gérer explicitement absence de propositions, proposition expirée, demande retirée, retard et litige.

### E. Modération/support
1. Utilisateur signale avec motif; le signalement ne sanctionne pas automatiquement.
2. Modérateur prend le dossier, examine les seules données nécessaires, décide avec motif et conserve l’audit.
3. L’utilisateur reçoit un statut et une résolution publiable, pas les notes internes. Une voie de contestation doit être prévue si la politique l’autorise.

## 6. Écrans et endpoints consommateurs

| Zone | Écrans | Principaux endpoints |
|---|---|---|
| Public | Accueil, recherche, résultats, détail offre, profil public, tarifs | `/public/config`, `/opportunities`, `/search/*`, `/professionals/{id}`, `/billing/plans` |
| Auth | Inscription, connexion, vérification, reset, sessions | `/auth/*`, `/me`, `/auth/sessions` |
| Profil professionnel | Profil, expérience, compétences, certifications, portfolio, CV, confidentialité | `/me/person-profile`, `/me/professional-profile*`, `/files/*`, `/me/privacy-settings` |
| Candidat | Mes candidatures, détail/timeline, entretiens, notifications, boîte de réception | `/me/applications*`, `/applications/{id}/*`, `/interviews/*`, `/me/notifications`, `/me/conversations` |
| Organisation | Paramètres, membres, invitations, annonces, candidatures, calendrier, analytics | `/organizations/*`, `/organization-invitations/*`, `/opportunities`, `/applications`, `/interviews`, `/analytics/recruitment` |
| Client/prestataire V2 | Catalogue, services, demande, propositions, disponibilités, avis | `/service-listings*`, `/service-requests*`, `/service-proposals*`, `/me/availability`, `/reviews*` |
| Transactions V3 | Contrats, commandes, étapes, paiements, remboursements, litiges | `/contracts*`, `/orders*`, `/payments*`, `/refund-requests`, `/disputes*` |
| Communauté V5 | Fil, publication, commentaires, ressources | `/community/*`, `/resources*` |
| Back-office | Comptes, organisation, taxonomie, modération, support, audit, configuration, finance | `/admin/*`, `/support/*` |

## 7. Découpage de backend FastAPI

```text
app/
  main.py
  core/                 # config, erreurs, logs, sécurité, rate limits, request_id
  api/v1/               # routers, dépendances auth, schémas HTTP
  modules/
    auth/ accounts/ professionals/ taxonomy/ organizations/
    opportunities/ applications/ interviews/ search/ messaging/
    notifications/ moderation/ support/ analytics/
    services/ reviews/ billing/ transactions/ community/
  infrastructure/
    db/                 # SQLAlchemy, transactions, migrations Alembic
    storage/            # stockage privé, URLs signées, scan de fichiers
    tasks/              # outbox, emails/SMS/push et reprises
    payments/           # adaptateurs PSP, webhooks et rapprochement
  tests/
    unit/ integration/ permissions/ workflows/ security/
```

Frontière recommandée : **router HTTP → schéma Pydantic → service métier → repository → PostgreSQL**. Le router gère HTTP; le service décide des règles et permissions; le repository ne prend pas la décision d’autorisation.

## 8. Ordre de réalisation et critères de sortie

| Lot | Construire | Critère de sortie |
|---|---|---|
| 0 | Migrations, erreurs, logs, request ID, pagination, stockage, outbox, tests CI | Une route simple est traçable et ses migrations/test tournent en CI. |
| 1 | Auth, vérification, session, `/me`, clôture, rate limits | OTP expiré/réutilisé refusé; sessions révoquées; anti-énumération testée. |
| 2 | Profil, fichiers privés, taxonomie | Aucun accès IDOR; profil public sans données privées; fichiers non scannés bloqués. |
| 3 | Organisations, adhésions, invitations et permissions | Pas d’organisation sans OWNER; révocation immédiate; tests inter-organisations passent. |
| 4 | Annonces, recherche et index | Annonce non publiée invisible; transitions interdites rejetées; résultats paginés. |
| 5 | Candidatures, tableau recruteur, entretiens | Pas de doublon concurrent; notes internes cachées; snapshot préservé. |
| 6 | Messagerie, notifications, signalement, support, back-office minimal | Reprises de notification; modération auditée; rôles testés. |
| 7 | Pilote mesuré | Mesures d’activation, profil complété, annonces valides, candidatures, conversion et rétention. |
| 8 | Demandes/propositions, avis, abonnements V2 | Devis, expiration, annulation, prix et avis authentiques testés. |
| 9 | Contrats, commandes, PSP, remboursements/litiges V3 | Webhooks signés, idempotence, rapprochement et règles pays validés. |
| 10 | Communauté/ressources V5+ | Modération et droits de publication/licence opérationnels. |

## 9. Tests de sécurité et de logique obligatoires

1. **BOLA/IDOR** : le compte A ne peut lire/modifier profil privé, candidature, fichier, conversation, commande ou ticket de B en remplaçant un UUID.
2. **Organisation** : un recruteur ne lit pas les candidatures d’une autre organisation; la révocation d’adhésion coupe l’accès immédiatement.
3. **États** : `PATCH` ne permet pas de passer une annonce en `PUBLISHED`; seule la commande dédiée peut le faire après validation.
4. **Concurrence** : deux candidatures identiques ne créent qu’un dossier; une seule proposition acceptée si exclusivité; aucun paiement doublé lors d’un retry.
5. **Confidentialité** : les routes publiques ne renvoient jamais contact privé, CV privé, note interne, OTP, jeton ou preuve sensible.
6. **Upload** : fichier non scanné, faux MIME, URL signée expirée et fichier d’un autre compte refusés.
7. **Abus** : OTP/login/invitation/message/report limités et réponses non révélatrices de l’existence du compte.
8. **Outbox/webhooks** : panne de SMS ne perd pas l’événement; un même webhook reçu dix fois ne produit qu’une mutation financière.
9. **Audit** : suspension, vérification, changement de permission, transfert de propriété, export et actions de masse tracent acteur/cible/motif/date.
10. **UX/CX** : erreurs codées et traduisibles; formulaires préservent les saisies; états chargement/vide/erreur/succès; confirmation des actions irréversibles; parcours accessible.
11. **Performance** : listes paginées, requêtes indexées, N+1 évités, exports/statistiques lourds asynchrones.

## 10. Décisions à trancher avant le premier endpoint métier

- Authentification primaire (email, téléphone ou les deux) et fournisseur réellement disponible au pays pilote.
- Politique refresh token, cookie web ou bearer, durées et révocation.
- Matrice exacte des permissions organisationnelles et transitions de statut.
- Visibilité profil/CV/coordonnées/preuves selon contexte et rôle.
- Types/taille de fichiers, stockage, scan antivirus et rétention.
- Champs obligatoires par type d’opportunité et périmètre MVP réellement activé.
- Notifications transactionnelles, préférences et délais de reprise.
- Définition analytique des événements et métriques (vue, offre publiée, candidature valide, conversion).
- Pour V2/V3 : commission, devises, annulation, prestataire de paiement, remboursement, litige, contrat et validation locale.

## 11. Recommandation finale de réalisation

Ne développe pas tous les modules en parallèle. Livre d’abord un parcours vertical complet : **inscription → profil minimal → recherche d’offre → candidature → réception côté recruteur → transition de statut → notification**. Ce parcours teste rapidement les frontières les plus risquées entre UX, modèles de données, permissions, concurrence et sécurité.
