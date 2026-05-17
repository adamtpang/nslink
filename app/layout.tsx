import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { cn } from "@/lib/utils";
import { PostHogProvider } from "./providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "NS_LINK | Router Ingestion",
  description: "Automated Router Scanning & Configuration System",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={cn(inter.className, "min-h-screen bg-background font-sans antialiased flex flex-col")}>
        <PostHogProvider>{children}</PostHogProvider>
        <footer style={{padding: '1.5rem 1rem', textAlign: 'center', fontSize: '0.75rem', opacity: 0.6, marginTop: 'auto'}}>
          Built by <a href="https://adampang.com" style={{textDecoration: 'underline'}}>Adam Pangelinan</a>
          {' · '}<a href="https://anchormarianas.com" style={{textDecoration: 'underline'}}>Anchor Marianas LLC</a>
          {' · '}<a href="https://sellsniper.com" style={{textDecoration: 'underline'}}>More projects</a>
        </footer>
      </body>
    </html>
  );
}
