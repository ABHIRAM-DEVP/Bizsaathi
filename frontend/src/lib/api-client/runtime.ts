"use client";

import { getBrowserApiUrl } from "../../../app/lib/api-url";

export interface CatalogProduct {
  id: string;
  name: string;
  price_inr: string | number;
  status: string;
  description?: string | null;
  version: number;
  stock: number;
  stock_version: number;
}

export interface PostClaim {
  id: string;
  text: string;
  kind: string;
  verdict: "supported" | "contradicted" | "unverified" | null;
  severity: string | null;
  repair_suggestion: string | null;
  evidence_ids: string[];
}

export interface DraftPost {
  id: string;
  product_id: string;
  channel: "instagram" | "whatsapp_status" | "facebook" | "generic";
  language: "en" | "hi" | "mr";
  text: string;
  version: number;
  status: string;
  provenance: { mode?: "mock" | "live"; model_id?: string };
  claims: PostClaim[];
  created_at: string;
  updated_at: string;
}

export interface DashboardSummary {
  pending_approvals: number;
  open_escalations: number;
  recent_jobs: Array<{ id: string; kind: string; status: string; created_at: string }>;
  low_stock: Array<{ id: string; sku: string | null; name: string; price_inr: string | number; status: string; stock_total: number; thumbnail_url: string | null }>;
  next_step: { label: string; route: string } | null;
}

export interface CustomerOrder {
  id: string;
  status: "DRAFT" | "AWAITING_PAYMENT" | "PAID" | "FULFILLED" | "CANCELLED" | "FAILED";
  customer_name: string;
  total_inr: string | number;
  payment_method: "cash" | "upi" | "bank" | "other" | null;
  delivery_note: string | null;
  demo_sample: boolean;
  created_at: string;
  items: Array<{
    variant_id: string;
    product_name: string;
    quantity: number;
    unit_price_inr: string | number;
  }>;
}

export function listOrders(): Promise<CustomerOrder[]> {
  return request<CustomerOrder[]>("/orders");
}

export interface ClaimCheck {
  post_id: string;
  version: number;
  claims: PostClaim[];
  summary: { supported: number; contradicted: number; unverified: number };
  overall: "pass" | "fail" | "needs_owner";
}

export class RuntimeApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
    this.name = "RuntimeApiError";
  }
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL;
const DEMO_ACCOUNT = process.env.NEXT_PUBLIC_DEMO_ACCOUNT
  || (process.env.NODE_ENV === "development" ? "demo-owner" : undefined);
const LOCAL_ACCOUNT_SESSION_KEY = "bizsaathi_local_account_session";

function apiUrl(path: string): string {
  if (!API_BASE) throw new RuntimeApiError("NEXT_PUBLIC_API_URL is not configured.", 0);
  return getBrowserApiUrl(path);
}

export function setLocalAccountSessionRequired(required: boolean): void {
  if (typeof window === "undefined") return;
  if (required) {
    window.localStorage.setItem(LOCAL_ACCOUNT_SESSION_KEY, "true");
  } else {
    window.localStorage.removeItem(LOCAL_ACCOUNT_SESSION_KEY);
  }
}

export function getRuntimeAuthHeaders(): Record<string, string> {
  const localAccountSessionRequired =
    typeof window !== "undefined" &&
    window.localStorage.getItem(LOCAL_ACCOUNT_SESSION_KEY) === "true";
  return {
    ...(DEMO_ACCOUNT && !localAccountSessionRequired ? { "X-Demo-Account": DEMO_ACCOUNT } : {}),
    ...(localAccountSessionRequired ? { "X-Local-Account-Required": "true" } : {}),
  };
}

export function redirectToLocalSignInIfNeeded(status: number): boolean {
  if (
    status !== 401 ||
    typeof window === "undefined" ||
    window.localStorage.getItem(LOCAL_ACCOUNT_SESSION_KEY) !== "true" ||
    window.location.pathname === "/login"
  ) {
    return false;
  }
  window.location.replace("/login?reason=session");
  return true;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(apiUrl(path), {
    ...init,
    credentials: "include",
    cache: "no-store",
    headers: {
      Accept: "application/json",
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...getRuntimeAuthHeaders(),
      ...init?.headers,
    },
  });

  if (!response.ok) {
    if (redirectToLocalSignInIfNeeded(response.status)) {
      throw new RuntimeApiError("Sign in to your local account to continue.", response.status);
    }
    let message = `Request failed (${response.status}).`;
    try {
      const problem: unknown = await response.json();
      if (
        typeof problem === "object" &&
        problem !== null &&
        "detail" in problem &&
        typeof problem.detail === "string"
      ) {
        message = problem.detail;
      }
    } catch {
      message = `Request failed (${response.status}).`;
    }
    throw new RuntimeApiError(message, response.status);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export interface LocalAccountRegistration {
  user: { id: string; display_name: string; role: "owner" };
  business: { id: string; name: string; slug: string };
}

export function registerLocalAccount(input: {
  owner_name: string;
  business_name: string;
  email: string;
  password: string;
}): Promise<LocalAccountRegistration> {
  return request<LocalAccountRegistration>("/auth/local/register", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function loginLocalAccount(input: {
  email: string;
  password: string;
}): Promise<LocalAccountRegistration> {
  return request<LocalAccountRegistration>("/auth/local/login", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function clearLocalSession(): Promise<void> {
  return request<void>("/auth/logout", { method: "POST" });
}

export function getDashboardSummary(): Promise<DashboardSummary> {
  return request<DashboardSummary>("/dashboard");
}

export function listCatalogProducts(statusFilter: "active" | "archived" | "all" = "active"): Promise<CatalogProduct[]> {
  return request<CatalogProduct[]>(`/products?status_filter=${statusFilter}`);
}

export function listDraftPosts(): Promise<DraftPost[]> {
  return request<DraftPost[]>("/posts");
}

export function createCatalogProduct(input: {
  sku?: string;
  name: string;
  description?: string;
  price_inr: string;
  stock: number;
}): Promise<CatalogProduct> {
  return request<CatalogProduct>("/products", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function generateDraftPost(
  productId: string,
  channel: DraftPost["channel"],
  language: DraftPost["language"],
): Promise<DraftPost> {
  return request<DraftPost>(`/posts/generate/${encodeURIComponent(productId)}`, {
    method: "POST",
    body: JSON.stringify({ channel, language }),
  });
}

export function generateQuickDraftPost(
  productId: string,
  channel: DraftPost["channel"],
  language: DraftPost["language"],
): Promise<DraftPost> {
  return request<DraftPost>(`/posts/generate/${encodeURIComponent(productId)}/quick`, {
    method: "POST",
    body: JSON.stringify({ channel, language }),
  });
}

export async function generateDraftPostStream(
  productId: string,
  channel: DraftPost["channel"],
  language: DraftPost["language"],
  onToken: (lineIndex: number, text: string) => void,
  onStatus: (message: string) => void,
): Promise<DraftPost> {
  const response = await fetch(apiUrl(`/posts/generate/${encodeURIComponent(productId)}/stream`), {
    method: "POST",
    credentials: "include",
    cache: "no-store",
    headers: {
      Accept: "text/event-stream",
      "Content-Type": "application/json",
      ...getRuntimeAuthHeaders(),
    },
    body: JSON.stringify({ channel, language }),
  });

  if (!response.ok) {
    if (redirectToLocalSignInIfNeeded(response.status)) {
      throw new RuntimeApiError("Sign in to your local account to continue.", response.status);
    }
    let message = `Request failed (${response.status}).`;
    try {
      const problem: unknown = await response.json();
      if (typeof problem === "object" && problem !== null && "detail" in problem) {
        const detail = problem.detail;
        if (typeof detail === "string") message = detail;
        else if (typeof detail === "object" && detail !== null && "detail" in detail
          && typeof detail.detail === "string") message = detail.detail;
      }
    } catch {
      message = `Request failed (${response.status}).`;
    }
    throw new RuntimeApiError(message, response.status);
  }
  if (!response.body) {
    throw new RuntimeApiError("The post-generation stream is unavailable.", response.status);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let completedPost: DraftPost | null = null;

  function processFrame(frame: string): void {
    let eventName = "message";
    const data: string[] = [];
    for (const line of frame.split(/\r?\n/)) {
      if (line.startsWith("event:")) eventName = line.slice(6).trim();
      else if (line.startsWith("data:")) data.push(line.slice(5).trimStart());
    }
    if (data.length === 0) return;

    const payload: unknown = JSON.parse(data.join("\n"));
    if (typeof payload !== "object" || payload === null) {
      throw new RuntimeApiError("The post-generation stream returned invalid data.", response.status);
    }
    if (
      eventName === "status"
      && "message" in payload
      && typeof payload.message === "string"
    ) {
      onStatus(payload.message);
    } else if (
      eventName === "token"
      && "line_index" in payload
      && typeof payload.line_index === "number"
      && "text" in payload
      && typeof payload.text === "string"
    ) {
      onToken(payload.line_index, payload.text);
    } else if (eventName === "complete" && "post" in payload) {
      const post = payload.post;
      if (
        typeof post !== "object"
        || post === null
        || !("id" in post)
        || typeof post.id !== "string"
        || !("product_id" in post)
        || typeof post.product_id !== "string"
        || !("text" in post)
        || typeof post.text !== "string"
        || !("provenance" in post)
        || typeof post.provenance !== "object"
        || post.provenance === null
      ) {
        throw new RuntimeApiError("The post-generation stream returned an invalid draft.", response.status);
      }
      completedPost = post as DraftPost;
    } else if (
      eventName === "error"
      && "detail" in payload
      && typeof payload.detail === "string"
    ) {
      const status = "status" in payload && typeof payload.status === "number"
        ? payload.status
        : response.status;
      throw new RuntimeApiError(payload.detail, status);
    }
  }

  try {
    while (true) {
      const { done, value } = await reader.read();
      buffer += decoder.decode(value, { stream: !done });
      const frames = buffer.split(/\r?\n\r?\n/);
      buffer = frames.pop() ?? "";
      for (const frame of frames) processFrame(frame);
      if (done) break;
    }
    if (buffer.trim()) processFrame(buffer);
  } finally {
    reader.releaseLock();
  }

  if (!completedPost) {
    throw new RuntimeApiError("The post-generation stream ended before a draft was saved.", response.status);
  }
  return completedPost;
}

export function updateDraftPost(post: DraftPost, text: string): Promise<DraftPost> {
  return request<DraftPost>(`/posts/${encodeURIComponent(post.id)}`, {
    method: "PATCH",
    headers: { "If-Match": String(post.version) },
    body: JSON.stringify({ text }),
  });
}

export function checkDraftClaims(post: DraftPost): Promise<ClaimCheck> {
  return request<ClaimCheck>(`/posts/${encodeURIComponent(post.id)}/claim-check`, {
    method: "POST",
    body: JSON.stringify({ version: post.version }),
  });
}


export function updateCatalogProduct(
  product: CatalogProduct,
  input: { name?: string; description?: string | null; price_inr?: string; }
): Promise<CatalogProduct> {
  return request<CatalogProduct>(`/products/${encodeURIComponent(product.id)}`, {
    method: "PATCH",
    headers: { "If-Match": String(product.version) },
    body: JSON.stringify(input),
  });
}

export async function archiveCatalogProduct(productId: string): Promise<void> {
  await request<{ id: string; status: string }>(`/products/${encodeURIComponent(productId)}/archive`, {
    method: "POST",
  });
}

export function adjustCatalogStock(
  product: CatalogProduct,
  delta: number,
): Promise<{ product_id: string; stock: number; stock_version: number }> {
  return request(`/products/${encodeURIComponent(product.id)}/stock`, {
    method: "POST",
    body: JSON.stringify({ delta, expected_stock_version: product.stock_version }),
  });
}

export interface UploadTicket {
  media_id: string;
  upload_url: string;
  storage_key: string;
  expires_in_seconds: number;
  method: "PUT";
}

export async function uploadProductImage(productId: string, file: File): Promise<void> {
  const ticket = await request<UploadTicket>("/uploads", {
    method: "POST",
    body: JSON.stringify({
      kind: "photo",
      filename: file.name,
      mime: file.type,
      size_bytes: file.size,
      product_id: productId,
    }),
  });
  const response = await fetch(ticket.upload_url, {
    method: ticket.method,
    headers: { "Content-Type": file.type },
    body: file,
    cache: "no-store",
  });
  if (!response.ok) {
    if (redirectToLocalSignInIfNeeded(response.status)) {
      throw new RuntimeApiError("Sign in to your local account to continue.", response.status);
    }
    throw new RuntimeApiError(`Image upload failed (${response.status}).`, response.status);
  }
}

export function productImageUrl(productId: string): string {
  return apiUrl(`/uploads/products/${encodeURIComponent(productId)}/image`);
}

export async function fetchProductImageForShare(productId: string): Promise<File> {
  const response = await fetch(productImageUrl(productId), {
    credentials: "include",
    cache: "no-store",
    headers: {
      Accept: "image/jpeg, image/png, image/webp",
      ...getRuntimeAuthHeaders(),
    },
  });
  if (!response.ok) {
    if (redirectToLocalSignInIfNeeded(response.status)) {
      throw new RuntimeApiError("Sign in to your local account to continue.", response.status);
    }
    throw new RuntimeApiError(
      response.status === 404
        ? "No verified uploaded image is available for this product. Add and verify a product image before sharing."
        : `Could not load the product image (${response.status}).`,
      response.status,
    );
  }

  const mimeType = response.headers.get("content-type")?.split(";", 1)[0].trim().toLowerCase();
  const extensionByMime: Record<string, string> = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
  };
  const extension = mimeType ? extensionByMime[mimeType] : undefined;
  if (!mimeType || !extension) {
    throw new RuntimeApiError("The uploaded product image has an unsupported file type.", 0);
  }
  return new File([await response.blob()], `product-image.${extension}`, { type: mimeType });
}

export interface ApprovalRecord {
  id: string;
  business_id: string;
  proposal_id: string;
  type: string;
  status: string;
  warnings: unknown[];
  risk: string;
  side_effect: Record<string, unknown>;
  proposal_version: number;
  diff: Record<string, unknown>;
  expires_at: string;
  created_at: string;
}

export function listPendingApprovals(): Promise<ApprovalRecord[]> {
  return request<ApprovalRecord[]>("/approvals?status_filter=pending");
}

export function decideApproval(
  approval: ApprovalRecord,
  decision: "approve" | "reject",
): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>(`/approvals/${encodeURIComponent(approval.id)}/${decision}`, {
    method: "POST",
    headers: decision === "approve"
      ? { "Idempotency-Key": `${approval.id}:${approval.proposal_version}:approve` }
      : undefined,
    body: JSON.stringify({ expected_proposal_version: approval.proposal_version }),
  });
}

export interface ExtractedProductInfo {
  name?: string;
  description?: string;
  color?: string;
  category?: string;
  material?: string;
  proposal_id?: string;
  uncertainties?: Array<{
    field: string;
    confidence: number;
    ask_seller: boolean;
    reason: string;
  }>;
}

export async function extractProductDetailsFromPhoto(file: File): Promise<ExtractedProductInfo> {
  const ticket = await request<UploadTicket>("/uploads", {
    method: "POST",
    body: JSON.stringify({
      kind: "photo",
      filename: file.name,
      mime: file.type || "image/jpeg",
      size_bytes: file.size,
    }),
  });

  const uploadRes = await fetch(ticket.upload_url, {
    method: ticket.method,
    headers: { "Content-Type": file.type || "image/jpeg" },
    body: file,
    cache: "no-store",
  });
  if (!uploadRes.ok) {
    throw new RuntimeApiError(`Photo upload failed (${uploadRes.status}).`, uploadRes.status);
  }

  const jobInit = await request<{ job_id: string; status: string; poll_url: string }>("/products/from-photo", {
    method: "POST",
    body: JSON.stringify({
      media_ids: [ticket.media_id],
    }),
  });

  const maxAttempts = 180;
  for (let i = 0; i < maxAttempts; i++) {
    await new Promise((resolve) => setTimeout(resolve, 1500));
    const job = await request<{
      id: string;
      status: string;
      result_ref?: {
        id?: string;
        fields?: Record<string, string>;
        uncertainties?: Array<{ field: string; confidence: number; ask_seller: boolean; reason: string }>;
      };
      error_message?: string;
    }>(`/jobs/${jobInit.job_id}`);

    if (job.status === "succeeded" || job.status === "awaiting_approval") {
      const fields = job.result_ref?.fields || {};
      return {
        name: fields.name,
        description: fields.description,
        color: fields.color,
        category: fields.category,
        material: fields.material,
        proposal_id: job.result_ref?.id,
        uncertainties: job.result_ref?.uncertainties,
      };
    }
    if (job.status === "failed" || job.status === "blocked") {
      throw new RuntimeApiError(job.error_message || "Product extraction failed.", 500);
    }
  }

  throw new RuntimeApiError("Product extraction timed out. Please enter details manually.", 504);
}
