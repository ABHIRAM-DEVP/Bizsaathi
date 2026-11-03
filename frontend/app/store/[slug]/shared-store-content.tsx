"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import {
  createPublicChatSession,
  getCurrentCustomerAccount,
  getPublicStore,
  loginCustomerAccount,
  logoutCustomerAccount,
  registerCustomerAccount,
  sendPublicChatMessage,
  subscribeToPublicChatSession,
  PublicChatApiError,
  type PublicCustomerAccount,
  type PublicChatReply,
  type PublicChatSession,
  type PublicStore,
} from "../public-chat-api";
import { useAuth } from "../../context/AuthContext";

interface DisplayMessage {
  id: string;
  sender: "customer" | "assistant" | "owner";
  text: string;
  evidenceIds: string[];
}

export function SharedStoreContent({ slug }: { slug: string }) {
  const { user } = useAuth();
  const [store, setStore] = useState<PublicStore | null>(null);
  const [session, setSession] = useState<PublicChatSession | null>(null);
  const [account, setAccount] = useState<PublicCustomerAccount | null>(null);
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [text, setText] = useState("");
  const [authMode, setAuthMode] = useState<"register" | "login">("register");
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(true);
  const [authBusy, setAuthBusy] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const latestMessageRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let active = true;
    Promise.all([getPublicStore(slug), getCurrentCustomerAccount()])
      .then(([storeResult, accountResult]) => {
        if (!active) return;
        setStore(storeResult);
        setAccount(accountResult);
      })
      .catch((cause: unknown) => {
        if (active) setError(cause instanceof Error ? cause.message : "Could not load this store.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [slug]);

  useEffect(() => {
    if (!account) return;
    let active = true;
    createPublicChatSession(slug)
      .then((result) => {
        if (!active) return;
        setSession(result);
        setMessages(result.messages.map((message) => ({
          id: message.id,
          sender: message.sender,
          text: message.text,
          evidenceIds: message.evidence_ids,
        })));
      })
      .catch((cause: unknown) => {
        if (active) setError(cause instanceof Error ? cause.message : "Could not open your customer chat.");
      });
    return () => {
      active = false;
    };
  }, [account, slug]);

  useEffect(() => {
    latestMessageRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, sending]);

  useEffect(() => {
    if (!account || !session) return;
    return subscribeToPublicChatSession(
      session.session_id,
      (reply) => {
        if (reply.sender !== "owner") return;
        setMessages((current) => current.some((message) => message.id === reply.message_id)
          ? current
          : [...current, {
            id: reply.message_id,
            sender: "owner",
            text: reply.text,
            evidenceIds: reply.evidence_ids,
          }]);
        setNotice("The store owner replied.");
      },
      (cause) => setError(cause.message),
    );
  }, [account, session]);

  async function submitAccount(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAuthBusy(true);
    setError("");
    setNotice("");
    try {
      const signedIn = authMode === "register"
        ? await registerCustomerAccount({ email, display_name: displayName, password })
        : await loginCustomerAccount({ email, password });
      setAccount(signedIn);
      setPassword("");
      setNotice(`Signed in as ${signedIn.display_name}. Your messages are saved to this account.`);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not sign in.");
    } finally {
      setAuthBusy(false);
    }
  }

  async function signOut() {
    try {
      await logoutCustomerAccount();
      setAccount(null);
      setSession(null);
      setMessages([]);
      setNotice("You are signed out.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not sign out.");
    }
  }

  async function submitMessage(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const messageText = text.trim();
    if (!messageText || sending) return;
    setSending(true);
    setError("");
    setNotice("");
    try {
      let activeSession = session ?? await createPublicChatSession(slug);
      setSession(activeSession);
      let reply: PublicChatReply;
      try {
        reply = await sendPublicChatMessage(activeSession.session_id, messageText);
      } catch (cause) {
        if (!(cause instanceof PublicChatApiError) || cause.status !== 409) throw cause;
        activeSession = await createPublicChatSession(slug);
        setSession(activeSession);
        setMessages(activeSession.messages.map((message) => ({
          id: message.id,
          sender: message.sender,
          text: message.text,
          evidenceIds: message.evidence_ids,
        })));
        reply = await sendPublicChatMessage(activeSession.session_id, messageText);
      }
      setMessages((current) => [
        ...current,
        { id: reply.message_id, sender: "customer", text: messageText, evidenceIds: [] },
        {
          id: reply.assistant_message.id,
          sender: "assistant",
          text: reply.assistant_message.text,
          evidenceIds: reply.assistant_message.evidence_ids,
        },
      ]);
      setText("");
      setNotice(reply.escalated
        ? "Seller review requested. No automatic order or payment action was taken."
        : "Answer grounded in this shop’s saved information.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not send your message.");
    } finally {
      setSending(false);
    }
  }

  function askAboutProduct(productName: string) {
    setText(`What is the price and availability of ${productName}?`);
    document.getElementById("public-chat-message")?.focus();
  }

  function askSuggestedQuestion(question: string) {
    setText(question);
    document.getElementById("public-chat-message")?.focus();
  }

  return (
    <main className="shared-store-page">
      <header className="shared-store-hero">
        <div>
          <span className="chip chip-good">Store assistant</span>
          <h1>{store?.business.name ?? "Store chat"}</h1>
          <p>
            Get clear answers about this shop, its products, prices, and saved policies.
          </p>
          <small>
            Answers come from the shop’s saved information. Sensitive order or payment issues are referred to the seller.
          </small>
          {user?.businessSlug === slug && (
            <p>
              <Link className="button" href="/">Open your seller workspace</Link>
            </p>
          )}
        </div>
        <div className="shared-store-hero-mark" aria-hidden="true">B</div>
      </header>

      {error && <p className="form-error" role="alert">{error}</p>}
      {notice && <p className="shared-store-notice" role="status">{notice}</p>}

      {loading ? (
        <section className="surface-card shared-store-card" role="status">Loading store…</section>
      ) : store ? (
        <>
          <section className="surface-card shared-store-card" aria-labelledby="shared-products-heading">
            <div className="shared-store-section-heading">
              <div>
                <span className="shared-store-eyebrow">SHOP CATALOG</span>
                <h2 id="shared-products-heading">Explore the products</h2>
              </div>
              <span className="chip">{store.products.length} listed</span>
            </div>
            {store.products.length === 0 ? (
              <p className="shared-store-empty">No public products are currently listed.</p>
            ) : (
              <ul className="shared-product-grid">
                {store.products.map((product) => (
                  <li key={product.id} className="shared-product-card">
                    <div className="shared-product-card-top">
                      <span className="shared-product-icon" aria-hidden="true">✦</span>
                      <span className={`shared-stock-label${product.in_stock ? " is-in-stock" : ""}`}>
                        {product.in_stock ? "In stock" : "Ask for availability"}
                      </span>
                    </div>
                    <strong>{product.name}</strong>
                    <div className="shared-product-card-bottom">
                      <span>₹{product.price_inr}</span>
                      {account && (
                        <button
                          type="button"
                          className="shared-ask-button"
                          onClick={() => askAboutProduct(product.name)}
                          aria-label={`Ask about ${product.name}`}
                        >
                          Ask about it <span aria-hidden="true">↗</span>
                        </button>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {!account ? (
            <section className="surface-card shared-store-card shared-account-card" aria-labelledby="customer-account-heading">
              <span className="shared-store-eyebrow">PERSONALIZED HELP</span>
              <h2 id="customer-account-heading">{authMode === "register" ? "Create a customer account" : "Sign in to chat"}</h2>
              <p>Your account keeps your conversation available when you return to this store.</p>
              <form onSubmit={submitAccount} className="shared-account-form">
                {authMode === "register" && (
                  <label style={{ display: "grid", gap: 6 }}>
                    Your name
                    <input value={displayName} onChange={(event) => setDisplayName(event.target.value)} maxLength={120} autoComplete="name" required />
                  </label>
                )}
                <label style={{ display: "grid", gap: 6 }}>
                  Email
                  <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} maxLength={320} autoComplete="email" required />
                </label>
                <label style={{ display: "grid", gap: 6 }}>
                  Password
                  <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} minLength={authMode === "register" ? 12 : 1} maxLength={72} autoComplete={authMode === "register" ? "new-password" : "current-password"} required />
                  {authMode === "register" && <small>Use at least 12 characters. Email verification is not enabled yet.</small>}
                </label>
                <button type="submit" className="b p" disabled={authBusy}>
                  {authBusy ? "Working…" : authMode === "register" ? "Create account and continue" : "Sign in and continue"}
                </button>
              </form>
              <button type="button" className="shared-auth-switch" onClick={() => setAuthMode((mode) => mode === "register" ? "login" : "register")}>
                {authMode === "register" ? "Already have an account? Sign in" : "New customer? Create an account"}
              </button>
            </section>
          ) : (
            <section className="surface-card shared-store-card shared-chat-card" aria-labelledby="customer-chat-heading">
              <div className="shared-chat-heading">
                <div className="shared-chat-identity">
                  <span className="shared-assistant-avatar" aria-hidden="true">B</span>
                  <div>
                    <span className="shared-store-eyebrow">SHOP SUPPORT</span>
                  <h2 id="customer-chat-heading">Message the store</h2>
                    <p><span className="shared-online-dot" /> Assistant ready · catalog-aware</p>
                  </div>
                </div>
                <div className="shared-chat-account">
                  <span>Signed in as {account.display_name} · {account.email}</span>
                  <button type="button" className="shared-auth-switch" onClick={() => void signOut()}>Sign out</button>
                </div>
              </div>
              {!session ? (
                <p role="status" className="shared-store-empty">Opening your saved conversation…</p>
              ) : (
                <>
                  <div className="shared-chat-thread" aria-live="polite" aria-label="Conversation messages">
                    {messages.length === 0
                      ? (
                        <div className="shared-chat-welcome">
                          <span className="shared-assistant-avatar" aria-hidden="true">B</span>
                          <div>
                            <strong>Welcome to {store.business.name}</strong>
                            <p>{store.business.description || "I can help with products, prices, availability, and shop policies. What would you like to know?"}</p>
                          </div>
                        </div>
                      )
                      : messages.map((message) => (
                        <article key={message.id} className={`shared-chat-message${message.sender === "customer" ? " from-customer" : " from-assistant"}`}>
                          {message.sender === "assistant" && <span className="shared-assistant-avatar shared-message-avatar" aria-hidden="true">B</span>}
                          <div className="shared-chat-bubble">
                            <small>{message.sender === "customer" ? "You" : message.sender === "owner" ? "Store owner" : store.business.name}</small>
                            <p>{message.text}</p>
                            {message.sender === "assistant" && message.evidenceIds.length > 0 && (
                              <span className="shared-evidence-label"><span aria-hidden="true">✓</span> Based on shop records</span>
                            )}
                          </div>
                        </article>
                      ))}
                    <div ref={latestMessageRef} />
                  </div>
                  <div className="shared-chat-suggestions" aria-label="Suggested questions">
                    {["Show me all products", "What are your prices?", "Tell me about this shop"].map((question) => (
                      <button
                        key={question}
                        type="button"
                        onClick={() => askSuggestedQuestion(question)}
                        disabled={!session || sending}
                      >
                        {question}
                      </button>
                    ))}
                  </div>
                  <form onSubmit={submitMessage} className="shared-chat-composer">
                    <textarea
                      id="public-chat-message"
                      aria-label="Your message"
                      value={text}
                      onChange={(event) => setText(event.target.value)}
                      maxLength={1000}
                      rows={2}
                      placeholder="Ask about products, prices, or shop policies…"
                      required
                    />
                    <button type="submit" className="shared-send-button" disabled={sending || !text.trim()}>
                      {sending ? "Sending…" : "Send"} <span aria-hidden="true">↑</span>
                    </button>
                  </form>
                  <small className="shared-chat-footnote">Shop answers are grounded in saved catalog and policy records.</small>
                </>
              )}
            </section>
          )}
        </>
      ) : (
        <section className="surface-card shared-store-card">
          <h2>Store not available</h2>
          <p>Check the link or contact the store owner.</p>
        </section>
      )}
      <footer className="shared-store-footer"><Link href="/">Powered by BizSaathi</Link><span>Private customer conversation</span></footer>
    </main>
  );
}
