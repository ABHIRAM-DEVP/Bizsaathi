"use client";

import { useEffect, useState, useCallback } from "react";
import { fetchHealth } from "../../src/lib/api-client";

export type ConnectionState = "loading" | "success" | "error" | "offline";

interface ConnectionStatusProps {
  initialState?: ConnectionState;
}

export function ConnectionStatus({ initialState }: ConnectionStatusProps) {
  const [status, setStatus] = useState<ConnectionState>(initialState || "loading");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<string | null>(null);

  const checkConnectivity = useCallback(async () => {
    if (typeof window !== "undefined" && !window.navigator.onLine) {
      setStatus("offline");
      setErrorMessage("Your device appears to be offline. Please check your network connection.");
      return;
    }

    try {
      const data = await fetchHealth();
      if (data.status === "ok") {
        setStatus("success");
        setErrorMessage(null);
        setLastChecked(new Date().toLocaleTimeString());
      } else {
        setStatus("error");
        setErrorMessage("Unexpected response from API server.");
      }
    } catch (err: unknown) {
      setStatus("error");
      const msg = err instanceof Error ? err.message : "Failed to connect to API server";
      setErrorMessage(msg);
    }
  }, []);

  const handleManualRetry = () => {
    setStatus("loading");
    setErrorMessage(null);
    checkConnectivity();
  };

  useEffect(() => {
    if (initialState) return;

    const initialTimer = setTimeout(() => {
      checkConnectivity();
    }, 0);

    const handleOnline = () => {
      setStatus("loading");
      checkConnectivity();
    };
    const handleOffline = () => {
      setStatus("offline");
      setErrorMessage("Device is offline");
    };

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    const interval = setInterval(checkConnectivity, 30000);

    return () => {
      clearTimeout(initialTimer);
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
      clearInterval(interval);
    };
  }, [checkConnectivity, initialState]);

  return (
    <div
      data-testid="connection-status"
      role="status"
      aria-live="polite"
      className="w-full rounded-xl border p-4 transition-all duration-200 backdrop-blur-sm"
      style={{
        backgroundColor:
          status === "success"
            ? "rgba(240, 253, 244, 0.9)"
            : status === "loading"
            ? "rgba(248, 250, 252, 0.9)"
            : status === "offline"
            ? "rgba(254, 252, 232, 0.9)"
            : "rgba(254, 242, 242, 0.9)",
        borderColor:
          status === "success"
            ? "#86efac"
            : status === "loading"
            ? "#cbd5e1"
            : status === "offline"
            ? "#fde047"
            : "#fca5a5",
      }}
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="relative flex h-3 w-3">
            {status === "loading" && (
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-slate-400 opacity-75" />
            )}
            {status === "success" && (
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            )}
            {status === "error" && (
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75" />
            )}
            {status === "offline" && (
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75" />
            )}
            <span
              className="relative inline-flex rounded-full h-3 w-3"
              style={{
                backgroundColor:
                  status === "success"
                    ? "#16a34a"
                    : status === "loading"
                    ? "#64748b"
                    : status === "offline"
                    ? "#ca8a04"
                    : "#dc2626",
              }}
            />
          </span>

          <div>
            <div className="font-semibold text-sm capitalize text-slate-800">
              {status === "loading" && "Connecting to BizSaathi Engine..."}
              {status === "success" && "API Engine Online"}
              {status === "error" && "API Engine Offline / Error"}
              {status === "offline" && "Device Offline"}
            </div>
            {errorMessage && (
              <p className="text-xs text-rose-700 mt-0.5">{errorMessage}</p>
            )}
            {lastChecked && status === "success" && (
              <p className="text-xs text-emerald-700 mt-0.5">
                Verified at {lastChecked}
              </p>
            )}
          </div>
        </div>

        {(status === "error" || status === "offline") && (
          <button
            onClick={handleManualRetry}
            className="self-start sm:self-auto px-3 py-1.5 text-xs font-medium rounded-lg bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 transition shadow-sm"
          >
            Retry Connection
          </button>
        )}
      </div>
    </div>
  );
}
