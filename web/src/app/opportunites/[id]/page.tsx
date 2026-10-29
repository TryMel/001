import { Suspense } from "react";
import { OpportunityDetail } from "./opportunity-detail";

export default function OpportunityPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  return (
    <Suspense fallback={<main className="container"><p className="loading">Chargement de l’opportunité…</p></main>}>
      <OpportunityResults params={params} />
    </Suspense>
  );
}

async function OpportunityResults({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <OpportunityDetail id={id} key={id} />;
}
