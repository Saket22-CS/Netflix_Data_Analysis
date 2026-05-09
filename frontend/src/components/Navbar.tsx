"use client";
import { motion } from "framer-motion";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Film,
  Search,
  Compass,
  BarChart2,
  GitCompare,
  Home,
  Tv,
} from "lucide-react";

const links = [
  { href: "/", label: "Home", icon: Home },
  { href: "/explore", label: "Explore", icon: Tv },
  { href: "/search", label: "Search", icon: Search }, // ← ADD THIS
  { href: "/discover", label: "Discover", icon: Compass },
  { href: "/analytics", label: "Analytics", icon: BarChart2 },
  { href: "/compare", label: "Compare", icon: GitCompare },
];

export function Navbar() {
  const path = usePathname();

  return (
    <motion.nav
      initial={{ y: -56, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="fixed top-0 left-0 right-0 z-50 bg-black/80 backdrop-blur-md border-b border-zinc-800"
    >
      <div className="max-w-7xl mx-auto px-3 sm:px-4 h-14 flex items-center justify-between gap-3">
        {/* Logo */}
        <Link
          href="/"
          className="flex items-center gap-2 font-bold gradient-text text-base sm:text-lg shrink-0"
        >
          <motion.div
            whileHover={{ rotate: 15, scale: 1.15 }}
            transition={{ type: "spring", stiffness: 300 }}
          >
            <Film size={20} className="text-red-500" />
          </motion.div>

          <span className="hidden sm:block">CineScope</span>
        </Link>

        {/* Nav Links */}
        <div className="flex items-center gap-1 overflow-x-auto scrollbar-hide">
          {links.map(({ href, label, icon: Icon }) => {
            const active = path === href;

            return (
              <Link
                key={href}
                href={href}
                className="relative shrink-0 px-2.5 sm:px-3 py-2 rounded-lg text-sm transition-colors"
              >
                {active && (
                  <motion.span
                    layoutId="nav-pill"
                    className="absolute inset-0 bg-zinc-800 rounded-lg"
                    transition={{
                      type: "spring",
                      stiffness: 380,
                      damping: 30,
                    }}
                  />
                )}

                <span
                  className={`relative flex items-center gap-1.5 ${
                    active ? "text-white" : "text-zinc-400 hover:text-white"
                  }`}
                >
                  <Icon size={16} />

                  {/* Hide text on mobile */}
                  <span className="hidden sm:block">{label}</span>
                </span>
              </Link>
            );
          })}
        </div>
      </div>
    </motion.nav>
  );
}
