"use client";
import { useEffect, useState } from "react";
import { api, Movie } from "@/lib/api";
import { MovieCard } from "@/components/MovieCard";
import { motion, AnimatePresence } from "framer-motion";
import { ScatterChart, Scatter, XAxis, YAxis, Tooltip,
         ResponsiveContainer, Cell, CartesianGrid } from "recharts";
         

const CLUSTER_COLORS = ["#ef4444","#3b82f6","#22c55e","#f97316","#8b5cf6","#ec4899"];

export default function DiscoverPage() {
  const [tab,    setTab]    = useState<"clusters"|"best"|"popular">("best");
  const [k,      setK]      = useState(4);
  const [clData, setClData] = useState<any>(null);
  const [best,   setBest]   = useState<Movie[]>([]);
  const [pop,    setPop]    = useState<Movie[]>([]);

  useEffect(() => {
    api.bestRated(24, 300).then(setBest);
    api.topPopular(24).then(setPop);
  }, []);

  useEffect(() => {
    if (tab === "clusters") api.clusters(k).then(setClData);
  }, [tab, k]);

  const tabs = [
    { id:"best",     label:"⭐ Best Rated" },
    { id:"popular",  label:"🔥 Most Popular" },
    { id:"clusters", label:"🤖 ML Clusters" },
  ];

  return (
    <div className="py-8 space-y-6">
      <h1 className="text-3xl font-bold text-white gradient-text">Discover</h1>

      <div className="flex gap-2">
        {tabs.map((t, i) => (
          <motion.button
            key={t.id}
            onClick={() => setTab(t.id as any)}
            whileHover={{ scale: 1.04 }}
            whileTap={{ scale: 0.96 }}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all 
              ${tab === t.id ? "bg-red-600 text-white" : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700"}`}
          >
            {t.label}
          </motion.button>
        ))}
      </div>

      <AnimatePresence mode="wait">

        <motion.div
          key={tab}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -12 }}
          transition={{ duration: 0.28 }}
        >

          {tab === "best" && (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
              {best.map((m, i) => (
                <MovieCard
                  key={m.Title}
                  movie={m}
                  index={i}
                />
              ))}
            </div>
          )}

          {tab === "popular" && (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
              {pop.map((m, i) => (
                <MovieCard
                  key={m.Title}
                  movie={m}
                  index={i}
                />
              ))}
            </div>
          )}

          {tab === "clusters" && (
            <div className="space-y-5">

              <div className="flex items-center gap-4">
                <label className="text-zinc-400 text-sm">
                  Clusters (K):
                </label>

                <input
                  type="range"
                  min={2}
                  max={8}
                  value={k}
                  step={1}
                  onChange={(e) => setK(+e.target.value)}
                  className="w-36 accent-red-500"
                />

                <span className="text-white font-bold">
                  {k}
                </span>
              </div>

              {clData ? (
                <>
                  <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
                    <h2 className="text-white font-semibold mb-4">
                      K-Means PCA Projection
                    </h2>

                    <ResponsiveContainer width="100%" height={400}>
                      <ScatterChart>

                        <CartesianGrid
                          strokeDasharray="3 3"
                          stroke="#27272a"
                        />

                        <XAxis
                          dataKey="pc1"
                          name="PC1"
                          tick={{ fill:"#71717a", fontSize:11 }}
                        />

                        <YAxis
                          dataKey="pc2"
                          name="PC2"
                          tick={{ fill:"#71717a", fontSize:11 }}
                        />

                        <Tooltip
                          cursor={false}
                          contentStyle={{
                            background:"#18181b",
                            border:"1px solid #3f3f46",
                            borderRadius:8,
                            color:"#fff"
                          }}

                          content={({ payload }) =>
                            payload?.[0] ? (
                              <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-2 text-xs text-white max-w-[180px]">
                                <p className="font-semibold">
                                  {payload[0].payload.title}
                                </p>

                                <p className="text-zinc-400">
                                  Pop: {payload[0].payload.popularity}
                                </p>

                                <p className="text-zinc-400">
                                  Vote: {payload[0].payload.vote_avg}
                                </p>
                              </div>
                            ) : null
                          }
                        />

                        <Scatter data={clData.points}>
                          {clData.points.map((_:any, i:number) => (
                            <Cell
                              key={i}
                              fill={
                                CLUSTER_COLORS[
                                  clData.points[i].cluster %
                                  CLUSTER_COLORS.length
                                ]
                              }
                              fillOpacity={0.7}
                            />
                          ))}
                        </Scatter>

                      </ScatterChart>
                    </ResponsiveContainer>
                  </div>

                  <div className="flex flex-wrap gap-3">
                    {[...Array(k)].map((_, i) => {
                      const pts = clData.points.filter(
                        (p:any) => p.cluster === i
                      );

                      const avgPop = (
                        pts.reduce(
                          (s:number,p:any)=>s+p.popularity,
                          0
                        ) / pts.length
                      ).toFixed(1);

                      const avgVote = (
                        pts.reduce(
                          (s:number,p:any)=>s+p.vote_avg,
                          0
                        ) / pts.length
                      ).toFixed(2);

                      return (
                        <motion.div
                          key={i}
                          initial={{ opacity: 0, scale: 0.92 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ delay: i * 0.05 }}
                          className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 flex-1 min-w-[140px]"
                        >
                          <div
                            className="w-3 h-3 rounded-full mb-2"
                            style={{
                              background: CLUSTER_COLORS[i]
                            }}
                          />

                          <p className="text-white font-bold text-sm">
                            Cluster {i}
                          </p>

                          <p className="text-zinc-500 text-xs">
                            {pts.length} movies
                          </p>

                          <p className="text-zinc-400 text-xs mt-1">
                            Pop avg: {avgPop}
                          </p>

                          <p className="text-zinc-400 text-xs">
                            Vote avg: {avgVote}
                          </p>
                        </motion.div>
                      );
                    })}
                  </div>
                </>
              ) : (
                <div className="text-zinc-500 animate-pulse">
                  Computing clusters…
                </div>
              )}

            </div>
          )}

        </motion.div>

      </AnimatePresence>
    </div>
  );
}