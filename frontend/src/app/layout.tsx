import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { AuthProvider } from "@/lib/auth-context";
import ErrorBoundary from "@/components/ErrorBoundary";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "Director AI — AI Filmmaking Assistant",
  description:
    "Your AI cinematography partner. Analyze scenes, plan shots, and get professional lighting & camera recommendations powered by artificial intelligence.",
  keywords: ["filmmaking", "AI", "cinematography", "scene analysis", "director", "camera"],
  authors: [{ name: "Director AI" }],
  openGraph: {
    title: "Director AI — AI Filmmaking Assistant",
    description: "Your AI cinematography partner for professional filmmaking.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={inter.variable}>
      <body>
        <ErrorBoundary>
          <AuthProvider>{children}</AuthProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
