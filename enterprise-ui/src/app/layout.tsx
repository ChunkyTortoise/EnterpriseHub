import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "@/lib/providers";
import { ClaudeConcierge } from "@/components/claude-concierge/ClaudeConcierge";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
  display: "swap",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Jorge's Real Estate AI Platform | EnterpriseHub",
  description: "Professional AI-powered real estate command center with enterprise-grade bot ecosystem, confrontational seller qualification, and intelligent property matching.",
  keywords: [
    "real estate AI",
    "property management",
    "lead qualification",
    "Jorge bots",
    "enterprise platform",
    "seller bot",
    "buyer leads",
    "property scanner",
    "real estate automation"
  ],
  authors: [{ name: "Jorge's Real Estate AI" }],
  creator: "Jorge's Real Estate AI Platform",
  publisher: "EnterpriseHub",
  category: "business",
  classification: "Real Estate Technology",
  robots: {
    index: false, // Private enterprise platform
    follow: false,
  },
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "Jorge AI",
    startupImage: [
      {
        url: "/splash/iphone5_splash.png",
        media: "(device-width: 320px) and (device-height: 568px) and (-webkit-device-pixel-ratio: 2)",
      },
      {
        url: "/splash/iphone6_splash.png",
        media: "(device-width: 375px) and (device-height: 667px) and (-webkit-device-pixel-ratio: 2)",
      },
      {
        url: "/splash/iphoneplus_splash.png",
        media: "(device-width: 621px) and (device-height: 1104px) and (-webkit-device-pixel-ratio: 3)",
      },
      {
        url: "/splash/iphonex_splash.png",
        media: "(device-width: 375px) and (device-height: 812px) and (-webkit-device-pixel-ratio: 3)",
      },
    ],
  },
  openGraph: {
    type: "website",
    siteName: "Jorge's Real Estate AI Platform",
    title: "Jorge's Real Estate AI Platform",
    description: "Professional AI-powered real estate command center with enterprise bot ecosystem",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Jorge's Real Estate AI Platform",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Jorge's Real Estate AI Platform",
    description: "Professional AI-powered real estate command center",
    images: ["/og-image.png"],
  },
  other: {
    "apple-mobile-web-app-capable": "yes",
    "apple-mobile-web-app-status-bar-style": "black-translucent",
    "apple-touch-fullscreen": "yes",
    "mobile-web-app-capable": "yes",
    "msapplication-TileColor": "#0052FF",
    "msapplication-config": "/browserconfig.xml",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#0052FF" },
    { media: "(prefers-color-scheme: dark)", color: "#0052FF" },
  ],
  colorScheme: "dark only",
  viewportFit: "cover",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full dark">
      <head>
        {/* Preconnect for performance */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />

        {/* PWA Icons */}
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <link rel="icon" href="/icon.svg" type="image/svg+xml" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />

        {/* PWA Meta Tags */}
        <meta name="application-name" content="Jorge AI" />
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <meta name="apple-mobile-web-app-title" content="Jorge AI" />
        <meta name="format-detection" content="telephone=no" />
        <meta name="msapplication-tap-highlight" content="no" />

        {/* Performance Hints */}
        <link rel="dns-prefetch" href="//api.openai.com" />
        <link rel="dns-prefetch" href="//api.anthropic.com" />

        {/* Jorge Brand Theme */}
        <meta name="theme-color" content="#0052FF" />
        <meta name="msapplication-navbutton-color" content="#0052FF" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased h-full bg-jorge-dark text-foreground overflow-x-hidden`}
      >
        <Providers>
          <div className="min-h-screen bg-jorge-gradient-dark">
            {children}
            <ClaudeConcierge />
          </div>
        </Providers>
      </body>
    </html>
  );
}
