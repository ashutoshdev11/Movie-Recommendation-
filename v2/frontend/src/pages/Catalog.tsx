import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Search, Filter, ArrowUpDown, ChevronLeft, ChevronRight, Sparkles } from 'lucide-react';
import { Movie } from '../types';
import { api } from '../services/api';
import { HolographicMovieCard } from '../components/common/HolographicMovieCard';
import { useAuth } from '../context/AuthContext';

const GENRES = [
  'All Genres',
  'Action',
  'Adventure',
  'Animation',
  "Children's",
  'Comedy',
  'Crime',
  'Documentary',
  'Drama',
  'Fantasy',
  'Film-Noir',
  'Horror',
  'Musical',
  'Mystery',
  'Romance',
  'Sci-Fi',
  'Thriller',
  'War',
  'Western',
];

export const Catalog: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { user } = useAuth();

  const queryFromUrl = searchParams.get('q') || '';
  const genreFromUrl = searchParams.get('genre') || '';
  const sortFromUrl = (searchParams.get('sort') as 'rating' | 'votes' | 'title' | 'year') || 'votes';
  const pageFromUrl = parseInt(searchParams.get('page') || '1', 10);

  const [movies, setMovies] = useState<Movie[]>([]);
  const [totalMovies, setTotalMovies] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(true);
  const [watchlistSet, setWatchlistSet] = useState<Set<number>>(new Set());

  // Input states
  const [searchInput, setSearchInput] = useState<string>(queryFromUrl);
  const [selectedGenre, setSelectedGenre] = useState<string>(genreFromUrl || 'All Genres');
  const [sortBy, setSortBy] = useState<'rating' | 'votes' | 'title' | 'year'>(sortFromUrl);
  const [currentPage, setCurrentPage] = useState<number>(pageFromUrl);

  // Load user watchlist
  useEffect(() => {
    if (!user) {
      setWatchlistSet(new Set());
      return;
    }
    api.watchlist.getWatchlist().then((items) => {
      setWatchlistSet(new Set(items.map((i) => i.movie_id)));
    }).catch((err) => console.error('Failed to load watchlist IDs:', err));
  }, [user]);

  // Fetch movies when params change
  useEffect(() => {
    const fetchCatalog = async () => {
      setLoading(true);
      try {
        const res = await api.movies.getCatalog({
          query: queryFromUrl || undefined,
          genre: genreFromUrl && genreFromUrl !== 'All Genres' ? genreFromUrl : undefined,
          sort_by: sortFromUrl,
          page: pageFromUrl,
          page_size: 20,
        });
        setMovies(res.movies);
        setTotalMovies(res.total);
        setTotalPages(res.total_pages);
      } catch (err) {
        console.error('Failed to fetch movies:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchCatalog();
  }, [queryFromUrl, genreFromUrl, sortFromUrl, pageFromUrl]);

  // Push filter changes to URL
  const updateParams = (newParams: { q?: string; genre?: string; sort?: string; page?: number }) => {
    const p: Record<string, string> = {};
    const q = newParams.q !== undefined ? newParams.q : queryFromUrl;
    const g = newParams.genre !== undefined ? newParams.genre : genreFromUrl;
    const s = newParams.sort !== undefined ? newParams.sort : sortFromUrl;
    const page = newParams.page !== undefined ? newParams.page : 1;

    if (q) p.q = q;
    if (g && g !== 'All Genres') p.genre = g;
    if (s) p.sort = s;
    if (page > 1) p.page = page.toString();

    setSearchParams(p);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateParams({ q: searchInput.trim(), page: 1 });
  };

  const handleGenreChange = (genre: string) => {
    setSelectedGenre(genre);
    updateParams({ genre: genre === 'All Genres' ? '' : genre, page: 1 });
  };

  const handleSortChange = (sort: 'rating' | 'votes' | 'title' | 'year') => {
    setSortBy(sort);
    updateParams({ sort, page: 1 });
  };

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage);
      updateParams({ page: newPage });
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handleWatchlistToggle = (movieId: number, newState: boolean) => {
    setWatchlistSet((prev) => {
      const next = new Set(prev);
      if (newState) next.add(movieId);
      else next.delete(movieId);
      return next;
    });
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-white font-['Space_Grotesk',sans-serif]">
          Movie <span className="text-holo-gradient">Catalog</span>
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Explore all 3,883 canonical MovieLens titles indexed with collaborative latent embeddings
        </p>
      </div>

      {/* Control Bar: Search, Genre, Sort */}
      <div className="p-4 rounded-2xl bg-[#090f24]/80 backdrop-blur-xl border border-cyan-500/20 mb-8 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-3">
          {/* Search Input */}
          <form onSubmit={handleSearchSubmit} className="md:col-span-5 relative">
            <Search className="w-4 h-4 text-cyan-400 absolute left-3.5 top-3" />
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search by title..."
              className="w-full pl-10 pr-4 py-2 rounded-xl bg-white/5 border border-white/10 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-cyan-400"
            />
          </form>

          {/* Genre Dropdown */}
          <div className="md:col-span-4 relative">
            <Filter className="w-4 h-4 text-cyan-400 absolute left-3.5 top-3 pointer-events-none" />
            <select
              value={selectedGenre}
              onChange={(e) => handleGenreChange(e.target.value)}
              className="w-full pl-10 pr-8 py-2 rounded-xl bg-[#070b19] border border-white/10 text-xs text-white focus:outline-none focus:border-cyan-400 appearance-none cursor-pointer"
            >
              {GENRES.map((g) => (
                <option key={g} value={g}>
                  {g}
                </option>
              ))}
            </select>
          </div>

          {/* Sort By Dropdown */}
          <div className="md:col-span-3 relative">
            <ArrowUpDown className="w-4 h-4 text-cyan-400 absolute left-3.5 top-3 pointer-events-none" />
            <select
              value={sortBy}
              onChange={(e) => handleSortChange(e.target.value as any)}
              className="w-full pl-10 pr-8 py-2 rounded-xl bg-[#070b19] border border-white/10 text-xs text-white focus:outline-none focus:border-cyan-400 appearance-none cursor-pointer"
            >
              <option value="votes">Most Rated</option>
              <option value="rating">Highest Rated</option>
              <option value="year">Newest First</option>
              <option value="title">Title (A-Z)</option>
            </select>
          </div>
        </div>

        {/* Results Count */}
        <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-white/5">
          <div>
            Showing <span className="text-cyan-400 font-mono">{movies.length}</span> of{' '}
            <span className="text-white font-mono">{totalMovies.toLocaleString()}</span> movies
          </div>
          <div>
            Page <span className="text-cyan-400 font-mono">{currentPage}</span> of{' '}
            <span className="text-white font-mono">{totalPages}</span>
          </div>
        </div>
      </div>

      {/* Movies Grid */}
      {loading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-5">
          {Array.from({ length: 15 }).map((_, i) => (
            <div key={i} className="aspect-[2/3] rounded-2xl bg-cosmic-800 animate-pulse" />
          ))}
        </div>
      ) : movies.length === 0 ? (
        <div className="text-center py-24 rounded-3xl bg-white/5 border border-white/10">
          <Sparkles className="w-12 h-12 text-cyan-400 mx-auto mb-3 opacity-50" />
          <h3 className="text-lg font-bold text-white">No Movies Found</h3>
          <p className="text-xs text-slate-400 mt-1">Try adjusting your search query or genre filter</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-5">
          {movies.map((movie) => (
            <HolographicMovieCard
              key={movie.movie_id}
              movie={movie}
              inWatchlist={watchlistSet.has(movie.movie_id)}
              onWatchlistToggle={handleWatchlistToggle}
            />
          ))}
        </div>
      )}

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-12">
          <button
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage <= 1}
            className="flex items-center gap-1 px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-xs text-slate-300 hover:bg-white/10 disabled:opacity-30 disabled:pointer-events-none"
          >
            <ChevronLeft className="w-4 h-4" />
            <span>Previous</span>
          </button>

          <span className="px-4 py-2 text-xs font-mono text-cyan-400 bg-cyan-950/40 rounded-xl border border-cyan-500/20">
            {currentPage} / {totalPages}
          </span>

          <button
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage >= totalPages}
            className="flex items-center gap-1 px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-xs text-slate-300 hover:bg-white/10 disabled:opacity-30 disabled:pointer-events-none"
          >
            <span>Next</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
};
