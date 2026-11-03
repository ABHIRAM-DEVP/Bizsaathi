"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { clearLocalSession, loginLocalAccount, registerLocalAccount } from "@/lib/api-client/runtime";
import { useAuth } from "../context/AuthContext";

const demoAccount = process.env.NEXT_PUBLIC_DEMO_ACCOUNT
  || (process.env.NODE_ENV === "development" ? "demo-owner" : undefined);
const demoBusinessName = process.env.NEXT_PUBLIC_DEMO_BUSINESS_NAME || "Local development workspace";
const demoOwnerName = process.env.NEXT_PUBLIC_DEMO_OWNER_NAME || "Local owner";

function LoginContent() {
  const router = useRouter();
  const sessionNotice = useSearchParams().get("reason") === "session";
  const { login } = useAuth();
  const [mode, setMode] = useState<"register" | "signin">("signin");
  const [ownerName, setOwnerName] = useState("");
  const [businessName, setBusinessName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function enterDevelopmentWorkspace() {
    if (!demoAccount) return;
    setIsSubmitting(true);
    setError(null);
    try {
      await clearLocalSession();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not clear the local session.");
      setIsSubmitting(false);
      return;
    }
    login({ businessName: demoBusinessName, ownerName: demoOwnerName, email: "" });
    router.replace("/");
  }

  async function submitLocalAccount(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    try {
      const account = mode === "register"
        ? await registerLocalAccount({
            owner_name: ownerName,
            business_name: businessName,
            email,
            password,
          })
        : await loginLocalAccount({ email, password });
      login({
        businessName: account.business.name,
        ownerName: account.user.display_name,
        email: "",
        businessSlug: account.business.slug,
      }, "local");
      router.replace("/");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not access the local account.");
      setIsSubmitting(false);
    }
  }

  return (
    <main className="login-container">
      <section className="login-card" aria-labelledby="login-title">
        <header className="login-header">
          <div className="login-brand">
            <span className="brand-mark" aria-hidden="true">B</span>
            <span className="brand-text">BizSaathi</span>
          </div>
          <p className="login-tagline">Evidence-grounded co-pilot for small sellers</p>
        </header>
        <div className="login-content">
          <h1 id="login-title" className="login-title">Development workspace</h1>
          <p className="login-subtitle">
            Sign in to your own shop, create an account, or continue with the shared demo. Nothing is published automatically.
          </p>
          {sessionNotice && (
            <p className="info-box" role="status">
              Your local session could not be verified. Sign in to continue to your shop.
            </p>
          )}
          {demoAccount ? (
            <section className="login-option" aria-labelledby="demo-access-title">
              <h2 id="demo-access-title">Use the demo workspace</h2>
              <button
                type="button"
                className="button button-primary full-button"
                onClick={enterDevelopmentWorkspace}
                disabled={isSubmitting}
              >
                Enter demo workspace
              </button>
            </section>
          ) : (
            <p className="info-box" role="status">Shared demo access is not configured.</p>
          )}
          <div className="login-divider" aria-hidden="true"><span>or use your own account</span></div>
          <section className="login-form" aria-labelledby="local-account-title">
            <h2 id="local-account-title">
              {mode === "register" ? "Create a local account" : "Sign in to your account"}
            </h2>
            <div className="login-option">
              <button
                type="button"
                className="button"
                onClick={() => {
                  setMode((current) => current === "register" ? "signin" : "register");
                  setError(null);
                }}
                disabled={isSubmitting}
              >
                {mode === "register" ? "Already have an account? Sign in" : "Need an account? Create one"}
              </button>
            </div>
            <form onSubmit={submitLocalAccount}>
              {mode === "register" && (
                <>
                  <label className="login-field">
                    Your name
                    <input
                      autoComplete="name"
                      maxLength={120}
                      name="owner_name"
                      onChange={(event) => setOwnerName(event.target.value)}
                      required
                      value={ownerName}
                    />
                  </label>
                  <label className="login-field">
                    Shop name
                    <input
                      autoComplete="organization"
                      maxLength={120}
                      name="business_name"
                      onChange={(event) => setBusinessName(event.target.value)}
                      required
                      value={businessName}
                    />
                  </label>
                </>
              )}
              <label className="login-field">
                Email
                <input
                  autoComplete="email"
                  maxLength={320}
                  name="email"
                  onChange={(event) => setEmail(event.target.value)}
                  required
                  type="email"
                  value={email}
                />
              </label>
              <label className="login-field">
                Password
                <input
                  autoComplete={mode === "register" ? "new-password" : "current-password"}
                  maxLength={72}
                  minLength={mode === "register" ? 6 : 1}
                  name="password"
                  onChange={(event) => setPassword(event.target.value)}
                  required
                  type="password"
                  value={password}
                />
              </label>
              <button type="submit" className="button button-secondary full-button" disabled={isSubmitting}>
                {isSubmitting
                  ? "Please wait..."
                  : mode === "register" ? "Create account" : "Sign in"}
              </button>
            </form>
            <p className="info-box" role="note">
              Local development only. Account credentials are used to sign in and are not stored in your browser.
            </p>
          </section>
          {error && <p className="login-error" role="alert">{error}</p>}
        </div>
      </section>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<main className="login-container" aria-busy="true" />}>
      <LoginContent />
    </Suspense>
  );
}
