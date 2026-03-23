import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Jazzy | Discover Jazz Albums",
  description: "Subscribe to receive periodic jazz album recommendations via email",
};

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
        <footer className="py-4 text-center text-xs text-gray-400 space-x-3">
          <Link href="/privacy" className="hover:underline">Privacy Policy</Link>
          <span>&middot;</span>
          <Link href="/imprint" className="hover:underline">Imprint</Link>
        </footer>
      </body>
    </html>
  );
}
