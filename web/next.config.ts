import type { NextConfig } from "next";

const isGithubPages = process.env.GITHUB_PAGES === "true";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
  // Project Pages URL: https://mohabdelkarim.github.io/citefolio/
  ...(isGithubPages
    ? {
        basePath: "/citefolio",
        assetPrefix: "/citefolio",
      }
    : {}),
};

export default nextConfig;
