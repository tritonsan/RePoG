import type { Metadata } from 'next';
import { Geist, Geist_Mono } from 'next/font/google';
import { headers } from 'next/headers';
import './globals.css';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

export async function generateMetadata(): Promise<Metadata> {
  const requestHeaders = await headers();
  const host = requestHeaders.get('x-forwarded-host') || requestHeaders.get('host') || 'localhost:3000';
  const protocol = requestHeaders.get('x-forwarded-proto') || (host.startsWith('localhost') ? 'http' : 'https');
  return {
    metadataBase: new URL(`${protocol}://${host}`),
    title: 'RePoG Living Table',
    description: 'A WebMCP-native narrative table where humans and browser agents play from bounded character perspectives.',
    openGraph: {
      title: 'RePoG Living Table',
      description: 'Humans and browser agents. One bounded world.',
      images: [{ url: '/og.png', width: 1792, height: 1024, alt: 'A luminous living campaign table linking human and agent seats.' }],
    },
    twitter: {
      card: 'summary_large_image',
      title: 'RePoG Living Table',
      description: 'Humans and browser agents. One bounded world.',
      images: ['/og.png'],
    },
  };
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
