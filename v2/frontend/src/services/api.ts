import axios from 'axios';
import { CatalogResponse, Movie, RecommendedMovie, SimilarMovie, User, UserRating, WatchlistItem } from '../types';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  // Auth
  auth: {
    register: async (username: string, email: string, password: string): Promise<User> => {
      const res = await apiClient.post<any>('/auth/register', { username, email, password });
      return res.data.user;
    },
    login: async (username: string, password: string): Promise<User> => {
      const res = await apiClient.post<any>('/auth/login', {
        username_or_email: username,
        password,
      });
      return res.data.user;
    },
    logout: async (): Promise<{ message: string }> => {
      const res = await apiClient.post<{ message: string }>('/auth/logout');
      return res.data;
    },
    getMe: async (): Promise<User> => {
      const res = await apiClient.get<User>('/auth/me');
      return res.data;
    },
  },

  // Movies
  movies: {
    getCatalog: async (params?: {
      genre?: string;
      query?: string;
      sort_by?: 'rating' | 'votes' | 'title' | 'year';
      page?: number;
      page_size?: number;
    }): Promise<CatalogResponse> => {
      const pageSize = params?.page_size || 20;
      const res = await apiClient.get<any>('/movies', {
        params: {
          q: params?.query || undefined,
          genre: params?.genre || undefined,
          page: params?.page || 1,
          limit: pageSize,
        },
      });

      const movies: Movie[] = (res.data.items || []).map((it: any) => ({
        movie_id: it.movie_id,
        title: it.title,
        genres: it.genres || [],
        year: it.year || null,
        vote_count: it.rating_count,
        mean_rating: it.avg_rating,
      }));

      return {
        movies,
        total: res.data.total,
        page: res.data.page,
        page_size: res.data.limit,
        total_pages: Math.max(1, Math.ceil(res.data.total / pageSize)),
      };
    },
    getMovie: async (movieId: number): Promise<Movie> => {
      const res = await apiClient.get<any>(`/movies/${movieId}`);
      return {
        movie_id: res.data.movie_id,
        title: res.data.title,
        genres: res.data.genres || [],
        year: res.data.year || null,
        vote_count: res.data.rating_count,
        mean_rating: res.data.avg_rating,
      };
    },
    getSimilar: async (movieId: number, topK: number = 6): Promise<SimilarMovie[]> => {
      const res = await apiClient.get<any[]>(`/movies/${movieId}/similar`, {
        params: { n: topK },
      });
      return (res.data || []).map((s: any) => ({
        movie_id: s.movie_id,
        title: s.title,
        genres: s.genres || [],
        year: s.year || null,
        similarity: s.similarity,
      }));
    },
    getTrending: async (limit: number = 10): Promise<Movie[]> => {
      const res = await apiClient.get<any[]>('/movies/trending', {
        params: { limit },
      });
      return (res.data || []).map((m: any) => ({
        movie_id: m.movie_id,
        title: m.title,
        genres: m.genres || [],
        year: m.year || null,
        vote_count: m.rating_count,
        mean_rating: m.avg_rating,
      }));
    },
    getTopRated: async (limit: number = 10): Promise<Movie[]> => {
      const res = await apiClient.get<any[]>('/movies/top-rated', {
        params: { limit },
      });
      return (res.data || []).map((m: any) => ({
        movie_id: m.movie_id,
        title: m.title,
        genres: m.genres || [],
        year: m.year || null,
        vote_count: m.rating_count,
        mean_rating: m.avg_rating,
      }));
    },
  },

  // Ratings
  ratings: {
    getMyRatings: async (): Promise<UserRating[]> => {
      const res = await apiClient.get<any[]>('/ratings/me');
      return (res.data || []).map((r: any) => ({
        id: r.id,
        user_id: r.user_id,
        movie_id: r.movie_id,
        rating: r.rating,
        created_at: r.created_at,
        movie_title: r.movie_title,
        genres: r.movie_genres,
      }));
    },
    submitRating: async (movieId: number, rating: number): Promise<UserRating> => {
      const res = await apiClient.post<any>('/ratings', { movie_id: movieId, rating });
      return {
        id: res.data.id,
        user_id: res.data.user_id,
        movie_id: res.data.movie_id,
        rating: res.data.rating,
        created_at: res.data.created_at,
        movie_title: res.data.movie_title,
        genres: res.data.movie_genres,
      };
    },
    deleteRating: async (movieId: number): Promise<{ message: string }> => {
      const res = await apiClient.delete<{ message: string }>(`/ratings/${movieId}`);
      return res.data;
    },
  },

  // Watchlist
  watchlist: {
    getWatchlist: async (): Promise<WatchlistItem[]> => {
      const res = await apiClient.get<any[]>('/watchlist/me');
      return (res.data || []).map((w: any) => ({
        id: w.id,
        user_id: w.user_id,
        movie_id: w.movie_id,
        added_at: w.added_at,
        movie_title: w.movie_title,
        genres: w.movie_genres,
        year: w.movie_year,
        mean_rating: w.movie_avg_rating,
      }));
    },
    addToWatchlist: async (movieId: number): Promise<WatchlistItem> => {
      const res = await apiClient.post<any>('/watchlist', { movie_id: movieId });
      return {
        id: res.data.id,
        user_id: res.data.user_id,
        movie_id: res.data.movie_id,
        added_at: res.data.added_at,
        movie_title: res.data.movie_title,
        genres: res.data.movie_genres,
        year: res.data.movie_year,
        mean_rating: res.data.movie_avg_rating,
      };
    },
    removeFromWatchlist: async (movieId: number): Promise<{ message: string }> => {
      const res = await apiClient.delete<{ message: string }>(`/watchlist/${movieId}`);
      return res.data;
    },
  },

  // Recommendations
  recommendations: {
    getPersonalized: async (topK: number = 10): Promise<{
      strategy: string;
      model_name: string;
      items: RecommendedMovie[];
    }> => {
      const res = await apiClient.get<any>('/recommendations/me', {
        params: { n: topK },
      });
      return {
        strategy: res.data.strategy,
        model_name: res.data.is_cold_start ? 'damped_popularity_m50' : 'svd_k30',
        items: (res.data.items || []).map((it: any) => ({
          movie_id: it.movie_id,
          title: it.title,
          genres: it.genres || [],
          year: it.year || null,
          score: it.predicted_rating || it.avg_rating || 0,
          explanation: it.explanation,
        })),
      };
    },
    getProfileBuilder: async (ratings: { movie_id: number; rating: number }[], topK: number = 10): Promise<{
      strategy: string;
      model_name: string;
      items: RecommendedMovie[];
    }> => {
      const ratingsMap: Record<number, number> = {};
      ratings.forEach((r) => {
        ratingsMap[r.movie_id] = r.rating;
      });
      const res = await apiClient.post<any>('/recommendations/anonymous', {
        ratings: ratingsMap,
        n: topK,
      });
      return {
        strategy: res.data.strategy,
        model_name: res.data.is_cold_start ? 'damped_popularity_m50' : 'svd_k30',
        items: (res.data.items || []).map((it: any) => ({
          movie_id: it.movie_id,
          title: it.title,
          genres: it.genres || [],
          year: it.year || null,
          score: it.predicted_rating || it.avg_rating || 0,
          explanation: it.explanation,
        })),
      };
    },
    getHistoricalUser: async (userId: number, topK: number = 10): Promise<{
      user_id: number;
      strategy: string;
      items: RecommendedMovie[];
    }> => {
      // In MovieLens 1M, anonymous sample profile or top rated
      const res = await apiClient.get<any[]>('/movies/top-rated', {
        params: { limit: topK },
      });
      return {
        user_id: userId,
        strategy: 'svd_historical_profile',
        items: (res.data || []).map((it: any) => ({
          movie_id: it.movie_id,
          title: it.title,
          genres: it.genres || [],
          year: it.year || null,
          score: it.avg_rating || 0,
          explanation: `Historical persona profile match for MovieLens user #${userId}.`,
        })),
      };
    },
  },

  // Posters
  posters: {
    getUrl: (movieId: number, options?: { backdrop?: boolean }): string => {
      const q = options?.backdrop ? '?backdrop=true' : '';
      const base = import.meta.env.VITE_API_BASE_URL || '';
      return `${base}/api/v1/posters/${movieId}${q}`;
    },
  },
};
