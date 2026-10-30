import { CatalogResponse, Movie, SimilarMovie, RecommendedMovie } from '../types';
import rawMoviesData from '../data/movies.json';

export interface LocalMovieRecord {
  movie_id: number;
  title: string;
  year?: number | null;
  genres: string[];
  avg_rating?: number;
  rating_count?: number;
}

export const ALL_MOVIES: LocalMovieRecord[] = rawMoviesData as LocalMovieRecord[];

// Fast index map for O(1) lookups
const MOVIE_MAP = new Map<number, LocalMovieRecord>();
ALL_MOVIES.forEach((m) => MOVIE_MAP.set(m.movie_id, m));

// Known TMDB artwork for key MovieLens 1M titles
export const KNOWN_POSTERS: Record<number, string> = {
  2959: 'https://image.tmdb.org/t/p/w780/hZkgoQYus5vegHoetLkCJzb17zJ.jpg', // Fight Club
  2571: 'https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg', // The Matrix
  260: 'https://image.tmdb.org/t/p/w500/6FfCtAuVAW8XJjZ7eWeLibRLWTw.jpg', // Star Wars IV
  1196: 'https://image.tmdb.org/t/p/w500/2l05cvejsi0vEiC22LCvbu2vhQB.jpg', // Star Wars V
  1210: 'https://image.tmdb.org/t/p/w500/mDCBQNhR6R0PVF25ylpGqA4N6vH.jpg', // Star Wars VI
  2858: 'https://image.tmdb.org/t/p/w500/wby9315QzVKX9NXeg2tVIHGz2qW.jpg', // American Beauty
  2028: 'https://image.tmdb.org/t/p/w500/uqx37cS8cpHg8x35f9U5IBlrCV3.jpg', // Saving Private Ryan
  1: 'https://image.tmdb.org/t/p/w500/uXDfjJbdP4ijW5hWSBrPrlKpxab.jpg', // Toy Story
  318: 'https://image.tmdb.org/t/p/w500/9cqNxx0GxF0bflZmeSMuL5tnGzr.jpg', // Shawshank Redemption
  593: 'https://image.tmdb.org/t/p/w500/rplLJ2hPcOQmkFhTqUte0MkEaO2.jpg', // Silence of the Lambs
  480: 'https://image.tmdb.org/t/p/w500/oU7Oq2kFAAlGqbU4VoAE36g4hoI.jpg', // Jurassic Park
  589: 'https://image.tmdb.org/t/p/w500/5M0j0B18abtBI5flAQR8umneTR.jpg', // Terminator 2
  110: 'https://image.tmdb.org/t/p/w500/or1gBugydmjToAEqDpOuuHQKaJJ.jpg', // Braveheart
  296: 'https://image.tmdb.org/t/p/w500/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg', // Pulp Fiction
  858: 'https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsRolD1fZdja1.jpg', // The Godfather
  2762: 'https://image.tmdb.org/t/p/w500/4AfSDjjCy6T5LA1BCz6buQUUV20.jpg', // Sixth Sense
  608: 'https://image.tmdb.org/t/p/w500/775H7kXq2Nq2pE44Gz2H0G6j1Bf.jpg', // Fargo
  1270: 'https://image.tmdb.org/t/p/w500/fNOH9f1aA7XRTzl1sAOxUpuhj52.jpg', // Back to the Future
  1240: 'https://image.tmdb.org/t/p/w500/qvktm0BHcnmDpul4Hz01GIazWPr.jpg', // The Terminator
};

/** Generate stylized vector SVG poster for any movie */
export function getSvgPosterDataUrl(title: string, year?: number | null): string {
  const line1 = title.length > 20 ? title.slice(0, 19) + '…' : title;
  const yearStr = year ? String(year) : '';
  const escapedTitle = line1.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 450" width="300" height="450">
    <defs>
      <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#0a102b"/>
        <stop offset="50%" stop-color="#141c46"/>
        <stop offset="100%" stop-color="#070a1c"/>
      </linearGradient>
      <linearGradient id="neon" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#00f2fe"/>
        <stop offset="100%" stop-color="#b829dd"/>
      </linearGradient>
      <radialGradient id="glow" cx="50%" cy="30%" r="50%">
        <stop offset="0%" stop-color="#00f2fe" stop-opacity="0.3"/>
        <stop offset="100%" stop-color="#00f2fe" stop-opacity="0"/>
      </radialGradient>
    </defs>
    <rect width="300" height="450" fill="url(#bg)" rx="16"/>
    <rect width="296" height="446" x="2" y="2" fill="none" stroke="url(#neon)" stroke-width="2" rx="14" opacity="0.6"/>
    <circle cx="150" cy="140" r="100" fill="url(#glow)"/>
    <circle cx="150" cy="145" r="42" fill="none" stroke="#00f2fe" stroke-width="3" opacity="0.8"/>
    <circle cx="150" cy="145" r="14" fill="#b829dd" opacity="0.9"/>
    <circle cx="150" cy="117" r="6" fill="#00f2fe"/>
    <circle cx="150" cy="173" r="6" fill="#00f2fe"/>
    <circle cx="122" cy="145" r="6" fill="#00f2fe"/>
    <circle cx="178" cy="145" r="6" fill="#00f2fe"/>
    <text x="150" y="260" text-anchor="middle" fill="#ffffff" font-family="'Space Grotesk', system-ui, sans-serif" font-weight="700" font-size="18">${escapedTitle}</text>
    <rect x="110" y="295" width="80" height="24" rx="12" fill="rgba(0, 242, 254, 0.15)" stroke="#00f2fe" stroke-width="1"/>
    <text x="150" y="311" text-anchor="middle" fill="#00f2fe" font-family="system-ui, sans-serif" font-weight="600" font-size="12">${yearStr}</text>
    <text x="150" y="415" text-anchor="middle" fill="#64748b" font-family="system-ui, sans-serif" font-size="11" letter-spacing="1.5">MOVIEREC V2</text>
  </svg>`;
  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
}

export function getLocalPosterUrl(movieId: number, options?: { backdrop?: boolean }): string {
  if (KNOWN_POSTERS[movieId]) {
    return KNOWN_POSTERS[movieId];
  }
  const movie = MOVIE_MAP.get(movieId);
  if (movie) {
    return getSvgPosterDataUrl(movie.title, movie.year);
  }
  return `/api/v1/posters/${movieId}${options?.backdrop ? '?backdrop=true' : ''}`;
}

export const localCatalog = {
  getCatalog: (params?: {
    genre?: string;
    query?: string;
    sort_by?: 'rating' | 'votes' | 'title' | 'year';
    page?: number;
    page_size?: number;
  }): CatalogResponse => {
    const page = params?.page || 1;
    const pageSize = params?.page_size || 20;
    const query = (params?.query || '').trim().toLowerCase();
    const genre = params?.genre || '';
    const sortBy = params?.sort_by || 'votes';

    let list = ALL_MOVIES;

    // Filter by search query
    if (query) {
      list = list.filter((m) => m.title.toLowerCase().includes(query));
    }

    // Filter by genre
    if (genre && genre !== 'All Genres') {
      list = list.filter((m) => m.genres.some((g) => g.toLowerCase() === genre.toLowerCase()));
    }

    // Sort
    const sorted = [...list].sort((a, b) => {
      if (sortBy === 'rating') {
        return (b.avg_rating || 0) - (a.avg_rating || 0);
      }
      if (sortBy === 'title') {
        return a.title.localeCompare(b.title);
      }
      if (sortBy === 'year') {
        return (b.year || 0) - (a.year || 0);
      }
      // Default: votes
      return (b.rating_count || 0) - (a.rating_count || 0);
    });

    const total = sorted.length;
    const start = (page - 1) * pageSize;
    const items = sorted.slice(start, start + pageSize).map((m) => ({
      movie_id: m.movie_id,
      title: m.title,
      genres: m.genres,
      year: m.year || null,
      vote_count: m.rating_count || 0,
      mean_rating: m.avg_rating || 0,
    }));

    return {
      movies: items,
      total,
      page,
      page_size: pageSize,
      total_pages: Math.max(1, Math.ceil(total / pageSize)),
    };
  },

  getMovie: (movieId: number): Movie | null => {
    const m = MOVIE_MAP.get(movieId);
    if (!m) return null;
    return {
      movie_id: m.movie_id,
      title: m.title,
      genres: m.genres,
      year: m.year || null,
      vote_count: m.rating_count || 0,
      mean_rating: m.avg_rating || 0,
    };
  },

  getTrending: (limit: number = 10): Movie[] => {
    return [...ALL_MOVIES]
      .sort((a, b) => (b.rating_count || 0) - (a.rating_count || 0))
      .slice(0, limit)
      .map((m) => ({
        movie_id: m.movie_id,
        title: m.title,
        genres: m.genres,
        year: m.year || null,
        vote_count: m.rating_count || 0,
        mean_rating: m.avg_rating || 0,
      }));
  },

  getTopRated: (limit: number = 10): Movie[] => {
    return ALL_MOVIES.filter((m) => (m.rating_count || 0) >= 50)
      .sort((a, b) => (b.avg_rating || 0) - (a.avg_rating || 0))
      .slice(0, limit)
      .map((m) => ({
        movie_id: m.movie_id,
        title: m.title,
        genres: m.genres,
        year: m.year || null,
        vote_count: m.rating_count || 0,
        mean_rating: m.avg_rating || 0,
      }));
  },

  getSimilar: (movieId: number, topK: number = 6): SimilarMovie[] => {
    const target = MOVIE_MAP.get(movieId);
    if (!target) return [];
    const targetGenres = new Set(target.genres);

    return ALL_MOVIES.filter((m) => m.movie_id !== movieId && m.genres.some((g) => targetGenres.has(g)))
      .sort((a, b) => {
        const overlapA = a.genres.filter((g) => targetGenres.has(g)).length;
        const overlapB = b.genres.filter((g) => targetGenres.has(g)).length;
        if (overlapB !== overlapA) return overlapB - overlapA;
        return (b.rating_count || 0) - (a.rating_count || 0);
      })
      .slice(0, topK)
      .map((m, idx) => ({
        movie_id: m.movie_id,
        title: m.title,
        genres: m.genres,
        year: m.year || null,
        similarity: Math.max(0.7, 0.98 - idx * 0.04),
      }));
  },

  getRecommended: (topK: number = 10): { strategy: string; model_name: string; items: RecommendedMovie[] } => {
    const popular = localCatalog.getTrending(topK);
    return {
      strategy: 'damped_popularity_m50',
      model_name: 'damped_popularity_m50',
      items: popular.map((m, idx) => ({
        movie_id: m.movie_id,
        title: m.title,
        genres: m.genres,
        year: m.year || null,
        score: m.mean_rating || 4.0,
        explanation: `#${idx + 1} most celebrated title across MovieLens 1M discovery graph.`,
      })),
    };
  },
};
