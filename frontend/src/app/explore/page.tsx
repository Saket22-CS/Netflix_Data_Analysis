"use client";
import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { tmdb, TMDBMovie, TMDBShow } from "@/lib/tmdb";
import {
  Search, TrendingUp, Tv, Film, Star, Calendar,
  Clock, Play, ChevronRight, Globe, Users, Award,
  Flame, X, ChevronLeft,
} from "lucide-react";
import Link from "next/link";

// ── Mini poster card ───────────────────────────────────────────────────────
function TMDBCard({
  item, type, index, onClick,
}: {
  item: any; type: "movie"|"tv"|"person"; index: number; onClick: () => void;
}) {
  const title    = item.title ?? item.name ?? "Unknown";
  const date     = item.release_date ?? item.first_air_date ?? "";
  const year     = date ? new Date(date).getFullYear() : null;
  const posterUrl = tmdb.poster(item.poster_path ?? item.profile_path, "w342");

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04, duration: 0.3 }}
      whileHover={{ y: -8, scale: 1.02 }}
      onClick={onClick}
      className="cursor-pointer group spotlight rounded-xl overflow-hidden glass
                 border border-white/5 hover:border-red-500/40 transition-colors duration-300"
    >
      <div className="poster-wrap aspect-[2/3]">
        {posterUrl
          ? <img src={posterUrl} alt={title}
                 className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110" />
          : <div className="w-full h-full bg-zinc-900 flex items-center justify-center">
              <Film size={32} className="text-zinc-700" />
            </div>
        }
        <div className="overlay">
          <div className="absolute inset-0 flex flex-col justify-end p-3">
            <p className="text-white font-semibold text-xs leading-tight line-clamp-2">{title}</p>
            <div className="flex items-center gap-2 mt-1">
              {item.vote_average > 0 && (
                <span className="flex items-center gap-0.5 text-yellow-400 text-[10px]">
                  <Star size={9} className="fill-yellow-400" />{item.vote_average?.toFixed(1)}
                </span>
              )}
              {year && <span className="text-zinc-400 text-[10px]">{year}</span>}
            </div>
          </div>
        </div>
        {/* Type badge */}
        <div className="absolute top-2 left-2">
          <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase
            ${type==="movie" ? "bg-red-600/80 text-white" :
              type==="tv"    ? "bg-blue-600/80 text-white" :
                               "bg-purple-600/80 text-white"}`}>
            {type === "tv" ? "TV" : type}
          </span>
        </div>
      </div>
      <div className="p-2">
        <p className="text-white text-xs font-medium truncate">{title}</p>
        <p className="text-zinc-500 text-[10px]">{year ?? "—"}</p>
      </div>
    </motion.div>
  );
}

// ── Horizontal scroll row ──────────────────────────────────────────────────
function ScrollRow({
  title, items, type, onSelect, icon: Icon, accentColor = "red",
}: {
  title: string; items: any[]; type: "movie"|"tv";
  onSelect: (item: any, type: "movie"|"tv") => void;
  icon: any; accentColor?: string;
}) {
  const rowRef = useRef<HTMLDivElement>(null);
  const scroll = (dir: "left"|"right") => {
    if (!rowRef.current) return;
    rowRef.current.scrollBy({ left: dir === "left" ? -600 : 600, behavior: "smooth" });
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon size={18} className={`text-${accentColor}-500`} />
          <h2 className="text-white font-semibold text-lg">{title}</h2>
        </div>
        <div className="flex gap-2">
          <button onClick={() => scroll("left")}
            className="p-1.5 rounded-lg glass border border-white/10 hover:border-white/20
                       text-zinc-400 hover:text-white transition-colors">
            <ChevronLeft size={15} />
          </button>
          <button onClick={() => scroll("right")}
            className="p-1.5 rounded-lg glass border border-white/10 hover:border-white/20
                       text-zinc-400 hover:text-white transition-colors">
            <ChevronRight size={15} />
          </button>
        </div>
      </div>
      <div ref={rowRef} className="flex gap-3 overflow-x-auto pb-2 scrollbar-hide"
           style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}>
        {items.map((item, i) => (
          <div key={item.id} style={{ minWidth: 130 }}>
            <TMDBCard item={item} type={type} index={i}
                      onClick={() => onSelect(item, type)} />
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Detail modal ───────────────────────────────────────────────────────────
function DetailModal({ item, type, onClose }: {
  item: any; type: "movie"|"tv"; onClose: () => void;
}) {
  const [detail, setDetail] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const fn = type === "movie" ? tmdb.movieDetail : tmdb.tvDetail;
    fn(item.id).then(d => { setDetail(d); setLoading(false); });
  }, [item.id, type]);

  const backdropUrl = tmdb.backdrop(item.backdrop_path ?? detail?.backdrop_path, "w1280");
  const posterUrl   = tmdb.poster(item.poster_path, "w500");
  const title       = item.title ?? item.name;
  const date        = item.release_date ?? item.first_air_date;
  const year        = date ? new Date(date).getFullYear() : null;

  // Get YouTube trailer
  const trailer = detail?.videos?.results?.find(
    (v: any) => v.type === "Trailer" && v.site === "YouTube"
  );

  // Watch providers (US)
  const providers = detail?.["watch/providers"]?.results?.US;
  const flatrate   = providers?.flatrate ?? [];
  const rent       = providers?.rent ?? [];

  // Cast
  const cast = detail?.credits?.cast?.slice(0, 10) ?? [];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[100] flex items-end sm:items-center justify-center p-0 sm:p-4"
      onClick={onClose}
    >
      {/* Backdrop blur */}
      <div className="absolute inset-0 bg-black/85 backdrop-blur-md" />

      <motion.div
        initial={{ y: 80, opacity: 0 }}
        animate={{ y: 0,  opacity: 1 }}
        exit={{    y: 80, opacity: 0 }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        onClick={e => e.stopPropagation()}
        className="relative z-10 w-full max-w-3xl max-h-[92vh] overflow-y-auto
                   rounded-t-2xl sm:rounded-2xl bg-[#0d0d14] border border-white/10"
      >
        {/* Hero backdrop */}
        {backdropUrl && (
          <div className="relative h-52 sm:h-72 overflow-hidden rounded-t-2xl sm:rounded-t-2xl">
            <img src={backdropUrl} alt={title}
                 className="w-full h-full object-cover" />
            <div className="absolute inset-0 bg-gradient-to-t from-[#0d0d14] via-[#0d0d14]/40 to-transparent" />
          </div>
        )}

        {/* Close */}
        <button onClick={onClose}
          className="absolute top-3 right-3 p-1.5 rounded-full bg-black/60 text-white
                     hover:bg-black/80 transition-colors z-20">
          <X size={16} />
        </button>

        <div className="p-5 sm:p-6 -mt-16 relative">
          <div className="flex gap-4">
            {/* Poster */}
            {posterUrl && (
              <div className="flex-shrink-0 w-24 sm:w-32 rounded-xl overflow-hidden
                              border-2 border-white/10 shadow-2xl">
                <img src={posterUrl} alt={title} className="w-full" />
              </div>
            )}
            <div className="flex-1 pt-16">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h2 className="text-xl sm:text-2xl font-bold text-white">{title}</h2>
                  <div className="flex flex-wrap items-center gap-2 mt-1 text-sm text-zinc-400">
                    {year && <span className="flex items-center gap-1"><Calendar size={12}/>{year}</span>}
                    {detail?.runtime && <span className="flex items-center gap-1"><Clock size={12}/>{detail.runtime}m</span>}
                    {detail?.status  && <span className="text-zinc-500">{detail.status}</span>}
                  </div>
                </div>
              </div>

              {/* Rating */}
              <div className="flex items-center gap-3 mt-3">
                <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg
                                bg-yellow-500/10 border border-yellow-500/20">
                  <Star size={14} className="text-yellow-400 fill-yellow-400" />
                  <span className="text-yellow-400 font-bold text-sm">
                    {item.vote_average?.toFixed(1)}
                  </span>
                  <span className="text-zinc-500 text-xs">
                    ({item.vote_count?.toLocaleString()} votes)
                  </span>
                </div>
                {detail?.popularity && (
                  <div className="flex items-center gap-1 text-orange-400 text-sm">
                    <Flame size={13} />
                    {detail.popularity?.toFixed(0)}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Genres */}
          {detail?.genres && (
            <div className="flex flex-wrap gap-1.5 mt-4">
              {detail.genres.map((g: any) => (
                <span key={g.id}
                  className="px-2.5 py-1 rounded-full text-xs border border-white/10
                             text-zinc-300 glass">
                  {g.name}
                </span>
              ))}
            </div>
          )}

          {/* Overview */}
          {(item.overview || detail?.overview) && (
            <p className="text-zinc-300 text-sm leading-relaxed mt-4">
              {item.overview || detail?.overview}
            </p>
          )}

          {/* Trailer button */}
          {trailer && (
            <a href={`https://www.youtube.com/watch?v=${trailer.key}`}
               target="_blank" rel="noopener noreferrer"
               className="inline-flex items-center gap-2 mt-4 px-4 py-2.5 rounded-xl
                          bg-red-600 hover:bg-red-700 text-white text-sm font-medium
                          transition-colors glow-red">
              <Play size={15} className="fill-white" /> Watch Trailer
            </a>
          )}

          {/* Where to Watch */}
          {(flatrate.length > 0 || rent.length > 0) && (
            <div className="mt-5">
              <p className="text-zinc-500 text-xs font-semibold uppercase tracking-wider mb-2">
                Where to Watch
              </p>
              <div className="flex flex-wrap gap-2">
                {[...flatrate, ...rent].slice(0, 6).map((p: any) => (
                  <div key={p.provider_id}
                    className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg glass
                               border border-white/10 text-xs text-zinc-300">
                    {p.logo_path && (
                      <img src={`https://image.tmdb.org/t/p/w45${p.logo_path}`}
                           alt={p.provider_name} className="w-4 h-4 rounded" />
                    )}
                    {p.provider_name}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Cast */}
          {cast.length > 0 && (
            <div className="mt-5">
              <p className="text-zinc-500 text-xs font-semibold uppercase tracking-wider mb-3">
                Cast
              </p>
              <div className="flex gap-3 overflow-x-auto pb-1"
                   style={{ scrollbarWidth: "none" }}>
                {cast.map((person: any) => {
                  const profileUrl = tmdb.profile(person.profile_path);
                  return (
                    <div key={person.id} className="flex-shrink-0 w-16 text-center">
                      <div className="w-16 h-16 rounded-full overflow-hidden bg-zinc-800
                                      border border-white/10 mx-auto mb-1">
                        {profileUrl
                          ? <img src={profileUrl} alt={person.name}
                                 className="w-full h-full object-cover" />
                          : <div className="w-full h-full flex items-center justify-center">
                              <Users size={20} className="text-zinc-600" />
                            </div>
                        }
                      </div>
                      <p className="text-white text-[10px] font-medium leading-tight truncate">
                        {person.name}
                      </p>
                      <p className="text-zinc-600 text-[9px] truncate">{person.character}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {loading && (
            <div className="mt-4 flex items-center gap-2 text-zinc-500 text-sm">
              <div className="w-3 h-3 rounded-full bg-red-500 animate-pulse" />
              Loading details…
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
}

// ── HERO SPOTLIGHT (trending #1) ───────────────────────────────────────────
function HeroSpotlight({ item, type, onClick }: { item: any; type: "movie"|"tv"; onClick: () => void }) {
  const title       = item.title ?? item.name;
  const backdropUrl = tmdb.backdrop(item.backdrop_path, "original");
  const year        = item.release_date ? new Date(item.release_date).getFullYear() : null;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.6 }}
      className="relative rounded-2xl overflow-hidden cursor-pointer group"
      style={{ height: 420 }}
      onClick={onClick}
    >
      {backdropUrl && (
        <motion.img
          src={backdropUrl} alt={title}
          className="absolute inset-0 w-full h-full object-cover"
          whileHover={{ scale: 1.03 }}
          transition={{ duration: 0.6 }}
        />
      )}
      <div className="absolute inset-0 bg-gradient-to-r from-black/95 via-black/50 to-transparent" />
      <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent" />

      {/* Content */}
      <div className="absolute inset-0 flex flex-col justify-end p-8">
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0,  opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.5 }}
        >
          <div className="flex items-center gap-2 mb-3">
            <span className="px-2 py-0.5 rounded-md bg-red-600 text-white text-xs font-bold uppercase">
              {type === "tv" ? "Series" : "Movie"} · Trending
            </span>
            {year && <span className="text-zinc-400 text-sm">{year}</span>}
          </div>

          <h1 className="text-4xl md:text-5xl font-black text-white mb-3 leading-tight max-w-lg">
            {title}
          </h1>

          <div className="flex items-center gap-4 mb-4">
            <div className="flex items-center gap-1.5">
              <Star size={16} className="text-yellow-400 fill-yellow-400" />
              <span className="text-yellow-400 font-bold">{item.vote_average?.toFixed(1)}</span>
              <span className="text-zinc-500 text-sm">/ 10</span>
            </div>
            <div className="flex items-center gap-1.5 text-orange-400 text-sm">
              <Flame size={14} />
              <span>{item.popularity?.toFixed(0)} popularity</span>
            </div>
          </div>

          <p className="text-zinc-300 text-sm leading-relaxed max-w-md line-clamp-2">
            {item.overview}
          </p>

          <motion.button
            whileHover={{ scale: 1.04 }}
            whileTap={{ scale: 0.96 }}
            className="mt-5 inline-flex items-center gap-2 px-5 py-2.5 rounded-xl
                       bg-red-600 hover:bg-red-700 text-white font-medium text-sm
                       transition-colors glow-red"
          >
            <Play size={15} className="fill-white" /> View Details
          </motion.button>
        </motion.div>
      </div>
    </motion.div>
  );
}

// ── MAIN PAGE ──────────────────────────────────────────────────────────────
export default function ExplorePage() {
  const [tab,       setTab]    = useState<"movies"|"tv"|"trending">("trending");
  const [query,     setQuery]  = useState("");
  const [searching, setSearch] = useState(false);
  const [searchRes, setSearchR] = useState<any[]>([]);
  const [selected,  setSelected] = useState<{ item: any; type: "movie"|"tv" } | null>(null);

  // Data buckets
  const [trendingAll,  setTrAll]  = useState<any[]>([]);
  const [trendingM,    setTrM]    = useState<any[]>([]);
  const [trendingTV,   setTrTV]   = useState<any[]>([]);
  const [nowPlaying,   setNowP]   = useState<any[]>([]);
  const [upcoming,     setUpcom]  = useState<any[]>([]);
  const [topRatedM,    setTopM]   = useState<any[]>([]);
  const [popularTV,    setPopTV]  = useState<any[]>([]);
  const [topRatedTV,   setTopTV]  = useState<any[]>([]);
  const [loading,      setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      tmdb.trendingAll("day"),
      tmdb.trendingMovies("week"),
      tmdb.trendingTV("week"),
      tmdb.nowPlaying(),
      tmdb.upcoming(),
      tmdb.topRated(),
      tmdb.popularTV(),
      tmdb.topRatedTV(),
    ]).then(([ta, tm, ttv, np, up, trm, ptv, trtv]) => {
      setTrAll(ta.results  ?? []);
      setTrM(tm.results    ?? []);
      setTrTV(ttv.results  ?? []);
      setNowP(np.results   ?? []);
      setUpcom(up.results  ?? []);
      setTopM(trm.results  ?? []);
      setPopTV(ptv.results ?? []);
      setTopTV(trtv.results ?? []);
      setLoading(false);
    });
  }, []);

  // Live search
  useEffect(() => {
    if (!query.trim()) { setSearchR([]); setSearch(false); return; }
    const t = setTimeout(async () => {
      setSearch(true);
      const res = await tmdb.searchMulti(query);
      setSearchR(res.results?.filter((r:any) => r.media_type !== "person") ?? []);
      setSearch(false);
    }, 400);
    return () => clearTimeout(t);
  }, [query]);

  const hero      = trendingAll[0];
  const heroType  = hero?.media_type === "tv" ? "tv" : "movie";

  const TABS = [
    { id: "trending", label: "🔥 Trending",  },
    { id: "movies",   label: "🎬 Movies",    },
    { id: "tv",       label: "📺 TV Shows",  },
  ];

  return (
    <div className="py-8 space-y-8">

      {/* ── Page header ── */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex flex-col sm:flex-row sm:items-end justify-between gap-4"
      >
        <div>
          <h1 className="text-4xl font-black gradient-text mb-1">Explore</h1>
          <p className="text-zinc-500 text-sm">
            Powered by TMDB · {(trendingAll.length + nowPlaying.length).toLocaleString()}+ titles loaded
          </p>
        </div>

        {/* TMDB badge */}
        <a href="https://www.themoviedb.org" target="_blank" rel="noopener noreferrer"
           className="flex items-center gap-2 px-3 py-1.5 rounded-lg glass border border-white/10
                      text-zinc-400 hover:text-white text-xs transition-colors">
          <div className="w-3 h-3 rounded-full bg-green-400" />
          Data by TMDB
        </a>
      </motion.div>

      {/* ── Search bar ── */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1, duration: 0.4 }}
        className="relative"
      >
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500" size={18} />
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Search any movie, TV show, or series worldwide…"
          className="w-full pl-11 pr-4 py-4 glass-strong border border-white/10
                     rounded-2xl text-white placeholder-zinc-600 focus:outline-none
                     focus:border-red-500/50 text-sm transition-colors"
        />
        {query && (
          <button onClick={() => setQuery("")}
            className="absolute right-4 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-white">
            <X size={16} />
          </button>
        )}
      </motion.div>

      {/* ── Search results ── */}
      <AnimatePresence>
        {query && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-3"
          >
            <p className="text-zinc-500 text-sm">
              {searching ? "Searching…" : `${searchRes.length} results for "${query}"`}
            </p>
            <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-3">
              {searchRes.slice(0, 16).map((item, i) => (
                <TMDBCard
                  key={item.id} item={item}
                  type={item.media_type === "tv" ? "tv" : "movie"}
                  index={i}
                  onClick={() => setSelected({ item, type: item.media_type === "tv" ? "tv" : "movie" })}
                />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {!query && !loading && (<>

        {/* ── Hero spotlight ── */}
        {hero && (
          <HeroSpotlight item={hero} type={heroType}
            onClick={() => setSelected({ item: hero, type: heroType })} />
        )}

        {/* ── Tabs ── */}
        <div className="flex gap-2">
          {TABS.map(t => (
            <motion.button
              key={t.id} onClick={() => setTab(t.id as any)}
              whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.96 }}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all
                ${tab === t.id
                  ? "bg-red-600 text-white glow-red"
                  : "glass border border-white/10 text-zinc-400 hover:text-white"}`}
            >
              {t.label}
            </motion.button>
          ))}
        </div>

        {/* ── Tab content ── */}
        <AnimatePresence mode="wait">
          <motion.div
            key={tab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.25 }}
            className="space-y-10"
          >
            {tab === "trending" && (<>
              <ScrollRow title="Trending Today — All" items={trendingAll}
                type="movie" icon={TrendingUp} accentColor="red"
                onSelect={(item) => setSelected({ item,
                  type: item.media_type === "tv" ? "tv" : "movie" })} />
              <div className="section-divider" />
              <ScrollRow title="Trending Movies This Week" items={trendingM}
                type="movie" icon={Film} accentColor="orange"
                onSelect={(item) => setSelected({ item, type: "movie" })} />
              <div className="section-divider" />
              <ScrollRow title="Trending TV This Week" items={trendingTV}
                type="tv" icon={Tv} accentColor="blue"
                onSelect={(item) => setSelected({ item, type: "tv" })} />
            </>)}

            {tab === "movies" && (<>
              <ScrollRow title="Now Playing in Cinemas" items={nowPlaying}
                type="movie" icon={Play} accentColor="red"
                onSelect={(item) => setSelected({ item, type: "movie" })} />
              <div className="section-divider" />
              <ScrollRow title="Coming Soon" items={upcoming}
                type="movie" icon={Calendar} accentColor="purple"
                onSelect={(item) => setSelected({ item, type: "movie" })} />
              <div className="section-divider" />
              <ScrollRow title="All-Time Top Rated" items={topRatedM}
                type="movie" icon={Award} accentColor="yellow"
                onSelect={(item) => setSelected({ item, type: "movie" })} />
            </>)}

            {tab === "tv" && (<>
              <ScrollRow title="Popular Right Now" items={popularTV}
                type="tv" icon={Flame} accentColor="orange"
                onSelect={(item) => setSelected({ item, type: "tv" })} />
              <div className="section-divider" />
              <ScrollRow title="All-Time Best TV" items={topRatedTV}
                type="tv" icon={Award} accentColor="blue"
                onSelect={(item) => setSelected({ item, type: "tv" })} />
            </>)}
          </motion.div>
        </AnimatePresence>

      </>)}

      {/* ── Loading skeleton ── */}
      {loading && !query && (
        <div className="space-y-8">
          {[...Array(3)].map((_, s) => (
            <div key={s} className="space-y-3">
              <div className="h-5 w-48 bg-zinc-800 rounded animate-pulse" />
              <div className="flex gap-3">
                {[...Array(8)].map((_, i) => (
                  <div key={i} className="flex-shrink-0 w-[130px]">
                    <div className="aspect-[2/3] bg-zinc-800 rounded-xl animate-pulse" />
                    <div className="h-3 bg-zinc-800 rounded mt-2 animate-pulse w-3/4" />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Detail modal ── */}
      <AnimatePresence>
        {selected && (
          <DetailModal item={selected.item} type={selected.type}
            onClose={() => setSelected(null)} />
        )}
      </AnimatePresence>

    </div>
  );
}