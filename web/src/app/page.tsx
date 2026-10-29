import Link from "next/link";

const parcours = [
  {
    titre: "Construire son parcours",
    texte: "Présentez vos compétences, vos expériences et vos réalisations selon le niveau de visibilité que vous choisissez.",
    icone: "person",
  },
  {
    titre: "Trouver une opportunité",
    texte: "Explorez des emplois, stages, missions et besoins de service, partout où Akasha est disponible.",
    icone: "search",
  },
  {
    titre: "Faire avancer un projet",
    texte: "Publiez un besoin, évaluez les candidatures et suivez les collaborations avec des règles claires.",
    icone: "briefcase",
  },
];

function Icone({ nom }: { nom: "person" | "search" | "briefcase" }) {
  const paths = {
    person: <><circle cx="12" cy="8" r="3.5" /><path d="M4.5 20c.8-3.5 3.4-5.4 7.5-5.4s6.7 1.9 7.5 5.4" /></>,
    search: <><circle cx="10.8" cy="10.8" r="5.7" /><path d="m15.2 15.2 4.3 4.3" /></>,
    briefcase: <><rect x="3" y="7" width="18" height="13" rx="2" /><path d="M9 7V5.5A1.5 1.5 0 0 1 10.5 4h3A1.5 1.5 0 0 1 15 5.5V7M3 12h18M10 12v2h4v-2" /></>,
  };
  return <svg aria-hidden="true" className="home-icon" fill="none" viewBox="0 0 24 24">{paths[nom]}</svg>;
}

export default function Home() {
  return (
    <main className="container">
      <section aria-labelledby="hero-title" className="hero home-hero">
        <div className="hero-content">
          <p className="eyebrow">Opportunités professionnelles, sans frontière</p>
          <h1 id="hero-title">Le travail mérite un espace plus juste.</h1>
          <p className="hero-copy">
            Akasha met en relation les personnes, les organisations et les projets
            sans se limiter à un pays, un statut ou un métier.
          </p>
          <form action="/opportunites" className="search-bar" method="get" role="search">
            <label className="sr-only" htmlFor="recherche-opportunites">
              Métier, compétence ou mot-clé
            </label>
            <input autoComplete="off" id="recherche-opportunites" name="search" placeholder="Métier, compétence ou mot-clé" type="search" />
            <button className="button" type="submit">Rechercher</button>
          </form>
          <div className="hero-tags" aria-label="Types d’opportunités">
            <span>Emploi</span><span>Stage</span><span>Mission</span><span>Service</span>
          </div>
        </div>
        <aside className="hero-principles" aria-label="Principes Akasha">
          <p>Une plateforme pensée pour les parcours réels.</p>
          <ul>
            <li>Choix de la visibilité du profil</li>
            <li>Référentiels de métiers traçables</li>
            <li>Règles locales prises en compte</li>
          </ul>
        </aside>
      </section>

      <section aria-labelledby="parcours-title" className="section">
        <div className="section-heading">
          <div>
            <p className="eyebrow home-eyebrow">Un parcours, plusieurs possibilités</p>
            <h2 id="parcours-title">Une expérience utile pour chaque rôle.</h2>
          </div>
          <Link className="text-link" href="/opportunites">Explorer les opportunités</Link>
        </div>
        <div className="feature-grid">
          {parcours.map((item) => (
            <article className="feature-card" key={item.titre}>
              <div aria-hidden="true" className="feature-icon"><Icone nom={item.icone as "person" | "search" | "briefcase"} /></div>
              <h3>{item.titre}</h3>
              <p>{item.texte}</p>
            </article>
          ))}
        </div>
      </section>

      <section aria-labelledby="confiance-title" className="section home-principles-grid">
        <div>
          <p className="eyebrow home-eyebrow">Confiance et responsabilité</p>
          <h2 id="confiance-title">Des informations expliquées, pas des promesses opaques.</h2>
          <p className="home-lead">
            Les données de profil, les références et les évaluations sont présentées
            avec leur contexte. Lorsqu’il manque des données, Akasha l’indique au lieu
            de fabriquer un score ou une recommandation.
          </p>
        </div>
        <ul className="principle-list">
          <li><strong>Ouvert à l’international</strong><span>Les pays, langues et règles locales sont traités comme des données de référence, pas comme des limites du produit.</span></li>
          <li><strong>Compétences avant les étiquettes</strong><span>Les métiers et compétences peuvent être reliés à leur classification et à leur source.</span></li>
          <li><strong>Choix et contrôle</strong><span>Chaque personne garde la maîtrise des informations visibles sur son profil.</span></li>
        </ul>
      </section>

      <section className="section notice home-cta">
        <div>
          <h2>Un profil pour avancer, recruter ou collaborer.</h2>
          <p>Créez un compte, choisissez vos rôles et complétez uniquement les informations utiles à votre parcours.</p>
        </div>
        <div className="home-cta-actions">
          <Link className="button" href="/inscription">Créer un compte</Link>
          <Link className="text-link" href="/connexion">Se connecter</Link>
        </div>
      </section>
    </main>
  );
}
