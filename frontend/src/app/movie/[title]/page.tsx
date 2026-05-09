"use client";

import { useEffect, useState, use } from "react";
import { api, Movie } from "@/lib/api";
import { MovieCard } from "@/components/MovieCard";
import {
  Star,
  Flame,
  Calendar,
  Globe,
  Hash,
  Layers,
  ChevronLeft,
} from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";


export default function MoviePage({
  params,
}: {
  params: Promise<{ title: string }>;
}) {

  // ✅ unwrap params promise
  const { title } = use(params);

  const decodedTitle = decodeURIComponent(title);

  const [movie, setMovie] = useState<Movie | null>(null);
  const [recs, setRecs] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);

    Promise.all([
      api.movie(decodedTitle),
      api.recommend(decodedTitle, 8),
    ])
      .then(([m, r]) => {
        setMovie(m);
        setRecs(r);
      })
      .finally(() => setLoading(false));
  }, [decodedTitle]);

  if (loading)
    return (
      <div className="py-10 space-y-4 animate-pulse">
        <div className="h-8 bg-zinc-800 rounded w-1/3" />
        <div className="h-80 bg-zinc-800 rounded-2xl" />
      </div>
    );

  if (!movie)
    return (
      <div className="py-10 text-zinc-400">
        Movie not found.
      </div>
    );

  const poster = movie.Poster_Url?.startsWith("http")
    ? movie.Poster_Url
    : null;


  return (
    <div className="py-8 space-y-10">
      <motion.div
        initial={{ opacity: 0, x: -10 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.3 }}
      >
        <Link href="/search"
          className="inline-flex items-center gap-1 text-zinc-400 hover:text-white text-sm transition-colors">
          <ChevronLeft size={15} /> Back to search
        </Link>
      </motion.div>

      {/* Main card */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden"
      >
        <div className="md:flex gap-0">

          {/* Poster — slides in from left */}
          <motion.div
            className="md:w-64 flex-shrink-0"
            initial={{ opacity: 0, x: -40 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.55, ease: "easeOut" }}
          >
            {poster
              ? <img src={poster} alt={movie.Title}
                    className="w-full h-full object-cover max-h-96 md:max-h-none" />
              : <div className="w-full h-64 md:h-full bg-zinc-800 flex items-center justify-center text-zinc-600">
                  No poster
                </div>
            }
          </motion.div>

          {/* Details — stagger children in */}
          <motion.div
            className="flex-1 p-6 space-y-4"
            initial="hidden"
            animate="visible"
            variants={{ visible: { transition: { staggerChildren: 0.08 } } }}
          >
            {/* Each child fades up */}
            {[
              // Title + year
              <div key="title">
                <h1 className="text-3xl font-bold text-white">{movie.Title}</h1>
                <p className="text-zinc-400 text-sm mt-1">{movie.Era} era · {movie.Decade}s</p>
              </div>,

              // Genre badges
              <div key="badges" className="flex flex-wrap gap-2">
                {movie.Genre?.split(", ").map(g => (
                  <motion.span key={g} whileHover={{ scale: 1.08 }}
                    className="px-3 py-1 bg-zinc-800 text-zinc-300 rounded-full text-xs border border-zinc-700">
                    {g}
                  </motion.span>
                ))}
                <span className="px-3 py-1 bg-red-900/40 text-red-400 rounded-full text-xs border border-red-800">{movie.Pop_Tier}</span>
                <span className="px-3 py-1 bg-green-900/40 text-green-400 rounded-full text-xs border border-green-800">{movie.Vote_Bucket}</span>
              </div>,

              // Stat grid
              <div key="stats" className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {[
                  { icon: Star,     label: "Vote Avg",   value: `${movie.Vote_Average?.toFixed(1)}/10`, color: "text-yellow-400" },
                  { icon: Hash,     label: "Votes",      value: movie.Vote_Count?.toLocaleString(),      color: "text-blue-400" },
                  { icon: Flame,    label: "Popularity", value: movie.Popularity?.toFixed(1),            color: "text-orange-400" },
                  { icon: Calendar, label: "Year",       value: movie.Year ?? "—",                       color: "text-zinc-400" },
                ].map(({ icon: Icon, label, value, color }) => (
                  <motion.div key={label} whileHover={{ scale: 1.05 }}
                    className="bg-zinc-800 rounded-xl p-3 text-center">
                    <Icon size={16} className={`${color} mx-auto mb-1`} />
                    <p className="text-white font-bold text-sm">{value}</p>
                    <p className="text-zinc-500 text-[11px]">{label}</p>
                  </motion.div>
                ))}
              </div>,

              // Vote bar
              <div key="votebar">
                <div className="flex justify-between text-xs text-zinc-500 mb-1">
                  <span>Vote Average</span><span>{movie.Vote_Average?.toFixed(1)}/10</span>
                </div>
                <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-red-600 to-yellow-500 rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${(movie.Vote_Average / 10) * 100}%` }}
                    transition={{ duration: 0.9, ease: "easeOut", delay: 0.4 }}
                  />
                </div>
              </div>,

              // Meta
              <div key="meta" className="flex flex-wrap gap-4 text-sm text-zinc-400">
                <span className="flex items-center gap-1.5"><Globe size={13} /> {movie.Original_Language}</span>
                <span className="flex items-center gap-1.5"><Layers size={13} /> {movie.Overview_WC} words in overview</span>
              </div>,

              // Overview
              <div key="overview">
                <p className="text-zinc-500 text-xs font-medium uppercase tracking-wider mb-2">Overview</p>
                <p className="text-zinc-300 text-sm leading-relaxed">{movie.Overview}</p>
              </div>,

            ].map((child, i) => (
              <motion.div
                key={i}
                variants={{
                  hidden:   { opacity: 0, y: 12 },
                  visible:  { opacity: 1, y: 0, transition: { duration: 0.35, ease: "easeOut" } },
                }}
              >
                {child}
              </motion.div>
            ))}
          </motion.div>
        </div>
      </motion.div>

      {/* Recommendations */}
      {recs.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-60px" }}
          transition={{ duration: 0.45 }}
        >
          <h2 className="gradient-text font-bold text-xl mb-4">Similar Movies</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-8 gap-3">
            {recs.map((m, i) => <MovieCard key={m.Title} movie={m} size="sm" index={i} />)}
          </div>
        </motion.div>
      )}
    </div>
  );
}