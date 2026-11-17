import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Recovra",
  description: "Receivables and collections copilot for Pakistani SMEs",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}