import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Star,
  Bookmark,
  Check,
  Calendar,
  Layers,
  Sparkles,
  ArrowLeft,
  Users,
} from 'lucide-react';
import { Movie, SimilarMovie } from '../types';
import { api } from '../services/api';
import { getSvgPosterDataUrl } from '../services/localCatalog';
import { useAuth } from '../context/AuthContext';
import { StarRating } from '../components/common/StarRating';
import { HolographicMovieCard } from '../components/common/HolographicMovieCard';

export const MovieDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const movieId = parseInt(id || '0', 10);
  const { user, openAuthModal } = useAuth();

  const [movie, setMovie] = useState<Movie | null>(null);
  const [similarMovies, setSimilarMovies] = useState<SimilarMovie[]>([]);
  const [loading, setLoading] = useState(true);
  const [userRating, setUserRating] = useState<number | null>(null);
  const [inWatchlist, setInWatchlist] = useState<boolean>(false);
  const [ratingMessage, setRatingMessage] = useState<string | null>(null);
  const [isSubmittingRating, setIsSubmittingRating] = useState<boolean>(false);

  useEffect(() => {
    if (!movieId) return;

    const fetchMovieDetails = async () => {
      setLoading(true);
      try {
        const [movieData, similarData] = await Promise.all([
          api.movies.getMovie(movieId),
          api.movies.getSimilar(movieId, 6),
        ]);
        setMovie(movieData);
        setSimilarMovies(similarData);
      } catch (err) {
        console.error('Failed to load movie details:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchMovieDetails();

    // Check user rating & watchlist if logged in
    if (user) {
      api.ratings.getMyRatings().then((ratings) => {
        const found = ratings.find((r) => r.movie_id === movieId);
        if (found) setUserRating(found.rating);
      }).catch(console.error);

      api.watchlist.getWatchlist().then((watchlist) => {
        const found = watchlist.some((w) => w.movie_id === movieId);
        setInWatchlist(found);
      }).catch(console.error);
    }
  }, [movieId, user]);

  const handleRatingChange = async (rating: number) => {
    if (!user) {
      openAuthModal('login');
      return;
    }

    setIsSubmittingRating(true);
    setRatingMessage(null);
    try {
      await api.ratings.submitRating(movieId, rating);
      setUserRating(rating);
      setRatingMessage('Rating recorded! Your personalized SVD latent vector has updated.');
    } catch (err) {
      console.error('Failed to submit rating:', err);
      setRatingMessage('Error recording rating.');
    } finally {
      setIsSubmittingRating(false);
    }
  };

  const handleWatchlistToggle = async () => {
    if (!user) {
      openAuthModal('login');
      return;
    }

    const nextState = !inWatchlist;
    try {
      if (nextState) {
        await api.watchlist.addToWatchlist(movieId);
      } else {
        await api.watchlist.removeFromWatchlist(movieId);
      }
      setInWatchlist(nextState);
    } catch (err) {
      console.error('Failed to toggle watchlist:', err);
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-20 text-center">
        <Sparkles className="w-10 h-10 text-cyan-400 animate-spin mx-auto mb-4" />
        <p className="text-slate-400 text-sm">Decoding movie latent vectors...</p>
      </div>
    );
  }

  if (!movie) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-20 text-center">
        <h2 className="text-2xl font-bold text-white mb-2">Movie Not Found</h2>
        <Link to="/catalog" className="text-cyan-400 hover:underline text-sm">
          Return to Catalog
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen pb-20">
      {/* Back Link */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6">
        <Link
          to="/catalog"
          className="inline-flex items-center gap-2 text-xs text-slate-400 hover:text-cyan-300 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Catalog</span>
        </Link>
      </div>

      {/* Main Movie Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="rounded-3xl p-6 sm:p-10 bg-[#090f24]/90 backdrop-blur-2xl border border-cyan-500/20 shadow-neon-cyan grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
          {/* Poster Column */}
          <div className="md:col-span-4 lg:col-span-3">
            <div className="relative aspect-[2/3] rounded-2xl overflow-hidden border border-cyan-400/30 shadow-2xl">
              <img
                src={api.posters.getUrl(movie.movie_id)}
                alt={movie.title}
                className="w-full h-full object-cover"
                onError={(e) => {
                  e.currentTarget.src = getSvgPosterDataUrl(movie.title, movie.year);
                }}
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent pointer-events-none" />
            </div>
          </div>

          {/* Details Column */}
          <div className="md:col-span-8 lg:col-span-9 space-y-6">
            <div>
              <div className="flex flex-wrap items-center gap-2 mb-3">
                {movie.genres.map((genre) => (
                  <span
                    key={genre}
                    className="px-3 py-1 rounded-full text-xs font-semibold bg-cyan-500/10 border border-cyan-500/30 text-cyan-300"
                  >
                    {genre}
                  </span>
                ))}
              </div>

              <h1 className="text-3xl sm:text-5xl font-extrabold text-white font-['Space_Grotesk',sans-serif]">
                {movie.title}
              </h1>

              <div className="flex flex-wrap items-center gap-6 mt-4 text-xs sm:text-sm text-slate-300">
                {movie.year && (
                  <div className="flex items-center gap-1.5">
                    <Calendar className="w-4 h-4 text-cyan-400" />
                    <span>Released in {movie.year}</span>
                  </div>
                )}
                {movie.vote_count !== undefined && (
                  <div className="flex items-center gap-1.5">
                    <Users className="w-4 h-4 text-purple-400" />
                    <span>{movie.vote_count.toLocaleString()} MovieLens Ratings</span>
                  </div>
                )}
                {movie.mean_rating !== undefined && (
                  <div className="flex items-center gap-1.5 text-amber-400 font-bold">
                    <Star className="w-4 h-4 fill-current" />
                    <span>{movie.mean_rating.toFixed(2)} Average Rating</span>
                  </div>
                )}
              </div>
            </div>

            {/* Watchlist Action */}
            <div className="flex flex-wrap items-center gap-4 pt-2">
              <button
                onClick={handleWatchlistToggle}
                className={`flex items-center gap-2 px-6 py-3 rounded-xl font-bold text-xs transition-all ${
                  inWatchlist
                    ? 'bg-cyan-500 text-black shadow-neon-cyan'
                    : 'bg-white/10 text-white hover:bg-white/20 border border-white/20'
                }`}
              >
                {inWatchlist ? (
                  <>
                    <Check className="w-4 h-4 stroke-[3]" />
                    <span>In Your Watchlist</span>
                  </>
                ) : (
                  <>
                    <Bookmark className="w-4 h-4" />
                    <span>Add to Watchlist</span>
                  </>
                )}
              </button>
            </div>

            {/* Interactive Rating Section */}
            <div className="p-5 rounded-2xl bg-white/5 border border-white/10 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4" />
                  Your Rating & SVD Vector Feedback
                </span>
                {userRating && (
                  <span className="text-xs text-amber-300 font-mono">
                    Rated {userRating}.0 ★
                  </span>
                )}
              </div>

              <StarRating
                initialRating={userRating || 0}
                onRatingChange={handleRatingChange}
                readOnly={isSubmittingRating}
                size="lg"
              />

              {isSubmittingRating && (
                <p className="text-xs text-amber-300 animate-pulse">Updating SVD latent factors...</p>
              )}
              {!isSubmittingRating && ratingMessage && (
                <p className="text-xs text-cyan-300 animate-fadeIn">{ratingMessage}</p>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Latent Space Nearest Neighbors (Similar Movies) */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 rounded-xl bg-purple-500/10 border border-purple-500/30 text-purple-400">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white tracking-tight">Similar Movies</h2>
            <p className="text-xs text-slate-400">
              Computed via cosine similarity on 30-dimensional SVD item latent vectors
            </p>
          </div>
        </div>

        {similarMovies.length === 0 ? (
          <p className="text-xs text-slate-400">No latent similarity neighbors found.</p>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {similarMovies.map((sim) => (
              <HolographicMovieCard
                key={sim.movie_id}
                movie={sim}
                showScore={true}
                score={sim.similarity}
                scoreLabel="Sim"
                badge={`${Math.round(sim.similarity * 100)}%`}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
};
