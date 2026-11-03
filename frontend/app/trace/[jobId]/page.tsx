import Link from "next/link";
import { SellerShell } from "../../components/SellerShell";

export const instant = false;

export default async function TracePage({ params }: { params: Promise<{ jobId: string }> }) {
  const { jobId } = await params;
  return <SellerShell><Link className="back-link" href="/">← Home</Link><section className="page-heading"><div><h1>Trust and safety</h1><p>Job {jobId} · observable events only. Internal reasoning and secrets are never stored or displayed.</p></div><span className="chip chip-good">✓ Protected</span></section><section className="split-grid"><article className="surface-card"><h2>What happened</h2><div className="timeline"><div><span className="timeline-dot done">✓</span><p><b>Product facts gathered</b><br /><small>Only tenant-scoped confirmed catalogue records were used.</small></p></div><div><span className="timeline-dot done">✓</span><p><b>Claims checked</b><br /><small>Every factual claim was compared with evidence.</small></p></div><div><span className="timeline-dot done">✓</span><p><b>Policy applied</b><br /><small>External sharing waits for your version-bound approval.</small></p></div></div></article><article className="surface-card"><h2>What BizSaathi never does</h2><ul className="check-list"><li>Never guesses price or stock</li><li>Never posts outside the app</li><li>Never exposes cross-tenant data</li><li>Never saves chain-of-thought</li></ul></article></section></SellerShell>;
}
