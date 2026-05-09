import type { Metadata } from "next";
import { Inter, Geist } from "next/font/google";
import "./globals.css";
import { Navbar } from "@/components/Navbar";
import { cn } from "@/lib/utils";


const geist = Geist({subsets:['latin'],variable:'--font-sans'});

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "CineScope — Movie Intelligence Platform",
  description: "Advanced movie analytics, AI recommendations, and poster discovery.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={cn("dark", "font-sans", geist.variable)}>
      <body className={`${inter.className} bg-black text-white min-h-screen`}>
        <Navbar />
        <main className="pt-14 max-w-7xl mx-auto px-4">
          {children}
          </main>
      </body>
    </html>
  );
}