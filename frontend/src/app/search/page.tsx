"use client";
import { useState, useEffect, useCallback } from "react";
import { api, Movie } from "@/lib/api";
import { MovieCard, MovieCardSkeleton } from "@/components/MovieCard";
import { Search, SlidersHorizontal } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function SearchPage() {
  const [query, setQuery]     = useState("");
  const [genre, setGenre]     = useState("");
  const [lang, setLang]       = useState("");
  const [minVote, setMinVote] = useState(0);
  const [sortBy, setSortBy]   = useState("Popularity");
  const [results, setResults] = useState<Movie[]>([]);
  const [total, setTotal]     = useState(0);
  const [page, setPage]       = useState(1);
  const [pages, setPages]     = useState(1);
  const [loading, setLoading] = useState(false);
  const [allGenres, setAllGenres] = useState<string[]>([]);
  const [allLangs,  setAllLangs]  = useState<string[]>([]);

  useEffect(() => {
    api.genres(50).then(gs => setAllGenres(gs.map((g:any) => g.genre)));
    api.languages(30).then(ls => setAllLangs(ls.map((l:any) => l.language)));
    doSearch(1);
  }, []);

  const doSearch = useCallback((p = 1) => {
    setLoading(true);
    api.search({ q:query, genre, language:lang, min_vote:minVote,
                 sort_by:sortBy, sort_asc:false, page:p, page_size:24 })
      .then(data => {
        setResults(data.results); setTotal(data.total);
        setPages(data.pages);    setPage(p);
      })
      .finally(() => setLoading(false));
  }, [query, genre, lang, minVote, sortBy]);

    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="py-8 space-y-6"
      >
      <h1 className="text-3xl font-bold text-white gradient-text">Search Movies</h1>

      {/* Search bar */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500" size={18} />
        <input
          value={query} onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === "Enter" && doSearch(1)}
          placeholder="Search by title, genre, or keyword in overview…"
          className="w-full pl-11 pr-4 py-3 bg-zinc-900 border border-zinc-700 rounded-xl
                     text-white placeholder-zinc-500 focus:outline-none focus:border-red-500 text-sm" />
      </div>

      {/* Filters row */}
      <div className="flex flex-wrap gap-3 items-end">
        <div className="flex flex-col gap-1">
          <label className="text-zinc-500 text-xs">Genre</label>
          <select value={genre} onChange={e => setGenre(e.target.value)}
            className="bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-white
                       focus:outline-none focus:border-red-500 min-w-[140px]">
            <option value="">All genres</option>
            {allGenres.map(g => <option key={g}>{g}</option>)}
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-zinc-500 text-xs">Language</label>
          <select value={lang} onChange={e => setLang(e.target.value)}
            className="bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-white
                       focus:outline-none focus:border-red-500 min-w-[100px]">
            <option value="">All</option>
            {allLangs.map(l => <option key={l}>{l}</option>)}
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-zinc-500 text-xs">Min Vote ≥ {minVote.toFixed(1)}</label>
          <input type="range" min={0} max={10} step={0.5} value={minVote}
            onChange={e => setMinVote(+e.target.value)}
            className="w-32 accent-red-500" />
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-zinc-500 text-xs">Sort by</label>
          <select value={sortBy} onChange={e => setSortBy(e.target.value)}
            className="bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-white
                       focus:outline-none focus:border-red-500">
            <option value="Popularity">Popularity</option>
            <option value="Vote_Average">Vote Average</option>
            <option value="Vote_Count">Vote Count</option>
            <option value="Year">Year</option>
          </select>
        </div>

        <button onClick={() => doSearch(1)}
          className="flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white px-5 py-2
                     rounded-lg text-sm font-medium transition-colors">
          <SlidersHorizontal size={14} /> Search
        </button>
      </div>

      {/* Results count */}
      <p className="text-zinc-500 text-sm">{total.toLocaleString()} results</p>

      {/* Grid */}
      <AnimatePresence mode="wait">
        <motion.div
          key={results.map(r => r.Title).join(",")}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.25 }}
          className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3"
        >
          {loading
            ? [...Array(24)].map((_, i) => (
                <MovieCardSkeleton key={i} index={i} />
              ))
            : results.map((m, i) => (
                <MovieCard
                  key={m.Title + m.Year}
                  movie={m}
                  index={i}
                />
              ))
          }
        </motion.div>
      </AnimatePresence>

      {/* Pagination */}
      {pages > 1 && (
        <div className="flex justify-center gap-2 pt-4">
          {page > 1 && <button onClick={() => doSearch(page-1)}
            className="px-4 py-2 bg-zinc-800 text-white rounded-lg hover:bg-zinc-700 text-sm">← Prev</button>}
          <span className="px-4 py-2 text-zinc-400 text-sm">Page {page} of {pages}</span>
          {page < pages && <button onClick={() => doSearch(page+1)}
            className="px-4 py-2 bg-zinc-800 text-white rounded-lg hover:bg-zinc-700 text-sm">Next →</button>}
        </div>
      )}
    </motion.div>
  );
}