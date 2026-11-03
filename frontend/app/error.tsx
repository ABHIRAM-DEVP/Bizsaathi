"use client";

import Link from "next/link";
import { SellerShell } from "./components/SellerShell";

export default function Error({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <SellerShell>
      <section className="route-error surface-card" role="alert">
        <p className="eyebrow">PAGE DID NOT LOAD</p>
        <h1>Let’s get you back on track</h1>
        <p>
          This page could not be opened. Your saved workspace data has not been
          changed. Try again, or return to Home.
        </p>
        <div className="route-error-actions">
          <button className="button button-primary" type="button" onClick={reset}>
            Try again
          </button>
          <Link className="button" href="/">
            Go to Home
          </Link>
        </div>
      </section>
    </SellerShell>
  );
}
