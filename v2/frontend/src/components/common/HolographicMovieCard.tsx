import React, { useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import { Star, Bookmark, Check, Sparkles } from 'lucide-react';
import { Movie } from '../../types';
import { api } from '../../services/api';
import { useAuth } from '../../context/AuthContext';

interface HolographicMovieCardProps {
  movie: Movie;
  inWatchlist?: boolean;
  onWatchlistToggle?: (movieId: number, newState: boolean) => void;
  showScore?: boolean;
  score?: number;
  scoreLabel?: string;
  badge?: string;
}

export const HolographicMovieCard: React.FC<HolographicMovieCardProps> = ({
  movie,
  inWatchlist = false,
  onWatchlistToggle,
  showScore = false,
  score,
  scoreLabel,
  badge,
}) => {
  const { user, openAuthModal } = useAuth();
  const [isSaved, setIsSaved] = useState<boolean>(inWatchlist);
  const [isToggling, setIsToggling] = useState<boolean>(false);
  const [posterLoaded, setPosterLoaded] = useState<boolean>(false);
  const [posterError, setPosterError] = useState<boolean>(false);

  // 3D Tilt calculation
  const cardRef = useRef<HTMLDivElement>(null);
  const [transformStyle, setTransformStyle] = useState<string>('');
  const [glareStyle, setGlareStyle] = useState<{ x: number; y: number; opacity: number }>({
    x: 50,
    y: 50,
    opacity: 0,
  });

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    const rotateX = ((y - centerY) / centerY) * -12;
    const rotateY = ((x - centerX) / centerX) * 12;

    setTransformStyle(
      `perspective(1000px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) scale3d(1.03, 1.03, 1.03)`
    );
    setGlareStyle({
      x: (x / rect.width) * 100,
      y: (y / rect.height) * 100,
      opacity: 0.35,
    });
  };

  const handleMouseLeave = () => {
    setTransformStyle('perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)');
    setGlareStyle((prev) => ({ ...prev, opacity: 0 }));
  };

  const handleToggleWatchlist = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (!user) {
      openAuthModal('login');
      return;
    }

    if (isToggling) return;
    setIsToggling(true);
    const targetState = !isSaved;

    try {
      if (targetState) {
        await api.watchlist.addToWatchlist(movie.movie_id);
      } else {
        await api.watchlist.removeFromWatchlist(movie.movie_id);
      }
      setIsSaved(targetState);
      if (onWatchlistToggle) {
        onWatchlistToggle(movie.movie_id, targetState);
      }
    } catch (err) {
      console.error('Failed to update watchlist:', err);
    } finally {
      setIsToggling(false);
    }
  };

  const posterUrl = api.posters.getUrl(movie.movie_id);

  return (
    <div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{
        transform: transformStyle,
        transition: 'transform 0.15s ease-out',
        transformStyle: 'preserve-3d',
      }}
      className="relative group rounded-2xl p-[1px] bg-gradient-to-b from-cyan-500/25 via-violet-500/15 to-transparent hover:from-cyan-400/60 hover:via-purple-500/40 hover:to-pink-500/30 transition-all duration-300 shadow-lg hover:shadow-card-hover"
    >
      {/* Glare effect overlay */}
      <div
        className="absolute inset-0 rounded-2xl pointer-events-none transition-opacity duration-300 z-20"
        style={{
          background: `radial-gradient(circle at ${glareStyle.x}% ${glareStyle.y}%, rgba(0, 242, 254, ${glareStyle.opacity}) 0%, transparent 60%)`,
        }}
      />

      <div className="relative rounded-2xl bg-[#090f24]/90 backdrop-blur-md overflow-hidden flex flex-col h-full border border-cyan-500/10 group-hover:border-cyan-400/30 transition-colors">
        {/* Poster Container */}
        <Link to={`/movies/${movie.movie_id}`} className="relative aspect-[2/3] w-full overflow-hidden block">
          {/* Skeleton placeholder while loading */}
          {!posterLoaded && (
            <div className="absolute inset-0 bg-cosmic-800 animate-pulse flex items-center justify-center">
              <Sparkles className="w-8 h-8 text-cyan-400/30" />
            </div>
          )}

          <img
            src={posterError ? `/api/v1/posters/${movie.movie_id}?placeholder=true` : posterUrl}
            alt={movie.title}
            loading="lazy"
            onLoad={() => setPosterLoaded(true)}
            onError={() => {
              if (!posterError) {
                setPosterError(true);
              } else {
                setPosterLoaded(true);
              }
            }}
            className={`w-full h-full object-cover transition-transform duration-500 group-hover:scale-105 ${
              posterLoaded ? 'opacity-100' : 'opacity-0'
            }`}
          />

          {/* Hologram gradient shadow at bottom of poster */}
          <div className="absolute inset-0 bg-gradient-to-t from-[#090f24] via-transparent to-black/30" />

          {/* Badge (e.g. Featured, Similar 95%, Rank) */}
          {badge && (
            <div className="absolute top-2.5 left-2.5 px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider bg-gradient-to-r from-cyan-500 to-purple-600 text-white shadow-md">
              {badge}
            </div>
          )}

          {/* Watchlist Quick Button */}
          <button
            onClick={handleToggleWatchlist}
            disabled={isToggling}
            aria-label={isSaved ? 'Remove from Watchlist' : 'Add to Watchlist'}
            className={`absolute top-2.5 right-2.5 p-2 rounded-xl backdrop-blur-md transition-all duration-200 z-10 ${
              isSaved
                ? 'bg-cyan-500 text-black shadow-neon-cyan'
                : 'bg-black/50 text-slate-300 hover:text-white hover:bg-black/75 border border-white/10'
            }`}
          >
            {isSaved ? <Check className="w-4 h-4 stroke-[3]" /> : <Bookmark className="w-4 h-4" />}
          </button>

          {/* Score Badge (for recommendations or similarity) */}
          {showScore && score !== undefined && (
            <div className="absolute bottom-2.5 left-2.5 px-2 py-0.5 rounded-md text-xs font-bold bg-cyan-950/80 border border-cyan-400/40 text-cyan-300 backdrop-blur-md">
              {scoreLabel ? `${scoreLabel}: ` : ''}
              {typeof score === 'number' ? score.toFixed(2) : score}
            </div>
          )}
        </Link>

        {/* Content Info */}
        <div className="p-3.5 flex flex-col flex-grow justify-between">
          <div>
            <Link
              to={`/movies/${movie.movie_id}`}
              className="text-sm font-semibold text-slate-100 group-hover:text-cyan-300 transition-colors line-clamp-1"
              title={movie.title}
            >
              {movie.title}
            </Link>

            <div className="flex items-center gap-2 mt-1.5 text-xs text-slate-400">
              {movie.year && <span>{movie.year}</span>}
              {movie.mean_rating !== undefined && (
                <div className="flex items-center text-amber-400 font-medium ml-auto">
                  <Star className="w-3.5 h-3.5 fill-current mr-1" />
                  <span>{movie.mean_rating.toFixed(1)}</span>
                </div>
              )}
            </div>
          </div>

          {/* Genres pills */}
          <div className="flex flex-wrap gap-1 mt-2.5">
            {movie.genres.slice(0, 2).map((g) => (
              <span
                key={g}
                className="text-[10px] px-2 py-0.5 rounded-md bg-white/5 border border-white/5 text-slate-300 group-hover:border-cyan-500/20"
              >
                {g}
              </span>
            ))}
            {movie.genres.length > 2 && (
              <span className="text-[10px] px-1.5 py-0.5 rounded-md bg-white/5 text-slate-400">
                +{movie.genres.length - 2}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
