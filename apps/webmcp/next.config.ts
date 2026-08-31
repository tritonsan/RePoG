import type { NextConfig } from 'next';

const nextConfig: NextConfig = { async headers() { return [{ source: '/(.*)', headers: [
  { key: 'Permissions-Policy', value: 'tools=(self)' }, { key: 'Origin-Agent-Cluster', value: '?1' },
  { key: 'X-Content-Type-Options', value: 'nosniff' }, { key: 'Referrer-Policy', value: 'no-referrer' },
  { key: 'Content-Security-Policy', value: "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'" },
] }]; } };

export default nextConfig;
