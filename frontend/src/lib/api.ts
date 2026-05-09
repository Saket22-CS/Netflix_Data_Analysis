const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const api = {
  stats:         () => fetch(`${BASE}/api/stats`).then(r => r.json()),
  moviesPerYear: (from = 1990) => fetch(`${BASE}/api/movies-per-year?from_year=${from}`).then(r => r.json()),
  genres:        (top = 20) => fetch(`${BASE}/api/genres?top=${top}`).then(r => r.json()),
  genreStats:    () => fetch(`${BASE}/api/genre-stats`).then(r => r.json()),
  languages:     () => fetch(`${BASE}/api/languages`).then(r => r.json()),
  voteDist:      () => fetch(`${BASE}/api/vote-distribution`).then(r => r.json()),
  topPopular:    (n = 20, minVotes = 0) => fetch(`${BASE}/api/top-popular?n=${n}&min_votes=${minVotes}`).then(r => r.json()),
  bestRated:     (n = 20, minVotes = 500) => fetch(`${BASE}/api/best-rated?n=${n}&min_votes=${minVotes}`).then(r => r.json()),
  search:        (params: Record<string, string|number|boolean>) => {
    const qs = new URLSearchParams(params as Record<string,string>).toString();
    return fetch(`${BASE}/api/search?${qs}`).then(r => r.json());
  },
  movie:         (title: string) => fetch(`${BASE}/api/movie/${encodeURIComponent(title)}`).then(r => r.json()),
  recommend:     (title: string, n = 8) => fetch(`${BASE}/api/recommend/${encodeURIComponent(title)}?n=${n}`).then(r => r.json()),
  mood:          (mood: string, n = 12) => fetch(`${BASE}/api/mood/${mood}?n=${n}`).then(r => r.json()),
  clusters:      (k = 4) => fetch(`${BASE}/api/clusters?k=${k}`).then(r => r.json()),
  wordFreq:      (top = 40) => fetch(`${BASE}/api/word-freq?top=${top}`).then(r => r.json()),
  yearlyTrend:   () => fetch(`${BASE}/api/yearly-trend`).then(r => r.json()),
  decadeGenre:   () => fetch(`${BASE}/api/decade-genre`).then(r => r.json()),
  titles:        () => fetch(`${BASE}/api/titles`).then(r => r.json()),
};

export type Movie = {
  Title: string; Year: number; Overview: string; Popularity: number;
  Vote_Count: number; Vote_Average: number; Original_Language: string;
  Genre: string; Poster_Url: string; Vote_Bucket: string;
  Pop_Tier: string; Era: string; Decade: number; Overview_WC: number;
};