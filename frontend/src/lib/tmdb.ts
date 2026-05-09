const TMDB_BASE  = "https://api.themoviedb.org/3";
const TMDB_IMG   = "https://image.tmdb.org/t/p";
const TOKEN      = process.env.NEXT_PUBLIC_TMDB_TOKEN ?? "";

const tmdbFetch = (path: string) =>
  fetch(`${TMDB_BASE}${path}`, {
    headers: {
      Authorization: `Bearer ${TOKEN}`,
      "Content-Type": "application/json",
    },
  }).then((r) => r.json());

export const tmdb = {
  // Images
  poster:   (path: string, size: "w185"|"w342"|"w500"|"original" = "w342") =>
    path ? `${TMDB_IMG}/${size}${path}` : null,
  backdrop: (path: string, size: "w780"|"w1280"|"original" = "w1280") =>
    path ? `${TMDB_IMG}/${size}${path}` : null,
  profile:  (path: string) => path ? `${TMDB_IMG}/w185${path}` : null,

  // Trending
  trendingMovies: (window: "day"|"week" = "week") =>
    tmdbFetch(`/trending/movie/${window}`),
  trendingTV:     (window: "day"|"week" = "week") =>
    tmdbFetch(`/trending/tv/${window}`),
  trendingAll:    (window: "day"|"week" = "day") =>
    tmdbFetch(`/trending/all/${window}`),

  // Movies
  nowPlaying:  () => tmdbFetch("/movie/now_playing?region=US"),
  upcoming:    () => tmdbFetch("/movie/upcoming?region=US"),
  topRated:    () => tmdbFetch("/movie/top_rated"),
  popular:     () => tmdbFetch("/movie/popular"),
  movieDetail: (id: number) =>
    tmdbFetch(`/movie/${id}?append_to_response=credits,videos,watch/providers,similar,reviews`),

  // TV
  popularTV:  () => tmdbFetch("/tv/popular"),
  topRatedTV: () => tmdbFetch("/tv/top_rated"),
  onAirTV:    () => tmdbFetch("/tv/on_the_air"),
  tvDetail:   (id: number) =>
    tmdbFetch(`/tv/${id}?append_to_response=credits,videos,watch/providers,similar`),

  // Search
  searchMovie:  (q: string, page = 1) =>
    tmdbFetch(`/search/movie?query=${encodeURIComponent(q)}&page=${page}`),
  searchTV:     (q: string, page = 1) =>
    tmdbFetch(`/search/tv?query=${encodeURIComponent(q)}&page=${page}`),
  searchMulti:  (q: string, page = 1) =>
    tmdbFetch(`/search/multi?query=${encodeURIComponent(q)}&page=${page}`),
  searchPerson: (q: string) =>
    tmdbFetch(`/search/person?query=${encodeURIComponent(q)}`),

  // Person
  personDetail: (id: number) =>
    tmdbFetch(`/person/${id}?append_to_response=movie_credits,tv_credits,images`),

  // Discover
  discover: (params: Record<string, string|number>) => {
    const qs = new URLSearchParams(params as Record<string,string>).toString();
    return tmdbFetch(`/discover/movie?${qs}`);
  },

  // Genres
  movieGenres: () => tmdbFetch("/genre/movie/list"),
  tvGenres:    () => tmdbFetch("/genre/tv/list"),
};

// Types
export interface TMDBMovie {
  id: number; title: string; overview: string;
  poster_path: string; backdrop_path: string;
  release_date: string; vote_average: number; vote_count: number;
  popularity: number; genre_ids: number[]; original_language: string;
}

export interface TMDBShow {
  id: number; name: string; overview: string;
  poster_path: string; backdrop_path: string;
  first_air_date: string; vote_average: number; vote_count: number;
  genre_ids: number[];
}

export interface TMDBPerson {
  id: number; name: string; profile_path: string;
  known_for_department: string; popularity: number;
}