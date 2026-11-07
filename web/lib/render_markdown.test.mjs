import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  renderMarkdownToSafeHtml,
  stripInlineCitations,
} from "./render_markdown.mjs";

describe("renderMarkdownToSafeHtml", () => {
  it("escapes HTML", () => {
    const html = renderMarkdownToSafeHtml('<script>alert(1)</script>');
    assert.equal(html.includes("<script>"), false);
    assert.equal(html.includes("&lt;script&gt;"), true);
  });

  it("renders paragraphs and bold", () => {
    const html = renderMarkdownToSafeHtml("Hello **world**.\n\nNext line.");
    assert.match(html, /<p>Hello <strong>world<\/strong>\.<\/p>/);
    assert.match(html, /<p>Next line\.<\/p>/);
  });

  it("renders unordered lists from asterisks", () => {
    const html = renderMarkdownToSafeHtml("* One\n* Two");
    assert.match(html, /<ul>/);
    assert.match(html, /<li>One<\/li>/);
    assert.match(html, /<li>Two<\/li>/);
  });
});

describe("stripInlineCitations", () => {
  it("removes bracket citations when sources exist", () => {
    const text = "Answer. [CV.pdf, p.1] More. [CV.pdf, p.2]";
    assert.equal(stripInlineCitations(text), "Answer. More.");
  });
});
