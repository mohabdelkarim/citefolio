export type Source = {
  filename: string;
  page: string | number;
  snippet?: string;
};

export type UploadResult = {
  status: string;
  session_id: string;
  chunks_created: number;
  filename: string;
  estimated_pages: number;
};

function apiBase(): string {
  const base =
    process.env.NEXT_PUBLIC_API_URL || "https://citefolio-api.vercel.app";
  return base.replace(/\/$/, "");
}

export async function createSession(): Promise<{
  session_id: string;
  expires_at: string;
}> {
  const res = await fetch(`${apiBase()}/api/session`, { method: "POST" });
  if (!res.ok) {
    throw new Error("Could not create session");
  }
  return res.json();
}

export function destroySessionBeacon(sessionId: string): void {
  const url = `${apiBase()}/api/session/${sessionId}`;
  void fetch(url, { method: "DELETE", keepalive: true });
}

export async function uploadDocument(
  sessionId: string,
  file: File,
): Promise<UploadResult> {
  const body = new FormData();
  body.append("session_id", sessionId);
  body.append("file", file);
  const res = await fetch(`${apiBase()}/api/upload`, {
    method: "POST",
    body,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || `Upload failed (${res.status})`);
  }
  return data as UploadResult;
}

export async function streamQuery(
  sessionId: string,
  query: string,
  handlers: {
    onToken: (token: string) => void;
    onSources: (sources: Source[]) => void;
    onDone: (meta: Record<string, unknown>) => void;
    onError: (message: string) => void;
  },
): Promise<void> {
  const res = await fetch(`${apiBase()}/api/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, query }),
  });
  if (!res.ok || !res.body) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `Query failed (${res.status})`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() || "";

    for (const part of parts) {
      const lines = part.split("\n");
      let event = "message";
      let dataLine = "";
      for (const line of lines) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        if (line.startsWith("data:")) dataLine += line.slice(5).trim();
      }
      if (!dataLine) continue;
      const payload = JSON.parse(dataLine) as Record<string, unknown>;
      if (event === "token") {
        handlers.onToken(String(payload.content || ""));
      } else if (event === "sources") {
        handlers.onSources((payload.sources as Source[]) || []);
      } else if (event === "done") {
        handlers.onDone(payload);
      } else if (event === "error") {
        handlers.onError(String(payload.detail || "Query failed"));
      }
    }
  }
}

export async function sendFeedback(
  sessionId: string,
  rating: 1 | -1,
  comment?: string,
): Promise<void> {
  await fetch(`${apiBase()}/api/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, rating, comment }),
  });
}
