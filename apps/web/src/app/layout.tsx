import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CultureShift bilateral fixture lab",
  description: "Static bilateral fixture previews for accountable human review.",
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
