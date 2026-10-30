import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  User as UserIcon,
  Star,
  Trash2,
  Calendar,
  Sparkles,
  PieChart,
} from 'lucide-react';
import { UserRating } from '../types';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';

export const Profile: React.FC = () => {
  const { user, openAuthModal, logout } = useAuth();
  const [ratings, setRatings] = useState<UserRating[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }

    const fetchRatings = async () => {
      setLoading(true);
      try {
        const userRatings = await api.ratings.getMyRatings();
        setRatings(userRatings);
      } catch (err) {
        console.error('Failed to load user ratings:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchRatings();
  }, [user]);

  const handleDeleteRating = async (movieId: number) => {
    try {
      await api.ratings.deleteRating(movieId);
      setRatings((prev) => prev.filter((r) => r.movie_id !== movieId));
    } catch (err) {
      console.error('Failed to delete rating:', err);
    }
  };

  if (!user) {
    return (
      <div className="max-w-xl mx-auto px-4 py-24 text-center">
        <UserIcon className="w-16 h-16 text-cyan-400 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-white mb-2">User Profile</h2>
        <p className="text-xs text-slate-400 mb-6">Please sign in to view your profile and saved ratings.</p>
        <button
          onClick={() => openAuthModal('login')}
          className="px-6 py-2.5 rounded-full bg-cyan-400 text-black font-bold text-xs"
        >
          Sign In
        </button>
      </div>
    );
  }

  // Calculate statistics
  const totalRatings = ratings.length;
  const avgRating =
    totalRatings > 0
      ? (ratings.reduce((sum, r) => sum + r.rating, 0) / totalRatings).toFixed(2)
      : '0.00';

  // Genre breakdown
  const genreCounts: Record<string, number> = {};
  ratings.forEach((r) => {
    r.genres?.forEach((g) => {
      genreCounts[g] = (genreCounts[g] || 0) + 1;
    });
  });

  const sortedGenres = Object.entries(genreCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Profile Overview Card */}
      <div className="rounded-3xl p-6 sm:p-8 bg-[#090f24]/90 backdrop-blur-xl border border-cyan-500/20 shadow-neon-cyan flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="flex items-center gap-5">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-cyan-400 to-purple-600 flex items-center justify-center text-black font-bold text-2xl shadow-md">
            {user.username.charAt(0).toUpperCase()}
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white">{user.username}</h1>
            <p className="text-xs text-slate-400">{user.email}</p>
            <div className="flex items-center gap-2 mt-2 text-[11px] text-cyan-400 font-mono">
              <Calendar className="w-3.5 h-3.5" />
              <span>Member since {new Date(user.created_at).toLocaleDateString()}</span>
            </div>
          </div>
        </div>

        <button
          onClick={logout}
          className="px-5 py-2 rounded-xl bg-white/5 border border-white/10 text-xs text-rose-400 hover:bg-rose-500/10 hover:border-rose-500/30 transition-colors"
        >
          Sign Out
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-5 rounded-2xl bg-white/5 border border-white/10">
          <div className="text-xs text-slate-400">Total Rated Titles</div>
          <div className="text-3xl font-extrabold text-white font-mono mt-1">{totalRatings}</div>
          <div className="text-[10px] text-cyan-400 mt-1">SVD folding-in sample basis</div>
        </div>

        <div className="p-5 rounded-2xl bg-white/5 border border-white/10">
          <div className="text-xs text-slate-400">Average Rating Given</div>
          <div className="text-3xl font-extrabold text-amber-400 font-mono mt-1 flex items-center gap-1.5">
            <Star className="w-6 h-6 fill-current" />
            <span>{avgRating}</span>
          </div>
          <div className="text-[10px] text-slate-400 mt-1">Out of 5.0 stars</div>
        </div>

        <div className="p-5 rounded-2xl bg-white/5 border border-white/10">
          <div className="text-xs text-slate-400 flex items-center gap-1">
            <PieChart className="w-3.5 h-3.5 text-purple-400" />
            <span>Top Taste Genres</span>
          </div>
          <div className="flex flex-wrap gap-1.5 mt-2">
            {sortedGenres.length > 0 ? (
              sortedGenres.map(([genre, count]) => (
                <span
                  key={genre}
                  className="px-2 py-0.5 rounded-md bg-purple-500/20 text-purple-300 text-xs font-mono"
                >
                  {genre} ({count})
                </span>
              ))
            ) : (
              <span className="text-xs text-slate-500">No ratings yet</span>
            )}
          </div>
        </div>
      </div>

      {/* Rated Movies List */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-cyan-400" />
            <span>Your Rated Movies ({ratings.length})</span>
          </h2>
          {ratings.length === 0 && (
            <Link to="/catalog" className="text-xs text-cyan-400 hover:underline">
              Browse Catalog to Rate Films
            </Link>
          )}
        </div>

        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-16 rounded-xl bg-white/5 animate-pulse" />
            ))}
          </div>
        ) : ratings.length === 0 ? (
          <div className="text-center py-16 rounded-2xl bg-white/5 border border-white/10">
            <p className="text-xs text-slate-400">
              You haven't rated any movies yet. Explore the catalog or use the Profile Builder!
            </p>
          </div>
        ) : (
          <div className="divide-y divide-white/5 rounded-2xl bg-[#090f24]/80 border border-white/10 overflow-hidden">
            {ratings.map((item) => (
              <div
                key={item.id}
                className="p-4 flex items-center justify-between hover:bg-white/5 transition-colors gap-4"
              >
                <div className="flex items-center gap-4 min-w-0">
                  <div className="w-10 h-14 rounded-lg overflow-hidden bg-black flex-shrink-0">
                    <img
                      src={api.posters.getUrl(item.movie_id)}
                      alt={item.movie_title || ''}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <div className="min-w-0">
                    <Link
                      to={`/movies/${item.movie_id}`}
                      className="text-sm font-semibold text-white hover:text-cyan-300 transition-colors truncate block"
                    >
                      {item.movie_title || `Movie #${item.movie_id}`}
                    </Link>
                    <div className="flex items-center gap-2 text-xs text-slate-400 mt-0.5">
                      {item.genres?.slice(0, 3).join(', ')}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-6 flex-shrink-0">
                  <div className="flex items-center text-amber-400 font-bold text-sm">
                    <Star className="w-4 h-4 fill-current mr-1" />
                    <span>{item.rating.toFixed(1)}</span>
                  </div>

                  <button
                    onClick={() => handleDeleteRating(item.movie_id)}
                    title="Delete Rating"
                    className="p-2 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-white/5 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
