import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "GroundedAI — Ground your LLM. Trust your answers.",
  description: "Production-Grade RAG System. Upload documents, ask questions, get grounded answers with citations. Zero hallucinations.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
