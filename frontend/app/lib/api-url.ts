const LOOPBACK_HOSTS = new Set(["localhost", "127.0.0.1", "[::1]"]);

export function getBrowserApiUrl(path: string): string {
  const configuredBase = process.env.NEXT_PUBLIC_API_URL;
  if (!configuredBase) throw new Error("NEXT_PUBLIC_API_URL is not configured.");

  const apiBase = new URL(configuredBase);
  if (
    typeof window !== "undefined"
    && LOOPBACK_HOSTS.has(apiBase.hostname)
    && LOOPBACK_HOSTS.has(window.location.hostname)
  ) {
    apiBase.hostname = window.location.hostname;
  }

  return `${apiBase.toString().replace(/\/+$/, "")}/v1${path}`;
}
