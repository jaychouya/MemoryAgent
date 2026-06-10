import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ 
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "MemoryAgent - 带记忆的通用助手",
  description: "认知记忆架构的个人 AI 助手，支持项目协作、偏好记忆与资料检索，越用越懂你",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" className="h-full">
      <body className={`${inter.variable} font-sans antialiased h-full overflow-hidden`}>
        {children}
      </body>
    </html>
  );
}
