"use client";
import { useEffect, useState, useRef } from "react";
import { motion, useInView, AnimatePresence } from "framer-motion";
import { api, Movie } from "@/lib/api";
import { MovieCard, MovieCardSkeleton } from "@/components/MovieCard";
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip,
         ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { Film, Star, Zap, Globe, TrendingUp, Award, Code2, UserRound, Mail } from "lucide-react";

// ── Counter animation hook ─────────────────────────────────────────────────
function useCountUp(target: number, duration = 1500) {
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (!target) return;
    let start = 0;
    const step = Math.ceil(target / (duration / 16));
    const timer = setInterval(() => {
      start = Math.min(start + step, target);
      setCount(start);
      if (start >= target) clearInterval(timer);
    }, 16);
    return () => clearInterval(timer);
  }, [target, duration]);
  return count;
}

// ── Animated stat card ─────────────────────────────────────────────────────
function StatCard({
  icon: Icon, label, rawValue, displayValue, delay,
}: {
  icon: any; label: string; rawValue: number; displayValue: string; delay: number;
}) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 20 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ delay, duration: 0.4, ease: "easeOut" }}
      whileHover={{ scale: 1.04, transition: { duration: 0.15 } }}
      className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-center cursor-default"
    >
      <Icon size={18} className="text-red-500 mx-auto mb-1" />
      <p className="text-lg font-bold text-white">{displayValue}</p>
      <p className="text-zinc-500 text-[11px] mt-0.5">{label}</p>
    </motion.div>
  );
}

const MOODS = [
  { id: "action",   label: "💥 Action" },
  { id: "comedy",   label: "😂 Comedy" },
  { id: "drama",    label: "😢 Drama" },
  { id: "scifi",    label: "🚀 Sci-Fi" },
  { id: "thriller", label: "😰 Thriller" },
  { id: "horror",   label: "👻 Horror" },
  { id: "romance",  label: "💘 Romance" },
  { id: "world",    label: "🌍 World" },
];

const PIE_COLORS = ["#ef4444","#f97316","#eab308","#22c55e","#3b82f6","#8b5cf6"];

export default function Home() {
  const [stats, setStats]         = useState<any>(null);
  const [yearData, setYearData]   = useState<any[]>([]);
  const [genres, setGenres]       = useState<any[]>([]);
  const [voteDist, setVoteDist]   = useState<any[]>([]);
  const [topMovies, setTop]       = useState<Movie[]>([]);
  const [mood, setMood]           = useState("action");
  const [moodMovies, setMoodM]    = useState<Movie[]>([]);
  const [moodLoading, setMoodL]   = useState(false);
  const [loading, setLoading]     = useState(true);

  useEffect(() => {
    Promise.all([
      api.stats(), api.moviesPerYear(), api.genres(12),
      api.voteDist(), api.topPopular(12),
    ]).then(([s, yr, g, vd, top]) => {
      setStats(s); setYearData(yr); setGenres(g); setVoteDist(vd); setTop(top);
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    setMoodL(true);
    api.mood(mood).then(m => { setMoodM(m); setMoodL(false); });
  }, [mood]);

  if (loading) return (
    <div className="py-12">
      <div className="h-40 bg-zinc-900 rounded-2xl animate-pulse mb-8" />
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-4 mb-8">
        {[...Array(6)].map((_, i) => <div key={i} className="h-24 bg-zinc-900 rounded-xl animate-pulse" />)}
      </div>
    </div>
  );

  const statCards = [
    { icon: Film,       label: "Total Movies", displayValue: stats?.total_movies?.toLocaleString(), rawValue: stats?.total_movies },
    { icon: Star,       label: "Avg Vote",     displayValue: `${stats?.avg_vote}/10`,               rawValue: 0 },
    { icon: Zap,        label: "Genres",       displayValue: String(stats?.unique_genres),           rawValue: stats?.unique_genres },
    { icon: Globe,      label: "Languages",    displayValue: String(stats?.languages),               rawValue: stats?.languages },
    { icon: TrendingUp, label: "Peak Year",    displayValue: String(stats?.peak_year),               rawValue: 0 },
    { icon: Award,      label: "Top Genre",    displayValue: stats?.top_genre,                       rawValue: 0 },
  ];

  return (
    <div className="py-8 space-y-10">

      {/* ── Hero ── */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="relative rounded-2xl overflow-hidden bg-gradient-to-br
                   from-zinc-900 via-zinc-800 to-zinc-900 border border-zinc-700 p-10 premium-card"
      >
        <motion.h1
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.15, duration: 0.5 }}
          className="  text-4xl md:text-5xl font-bold text-white mb-3"
        >
          🎬 CineScope
        </motion.h1>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.5 }}
          className="text-zinc-400 text-lg mb-2"
        >
          Movie Intelligence Platform
        </motion.p>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.45, duration: 0.5 }}
          className="text-zinc-500 text-sm"
        >
          {stats?.total_movies?.toLocaleString()} movies · AI recommendations · Deep analytics
        </motion.p>
      </motion.div>

      {/* ── Stat cards ── */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 ">
        {statCards.map(({ icon, label, displayValue, rawValue }, i) => (
          <StatCard
            key={label}
            icon={icon}
            label={label}
            displayValue={displayValue}
            rawValue={rawValue}
            delay={i * 0.07}
          />
        ))}
      </div>

      {/* ── Charts ── */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="grid md:grid-cols-3 gap-6"
        >
        <div className="md:col-span-2 bg-zinc-900 border border-zinc-800 rounded-xl p-5 premium-card">
          <h2 className="text-white font-semibold mb-4">Movies per Year</h2>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={yearData}>
              <defs>
                <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#ef4444" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="Year" tick={{ fill: "#71717a", fontSize: 11 }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fill: "#71717a", fontSize: 11 }} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", borderRadius: 8, color: "#fff" }} />
              <Area type="monotone" dataKey="count" stroke="#ef4444" fill="url(#grad)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 premium-card">
          <h2 className="text-white font-semibold mb-4">Vote Distribution</h2>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={voteDist} dataKey="count" nameKey="category"
                   cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={3}>
                {voteDist.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
              </Pie>
              <Tooltip contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", borderRadius: 8, color: "#fff" }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </motion.div>

      {/* ── Top popular poster wall ── */}
      <div>
        <motion.h2
          initial={{ opacity: 0, x: -10 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4 }}
          className="text-white font-bold text-xl mb-4"
        >
          🔥 Most Popular Right Now
        </motion.h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
          {topMovies.map((m, i) => <MovieCard key={m.Title} movie={m} index={i} />)}
        </div>
      </div>

      {/* ── Mood picker ── */}
      <div>
        <motion.h2
          initial={{ opacity: 0, x: -10 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4 }}
          className="text-white font-bold text-xl mb-4"
        >
          🎭 What's your mood?
        </motion.h2>

        <div className="flex flex-wrap gap-2 mb-5">
          {MOODS.map((m) => (
            <motion.button
              key={m.id}
              onClick={() => setMood(m.id)}
              whileHover={{ scale: 1.06 }}
              whileTap={{ scale: 0.95 }}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors
                ${mood === m.id
                  ? "bg-red-600 text-white"
                  : "bg-zinc-800 text-zinc-300 hover:bg-zinc-700"}`}
            >
              {m.label}
            </motion.button>
          ))}
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={mood}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -16 }}
            transition={{ duration: 0.3 }}
            className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3"
          >
            {moodLoading
              ? [...Array(6)].map((_, i) => <MovieCardSkeleton key={i} index={i} />)
              : moodMovies.map((m, i) => <MovieCard key={m.Title} movie={m} index={i} />)
            }
          </motion.div>
        </AnimatePresence>
      </div>
    {/* Footer */}
      <footer className="border-t border-zinc-800 pt-6 mt-10">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">

          {/* Left Side */}
          <div>
            <p className="text-zinc-400 text-sm">
              Made with ❤️ by{" "}
              <span className="text-white font-semibold">
                Saket Chaudhary
              </span>
            </p>

            <p className="text-zinc-500 text-xs mt-1">
              CineScope • Movie Intelligence Platform
            </p>
          </div>

          {/* Right Side */}
          <div className="flex items-center gap-4 text-zinc-400">

            <a
              href="https://github.com/Saket22-CS"
              target="_blank"
              className="hover:text-white transition-colors"
            >
              <Code2 size={20} />
            </a>

            <a
              href="https://www.linkedin.com/in/saket-chaudhary22/"
              target="_blank"
              className="hover:text-white transition-colors"
            >
              <UserRound size={20} />
            </a>

            <a
              href="mailto:saketrishu64821@gmail.com"
              className="hover:text-white transition-colors"
            >
              <Mail size={20} />
            </a>

          </div>
        </div>
      </footer>
    </div>
  );
}