const TOKEN_KEY = "medbot_token";
const IDENTITY_KEY = "medbot_identity_type";

export type IdentityType = "user" | "guest" | "admin";

export function saveToken(token: string, identityType: IdentityType) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(IDENTITY_KEY, identityType);
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getIdentityType(): IdentityType | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(IDENTITY_KEY) as IdentityType | null;
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(IDENTITY_KEY);
}

export function isLoggedIn(): boolean {
  return !!getToken();
}
