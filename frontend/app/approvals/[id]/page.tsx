import { SellerShell } from "../../components/SellerShell";

export const instant = false;

export default async function ApprovalPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <SellerShell><h1 className="text-2xl font-bold">Approval review</h1><p className="mt-1 text-slate-600">Approval {id}</p><section className="mt-6 space-y-3 rounded-xl border border-slate-200 bg-white p-5"><h2 className="font-semibold">Proposed side effect</h2><p>Create a product using seller-confirmed price and stock.</p><p className="rounded bg-slate-100 p-3 text-sm">Version-bound approval: if the proposal changes, this approval is disabled and must be recreated.</p><button disabled className="rounded bg-slate-300 px-4 py-2 font-semibold text-white">Approve (no current proposal)</button></section></SellerShell>;
}
