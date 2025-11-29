import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "EchoSphere",
  description: "Real-time AI voice interaction platform",
};

interface RootLayoutProps {
  children: ReactNode;
}

export default function RootLayout({ children }: RootLayoutProps): ReactNode {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
