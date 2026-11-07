declare module "@/lib/render_markdown.mjs" {
  export function escapeHtml(text: string): string;
  export function stripInlineCitations(text: string): string;
  export function renderMarkdownToSafeHtml(markdown: string): string;
}

declare module "./render_markdown.mjs" {
  export function escapeHtml(text: string): string;
  export function stripInlineCitations(text: string): string;
  export function renderMarkdownToSafeHtml(markdown: string): string;
}
