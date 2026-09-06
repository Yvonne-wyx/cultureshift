import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CultureShift — Cross-Cultural Creative Reasoning",
  description: "A constrained, human-in-the-loop workflow for adapting AI-product advertising between China and the UK.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
