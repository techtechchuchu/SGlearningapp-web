import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SG고등관 | 오답노트",
  description: "틀린 문제를 기록하고 복습하는 SG고등관 오답노트 학생용 웹 체험.",
  other: {
    "codex-preview": "development",
  },
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body className="antialiased">{children}</body>
    </html>
  );
}
