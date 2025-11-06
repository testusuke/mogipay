import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "MogiPay - レジ/売上管理システム",
  description: "学園祭模擬店向けレジ/売上管理WebApp",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <nav className="border-b">
          <div className="container mx-auto px-4">
            <div className="flex h-16 items-center space-x-8">
              <Link href="/" className="text-xl font-bold">
                MogiPay
              </Link>
              <div className="flex space-x-4">
                <Link
                  href="/pos"
                  className="text-sm font-medium transition-colors hover:text-primary"
                >
                  レジ
                </Link>
                <Link
                  href="/products"
                  className="text-sm font-medium transition-colors hover:text-primary"
                >
                  商品管理
                </Link>
                <Link
                  href="/dashboard"
                  className="text-sm font-medium transition-colors hover:text-primary"
                >
                  ダッシュボード
                </Link>
              </div>
            </div>
          </div>
        </nav>
        <main>{children}</main>
      </body>
    </html>
  );
}
