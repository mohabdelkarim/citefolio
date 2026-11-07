"use client";

import { FormEvent, useEffect, useRef, useState } from "react";

import { SourceList } from "@/components/source_list";
import type { Source } from "@/lib/api";
import {
  renderMarkdownToSafeHtml,
  stripInlineCitations,
} from "@/lib/render_markdown.mjs";

type Message = {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  streaming?: boolean;
  error?: boolean;
};

type ChatStreamProps = {
  disabled?: boolean;
  messages: Message[];
  onAsk: (query: string) => Promise<void>;
};

function AssistantBody({
  content,
  sources,
  streaming,
  error,
}: {
  content: string;
  sources?: Source[];
  streaming?: boolean;
  error?: boolean;
}) {
  if (error) {
    return <p className="bubble__error">{content || "Something went wrong."}</p>;
  }

  const display =
    sources && sources.length > 0 ? stripInlineCitations(content) : content;
  const html = renderMarkdownToSafeHtml(display);

  if (!html && streaming) {
    return (
      <p className="bubble__pending">
        Thinking
        <span className="caret" aria-hidden />
      </p>
    );
  }

  return (
    <div className="bubble__md">
      <div dangerouslySetInnerHTML={{ __html: html }} />
      {streaming ? <span className="caret" aria-hidden /> : null}
    </div>
  );
}

export function ChatStream({ disabled, messages, onAsk }: ChatStreamProps) {
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const logRef = useRef<HTMLDivElement>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end", behavior: "smooth" });
  }, [messages]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const query = draft.trim();
    if (!query || busy || disabled) return;
    setBusy(true);
    setDraft("");
    try {
      await onAsk(query);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="chat">
      <div className="chat__log" ref={logRef} aria-live="polite">
        {messages.length === 0 ? (
          <div className="chat__empty" role="status">
            <p className="chat__empty-title">Ready when you are</p>
            <p className="chat__empty-copy">
              Upload a PDF, then ask a concrete question. Answers cite the page.
            </p>
          </div>
        ) : (
          messages.map((message, index) => (
            <article
              key={`${message.role}-${index}`}
              className={[
                "bubble",
                `bubble--${message.role}`,
                message.error ? "bubble--error" : "",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              {message.role === "user" ? (
                <p className="bubble__text">{message.content}</p>
              ) : (
                <AssistantBody
                  content={message.content}
                  sources={message.sources}
                  streaming={message.streaming}
                  error={message.error}
                />
              )}
              {message.role === "assistant" &&
              message.sources &&
              message.sources.length > 0 &&
              !message.error ? (
                <SourceList sources={message.sources} />
              ) : null}
            </article>
          ))
        )}
        <div ref={endRef} className="chat__anchor" aria-hidden />
      </div>
      <form className="composer" onSubmit={handleSubmit}>
        <input
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder={disabled ? "Upload a document first" : "Ask about the document"}
          disabled={disabled || busy}
          maxLength={1000}
          aria-label="Ask about the document"
        />
        <button type="submit" disabled={disabled || busy || !draft.trim()}>
          Ask
        </button>
      </form>
    </section>
  );
}

export type { Message };
