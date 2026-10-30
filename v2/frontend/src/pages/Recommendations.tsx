import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import {
  Sparkles,
  Users,
  Search,
  Sliders,
  CheckCircle2,
  Info,
} from 'lucide-react';
import { RecommendedMovie } from '../types';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { HolographicMovieCard } from '../components/common/HolographicMovieCard';

export const Recommendations: React.FC = () => {
  const [searchParams] = useSearchParams();
  const inspectorParam = searchParams.get('inspector') === 'true';
  const initialUserId = searchParams.get('user_id') || '1';

  const { user, openAuthModal } = useAuth();
  const [activeTab, setActiveTab] = useState<'me' | 'inspector'>(
    inspectorParam ? 'inspector' : 'me'
  );

  // Recommendations state
  const [recs, setRecs] = useState<RecommendedMovie[]>([]);
  const [strategy, setStrategy] = useState<string>('');
  const [modelName, setModelName] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);

  // Inspector state
  const [inspectorUserId, setInspectorUserId] = useState<string>(initialUserId);
  const [searchedUserId, setSearchedUserId] = useState<number>(parseInt(initialUserId, 10));

  useEffect(() => {
    const fetchRecs = async () => {
      setLoading(true);
      try {
        if (activeTab === 'me') {
          if (user) {
            const data = await api.recommendations.getPersonalized(12);
            setRecs(data.items);
            setStrategy(data.strategy);
            setModelName(data.model_name);
          } else {
            // Unauthenticated: fetch fallback popular
            const data = await api.recommendations.getHistoricalUser(1, 12);
            setRecs(data.items);
            setStrategy('popularity_fallback');
            setModelName('damped_popularity_m50');
          }
        } else {
          // Inspector mode
          const data = await api.recommendations.getHistoricalUser(searchedUserId, 12);
          setRecs(data.items);
          setStrategy(data.strategy);
          setModelName('svd_k30');
        }
      } catch (err) {
        console.error('Failed to load recommendations:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchRecs();
  }, [activeTab, user, searchedUserId]);

  const handleInspectorSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const id = parseInt(inspectorUserId, 10);
    if (!isNaN(id) && id >= 1 && id <= 6040) {
      setSearchedUserId(id);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Title Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white font-['Space_Grotesk',sans-serif]">
            Recommendation <span className="text-holo-gradient">Nexus</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time inference powered by Truncated SVD matrix factorization (30 latent factors)
          </p>
        </div>

        {/* Tab switch */}
        <div className="inline-flex p-1 rounded-2xl bg-white/5 border border-white/10 self-start sm:self-auto">
          <button
            onClick={() => setActiveTab('me')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'me'
                ? 'bg-cyan-500 text-black shadow-neon-cyan'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>My Personalized Recs</span>
          </button>
          <button
            onClick={() => setActiveTab('inspector')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'inspector'
                ? 'bg-purple-500 text-white shadow-neon-violet'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Users className="w-3.5 h-3.5" />
            <span>Historical User Inspector</span>
          </button>
        </div>
      </div>

      {/* Mode Sub-headers & Status Alerts */}
      {activeTab === 'me' && (
        <div className="mb-8">
          {!user ? (
            <div className="p-4 rounded-2xl bg-gradient-to-r from-cyan-950/40 via-purple-950/40 to-cyan-950/40 border border-cyan-500/30 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <Info className="w-5 h-5 text-cyan-400 flex-shrink-0" />
                <div className="text-xs text-slate-300">
                  <span className="font-bold text-white">Showing Top Rated Popularity Fallback.</span>{' '}
                  Sign in or create an account to activate your personal SVD latent embedding.
                </div>
              </div>
              <button
                onClick={() => openAuthModal('login')}
                className="px-4 py-2 rounded-xl bg-cyan-400 text-black text-xs font-bold hover:shadow-neon-cyan transition-all flex-shrink-0"
              >
                Sign In Now
              </button>
            </div>
          ) : strategy === 'svd_folding_in' ? (
            <div className="p-4 rounded-2xl bg-cyan-950/40 border border-cyan-500/30 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-cyan-400" />
                <div className="text-xs text-slate-200">
                  <span className="font-bold text-cyan-300">Live SVD Latent Profile Active:</span>{' '}
                  Your saved ratings were folded into the 30-dimensional space in &lt;3ms.
                </div>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                {modelName}
              </span>
            </div>
          ) : (
            <div className="p-4 rounded-2xl bg-purple-950/40 border border-purple-500/30 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <Info className="w-5 h-5 text-purple-400 flex-shrink-0" />
                <div className="text-xs text-slate-300">
                  <span className="font-bold text-purple-300">Cold Start Profile:</span> Rate at
                  least 5 movies to calibrate your personal SVD latent vector, or use our Profile
                  Builder tool.
                </div>
              </div>
              <Link
                to="/profile-builder"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-purple-500 text-white text-xs font-bold hover:shadow-neon-violet transition-all flex-shrink-0"
              >
                <Sliders className="w-3.5 h-3.5" />
                <span>Open Profile Builder</span>
              </Link>
            </div>
          )}
        </div>
      )}

      {activeTab === 'inspector' && (
        <div className="p-5 rounded-2xl bg-[#090f24]/80 backdrop-blur-xl border border-purple-500/30 mb-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Users className="w-4 h-4 text-purple-400" />
              MovieLens 1M Persona Selector
            </h3>
            <p className="text-xs text-slate-400">
              Enter any User ID from 1 to 6,040 to inspect their predicted collaborative filtering scores
            </p>
          </div>

          <form onSubmit={handleInspectorSubmit} className="flex items-center gap-2 w-full sm:w-auto">
            <div className="relative">
              <input
                type="number"
                min="1"
                max="6040"
                value={inspectorUserId}
                onChange={(e) => setInspectorUserId(e.target.value)}
                placeholder="User ID (1-6040)"
                className="w-40 pl-4 pr-3 py-2 rounded-xl bg-white/5 border border-white/10 text-xs text-white focus:outline-none focus:border-purple-400 font-mono"
              />
            </div>
            <button
              type="submit"
              className="px-4 py-2 rounded-xl bg-purple-500 text-white text-xs font-bold hover:opacity-90 transition-opacity flex items-center gap-1.5"
            >
              <Search className="w-3.5 h-3.5" />
              <span>Inspect</span>
            </button>
          </form>
        </div>
      )}

      {/* Recommendation Results Grid */}
      {loading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {Array.from({ length: 12 }).map((_, i) => (
            <div key={i} className="aspect-[2/3] rounded-2xl bg-cosmic-800 animate-pulse" />
          ))}
        </div>
      ) : recs.length === 0 ? (
        <div className="text-center py-20 rounded-3xl bg-white/5 border border-white/10">
          <p className="text-sm text-slate-300">No recommendations available.</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {recs.map((rec, index) => (
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
      )}
    </div>
  );
};
