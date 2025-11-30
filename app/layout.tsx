import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { cn } from "@/lib/utils";

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
      <body className={cn(inter.className, "min-h-screen bg-background font-sans antialiased")}>
        {children}
      </body>
    </html>
  );
}
