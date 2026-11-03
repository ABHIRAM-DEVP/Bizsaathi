"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { SellerShell } from "../components/SellerShell";
import {
  decideApproval,
  listPendingApprovals,
  RuntimeApiError,
  type ApprovalRecord,
} from "@/lib/api-client/runtime";

function message(cause: unknown): string {
  return cause instanceof RuntimeApiError ? cause.message : "Unable to complete the request. Check the API connection and retry.";
}

export default function ApprovalsPage() {
  const [approvals, setApprovals] = useState<ApprovalRecord[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const selected = approvals.find((approval) => approval.id === selectedId) ?? null;

  const refresh = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const records = await listPendingApprovals();
      setApprovals(records);
      setSelectedId((current) => records.some((item) => item.id === current) ? current : records[0]?.id ?? "");
    } catch (cause: unknown) {
      setError(message(cause));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    listPendingApprovals()
      .then((records) => {
        if (cancelled) return;
        setApprovals(records);
        setSelectedId((current) => records.some((item) => item.id === current) ? current : records[0]?.id ?? "");
      })
      .catch((cause: unknown) => {
        if (!cancelled) setError(message(cause));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  async function decide(decision: "approve" | "reject") {
    if (!selected) return;
    if (decision === "approve" && !window.confirm("Approve this exact proposal version? The backend execution service will validate its effects.")) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await decideApproval(selected, decision);
      setNotice(decision === "approve" ? "Approval recorded by the backend." : "Proposal rejected by the backend.");
      await refresh();
    } catch (cause: unknown) {
      setError(message(cause));
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  return (
    <SellerShell>
      <Link href="/" className="back-link">← Home</Link>
      <header className="page-heading">
        <div><h1>Approvals</h1><p>Only real pending approvals from your business are shown here. Decisions are version-bound and recorded by the API.</p></div>
        <button type="button" className="button" onClick={() => void refresh()} disabled={loading || busy}>Refresh</button>
      </header>
      {error && <p role="alert" className="surface-card" style={{ padding: 14, color: "#8A1F1F" }}>{error}</p>}
      {notice && <p role="status" className="surface-card" style={{ padding: 14, color: "#0B6E5C" }}>{notice}</p>}
      <p>{approvals.length} pending approval{approvals.length === 1 ? "" : "s"}</p>
      {loading ? <p role="status">Loading approvals…</p> : approvals.length === 0 ? (
        <section className="surface-card" style={{ padding: 24 }}>
          <h2>No pending approvals</h2>
          <p>Generated posts are drafts and are not published or scheduled from this app. Review drafts and claims in the content studio.</p>
          <Link className="button button-primary" href="/posts">Open content studio</Link>
        </section>
      ) : (
        <div className="approval-layout">
          <section aria-label="Pending approval list" className="approval-list">
            {approvals.map((approval) => (
              <button key={approval.id} type="button" onClick={() => setSelectedId(approval.id)} aria-pressed={approval.id === selectedId} className={`approval-item${approval.id === selectedId ? " active" : ""}`}>
                <strong>{approval.type.replaceAll("_", " ")}</strong>
                <small>Version {approval.proposal_version} · {new Date(approval.created_at).toLocaleString()}</small>
              </button>
            ))}
          </section>
          {selected && <section className="surface-card approval-detail">
            <h2 style={{ marginTop: 0 }}>Review proposal</h2>
            <p><strong>Type:</strong> {selected.type.replaceAll("_", " ")}</p>
            <p><strong>Risk:</strong> {selected.risk}</p>
            <p><strong>Proposal version:</strong> {selected.proposal_version}</p>
            <h3>Proposal data</h3>
            <pre style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere", padding: 14, background: "#F5F7F5", borderRadius: 10 }}>{JSON.stringify(selected.diff, null, 2)}</pre>
            <h3>Warnings</h3>
            {selected.warnings.length ? <ul>{selected.warnings.map((warning, index) => <li key={index}>{String(warning)}</li>)}</ul> : <p>No warnings recorded.</p>}
            <h3>Side effect</h3>
            <pre style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere", padding: 14, background: "#F5F7F5", borderRadius: 10 }}>{JSON.stringify(selected.side_effect, null, 2)}</pre>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
              <button type="button" className="button button-primary" onClick={() => void decide("approve")} disabled={busy}>Approve exact version</button>
              <button type="button" className="button" onClick={() => void decide("reject")} disabled={busy}>Reject</button>
            </div>
          </section>}
        </div>
      )}
    </SellerShell>
  );
}
