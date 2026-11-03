"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { SellerShell } from "../components/SellerShell";
import { WorkflowStepper, type WorkflowStep } from "../components/WorkflowStepper";
import {
  checkDraftClaims,
  fetchProductImageForShare,
  generateDraftPostStream,
  generateQuickDraftPost,
  listCatalogProducts,
  listDraftPosts,
  RuntimeApiError,
  updateDraftPost,
  type ClaimCheck,
  type DraftPost,
  type CatalogProduct,
} from "@/lib/api-client/runtime";
import { getCurrentBusinessProfile } from "./share-widget-api";

const channels: Array<{ value: DraftPost["channel"]; label: string }> = [
  { value: "instagram", label: "Instagram" },
  { value: "facebook", label: "Facebook" },
  { value: "whatsapp_status", label: "WhatsApp status" },
  { value: "generic", label: "Other" },
];

const languages: Array<{ value: DraftPost["language"]; label: string }> = [
  { value: "en", label: "English" },
  { value: "hi", label: "Hindi" },
  { value: "mr", label: "Marathi" },
];

const fieldStyle = {
  width: "100%",
  minHeight: 44,
  padding: "10px 12px",
  border: "1px solid #D5DFDA",
  borderRadius: 10,
  background: "#fff",
  color: "#12201B",
  fontSize: 15,
};

function errorMessage(error: unknown): string {
  if (error instanceof RuntimeApiError) return error.message;
  return "The request could not be completed. Check the API connection and try again.";
}

function formatPrice(value: string | number): string {
  const amount = Number(value);
  return Number.isFinite(amount)
    ? new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(amount)
    : "Price unavailable";
}

export default function PostsPage() {
  const productFormRef = useRef<HTMLFormElement>(null);
  const [products, setProducts] = useState<CatalogProduct[]>([]);
  const [posts, setPosts] = useState<DraftPost[]>([]);
  const [productId, setProductId] = useState("");
  const [channel, setChannel] = useState<DraftPost["channel"]>("instagram");
  const [language, setLanguage] = useState<DraftPost["language"]>("en");
  const [selectedId, setSelectedId] = useState("");
  const [editedText, setEditedText] = useState("");
  const [loading, setLoading] = useState(true);
  const [businessProfile, setBusinessProfile] = useState<{ name: string; slug: string } | null>(null);
  const [businessProfileError, setBusinessProfileError] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [streamingLines, setStreamingLines] = useState<string[]>([]);
  const [generationStatus, setGenerationStatus] = useState("");
  const [claimCheck, setClaimCheck] = useState<ClaimCheck | null>(null);
  const [reviewedDraftKey, setReviewedDraftKey] = useState("");
  const [forwardedDraftKey, setForwardedDraftKey] = useState("");
  const [widgetUrl, setWidgetUrl] = useState("");
  const [shareImageState, setShareImageState] = useState<{
    key: string;
    status: "ready" | "unavailable";
    image?: File;
    message?: string;
  } | null>(null);

  const selectedPost = posts.find((post) => post.id === selectedId) ?? null;
  const selectedProductId = selectedPost?.product_id;
  const draftNeedsSaving = Boolean(selectedPost && editedText.trim() !== selectedPost.text);
  const claimCheckIsCurrent = Boolean(
    selectedPost &&
    claimCheck?.post_id === selectedPost.id &&
    claimCheck.version === selectedPost.version &&
    !draftNeedsSaving,
  );
  const reviewedCurrentDraft = Boolean(
    selectedPost && reviewedDraftKey === `${selectedPost.id}:${selectedPost.version}`,
  );
  const forwardedCurrentDraft = Boolean(
    selectedPost && forwardedDraftKey === `${selectedPost.id}:${selectedPost.version}`,
  );
  const shareImageKey = selectedPost ? `${selectedPost.id}:${selectedPost.version}` : "";
  const currentShareImage = reviewedCurrentDraft && shareImageState?.key === shareImageKey
    ? shareImageState
    : null;
  const shareImageStatus = !reviewedCurrentDraft
    ? "idle"
    : currentShareImage?.status ?? "loading";

  useEffect(() => {
    let cancelled = false;
    if (!selectedProductId || !reviewedCurrentDraft) {
      return () => {
        cancelled = true;
      };
    }

    fetchProductImageForShare(selectedProductId)
      .then((image) => {
        if (cancelled) return;
        setShareImageState({ key: shareImageKey, status: "ready", image });
      })
      .catch((cause: unknown) => {
        if (cancelled) return;
        setShareImageState({
          key: shareImageKey,
          status: "unavailable",
          message: errorMessage(cause),
        });
      });
    return () => {
      cancelled = true;
    };
  }, [selectedProductId, reviewedCurrentDraft, shareImageKey]);
  const workflowSteps: WorkflowStep[] = [
    {
      label: "Product",
      description: productId ? "Confirmed catalog facts" : "Choose a saved product",
      status: productId ? "complete" : "current",
    },
    {
      label: "Create draft",
      description: selectedPost ? "Draft saved" : "Generate from your product",
      status: selectedPost ? "complete" : productId ? "current" : "upcoming",
    },
    {
      label: "Check claims",
      description: claimCheckIsCurrent ? "Results ready to review" : "Verify the current draft",
      status: claimCheckIsCurrent ? "complete" : selectedPost ? "current" : "upcoming",
    },
    {
      label: "Your review",
      description: reviewedCurrentDraft ? "You approved this wording" : "Review the full post and claim results",
      status: reviewedCurrentDraft ? "complete" : claimCheckIsCurrent ? "current" : "upcoming",
    },
    {
      label: "Forward to app",
      description: forwardedCurrentDraft
        ? "Share sheet used; finish posting in the chosen app"
        : "Forward the reviewed copy with your device share sheet",
      status: forwardedCurrentDraft ? "complete" : reviewedCurrentDraft ? "current" : "upcoming",
    },
  ];

  const workflowAction = loading
    ? {
        label: "Loading…",
        description: "Loading your confirmed products and recent drafts.",
        onClick: () => undefined,
        disabled: true,
      }
    : products.length === 0
      ? {
        label: "Add a product",
        description: "Start with a product and price you have confirmed.",
        href: "/products/new",
      }
      : !productId
        ? {
          label: "Choose a product",
          description: "Select an active product with a confirmed price.",
          href: "/products",
        }
        : !selectedPost
          ? {
            label: busy ? "Generating…" : "Generate draft",
            description: "Create a draft from the selected product facts.",
            onClick: () => productFormRef.current?.requestSubmit(),
            disabled: busy || loading,
          }
          : draftNeedsSaving
            ? {
              label: busy ? "Saving…" : "Save edits",
              description: "Save your changes before checking the updated copy.",
              onClick: () => void handleSave(),
              disabled: busy || !editedText.trim(),
            }
            : !claimCheckIsCurrent
              ? {
                label: busy ? "Checking…" : "Check claims",
                description: "Check the draft against the evidence before using it.",
                onClick: () => void handleCheck(),
                disabled: busy,
              }
              : !reviewedCurrentDraft
                ? {
                  label: "Confirm review",
                  description: "Confirm you reviewed the current wording and claim-check results.",
                  onClick: () => confirmDraftReview(),
                  disabled: busy,
                }
                : {
                  label: forwardedCurrentDraft ? "Forward again" : "Forward to social app",
                  description: "Open your device share sheet. You choose the app and complete posting there.",
                  onClick: () => void forwardReviewedDraft(),
                  disabled: busy,
                };

  useEffect(() => {
    let cancelled = false;
    getCurrentBusinessProfile()
      .then((profile) => {
        if (!cancelled) {
          setBusinessProfile(profile);
          setBusinessProfileError("");
        }
      })
      .catch((cause: unknown) => {
        if (!cancelled) setBusinessProfileError(errorMessage(cause));
      });
    Promise.all([listCatalogProducts(), listDraftPosts()])
      .then(([catalog, drafts]) => {
        if (cancelled) return;
        setProducts(catalog.filter((product) => product.status === "active"));
        setPosts(drafts);
        const requestedProductId = new URLSearchParams(window.location.search).get("product_id");
        const requestedProduct = catalog.find(
          (product) => product.status === "active" && product.id === requestedProductId,
        );
        const activeProductId =
          requestedProduct?.id ?? catalog.find((product) => product.status === "active")?.id ?? "";
        setProductId(activeProductId);
        const initialDraft = drafts.find((draft) => draft.product_id === activeProductId);
        if (initialDraft) {
          setSelectedId(initialDraft.id);
          setEditedText(initialDraft.text);
        }
        if (new URLSearchParams(window.location.search).get("created") === "1" && requestedProduct) {
          setNotice(`${requestedProduct.name} is ready. Choose a channel and generate its first post draft.`);
        }
      })
      .catch((cause: unknown) => {
        if (!cancelled) setError(errorMessage(cause));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleGenerate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!productId) {
      setError("Add a confirmed, active product with a price before generating a post.");
      return;
    }
    setBusy(true);
    setError("");
    setNotice("");
    setStreamingLines(["", ""]);
    setGenerationStatus("Connecting to the model stream…");
    try {
      const post = await generateDraftPostStream(
        productId,
        channel,
        language,
        (lineIndex, text) => {
          if (lineIndex < 0 || lineIndex > 1) return;
          setStreamingLines((current) => {
            const next = [...current];
            next[lineIndex] = text;
            return next;
          });
        },
        setGenerationStatus,
      );
      setPosts((current) => [post, ...current]);
      setSelectedId(post.id);
      setEditedText(post.text);
      setClaimCheck(null);
      setReviewedDraftKey("");
      setForwardedDraftKey("");
      setStreamingLines([]);
      setGenerationStatus("");
      setNotice(post.provenance.mode === "mock"
        ? "Draft generated in MOCK mode, not by the live AI model. Review the suggestion and evidence; configure a live provider on the server for live generation."
        : "Draft generated by the live AI model. Review the unverified suggestion and evidence before using it.");
      window.requestAnimationFrame(() => {
        const preview = document.getElementById("draft-preview");
        preview?.scrollIntoView({
          behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
          block: "start",
        });
        preview?.focus({ preventScroll: true });
      });
    } catch (cause: unknown) {
      setError(errorMessage(cause));
    } finally {
      setBusy(false);
      setGenerationStatus("");
    }
  }

  async function handleQuickGenerate() {
    if (!productId) {
      setError("Add a confirmed, active product with a price before generating a post.");
      return;
    }
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const post = await generateQuickDraftPost(productId, channel, language);
      setPosts((current) => [post, ...current]);
      setSelectedId(post.id);
      setEditedText(post.text);
      setClaimCheck(null);
      setReviewedDraftKey("");
      setForwardedDraftKey("");
      setStreamingLines([]);
      setNotice("Instant local template created—no AI was called. Edit it as needed, and review its claims before sharing.");
      window.requestAnimationFrame(() => {
        const preview = document.getElementById("draft-preview");
        preview?.scrollIntoView({
          behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
          block: "start",
        });
        preview?.focus({ preventScroll: true });
      });
    } catch (cause: unknown) {
      setError(errorMessage(cause));
    } finally {
      setBusy(false);
    }
  }

  async function handleSave() {
    if (!selectedPost || editedText.trim() === selectedPost.text) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const updated = await updateDraftPost(selectedPost, editedText.trim());
      setPosts((current) => current.map((post) => (post.id === updated.id ? updated : post)));
      setClaimCheck(null);
      setReviewedDraftKey("");
      setForwardedDraftKey("");
      setNotice("Draft saved. Previous claim checks were invalidated because the text changed.");
    } catch (cause: unknown) {
      setError(errorMessage(cause));
    } finally {
      setBusy(false);
    }
  }

  async function handleCheck() {
    if (!selectedPost) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const result = await checkDraftClaims(selectedPost);
      setClaimCheck(result);
      setPosts((current) => current.map((post) =>
        post.id === result.post_id
          ? { ...post, status: "checked", claims: result.claims }
          : post,
      ));
      setNotice("Claim review completed. Any unverified suggestion still needs your review.");
    } catch (cause: unknown) {
      setError(errorMessage(cause));
    } finally {
      setBusy(false);
    }
  }

  function confirmDraftReview() {
    if (
      !selectedPost ||
      !claimCheck ||
      claimCheck.post_id !== selectedPost.id ||
      claimCheck.version !== selectedPost.version ||
      editedText.trim() !== selectedPost.text ||
      claimCheck.overall === "fail"
    ) {
      setError("Review requires a current claim check with no contradicted claims. Resolve the findings before sharing.");
      return;
    }

    if (!window.confirm(
      `The claim check is ${claimCheck.overall.replace("_", " ")}. Confirm that you reviewed every statement and its evidence. BizSaathi will not publish the post.`,
    )) return;
    setReviewedDraftKey(`${selectedPost.id}:${selectedPost.version}`);
    setForwardedDraftKey("");
    setNotice("Review confirmed for this draft version. Choose Forward to social app when ready.");
    setError("");
  }

  async function copyReviewedDraft() {
    if (
      !selectedPost ||
      !reviewedCurrentDraft ||
      !claimCheckIsCurrent ||
      claimCheck?.overall === "fail"
    ) {
      setError("Review and confirm the current checked draft before copying it.");
      return;
    }

    try {
      await navigator.clipboard.writeText(selectedPost.text);
      setNotice("Post text copied. Paste it into your chosen social app and complete posting there.");
      setError("");
    } catch (cause: unknown) {
      setError(cause instanceof Error
        ? `Could not copy the post: ${cause.message}`
        : "Clipboard access was denied. Select and copy the post text manually.");
    }
  }

  async function forwardReviewedDraft() {
    if (
      !selectedPost ||
      !reviewedCurrentDraft ||
      !claimCheckIsCurrent ||
      claimCheck?.overall === "fail"
    ) {
      setError("Review and confirm the current checked draft before forwarding it.");
      return;
    }
    if (!businessProfile) {
      setError(businessProfileError || "The public chat link is still loading. Try again shortly.");
      return;
    }

    setError("");
    setNotice("");
    const image = currentShareImage?.image;
    if (!image) {
      setError(currentShareImage?.message || "The verified product image is not ready to share. Wait for it to load or check that one is uploaded.");
      return;
    }
    if (typeof navigator.share !== "function" || typeof navigator.canShare !== "function") {
      setError("This browser does not support sharing image files. Use Copy post text and attach the product image in your social app.");
      return;
    }

    try {
      if (!navigator.canShare({ files: [image] })) {
        setError("This browser or device cannot share image files. Use Copy post text and attach the product image in your social app.");
        return;
      }
      const chatUrl = new URL(
        `/store/${encodeURIComponent(businessProfile.slug)}`,
        window.location.origin,
      ).toString();
      await navigator.share({
        title: `${products.find((product) => product.id === selectedPost.product_id)?.name ?? "Product"} post`,
        text: `${selectedPost.text}\n\nChat with ${businessProfile.name}: ${chatUrl}`,
        url: chatUrl,
        files: [image],
      });
      setForwardedDraftKey(`${selectedPost.id}:${selectedPost.version}`);
      setNotice("Share sheet completed. Choose the social app and finish posting there; BizSaathi has not published it.");
    } catch (cause: unknown) {
      if (cause instanceof DOMException && cause.name === "AbortError") {
        setNotice("Sharing was cancelled. Your reviewed draft is unchanged.");
        return;
      }
      setError(cause instanceof Error
        ? `Could not open the share sheet: ${cause.message}`
        : "Could not open the share sheet. Use Copy post text and attach the product image in your social app.");
    }
  }

  async function shareWidgetLink() {
    if (!businessProfile) {
      setError(businessProfileError || "The public chat link is still loading. Try again shortly.");
      return;
    }
    const url = new URL(
      `/store/${encodeURIComponent(businessProfile.slug)}`,
      window.location.origin,
    ).toString();
    setWidgetUrl(url);
    setError("");
    try {
      if (typeof navigator.share === "function") {
        await navigator.share({
          title: `Chat with ${businessProfile.name}`,
          text: `Ask ${businessProfile.name} about products in its confirmed catalog.`,
          url,
        });
        setNotice("Customer chat link shared. It opens on this app's current host.");
      } else {
        await navigator.clipboard.writeText(url);
        setNotice("Customer chat link copied. Share it with customers to open the public chat.");
      }
    } catch (cause: unknown) {
      if (cause instanceof DOMException && cause.name === "AbortError") {
        setNotice("Link sharing was cancelled. The customer chat link is still available below.");
        return;
      }
      setError(cause instanceof Error
        ? `Could not share the customer chat link: ${cause.message}`
        : "Could not share the customer chat link. Copy the link shown below.");
    }
  }

  return (
    <SellerShell>
      <Link href="/" style={{ color: "#0B6E5C", fontWeight: 600, textDecoration: "none" }}>
        ← Home
      </Link>
      <header style={{ marginTop: 16 }}>
        <p style={{ margin: 0, color: "#0B6E5C", fontSize: 13, fontWeight: 700, letterSpacing: ".08em" }}>
          CONTENT STUDIO
        </p>
        <h1 style={{ margin: "6px 0", fontSize: 30, letterSpacing: "-.03em" }}>Create a post</h1>
        <p style={{ maxWidth: 680, color: "#5B6A64", lineHeight: 1.6 }}>
          Start from your confirmed catalog. The AI contributes only a creative suggestion; product facts and price come from your catalog.
        </p>
      </header>

      {error && <p role="alert" style={{ padding: 12, borderRadius: 10, background: "#FCECEA", color: "#8A1F1F" }}>{error}</p>}
      {notice && <p role="status" style={{ padding: 12, borderRadius: 10, background: "#E4F1EC", color: "#0B6E5C" }}>{notice}</p>}

      <div className="post-studio">
        <WorkflowStepper
          label="Post workflow"
          context={products.find((product) => product.id === productId)?.name ?? "Post draft"}
          steps={workflowSteps}
          nextAction={workflowAction}
        />
        <section id="generate-title" aria-labelledby="generate-heading" style={{ padding: 20, border: "1px solid #E1E8E4", borderRadius: 16, background: "#fff" }}>
          <h2 id="generate-heading" style={{ marginTop: 0, fontSize: 19 }}>Your product</h2>
          <form ref={productFormRef} onSubmit={handleGenerate} style={{ display: "grid", gap: 14 }}>
            <label style={{ display: "grid", gap: 6, color: "#42524B", fontSize: 14, fontWeight: 600 }}>
              Confirmed product
              <select value={productId} onChange={(event) => {
                setProductId(event.target.value);
                setSelectedId("");
                setEditedText("");
                setClaimCheck(null);
                setReviewedDraftKey("");
                setForwardedDraftKey("");
              }} style={fieldStyle} disabled={loading || products.length === 0}>
                <option value="">{loading ? "Loading catalog…" : "Select a product"}</option>
                {products.map((product) => (
                  <option key={product.id} value={product.id}>
                    {product.name} · {formatPrice(product.price_inr)}
                  </option>
                ))}
              </select>
              <span style={{ color: "#5B6A64", fontSize: 13, fontWeight: 400, lineHeight: 1.5 }}>
                Copy can use features from the product’s saved description and attributes. Add accurate product details in your catalog for more specific lines.
              </span>
            </label>
            <label style={{ display: "grid", gap: 6, color: "#42524B", fontSize: 14, fontWeight: 600 }}>
              Channel
              <select value={channel} onChange={(event) => setChannel(event.target.value as DraftPost["channel"])} style={fieldStyle}>
                {channels.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
              </select>
            </label>
            <label style={{ display: "grid", gap: 6, color: "#42524B", fontSize: 14, fontWeight: 600 }}>
              Language
              <select value={language} onChange={(event) => setLanguage(event.target.value as DraftPost["language"])} style={fieldStyle}>
                {languages.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
              </select>
            </label>
            <button type="submit" disabled={busy || loading || products.length === 0} style={{ ...fieldStyle, border: 0, background: "#0B6E5C", color: "#fff", fontWeight: 700, cursor: "pointer" }}>
              {busy ? "Working…" : "Generate draft"}
            </button>
            <button type="button" onClick={() => void handleQuickGenerate()} disabled={busy || loading || products.length === 0} style={{ ...fieldStyle, border: "1px solid #D5DFDA", background: "#fff", color: "#12201B", fontWeight: 700, cursor: "pointer" }}>
              {busy ? "Working…" : "Quick local draft (no AI)"}
            </button>
            <p style={{ margin: "-6px 0 0", color: "#5B6A64", fontSize: 13, lineHeight: 1.5 }}>
              Creates an instant English, Hindi, or Marathi template using catalog-verified product name and price; it does not call the AI provider.
            </p>
          </form>
          {!loading && products.length === 0 && (
            <p style={{ marginBottom: 0, color: "#7A4A08", fontSize: 14, lineHeight: 1.5 }}>
              No active confirmed products are available. Add a product and owner-confirm its price first.
            </p>
          )}
          {posts.length > 0 && (
            <div style={{ marginTop: 20, borderTop: "1px solid #E1E8E4", paddingTop: 14 }}>
              <h3 style={{ margin: "0 0 8px", fontSize: 15 }}>Recent drafts</h3>
              <ul style={{ display: "grid", gap: 8, margin: 0, padding: 0, listStyle: "none" }}>
                {posts.map((post) => (
                  <li key={post.id}>
                    <button type="button" onClick={() => {
                      setSelectedId(post.id);
                      setProductId(post.product_id);
                      setEditedText(post.text);
                      setClaimCheck(null);
                      setReviewedDraftKey("");
                      setForwardedDraftKey("");
                    }} aria-pressed={post.id === selectedId} style={{ width: "100%", padding: 10, textAlign: "left", border: "1px solid #E1E8E4", borderRadius: 10, background: post.id === selectedId ? "#F2F9F6" : "#fff", color: "#12201B", cursor: "pointer" }}>
                      <span style={{ display: "block", fontWeight: 600 }}>{channels.find((item) => item.value === post.channel)?.label ?? post.channel}</span>
                      <span style={{ display: "block", marginTop: 3, color: "#5B6A64", fontSize: 12 }}>{new Date(post.created_at).toLocaleString()}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>

        <section id="draft-preview" tabIndex={-1} aria-labelledby="draft-title" style={{ minWidth: 0, padding: 20, border: "1px solid #E1E8E4", borderRadius: 16, background: "#fff", scrollMarginTop: 20 }}>
          <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", gap: 12, alignItems: "center" }}>
            <h2 id="draft-title" style={{ margin: 0, fontSize: 19 }}>Draft preview</h2>
            {selectedPost && <span style={{ padding: "5px 9px", borderRadius: 999, background: selectedPost.provenance.model_id === "quick-local-template-v1" || selectedPost.provenance.mode === "mock" ? "#FFF8EE" : "#F2F9F6", color: selectedPost.provenance.model_id === "quick-local-template-v1" || selectedPost.provenance.mode === "mock" ? "#8A4B08" : "#0B6E5C", fontSize: 12, fontWeight: 700 }}>{selectedPost.provenance.model_id === "quick-local-template-v1" ? "LOCAL TEMPLATE · NO AI" : selectedPost.provenance.mode === "mock" ? "MOCK AI" : "LIVE AI"}</span>}
          </div>
          {!selectedPost ? (
            <div style={{ padding: "48px 12px", textAlign: "center", color: "#5B6A64" }}>
              <p style={{ margin: 0, fontWeight: 600 }}>{loading ? "Loading your drafts…" : "Your generated draft will appear here."}</p>
              <p style={{ marginBottom: 0, fontSize: 14 }}>No sample catalog or post is substituted when the API is unavailable.</p>
              {(busy || streamingLines.some(Boolean)) && (
                <div role="status" aria-live="polite" style={{ marginTop: 16, padding: 14, borderRadius: 12, background: "#F2F9F6", textAlign: "left" }}>
                  <strong>Streaming AI suggestion · not yet saved or verified</strong>
                  <p style={{ margin: "8px 0", color: "#5B6A64", fontSize: 13 }}>{generationStatus || "Receiving generated text…"}</p>
                  {streamingLines.map((line, index) => line && (
                    <p key={index} style={{ margin: "8px 0", lineHeight: 1.6 }}>{line}</p>
                  ))}
                  {!streamingLines.some(Boolean) && <p style={{ margin: 0 }}>Waiting for the first generated text…</p>}
                  <small>Catalog facts are added and checked by the server after generation completes.</small>
                </div>
              )}
            </div>
          ) : (
            <>
              <p style={{ color: "#7A4A08", fontSize: 13, lineHeight: 1.5 }}>
                AI suggestion — review every claim and its evidence. Forwarding opens your device share sheet; you choose the app and finish posting there. BizSaathi never publishes or schedules externally.
              </p>
              <label htmlFor="draft-text" style={{ display: "block", marginBottom: 6, color: "#42524B", fontSize: 14, fontWeight: 600 }}>Post copy</label>
              <textarea id="draft-text" value={editedText} onChange={(event) => {
                setEditedText(event.target.value);
                setReviewedDraftKey("");
                setForwardedDraftKey("");
              }} rows={9} maxLength={4000} style={{ ...fieldStyle, minHeight: 200, resize: "vertical", lineHeight: 1.6 }} />
              <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginTop: 12 }}>
                <button type="button" onClick={handleSave} disabled={busy || editedText.trim() === selectedPost.text || !editedText.trim()} style={{ ...fieldStyle, width: "auto", border: 0, background: "#12201B", color: "#fff", fontWeight: 700, cursor: "pointer" }}>Save edits</button>
                <button type="button" onClick={handleCheck} disabled={busy || editedText.trim() !== selectedPost.text} style={{ ...fieldStyle, width: "auto", background: "#fff", color: "#0B6E5C", fontWeight: 700, cursor: "pointer" }}>Check claims</button>
                <button
                  type="button"
                  onClick={confirmDraftReview}
                  disabled={busy || !claimCheckIsCurrent || claimCheck?.overall === "fail"}
                  style={{ ...fieldStyle, width: "auto", background: "#fff", color: "#0B6E5C", fontWeight: 700, cursor: "pointer" }}
                >
                  {reviewedCurrentDraft ? "Review confirmed" : "Confirm review"}
                </button>
                {reviewedCurrentDraft && (
                  <>
                    <button
                      type="button"
                      onClick={() => void forwardReviewedDraft()}
                      disabled={busy || !claimCheckIsCurrent || claimCheck?.overall === "fail" || shareImageStatus === "loading" || !businessProfile}
                      style={{ ...fieldStyle, width: "auto", border: 0, background: "#0B6E5C", color: "#fff", fontWeight: 700, cursor: "pointer" }}
                    >
                      {shareImageStatus === "loading" ? "Loading image…" : "Forward post + image"}
                    </button>
                    <button
                      type="button"
                      onClick={() => void shareWidgetLink()}
                      disabled={busy || !businessProfile}
                      style={{ ...fieldStyle, width: "auto", background: "#fff", color: "#0B6E5C", fontWeight: 700, cursor: "pointer" }}
                    >
                      Share chat widget
                    </button>
                    <button
                      type="button"
                      onClick={() => void copyReviewedDraft()}
                      disabled={busy || !claimCheckIsCurrent || claimCheck?.overall === "fail"}
                      style={{ ...fieldStyle, width: "auto", background: "#fff", color: "#0B6E5C", fontWeight: 700, cursor: "pointer" }}
                    >
                      Copy post text
                    </button>
                  </>
                )}
              </div>
              {businessProfileError && (
                <p role="alert" style={{ color: "#8A1F1F", fontSize: 13, lineHeight: 1.5 }}>
                  Could not load the public chat link: {businessProfileError}
                </p>
              )}
              {widgetUrl && (
                <p style={{ marginTop: 10, fontSize: 13, overflowWrap: "anywhere" }}>
                  Public customer chat: <a href={widgetUrl} target="_blank" rel="noreferrer">{widgetUrl}</a>
                </p>
              )}
              {reviewedCurrentDraft && shareImageStatus === "unavailable" && (
                <p role="alert" style={{ color: "#8A1F1F", fontSize: 13, lineHeight: 1.5 }}>
                  {currentShareImage?.message}
                </p>
              )}
              {reviewedCurrentDraft && shareImageStatus === "ready" && (
                <p role="status" style={{ color: "#0B6E5C", fontSize: 13 }}>
                  The verified uploaded product image will be attached to the share.
                </p>
              )}
              {claimCheck && (
                <div role="status" style={{ marginTop: 18, padding: 14, borderRadius: 12, background: claimCheck.overall === "pass" ? "#F2F9F6" : "#FFF8EE", color: "#42524B" }}>
                  <strong>Claim check: {claimCheck.overall.replace("_", " ")}</strong>
                  {claimCheck.claims.length === 0 && <p>No structured claims were checked. Review every sentence manually; this is not approval.</p>}
                  <p style={{ margin: "6px 0 10px", fontSize: 13 }}>
                    {claimCheck.summary.supported} supported · {claimCheck.summary.contradicted} contradicted · {claimCheck.summary.unverified} unverified
                  </p>
                  {claimCheck.claims.map((claim) => (
                    <div key={claim.id} style={{ padding: "9px 0", borderTop: "1px solid #D5DFDA", fontSize: 13 }}>
                      <span style={{ fontWeight: 600 }}>{claim.verdict ?? "unverified"}: </span>{claim.text}
                      {claim.evidence_ids.length > 0 && <span> · {claim.evidence_ids.length} evidence record(s)</span>}
                      {claim.repair_suggestion && <p style={{ margin: "4px 0 0" }}>{claim.repair_suggestion}</p>}
                    </div>
                  ))}
                </div>
              )}
              <p style={{ marginBottom: 0, color: "#68766F", fontSize: 12 }}>Draft version {selectedPost.version} · {selectedPost.status}</p>
            </>
          )}
        </section>
      </div>
    </SellerShell>
  );
}
