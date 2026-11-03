import { SellerShell } from "./components/SellerShell";

export default function Loading() {
  return (
    <SellerShell>
      <section className="route-loading" aria-busy="true" aria-live="polite">
        <p className="eyebrow">BIZSAATHI WORKSPACE</p>
        <h1>Opening your page…</h1>
        <p>Your workspace stays here while the next step loads.</p>
        <div className="route-loading-grid" aria-hidden="true">
          <div className="route-loading-card" />
          <div className="route-loading-card" />
          <div className="route-loading-card route-loading-wide" />
        </div>
      </section>
    </SellerShell>
  );
}
