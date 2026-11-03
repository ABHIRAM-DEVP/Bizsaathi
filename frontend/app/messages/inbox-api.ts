import { getBrowserApiUrl } from "../lib/api-url";
import { getRuntimeAuthHeaders, redirectToLocalSignInIfNeeded } from "@/lib/api-client/runtime";

export type InboxStatus = "open" | "escalated" | "closed";
export type InboxSource = "public" | "demo";
export type InboxSender = "customer" | "agent" | "owner" | "system";

export interface InboxMessage {
  id: string;
  conversation_id: string;
  sender: InboxSender;
  text: string;
  evidence_ids: string[];
  created_at: string;
  delivery_status?: "delivered" | "not_sent";
}

export interface InboxConversation {
  id: string;
  business_id: string;
  status: InboxStatus;
  source: InboxSource;
  customer_name: string;
  escalation_reason: string | null;
  last_message: string | null;
  unread_count: number;
  created_at: string;
  updated_at: string;
  messages: InboxMessage[];
}

interface ConversationListResponse {
  items: InboxConversation[];
  next_cursor: string | null;
}

interface DemoStartResponse {
  conversations: InboxConversation[];
  label: "synthetic_demo";
}

interface DemoMessageResponse {
  conversation: InboxConversation;
  automated_reply: boolean;
  escalation: boolean;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(getBrowserApiUrl(path), {
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
      throw new Error("Sign in to your local account to continue.");
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
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export function listInbox(
  status?: InboxStatus,
  cursor?: string | null,
): Promise<ConversationListResponse> {
  const query = new URLSearchParams({ limit: "50" });
  if (status) query.set("status", status);
  if (cursor) query.set("cursor", cursor);
  return request(`/conversations?${query.toString()}`);
}

export function getInboxConversation(id: string): Promise<InboxConversation> {
  return request(`/conversations/${encodeURIComponent(id)}`);
}

export function startDemoInbox(): Promise<DemoStartResponse> {
  return request("/conversations/demo/start", { method: "POST" });
}

export function sendDemoMessage(id: string, text: string): Promise<DemoMessageResponse> {
  return request(`/conversations/${encodeURIComponent(id)}/demo-messages`, {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}

export function simulateNextDemoMessage(): Promise<DemoMessageResponse> {
  return request("/conversations/demo/simulate", { method: "POST" });
}

export function sendOwnerReply(id: string, text: string): Promise<InboxMessage> {
  return request(`/conversations/${encodeURIComponent(id)}/reply`, {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}
