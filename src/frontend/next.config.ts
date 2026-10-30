import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  experimental: {
    optimizePackageImports: [
      "lucide-react",
      "radix-ui",
      "recharts",
      "date-fns",
    ],
  },
};

export default nextConfig;
