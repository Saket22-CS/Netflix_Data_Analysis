"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import {
  AreaChart, Area, BarChart, Bar, ScatterChart, Scatter,
  XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line,
  CartesianGrid, Cell, Legend,
} from "recharts";
import { motion } from "framer-motion";

const COLORS = ["#ef4444","#f97316","#eab308","#22c55e","#3b82f6","#8b5cf6","#ec4899","#14b8a6"];

export default function AnalyticsPage() {
  const [trend,   setTrend]   = useState<any[]>([]);
  const [gStats,  setGStats]  = useState<any[]>([]);
  const [wFreq,   setWFreq]   = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.yearlyTrend(), api.genreStats(), api.wordFreq(20)])
      .then(([t,g,w]) => { setTrend(t); setGStats(g.slice(0,15)); setWFreq(w); })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="py-20 text-center text-zinc-500 animate-pulse">Loading analytics…</div>;

  return (
    <div className="py-8 space-y-8">
      <h1 className="text-3xl font-bold gradient-text">Analytics</h1>

      {/* Trend dual axis */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-60px" }}
          transition={{ duration: 0.45, ease: "easeOut" }}
          className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 premium-card"
        >
        <h2 className="text-white font-semibold mb-4">Vote Average & Popularity Over Time</h2>
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={trend}>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
            <XAxis dataKey="Year" tick={{ fill:"#71717a", fontSize:11 }} />
            <YAxis yAxisId="left"  tick={{ fill:"#71717a", fontSize:11 }} domain={[4,9]} />
            <YAxis yAxisId="right" orientation="right" tick={{ fill:"#71717a", fontSize:11 }} />
            <Tooltip contentStyle={{ background:"#18181b", border:"1px solid #3f3f46", borderRadius:8, color:"#fff" }} />
            <Legend wrapperStyle={{ color:"#a1a1aa", fontSize:12 }} />
            <Line yAxisId="left"  type="monotone" dataKey="avg_vote" stroke="#ef4444" dot={false} name="Avg Vote" strokeWidth={2} />
            <Line yAxisId="right" type="monotone" dataKey="avg_pop"  stroke="#3b82f6" dot={false} name="Avg Popularity" strokeWidth={2} strokeDasharray="5 5" />
          </LineChart>
        </ResponsiveContainer>
      </motion.div>

      {/* Genre scatter: avg popularity vs avg vote */}
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-60px" }}
        transition={{ duration: 0.45, ease: "easeOut" }}
        className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 premium-card"
      >
        <h2 className="text-white font-semibold mb-4">Genre — Popularity vs Vote Average</h2>
        <ResponsiveContainer width="100%" height={300}>
          <ScatterChart>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
            <XAxis dataKey="avg_pop"  name="Popularity" tick={{ fill:"#71717a", fontSize:11 }}
                   label={{ value:"Avg Popularity", position:"insideBottom", offset:-4, fill:"#71717a", fontSize:11 }} />
            <YAxis dataKey="avg_vote" name="Vote"       tick={{ fill:"#71717a", fontSize:11 }}
                   label={{ value:"Avg Vote", angle:-90, position:"insideLeft", fill:"#71717a", fontSize:11 }} />
            <Tooltip cursor={{ strokeDasharray:"3 3" }}
              contentStyle={{ background:"#18181b", border:"1px solid #3f3f46", borderRadius:8, color:"#fff" }}
              formatter={(_:any,__:any,p:any) => [p.payload.genre, ""]} />
            <Scatter data={gStats} fill="#ef4444">
              {gStats.map((_,i) => <Cell key={i} fill={COLORS[i%COLORS.length]} />)}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </motion.div>

      {/* Genre avg vote bar */}
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-60px" }}
        transition={{ duration: 0.45, ease: "easeOut" }}
        className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 premium-card"
      >
        <h2 className="text-white font-semibold mb-4">Avg Vote Average by Genre</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={[...gStats].sort((a,b)=>b.avg_vote-a.avg_vote).slice(0,12)} layout="vertical">
            <XAxis type="number" domain={[0,10]} tick={{ fill:"#71717a", fontSize:11 }} tickLine={false} axisLine={false} />
            <YAxis dataKey="genre" type="category" tick={{ fill:"#a1a1aa", fontSize:11 }} width={120} tickLine={false} axisLine={false} />
            <Tooltip contentStyle={{ background:"#18181b", border:"1px solid #3f3f46", borderRadius:8, color:"#fff" }} />
            <Bar dataKey="avg_vote" fill="#8b5cf6" radius={[0,4,4,0]}>
              {gStats.map((_,i) => <Cell key={i} fill={COLORS[i%COLORS.length]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </motion.div>

      {/* Word frequency */}
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-60px" }}
        transition={{ duration: 0.45, ease: "easeOut" }}
        className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 premium-card"
      >
        <h2 className="text-white font-semibold mb-4">Top Words in Movie Overviews</h2>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={wFreq} layout="vertical">
            <XAxis type="number" tick={{ fill:"#71717a", fontSize:11 }} tickLine={false} axisLine={false} />
            <YAxis dataKey="word" type="category" tick={{ fill:"#a1a1aa", fontSize:11 }} width={90} tickLine={false} axisLine={false} />
            <Tooltip contentStyle={{ background:"#18181b", border:"1px solid #3f3f46", borderRadius:8, color:"#fff" }} />
            <Bar dataKey="count" fill="#8b5cf6" radius={[0,4,4,0]} />
          </BarChart>
        </ResponsiveContainer>
      </motion.div>
    </div>
  );
}