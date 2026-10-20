import "./globals.css";
import Link from "next/link";
import { IBM_Plex_Sans, IBM_Plex_Mono } from "next/font/google";

const sans = IBM_Plex_Sans({ subsets: ["latin"], weight: ["400", "600"], variable: "--font" });
const mono = IBM_Plex_Mono({ subsets: ["latin"], weight: ["400"], variable: "--mono" });

export const metadata = { title: "AgentBench Studio", description: "Author, run, verify and compare AI agent tasks" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${sans.variable} ${mono.variable}`}>
      <body>
        <nav><b>AgentBench Studio</b><Link href="/">Tasks</Link><Link href="/benchmarks">Benchmarks</Link></nav>
        <main>{children}</main>
      </body>
    </html>
  );
}
