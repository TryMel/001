# Parcours des acteurs et règles d'accès Akasha

**Statut :** spécification fonctionnelle proposée, issue d'une revue du code actuel  
**Périmètre :** application mobile, API et console d'administration  
**Références :** Akasha v1, référentiel fonctionnel v2, maquette mobile et principes UX observés sur Free-Work  

> Cette spécification décrit la cible et distingue les fonctions présentes des fonctions partielles ou absentes. Une fonction décrite comme cible n'est pas réputée implémentée. Les permissions de l'API font autorité ; masquer un bouton dans l'application ne constitue jamais une restriction d'accès.

## 1. Légende et règles de lecture

- **Présent** : le code actuel met en œuvre l'essentiel du parcours.
- **Partiel** : une partie existe, mais il manque des étapes, une interface dédiée ou des contrôles.
- **À construire** : le besoin produit est identifié, mais il ne faut pas le présenter comme disponible.
- **Bloquant sécurité** : l'écart doit être corrigé avant d'exposer le parcours à des utilisateurs réels.

Free-Work sert ici de repère de lisibilité pour l'emploi et le freelance : intention immédiatement compréhensible, critères comparables, informations utiles mises en évidence, action principale évidente. Akasha reprend ces principes, mais conserve les parcours métier et les règles qui lui sont propres. La maquette `../maquette.jpeg` sert de repère de séquençage et de style ; les écrans et le contenu doivent être adaptés à chaque acteur.

## 2. Modèle commun : un compte, plusieurs espaces

1. Une personne crée **un compte personnel**. Elle peut ensuite cumuler plusieurs espaces, par exemple `professionnel + client` ou `candidat + recruteur`.
2. L'inscription ne doit pas obliger à choisir une seule identité définitive. L'onboarding demande les objectifs et attribue les espaces correspondants ; l'utilisateur peut en ajouter ultérieurement selon les règles de la plateforme.
3. Le **rôle actif** détermine le vocabulaire, l'accueil, les raccourcis et les onglets affichés. Il ne donne aucun droit supplémentaire à lui seul.
4. Chaque action sensible est vérifiée par l'API avec le rôle attribué, la propriété de la ressource, l'appartenance à l'organisation et l'état métier concerné.
5. Les organisations sont des entités distinctes des comptes personnels. Les données d'une organisation ne deviennent pas la propriété d'un membre à titre personnel.
6. Le visiteur, le modérateur et l'administrateur ne sont pas des espaces sélectionnables lors de l'inscription. Les accès internes sont attribués séparément et restent dans la console d'administration.
7. Les paiements de prestations, le séquestre et la libération d'argent ne font pas partie du parcours actuel. L'interface ne doit jamais laisser croire qu'un paiement est sécurisé ou qu'un jalon déclenche un paiement.

### Entrée commune dans l'application

1. **Découverte publique** : comprendre la valeur d'Akasha et parcourir les contenus explicitement publics sans devoir créer un compte.
2. **Inscription / connexion** : adresse e-mail, mot de passe, consentement et vérification de l'adresse selon le parcours.
3. **Choix des objectifs** : trouver un emploi, chercher un stage, proposer ses services, trouver un professionnel ou recruter. Traduire les objectifs en un ou plusieurs espaces.
4. **Configuration minimale** : ne demander que les informations nécessaires au premier objectif. Permettre de terminer un profil plus tard.
5. **Accueil de l'espace actif** : présenter un seul objectif principal, une action primaire et l'activité pertinente de cet espace.
6. **Changement d'espace** : accessible depuis l'en-tête ou le profil, sans déconnexion et sans mélanger les listes privées des différents espaces.

**État actuel :** l'inscription, le choix multi-rôles et la bascule de rôle existent. En revanche, le démarrage mobile mène à un écran de bienvenue puis à une présentation générique ; il n'existe pas encore de vraie navigation publique de découverte. Le parcours de rôle est donc une base, pas encore un onboarding par intention.

## 3. Parcours par acteur

### 3.1 Visiteur — découvrir avant de s'inscrire

**Objectif :** comprendre ce qu'offre Akasha, trouver un métier, un service ou une opportunité, puis s'inscrire seulement lorsqu'une action le nécessite.

**Parcours cible**

1. Accueil public avec recherche « Quel métier, service ou emploi cherchez-vous ? »
2. Choix d'une intention : **Emplois et stages**, **Services professionnels**, **Trouver un professionnel**, **Recruter**.
3. Résultats publics filtrables par secteur/métier, lieu, type, budget ou modalité quand ces données existent.
4. Consultation d'une fiche publique : description, compétences, localisation générale, conditions, statut de vérification réellement établi.
5. Action nécessitant un compte (postuler, publier, proposer, enregistrer ou contacter) : expliquer pourquoi la connexion est nécessaire, préserver la recherche en cours et reprendre après connexion.

**Droits :** lire uniquement les fiches explicitement publiques et publiées ; jamais les brouillons, demandes privées, candidatures, coordonnées personnelles, messages ou informations de membres.

**État actuel — partiel :** l'API expose des offres publiées, des services publiés, certains profils publics et les organisations vérifiées. L'application mobile ne propose pas encore le parcours visiteur avec recherche et navigation publique décrits ici.

### 3.2 Particulier / client — trouver et suivre un prestataire

**Objectif :** décrire simplement un besoin, recevoir des propositions comparables, choisir un professionnel et suivre le travail sans confusion avec un recrutement salarié.

**Parcours cible, inspiré de la maquette**

1. **Accueil client** : salutation, lieu actif modifiable, action primaire « Décrire mon besoin », raccourcis par besoins fréquents et suivi des demandes existantes.
2. **Décrire le besoin** en étapes courtes :
   - nature du besoin ou catégorie ;
   - titre et description en langage simple ;
   - photos facultatives ;
   - ville/zone d'intervention, sans afficher l'adresse exacte publiquement ;
   - budget indicatif facultatif et délai souhaité ;
   - visibilité et aperçu des informations qui seront partagées.
3. **Enregistrer en brouillon**, relire, puis publier explicitement. Expliquer qu'une demande publique sera visible par les professionnels habilités.
4. **Suivre les réponses** : état de la demande, nombre de propositions reçues et prochaine action à effectuer.
5. **Comparer les propositions** côte à côte : prix et devise, délai, périmètre, message, profil/portfolio, disponibilité et vérifications effectivement réalisées. Ne pas inventer de score ou de garantie.
6. **Clarifier puis choisir** une proposition. L'acceptation crée une collaboration et rend les autres propositions indisponibles conformément à la règle métier.
7. **Suivre la collaboration** : accord, démarrage, échanges liés au projet, échéances/livrables si pris en charge, confirmation de fin par les deux parties, puis avis fondé sur la collaboration terminée.
8. **Après la fin** : proposer l'évaluation et un accès à l'historique ; expliquer clairement les recours disponibles. Ne pas afficher d'étape de paiement inexistante.

**Droits du client**

- Créer et gérer ses propres demandes selon leur état ; supprimer uniquement un brouillon ; publier explicitement ; fermer une demande ouverte.
- Voir les propositions reçues uniquement sur ses demandes ; accepter une seule proposition recevable.
- Voir ses propres collaborations et confirmer la fin en tant que partie cliente.
- Évaluer l'autre participant après la fin mutuellement confirmée de la collaboration ; signaler un compte ou un avis selon les mécanismes disponibles.
- Ne jamais modifier les tarifs, délais, profil ou proposition du prestataire.
- Ne jamais accéder aux demandes privées d'autrui, aux messages d'autres personnes, ni aux données privées du prestataire.

**État actuel — partiel :** demandes, brouillons, publication, propositions, acceptation, création de collaboration et confirmation mutuelle de fin existent. L'écran `demandes.tsx` regroupe cependant plusieurs rôles et objets. Les conversations restent rattachées aux candidatures, pas aux prestations ; jalons et livrables sont exposés en lecture seule ; aucun paiement ni mécanisme de litige de collaboration complet n'est actif.

### 3.3 Professionnel / prestataire — présenter son offre et répondre aux besoins

**Objectif :** présenter un savoir-faire crédible, recevoir des demandes adaptées et suivre les engagements acceptés.

**Parcours cible**

1. Créer un passeport professionnel : métier, compétences, expérience ou réalisations ; indiquer la zone et les disponibilités.
2. Choisir explicitement si le profil est public. Expliquer les champs visibles, et garder coordonnées et justificatifs privés par défaut.
3. Publier une ou plusieurs fiches de service avec description, tarif forfaitaire ou « sur devis », délai et médias facultatifs.
4. Découvrir les demandes compatibles ; comprendre pourquoi une demande est proposée et ajuster les filtres.
5. Envoyer une proposition avec montant, devise, délai et périmètre. Afficher l'état d'envoi et permettre le retrait ou la modification tant qu'elle est encore recevable.
6. Après acceptation, accéder à la collaboration, convenir du démarrage, suivre les livrables réellement pris en charge et confirmer la fin.
7. Développer sa réputation avec des avis issus de collaborations terminées ; ne jamais vendre un badge de vérification comme acquis.

**Droits du prestataire**

- Gérer son propre profil, ses services, disponibilités et portfolio si un espace professionnel, candidat ou étudiant lui est attribué.
- Une offre de service est publique uniquement après publication et si le profil est rendu visible.
- Proposer uniquement sur les demandes publiques ouvertes/en discussion, sans proposer sur sa propre demande ou celle de son organisation.
- Voir et modifier uniquement ses propres propositions en attente ; retirer uniquement sa propre proposition recevable.
- Voir ses propres collaborations ; ne pas consulter les autres propositions concurrentes ni les données privées du client.
- Ne pas publier d'offre d'emploi au seul motif qu'un espace professionnel est actif.

**État actuel — partiel :** services, disponibilité, profils publics, portfolio, propositions et fin de collaboration sont présents. Les jalons/livrables ne sont pas modifiables par API et il n'existe pas de messagerie liée aux propositions ou collaborations.

### 3.4 Candidat — chercher un emploi et suivre ses candidatures

**Objectif :** trouver une offre salariée pertinente et connaître exactement l'avancement de chaque candidature.

**Parcours cible**

1. Compléter les informations utiles au recrutement et préciser préférences : métier, lieu, type de contrat, rémunération, présence/hybride/distance.
2. Parcourir les offres d'emploi et filtrer clairement par ces critères.
3. Consulter une fiche structurée : mission, compétences, contrat, rémunération si connue, lieu/modalité, organisation et date.
4. Envoyer une candidature en connaissant les éléments transmis ; éviter de demander les mêmes informations si le profil les contient déjà.
5. Suivre un pipeline : envoyée → en revue → présélectionnée → entretien → offre → acceptée/refusée ; recevoir une notification à chaque changement significatif.
6. Échanger dans une conversation liée à la candidature ; retirer une candidature seulement si la règle produit le permet.

**Droits du candidat**

- Lire les offres publiées ; créer, consulter et retirer ses propres candidatures selon leur état.
- Ne jamais consulter les candidatures d'autres personnes ni les candidatures reçues par un recruteur.
- Les coordonnées, CV et pièces privées ne sont communiqués qu'au destinataire autorisé et selon un consentement explicite.
- Ne jamais modifier le statut décidé par le recruteur.

**État actuel — partiel :** recherche d'offres, candidature, transitions historisées, notifications et messagerie de candidature existent. Les préférences et alertes d'emploi, le CV dédié et l'agenda d'entretien ne sont pas établis comme parcours complet. **La candidature n'est pas restreinte par rôle dans l'API ni dans l'écran mobile** : le bouton « Postuler » est affiché à tous les rôles qui ne sont pas recruteur. Il faut le limiter à candidat/étudiant dans l'interface et vérifier le rôle attribué dans l'API.

### 3.5 Étudiant / jeune diplômé — accéder aux premières opportunités

**Objectif :** trouver stage, alternance ou première expérience et valoriser des projets même sans expérience professionnelle classique.

**Parcours cible**

1. Choisir l'objectif : stage, alternance ou premier emploi ; saisir le niveau/formation seulement lorsque pertinent.
2. Ajouter des projets, réalisations, compétences et expériences facultatives ; ne pas rendre un diplôme obligatoire pour les métiers qui n'en exigent pas.
3. Découvrir des offres dédiées avec filtres et explications adaptés.
4. Postuler et suivre le même pipeline lisible que le candidat, avec une présentation adaptée au stage/alternance.
5. Découvrir mentorat et ressources seulement quand ces services sont effectivement disponibles.

**Droits :** mêmes protections de candidature et de profil que le candidat ; l'espace étudiant ne donne pas accès aux candidatures reçues, aux données d'un établissement ou aux outils de recrutement.

**État actuel — partiel :** l'espace étudiant existe, permet un profil/portfolio et l'UI présente les offres comme des stages. Le mentorat, les ressources d'insertion et une spécialisation complète des offres ne sont pas présents.

### 3.6 Recruteur — publier et traiter des candidatures

**Objectif :** publier une offre claire, trier les candidatures reçues et communiquer avec les candidats dans un pipeline traçable.

**Parcours cible**

1. Sélectionner l'organisation représentée et vérifier son droit d'agir pour elle.
2. Créer un brouillon avec champs adaptés au type d'opportunité (emploi, stage, mission), puis vérifier l'aperçu et publier.
3. Voir les seules offres et candidatures de cette organisation sur lesquelles le recruteur est autorisé.
4. Trier sans fuite de données : statut, date, critères déclarés ; ouvrir les éléments du profil explicitement partagés.
5. Faire évoluer les candidatures par transitions autorisées, avec historique et notification au candidat.
6. Conduire les échanges et documenter les entretiens sans inventer des événements non pris en charge.
7. Fermer l'offre et préserver l'historique nécessaire.

**Droits**

- Un recruteur n'accède qu'aux offres et candidatures de l'organisation et du périmètre qui lui sont attribués.
- Il ne peut pas consulter les conversations ou candidatures d'une autre organisation.
- Il ne peut pas transformer son rôle de recruteur en propriétaire, administrateur ou modérateur.
- Une candidature ne peut être modifiée que par son candidat ou faire l'objet d'une transition autorisée par le recruteur responsable.

**État actuel — partiel :** les offres peuvent maintenant être publiées à titre personnel par un compte recruteur ou au nom d'une organisation vérifiée par un propriétaire ou recruteur membre. Les brouillons et candidatures reçues d'une organisation sont cloisonnés à ses recruteurs/propriétaires ; le retrait d'une appartenance révoque immédiatement cet accès. Le rattachement reste facultatif pour les offres personnelles historiques. Les invitations avec acceptation, l'attribution fine des offres et le traitement complet du recrutement d'entreprise restent à construire.

### 3.7 Organisation / entreprise — agir au nom de l'entité

**Objectif :** séparer les actions de l'entreprise des actions personnelles et donner à chaque membre uniquement le périmètre nécessaire.

**Rôles organisationnels cibles**

| Rôle | Droits cibles |
|---|---|
| Propriétaire | Gérer la fiche et les membres, attribuer les rôles, gérer les offres et demandes, consulter les activités de l'organisation. Transfert de propriété par procédure dédiée. |
| Recruteur | Gérer les offres de recrutement et les candidatures attribuées ; aucun accès automatique aux demandes de service ou aux finances. |
| Gestionnaire | Gérer les demandes de service, propositions reçues et collaborations du périmètre confié ; pas d'administration des membres ni de transfert de propriété. |
| Membre | Accéder uniquement aux ressources explicitement partagées ; pas d'accès implicite aux candidatures, messages privés, factures ou autres équipes. |

**Parcours cible**

1. Créer ou rejoindre une organisation ; distinguer la fiche publique de l'espace privé de gestion.
2. Vérifier l'organisation avant toute publication qui nécessite une représentation confirmée.
3. Inviter un membre avec rôle et périmètre explicites ; le membre accepte avant d'accéder aux données.
4. Choisir l'organisation lors d'une publication ; les offres, demandes, candidatures et collaborations indiquent clairement au nom de quelle entité l'action est faite.
5. Retirer un membre ou révoquer ses droits immédiatement sans transférer ses droits à son compte personnel.

**État actuel — partiel :** fiche d'organisation, état de vérification, appartenance et certains droits propriétaire/gestionnaire existent. Les invitations avec acceptation, les périmètres par ressource, l'association des offres d'emploi à l'organisation et une console métier complète ne sont pas établis. De plus, la liste générique d'organisations utilise actuellement un queryset non filtré : voir les blocages sécurité en section 7.

### 3.8 Établissement de formation — accompagner ses apprenants

**Objectif cible :** gérer une organisation d'établissement, ses membres habilités et des partenariats/stages consentis par les apprenants.

**Parcours cible :** création et vérification de l'établissement → invitation/acceptation d'équipe → publication ou partage d'opportunités partenaires → participation de l'étudiant avec son consentement → suivi agrégé de l'insertion. Un établissement ne consulte jamais par défaut le profil privé, les messages, les candidatures ou les documents d'un étudiant.

**Droits cibles :** les droits sont accordés à l'établissement et à ses membres par ressource ; aucune vue globale des étudiants n'est permise sans relation et base légitime explicites.

**État actuel — à construire :** `etablissement` existe comme rôle sélectionnable, mais il n'y a pas de modèle d'appartenance ou de parcours d'établissement dédié. Ne pas afficher d'actions de convention, de certification ou de suivi d'apprenants comme si elles étaient disponibles.

### 3.9 Modération et administration — opérations internes

**Objectif cible :** traiter les vérifications, signalements et incidents avec des permissions internes minimales, journalisées et séparées des comptes utilisateurs.

**Droits cibles :** accès aux seuls dossiers attribués ; motif requis pour une décision ; aucune consultation de routine des conversations privées ; accès aux pièces limité et audité ; les changements de statut de vérification et les suspensions ne sont jamais accessibles aux rôles ordinaires.

**État actuel — partiel :** modération et administration ne sont pas sélectionnables comme espaces utilisateurs, ce qui est approprié. Django admin/Unfold existe. Des demandes de vérification et signalements existent côté API, mais l'interface et les workflows de traitement modérateur décrits par le référentiel ne sont pas démontrés comme achevés.

## 4. Navigation mobile cible

Les onglets sont des portes d'entrée par tâche, pas des noms techniques. L'espace actif doit rester visible et facilement modifiable ; le changement d'espace change les listes et actions, pas l'identité du compte.

| Espace actif | Navigation principale proposée | Action principale |
|---|---|---|
| Visiteur | Découvrir · Opportunités · Services · Connexion | Rechercher |
| Particulier/client | Accueil · Trouver · Mes demandes · Messages · Profil | Décrire un besoin |
| Professionnel/prestataire | Accueil · Demandes · Mes services · Collaborations · Profil | Répondre à un besoin |
| Candidat | Accueil · Emplois · Candidatures · Messages · Profil | Trouver un emploi |
| Étudiant | Accueil · Stages · Candidatures · Portfolio · Profil | Trouver un stage |
| Recruteur | Pilotage · Offres · Candidatures · Messages · Organisation | Publier une offre |
| Organisation | Vue d'ensemble · Recrutement · Prestations · Équipe · Profil organisation | Choisir le type de besoin |
| Établissement | À cadrer après création des droits et ressources établissement | Ne pas simuler un portail |
| Modération / administration | Console web avec permissions internes | Traiter un dossier autorisé |

Sur téléphone, viser quatre ou cinq onglets principaux au maximum. Les filtres secondaires, préférences et réglages restent dans des écrans secondaires. Conserver les couleurs Akasha, la hiérarchie visuelle, les cartes, la typographie lisible et les actions primaires de la maquette sans multiplier les formulaires longs.

## 5. Matrice condensée des données et permissions

| Ressource | Visiteur | Propriétaire / participant | Autre rôle connecté | Organisation / équipe | Équipe Akasha |
|---|---|---|---|---|---|
| Profil professionnel | Lecture des champs rendus publics uniquement | Lecture et modification de son profil | Pas d'accès aux champs privés | Pas d'accès sans partage/consentement | Accès exceptionnel, justifié et audité |
| Offre publiée | Lecture publique | Créateur autorisé à modifier/fermer selon état | Pas de brouillon ni candidature privée | Recruteur habilité uniquement après liaison à l'organisation | Modération limitée aux besoins de traitement |
| Demande de service publique | Lecture si la surface publique est activée | Client : gestion selon état | Professionnel habilité : voir et proposer | Propriétaire/gestionnaire pour les demandes de l'organisation | Intervention exceptionnelle et auditée |
| Demande privée | Aucun accès | Client et personnes explicitement autorisées | Aucun accès | Membres explicitement autorisés | Pas d'accès de routine |
| Proposition | Aucun accès | Prestataire auteur et client destinataire | Aucun accès aux propositions concurrentes | Gestionnaire autorisé pour la demande organisationnelle | Pas d'accès de routine |
| Candidature | Aucune | Candidat auteur et recruteur propriétaire/assigné | Aucune candidature d'autrui | Recruteur habilité si l'offre appartient à l'organisation | Accès exceptionnel selon procédure |
| Conversation | Aucune | Participants liés à la ressource concernée | Aucun accès par devinette d'identifiant | Pas d'accès automatique des autres membres | Aucune lecture de routine |
| Avis | Avis publics publiés selon politique | Écriture uniquement après collaboration terminée | Pas de modification de l'avis d'autrui | Aucun contrôle de l'avis d'un membre | Modération selon contestation et procédure |
| Vérification / justificatif | Aucun accès | Demandeur voit son statut, pas les décisions internes | Aucun accès | Seulement si dossier organisationnel et habilitation | Traitement par personnel habilité et journalisé |

**Données à minimiser par défaut :** adresse e-mail, téléphone, adresse exacte, pièces d'identité, justificatifs et messages privés. La visibilité publique d'un profil n'autorise pas la publication de ces champs.

## 6. États métier à présenter sans ambiguïté

### Recrutement

`Brouillon → Publiée → Fermée`

La candidature possède un cycle distinct : `Envoyée → En revue → Présélectionnée → Entretien → Offre → Acceptée`, avec sorties possibles `Refusée` ou `Retirée`. Une offre fermée n'efface ni les candidatures ni leur historique. L'expiration automatique et l'approbation modérateur ne doivent pas être affichées comme actives tant qu'elles ne sont pas implémentées.

### Services et collaboration

`Demande brouillon → Ouverte → En discussion → Attribuée → Fermée/Expirée`

Une proposition passe de `Soumise` à `Acceptée`, `Retirée` ou `Refusée`. L'acceptation crée une collaboration `Accordée → En cours → Terminée`, cette dernière nécessitant la confirmation des deux parties dans l'implémentation actuelle.

Les étapes `Jalons`, `Livrables modifiables`, `Litige/Médiation` et `Paiement/libération` sont **à construire ou désactivées**. La maquette et les écrans ne doivent pas les présenter comme des garanties actuellement fournies.

## 7. Écarts et blocages relevés dans le code

Les constats ci-dessous décrivent les fichiers examinés ; ils doivent devenir des tâches testées avant d'annoncer les restrictions correspondantes.

### P0 — Bloquants de restriction à corriger avant exposition

1. **Organisations cloisonnées** — l'API de gestion liste et révèle désormais uniquement les organisations dont l'utilisateur est membre. La fiche publique reste séparée et limitée aux organisations vérifiées ; des tests couvrent la lecture croisée.
2. **Opportunité d'organisation protégée** — les offres sont rattachées à l'organisation ; seuls ses propriétaires et recruteurs peuvent les gérer ou traiter les candidatures, et la publication attend sa vérification.
3. **Candidature protégée** — l'API n'accepte les candidatures que des rôles `candidat` et `etudiant`, et le bouton mobile est limité à ces espaces.
4. **Rôle actif et rôle attribué** — les endpoints doivent autoriser via les rôles attribués et la ressource, jamais simplement parce qu'un écran ou rôle actif est sélectionné. Une bascule d'espace n'est pas une élévation de privilèges.

### P1 — Parcours incomplets ou incohérents

5. **Conversation de prestation absente** — les conversations/messages vérifient aujourd'hui une candidature. Il faut un contexte de conversation distinct pour proposition/collaboration, restreint au client et au prestataire (et au gestionnaire organisationnel explicitement habilité), sans exposer téléphone/adresse.
6. **Recruteur non relié aux offres d'organisation** — une offre est rattachée à un créateur utilisateur, pas à une organisation ; le rôle `recruteur` d'appartenance n'est donc pas le contrôle effectif des candidatures d'entreprise.
7. **Membre invité sans acceptation démontrée** — l'appartenance contient organisation, utilisateur et rôle ; le modèle consulté ne montre pas de statut d'invitation/acceptation. Le parcours cible exige une invitation et une acceptation, pas l'attribution silencieuse d'un accès.
8. **Jalons/livrables en lecture seule** — les viewsets examinés ne fournissent pas les opérations de création, dépôt ou validation. Ne pas afficher de bouton fonctionnel « Déposer un livrable » avant leur implémentation et leurs tests de rôle/état.
9. **Établissement sans modèle métier dédié** — rôle présent, relations et données de suivi absentes ; ne pas promettre conventions, suivi d'insertion ou accès aux apprenants.
10. **Recherche et accueil public manquants côté mobile** — l'API offre quelques ressources publiques, mais il n'y a pas de véritable parcours mobile public universel avec filtres et fiches.
11. **Ressources communautaires limitées** — le module actuel expose des ressources, pas le cycle complet discussion/questions-réponses, modération et signalement annoncé dans Akasha v1.
12. **Console de modération incomplète** — créer une demande de vérification ou un signalement n'est pas la même chose que la traiter avec motif, droits internes et journal d'audit.

## 8. Priorité de réalisation

1. **Sécuriser l'API** : le cloisonnement des organisations, les contrôles de rôle et l'accès aux opportunités/candidatures organisationnelles sont implémentés. Il reste à étendre les droits fins à l'attribution des offres et aux invitations acceptées.
2. **Clarifier le premier lancement** : choisir l'objectif à l'inscription, réduire le formulaire initial, créer des accueils et états vides dédiés, offrir une découverte publique explicitement limitée.
3. **Terminer le binôme Particulier ↔ Professionnel** : demande courte, comparaison lisible de propositions, conversation rattachée à la prestation, collaboration et confirmation mutuelle ; aucune simulation de paiement.
4. **Séparer Emploi/Stage/Recrutement** : offres et filtres adaptés, dossiers candidat, espace recruteur et droits d'organisation.
5. **Ajouter Établissement et Communauté seulement après définition** de leurs ressources, consentements, droits et responsabilités.
6. **Créer des tests de parcours mobiles** pour les flux prioritaires, en plus des tests API. Chaque état de chargement, erreur, absence de résultat et reprise réseau doit rester compréhensible.

## 9. Critères d'acceptation UX et sécurité

- Un utilisateur comprend dans chaque écran **dans quel espace il se trouve**, **ce qu'il peut faire ensuite** et **quelles données seront partagées**.
- Un compte cumulant plusieurs rôles peut changer d'espace sans perdre ses données ni voir les listes privées d'un autre utilisateur.
- Toute API sensible rejette un utilisateur non autorisé même si celui-ci appelle l'endpoint directement ou modifie son rôle actif.
- Les objets privés sont absents des listes et non accessibles par changement d'identifiant ; utiliser une réponse 404 pour ne pas révéler leur existence lorsque la politique le prévoit.
- Toute action est bloquée si la transition d'état correspondante n'est pas permise ; les changements importants sont historisés et notifiés.
- Aucun paiement, vérification, entretien, matching ou badge n'est présenté comme effectué s'il n'existe pas de preuve côté serveur.
- Le particulier voit la proposition complète et peut comparer avant de s'engager ; le prestataire ne voit pas les propositions concurrentes.
- L'interface mobile reste accessible, lisible, utilisable sur petit écran et tolérante aux réseaux instables ; les erreurs gardent les informations non envoyées lorsque c'est sûr.

## 10. Références de code et de produit

- Vision initiale : [`Notes_261023_234339.txt`](./txt%20files/Notes_261023_234339.txt)
- Référentiel actuel : [`REFERENTIEL_FONCTIONNEL_ET_ARCHITECTURE.md`](./REFERENTIEL_FONCTIONNEL_ET_ARCHITECTURE.md)
- Maquette : [`maquette.jpeg`](../maquette.jpeg)
- Navigation mobile actuelle : [`mobile/app/(onglets)/_layout.tsx`](../mobile/app/(onglets)/_layout.tsx)
- Accueil par rôle actuel : [`mobile/app/(onglets)/accueil.tsx`](../mobile/app/(onglets)/accueil.tsx)
- Permissions et états des services : [`backend/collaborations/views.py`](../backend/collaborations/views.py), [`backend/collaborations/permissions.py`](../backend/collaborations/permissions.py)
- Permissions et états recrutement : [`backend/opportunites/views.py`](../backend/opportunites/views.py)
- Organisations et appartenances : [`backend/organisations/views.py`](../backend/organisations/views.py)
- Messagerie actuelle : [`backend/messagerie/views.py`](../backend/messagerie/views.py)
- Repère UX public : [Free-Work — plateforme Tech-IT](https://www.free-work.com/fr/tech-it)

## 11. Données de démonstration locales

Depuis `backend`, créer les comptes et parcours fictifs sur la base de développement locale :

```powershell
python manage.py charger_donnees_demo --confirm-local-development-db --password "VotreMotDePasseDeDemo"
```

La commande refuse `DEBUG=False`, les bases PostgreSQL non locales et toute exécution sans confirmation explicite. Elle crée des profils client, professionnel, candidat, étudiant, recruteur et organisation, une offre avec candidature, un brouillon rattaché à l'organisation non vérifiée, deux demandes de service et une proposition. Le brouillon d'entreprise permet de tester l'accès organisationnel sans contourner l'étape de vérification. La commande n'efface aucune donnée et conserve les états métier déjà modifiés lors d'une exécution précédente. Utiliser uniquement sur une base de développement ; le même mot de passe est appliqué aux comptes de démonstration.
