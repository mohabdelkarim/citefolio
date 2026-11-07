"use client";

import type { Source } from "@/lib/api";

type SourceListProps = {
  sources: Source[];
};

export function SourceList({ sources }: SourceListProps) {
  if (!sources.length) return null;
  return (
    <ul className="sources">
      {sources.map((source) => (
        <li key={`${source.filename}-${source.page}`} className="sources__chip">
          <span className="sources__file">{source.filename}</span>
          <span className="sources__page">p.{source.page}</span>
        </li>
      ))}
    </ul>
  );
}
