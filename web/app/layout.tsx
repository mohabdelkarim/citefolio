import type { Metadata } from "next";
import { Fraunces, IBM_Plex_Mono, IBM_Plex_Sans } from "next/font/google";

import "./globals.css";

const display = Fraunces({
  subsets: ["latin"],
  variable: "--font-display",
});

const sans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-sans",
});

const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-mono",
});

const siteUrl = "https://mohabdelkarim.github.io/citefolio";
const title = "Citefolio";
const description = "Ask your PDF. Answers cite the page.";

export const viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover" as const,
};

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: title,
    template: "%s · Citefolio",
  },
  description,
  applicationName: "Citefolio",
  keywords: [
    "RAG",
    "PDF Q&A",
    "citations",
    "pgvector",
    "Next.js",
    "FastAPI",
    "Neon",
  ],
  authors: [{ name: "MOHAbdelkarim", url: "https://github.com/mohabdelkarim" }],
  creator: "MOHAbdelkarim",
  icons: {
    icon: [
      { url: "/icon.svg", type: "image/svg+xml" },
      { url: "/favicon.ico", sizes: "any" },
    ],
    apple: [{ url: "/apple-touch-icon.png", sizes: "180x180" }],
  },
  openGraph: {
    type: "website",
    url: siteUrl,
    title,
    description,
    siteName: "Citefolio",
    images: [
      {
        url: "/og.png",
        width: 1200,
        height: 630,
        alt: "Citefolio — Ask your PDF. Answers cite the page.",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title,
    description,
    images: ["/og.png"],
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${display.variable} ${sans.variable} ${mono.variable}`}>
      <body style={{ fontFamily: "var(--font-sans), IBM Plex Sans, sans-serif" }}>
        {children}
      </body>
    </html>
  );
}
