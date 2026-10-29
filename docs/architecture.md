# Architecture Akasha — v1

## Décisions confirmées

| Code | Décision | Statut |
| --- | --- | --- |
| ARC-001 | Monolithe modulaire Django/DRF | Confirmé |
| ARC-002 | PostgreSQL 15 comme base transactionnelle | Confirmé |
| SEC-001 | JWT avec accès court, rotation et révocation | Confirmé |
| API-001 | API REST documentée par OpenAPI | Confirmé |
| MOB-001 | Expo SDK 54 et navigation Expo Router | Confirmé |

## Modules et responsabilités

| Module | Responsabilité | Priorité |
| --- | --- | --- |
| comptes | identité, JWT, profil personnel | P0 |
| profils / portfolios | passeport professionnel, formations, réalisations | P0 |
| referentiel / correspondance | métiers, compétences, recherche expliquée | P0 |
| opportunites | emploi, stage, missions, candidatures | P0 |
| collaborations | besoins, propositions, accord, jalons, livrables | P0 |
| organisations | entreprise, membres et rôles | P0 |
| confiance | vérifications, avis, signalements | P1 |
| facturation | abonnements et factures, sans fournisseur de paiement | P1 |
| internationalisation | pays, devise et règles locales | P1 |

## Contrat JWT

- `POST /api/comptes/inscription/` crée le compte et retourne `access` et `refresh`.
- `POST /api/comptes/connexion/` retourne une paire JWT.
- `POST /api/comptes/rafraichir/` renouvelle l'accès et fait tourner le jeton de rafraîchissement.
- `POST /api/comptes/deconnexion/` révoque le jeton de rafraîchissement.
- Les routes protégées attendent `Authorization: Bearer <access>`.

`SEC-002` — Ne jamais intégrer un mot de passe de base de données dans l'application mobile ou un dépôt. Les secrets sont lus depuis `backend/.env` en développement et devront provenir d’un coffre de secrets au déploiement.

## Profil et portfolio

- `GET/PATCH /api/comptes/moi/` expose et modifie les champs d'identité autorisés (`first_name`, `last_name`, `telephone`, `pays`). L'adresse e-mail, les rôles attribués, le rôle actif et les indicateurs de vérification restent non modifiables par cette route.
- `GET/PATCH /api/profils/moi/` retourne ou met à jour le profil du compte connecté. La première lecture crée le profil si nécessaire. Les espaces professionnel, candidat et étudiant donnent accès à cette capacité de façon cumulative; le rôle actif ne la restreint pas.
- Les routes `/api/portfolios/{experiences,formations,realisations,qualifications}/` sont limitées aux entrées du compte connecté. Le serveur attribue le profil automatiquement, vérifie les périodes et ne laisse jamais le client modifier les indicateurs administratifs.
- Les profils ne disposent pas de route de lecture publique dans cette version. L'adresse e-mail et le téléphone ne sont pas exposés dans les données professionnelles.

## Exceptions API

Chaque réponse d’erreur utilise le format suivant :

```json
{"code":"validation_error","detail":"La requête est invalide.","erreurs":{"champ":["Erreur"]}}
```

Les appels anonymes et authentifiés sont limités en fréquence. Les autorisations métier restent contrôlées au niveau de chaque vue et ne doivent jamais être déduites de l’interface mobile.

## Décisions encore ouvertes

- Fournisseur d’e-mail, SMS/OTP, stockage de fichiers et paiement : à sélectionner après validation des pays et des contraintes contractuelles.
- Séquestre, redistribution de fonds et Mobile Money : bloqués jusqu’à validation juridique et contractuelle.
- MFA : P1 ; choisir TOTP avant un mécanisme SMS si le niveau de risque le justifie.
- Politique de conservation, anonymisation et conformité locale : à valider juridiquement avant le pilote.
