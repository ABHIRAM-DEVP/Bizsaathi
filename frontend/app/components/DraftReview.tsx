"use client";

import { useState } from "react";

type DraftReviewProps = { productName?: string };

export function DraftReview({ productName = "Cotton blend kurta" }: DraftReviewProps) {
  const [conflictChoice, setConflictChoice] = useState<"catalogue" | "suggestion" | null>(null);
  const [price, setPrice] = useState("");
  const [stock, setStock] = useState("");
  const canConfirm = Boolean(conflictChoice && price && stock);

  return (
    <section className="space-y-5 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div>
        <p className="text-sm font-medium text-sky-700">Suggested by AI</p>
        <h2 className="text-xl font-bold">{productName}</h2>
        <p className="mt-1 text-sm text-slate-600">Review suggestions. Nothing becomes a catalogue fact until you confirm it.</p>
      </div>
      <div className="rounded-lg border border-amber-300 bg-amber-50 p-4">
        <p className="font-semibold text-amber-900">Needs your confirmation: material</p>
        <p className="text-sm text-amber-800">The photo is blurry, so material was not treated as a confirmed value.</p>
      </div>
      <fieldset className="rounded-lg border border-rose-300 bg-rose-50 p-4">
        <legend className="px-1 font-semibold text-rose-900">Conflict: colour</legend>
        <p className="mb-3 text-sm text-rose-800">Choose one value before continuing.</p>
        <label className="mr-4 inline-flex gap-2"><input type="radio" name="colour" onChange={() => setConflictChoice("catalogue")} /> Existing catalogue: blue</label>
        <label className="inline-flex gap-2"><input type="radio" name="colour" onChange={() => setConflictChoice("suggestion")} /> AI suggestion: green</label>
      </fieldset>
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="font-medium">Confirmed price (INR)<input aria-label="Confirmed price (INR)" value={price} onChange={(event) => setPrice(event.target.value)} inputMode="decimal" className="mt-1 block w-full rounded border border-slate-300 p-2" placeholder="Required" /></label>
        <label className="font-medium">Confirmed stock<input aria-label="Confirmed stock" value={stock} onChange={(event) => setStock(event.target.value)} inputMode="numeric" className="mt-1 block w-full rounded border border-slate-300 p-2" placeholder="Required" /></label>
      </div>
      <button disabled={!canConfirm} className="rounded bg-sky-700 px-4 py-2 font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-300">Create approval request</button>
    </section>
  );
}
