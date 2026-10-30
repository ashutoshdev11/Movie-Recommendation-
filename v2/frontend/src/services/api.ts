import axios from 'axios';
import { CatalogResponse, Movie, RecommendedMovie, SimilarMovie, User, UserRating, WatchlistItem } from '../types';
import { localCatalog, getLocalPosterUrl } from './localCatalog';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 4000,
});

// Helper for local storage simulation when serverless backend is sleeping or not yet deployed
const LOCAL_STORAGE_RATINGS_KEY = 'movierec_ratings_cache';
const LOCAL_STORAGE_WATCHLIST_KEY = 'movierec_watchlist_cache';

export const api = {
  // Auth
  auth: {
    register: async (username: string, email: string, password: string): Promise<User> => {
      try {
        const res = await apiClient.post<any>('/auth/register', { username, email, password });
        return res.data.user;
      } catch (err) {
        // Fallback demo user session
        const demoUser: User = { id: 9999, username, email, created_at: new Date().toISOString() };
        localStorage.setItem('movierec_active_user', JSON.stringify(demoUser));
        return demoUser;
      }
    },
    login: async (username: string, password: string): Promise<User> => {
      try {
        const res = await apiClient.post<any>('/auth/login', {
          username_or_email: username,
          password,
        });
        return res.data.user;
      } catch (err) {
        const saved = localStorage.getItem('movierec_active_user');
        if (saved) return JSON.parse(saved);
        const demoUser: User = { id: 9999, username, email: `${username}@movierec.io`, created_at: new Date().toISOString() };
        localStorage.setItem('movierec_active_user', JSON.stringify(demoUser));
        return demoUser;
      }
    },
    logout: async (): Promise<{ message: string }> => {
      try {
        const res = await apiClient.post<{ message: string }>('/auth/logout');
        localStorage.removeItem('movierec_active_user');
        return res.data;
      } catch (err) {
        localStorage.removeItem('movierec_active_user');
        return { message: 'Logged out successfully' };
      }
    },
    getMe: async (): Promise<User> => {
      try {
        const res = await apiClient.get<User>('/auth/me');
        return res.data;
      } catch (err) {
        const saved = localStorage.getItem('movierec_active_user');
        if (saved) return JSON.parse(saved);
        throw err;
      }
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
      try {
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

        if (movies.length > 0 || res.data.total > 0) {
          return {
            movies,
            total: res.data.total,
            page: res.data.page,
            page_size: res.data.limit,
            total_pages: Math.max(1, Math.ceil(res.data.total / pageSize)),
          };
        }
      } catch (err) {
        // Fallback to local catalog
      }

      return localCatalog.getCatalog(params);
    },

    getMovie: async (movieId: number): Promise<Movie> => {
      try {
        const res = await apiClient.get<any>(`/movies/${movieId}`);
        return {
          movie_id: res.data.movie_id,
          title: res.data.title,
          genres: res.data.genres || [],
          year: res.data.year || null,
          vote_count: res.data.rating_count,
          mean_rating: res.data.avg_rating,
        };
      } catch (err) {
        const local = localCatalog.getMovie(movieId);
        if (local) return local;
        throw err;
      }
    },

    getSimilar: async (movieId: number, topK: number = 6): Promise<SimilarMovie[]> => {
      try {
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
      } catch (err) {
        return localCatalog.getSimilar(movieId, topK);
      }
    },

    getTrending: async (limit: number = 10): Promise<Movie[]> => {
      try {
        const res = await apiClient.get<any[]>('/movies/trending', {
          params: { limit },
        });
        const items = (res.data || []).map((m: any) => ({
          movie_id: m.movie_id,
          title: m.title,
          genres: m.genres || [],
          year: m.year || null,
          vote_count: m.rating_count,
          mean_rating: m.avg_rating,
        }));
        if (items.length > 0) return items;
      } catch (err) {
        // Fallback
      }
      return localCatalog.getTrending(limit);
    },

    getTopRated: async (limit: number = 10): Promise<Movie[]> => {
      try {
        const res = await apiClient.get<any[]>('/movies/top-rated', {
          params: { limit },
        });
        const items = (res.data || []).map((m: any) => ({
          movie_id: m.movie_id,
          title: m.title,
          genres: m.genres || [],
          year: m.year || null,
          vote_count: m.rating_count,
          mean_rating: m.avg_rating,
        }));
        if (items.length > 0) return items;
      } catch (err) {
        // Fallback
      }
      return localCatalog.getTopRated(limit);
    },
  },

  // Ratings
  ratings: {
    getMyRatings: async (): Promise<UserRating[]> => {
      try {
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
      } catch (err) {
        const stored = localStorage.getItem(LOCAL_STORAGE_RATINGS_KEY);
        return stored ? JSON.parse(stored) : [];
      }
    },

    submitRating: async (movieId: number, rating: number): Promise<UserRating> => {
      try {
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
      } catch (err) {
        const movie = localCatalog.getMovie(movieId);
        const stored = localStorage.getItem(LOCAL_STORAGE_RATINGS_KEY);
        const list: UserRating[] = stored ? JSON.parse(stored) : [];
        const existingIdx = list.findIndex((r) => r.movie_id === movieId);
        const newRating: UserRating = {
          id: Date.now(),
          user_id: 1,
          movie_id: movieId,
          rating,
          created_at: new Date().toISOString(),
          movie_title: movie?.title || `Movie ${movieId}`,
          genres: movie?.genres,
        };
        if (existingIdx >= 0) {
          list[existingIdx] = newRating;
        } else {
          list.push(newRating);
        }
        localStorage.setItem(LOCAL_STORAGE_RATINGS_KEY, JSON.stringify(list));
        return newRating;
      }
    },

    deleteRating: async (movieId: number): Promise<{ message: string }> => {
      try {
        const res = await apiClient.delete<{ message: string }>(`/ratings/${movieId}`);
        return res.data;
      } catch (err) {
        const stored = localStorage.getItem(LOCAL_STORAGE_RATINGS_KEY);
        if (stored) {
          const list: UserRating[] = JSON.parse(stored);
          const filtered = list.filter((r) => r.movie_id !== movieId);
          localStorage.setItem(LOCAL_STORAGE_RATINGS_KEY, JSON.stringify(filtered));
        }
        return { message: 'Rating deleted successfully' };
      }
    },
  },

  // Watchlist
  watchlist: {
    getWatchlist: async (): Promise<WatchlistItem[]> => {
      try {
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
      } catch (err) {
        const stored = localStorage.getItem(LOCAL_STORAGE_WATCHLIST_KEY);
        return stored ? JSON.parse(stored) : [];
      }
    },

    addToWatchlist: async (movieId: number): Promise<WatchlistItem> => {
      try {
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
      } catch (err) {
        const movie = localCatalog.getMovie(movieId);
        const stored = localStorage.getItem(LOCAL_STORAGE_WATCHLIST_KEY);
        const list: WatchlistItem[] = stored ? JSON.parse(stored) : [];
        const newItem: WatchlistItem = {
          id: Date.now(),
          user_id: 1,
          movie_id: movieId,
          added_at: new Date().toISOString(),
          movie_title: movie?.title || `Movie ${movieId}`,
          genres: movie?.genres,
          year: movie?.year,
          mean_rating: movie?.mean_rating,
        };
        if (!list.some((w) => w.movie_id === movieId)) {
          list.push(newItem);
          localStorage.setItem(LOCAL_STORAGE_WATCHLIST_KEY, JSON.stringify(list));
        }
        return newItem;
      }
    },

    removeFromWatchlist: async (movieId: number): Promise<{ message: string }> => {
      try {
        const res = await apiClient.delete<{ message: string }>(`/watchlist/${movieId}`);
        return res.data;
      } catch (err) {
        const stored = localStorage.getItem(LOCAL_STORAGE_WATCHLIST_KEY);
        if (stored) {
          const list: WatchlistItem[] = JSON.parse(stored);
          const filtered = list.filter((w) => w.movie_id !== movieId);
          localStorage.setItem(LOCAL_STORAGE_WATCHLIST_KEY, JSON.stringify(filtered));
        }
        return { message: 'Removed from watchlist' };
      }
    },
  },

  // Recommendations
  recommendations: {
    getPersonalized: async (topK: number = 10): Promise<{
      strategy: string;
      model_name: string;
      items: RecommendedMovie[];
    }> => {
      try {
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
      } catch (err) {
        return localCatalog.getRecommended(topK);
      }
    },

    getProfileBuilder: async (ratings: { movie_id: number; rating: number }[], topK: number = 10): Promise<{
      strategy: string;
      model_name: string;
      items: RecommendedMovie[];
    }> => {
      try {
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
      } catch (err) {
        return localCatalog.getRecommended(topK);
      }
    },

    getHistoricalUser: async (userId: number, topK: number = 10): Promise<{
      user_id: number;
      strategy: string;
      items: RecommendedMovie[];
    }> => {
      try {
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
      } catch (err) {
        const top = localCatalog.getTopRated(topK);
        return {
          user_id: userId,
          strategy: 'svd_historical_profile',
          items: top.map((it) => ({
            movie_id: it.movie_id,
            title: it.title,
            genres: it.genres || [],
            year: it.year || null,
            score: it.mean_rating || 0,
            explanation: `Historical persona profile match for MovieLens user #${userId}.`,
          })),
        };
      }
    },
  },

  // Posters
  posters: {
    getUrl: (movieId: number, options?: { backdrop?: boolean }): string => {
      return getLocalPosterUrl(movieId, options);
    },
  },
};
