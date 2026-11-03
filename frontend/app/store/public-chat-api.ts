import { getBrowserApiUrl } from "../lib/api-url";

export interface PublicStore {
  business: { name: string; slug: string; description: string | null };
  products: Array<{
    id: string;
    name: string;
    price_inr: string;
    in_stock: boolean;
    image_url: string | null;
  }>;
}

export interface PublicChatSession {
  session_id: string;
  expires_at: string;
  disclosure: string;
  messages: Array<{
    id: string;
    sender: "customer" | "assistant" | "owner";
    text: string;
    evidence_ids: string[];
  }>;
}

export interface PublicSessionUpdate {
  message_id: string;
  sender: "assistant" | "owner";
  text: string;
  evidence_ids: string[];
  created_at: string;
}

export interface PublicCustomerAccount {
  id: string;
  email: string;
  display_name: string;
}

export interface PublicChatReply {
  message_id: string;
  assistant_message: {
    id: string;
    text: string;
    evidence_ids: string[];
    created_at: string;
  };
  escalated: boolean;
}

export class PublicChatApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
    this.name = "PublicChatApiError";
  }
}

async function publicRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const method = init?.method?.toUpperCase() ?? "GET";
  const response = await fetch(getBrowserApiUrl(path), {
    ...init,
    credentials: "include",
    cache: "no-store",
    headers: {
      Accept: "application/json",
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...(method !== "GET" && method !== "HEAD" ? { "X-Customer-Request": "1" } : {}),
      ...init?.headers,
    },
  });
  if (!response.ok) {
    let message = `The customer chat request failed (${response.status}).`;
    try {
      const problem: unknown = await response.json();
      if (typeof problem === "object" && problem !== null && "detail" in problem) {
        const detail = problem.detail;
        if (typeof detail === "string") message = detail;
        else if (typeof detail === "object" && detail !== null && "detail" in detail
          && typeof detail.detail === "string") message = detail.detail;
      }
    } catch {
      message = `The customer chat request failed (${response.status}).`;
    }
    throw new PublicChatApiError(message, response.status);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export function getPublicStore(slug: string): Promise<PublicStore> {
  return publicRequest(`/public/stores/${encodeURIComponent(slug)}`);
}

export function createPublicChatSession(slug: string): Promise<PublicChatSession> {
  return publicRequest(`/public/stores/${encodeURIComponent(slug)}/sessions`, { method: "POST" });
}

export function subscribeToPublicChatSession(
  sessionId: string,
  onReply: (reply: PublicSessionUpdate) => void,
  onError: (error: Error) => void,
): () => void {
  const source = new EventSource(
    getBrowserApiUrl(`/public/sessions/${encodeURIComponent(sessionId)}/stream`),
    { withCredentials: true },
  );
  const handleReply = (event: Event) => {
    try {
      const payload: unknown = JSON.parse((event as MessageEvent<string>).data);
      if (
        typeof payload !== "object"
        || payload === null
        || !("message_id" in payload)
        || typeof payload.message_id !== "string"
        || !("sender" in payload)
        || (payload.sender !== "assistant" && payload.sender !== "owner")
        || !("text" in payload)
        || typeof payload.text !== "string"
        || !("evidence_ids" in payload)
        || !Array.isArray(payload.evidence_ids)
        || !payload.evidence_ids.every((id: unknown) => typeof id === "string")
        || !("created_at" in payload)
        || typeof payload.created_at !== "string"
      ) {
        throw new Error("The customer chat received an invalid reply event.");
      }
      onReply(payload as PublicSessionUpdate);
    } catch (cause) {
      onError(cause instanceof Error ? cause : new Error("Could not read the latest chat reply."));
    }
  };
  source.addEventListener("reply", handleReply);
  source.onerror = () => {
    if (source.readyState === EventSource.CLOSED) {
      onError(new Error("The customer chat connection closed. Refresh the page to reconnect."));
    }
  };
  return () => source.close();
}

export function sendPublicChatMessage(
  sessionId: string,
  text: string,
): Promise<PublicChatReply> {
  return publicRequest<PublicChatReply>(`/public/sessions/${encodeURIComponent(sessionId)}/messages`, {
    method: "POST",
    body: JSON.stringify({ text }),
  }).then((reply) => {
    if (!reply.assistant_message?.text.trim()) {
      throw new Error("The shop chat returned no reply. Refresh the page and try again.");
    }
    return reply;
  });
}

export function getCurrentCustomerAccount(): Promise<PublicCustomerAccount | null> {
  return publicRequest<PublicCustomerAccount>("/public/customer-accounts/me")
    .catch((cause: unknown) => {
      if (cause instanceof PublicChatApiError && cause.status === 401) return null;
      throw cause;
    });
}

export function registerCustomerAccount(input: {
  email: string;
  display_name: string;
  password: string;
}): Promise<PublicCustomerAccount> {
  return publicRequest("/public/customer-accounts/register", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function loginCustomerAccount(input: {
  email: string;
  password: string;
}): Promise<PublicCustomerAccount> {
  return publicRequest("/public/customer-accounts/login", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function logoutCustomerAccount(): Promise<void> {
  return publicRequest<void>("/public/customer-accounts/logout", { method: "POST" });
}
