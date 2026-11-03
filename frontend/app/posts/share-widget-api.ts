import { getRuntimeAuthHeaders, redirectToLocalSignInIfNeeded } from "@/lib/api-client/runtime";
import { getBrowserApiUrl } from "../lib/api-url";

interface BusinessProfile {
  id: string;
  name: string;
  slug: string;
}

export async function getCurrentBusinessProfile(): Promise<BusinessProfile> {
  const response = await fetch(getBrowserApiUrl("/businesses/me"), {
    credentials: "include",
    cache: "no-store",
    headers: {
      Accept: "application/json",
      ...getRuntimeAuthHeaders(),
    },
  });
  if (!response.ok) {
    if (redirectToLocalSignInIfNeeded(response.status)) {
      throw new Error("Sign in to your local account to continue.");
    }
    let message = `Could not load the public store link (${response.status}).`;
    try {
      const problem: unknown = await response.json();
      if (typeof problem === "object" && problem !== null && "detail" in problem) {
        const detail = problem.detail;
        if (typeof detail === "string") message = detail;
        else if (typeof detail === "object" && detail !== null && "detail" in detail
          && typeof detail.detail === "string") message = detail.detail;
      }
    } catch {
      message = `Could not load the public store link (${response.status}).`;
    }
    throw new Error(message);
  }
  return response.json() as Promise<BusinessProfile>;
}
