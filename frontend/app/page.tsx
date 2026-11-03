"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { SellerShell } from "./components/SellerShell";
import { useAuth } from "./context/AuthContext";
import { getDashboardSummary, RuntimeApiError, type DashboardSummary } from "@/lib/api-client/runtime";

function errorText(cause: unknown): string {
  return cause instanceof RuntimeApiError
    ? cause.message
    : "The dashboard could not load. Check the API connection and retry.";
}

export default function Home() {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setStats(await getDashboardSummary());
    } catch (cause: unknown) {
      setError(errorText(cause));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    getDashboardSummary()
      .then((result) => {
        if (!cancelled) setStats(result);
      })
      .catch((cause: unknown) => {
        if (!cancelled) setError(errorText(cause));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  return (
    <SellerShell>
      <header className="dashboard-heading">
        <div>
          <div className="dashboard-title">
            <h1>Good morning, {user?.ownerName.trim().split(/\s+/)[0] || "seller"}</h1>
            <span className="chip">Owner workspace</span>
          </div>
          <p>Your catalog and approvals, all in one place.</p>
        </div>
        <div className="dashboard-actions">
          <Link href="/products" className="button">View catalog</Link>
          <Link href="/products/new" className="button button-primary">+ New product</Link>
        </div>
      </header>

      {error && (
        <div role="alert" className="surface-card error-panel">
          <p>{error}</p>
          <button type="button" className="button" onClick={() => void refresh()} disabled={loading}>Retry</button>
        </div>
      )}
      {loading && <p role="status">Loading your business data…</p>}

      {stats && (
        <>
          {stats.pending_approvals > 0 && (
            <section className="attention-card" aria-label="Next step">
              <div>
                <span className="eyebrow">YOUR NEXT STEP</span>
                <h2>{stats.pending_approvals} item{stats.pending_approvals === 1 ? "" : "s"} need your review</h2>
                <p>Review the saved proposal and its details before deciding.</p>
              </div>
              <Link href="/approvals" className="button button-primary">Go to approvals →</Link>
            </section>
          )}

          <div className="dashboard-workspace-grid">
            <section className="surface-card dashboard-start-card" aria-labelledby="start-title">
              <span className="eyebrow">GET STARTED</span>
              <h2 id="start-title">Add a product to your catalog</h2>
              <p>Enter the details you’ve confirmed. Your saved catalog is the source for product facts and prices.</p>
              <div className="dashboard-start-actions">
                <Link href="/products/new" className="button button-primary">Add product details</Link>
                <Link href="/posts" className="button">Create a post draft</Link>
              </div>
            </section>

            <section className="surface-card dashboard-snapshot" aria-labelledby="snapshot-title">
              <h2 id="snapshot-title">Your workspace</h2>
              <ul className="dashboard-list">
                <li><span>Approvals waiting</span><span className="chip">{stats.pending_approvals}</span></li>
                <li><span>Low-stock products</span><span className="chip chip-warn">{stats.low_stock.length}</span></li>
                <li><span>Recent jobs</span><span className="chip">{stats.recent_jobs.length}</span></li>
              </ul>
              <Link href="/approvals" className="dashboard-inline-link">Review approvals →</Link>
            </section>
          </div>

          <div className="dashboard-grid">
            <section className="surface-card" aria-labelledby="low-stock-title">
              <div className="section-title">
                <div>
                  <h2 id="low-stock-title">Products to check</h2>
                  <p>Low-stock items from your saved catalog.</p>
                </div>
                <Link href="/products">Open catalog →</Link>
              </div>
              {stats.low_stock.length === 0 ? <p>No low-stock products in the current catalog.</p> : (
                <ul className="dashboard-list">
                  {stats.low_stock.map((product) => (
                    <li key={product.id}>
                      <span>{product.name}</span>
                      <span className="chip chip-warn">{product.stock_total} in stock</span>
                    </li>
                  ))}
                </ul>
              )}
            </section>
            <section className="surface-card" aria-labelledby="recent-jobs-title">
              <div className="section-title">
                <div>
                  <h2 id="recent-jobs-title">Recent work</h2>
                  <p>Background tasks recorded for your business.</p>
                </div>
              </div>
              {stats.recent_jobs.length === 0 ? <p>No recent background work.</p> : (
                <ul className="dashboard-list dashboard-list-compact">
                  {stats.recent_jobs.map((job) => (
                    <li key={job.id}>
                      <span>{job.kind.replaceAll("_", " ")}</span>
                      <span className="chip">{job.status}</span>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        </>
      )}
    </SellerShell>
  );
}
