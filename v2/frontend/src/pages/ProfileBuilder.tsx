import React, { useEffect, useState } from 'react';
import { Sliders, Sparkles, RefreshCw, Zap } from 'lucide-react';
import { Movie, RecommendedMovie } from '../types';
import { api } from '../services/api';
import { StarRating } from '../components/common/StarRating';
import { HolographicMovieCard } from '../components/common/HolographicMovieCard';

export const ProfileBuilder: React.FC = () => {
  const [sampleMovies, setSampleMovies] = useState<Movie[]>([]);
  const [userRatings, setUserRatings] = useState<Record<number, number>>({});
  const [recommendations, setRecommendations] = useState<RecommendedMovie[]>([]);
  const [loadingSamples, setLoadingSamples] = useState<boolean>(true);
  const [calculating, setCalculating] = useState<boolean>(false);
  const [modelMeta, setModelMeta] = useState<{ model_name?: string; strategy?: string }>({});

  useEffect(() => {
    // Fetch a diverse set of 12 highly-rated / popular movies for calibration
    const fetchSamples = async () => {
      setLoadingSamples(true);
      try {
        const topMovies = await api.movies.getTrending(12);
        setSampleMovies(topMovies);
      } catch (err) {
        console.error('Failed to load calibration movies:', err);
      } finally {
        setLoadingSamples(false);
      }
    };
    fetchSamples();
  }, []);

  const handleRate = (movieId: number, rating: number) => {
    setUserRatings((prev) => ({
      ...prev,
      [movieId]: rating,
    }));
  };

  const ratedCount = Object.keys(userRatings).length;

  const handleCalculateRecs = async () => {
    if (ratedCount === 0) return;
    setCalculating(true);
    try {
      const payload = Object.entries(userRatings).map(([id, rating]) => ({
        movie_id: parseInt(id, 10),
        rating,
      }));
      const res = await api.recommendations.getProfileBuilder(payload, 12);
      setRecommendations(res.items);
      setModelMeta({ model_name: res.model_name, strategy: res.strategy });
    } catch (err) {
      console.error('Failed to calculate folded recommendations:', err);
    } finally {
      setCalculating(false);
    }
  };

  const handleReset = () => {
    setUserRatings({});
    setRecommendations([]);
    setModelMeta({});
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-teal-500/10 border border-teal-500/30 text-teal-400 text-xs font-semibold uppercase tracking-wider mb-2">
          <Zap className="w-3.5 h-3.5 animate-pulse" />
          <span>Interactive Cold-Start Calibration</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-white font-['Space_Grotesk',sans-serif]">
          Profile <span className="text-holo-gradient">Builder</span>
        </h1>
        <p className="text-xs text-slate-400 mt-1 max-w-2xl">
          Rate 3 or more movies below. Our recommendation engine projects your ratings onto the
          30-dimensional SVD item matrix in real time to generate instant collaborative filtering recommendations.
        </p>
      </div>

      {/* Control Banner */}
      <div className="p-5 rounded-2xl bg-[#090f24]/90 backdrop-blur-xl border border-teal-500/30 mb-8 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <span className="text-sm font-bold text-white">Your Calibration Progress: </span>
          <span className="text-sm font-mono text-teal-300 font-bold">
            {ratedCount} {ratedCount === 1 ? 'movie' : 'movies'} rated
          </span>
          <p className="text-xs text-slate-400 mt-0.5">
            {ratedCount >= 3
              ? 'Ready for SVD projection!'
              : `Rate ${3 - ratedCount} more movie${3 - ratedCount > 1 ? 's' : ''} to unlock high-accuracy SVD.`}
          </p>
        </div>

        <div className="flex items-center gap-3">
          {ratedCount > 0 && (
            <button
              onClick={handleReset}
              className="p-2.5 rounded-xl text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
              title="Reset Ratings"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          )}

          <button
            onClick={handleCalculateRecs}
            disabled={ratedCount === 0 || calculating}
            className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-teal-400 via-cyan-400 to-purple-500 text-black font-bold text-xs hover:shadow-neon-cyan disabled:opacity-40 disabled:pointer-events-none transition-all"
          >
            <Sliders className="w-4 h-4" />
            <span>{calculating ? 'Projecting SVD Vector...' : 'Generate SVD Recommendations'}</span>
          </button>
        </div>
      </div>

      {/* Calibration Movie Grid */}
      <div className="mb-12">
        <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <span>Rate Sample Movies</span>
          <span className="text-xs text-slate-400 font-normal">(Click stars to set your rating)</span>
        </h2>

        {loadingSamples ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {Array.from({ length: 12 }).map((_, i) => (
              <div key={i} className="aspect-[2/3] rounded-2xl bg-cosmic-800 animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {sampleMovies.map((movie) => {
              const currentRating = userRatings[movie.movie_id] || 0;
              return (
                <div
                  key={movie.movie_id}
                  className="rounded-2xl p-3 bg-white/5 border border-white/10 flex flex-col justify-between"
                >
                  <div className="aspect-[2/3] rounded-xl overflow-hidden mb-3 bg-black">
                    <img
                      src={api.posters.getUrl(movie.movie_id)}
                      alt={movie.title}
                      className="w-full h-full object-cover"
                    />
                  </div>

                  <div>
                    <h4 className="text-xs font-semibold text-white line-clamp-1 mb-1" title={movie.title}>
                      {movie.title}
                    </h4>
                    <p className="text-[10px] text-slate-400 line-clamp-1 mb-2">
                      {movie.genres.join(', ')}
                    </p>
                    <StarRating
                      initialRating={currentRating}
                      onRatingChange={(r) => handleRate(movie.movie_id, r)}
                      size="sm"
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Generated Recommendations Section */}
      {recommendations.length > 0 && (
        <div className="pt-8 border-t border-cyan-500/20 animate-fadeIn">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-white tracking-tight">Your Custom Recommendations</h2>
                <p className="text-xs text-slate-400">
                  Calculated via online SVD folding-in ({modelMeta.model_name || 'svd_k30'})
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {recommendations.map((rec, index) => (
              <HolographicMovieCard
                key={rec.movie_id}
                movie={rec}
                showScore={true}
                score={rec.score}
                scoreLabel="Pred"
                badge={`#${index + 1}`}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
