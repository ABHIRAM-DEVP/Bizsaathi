"use client";

import { useCallback, useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { SellerShell } from "../components/SellerShell";
import {
  adjustCatalogStock,
  archiveCatalogProduct,
  listCatalogProducts,
  productImageUrl,
  RuntimeApiError,
  updateCatalogProduct,
  type CatalogProduct,
} from "@/lib/api-client/runtime";

const inputStyle = {
  width: "100%",
  minHeight: 40,
  padding: "8px 10px",
  border: "1px solid #D5DFDA",
  borderRadius: 8,
  fontSize: 14,
};

function errorText(cause: unknown): string {
  return cause instanceof RuntimeApiError ? cause.message : "The request failed. Check the API connection and retry.";
}

function formatPrice(price: string | number): string {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(Number(price));
}

export default function ProductsPage() {
  const [products, setProducts] = useState<CatalogProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [filter, setFilter] = useState<"all" | "active" | "archived" | "low">("all");
  const [search, setSearch] = useState("");
  const [editing, setEditing] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [price, setPrice] = useState("");
  const [stockDelta, setStockDelta] = useState("");
  const [imageErrors, setImageErrors] = useState<string[]>([]);

  const refresh = useCallback(async () => {
    setError("");
    setLoading(true);
    try {
      setProducts(await listCatalogProducts("all"));
    } catch (cause: unknown) {
      setError(errorText(cause));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    listCatalogProducts("all")
      .then((records) => {
        if (!cancelled) setProducts(records);
      })
      .catch((cause: unknown) => {
        if (!cancelled) setError(errorText(cause));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  const visible = products.filter((product) => {
    const matchesText = product.name.toLowerCase().includes(search.toLowerCase());
    const matchesFilter = filter === "all"
      || (filter === "active" && product.status === "active")
      || (filter === "archived" && product.status === "archived")
      || (filter === "low" && product.status === "active" && product.stock < 5);
    return matchesText && matchesFilter;
  });

  function beginEdit(product: CatalogProduct) {
    setEditing(product.id);
    setName(product.name);
    setDescription(product.description ?? "");
    setPrice(String(product.price_inr));
    setStockDelta("");
    setError("");
    setNotice("");
  }

  async function saveEdit(product: CatalogProduct) {
    if (!name.trim() || !/^\d+(?:\.\d{1,2})?$/.test(price) || Number(price) <= 0) {
      setError("Enter a product name and a positive confirmed price with at most two decimals.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const updated = await updateCatalogProduct(product, {
        name: name.trim(),
        description: description.trim() || null,
        price_inr: price,
      });
      setProducts((current) => current.map((item) => item.id === updated.id ? updated : item));
      setEditing(null);
      setNotice("Confirmed product details saved.");
    } catch (cause: unknown) {
      setError(errorText(cause));
    } finally {
      setBusy(false);
    }
  }

  async function changeStock(product: CatalogProduct) {
    if (!/^-?\d+$/.test(stockDelta) || Number(stockDelta) === 0) {
      setError("Enter a non-zero whole-number stock adjustment.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const updated = await adjustCatalogStock(product, Number(stockDelta));
      setProducts((current) => current.map((item) => item.id === product.id
        ? { ...item, stock: updated.stock, stock_version: updated.stock_version }
        : item));
      setStockDelta("");
      setNotice("Stock adjustment saved.");
    } catch (cause: unknown) {
      setError(errorText(cause));
    } finally {
      setBusy(false);
    }
  }

  async function archive(product: CatalogProduct) {
    if (!window.confirm(`Archive ${product.name}? It will no longer be offered for new posts.`)) return;
    setBusy(true);
    setError("");
    try {
      await archiveCatalogProduct(product.id);
      setProducts((current) => current.map((item) => item.id === product.id ? { ...item, status: "archived" } : item));
      setNotice("Product archived. Existing records were kept.");
    } catch (cause: unknown) {
      setError(errorText(cause));
    } finally {
      setBusy(false);
    }
  }

  return (
    <SellerShell>
      <Link href="/" className="back-link">← Home</Link>
      <header className="page-heading">
        <div><h1>My Products</h1><p>{products.length} catalog products. Facts shown here are owner-confirmed.</p></div>
        <Link href="/products/new" className="button button-primary">+ New product</Link>
      </header>
      {error && <p role="alert" className="surface-card" style={{ padding: 14, color: "#8A1F1F" }}>{error}</p>}
      {notice && <p role="status" className="surface-card" style={{ padding: 14, color: "#0B6E5C" }}>{notice}</p>}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 10, alignItems: "center" }}>
        <label style={{ flex: "1 1 240px" }}>Search catalog
          <input value={search} onChange={(event) => setSearch(event.target.value)} style={inputStyle} />
        </label>
        <label>Show
          <select value={filter} onChange={(event) => setFilter(event.target.value as typeof filter)} style={inputStyle}>
            <option value="all">All</option><option value="active">Active</option><option value="low">Low stock</option><option value="archived">Archived</option>
          </select>
        </label>
        <button type="button" className="button" onClick={() => void refresh()} disabled={loading || busy}>Refresh</button>
      </div>
      {loading ? <p role="status">Loading catalog…</p> : visible.length === 0 ? (
        <section className="surface-card" style={{ padding: 24, textAlign: "center" }}>
          <h2>{products.length === 0 ? "Your catalog is empty" : "No matching products"}</h2>
          <p>Add confirmed product information to use post generation and stock tracking.</p>
          <Link href="/products/new" className="button button-primary">Add a product</Link>
        </section>
      ) : (
        <div className="product-grid">
          {visible.map((product) => (
            <article key={product.id} className="surface-card product-card" style={{ overflow: "hidden", padding: 0 }}>
              {product.status === "active" && !imageErrors.includes(product.id) ? (
                <Image src={productImageUrl(product.id)} alt={`${product.name} product photo`} width={480} height={170} unoptimized onError={() => setImageErrors((current) => current.includes(product.id) ? current : [...current, product.id])} style={{ width: "100%", height: 170, objectFit: "cover", background: "#EEF2EF" }} />
              ) : (
                <div className="product-photo-placeholder" aria-label={`No photo for ${product.name}`}>No product photo</div>
              )}
              <div style={{ padding: 16, display: "grid", gap: 10 }}>
                <div><h2 style={{ margin: 0, fontSize: 18 }}>{product.name}</h2><p style={{ margin: "5px 0", color: "#5B6A64" }}>{formatPrice(product.price_inr)} · {product.stock} in stock · {product.status}</p></div>
                {editing === product.id ? (
                  <div style={{ display: "grid", gap: 8 }}>
                    <label>Name<input value={name} onChange={(event) => setName(event.target.value)} maxLength={200} style={inputStyle} /></label>
                    <label>Description<textarea value={description} onChange={(event) => setDescription(event.target.value)} maxLength={5000} style={inputStyle} /></label>
                    <label>Owner-confirmed price (INR)<input type="number" min="0.01" step="0.01" value={price} onChange={(event) => setPrice(event.target.value)} style={inputStyle} /></label>
                    <div style={{ display: "flex", gap: 8 }}><button type="button" className="button button-primary" disabled={busy} onClick={() => void saveEdit(product)}>Save details</button><button type="button" className="button" onClick={() => setEditing(null)}>Cancel</button></div>
                  </div>
                ) : (
                  <>
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                      <Link href={`/posts?product_id=${encodeURIComponent(product.id)}`} className="button button-primary">Create post</Link>
                      {product.status === "active" && <button className="button" type="button" onClick={() => beginEdit(product)} disabled={busy}>Edit</button>}
                      {product.status === "active" && <button className="button" type="button" onClick={() => void archive(product)} disabled={busy}>Archive</button>}
                    </div>
                    {product.status === "active" && <div style={{ display: "flex", gap: 8 }}>
                      <label style={{ flex: 1 }}>Stock change (+/-)<input aria-label={`Stock adjustment for ${product.name}`} type="number" step="1" value={editing === product.id ? stockDelta : undefined} onChange={(event) => setStockDelta(event.target.value)} style={inputStyle} /></label>
                      <button className="button" type="button" disabled={busy} onClick={() => void changeStock(product)}>Adjust stock</button>
                    </div>}
                  </>
                )}
              </div>
            </article>
          ))}
        </div>
      )}
    </SellerShell>
  );
}
