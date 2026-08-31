import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "HPC/HTC AI Platform",
  description: "Prompt-driven multi-agent data analysis platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
