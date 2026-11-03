"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { getDashboardSummary } from "@/lib/api-client/runtime";

const navigation = [
  { href: "/", label: "Home" },
  { href: "/posts", label: "Posts" },
  { href: "/products", label: "My Products" },
  { href: "/messages", label: "Messages" },
  { href: "/orders", label: "Orders" },
];

export function SellerShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [menuOpen, setMenuOpen] = useState(false);
  const [pendingApprovals, setPendingApprovals] = useState<number | null>(null);
  const [logoutError, setLogoutError] = useState<string | null>(null);
  const { user, logout } = useAuth();

  useEffect(() => {
    let cancelled = false;
    getDashboardSummary()
      .then((summary) => {
        if (!cancelled) setPendingApprovals(summary.pending_approvals);
      })
      .catch(() => {
        if (!cancelled) setPendingApprovals(null);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  function isActive(href: string): boolean {
    return href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`);
  }

  async function exitWorkspace() {
    setLogoutError(null);
    try {
      await logout();
      setMenuOpen(false);
      router.replace("/login");
    } catch (error) {
      setLogoutError(error instanceof Error ? error.message : "Could not end the local session.");
    }
  }

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">Skip to content</a>
      <header className="reference-topbar">
        <div className="reference-topbar-inner">
          <Link className="reference-brand" href="/" aria-label="BizSaathi home">
            <span className="brand-mark" aria-hidden="true">B</span>
            <span>BizSaathi</span>
          </Link>

          <nav className="reference-nav" aria-label="Main">
            {navigation.map(({ href, label }) => (
              <Link
                key={href}
                href={href}
                className={`nv${isActive(href) ? " on" : ""}`}
                aria-current={isActive(href) ? "page" : undefined}
              >
                {label}
              </Link>
            ))}
          </nav>

          <div className="reference-account">
            <Link
              href="/approvals"
              className="b"
              aria-current={pathname.startsWith("/approvals") ? "page" : undefined}
            >
              Approvals
              {pendingApprovals !== null && pendingApprovals > 0 && (
                <span className="nav-count" aria-label={`${pendingApprovals} pending`}>
                  {pendingApprovals}
                </span>
              )}
            </Link>

            <div className="reference-account-menu">
              <button
                type="button"
                aria-label="Account menu"
                aria-haspopup="menu"
                aria-expanded={menuOpen}
                className="account-button"
                onClick={() => setMenuOpen((open) => !open)}
              >
                {user?.ownerName.trim().charAt(0).toUpperCase() || "D"}
              </button>

              {menuOpen && (
                <div className="reference-menu" role="menu">
                  <div className="reference-menu-heading">
                    <strong>{user?.businessName || "Development workspace"}</strong>
                    <span>Local development access</span>
                  </div>
                  {user && (
                    <button
                      type="button"
                      role="menuitem"
                      className="reference-menu-action"
                      onClick={() => void exitWorkspace()}
                    >
                      Exit local workspace
                    </button>
                  )}
                  {logoutError && <p className="reference-menu-error" role="alert">{logoutError}</p>}
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      <main id="main-content" className="reference-main">
        {children}
      </main>

      <nav className="mobile-bottom-nav" aria-label="Mobile navigation">
        {[
          { href: "/", label: "Home" },
          { href: "/posts", label: "Posts" },
          { href: "/products", label: "Products" },
          { href: "/messages", label: "Messages" },
          { href: "/orders", label: "Orders" },
          { href: "/approvals", label: "Approvals" },
        ].map(({ href, label }) => (
          <Link
            key={href}
            href={href}
            className={`mobile-bottom-link${isActive(href) ? " active" : ""}`}
            aria-current={isActive(href) ? "page" : undefined}
          >
            {label}
          </Link>
        ))}
      </nav>
    </div>
  );
}
