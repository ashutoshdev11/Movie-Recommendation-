import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Bookmark, Sparkles, Trash2, ArrowRight } from 'lucide-react';
import { WatchlistItem } from '../types';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { HolographicMovieCard } from '../components/common/HolographicMovieCard';

export const Watchlist: React.FC = () => {
  const { user, openAuthModal } = useAuth();
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }

    const fetchWatchlist = async () => {
      setLoading(true);
      try {
        const list = await api.watchlist.getWatchlist();
        setItems(list);
      } catch (err) {
        console.error('Failed to load watchlist:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchWatchlist();
  }, [user]);

  const handleRemove = async (movieId: number) => {
    try {
      await api.watchlist.removeFromWatchlist(movieId);
      setItems((prev) => prev.filter((item) => item.movie_id !== movieId));
    } catch (err) {
      console.error('Failed to remove from watchlist:', err);
    }
  };

  if (!user) {
    return (
      <div className="max-w-xl mx-auto px-4 py-24 text-center">
        <div className="w-16 h-16 rounded-3xl bg-pink-500/10 border border-pink-500/30 flex items-center justify-center text-pink-400 mx-auto mb-4">
          <Bookmark className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">Save Your Cinematic Journey</h2>
        <p className="text-xs text-slate-400 mb-6">
          Sign in to curate your personal watchlist and synchronize it across your devices.
        </p>
        <button
          onClick={() => openAuthModal('login')}
          className="px-6 py-3 rounded-full bg-gradient-to-r from-cyan-400 to-purple-600 text-black font-bold text-xs hover:shadow-neon-cyan transition-all"
        >
          Sign In or Register
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white font-['Space_Grotesk',sans-serif]">
            My <span className="text-holo-gradient">Watchlist</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            {items.length} {items.length === 1 ? 'film' : 'films'} queued for viewing
          </p>
        </div>

        <Link
          to="/catalog"
          className="flex items-center gap-1.5 text-xs font-semibold text-cyan-400 hover:text-cyan-300"
        >
          <span>Explore More</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      {loading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-5">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="aspect-[2/3] rounded-2xl bg-cosmic-800 animate-pulse" />
          ))}
        </div>
      ) : items.length === 0 ? (
        <div className="text-center py-24 rounded-3xl bg-white/5 border border-white/10">
          <Sparkles className="w-12 h-12 text-pink-400 mx-auto mb-3 opacity-50" />
          <h3 className="text-lg font-bold text-white">Your Watchlist is Empty</h3>
          <p className="text-xs text-slate-400 mt-1 mb-6">
            Click the bookmark icon on any movie card in the catalog to add it here
          </p>
          <Link
            to="/catalog"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-cyan-500 text-black text-xs font-bold hover:shadow-neon-cyan transition-all"
          >
            Browse Movies
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-5">
          {items.map((item) => (
            <div key={item.id} className="relative group">
              <HolographicMovieCard
                movie={{
                  movie_id: item.movie_id,
                  title: item.movie_title || `Movie #${item.movie_id}`,
                  genres: item.genres || [],
                  year: item.year || null,
                  mean_rating: item.mean_rating || undefined,
                }}
                inWatchlist={true}
                onWatchlistToggle={(id) => handleRemove(id)}
              />

              <button
                onClick={() => handleRemove(item.movie_id)}
                title="Remove from Watchlist"
                className="absolute -top-2 -right-2 p-1.5 rounded-full bg-rose-600/90 text-white shadow-md hover:bg-rose-500 transition-colors z-30 opacity-0 group-hover:opacity-100"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
