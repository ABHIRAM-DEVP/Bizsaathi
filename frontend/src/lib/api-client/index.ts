/**
 * BizSaathi API Client
 * Derived from contracts/openapi.json
 */

export interface HealthResponse {
  status: string;
}

export interface ReadinessResponse {
  status: string;
  checks: {
    db: string;
    redis?: string | null;
  };
}

export interface ProblemDetails {
  type: string;
  title: string;
  status: number;
  detail: string;
  request_id: string;
  errors?: Array<{ field: string; message: string }>;
}

export interface UploadRequest {
  kind: "photo" | "audio";
  filename: string;
  mime: string;
  size_bytes: number;
}

export interface UploadResponse {
  media_id: string;
  upload_url: string;
  storage_key: string;
  expires_in_seconds: number;
  method: string;
}

export interface JobResponse {
  id: string;
  business_id: string;
  kind: string;
  status: string;
  progress_step: number;
  progress_total: number;
  result_ref?: Record<string, unknown> | null;
  error_code?: string | null;
  error_message?: string | null;
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL;

function apiUrl(path: string): string {
  if (!API_BASE) throw new Error("NEXT_PUBLIC_API_URL is not configured.");
  return `${API_BASE}/v1${path}`;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public problem: ProblemDetails | string
  ) {
    super(typeof problem === "string" ? problem : problem.detail);
    this.name = "ApiError";
  }
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(apiUrl("/health"), {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  if (!res.ok) {
    throw new ApiError(res.status, `Health check failed with status ${res.status}`);
  }
  return res.json();
}

export async function fetchReadiness(): Promise<ReadinessResponse> {
  const res = await fetch(apiUrl("/health/ready"), {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  if (!res.ok) {
    throw new ApiError(res.status, `Readiness check failed with status ${res.status}`);
  }
  return res.json();
}

export async function requestUpload(
  req: UploadRequest,
  token?: string
): Promise<UploadResponse> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const res = await fetch(apiUrl("/uploads"), {
    method: "POST",
    headers,
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    let errBody: ProblemDetails | string;
    try {
      errBody = await res.json();
    } catch {
      errBody = await res.text();
    }
    throw new ApiError(res.status, errBody);
  }
  return res.json();
}

export async function getJob(
  jobId: string,
  token?: string
): Promise<JobResponse> {
  const headers: Record<string, string> = {
    Accept: "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const res = await fetch(apiUrl(`/jobs/${jobId}`), {
    method: "GET",
    headers,
  });
  if (!res.ok) {
    let errBody: ProblemDetails | string;
    try {
      errBody = await res.json();
    } catch {
      errBody = await res.text();
    }
    throw new ApiError(res.status, errBody);
  }
  return res.json();
}

// ============================================================================
// Extended Types (matching backend schemas)
// ============================================================================

export interface Product {
  id: string;
  business_id: string;
  sku: string | null;
  name: string;
  description: string | null;
  price_inr: number;
  status: "active" | "draft" | "archived";
  created_at: string;
  updated_at: string;
  variants: ProductVariant[];
  media: MediaItem[];
}

export interface ProductVariant {
  id: string;
  product_id: string;
  color: string | null;
  size: string | null;
  stock: number;
  stock_version: number;
}

export interface MediaItem {
  id: string;
  kind: "photo" | "audio";
  url: string;
  filename: string;
}

export interface ProductListItem {
  id: string;
  sku: string | null;
  name: string;
  price_inr: number;
  status: string;
  stock_total: number;
  thumbnail_url: string | null;
}

export interface ProductListResponse {
  items: ProductListItem[];
  next_cursor: string | null;
}

export interface CreateProductRequest {
  sku?: string;
  name: string;
  description?: string;
  price_inr: number;
  variants: Array<{
    color?: string;
    size?: string;
    stock: number;
  }>;
  media_ids: string[];
}

export interface ProductFromPhotoRequest {
  upload_ids: string[];
  seller_note?: string;
  language?: string;
}

export interface UpdateProductRequest {
  name?: string;
  description?: string;
  price_inr?: number;
  status?: "active" | "draft" | "archived";
}

export interface StockAdjustmentRequest {
  variant_id: string;
  delta?: number;
  set_to?: number;
  reason: string;
  expected_stock_version: number;
}

export interface Post {
  id: string;
  product_id: string;
  channel: "instagram" | "whatsapp_status" | "facebook" | "generic";
  language: string;
  text: string;
  version: number;
  status: "draft" | "checked" | "pending_approval" | "approved" | "exported";
  claims: Claim[];
  created_at: string;
  updated_at: string;
}

export interface Claim {
  id: string;
  text: string;
  verdict?: "supported" | "contradicted" | "unverified";
  severity?: string;
  evidence: Evidence[];
}

export interface Evidence {
  id: string;
  source_kind: string;
  source_id: string;
  source_version: number;
}

export interface GeneratePostRequest {
  channel: "instagram" | "whatsapp_status" | "facebook" | "generic";
  language: string;
  tone?: string;
  objective?: string;
}

export interface Approval {
  id: string;
  type: "product_create" | "product_update" | "post_publish" | "order_action" | "reply";
  status: "pending" | "approved" | "rejected" | "expired" | "invalidated";
  proposal: {
    id: string;
    version: number;
    payload: Record<string, unknown>;
    diff?: {
      before: Record<string, unknown>;
      after: Record<string, unknown>;
    };
  };
  evidence: Evidence[];
  warnings: string[];
  risk: string;
  side_effect?: {
    description: string;
    reversible: boolean;
  };
  expires_at: string;
  created_at: string;
}

export interface ApprovalListResponse {
  items: Approval[];
  next_cursor: string | null;
}

export interface Order {
  id: string;
  business_id: string;
  status: "DRAFT" | "AWAITING_PAYMENT" | "PAID" | "FULFILLED" | "CANCELLED" | "FAILED";
  items: OrderItem[];
  total_inr: number;
  customer_name?: string;
  delivery_note?: string;
  created_at: string;
  updated_at: string;
}

export interface OrderItem {
  variant_id: string;
  product_name: string;
  qty: number;
  unit_price_inr: number;
}

export interface OrderListResponse {
  items: Order[];
  next_cursor: string | null;
}

export interface Message {
  id: string;
  conversation_id: string;
  sender: "customer" | "agent" | "owner";
  text: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  business_id: string;
  status: "open" | "escalated" | "closed";
  customer_name?: string;
  messages: Message[];
  created_at: string;
  updated_at: string;
}

export interface ConversationListResponse {
  items: Conversation[];
  next_cursor: string | null;
}

export interface DashboardStats {
  pending_approvals: number;
  open_escalations: number;
  recent_jobs: JobResponse[];
  low_stock: ProductListItem[];
  next_step?: {
    label: string;
    route: string;
  };
}

// ============================================================================
// Products API
// ============================================================================

export async function listProducts(params?: {
  status?: string;
  q?: string;
  sku?: string;
  low_stock?: boolean;
  limit?: number;
  cursor?: string;
}): Promise<ProductListResponse> {
  const query = new URLSearchParams();
  if (params?.status) query.set("status", params.status);
  if (params?.q) query.set("q", params.q);
  if (params?.sku) query.set("sku", params.sku);
  if (params?.low_stock) query.set("low_stock", "true");
  if (params?.limit) query.set("limit", params.limit.toString());
  if (params?.cursor) query.set("cursor", params.cursor);

  const res = await fetch(`${API_BASE}/v1/products?${query}`, {
    credentials: "include",
    headers: { Accept: "application/json" },
  });

  if (!res.ok) {
    let errBody: ProblemDetails | string;
    try {
      errBody = await res.json();
    } catch {
      errBody = await res.text();
    }
    throw new ApiError(res.status, errBody);
  }
  return res.json();
}

export async function getProduct(productId: string): Promise<Product> {
  const res = await fetch(`${API_BASE}/v1/products/${productId}`, {
    credentials: "include",
    headers: { Accept: "application/json" },
  });

  if (!res.ok) {
    let errBody: ProblemDetails | string;
    try {
      errBody = await res.json();
    } catch {
      errBody = await res.text();
    }
    throw new ApiError(res.status, errBody);
  }
  return res.json();
}

export async function createProduct(req: CreateProductRequest): Promise<Product> {
  const res = await fetch(`${API_BASE}/v1/products`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(req),
  });

  if (!res.ok) {
    let errBody: ProblemDetails | string;
    try {
      errBody = await res.json();
    } catch {
      errBody = await res.text();
    }
    throw new ApiError(res.status, errBody);
  }
  return res.json();
}

export async function createProductFromPhoto(req: ProductFromPhotoRequest): Promise<JobResponse> {
  const res = await fetch(`${API_BASE}/v1/products/from-photo`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(req),
  });

  if (!res.ok) {
    let errBody: ProblemDetails | string;
    try {
      errBody = await res.json();
    } catch {
      errBody = await res.text();
    }
    throw new ApiError(res.status, errBody);
  }
  return res.json();
}

export async function updateProduct(
  productId: string,
  req: UpdateProductRequest
): Promise<Product> {
  const res = await fetch(`${API_BASE}/v1/products/${productId}`, {
    method: "PATCH",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(req),
  });

  if (!res.ok) {
    let errBody: ProblemDetails | string;
    try {
      errBody = await res.json();
    } catch {
      errBody = await res.text();
    }
    throw new ApiError(res.status, errBody);
  }
  return res.json();
}

export async function archiveProduct(productId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/v1/products/${productId}`, {
    method: "DELETE",
    credentials: "include",
  });

  if (!res.ok) {
    let errBody: ProblemDetails | string;
    try {
      errBody = await res.json();
    } catch {
      errBody = await res.text();
    }
    throw new ApiError(res.status, errBody);
  }
}

export async function adjustStock(
  productId: string,
  req: StockAdjustmentRequest
): Promise<{ variant_id: string; stock: number; stock_version: number }> {
  const res = await fetch(`${API_BASE}/v1/products/${productId}/stock`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(req),
  });

  if (!res.ok) {
    let errBody: ProblemDetails | string;
    try {
      errBody = await res.json();
    } catch {
      errBody = await res.text();
    }
    throw new ApiError(res.status, errBody);
  }
  return res.json();
}

// ============================================================================
// Posts API
// ============================================================================

export async function listPosts(params?: {
  product_id?: string;
  status?: string;
  limit?: number;
  cursor?: string;
}): Promise<{ items: Post[]; next_cursor: string | null }> {
  const query = new URLSearchParams();
  if (params?.product_id) query.set("product_id", params.product_id);
  if (params?.status) query.set("status", params.status);
  if (params?.limit) query.set("limit", params.limit.toString());
  if (params?.cursor) query.set("cursor", params.cursor);

  const res = await fetch(`${API_BASE}/v1/posts?${query}`, {
    credentials: "include",
    headers: { Accept: "application/json" },
  });

  if (!res.ok) {
    let errBody: ProblemDetails | string;
    try {
      errBody = await res.json();
    } catch {
      errBody = await res.text();
    }
    throw new ApiError(res.status, errBody);
  }
  return res.json();
}

export async function getPost(postId: string): Promise<Post> {
  const res = await fetch(`${API_BASE}/v1/posts/${postId}`, {
    credentials: "include",
    headers: { Accept: "application/json" },
  });

  if (!res.ok) {
    let errBody: ProblemDetails | string;
    try {
      errBody = await res.json();
    } catch {
      errBody = await res.text();
    }
    throw new ApiError(res.status, errBody);
  }
  return res.json();
}

export async function generatePost(
  productId: string,
  req: GeneratePostRequest
): Promise<JobResponse> {
  const res = await fetch(`${API_BASE}/v1/products/${productId}/posts/generate`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(req),
  });

  if (!res.ok) {
    let errBody: ProblemDetails | string;
    try {
      errBody = await res.json();
    } catch {
      errBody = await res.text();
    }
    throw new ApiError(res.status, errBody);
  }
  return res.json();
}

export async function updatePost(
  postId: string,
  req: { text: string }
): Promise<Post> {
  const res = await fetch(`${API_BASE}/v1/posts/${postId}`, {
    method: "PATCH",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(req),
  });

  if (!res.ok) {
    let errBody: ProblemDetails | string;
    try {
      errBody = await res.json();
    } catch {
      errBody = await res.text();
    }
    throw new ApiError(res.status, errBody);
  }
  return res.json();
}

export async function checkClaims(
  postId: string,
  version: number
): Promise<{
  post_id: string;
  version: number;
  claims: Claim[];
  summary: { supported: number; contradicted: number; unverified: number };
  overall: "pass" | "fail" | "needs_owner";
}> {
  const res = await fetch(`${API_BASE}/v1/posts/${postId}/claim-check`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({ version }),
  });

  if (!res.ok) {
    let errBody: ProblemDetails | string;
    try {
      errBody = await res.json();
    } catch {
      errBody = await res.text();
    }
    throw new ApiError(res.status, errBody);
  }
  return res.json();
}

export async function submitPost(
  postId: string,
  version: number
): Promise<{ approval_id: string }> {
  const res = await fetch(`${API_BASE}/v1/posts/${postId}/submit`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({ version }),
  });

  if (!res.ok) {
    let errBody: ProblemDetails | string;
    try {
      errBody = await res.json();
    } catch {
      errBody = await res.text();
    }
    throw new ApiError(res.status, errBody);
  }
  return res.json();
}

// ============================================================================
// Approvals API
// ============================================================================

export async function listApprovals(params?: {
  type?: string;
  status?: string;
  limit?: number;
  cursor?: string;
}): Promise<ApprovalListResponse> {
  const query = new URLSearchParams();
  if (params?.type) query.set("type", params.type);
  if (params?.status) query.set("status", params.status);
  if (params?.limit) query.set("limit", params.limit.toString());
  if (params?.cursor) query.set("cursor", params.cursor);

  const res = await fetch(`${API_BASE}/v1/approvals?${query}`, {
    credentials: "include",
    headers: { Accept: "application/json" },
  });

  if (!res.ok) {
    let errBody: ProblemDetails | string;
    try {
      errBody = await res.json();
    } catch {
      errBody = await res.text();
    }
    throw new ApiError(res.status, errBody);
  }
  return res.json();
}

export async function getApproval(approvalId: string): Promise<Approval> {
  const res = await fetch(`${API_BASE}/v1/approvals/${approvalId}`, {
    credentials: "include",
    headers: { Accept: "application/json" },
  });

  if (!res.ok) {
    let errBody: ProblemDetails | string;
    try {
      errBody = await res.json();
    } catch {
      errBody = await res.text();
    }
    throw new ApiError(res.status, errBody);
  }
  return res.json();
}

export async function approveApproval(
  approvalId: string,
  proposalVersion: number
): Promise<{ execution_id: string; status: string; result_ref?: Record<string, unknown> }> {
  const res = await fetch(`${API_BASE}/v1/approvals/${approvalId}/approve`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({ proposal_version: proposalVersion }),
  });

  if (!res.ok) {
    let errBody: ProblemDetails | string;
    try {
      errBody = await res.json();
    } catch {
      errBody = await res.text();
    }
    throw new ApiError(res.status, errBody);
  }
  return res.json();
}

export async function rejectApproval(
  approvalId: string,
  reason?: string
): Promise<void> {
  const res = await fetch(`${API_BASE}/v1/approvals/${approvalId}/reject`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({ reason }),
  });

  if (!res.ok) {
    let errBody: ProblemDetails | string;
    try {
      errBody = await res.json();
    } catch {
      errBody = await res.text();
    }
    throw new ApiError(res.status, errBody);
  }
}

// ============================================================================
// Orders API (partial - EP-G endpoints)
// ============================================================================

export async function listOrders(params?: {
  status?: string;
  limit?: number;
  cursor?: string;
}): Promise<OrderListResponse> {
  const query = new URLSearchParams();
  if (params?.status) query.set("status", params.status);
  if (params?.limit) query.set("limit", params.limit.toString());
  if (params?.cursor) query.set("cursor", params.cursor);

  const res = await fetch(`${API_BASE}/v1/orders?${query}`, {
    credentials: "include",
    headers: { Accept: "application/json" },
  });

  if (!res.ok) {
    let errBody: ProblemDetails | string;
    try {
      errBody = await res.json();
    } catch {
      errBody = await res.text();
    }
    throw new ApiError(res.status, errBody);
  }
  return res.json();
}

export async function getOrder(orderId: string): Promise<Order> {
  const res = await fetch(`${API_BASE}/v1/orders/${orderId}`, {
    credentials: "include",
    headers: { Accept: "application/json" },
  });

  if (!res.ok) {
    let errBody: ProblemDetails | string;
    try {
      errBody = await res.json();
    } catch {
      errBody = await res.text();
    }
    throw new ApiError(res.status, errBody);
  }
  return res.json();
}

// ============================================================================
// Conversations API (partial - EP-F endpoints)
// ============================================================================

export async function listConversations(params?: {
  status?: string;
  limit?: number;
  cursor?: string;
}): Promise<ConversationListResponse> {
  const query = new URLSearchParams();
  if (params?.status) query.set("status", params.status);
  if (params?.limit) query.set("limit", params.limit.toString());
  if (params?.cursor) query.set("cursor", params.cursor);

  const res = await fetch(`${API_BASE}/v1/conversations?${query}`, {
    credentials: "include",
    headers: { Accept: "application/json" },
  });

  if (!res.ok) {
    let errBody: ProblemDetails | string;
    try {
      errBody = await res.json();
    } catch {
      errBody = await res.text();
    }
    throw new ApiError(res.status, errBody);
  }
  return res.json();
}

export async function getConversation(conversationId: string): Promise<Conversation> {
  const res = await fetch(`${API_BASE}/v1/conversations/${conversationId}`, {
    credentials: "include",
    headers: { Accept: "application/json" },
  });

  if (!res.ok) {
    let errBody: ProblemDetails | string;
    try {
      errBody = await res.json();
    } catch {
      errBody = await res.text();
    }
    throw new ApiError(res.status, errBody);
  }
  return res.json();
}

export async function replyToConversation(
  conversationId: string,
  text: string
): Promise<Message> {
  const res = await fetch(`${API_BASE}/v1/conversations/${conversationId}/reply`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({ text }),
  });

  if (!res.ok) {
    let errBody: ProblemDetails | string;
    try {
      errBody = await res.json();
    } catch {
      errBody = await res.text();
    }
    throw new ApiError(res.status, errBody);
  }
  return res.json();
}

// ============================================================================
// Dashboard API
// ============================================================================

export async function getDashboard(): Promise<DashboardStats> {
  const res = await fetch(`${API_BASE}/v1/dashboard`, {
    credentials: "include",
    headers: { Accept: "application/json" },
  });

  if (!res.ok) {
    let errBody: ProblemDetails | string;
    try {
      errBody = await res.json();
    } catch {
      errBody = await res.text();
    }
    throw new ApiError(res.status, errBody);
  }
  return res.json();
}
