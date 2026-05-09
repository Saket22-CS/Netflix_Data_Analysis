"use client";
import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { api, Movie } from "@/lib/api";
import { Star, Flame, Hash, Calendar } from "lucide-react";
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Legend } from "recharts";
import Select from "react-select";

const COLORS = ["#ef4444","#3b82f6","#22c55e","#f97316"];
const selectStyles = {
  control: (base: any) => ({
    ...base,
    backgroundColor: "#18181b",
    borderColor: "#3f3f46",
    color: "white",
    minHeight: "42px",
    boxShadow: "none",
  }),

  menu: (base: any) => ({
    ...base,
    backgroundColor: "#18181b",
    border: "1px solid #3f3f46",
  }),

  option: (base: any, state: any) => ({
    ...base,
    backgroundColor: state.isFocused ? "#27272a" : "#18181b",
    color: "white",
    cursor: "pointer",
  }),

  singleValue: (base: any) => ({
    ...base,
    color: "white",
  }),

  input: (base: any) => ({
    ...base,
    color: "white",
  }),

  placeholder: (base: any) => ({
    ...base,
    color: "#71717a",
  }),
};

export default function ComparePage() {
  const [allTitles, setAllTitles] = useState<string[]>([]);
  const [picks, setPicks]   = useState<(string|"")[]>(["","","",""]);
  const [movies, setMovies] = useState<(Movie|null)[]>([null,null,null,null]);
  const [maxVals, setMaxVals] = useState({ Popularity:1, Vote_Count:1, Vote_Average:10 });

  useEffect(() => {
    api.titles().then((ts: string[]) => setAllTitles(ts));
    api.stats().then((s:any) => setMaxVals({ Popularity:s.max_popularity, Vote_Count:50000, Vote_Average:10 }));
  }, []);

  const pickMovie = async (i: number, title: string) => {
    const next = [...picks]; next[i] = title; setPicks(next);
    if (!title) { const nm=[...movies]; nm[i]=null; setMovies(nm); return; }
    const m = await api.movie(title);
    const nm = [...movies]; nm[i] = m; setMovies(nm);
  };

  const active = movies.filter(Boolean) as Movie[];

  const radarData = [
    { metric:"Popularity",  ...Object.fromEntries(active.map(m => [m.Title.slice(0,12), +(m.Popularity/maxVals.Popularity*100).toFixed(1)])) },
    { metric:"Vote Count",  ...Object.fromEntries(active.map(m => [m.Title.slice(0,12), +(m.Vote_Count/maxVals.Vote_Count*100).toFixed(1)])) },
    { metric:"Vote Avg",    ...Object.fromEntries(active.map(m => [m.Title.slice(0,12), +(m.Vote_Average/maxVals.Vote_Average*100).toFixed(1)])) },
  ];

  return (
    <div className="py-8 space-y-8">
      <h1 className="text-3xl font-bold gradient-text">Movie Comparator</h1>

      {/* Picker */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {picks.map((p,i) => (
          <div key={i} className="space-y-1">
            <label className="text-zinc-500 text-xs">Movie {i+1}</label>
            <Select
              options={allTitles.map(t => ({
                value: t,
                label: t,
              }))}

              value={
                p
                  ? { value: p, label: p }
                  : null
              }

              onChange={(selected) =>
                pickMovie(i, selected?.value || "")
              }

              placeholder="Search movie..."
              isClearable
              isSearchable
              styles={selectStyles}
            />
          </div>
        ))}
      </div>

      {active.length < 2 && (
        <p className="text-zinc-500 text-sm">Select at least 2 movies to compare.</p>
      )}

      {active.length >= 2 && (<>
        {/* Poster row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">

          <AnimatePresence>
            {active.map((m, i) => {
              const poster = m.Poster_Url?.startsWith("http")
                ? m.Poster_Url
                : null;

              return (
                <motion.div
                  key={m.Title}
                  initial={{ opacity: 0, scale: 0.9, y: 20 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.9, y: 20 }}
                  transition={{ duration: 0.35, ease: "easeOut" }}
                  className="bg-zinc-900 border-2 rounded-xl overflow-hidden"
                  style={{ borderColor: COLORS[i] }}
                >
                  {poster ? (
                    <img
                      src={poster}
                      alt={m.Title}
                      className="w-full h-52 object-cover"
                    />
                  ) : (
                    <div className="w-full h-52 bg-zinc-800 flex items-center justify-center text-zinc-600 text-sm">
                      No poster
                    </div>
                  )}

                  <div className="p-3">
                    <p className="text-white font-semibold text-sm truncate">
                      {m.Title}
                    </p>

                    <p className="text-zinc-500 text-xs mt-0.5">
                      {m.Year}
                    </p>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>

        </div>

        {/* Stats table */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-800">
                <th className="text-left p-4 text-zinc-500 font-medium">Metric</th>
                {active.map((m,i) => (
                  <th key={m.Title} className="text-left p-4 font-medium"
                      style={{ color: COLORS[i] }}>{m.Title.slice(0,20)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[
                { label:"Vote Average", key:"Vote_Average", fmt:(v:number) => `${v.toFixed(1)}/10`, icon:Star },
                { label:"Vote Count",   key:"Vote_Count",   fmt:(v:number) => v.toLocaleString(),    icon:Hash },
                { label:"Popularity",   key:"Popularity",   fmt:(v:number) => v.toFixed(1),          icon:Flame },
                { label:"Year",         key:"Year",         fmt:(v:number) => String(v??"-"),         icon:Calendar },
                { label:"Genre",        key:"Genre",        fmt:(v:string) => v,                      icon:null },
                { label:"Language",     key:"Original_Language", fmt:(v:string) => v,                 icon:null },
                { label:"Era",          key:"Era",          fmt:(v:string) => v,                      icon:null },
                { label:"Vote Category",key:"Vote_Bucket",  fmt:(v:string) => v,                      icon:null },
              ].map(({ label, key, fmt }) => (
                <tr key={label} className="border-b border-zinc-800/50 hover:bg-zinc-800/30">
                  <td className="p-4 text-zinc-400 font-medium">{label}</td>
                  {active.map(m => (
                    <td key={m.Title} className="p-4 text-white">{fmt((m as any)[key])}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Radar chart */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
          <h2 className="text-white font-semibold mb-4">Radar Comparison (normalised to dataset max)</h2>
          <ResponsiveContainer width="100%" height={320}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#27272a" />
              <PolarAngleAxis dataKey="metric" tick={{ fill:"#a1a1aa", fontSize:12 }} />
              {active.map((m,i) => (
                <Radar key={m.Title} name={m.Title.slice(0,14)}
                  dataKey={m.Title.slice(0,12)} stroke={COLORS[i]} fill={COLORS[i]}
                  fillOpacity={0.2} strokeWidth={2} />
              ))}
              <Legend wrapperStyle={{ color:"#a1a1aa", fontSize:12 }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </>)}
    </div>
  );
}