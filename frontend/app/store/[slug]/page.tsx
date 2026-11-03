import { SharedStoreContent } from "./shared-store-content";

export const instant = false;

export default async function SharedStorePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  return <SharedStoreContent slug={slug} />;
}
