"use client";
import { motion } from "framer-motion";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Film, Search, Compass, BarChart2, GitCompare, Home, Tv } from "lucide-react";

const links = [
  { href: "/",         label: "Home",     icon: Home },
  { href: "/explore",  label: "Explore",  icon: Tv },  
  { href: "/search",   label: "Search",   icon: Search },     // ← ADD THIS
  { href: "/discover", label: "Discover", icon: Compass },
  { href: "/analytics",label: "Analytics",icon: BarChart2 },
  { href: "/compare",  label: "Compare",  icon: GitCompare },
];

export function Navbar() {
  const path = usePathname();

  return (
    <motion.nav
      initial={{ y: -56, opacity: 0 }}
      animate={{ y: 0,   opacity: 1 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="fixed top-0 left-0 right-0 z-50 bg-black/80 backdrop-blur-md border-b border-zinc-800"
    >
      <div className="max-w-7xl mx-auto px-4 flex items-center justify-between h-14">
        <Link href="/" className="flex items-center gap-2 font-bold gradient-text text-lg">
          <motion.div
            whileHover={{ rotate: 15, scale: 1.15 }}
            transition={{ type: "spring", stiffness: 300 }}
          >
            <Film size={22} className="text-red-500" />
          </motion.div>
          CineScope
        </Link>

        <div className="flex items-center gap-1">
          {links.map(({ href, label, icon: Icon }) => {
            const active = path === href;
            return (
              <Link key={href} href={href} className="relative px-3 py-1.5 rounded-lg text-sm transition-colors">
                {active && (
                  <motion.span
                    layoutId="nav-pill"
                    className="absolute inset-0 bg-zinc-800 rounded-lg"
                    transition={{ type: "spring", stiffness: 380, damping: 30 }}
                  />
                )}
                <span className={`relative flex items-center gap-1.5 ${active ? "text-white" : "text-zinc-400 hover:text-white"}`}>
                  <Icon size={15} />
                  {label}
                </span>
              </Link>
            );
          })}
        </div>
      </div>
    </motion.nav>
  );
}