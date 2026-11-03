"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { SellerShell } from "../../components/SellerShell";
import { WorkflowStepper, type WorkflowStep } from "../../components/WorkflowStepper";
import { createCatalogProduct, RuntimeApiError, uploadProductImage, extractProductDetailsFromPhoto } from "@/lib/api-client/runtime";

const inputStyle = {
  width: "100%",
  minHeight: 44,
  padding: "10px 12px",
  border: "1px solid #D5DFDA",
  borderRadius: 10,
  fontSize: 15,
};

type ProductField = "name" | "sku" | "description" | "price" | "stock";

interface SpeechRecognitionResultItem {
  transcript: string;
}

type SpeechRecognitionResult = ArrayLike<SpeechRecognitionResultItem>;

interface SpeechRecognitionEvent extends Event {
  results: ArrayLike<SpeechRecognitionResult>;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
}

interface SpeechRecognitionLike {
  lang: string;
  interimResults: boolean;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
}

type SpeechRecognitionConstructor = new () => SpeechRecognitionLike;
type SpeechWindow = Window & {
  SpeechRecognition?: SpeechRecognitionConstructor;
  webkitSpeechRecognition?: SpeechRecognitionConstructor;
};

const voiceFieldLabels: Record<ProductField, string> = {
  name: "product name",
  sku: "SKU",
  description: "description",
  price: "selling price",
  stock: "stock count",
};

export default function NewProductPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [sku, setSku] = useState("");
  const [description, setDescription] = useState("");
  const [price, setPrice] = useState("");
  const [stock, setStock] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [created, setCreated] = useState("");
  const [createdProductId, setCreatedProductId] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [imageUploaded, setImageUploaded] = useState(false);
  const [voiceStatus, setVoiceStatus] = useState("Voice entry is optional.");
  const [voiceField, setVoiceField] = useState<ProductField | null>(null);
  const [analyzingPhoto, setAnalyzingPhoto] = useState(false);
  const [photoAiNote, setPhotoAiNote] = useState("");
  const speechRef = useRef<SpeechRecognitionLike | null>(null);

  useEffect(() => () => {
    speechRef.current?.stop();
  }, []);
  const workflowSteps: WorkflowStep[] = [
    {
      label: "Product",
      description: createdProductId ? "Confirmed catalog facts" : "Enter facts and price",
      status: createdProductId ? "complete" : "current",
    },
    {
      label: "Create draft",
      description: createdProductId ? "Use the saved product" : "After saving",
      status: createdProductId ? "current" : "upcoming",
    },
    {
      label: "Check claims",
      description: "Verify the current draft",
      status: "upcoming",
    },
    {
      label: "Your review",
      description: "You decide what to share",
      status: "upcoming",
    },
  ];
  const continueToPost = createdProductId
    ? `/posts?product_id=${encodeURIComponent(createdProductId)}`
    : "";

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setCreated("");
    if (!confirmed) {
      setError("Confirm that the entered catalog details are accurate before saving.");
      return;
    }
    if (!/^\d+(?:\.\d{1,2})?$/.test(price) || Number(price) <= 0) {
      setError("Enter the owner-confirmed price in INR, greater than zero, with at most two decimal places.");
      return;
    }
    if (!/^\d+$/.test(stock)) {
      setError("Enter a whole-number stock count confirmed by the owner.");
      return;
    }

    setSaving(true);
    let canContinueToPost = !image;
    try {
      const product = await createCatalogProduct({
        ...(sku.trim() ? { sku: sku.trim() } : {}),
        name: name.trim(),
        ...(description.trim() ? { description: description.trim() } : {}),
        price_inr: price,
        stock: Number(stock),
      });
      setCreated(product.name);
      setCreatedProductId(product.id);
      if (image) {
        try {
          await uploadProductImage(product.id, image);
          setImageUploaded(true);
          setImage(null);
          canContinueToPost = true;
        } catch (uploadError: unknown) {
          setError(`Product saved, but its image did not upload: ${uploadError instanceof Error ? uploadError.message : "upload failed"}. Retry the image upload below.`);
        }
      }
      setName("");
      setSku("");
      setDescription("");
      setPrice("");
      setStock("");
      setConfirmed(false);
      if (canContinueToPost) {
        router.push(`/posts?product_id=${encodeURIComponent(product.id)}&created=1`);
      }
    } catch (cause: unknown) {
      setError(cause instanceof RuntimeApiError ? cause.message : "The product could not be saved. Check the API connection and try again.");
    } finally {
      setSaving(false);
    }
  }

  async function retryImageUpload() {
    if (!createdProductId || !image) return;
    setSaving(true);
    setError("");
    try {
      await uploadProductImage(createdProductId, image);
      setImageUploaded(true);
      setImage(null);
    } catch (cause: unknown) {
      setError(cause instanceof Error ? cause.message : "Image upload failed. Retry when the API is available.");
    } finally {
      setSaving(false);
    }
  }

  function setVoiceValue(field: ProductField, value: string) {
    if (field === "name") setName(value);
    if (field === "sku") setSku(value);
    if (field === "description") setDescription(value);
    if (field === "price") setPrice(value);
    if (field === "stock") setStock(value);
    setConfirmed(false);
  }

  function startVoiceInput(field: ProductField) {
    if (voiceField) {
      speechRef.current?.stop();
      return;
    }

    const speechWindow = window as SpeechWindow;
    const SpeechRecognition = speechWindow.SpeechRecognition ?? speechWindow.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setVoiceStatus("Speech recognition is not supported in this browser. You can type the details instead.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-IN";
    recognition.interimResults = false;
    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((result) => result[0]?.transcript ?? "")
        .join(" ")
        .trim();
      if (transcript) {
        setVoiceValue(field, transcript);
        setVoiceStatus(`Voice transcription added to ${voiceFieldLabels[field]}. Review it before confirming.`);
      }
    };
    recognition.onerror = (event) => setVoiceStatus(`Voice input stopped: ${event.error}. You can type the details instead.`);
    recognition.onend = () => {
      speechRef.current = null;
      setVoiceField(null);
    };
    speechRef.current = recognition;
    setVoiceField(field);
    setVoiceStatus(`Listening for ${voiceFieldLabels[field]}…`);
    recognition.start();
  }

  return (
    <SellerShell>
      <Link href="/products" className="back-link">← Products</Link>
      <section className="page-heading">
        <div>
          <h1>Add a product</h1>
          <p>Only details you confirm are saved as catalog facts. AI suggestions are not used to fill these fields.</p>
        </div>
      </section>

      <div className="product-create-layout">
        <WorkflowStepper
          label="Product to post workflow"
          context={createdProductId ? `${created} is ready` : "Start with confirmed details"}
          steps={workflowSteps}
          nextAction={createdProductId
            ? {
                label: "Create a post",
                description: "Continue with this product already selected.",
                href: continueToPost,
              }
            : {
                label: "Enter product details",
                description: "Confirm the product name, price, and stock before saving.",
                href: "#product-form",
              }}
        />

        <div className="product-create-content">
          {error && <p role="alert" className="surface-card" style={{ padding: 14, color: "#8A1F1F", background: "#FCECEA" }}>{error}</p>}
          {created && (
            <p role="status" className="surface-card" style={{ padding: 14, color: "#0B6E5C", background: "#F2F9F6" }}>
              {created} was saved to your confirmed catalog. {imageUploaded ? "The image is stored." : image ? "The product is saved; image upload is pending." : ""}
            </p>
          )}

          {image && createdProductId && !imageUploaded && <button type="button" className="button" onClick={() => void retryImageUpload()} disabled={saving}>Retry image upload</button>}
          <form id="product-form" onSubmit={handleSubmit} className="surface-card product-create-form">
        <fieldset className="voice-entry">
          <legend>Enter details by voice</legend>
          <p>Choose a field, then speak. Voice text is not saved until you review it and confirm the product.</p>
          <div className="voice-entry-actions">
            {(Object.keys(voiceFieldLabels) as ProductField[]).map((field) => (
              <button
                key={field}
                type="button"
                className="button"
                onClick={() => startVoiceInput(field)}
                aria-pressed={voiceField === field}
                disabled={voiceField !== null && voiceField !== field}
              >
                {voiceField === field ? "Stop listening" : `Use voice for ${voiceFieldLabels[field]}`}
              </button>
            ))}
          </div>
          <small role="status">{voiceStatus}</small>
          <small>Browser speech recognition may use your browser’s voice service. Price and stock may need numeric editing.</small>
        </fieldset>
        <label style={{ display: "grid", gap: 6, fontWeight: 600 }}>
          Product name
          <input required maxLength={200} value={name} onChange={(event) => setName(event.target.value)} style={inputStyle} />
        </label>
        <label style={{ display: "grid", gap: 6, fontWeight: 600 }}>
          SKU <span style={{ fontWeight: 400, color: "#68766F" }}>(optional)</span>
          <input maxLength={64} value={sku} onChange={(event) => setSku(event.target.value)} style={inputStyle} />
        </label>
        <label style={{ display: "grid", gap: 6, fontWeight: 600 }}>
          Product photo <span style={{ fontWeight: 400, color: "#68766F" }}>(JPEG, PNG, or WebP; maximum 10 MB)</span>
          <input type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => { setImage(event.target.files?.[0] ?? null); setImageUploaded(false); setPhotoAiNote(""); }} />
          {image && (
            <div style={{ display: "flex", gap: 10, alignItems: "center", marginTop: 6, flexWrap: "wrap" }}>
              <button
                type="button"
                className="button"
                disabled={analyzingPhoto || saving}
                onClick={async () => {
                  if (!image) return;
                  setAnalyzingPhoto(true);
                  setPhotoAiNote("AI agent is analyzing photo in pipeline...");
                  setError("");
                  try {
                    const info = await extractProductDetailsFromPhoto(image);
                    if (info.name && !name) setName(info.name);
                    if (info.description && !description) setDescription(info.description);
                    setPhotoAiNote("Photo analyzed! Suggested details loaded into form. Please verify and confirm price.");
                  } catch (err: unknown) {
                    setPhotoAiNote("");
                    setError(err instanceof Error ? err.message : "Failed to extract product from photo.");
                  } finally {
                    setAnalyzingPhoto(false);
                  }
                }}
              >
                {analyzingPhoto ? "Scanning Photo with AI…" : "✨ Scan Photo to Auto-fill"}
              </button>
              {photoAiNote && <small style={{ color: "#0B6E5C", fontWeight: 600 }}>{photoAiNote}</small>}
            </div>
          )}
        </label>
        <label style={{ display: "grid", gap: 6, fontWeight: 600 }}>
          Description <span style={{ fontWeight: 400, color: "#68766F" }}>(optional; use only confirmed details)</span>
          <textarea maxLength={5000} rows={4} value={description} onChange={(event) => setDescription(event.target.value)} style={{ ...inputStyle, resize: "vertical" }} />
        </label>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 14 }}>
          <label style={{ display: "grid", gap: 6, fontWeight: 600 }}>
            Confirmed selling price (INR)
            <input required inputMode="decimal" type="number" min="0.01" step="0.01" value={price} onChange={(event) => setPrice(event.target.value)} style={inputStyle} />
          </label>
          <label style={{ display: "grid", gap: 6, fontWeight: 600 }}>
            Confirmed stock count
            <input required inputMode="numeric" type="number" min="0" step="1" value={stock} onChange={(event) => setStock(event.target.value)} style={inputStyle} />
          </label>
        </div>
        <label style={{ display: "flex", gap: 10, alignItems: "flex-start", lineHeight: 1.5 }}>
          <input type="checkbox" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} />
          <span>I confirm these product details and price are accurate.</span>
        </label>
        <button className="button button-primary" type="submit" disabled={saving}>
          {saving ? "Saving…" : "Save confirmed product"}
        </button>
          </form>
        </div>
      </div>
    </SellerShell>
  );
}
