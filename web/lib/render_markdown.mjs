/** Minimal safe markdown → HTML. Escape first; then bold, lists, paragraphs. */

/**
 * @param {string} text
 * @returns {string}
 */
export function escapeHtml(text) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

/**
 * Strip trailing/inline `[file, p.N]` citations when chips carry sources.
 * @param {string} text
 * @returns {string}
 */
export function stripInlineCitations(text) {
  return text
    .replace(/\s*\[[^\[\]]+,\s*p\.\s*[\d.]+\]/gi, "")
    .replace(/[ \t]+\n/g, "\n")
    .replace(/ {2,}/g, " ")
    .trim();
}

/**
 * @param {string} inline
 * @returns {string}
 */
function formatInline(inline) {
  return escapeHtml(inline).replace(
    /\*\*(.+?)\*\*/g,
    "<strong>$1</strong>",
  );
}

/**
 * @param {string} markdown
 * @returns {string}
 */
export function renderMarkdownToSafeHtml(markdown) {
  const source = String(markdown || "").replace(/\r\n/g, "\n").trim();
  if (!source) return "";

  const blocks = source.split(/\n{2,}/);
  /** @type {string[]} */
  const html = [];

  for (const block of blocks) {
    const lines = block.split("\n");
    const listItems = lines.every((line) => /^\s*([-*]|\d+\.)\s+/.test(line));

    if (listItems) {
      const items = lines
        .map((line) => line.replace(/^\s*([-*]|\d+\.)\s+/, ""))
        .map((item) => `<li>${formatInline(item)}</li>`)
        .join("");
      html.push(`<ul>${items}</ul>`);
      continue;
    }

    // Soft line breaks inside a paragraph
    const joined = lines.map((line) => formatInline(line)).join("<br />");
    html.push(`<p>${joined}</p>`);
  }

  return html.join("");
}
