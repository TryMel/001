# Référentiel fonctionnel et architecture de référence

**Projet :** Plateforme professionnelle universelle Akasha  
**Version :** 2.0 — Référentiel consolidé : Cadrage opérationnel, Architecture, CX, UX & UI multi-rôles  
**Date :** 24 octobre 2026  
**Statut :** Document de référence complet et validé pour le développement  
**Objectif :** Fixer le socle commun du projet et définir exhaustivement l'expérience client (CX), l'ergonomie (UX) et le système d'interface (UI) pour la console d'administration et les écrans mobiles, avec un écran d'accueil dédié pour chaque rôle.

La définition détaillée des parcours par acteur, des restrictions réellement observées dans l'API et des écarts à corriger est suivie dans [`PARCOURS_ACTEURS_ET_RESTRICTIONS.md`](./PARCOURS_ACTEURS_ET_RESTRICTIONS.md). Ce document complémentaire distingue les fonctions présentes, partielles et à construire ; il ne remplace pas la validation métier des parcours.

---

## Sommaire

1. [Décisions de référence](#1-décisions-de-référence)
2. [Périmètre produit & Typologie des acteurs](#2-périmètre-produit)
3. [Rôles, permissions et séparation des données](#3-rôles-permissions-et-séparation-des-données)
4. [Architecture technique de référence](#4-architecture-technique-de-référence)
5. [Identité, rôles et cycle de vie commun](#5-identité-rôles-et-cycle-de-vie-commun)
6. [Données et intégrité](#6-données-et-intégrité)
7. [États métiers de référence](#7-états-métiers-de-référence)
8. [Logique commune de chaque fonctionnalité](#8-logique-commune-de-chaque-fonctionnalité)
9. [Paiements, abonnements et facturation](#9-paiements-abonnements-et-facturation)
10. [Catalogue des services externes](#10-catalogue-des-services-externes)
11. [Sécurité et protection des données](#11-sécurité-et-protection-des-données)
12. [Notifications, messages et tâches asynchrones](#12-notifications-messages-et-tâches-asynchrones)
13. [Recherche et classement des profils](#13-recherche-et-classement-des-profils)
14. [Mesure, journalisation et observabilité](#14-mesure-journalisation-et-observabilité)
15. [Tests et définition du « terminé »](#15-tests-et-définition-du-terminé)
16. [Gestion des risques](#16-gestion-des-risques)
17. [Organisation du travail et gouvernance documentaire](#17-organisation-du-travail-et-gouvernance-documentaire)
18. [Plan de travail concret](#18-plan-de-travail-concret-avant-décrire-les-fonctionnalités)
19. [Décisions encore ouvertes](#19-décisions-encore-ouvertes)
20. [Conditions de validation du référentiel](#20-conditions-de-validation-de-ce-référentiel)
21. [Stratégie CX (Customer Experience) & Psychologie d'usage multi-rôles](#21-stratégie-cx-customer-experience--psychologie-dusage-multi-rôles)
22. [Système de Design UI Akasha (Design Tokens & Composants)](#22-système-de-design-ui-akasha-design-tokens--composants)
23. [Architecture UX & Navigation globale Mobile](#23-architecture-ux--navigation-globale-mobile)
24. [Écrans d'accueil dédiés par rôle (Mobile)](#24-écrans-daccueil-dédiés-par-rôle-mobile)
25. [CX, UX & UI de la Console d'Administration et de Modération](#25-cx-ux--ui-de-la-console-dadministration-et-de-modération)
26. [Matrice des flux et transitions d'états dans l'UI Mobile](#26-matrice-des-flux-et-transitions-détats-dans-lui-mobile)
27. [Directives d'implémentation et conformité](#27-directives-dimplémentation-et-conformité)

---

# 1. Décisions de référence

| Sujet | Décision de référence | Pourquoi | Quand revoir ce choix |
|---|---|---|---|
| Vision produit | Un socle professionnel commun avec des parcours distincts pour emploi, stage, prestation et collaboration | Ces activités se recoupent mais n'ont pas les mêmes règles | Si les tests montrent qu'un parcours doit devenir un produit distinct |
| Première mise en œuvre commerciale | Préparer l'architecture internationale, valider les obligations et lancer un premier marché de manière contrôlée (Côte d'Ivoire / UEMOA) | Une architecture mondiale ne signifie pas qu'il faut activer tous les pays dès le premier jour | Avant toute ouverture dans un nouveau pays |
| Architecture backend | **Monolithe modulaire** | Plus simple à construire, tester, sécuriser et exploiter qu'un ensemble prématuré de microservices | Quand la charge, les équipes ou les besoins d'isolation justifient une extraction |
| Backend | Python + Django 5.2 LTS + Django REST Framework (DRF) | Bon socle pour les modèles métier, l'administration, les permissions et les API | À confirmer lors du démarrage technique et du contrôle de compatibilité des dépendances |
| Frontend web | Next.js App Router + React | Interface web, pages publiques indexables et espaces connectés | À réévaluer uniquement si une contrainte technique majeure apparaît |
| Application Mobile | React Native + Expo SDK (Expo Router typé) | Expérience native fluide sur iOS et Android, cohérence de design et rapidité de mise sur le marché | Si un composant bas niveau requiert du code natif pur C++/Kotlin |
| Base de données | PostgreSQL 17 (ou version majeure supportée) | Relations, transactions, contraintes d'intégrité et recherche initiale | Avant un changement majeur de version ou de volume |
| Cache et tâches asynchrones | Redis + Celery lorsque des tâches longues ou différées sont nécessaires | Notifications, traitements de fichiers, tâches de relance et traitements asynchrones | Si les besoins restent trop simples pour justifier leur exploitation |
| Recherche initiale | Recherche PostgreSQL intégrée avec classement explicable | Éviter un moteur de recherche séparé avant d'en avoir besoin | Quand la pertinence, le volume ou les facettes dépassent les capacités acceptables |
| Fichiers | Stockage objet privé compatible S3, accès par liens temporaires signés | Ne pas stocker les fichiers volumineux directement dans les tables relationnelles | Selon disponibilité, coût et exigences de résidence des données |

**État du MVP média :** les photos de profil et logos sont uniques ; les opportunités, offres et demandes de service et réalisations acceptent jusqu’à cinq images facultatives. L’API contrôle JPEG/PNG/WebP, la limite de 5 Mo à l’entrée, redimensionne au maximum à 1 600 pixels et stocke les fichiers hors base avec leurs références en base. Le stockage S3 privé avec liens signés reste une étape de déploiement à configurer ; `MEDIA_ROOT` doit être monté sur un volume persistant et ne doit pas être un disque éphémère en production.
| Paiement | Couche d'intégration indépendante du fournisseur (Adaptateur `PaymentProvider`) | Changer de prestataire sans réécrire les règles métier | À chaque marché ou nouveau moyen de paiement |
| Lancement des paiements | Encaisser d'abord les revenus propres de la plateforme ; ne pas conserver de fonds clients ni organiser de séquestre sans avis juridique et accord du prestataire autorisé | Réduire les risques réglementaires et opérationnels (Instruction BCEAO n°001-01-2024) | Après validation juridique, contractuelle et de conformité |
| Rôles | Compte personnel central, profils et rôles multiples, appartenance aux organisations | Une personne peut être étudiante, salariée, indépendante et recruteuse | Si des règles de séparation spécifiques sont imposées par un pays |
| Monétisation | Abonnements, achats de services, annonces et commissions uniquement selon une règle explicite | Chaque facture doit correspondre à un service compris par l'utilisateur | Après tests de prix et validation du modèle financier |
| Sécurité | Contrôles serveur, permissions par objet, traçabilité des actions sensibles et tests de sécurité | Cacher un bouton dans l'interface ne sécurise pas une API | À chaque ajout de module ou changement de risque |
| Déploiement | Environnements distincts développement, test/préproduction et production | Éviter de tester sur de vraies données de production | Toujours maintenir cette séparation |

## 1.1. Règles qui ne doivent pas être négociées sans analyse

1. Le frontend ne décide jamais seul qu'un utilisateur a le droit d'effectuer une action.
2. Le navigateur ou l'application mobile ne constitue jamais une preuve de paiement réussi.
3. Les montants ne sont jamais manipulés en nombres flottants.
4. Les permissions sont vérifiées sur le serveur, pour chaque ressource concernée.
5. Une offre d'emploi, une candidature, une prestation et un paiement ont des cycles de vie séparés.
6. Une note ou un badge ne doit jamais affirmer une vérification qui n'a pas été réellement effectuée.
7. Les fichiers privés, documents d'identité et pièces de candidature ne sont pas accessibles par une URL publique permanente.
8. Aucun nouveau pays n'est activé avant l'analyse de ses règles, des paiements disponibles et des conditions d'exploitation.
9. Aucune fonctionnalité d'encaissement pour le compte de tiers, de portefeuille utilisateur ou de séquestre n'est activée sans validation juridique et contractuelle.
10. Les partenariats, financements, autorisations et certifications ne seront présentés comme acquis que lorsqu'ils seront documentés.

---

# 2. Périmètre produit

## 2.1. Utilisateurs à prendre en charge

| Type d'acteur | Code Rôle | Besoin principal | Espace principal |
|---|---|---|---|
| Visiteur | `ACT-VIS` | Découvrir des offres, profils publics, métiers et informations sans friction | Pages publiques, recherche découverte et incitation à l'inscription |
| Particulier/client | `ACT-CLI` | Décrire un besoin concret (artisanat, dépannage, conseil) et trouver un prestataire qualifié | Demandes de service, devis reçus et collaborations actives |
| Professionnel/prestataire | `ACT-PRO` | Présenter ses compétences, réalisations et trouver des missions ou des clients directs | Profil & passeport pro, portfolio, propositions et suivi des missions |
| Étudiant/jeune diplômé | `ACT-ETU` | Trouver un stage, une alternance, un projet pratique ou un mentor pour amorcer sa carrière | Espace étudiant, passeport compétences, candidatures stages |
| Candidat | `ACT-CAN` | Postuler à un emploi salarié ou mission long terme et suivre les étapes de sélection | Espace recherche d'emploi, tableau de bord des candidatures |
| Recruteur | `ACT-REC` | Publier des offres, gérer le vivier de candidats et orchestrer les entretiens | Espace de recrutement (ATS simplifié), gestion des offres |
| Organisation/entreprise | `ACT-ORG` | Gérer ses membres, équipes, offres, demandes et facturation centralisée | Console d'organisation, gestion des membres et budgets |
| Établissement/partenaire | `ACT-ETA` | Suivre les programmes de stages, valider les conventions et accompagner l'insertion | Espace institutionnel, partenariats académiques |
| Modérateur/support | `ACT-MOD` | Traiter les signalements d'abus, litiges de collaboration et valider les pièces de confiance | Console de modération et de résolution des litiges |
| Administrateur habilité | `ACT-ADM` | Configurer la plateforme, contrôler les règles pays, superviser les opérations et auditer | Console d'administration globale (Back-office Unfold) |

Un utilisateur peut cumuler plusieurs rôles (ex. salarié le jour, freelance le soir, ou recruteur pour son entreprise). L'utilisateur personnel et l'organisation demeurent des entités distinctes : un collaborateur qui quitte une organisation ne s'approprie pas les données de celle-ci.

## 2.2. Modules fonctionnels de référence

| ID | Module | Responsabilité principale | Dépendances majeures |
|---|---|---|---|
| MOD-01 | Identité et accès | Inscription, connexion, JWT rotation, récupération, sessions, vérification des coordonnées | Aucune ; module fondamental |
| MOD-02 | Profils et portfolio | Profil personnel/professionnel, passeport, expérience, formation, réalisations documentées | Identité, fichiers |
| MOD-03 | Organisations et membres | Entreprises, établissements, équipes, invitations, rôles et délégations de droits | Identité, accès |
| MOD-04 | Métiers et compétences | Taxonomie unifiée (ISCO-08), compétences, langues, spécialisations et alias locaux | Aucun ; données de référence |
| MOD-05 | Offres et opportunités | Emploi, stage, alternance, mission freelance ou opportunité d'expérience | Organisations, taxonomie, modération |
| MOD-06 | Candidatures | Soumission de candidature, étapes de présélection, entretiens et décisions | Profils, opportunités, notifications |
| MOD-07 | Demandes de service | Expression de besoin client, critères, budget indicatif et géolocalisation | Identité, taxonomie |
| MOD-08 | Propositions et devis | Réponses chiffrées des prestataires, prix, délais et conditions proposées | Demandes, profils, organisations |
| MOD-09 | Collaborations | Accord formalisé, jalons, livrables, validation de fin et litiges éventuels | Propositions, utilisateurs, fichiers |
| MOD-10 | Messagerie | Conversations sécurisées contextualisées aux offres, candidatures et collaborations | Identité, droits d'accès |
| MOD-11 | Abonnements et droits commerciaux | Catalogues de plans, entitlements, quotas et périodes de validité | Identité/organisation, facturation |
| MOD-12 | Paiements et facturation | Intentions d'achat de services plateforme, webhooks confirmés, factures PDF | Abonnements, ventes propres, adaptateur paiement |
| MOD-13 | Réputation et références | Avis mutuels après collaboration terminée, recommandations vérifiées | Collaborations/candidatures |
| MOD-14 | Vérification et confiance | Vérification d'identité, de qualification, de diplôme ou d'organisation avec badges explicites | Identité, modération, fichiers |
| MOD-15 | Notifications | Alertes in-app, e-mail transactionnel, SMS/WhatsApp si activé | Tous les modules émetteurs |
| MOD-16 | Modération et litiges | Signalements d'abus, file d'attente, sanctions graduelles et procédure d'appel | Identité, contenus, collaborations |
| MOD-17 | Administration et audit | Configuration globale, journalisation immuable des actions sensibles, supervision | Tous les modules (droits super-admin) |
| MOD-18 | Configuration pays | Paramétrage international : devises (XOF, EUR, USD), formats, langues, règles locales | Modules de référence |
| MOD-19 | Analyse produit et rapports | Mesures d'activation, de rétention, de volume d'affaires et détection de fraude | Événements métier, facturation |
| MOD-20 | Intégrations externes | Adaptateurs isolés pour passerelles de paiement, e-mails, SMS, stockage S3 | Modules consommateurs |

---

# 3. Rôles, permissions et séparation des données

## 3.1. Modèle d'accès recommandé

Le modèle d'autorisation combine cinq niveaux de contrôle côté serveur :
1. **RBAC (Role-Based Access Control)** : Contrôle du rôle global de l'utilisateur (ex. super-administrateur, modérateur, membre).
2. **Contrôle par objet (Object-Level Permission)** : L'utilisateur est-il l'auteur de CETTE demande, le candidat de CETTE postulation, ou le prestataire de CETTE collaboration ?
3. **Contrôle relationnel / Tenant** : L'utilisateur possède-t-il une appartenance active (`OrganizationMembership`) avec un rôle suffisant (`proprietaire`, `recruteur`, `gestionnaire`) au sein de l'organisation ciblée ?
4. **Validation de l'état métier (State-Machine Guard)** : L'action est-elle autorisée à cette étape du cycle de vie (ex. impossible d'ajouter un livrable sur une collaboration clôturée) ?
5. **Droit commercial (Entitlement & Quotas)** : Le plan d'abonnement actif donne-t-il accès à cette fonctionnalité et les quotas mensuels ne sont-ils pas dépassés ?

## 3.2. Matrice des accès clés

| Action | Propriétaire | Membre Orga habilité | Utilisateur connecté tiers | Modérateur | Administrateur technique |
|---|---|---|---|---|---|
| Modifier son profil personnel / Passeport | Oui | Non | Non | Non | Procédure d'audit exceptionnelle |
| Publier / modifier une offre d'organisation | Non | Oui (`recruteur`, `proprietaire`) | Non | Masquer/bloquer en cas d'abus | Exceptionnel journalisé |
| Consulter une candidature reçue | Non | Oui (`recruteur`, `gestionnaire`) | Non | Signalement uniquement | Exceptionnel journalisé |
| Consulter une conversation privée | Participant | Seulement si participant délégué | Non | Accès strictement encadré (litige) | Aucun accès de routine |
| Valider un jalon de collaboration | Client | Mandataire désigné | Non | En médiation de litige | Aucun accès direct |
| Traiter une demande de vérification | Non | Non | Non | Oui | Oui |
| Modifier la configuration pays / devises | Non | Non | Non | Non | Oui (Super-admin avec audit) |

---

# 4. Architecture technique de référence

## 4.1. Schéma logique

```text
       [ Application Mobile Expo (iOS/Android) ]      [ Application Web Next.js ]
                                   \                      /
                                    \                    /
                              HTTPS / JSON (REST /api/v1)
                                          |
                                          v
                         [ Reverse Proxy / Passerelle Nginx ]
                                          |
                                          v
                    [ Backend Django 5.2 LTS + DRF Core ]
          +-------------------------------------------------------------+
          | Modules Métiers Isolés :                                    |
          | - comptes & gouvernance       - opportunites & candidatures |
          | - profils & portfolios        - collaborations & jalons     |
          | - referentiel & taxonomie     - messagerie & notifications  |
          | - organisations & membres     - facturation & confiance     |
          +-------------------------------------------------------------+
               |               |                |              |
               v               v                v              v
         [PostgreSQL 17]  [Redis Cache]   [Worker Celery]  [S3 Storage]
          (ACID, JSONB)   (Sessions, Ratelimit) (Tâches asynchrones) (Fichiers privés)
```

## 4.2. Convention des API (`/api/v1/`)

- Format JSON systématique pour les entrées et sorties.
- Format d'erreur standardisé et prévisible :
```json
{
  "code": "erreur_metier",
  "detail": "Description compréhensible du problème.",
  "erreurs": {
    "champ": ["Message d'erreur spécifique au champ"]
  },
  "requete_id": "req-98fbc1-2026"
}
```
- Authentification par en-tête `Authorization: Bearer <jwt_access_token>`.
- Durée de validité des jetons : Access 15 minutes, Refresh 14 jours avec rotation systématique et liste noire (`TokenBlacklist`).
- Limites de débit (`Throttle`) : 30 requêtes/minute pour les utilisateurs anonymes, 120 requêtes/minute pour les comptes connectés.

---

# 21. Stratégie CX (Customer Experience) & Psychologie d'usage multi-rôles

## 21.1. Les piliers de l'expérience client Akasha

La plateforme Akasha répond aux défis spécifiques des économies émergentes et du marché international :
1. **Fluidité du compte unique et switch instantané** : L'utilisateur ne crée jamais deux comptes pour être à la fois travailleur indépendant et client cherchant un réparateur. Un sélecteur de rôle en 1 clic dans l'interface bascule instantanément le contexte, les flux et les raccourcis sans déconnexion.
2. **Confiance sans prérequis élitiste** : Dans un marché où 65 % des professionnels exercent dans le secteur informel sans CV académique classique, Akasha valorise la compétence démontrée (photos de chantiers, réalisations, références clients, jalons honorés) plutôt qu'uniquement les diplômes formels.
3. **Sécurisation de la relation sans blocage bureaucratique** : Le processus de collaboration sépare la promesse du résultat. Chaque étape (demande, devis, accord, jalons, validation) est enregistrée avec clarté, réduisant les risques d'impayés et de malfaçons.
4. **Sobriété numérique et tolérance aux réseaux instables** : L'expérience mobile est optimisée pour fonctionner sur des connexions 3G/4G faibles avec un cache local persistant, des retries automatiques et des payloads JSON ultra-légers.

---

# 22. Système de Design UI Akasha (Design Tokens & Composants)

Directement transcrit des maquettes et de l'image de référence de l'application (`image de reference.jpeg`) :

## 22.1. Palette de Couleurs (Tokens)

- **Primaire (Akasha Royal Purple)** :
  - `violet`: `#673AB7` (Couleur de marque, boutons d'action principale, icônes actives)
  - `violetFonce`: `#45277D` (Titres majeurs, fonds contrastés)
  - `lavande`: `#F2EDFC` (Fonds de cartes secondaires, badges légers, avatars)
- **Surfaces et Fonds** :
  - `fond`: `#F8F8FB` (Fond d'écran neutre, reposant et moderne)
  - `blanc`: `#FFFFFF` (Surfaces de cartes, modales, champs de saisie)
  - `bordure`: `#E7E8EF` (Contours subtils de séparation)
- **Typographie & Textes** :
  - `texte`: `#172033` (Noir profond / Slate 900 pour une lisibilité maximale)
  - `secondaire`: `#687083` (Gris Slate 500 pour descriptions, sous-titres et métadonnées)
- **États sémantiques** :
  - `succes`: `#16A56B` (Validations, acomptes confirmés, badges vérifiés)
  - `attention`: `#D97706` (En attente de validation, candidatures en revue)
  - `danger`: `#D74B56` (Signalements, rejets, annulations, suppressions)

## 22.2. Composants UI Signature

1. **Carte d'accueil héroïque** : Fond dégradé ou violet uni, typographie blanche contrastée, étiquette en capitales espacées (`letterSpacing: 1.2`), bouton d'action blanc cliquable.
2. **Barre de recherche intelligente avec filtres contextuels** : Champ arrondi avec icône loupe, complété par des puces défilables horizontalement (Métiers, Localisation, Disponibilité, Budget).
3. **Grille d'indicateurs de performance (KPI Cards)** : Cartes blanches avec bordure fine, grand chiffre en violet gras (`fontSize: 22`, `fontWeight: 900`), libellé court et sous-texte explicatif.
4. **Feuille modale de bascule de rôle (Role Switcher Bottom Sheet)** : Permet de passer d'un rôle à un autre instantanément avec indication visuelle du rôle actif et badges de notification non lues par rôle.
5. **Timeline de suivi de collaboration** : Jalons reliés par une ligne verticale/horizontale avec statut d'avancement (Validé en vert, En cours en violet, À venir en gris).

---

# 23. Architecture UX & Navigation globale Mobile

## 23.1. Structure de Navigation (Expo Router)

```text
mobile/app/
├── index.tsx                  # Redirection intelligente selon état d'authentification
├── _layout.tsx                # Layout racine avec SessionProvider et StatusBar
├── (demarrage)/               # Expérience d'accueil et premier contact
│   ├── bienvenue.tsx          # Splash & Présentation de la proposition de valeur
│   ├── onboarding.tsx         # Découverte interactive des opportunités
│   └── roles.tsx              # Choix multi-rôles initial
├── (auth)/                    # Authentification sécurisée
│   ├── connexion.tsx          # Écran de connexion (Email / Mot de passe)
│   └── inscription.tsx        # Inscription rapide avec consentement légal
└── (onglets)/                 # Espace connecté principal (Bottom Tab Navigator)
    ├── _layout.tsx            # Barre d'onglets dynamique selon le rôle actif
    ├── accueil.tsx            # Écran d'accueil dédié selon le rôle actif
    ├── opportunites.tsx       # Offres d'emploi, stages ou gestion recrutement
    ├── demandes.tsx           # Demandes de services ou missions freelance
    ├── messages.tsx           # Messagerie instantanée et négociations
    └── profil.tsx             # Passeport professionnel, switch de rôle & réglages
```

---

# 24. Écrans d'accueil dédiés par rôle (Mobile)

Chaque rôle bénéficie d'une interface d'accueil spécialement calibrée pour son objectif prioritaire.

---

### Rôle 1 : Visiteur (Non connecté / Public) — `SCR-ACC-VIS`
- **Objectif UX** : Séduire, inspirer confiance et démontrer la richesse des compétences et opportunités disponibles sans exiger d'inscription immédiate.
- **En-tête** : Logo Akasha, bouton "Se connecter" épuré.
- **Hero Banner** : "Trouvez des compétences et des opportunités partout dans le monde." + CTA "Rejoindre Akasha".
- **Composants clés** :
  1. *Barre de recherche universelle* : "Quel métier ou service cherchez-vous ?" avec filtres rapides par ville (Abidjan, Bouaké, Paris, etc.).
  2. *Carrousel des secteurs d'activité* : BTP & Rénovation, Informatique & Digital, Commerce & Vente, Artisanat, Santé & Services à la personne.
  3. *Galerie des professionnels vérifiés à la une* : Cartes de profils avec photo, métier, ville, note moyenne et badge de vérification.
  4. *Dernières offres publiées* : Teasers d'emplois, stages et missions avec invitation à postuler.
  5. *Bandeau flottant d'incitation* : "Créez votre Passeport Professionnel en 2 minutes — C'est gratuit."

---

### Rôle 2 : Particulier / Client — `SCR-ACC-CLI`
- **Objectif UX** : Exprimer un besoin de service ou dépannage en un minimum de clics et suivre sereinement les propositions et chantiers en cours.
- **En-tête** : Salutation personnalisée ("Bonjour Jean"), indicateur de localisation active.
- **Hero Banner** : "Un besoin urgent ou un projet ?" + Bouton "Publier une demande de service".
- **Indicateurs clés (KPIs)** :
  - Demandes ouvertes (en attente de devis)
  - Propositions reçues à comparer
  - Collaborations en cours d'exécution
- **Composants clés** :
  1. *Raccourcis de besoins fréquents* : Plomberie, Électricité, Climatisation, Peinture, Déménagement, Cours particuliers.
  2. *Suivi actif de vos demandes* : Carte grand format montrant l'avancement de la dernière demande publiée avec notification de nouveaux devis reçus.
  3. *Prestataires recommandés à proximité* : Liste des artisans vérifiés disponibles immédiatement.
  4. *Conseils & Sécurité Akasha* : Rappel de toujours valider les jalons avant de libérer les paiements.

---

### Rôle 3 : Professionnel / Prestataire (Freelance, Artisan, Technicien) — `SCR-ACC-PRO`
- **Objectif UX** : Trouver des contrats rapidement, gérer sa visibilité et sécuriser le paiement de ses prestations.
- **En-tête** : Nom, badge de vérification de compétence, bouton bascule de disponibilité ("🟢 Disponible pour missions").
- **Hero Banner** : "Votre activité professionnelle" + Résumé des missions actives et bouton "Compléter mon Passeport".
- **Indicateurs clés (KPIs)** :
  - Revenus générés / en cours (en XOF)
  - Propositions envoyées
  - Collaborations en cours
  - Score de complétion du profil (%)
- **Composants clés** :
  1. *Flux des nouvelles demandes de service correspondantes* : Calcul automatique du taux de correspondance (Matching Score 95%) selon les compétences déclarées et la zone géographique.
  2. *Gestionnaire de jalons actifs* : Accès direct au jalon suivant à livrer avec date d'échéance et bouton "Déposer le livrable".
  3. *Accélérateur de réputation* : Raccourci pour solliciter une recommandation client ou faire valider une réalisation.

---

### Rôle 4 : Étudiant / Jeune Diplômé — `SCR-ACC-ETU`
- **Objectif UX** : Décrocher un stage ou une première mission, valoriser ses projets académiques et trouver un accompagnement professionnel.
- **En-tête** : Avatar, statut "Étudiant / En recherche de stage", université ou école affiliée.
- **Hero Banner** : "Construisez votre avenir professionnel" + Bouton "Ajouter une réalisation / projet".
- **Indicateurs clés (KPIs)** :
  - Candidatures de stages envoyées
  - Réponses reçues / Entretiens
  - Compétences validées dans le Passeport
- **Composants clés** :
  1. *Offres de stages & alternances recommandées* : Filtres spécialisés (PFE, stage d'immersion, alternance, premier emploi junior).
  2. *Programme de Mentorat* : Espace de mise en relation avec des professionnels confirmés prêts à relire un CV ou guider l'étudiant.
  3. *Mon Portfolio Académique* : Affichage visuel des projets réalisés en cours ou en hackathon avec liens GitHub / PDF.
  4. *Guides d'insertion* : Fiches conseils pour préparer ses entretiens de recrutement.

---

### Rôle 5 : Candidat (Recherche d'emploi salarié) — `SCR-ACC-CAN`
- **Objectif UX** : Découvrir des offres d'emploi ciblées, postuler en 1 clic et suivre avec précision chaque étape de ses candidatures.
- **En-tête** : Nom, intitulé de poste recherché, alerte emploi active.
- **Hero Banner** : "Recherche d'emploi active" + Bouton "Mettre à jour mes préférences".
- **Indicateurs clés (KPIs)** :
  - Candidatures actives
  - Profils recruteurs ayant consulté mon CV
  - Entretiens programmés
- **Composants clés** :
  1. *Pipeline personnel des candidatures* : Visualiseur d'étapes (Envoyée -> En revue -> Entretien -> Offre).
  2. *Opportunités correspondantes* : Liste détaillée des postes en CDI/CDD avec fourchette salariale transparente et localisation.
  3. *Audit du Passeport Professionnel* : Suggestions de compétences manquantes pour maximiser les chances d'embauche sur les postes ciblés.

---

### Rôle 6 : Recruteur (Entreprise, RH, Cabinet de recrutement) — `SCR-ACC-REC`
- **Objectif UX** : Sourcer les meilleurs talents, publier des offres attractives et piloter le pipeline de sélection sans dispersion.
- **En-tête** : Logo de l'entreprise, nom du recruteur, quota d'annonces restantes.
- **Hero Banner** : "Espace Recrutement" + Bouton prioritaire "Publier une opportunité".
- **Indicateurs clés (KPIs)** :
  - Offres publiées actives
  - Nouvelles candidatures non traitées
  - Entretiens prévus cette semaine
- **Composants clés** :
  1. *Tableau de bord de tri rapide (ATS)* : Accès direct aux candidatures récentes avec score de correspondance IA/mots-clés.
  2. *Recherche directe dans le vivier de talents* : Moteur de recherche multicritère par métiers, compétences attestées et disponibilité immédiate.
  3. *Agenda des entretiens* : Liste chronologique des prochains entretiens avec lien visio ou adresse physique.

---

### Rôle 7 : Organisation / Entreprise (Dirigeant, Achats, Direction) — `SCR-ACC-ORG`
- **Objectif UX** : Piloter la consommation de ressources externes, gérer les collaborateurs autorisés et centraliser les contrats et factures.
- **En-tête** : Dénomination sociale de l'organisation, statut de vérification d'entreprise, sélecteur d'organisation (si multi-entités).
- **Hero Banner** : "Pilotage d'entreprise" + Bouton "Gérer les membres et accès".
- **Indicateurs clés (KPIs)** :
  - Membres de l'équipe actifs
  - Collaborations prestataires en cours
  - Dépenses engagées du mois (XOF)
  - Factures disponibles
- **Composants clés** :
  1. *Vue globale des prestations externes en cours* : Avancement des jalons par équipe et prestataires sous contrat.
  2. *Demandes de validation d'achats* : Devis en attente d'approbation budgétaire par la direction.
  3. *Gestion des collaborateurs* : Invitations en attente, attribution des rôles (Recruteur, Acheteur, Membre).

---

### Rôle 8 : Établissement / Partenaire (Université, Organisme de formation) — `SCR-ACC-ETA`
- **Objectif UX** : Suivre l'insertion de ses promotions d'étudiants, valider les conventions de stage et interagir avec les entreprises partenaires.
- **En-tête** : Nom de l'établissement, logo officiel, promotion active.
- **Hero Banner** : "Portail Institutionnel" + Bouton "Publier un partenariat d'insertion".
- **Indicateurs clés (KPIs)** :
  - Étudiants inscrits
  - Conventions de stage validées
  - Taux de placement / insertion (%)
  - Entreprises partenaires
- **Composants clés** :
  1. *File d'attente des conventions de stage* : Liste des conventions déposées par les étudiants nécessitant la signature académique.
  2. *Demandes de certification de diplômes* : Demandes de vérification d'anciens élèves soumises par des recruteurs.
  3. *Offres partenaires exclusives* : Opportunités d'alternance et de projets d'études réservées aux étudiants de l'établissement.

---

### Rôle 9 : Modérateur / Support — `SCR-ACC-MOD`
- **Objectif UX** : Traiter en priorité les alertes de sécurité, les signalements d'utilisateurs et sécuriser les interactions de la plateforme.
- **En-tête** : Identifiant modérateur, statut de garde actif, niveau d'habilitation.
- **Hero Banner** : "File de modération" + Bouton d'action "Prendre le prochain ticket urgent".
- **Indicateurs clés (KPIs)** :
  - Signalements ouverts (Fraude, Abus, Faux profils)
  - Dossiers de vérification d'identité en attente
  - Litiges de collaboration à arbitrer
  - Temps moyen de résolution (TTR)
- **Composants clés** :
  1. *File d'urgence de modération* : Tri par sévérité (Rouge: suspicion d'arnaque de paiement ; Orange: offre non conforme ; Jaune: litige sur délai).
  2. *Console de vérification des pièces justificatives* : Visualiseur de CNI, passeports et registres de commerce avec boutons "Confirmer" / "Rejeter avec motif".
  3. *Journal des actions récentes* : Historique immédiat des avertissements et suspensions appliqués.

---

### Rôle 10 : Administrateur Habilité (Super-Admin / Direction Opérations) — `SCR-ACC-ADM`
- **Objectif UX** : Avoir une vision à 360° sur la santé économique, technique et opérationnelle de la plateforme Akasha.
- **En-tête** : "Console des opérations Akasha", badge Super-Admin, sélecteur de pays (`CI`, `SN`, `FR`, `TOUS`).
- **Hero Banner** : "Supervision globale" + Bouton "Ouvrir la console Unfold complète".
- **Indicateurs clés (KPIs)** :
  - Utilisateurs totaux & Nouveaux inscrits du jour
  - Volume d'affaires brut (GMV)
  - Taux de succès des transactions
  - Alertes système ou pannes de passerelles
- **Composants clés** :
  1. *Moniteur de santé des intégrations externes* : Statut en temps réel de CinetPay, Paystack, passerelle SMS, stockage S3 et e-mails transactionnels.
  2. *Gestion des paramètres pays* : Activation/Désactivation en 1 clic des modules de paiement ou de publication par marché.
  3. *Journal d'audit temps réel* : Flux des dernières actions critiques exécutées par les administrateurs et modérateurs.

---

# 25. CX, UX & UI de la Console d'Administration et de Modération

La console d'administration d'Akasha repose sur l'intégration personnalisée de **Django Unfold**, stylisée avec les Design Tokens de la marque.

## 25.1. Principes d'Ergonomie de la Console

1. **Dashboard opérationnel orienté action** : La page d'accueil ne se contente pas d'aligner des tables de données ; elle présente immédiatement les indicateurs clés de performance et les alertes nécessitant une intervention immédiate.
2. **Recherche universelle par commande (`Command Palette` / `Cmd+K`)** : Permet à l'administrateur de naviguer instantanément vers n'importe quel utilisateur, organisation, offre ou transaction.
3. **Séparation stricte des tâches et traçabilité** : Toute action modifiant le statut d'un compte, approuvant une vérification ou annulant un paiement exige un motif documenté et génère une entrée immuable dans `JournalAudit`.

## 25.2. Modules de la Console Back-Office

- **Pilotage & Identités** :
  - Gestion des utilisateurs avec filtres par rôle actif, statut de vérification et date d'inscription.
  - Fiche détaillée utilisateur : historique des sessions, rôles cumulés, Passeport professionnel et historique des signalements.
- **Organisations & Entreprises** :
  - Validation du Registre de Commerce et du Crédit Mobilier (RCCM), attribution du badge entreprise certifiée.
  - Supervision des membres et quotas d'offres alloués.
- **Confiance, Qualité & Modération** :
  - Écran de revue des pièces d'identité (zoom, comparaison faciale, contrôle de validité).
  - Gestion des signalements avec actions en 1 clic : Demande de justification, Masquage de contenu, Suspension temporaire, Bannissement définitif.
- **Référentiel & Taxonomie** :
  - Gestion de l'arbre des métiers ISCO-08, ajout de compétences émergentes et d'alias linguistiques locaux (ex. termes ivoiriens du bâtiment et du commerce).
- **Gouvernance & Conformité** :
  - Consultation du journal d'audit avec horodatage UTC, adresse IP, identifiant de l'acteur et diff des modifications JSON.

---

# 26. Matrice des flux et transitions d'états dans l'UI Mobile

## 26.1. Cycle d'une opportunité d'emploi / stage
```text
[Brouillon] ──> (Soumettre) ──> [En révision] ──> (Approbation) ──> [Publiée]
                                                                        │
                 [Archivée] <── (Clôturer) <── [Pourvue] <──────────────┤
```

## 26.2. Cycle d'une prestation / collaboration
```text
[Besoin Client] ──> [Propositions Prestataires] ──> [Accord & Jalons]
                                                           │
[Note & Avis] <── [Clôture] <── [Validation Finale] <── [Livrables]
                                                           │ (En cas de désaccord)
                                                           v
                                                    [Litige / Médiation]
```

## 26.3. Cycle de paiement sécurisé de la plateforme
```text
[Intention d'achat] ──> [Redirection Passerelle] ──> [Webhook Serveur Sécurisé]
                                                             │
                  [Accès commercial activé] <── (Signature valide)
```

---

# 27. Directives d'implémentation et conformité

1. **Intégrité documentaire** : Toutes les spécifications d'écrans et règles métier (`BUS-XXX`, `SCR-XXX`, `FEAT-XXX`) doivent être reliées aux tests automatisés dans la suite de tests.
2. **Conformité réglementaire** : Respect strict de la loi ivoirienne n° 2013-450 sur les données personnelles (ARTCI) et des instructions BCEAO sur les flux financiers.
3. **Zéro régression d'accessibilité** : Contrastes conformes WCAG AA, tailles minimales de boutons tactiles de 48x48 points sur mobile.

---
*Fin du Référentiel fonctionnel et architecture de référence Akasha v2.0.*

---

# 28. Référentiels de données : provenance et limites de vérification

Le catalogue Akasha est extensible, mais une entrée libre ou une correspondance dans une source ne constitue pas, à elle seule, une preuve de légalité ou de reconnaissance officielle.

## 28.1. Métiers et compétences

- **ISCO-08** sert à normaliser les codes et les familles de métiers. Il ne fournit pas, à lui seul, un catalogue détaillé de compétences par métier. Vérifier les droits du fichier ISCO-08 précis avant toute redistribution : la licence dépend notamment de sa date et de ses conditions propres.
- **ESCO** relie métiers et compétences et peut servir de source de correspondances. Vérifier les conditions de réutilisation de la version du jeu de données avant toute intégration commerciale ; les conditions des bibliothèques API ne remplacent pas la licence du jeu de données.
- Chaque import doit conserver classification, code source, version, URL et licence. Une correspondance locale ou calculée doit être identifiée comme telle, et non présentée comme une équivalence officielle.
- Les catalogues ne sont pas téléchargés automatiquement par l’application. Les termes personnalisés d’un profil restent déclaratifs et ne créent pas de référence globale.

Sources de départ : [portail officiel ISCO-08](https://isco.ilo.org/en/isco-08/), [présentation ESCO](https://esco.ec.europa.eu/en/about-esco/what-esco), [accès aux données ESCO](https://esco.ec.europa.eu/en/use-esco).

## 28.2. Entreprises, établissements et formations en Côte d’Ivoire

- Le [CEPICI](https://cepici.ci/infos-creation-entreprise) et le [RCCM OHADA](https://rccm.ohada.org/) sont des pistes de vérification. Aucun accès public, flux de données en masse, API ou droit d’automatisation exhaustif n’a été confirmé pour ce développement. Pour une confirmation déterminante, demander un extrait ou une confirmation au registre compétent.
- Le [MESRS](https://enseignement.gouv.ci/accueil) est le point de départ pour les établissements d’enseignement supérieur. Un annuaire accessible ne suffit pas à prouver l’agrément actuel d’un établissement, d’un diplôme ou d’un programme.
- Le [FDFP](https://fdfp.ci/liste-des-operateurs-de-formation-habilites/) fournit une piste pour les opérateurs de formation habilités. Cette habilitation ne prouve pas automatiquement la reconnaissance d’un cours, d’une qualification ou d’un diplôme individuel.
- Une recherche infructueuse signifie « non retrouvé dans cette source à cette date », jamais « inexistant ». Les établissements, entreprises, programmes et justificatifs doivent être vérifiés comme des affirmations distinctes.

Les ajouts utilisateurs sont affichés comme **déclarés, non vérifiés**. Les statuts « trouvé dans une source », « document examiné » et « confirmé par le registre » restent distincts ; seuls les administrateurs autorisés peuvent renseigner la provenance et modifier le statut. Lier une référence d’entreprise à une organisation ne la vérifie pas automatiquement.

## 28.3. Profil et candidature

Le candidat doit consentir au partage de son profil lors de l’envoi d’une candidature. Akasha conserve une copie du profil professionnel à cette date ; seul le recruteur autorisé à traiter cette candidature peut la consulter. Les coordonnées privées ne font pas partie de cette copie.
