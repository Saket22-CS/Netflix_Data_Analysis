"use client";
import { motion } from "framer-motion";
import { Movie } from "@/lib/api";
import { Star, Flame, Calendar } from "lucide-react";
import Link from "next/link";

// ── Reusable variants ──────────────────────────────────────────────────────
export const cardVariants = {
  hidden:  { opacity: 0, y: 24 },
  visible: (i: number) => ({
    opacity: 1, y: 0,
    transition: { delay: i * 0.05, duration: 0.35, ease: "easeOut" },
  }),
};

export function MovieCard({
  movie, size = "md", index = 0,
}: {
  movie: Movie; size?: "sm" | "md" | "lg"; index?: number;
}) {
  const poster = movie.Poster_Url?.startsWith("http") ? movie.Poster_Url : null;
  const isLg   = size === "lg";

  return (
    <motion.div
      custom={index}
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      whileHover={{ y: -6, transition: { duration: 0.2 } }}
    >
      <Link
        href={`/movie/${encodeURIComponent(movie.Title)}`}
        className="group block rounded-xl overflow-hidden border border-white/5
           glass hover:border-red-500/30 transition-all duration-300
           hover:shadow-2xl hover:shadow-red-500/10 spotlight"
      >
        <div className={`relative overflow-hidden ${isLg ? "h-72" : "h-52"} bg-zinc-800`}>
          {poster ? (
            <motion.img
              src={poster}
              alt={movie.Title}
              className="w-full h-full object-cover"
              whileHover={{ scale: 1.07 }}
              transition={{ duration: 0.4 }}
              onError={(e) => {
                (e.target as HTMLImageElement).src = "/placeholder.png";
              }}
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-zinc-600 text-sm">
              No poster
            </div>
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
          <div className="absolute bottom-2 left-2 flex gap-1 flex-wrap">
            {movie.Genre?.split(", ").slice(0, 2).map((g) => (
              <span
                key={g}
                className="px-2 py-0.5 bg-black/60 text-white text-[10px] rounded-full
                           backdrop-blur-sm border border-white/10"
              >
                {g}
              </span>
            ))}
          </div>
        </div>
        <div className="p-3">
          <p className="font-semibold text-white text-sm leading-tight line-clamp-2 mb-2">
            {movie.Title}
          </p>
          <div className="flex items-center justify-between text-xs text-zinc-400">
            <span className="flex items-center gap-1">
              <Star size={11} className="text-yellow-400 fill-yellow-400" />
              {movie.Vote_Average?.toFixed(1)}
            </span>
            <span className="flex items-center gap-1">
              <Flame size={11} className="text-orange-400" />
              {movie.Popularity?.toFixed(0)}
            </span>
            <span className="flex items-center gap-1">
              <Calendar size={11} />
              {movie.Year ?? "—"}
            </span>
          </div>
        </div>
      </Link>
    </motion.div>
  );
}

export function MovieCardSkeleton({ index = 0 }: { index?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: index * 0.04, duration: 0.3 }}
      className="bg-zinc-900 rounded-xl overflow-hidden border border-zinc-800 animate-pulse"
    >
      <div className="h-52 bg-zinc-800" />
      <div className="p-3 space-y-2">
        <div className="h-3 bg-zinc-700 rounded w-3/4" />
        <div className="h-3 bg-zinc-700 rounded w-1/2" />
      </div>
    </motion.div>
  );
}