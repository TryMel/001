import { ProfilPublicView } from "./profil-public";

export default async function PublicProfilePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <ProfilPublicView identifiant={id} />;
}
