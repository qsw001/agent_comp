import type { ApiResponse } from "@/types";

const TOKEN_KEY = "auth_token";
const DEFAULT_REDIRECT = "/dashboard";

function readCookie(name: string) {
  if (typeof document === "undefined") return null;

  const cookie = document.cookie
    .split("; ")
    .find((item) => item.startsWith(`${name}=`));

  if (!cookie) return null;
  return decodeURIComponent(cookie.split("=").slice(1).join("="));
}

export function getAuthToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY) || readCookie(TOKEN_KEY);
}

export function saveAuthToken(token: string, expiresInHours: number) {
  const maxAge = expiresInHours * 60 * 60;
  localStorage.setItem(TOKEN_KEY, token);
  document.cookie = `${TOKEN_KEY}=${encodeURIComponent(token)}; path=/; max-age=${maxAge}; SameSite=Lax`;
}

export function clearAuthToken() {
  if (typeof window === "undefined") return;

  localStorage.removeItem(TOKEN_KEY);
  document.cookie = `${TOKEN_KEY}=; path=/; max-age=0; SameSite=Lax`;
}

export function getSafeNext(value: string | null) {
  if (!value) return DEFAULT_REDIRECT;
  if (!value.startsWith("/") || value.startsWith("//")) return DEFAULT_REDIRECT;
  return value;
}

export function getApiErrorMessage(error: unknown, fallback = "请求失败，请稍后再试") {
  const responseData = (error as { response?: { data?: ApiResponse<never> | { detail?: unknown } } })
    ?.response?.data;

  if (responseData && "error" in responseData && responseData.error?.message) {
    return responseData.error.message;
  }

  const detail = responseData && "detail" in responseData ? responseData.detail : null;
  if (typeof detail === "string") return detail;
  if (
    detail &&
    typeof detail === "object" &&
    "message" in detail &&
    typeof detail.message === "string"
  ) {
    return detail.message;
  }

  return error instanceof Error ? error.message : fallback;
}
