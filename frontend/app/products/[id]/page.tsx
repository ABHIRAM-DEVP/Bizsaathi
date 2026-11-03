import { DraftReview } from "../../components/DraftReview";
import { SellerShell } from "../../components/SellerShell";

export const instant = false;

export default async function ProductDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <SellerShell><p className="text-sm text-slate-500">Product reference: {id}</p><h1 className="text-2xl font-bold">Product review</h1><div className="mt-6"><DraftReview productName="Draft product" /></div></SellerShell>;
}
