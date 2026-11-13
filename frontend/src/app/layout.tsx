import type { Metadata } from "next";
import { connection } from "next/server";
import { SessionProvider } from "@/components/session";
import { GovernanceApp } from "@/components/governance-app";
import "./globals.css";
export const metadata: Metadata = {
  title: "Unified AI Governance & Security",
  description:
    "Independent governance, evidence and security workspaces for AI systems.",
};
export default async function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  await connection();
  return (
    <html lang="en">
      <body>
        <SessionProvider>
          <GovernanceApp />
          {children}
        </SessionProvider>
      </body>
    </html>
  );
}
