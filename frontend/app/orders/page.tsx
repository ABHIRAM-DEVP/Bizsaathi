"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { SellerShell } from "../components/SellerShell";
import { listOrders, RuntimeApiError, type CustomerOrder } from "@/lib/api-client/runtime";

function formatPrice(value: string | number): string {
  const amount = Number(value);
  return Number.isFinite(amount)
    ? new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(amount)
    : "Price unavailable";
}

function orderErrorMessage(error: unknown): string {
  if (error instanceof RuntimeApiError) return error.message;
  return "Orders could not be loaded. Check the API connection and try again.";
}

const statusLabels: Record<CustomerOrder["status"], string> = {
  DRAFT: "Needs review",
  AWAITING_PAYMENT: "Awaiting payment",
  PAID: "Paid",
  FULFILLED: "Fulfilled",
  CANCELLED: "Cancelled",
  FAILED: "Failed",
};

export default function OrdersPage() {
  const [orders, setOrders] = useState<CustomerOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    listOrders()
      .then((result) => {
        if (!cancelled) setOrders(result);
      })
      .catch((cause: unknown) => {
        if (!cancelled) setError(orderErrorMessage(cause));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <SellerShell>
      <Link href="/" className="back-link">← Home</Link>
      <header className="page-heading">
        <div>
          <h1>Orders</h1>
          <p>Orders and line-item prices are loaded from your tenant-scoped catalog records.</p>
        </div>
        <span className="chip chip-good">Connected</span>
      </header>

      {error && <p role="alert" className="surface-card">{error}</p>}
      {loading ? (
        <section className="surface-card orders-empty" aria-live="polite">
          <h2>Loading orders…</h2>
        </section>
      ) : orders.length === 0 && !error ? (
        <section className="surface-card orders-empty" aria-labelledby="orders-empty-title">
          <span className="orders-empty-icon" aria-hidden="true">—</span>
          <h2 id="orders-empty-title">No orders yet</h2>
          <p>New customer orders will appear here after they are recorded for this business.</p>
          <div className="orders-empty-actions">
            <Link href="/products" className="b">Open catalog</Link>
            <Link href="/approvals" className="b p">Review approvals</Link>
          </div>
        </section>
      ) : (
        <section aria-label="Order list" style={{ display: "grid", gap: 14 }}>
          {orders.map((order) => (
            <article key={order.id} className="surface-card" style={{ display: "grid", gap: 12 }}>
              <header style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", gap: 10 }}>
                <div>
                  <h2 style={{ margin: 0, fontSize: 17 }}>{order.customer_name}</h2>
                  <p style={{ margin: "5px 0 0", color: "#5B6A64", fontSize: 13 }}>
                    {new Date(order.created_at).toLocaleString()}
                  </p>
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", alignItems: "start", gap: 8 }}>
                  <span className="chip">{statusLabels[order.status]}</span>
                  {order.demo_sample && <span className="chip chip-warn">Synthetic demo data</span>}
                </div>
              </header>
              <ul style={{ display: "grid", gap: 8, margin: 0, padding: 0, listStyle: "none" }}>
                {order.items.map((item, index) => (
                  <li key={`${item.variant_id}-${index}`} style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                    <span>{item.product_name} × {item.quantity}</span>
                    <span>{formatPrice(item.unit_price_inr)}</span>
                  </li>
                ))}
              </ul>
              <footer style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", gap: 8, borderTop: "1px solid #E1E8E4", paddingTop: 10 }}>
                <span>
                  {order.payment_method
                    ? `Payment method: ${order.payment_method}${order.demo_sample ? " (sample)" : ""}`
                    : "Payment not recorded"}
                </span>
                <strong>Total {formatPrice(order.total_inr)}</strong>
              </footer>
              {order.delivery_note && <p style={{ margin: 0, color: "#5B6A64", fontSize: 13 }}>{order.delivery_note}</p>}
              {order.status === "DRAFT" && (
                <Link href="/approvals" className="b p" style={{ justifySelf: "start" }}>Review order approval</Link>
              )}
            </article>
          ))}
        </section>
      )}
    </SellerShell>
  );
}
