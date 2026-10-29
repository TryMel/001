# Akasha Web

Application web MVP Akasha construite avec Next.js App Router, React et TypeScript. Les écrans appellent l’API Django **v2** via les routes serveur `/api/backend/*` ; le navigateur ne reçoit jamais les jetons JWT.

## Configuration requise

- `AKASHA_API_BASE_URL` — origine HTTP(S) du backend Django, configurée uniquement côté serveur. Les routes BFF l’utilisent pour joindre les endpoints `/api/v2/`.
- `NODE_ENV` — Next.js active automatiquement l’attribut `Secure` des cookies lorsque `NODE_ENV=production`.

Ne pas préfixer `AKASHA_API_BASE_URL` par `NEXT_PUBLIC_`. Aucun fichier `.env` existant n’est requis ni inspecté par cette application. Pour le développement, fournir cette variable dans l’environnement du processus Next.js.

Le backend Django doit également autoriser les règles d’accès à son API v2. Les requêtes web partent du serveur Next.js ; l’URL interne du backend n’est pas incluse dans le bundle navigateur.

## Lancer l’application

```bash
npm install
npm run dev
```

Le serveur Next.js est normalement disponible sur `http://localhost:3000`.

## Validation

```bash
npm run lint
npm run typecheck
npm run build
```

Les routes publiques couvrent la page d’accueil et la découverte d’opportunités. Les espaces connectés couvrent la configuration des rôles, le profil candidat/professionnel, les candidatures et l’espace recruteur. Les organisations sont demandées uniquement depuis l’endpoint membre-scopé existant ; aucune liste privée n’est exposée publiquement. La console d’administration existante reste fournie par Django sous `/administration/`.

Les comptes utilisent des cookies `HttpOnly`, `SameSite=Lax` et `Secure` en production. La connexion et l’inscription placent les jetons côté serveur, les appels protégés les transmettent dans `Authorization`, les réponses 401 déclenchent un rafraîchissement avec rotation, et la déconnexion révoque le jeton de rafraîchissement auprès de Django avant d’effacer les cookies.
