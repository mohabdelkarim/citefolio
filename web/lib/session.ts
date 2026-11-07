const SESSION_KEY = "citefolio_session_id";

export function readSessionId(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem(SESSION_KEY);
}

export function writeSessionId(sessionId: string): void {
  sessionStorage.setItem(SESSION_KEY, sessionId);
}

export function clearSessionId(): void {
  sessionStorage.removeItem(SESSION_KEY);
}
