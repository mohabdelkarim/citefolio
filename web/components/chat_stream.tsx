"use client";

import { FormEvent, useState } from "react";

import { SourceList } from "@/components/source_list";
import type { Source } from "@/lib/api";

type Message = {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  streaming?: boolean;
};

type ChatStreamProps = {
  disabled?: boolean;
  messages: Message[];
  onAsk: (query: string) => Promise<void>;
};

export function ChatStream({ disabled, messages, onAsk }: ChatStreamProps) {
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);

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
      <div className="chat__log" aria-live="polite">
        {messages.length === 0 ? (
          <p className="chat__empty">
            Upload a document, then ask a concrete question. Answers cite the page.
          </p>
        ) : (
          messages.map((message, index) => (
            <article
              key={`${message.role}-${index}`}
              className={`bubble bubble--${message.role}`}
            >
              <p>
                {message.content}
                {message.streaming ? <span className="caret" aria-hidden /> : null}
              </p>
              {message.sources ? <SourceList sources={message.sources} /> : null}
            </article>
          ))
        )}
      </div>
      <form className="composer" onSubmit={handleSubmit}>
        <input
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder={disabled ? "Upload a document first" : "Ask about the document"}
          disabled={disabled || busy}
          maxLength={1000}
        />
        <button type="submit" disabled={disabled || busy || !draft.trim()}>
          Ask
        </button>
      </form>
    </section>
  );
}

export type { Message };
