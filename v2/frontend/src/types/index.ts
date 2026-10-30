export interface Movie {
  movie_id: number;
  title: string;
  genres: string[];
  year: number | null;
  vote_count?: number;
  mean_rating?: number;
}

export interface MovieDetail extends Movie {
  synopsis?: string;
  similar?: Movie[];
}

export interface RecommendedMovie {
  movie_id: number;
  title: string;
  genres: string[];
  year: number | null;
  score: number;
  explanation?: string;
}

export interface SimilarMovie {
  movie_id: number;
  title: string;
  genres: string[];
  year: number | null;
  similarity: number;
}

export interface User {
  id: number;
  username: string;
  email: string;
  created_at: string;
}

export interface UserRating {
  id: number;
  user_id: number;
  movie_id: number;
  rating: number;
  created_at: string;
  movie_title?: string;
  genres?: string[];
}

export interface WatchlistItem {
  id: number;
  user_id: number;
  movie_id: number;
  added_at: string;
  movie_title?: string;
  genres?: string[];
  year?: number | null;
  mean_rating?: number | null;
}

export interface CatalogResponse {
  movies: Movie[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
