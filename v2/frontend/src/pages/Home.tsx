import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Sparkles,
  Search,
  Flame,
  ArrowRight,
  Sliders,
  Users,
  Compass,
  Database,
  Star,
  Play,
} from 'lucide-react';
import { Movie } from '../types';
import { api } from '../services/api';
import { CosmicHeroCanvas } from '../components/3d/CosmicHeroCanvas';
import { FeaturedCardHoloStage } from '../components/3d/FeaturedCardHoloStage';
import { HolographicMovieCard } from '../components/common/HolographicMovieCard';

const GENRE_PILLS = [
  'Action',
  'Adventure',
  'Comedy',
  'Drama',
  'Sci-Fi',
  'Thriller',
  'Romance',
  'Horror',
];

export const Home: React.FC = () => {
  const [trendingMovies, setTrendingMovies] = useState<Movie[]>([]);
  const [featuredMovie, setFeaturedMovie] = useState<Movie | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [trending, fcMovie] = await Promise.all([
          api.movies.getTrending(10),
          // Specifically load Fight Club (1999) - MovieLens 1M ID 2959 as featured champion
          api.movies.getMovie(2959).catch(() => null),
        ]);
        setTrendingMovies(trending);
        if (fcMovie) {
          setFeaturedMovie(fcMovie);
        } else if (trending.length > 0) {
          const featured =
            trending.find((m) => m.title.includes('Fight Club')) || trending[0];
          setFeaturedMovie(featured);
        }
      } catch (err) {
        console.error('Failed to load homepage trending movies:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/catalog?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden pb-20">
      {/* 3D Cosmic Background Canvas */}
      <CosmicHeroCanvas className="h-[750px] opacity-90" />

      {/* Hero Section Container */}
      <section className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-10 sm:pt-16 pb-12 z-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          {/* Left Column: Heading, Search & Quick Filters */}
          <div className="lg:col-span-7 space-y-6">
            <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-semibold tracking-wide uppercase shadow-neon-cyan">
              <Sparkles className="w-3.5 h-3.5 animate-pulse" />
              <span>AI-Powered Recommendations</span>
            </div>

            <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight leading-none text-white font-['Space_Grotesk',sans-serif]">
              Discover Your Next <br />
              <span className="text-holo-gradient">Favourite Movie</span>
            </h1>

            <p className="text-slate-300 text-sm sm:text-base max-w-xl leading-relaxed">
              Experience next-generation cinematic discovery with Truncated SVD matrix factorization,
              real-time latent profile folding, and interactive 3D universe exploration.
            </p>

            {/* Large Search Bar */}
            <form onSubmit={handleSearch} className="relative max-w-xl">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search for a movie, e.g. Inception, Matrix, Jurassic Park..."
                className="w-full pl-5 pr-14 py-4 rounded-2xl bg-[#090f24]/90 border border-cyan-500/30 text-white placeholder-slate-400 text-sm focus:outline-none focus:border-cyan-400 focus:shadow-neon-cyan backdrop-blur-xl transition-all"
              />
              <button
                type="submit"
                aria-label="Search Catalog"
                className="absolute right-2.5 top-2.5 bottom-2.5 px-4 rounded-xl bg-gradient-to-r from-cyan-400 to-purple-600 text-black font-bold flex items-center justify-center hover:opacity-90 shadow-md transition-all"
              >
                <Search className="w-4 h-4" />
              </button>
            </form>

            {/* Quick Genre Chips */}
            <div className="flex flex-wrap gap-2 pt-2">
              {GENRE_PILLS.map((genre) => (
                <button
                  key={genre}
                  onClick={() => navigate(`/catalog?genre=${encodeURIComponent(genre)}`)}
                  className={`px-3.5 py-1.5 rounded-full text-xs font-medium backdrop-blur-md transition-all ${
                    genre === 'Drama'
                      ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white border border-purple-400/50 shadow-[0_0_15px_rgba(168,85,247,0.4)]'
                      : 'bg-white/5 border border-white/10 hover:border-cyan-400 hover:text-cyan-300 hover:bg-cyan-950/40 text-slate-300'
                  }`}
                >
                  {genre}
                </button>
              ))}
            </div>
          </div>

          {/* Right Column: 3D Featured Hologram Card with Holographic Stage */}
          <div className="lg:col-span-5 flex justify-center items-center relative py-6 px-2 sm:px-4">
            {/* 3D Holographic Stage (Positioned BEHIND and AROUND the card) */}
            <div className="absolute inset-0 -inset-x-8 sm:-inset-x-14 -inset-y-6 sm:-inset-y-10 z-0 pointer-events-none">
              <FeaturedCardHoloStage />
            </div>

            {/* Featured Movie Card in Foreground */}
            {featuredMovie && (
              <div className="relative z-20 w-full max-w-[430px] rounded-[28px] p-1 bg-gradient-to-tr from-cyan-400/80 via-purple-500/40 to-pink-500/60 shadow-[0_0_50px_rgba(0,242,254,0.35)] transform hover:-translate-y-1.5 transition-all duration-300">
                <div className="rounded-[24px] bg-[#070b19]/95 backdrop-blur-2xl p-5 sm:p-6 border border-cyan-400/30 overflow-hidden shadow-2xl">
                  {/* Poster / Backdrop Image Container */}
                  <div className="relative aspect-[16/10] rounded-2xl overflow-hidden mb-4 border border-white/10 bg-slate-900 shadow-inner">
                    <img
                      src={api.posters.getUrl(featuredMovie.movie_id, { backdrop: true })}
                      alt={featuredMovie.title}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        const target = e.currentTarget;
                        if (!target.src.includes('placeholder=true')) {
                          target.src = `/api/v1/posters/${featuredMovie.movie_id}?placeholder=true`;
                        }
                      }}
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent pointer-events-none" />
                    <div className="absolute top-3 left-3 px-3 py-1 rounded-full text-[11px] font-extrabold uppercase tracking-wider bg-purple-600 text-white shadow-lg">
                      FEATURED
                    </div>
                  </div>

                  {/* Title */}
                  <h3 className="text-2xl font-bold text-white tracking-tight line-clamp-1 font-['Space_Grotesk',sans-serif]">
                    {featuredMovie.title}
                  </h3>

                  {/* Release Year & Genres */}
                  <div className="flex items-center gap-2 mt-2 text-xs sm:text-sm text-slate-300 font-medium">
                    {featuredMovie.year && <span>({featuredMovie.year})</span>}
                    <span className="text-slate-500">•</span>
                    <span className="text-cyan-400 font-semibold">
                      {featuredMovie.movie_id === 2959
                        ? 'Drama, Thriller'
                        : featuredMovie.genres.join(', ') || 'Drama'}
                    </span>
                  </div>

                  {/* Rating & Explore Action Button */}
                  <div className="flex items-center justify-between mt-5 pt-4 border-t border-white/10">
                    <div className="flex items-center text-amber-400 font-bold text-base">
                      <Star className="w-5 h-5 fill-current mr-2 text-amber-400" />
                      <span>
                        {featuredMovie.movie_id === 2959
                          ? '4.3/5.0'
                          : `${featuredMovie.mean_rating?.toFixed(1) || '4.2'}/5.0`}
                      </span>
                    </div>

                    <Link
                      to={`/movies/${featuredMovie.movie_id}`}
                      className="inline-flex items-center gap-2 px-6 py-2.5 rounded-full bg-gradient-to-r from-cyan-400 to-teal-300 hover:from-cyan-300 hover:to-teal-200 text-black text-sm font-extrabold shadow-[0_0_20px_rgba(0,242,254,0.4)] transition-all transform hover:scale-105"
                    >
                      <Play className="w-4 h-4 fill-current" />
                      <span>Explore Movie</span>
                    </Link>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Trending Movies Carousel */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 relative z-10">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-gradient-to-tr from-amber-500 to-rose-500 text-black shadow-md">
              <Flame className="w-5 h-5 fill-current" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white tracking-tight">Trending Now</h2>
              <p className="text-xs text-slate-400">Most engaged titles across MovieLens 1M</p>
            </div>
          </div>

          <Link
            to="/catalog?sort=votes"
            className="flex items-center gap-1 text-xs font-semibold text-cyan-400 hover:text-cyan-300 transition-colors"
          >
            <span>View All</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {/* Horizontal Carousel */}
        {loading ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="aspect-[2/3] rounded-2xl bg-cosmic-800 animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-5">
            {trendingMovies.slice(0, 5).map((movie) => (
              <HolographicMovieCard key={movie.movie_id} movie={movie} />
            ))}
          </div>
        )}
      </section>

      {/* Three Main Feature Gateways (Matching Holographic Reference UI) */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 relative z-10">
        <div className="text-center max-w-2xl mx-auto mb-10">
          <h2 className="text-3xl font-extrabold text-white tracking-tight">
            Next-Gen <span className="text-holo-gradient">Discovery Gateways</span>
          </h2>
          <p className="text-xs text-slate-400 mt-2">
            Three interactive recommendation modalities powered by Truncated SVD matrix factorization
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1: Profile Builder */}
          <div className="relative rounded-3xl p-6 bg-[#090f24]/80 backdrop-blur-xl border border-cyan-500/20 hover:border-cyan-400/50 hover:shadow-neon-cyan transition-all group">
            <div className="w-12 h-12 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 mb-4 group-hover:scale-110 transition-transform">
              <Sliders className="w-6 h-6" />
            </div>
            <div className="text-xs font-bold text-cyan-400 tracking-wider uppercase mb-1">01 / Engine</div>
            <h3 className="text-xl font-bold text-white mb-2">Profile Builder</h3>
            <p className="text-xs text-slate-400 leading-relaxed mb-6">
              Rate your favourite films interactively. Our online folding-in projection derives your 30-dimensional
              latent vector in &lt;3ms to surface instant recommendations without retraining.
            </p>
            <Link
              to="/profile-builder"
              className="inline-flex items-center gap-2 text-xs font-bold text-cyan-300 hover:text-white"
            >
              <span>Build Taste Profile</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>

          {/* Card 2: Historical User Inspector */}
          <div className="relative rounded-3xl p-6 bg-[#090f24]/80 backdrop-blur-xl border border-purple-500/20 hover:border-purple-400/50 hover:shadow-neon-violet transition-all group">
            <div className="w-12 h-12 rounded-2xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400 mb-4 group-hover:scale-110 transition-transform">
              <Users className="w-6 h-6" />
            </div>
            <div className="text-xs font-bold text-purple-400 tracking-wider uppercase mb-1">02 / Explorer</div>
            <h3 className="text-xl font-bold text-white mb-2">Historical User Inspector</h3>
            <p className="text-xs text-slate-400 leading-relaxed mb-6">
              Inspect any of the 6,040 real MovieLens personas. Compare their historical taste footprints
              against model predicted rankings to evaluate collaborative filtering behavior.
            </p>
            <Link
              to="/recommendations?inspector=true"
              className="inline-flex items-center gap-2 text-xs font-bold text-purple-300 hover:text-white"
            >
              <span>Inspect User Personas</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>

          {/* Card 3: Similarity Explorer */}
          <div className="relative rounded-3xl p-6 bg-[#090f24]/80 backdrop-blur-xl border border-pink-500/20 hover:border-pink-400/50 hover:shadow-lg transition-all group">
            <div className="w-12 h-12 rounded-2xl bg-pink-500/10 border border-pink-500/30 flex items-center justify-center text-pink-400 mb-4 group-hover:scale-110 transition-transform">
              <Compass className="w-6 h-6" />
            </div>
            <div className="text-xs font-bold text-pink-400 tracking-wider uppercase mb-1">03 / Latent Space</div>
            <h3 className="text-xl font-bold text-white mb-2">Similarity Explorer</h3>
            <p className="text-xs text-slate-400 leading-relaxed mb-6">
              Traverse the 30-dimensional SVD item space using cosine similarity. Discover movies with
              parallel directorial style, thematic tone, and audience affinity.
            </p>
            <Link
              to="/catalog"
              className="inline-flex items-center gap-2 text-xs font-bold text-pink-300 hover:text-white"
            >
              <span>Browse 3,883 Movies</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        </div>
      </section>

      {/* Dataset & Architecture Footprint Banner */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 relative z-10">
        <div className="rounded-3xl p-6 bg-gradient-to-r from-cosmic-900 via-cosmic-850 to-cosmic-900 border border-cyan-500/20 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
              <Database className="w-6 h-6" />
            </div>
            <div>
              <div className="text-sm font-bold text-white">MovieLens 1M Production Engine</div>
              <div className="text-xs text-slate-400">
                1,000,209 Chronological Ratings • 3,883 Catalog Titles • Truncated SVD (k=30, seed=42)
              </div>
            </div>
          </div>

          <div className="flex items-center gap-6 text-xs text-slate-300 font-mono">
            <div>
              <span className="text-cyan-400 font-bold block text-base">0.0802</span>
              Test NDCG@10
            </div>
            <div className="h-8 w-px bg-white/10" />
            <div>
              <span className="text-purple-400 font-bold block text-base">1.0657</span>
              Test RMSE
            </div>
            <div className="h-8 w-px bg-white/10" />
            <div>
              <span className="text-teal-400 font-bold block text-base">&lt; 3 ms</span>
              Latency
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
