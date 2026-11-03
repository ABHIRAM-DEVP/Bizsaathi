"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { SellerShell } from "../components/SellerShell";
import {
  getInboxConversation,
  listInbox,
  sendOwnerReply,
  sendDemoMessage,
  simulateNextDemoMessage,
  startDemoInbox,
} from "./inbox-api";
import type { InboxConversation, InboxMessage, InboxStatus } from "./inbox-api";

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

type Filter = "all" | "needs_you" | "open";

const isDevelopment = process.env.NODE_ENV === "development";

function messageLabel(message: InboxMessage, source: InboxConversation["source"]): string {
  if (message.sender === "owner") {
    return source === "public" ? "Your reply · customer chat" : "Demo reply";
  }
  if (message.sender === "agent") return "Catalog assistant";
  if (message.sender === "system") return "System";
  return "Synthetic customer";
}

export default function MessagesPage() {
  const [conversations, setConversations] = useState<InboxConversation[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState("");
  const [conversation, setConversation] = useState<InboxConversation | null>(null);
  const [filter, setFilter] = useState<Filter>("all");
  const [customerText, setCustomerText] = useState("");
  const [replyText, setReplyText] = useState("");
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [voiceStatus, setVoiceStatus] = useState("Voice input is optional.");
  const speechRef = useRef<SpeechRecognitionLike | null>(null);
  const simulationInFlightRef = useRef(false);
  const knownUnreadCountsRef = useRef(new Map<string, number>());

  const refreshList = useCallback(async (replace = false) => {
    const status: InboxStatus | undefined = filter === "all"
      ? undefined
      : filter === "needs_you" ? "escalated" : "open";
    const result = await listInbox(status);
    setNextCursor(result.next_cursor);
    if (replace) {
      knownUnreadCountsRef.current = new Map(
        result.items.map((item) => [item.id, item.unread_count]),
      );
    } else {
      const newMessage = result.items.find((item) => (
        item.unread_count > (knownUnreadCountsRef.current.get(item.id) ?? item.unread_count)
      ));
      if (newMessage) {
        setNotice(`New customer message from ${newMessage.customer_name}.`);
      }
      for (const item of result.items) {
        knownUnreadCountsRef.current.set(item.id, item.unread_count);
      }
    }
    setConversations((current) => {
      if (replace) return result.items;
      const merged = new Map(current.map((item) => [item.id, item]));
      for (const item of result.items) merged.set(item.id, item);
      return [...merged.values()].sort((left, right) => (
        Date.parse(right.updated_at) - Date.parse(left.updated_at)
        || right.id.localeCompare(left.id)
      ));
    });
    setSelectedId((current) => replace ? result.items[0]?.id ?? "" : current || result.items[0]?.id || "");
  }, [filter]);

  useEffect(() => {
    let active = true;
    async function initialize() {
      setLoading(true);
      setError(null);
      try {
        if (isDevelopment) await startDemoInbox();
        await refreshList(true);
      } catch (reason) {
        if (active) setError(reason instanceof Error ? reason.message : "Could not load messages.");
      } finally {
        if (active) setLoading(false);
      }
    }
    void initialize();
    return () => {
      active = false;
      speechRef.current?.stop();
    };
  }, [refreshList]);

  useEffect(() => {
    if (!selectedId) return;
    let active = true;
    getInboxConversation(selectedId)
      .then((result) => {
        if (active) setConversation(result);
      })
      .catch((reason: unknown) => {
        if (active) setError(reason instanceof Error ? reason.message : "Could not load this conversation.");
      });
    return () => {
      active = false;
    };
  }, [selectedId]);

  useEffect(() => {
    if (loading) return;
    const timer = window.setInterval(() => {
      void refreshList().catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : "Could not refresh the inbox.");
      });
      if (selectedId) {
        void getInboxConversation(selectedId)
          .then(setConversation)
          .catch((reason: unknown) => {
            setError(reason instanceof Error ? reason.message : "Could not refresh this conversation.");
          });
      }
    }, 5000);
    return () => window.clearInterval(timer);
  }, [loading, refreshList, selectedId]);

  useEffect(() => {
    if (loading || !isDevelopment) return;
    let active = true;
    const timer = window.setInterval(() => {
      if (!active || simulationInFlightRef.current) return;
      simulationInFlightRef.current = true;
      void simulateNextDemoMessage()
        .then(async (result) => {
          if (!active) return;
          if (result.conversation.id === selectedId) setConversation(result.conversation);
          setError(null);
          setNotice(`A synthetic message arrived from ${result.conversation.customer_name}.`);
          await refreshList();
        })
        .catch((reason: unknown) => {
          if (active) {
            setError(reason instanceof Error ? reason.message : "Could not simulate the next customer message.");
          }
        })
        .finally(() => {
          simulationInFlightRef.current = false;
        });
    }, 30_000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [loading, refreshList, selectedId]);

  async function submitCustomerMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedConversation || selectedConversation.source !== "demo" || !customerText.trim()) return;
    setSubmitting(true);
    setError(null);
    setNotice(null);
    try {
      const result = await sendDemoMessage(selectedConversation.id, customerText.trim());
      setConversation(result.conversation);
      setCustomerText("");
      setNotice(result.escalation
        ? "Escalated to the seller. No external message was sent."
        : "Catalog-grounded demo reply added to this synthetic thread.");
      await refreshList();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not simulate this customer message.");
    } finally {
      setSubmitting(false);
    }
  }

  async function sendReply(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedConversation || !replyText.trim()) return;
    setSubmitting(true);
    setError(null);
    setNotice(null);
    try {
      const message = await sendOwnerReply(selectedConversation.id, replyText.trim());
      setConversation((current) => current
        ? { ...current, messages: [...current.messages, message] }
        : current);
      setReplyText("");
      setNotice(message.delivery_status === "delivered"
        ? "Reply sent in the customer chat."
        : "Saved as a demo note; demo replies are not delivered to customers.");
      await refreshList();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not send this reply.");
    } finally {
      setSubmitting(false);
    }
  }

  async function loadMoreConversations() {
    if (!nextCursor || loadingMore) return;
    setLoadingMore(true);
    setError(null);
    const status: InboxStatus | undefined = filter === "all"
      ? undefined
      : filter === "needs_you" ? "escalated" : "open";
    try {
      const result = await listInbox(status, nextCursor);
      setConversations((current) => {
        const existing = new Set(current.map((item) => item.id));
        return [
          ...current,
          ...result.items.filter((item) => !existing.has(item.id)),
        ];
      });
      setNextCursor(result.next_cursor);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not load more conversations.");
    } finally {
      setLoadingMore(false);
    }
  }

  function startVoiceInput() {
    const speechWindow = window as SpeechWindow;
    const SpeechRecognition = speechWindow.SpeechRecognition ?? speechWindow.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setVoiceStatus("Speech recognition is not supported in this browser. You can type your reply.");
      return;
    }

    speechRef.current?.stop();
    const recognition = new SpeechRecognition();
    recognition.lang = "en-IN";
    recognition.interimResults = false;
    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((result) => result[0]?.transcript ?? "")
        .join(" ")
        .trim();
      if (transcript) {
        setReplyText((current) => [current.trim(), transcript].filter(Boolean).join(" "));
        setVoiceStatus("Voice transcription added to the draft. Review it before saving.");
      }
    };
    recognition.onerror = (event) => setVoiceStatus(`Voice input stopped: ${event.error}.`);
    recognition.onend = () => {
      speechRef.current = null;
    };
    speechRef.current = recognition;
    setVoiceStatus("Listening…");
    recognition.start();
  }

  const visibleConversations = conversations;
  const selectedConversation = conversation?.id === selectedId ? conversation : null;

  return (
    <SellerShell>
      <Link href="/" className="back-link">← Home</Link>
      <header className="page-heading">
        <div>
          <h1>Customer messages</h1>
          <p>Catalog-grounded replies, with sensitive requests brought to you.</p>
          {isDevelopment && <p>Local demo: a longer product-description inquiry arrives every 30 seconds from one of three synthetic customers.</p>}
        </div>
        {isDevelopment
          ? <span className="chip chip-warn">Synthetic demo · no external sending</span>
          : <span className="chip">Owner inbox</span>}
      </header>

      {error && <p className="form-error" role="alert">{error}</p>}
      {notice && <p className="form-success" role="status">{notice}</p>}

      <section className="inbox-layout" aria-label="Customer inbox">
        <div className="surface-card inbox-list">
          <div className="inbox-filter-row" aria-label="Conversation filters">
            {([
              ["all", "All"],
              ["needs_you", "Needs you"],
              ["open", "Open"],
            ] as const).map(([value, label]) => (
              <button
                key={value}
                type="button"
                className={`b${filter === value ? " s" : ""}`}
                aria-pressed={filter === value}
                onClick={() => setFilter(value)}
              >
                {label}
              </button>
            ))}
          </div>
          {loading ? (
            <div className="inbox-empty" role="status"><p>Loading conversations…</p></div>
          ) : visibleConversations.length === 0 ? (
            <div className="inbox-empty">
              <span className="inbox-empty-icon" aria-hidden="true">···</span>
              <h2>No conversations yet</h2>
              <p>{isDevelopment
                ? "The demo could not find conversations. Check the API connection and try again."
                : "New customer conversations will appear here."}</p>
            </div>
          ) : (
            <ul className="inbox-conversation-list">
              {visibleConversations.map((item) => (
                <li key={item.id}>
                  <button
                    type="button"
                    className={`inbox-conversation-button${item.id === selectedId ? " selected" : ""}`}
                    onClick={() => setSelectedId(item.id)}
                    aria-current={item.id === selectedId ? "true" : undefined}
                  >
                    <span className="inbox-conversation-heading">
                      <strong>{item.customer_name}</strong>
                      <span style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>
                        {item.unread_count > 0 && <span className="chip chip-warn">{item.unread_count} new</span>}
                        <span className={`chip ${item.status === "escalated" ? "chip-warn" : ""}`}>
                          {item.status === "escalated" ? "Needs you" : item.status}
                        </span>
                      </span>
                    </span>
                    <span className="inbox-conversation-preview">{item.last_message || "No messages yet"}</span>
                    {item.source === "demo" && <small>Synthetic demo conversation</small>}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {selectedConversation ? (
          <div className="surface-card inbox-detail inbox-thread">
            <div className="inbox-thread-heading">
              <div>
                <h2>{selectedConversation.customer_name}</h2>
                <p>{selectedConversation.source === "demo" ? "Synthetic conversation" : "Customer conversation"}</p>
              </div>
              <span className={`chip ${selectedConversation.status === "escalated" ? "chip-warn" : ""}`}>
                {selectedConversation.status === "escalated" ? "Seller review needed" : selectedConversation.status}
              </span>
            </div>

            {selectedConversation.escalation_reason && (
              <div className="inbox-escalation" role="status">
                <strong>Needs your attention</strong>
                <span>{selectedConversation.escalation_reason}</span>
                <small>The assistant will not take payment, promise a refund, or send messages.</small>
              </div>
            )}

            <div className="inbox-messages" aria-label="Conversation messages">
              {selectedConversation.messages.map((message) => (
                <article key={message.id} className={`inbox-message inbox-message-${message.sender}`}>
                  <small>{messageLabel(message, selectedConversation.source)}</small>
                  <p>{message.text}</p>
                  {message.sender === "agent" && message.evidence_ids.length > 0 && (
                    <small>Catalog evidence attached · {message.evidence_ids.length} reference(s)</small>
                  )}
                </article>
              ))}
            </div>

            <form className="inbox-reply-form" onSubmit={sendReply}>
              <label htmlFor="owner-reply">
                {selectedConversation.source === "public" ? "Reply to customer" : "Demo reply"}
              </label>
              <textarea
                id="owner-reply"
                rows={3}
                maxLength={1000}
                value={replyText}
                onChange={(event) => setReplyText(event.target.value)}
                placeholder={selectedConversation.source === "public"
                  ? "Write a reply to the customer…"
                  : "Write a note for this synthetic conversation…"}
              />
              <div className="inbox-form-actions">
                <button type="button" className="b" onClick={startVoiceInput}>
                  Use voice
                </button>
                <button type="submit" className="b p" disabled={submitting || !replyText.trim()}>
                  {selectedConversation.source === "public" ? "Send reply" : "Save demo reply"}
                </button>
              </div>
              <small role="status">{voiceStatus}</small>
              <small>Browser speech recognition may use your browser’s voice service. Review the transcript before saving.</small>
            </form>
          </div>
        ) : (
          <div className="surface-card inbox-detail">
            <span className="chip chip-warn">No conversation selected</span>
            <h2>{loading ? "Loading inbox…" : "Select a conversation"}</h2>
            <p>Customer messages and replies stay in their in-app workspace; no external service sends them.</p>
          </div>
        )}
      </section>

      <section className="surface-card inbox-widget-preview" aria-labelledby="widget-preview-heading">
        <div className="inbox-widget-header">
          <div>
            <span className="chip chip-warn">Preview only · synthetic data</span>
            <h2 id="widget-preview-heading">Customer chat widget</h2>
            <p>Try a question against the selected demo thread. Replies only use confirmed catalog facts.</p>
          </div>
          <span className="widget-preview-icon" aria-hidden="true">◉</span>
        </div>
        {selectedConversation?.source === "demo" ? (
          <>
            <div className="widget-preview-thread" aria-live="polite">
              {selectedConversation.messages.slice(-6).map((message) => (
                <div key={message.id} className={`widget-preview-message ${message.sender}`}>
                  <small>{messageLabel(message, "demo")}</small>
                  <p>{message.text}</p>
                </div>
              ))}
            </div>
            <form className="widget-preview-form" onSubmit={submitCustomerMessage}>
              <label className="sr-only" htmlFor="widget-customer-message">Simulate a customer message</label>
              <input
                id="widget-customer-message"
                value={customerText}
                maxLength={1000}
                onChange={(event) => setCustomerText(event.target.value)}
                placeholder="Try: What is the price?"
              />
              <button type="submit" className="b p" disabled={submitting || !customerText.trim()}>
                Simulate message
              </button>
            </form>
            {nextCursor && (
              <button
                type="button"
                className="b"
                onClick={() => void loadMoreConversations()}
                disabled={loadingMore}
              >
                {loadingMore ? "Loading…" : "Load older conversations"}
              </button>
            )}
          </>
        ) : (
          <p>Select a synthetic demo conversation to try the widget preview.</p>
        )}
        <small>Nothing is published or sent to real customers. Critical or unverified questions are escalated.</small>
      </section>
    </SellerShell>
  );
}
