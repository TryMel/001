import { Suspense } from "react";
import { OpportunitiesExplorer } from "./explorer";

export default function OpportunitesPage({
  searchParams,
}: {
  searchParams: Promise<{ search?: string | string[] }>;
}) {
  return (
    <Suspense fallback={<main className="container"><p className="loading">Chargement des opportunités…</p></main>}>
      <OpportunitiesResults searchParams={searchParams} />
    </Suspense>
  );
}

async function OpportunitiesResults({
  searchParams,
}: {
  searchParams: Promise<{ search?: string | string[] }>;
}) {
  const { search } = await searchParams;
  const initialSearch = Array.isArray(search) ? search[0] ?? "" : search ?? "";
  return <OpportunitiesExplorer initialSearch={initialSearch} />;
}
