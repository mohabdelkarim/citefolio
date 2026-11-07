"use client";

import { useEffect, useState } from "react";

import { ChatStream, type Message } from "@/components/chat_stream";
import { FeedbackRow } from "@/components/feedback_row";
import { UploadZone } from "@/components/upload_zone";
import {
  createSession,
  destroySessionBeacon,
  sendFeedback,
  streamQuery,
  uploadDocument,
  type Source,
} from "@/lib/api";
import {
  clearSessionId,
  readSessionId,
  writeSessionId,
} from "@/lib/session";

export default function HomePage() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [docLabel, setDocLabel] = useState<string | undefined>();
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [status, setStatus] = useState("Starting session…");
  const [messages, setMessages] = useState<Message[]>([]);
  const [feedbackNote, setFeedbackNote] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    let active = true;

    async function boot() {
      try {
        const existing = readSessionId();
        if (existing) {
          if (active) {
            setSessionId(existing);
            setStatus("Session ready");
          }
          return;
        }
        const created = await createSession();
        if (!active) return;
        writeSessionId(created.session_id);
        setSessionId(created.session_id);
        setStatus("Session ready");
      } catch {
        if (active) setStatus("Could not start session. Check API URL.");
      }
    }

    void boot();

    function onUnload() {
      const id = readSessionId();
      if (id) {
        destroySessionBeacon(id);
        clearSessionId();
      }
    }

    window.addEventListener("pagehide", onUnload);
    return () => {
      active = false;
      window.removeEventListener("pagehide", onUnload);
    };
  }, []);

  async function handleFile(file: File) {
    if (!sessionId) return;
    setUploadError(null);
    setUploading(true);
    setStatus("Indexing document…");
    try {
      const result = await uploadDocument(sessionId, file);
      setDocLabel(`${result.filename} · ${result.chunks_created} chunks`);
      setStatus("Document ready");
      setMessages([]);
      setFeedbackNote(null);
    } catch (error) {
      setDocLabel(undefined);
      setUploadError(error instanceof Error ? error.message : "Upload failed");
      setStatus("Upload failed");
    } finally {
      setUploading(false);
    }
  }

  async function handleAsk(query: string) {
    if (!sessionId) return;
    setFeedbackNote(null);
    setMessages((prev) => [
      ...prev,
      { role: "user", content: query },
      { role: "assistant", content: "", streaming: true, sources: [] },
    ]);

    let assembled = "";
    let sources: Source[] = [];

    try {
      await streamQuery(sessionId, query, {
        onToken: (token) => {
          assembled += token;
          setMessages((prev) => {
            const next = [...prev];
            next[next.length - 1] = {
              role: "assistant",
              content: assembled,
              streaming: true,
              sources,
            };
            return next;
          });
        },
        onSources: (nextSources) => {
          sources = nextSources;
          setMessages((prev) => {
            const next = [...prev];
            next[next.length - 1] = {
              role: "assistant",
              content: assembled,
              streaming: true,
              sources,
            };
            return next;
          });
        },
        onDone: () => {
          setMessages((prev) => {
            const next = [...prev];
            next[next.length - 1] = {
              role: "assistant",
              content: assembled,
              streaming: false,
              sources,
            };
            return next;
          });
        },
        onError: (message) => {
          setMessages((prev) => {
            const next = [...prev];
            next[next.length - 1] = {
              role: "assistant",
              content: message,
              streaming: false,
              error: true,
            };
            return next;
          });
        },
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Query failed";
      setMessages((prev) => {
        const next = [...prev];
        next[next.length - 1] = {
          role: "assistant",
          content: message,
          streaming: false,
          error: true,
        };
        return next;
      });
    }
  }

  async function handleRate(rating: 1 | -1) {
    if (!sessionId) return;
    await sendFeedback(sessionId, rating);
    setFeedbackNote(rating === 1 ? "Thanks." : "Noted — thanks for the signal.");
  }

  return (
    <main className="shell">
      <aside className="brand">
        <h1
          className="brand__name"
          style={{ fontFamily: "var(--font-display), Fraunces, Georgia, serif" }}
        >
          Citefolio
        </h1>
        <p className="brand__tag">Ask your PDF. Answers cite the page.</p>
        <UploadZone
          disabled={!sessionId || uploading}
          readyLabel={docLabel}
          onFile={handleFile}
          error={uploadError}
        />
        <div className="brand__meta" style={{ marginTop: "1.25rem" }}>
          <span>{status}</span>
          <span>Ephemeral · no login · 2h TTL</span>
        </div>
      </aside>

      <section className="stage">
        <ChatStream
          disabled={!docLabel || uploading}
          messages={messages}
          onAsk={handleAsk}
        />
        {messages.some((m) => m.role === "assistant" && !m.streaming && m.content) ? (
          <FeedbackRow onRate={handleRate} note={feedbackNote} />
        ) : null}
      </section>
    </main>
  );
}
