import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Film,
  Compass,
  Sparkles,
  Bookmark,
  User as UserIcon,
  Search,
  LogIn,
  LogOut,
  Menu,
  X,
  Sliders,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const Navbar: React.FC = () => {
  const { user, openAuthModal, logout } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navigate = useNavigate();

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/catalog?q=${encodeURIComponent(searchQuery.trim())}`);
      setSearchQuery('');
      setMobileMenuOpen(false);
    }
  };

  return (
    <header className="sticky top-0 z-40 w-full bg-[#030712]/80 backdrop-blur-xl border-b border-cyan-500/15">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 gap-4">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2.5 group flex-shrink-0">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-purple-600 flex items-center justify-center shadow-neon-cyan group-hover:scale-105 transition-transform">
              <Film className="w-5 h-5 text-black stroke-[2.5]" />
            </div>
            <div>
              <span className="text-xl font-extrabold tracking-tight text-holo-gradient font-['Space_Grotesk',sans-serif]">
                MovieRec
              </span>
              <span className="text-[10px] block font-mono tracking-widest text-cyan-400/80 -mt-1">
                V2 • 3D ENGINE
              </span>
            </div>
          </Link>

          {/* Desktop Search Bar */}
          <form
            onSubmit={handleSearchSubmit}
            className="hidden md:flex items-center flex-1 max-w-md mx-4 relative"
          >
            <Search className="w-4 h-4 text-cyan-400 absolute left-3.5 pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search 3,883 movies (e.g. Inception, Matrix)..."
              className="w-full pl-10 pr-4 py-1.5 rounded-full bg-white/5 border border-cyan-500/20 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-cyan-400 focus:bg-white/10 transition-all"
            />
          </form>

          {/* Desktop Navigation Links */}
          <nav className="hidden lg:flex items-center gap-1 text-sm font-medium text-slate-300">
            <Link
              to="/"
              className="px-3 py-1.5 rounded-lg hover:text-cyan-300 hover:bg-white/5 transition-colors"
            >
              Home
            </Link>
            <Link
              to="/catalog"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg hover:text-cyan-300 hover:bg-white/5 transition-colors"
            >
              <Compass className="w-4 h-4 text-cyan-400" />
              Catalog
            </Link>
            <Link
              to="/recommendations"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg hover:text-purple-300 hover:bg-white/5 transition-colors"
            >
              <Sparkles className="w-4 h-4 text-purple-400" />
              AI Recs
            </Link>
            <Link
              to="/profile-builder"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg hover:text-teal-300 hover:bg-white/5 transition-colors"
            >
              <Sliders className="w-4 h-4 text-teal-400" />
              Profile Builder
            </Link>
            <Link
              to="/watchlist"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg hover:text-pink-300 hover:bg-white/5 transition-colors"
            >
              <Bookmark className="w-4 h-4 text-pink-400" />
              Watchlist
            </Link>
          </nav>

          {/* User Auth Section */}
          <div className="flex items-center gap-3">
            {user ? (
              <div className="flex items-center gap-2">
                <Link
                  to="/profile"
                  className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-cyan-950/60 border border-cyan-500/30 text-cyan-300 text-xs font-medium hover:border-cyan-400 transition-colors"
                >
                  <UserIcon className="w-3.5 h-3.5 text-cyan-400" />
                  <span className="hidden sm:inline font-mono">{user.username}</span>
                </Link>
                <button
                  onClick={logout}
                  title="Sign Out"
                  className="p-2 rounded-xl text-slate-400 hover:text-rose-400 hover:bg-white/5 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button
                onClick={() => openAuthModal('login')}
                className="flex items-center gap-2 px-4 py-1.5 rounded-full bg-gradient-to-r from-cyan-400 to-purple-600 text-black text-xs font-bold hover:opacity-95 shadow-neon-cyan transition-all"
              >
                <LogIn className="w-3.5 h-3.5 stroke-[2.5]" />
                <span>Sign In</span>
              </button>
            )}

            {/* Mobile Hamburger */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/5"
              aria-label="Toggle Navigation Menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden bg-[#070b19] border-b border-cyan-500/20 px-4 pt-3 pb-6 space-y-3 animate-fadeIn">
          <form onSubmit={handleSearchSubmit} className="relative">
            <Search className="w-4 h-4 text-cyan-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search movies..."
              className="w-full pl-9 pr-4 py-2 rounded-xl bg-white/5 border border-white/10 text-xs text-white placeholder-slate-400"
            />
          </form>

          <nav className="flex flex-col space-y-1 text-sm font-medium text-slate-200">
            <Link
              to="/"
              onClick={() => setMobileMenuOpen(false)}
              className="px-3 py-2 rounded-lg hover:bg-white/5 flex items-center gap-2"
            >
              Home
            </Link>
            <Link
              to="/catalog"
              onClick={() => setMobileMenuOpen(false)}
              className="px-3 py-2 rounded-lg hover:bg-white/5 flex items-center gap-2"
            >
              <Compass className="w-4 h-4 text-cyan-400" /> Catalog
            </Link>
            <Link
              to="/recommendations"
              onClick={() => setMobileMenuOpen(false)}
              className="px-3 py-2 rounded-lg hover:bg-white/5 flex items-center gap-2"
            >
              <Sparkles className="w-4 h-4 text-purple-400" /> AI Recommendations
            </Link>
            <Link
              to="/profile-builder"
              onClick={() => setMobileMenuOpen(false)}
              className="px-3 py-2 rounded-lg hover:bg-white/5 flex items-center gap-2"
            >
              <Sliders className="w-4 h-4 text-teal-400" /> Profile Builder
            </Link>
            <Link
              to="/watchlist"
              onClick={() => setMobileMenuOpen(false)}
              className="px-3 py-2 rounded-lg hover:bg-white/5 flex items-center gap-2"
            >
              <Bookmark className="w-4 h-4 text-pink-400" /> Watchlist
            </Link>
            {user && (
              <Link
                to="/profile"
                onClick={() => setMobileMenuOpen(false)}
                className="px-3 py-2 rounded-lg hover:bg-white/5 flex items-center gap-2"
              >
                <UserIcon className="w-4 h-4 text-cyan-400" /> Profile ({user.username})
              </Link>
            )}
          </nav>
        </div>
      )}
    </header>
  );
};
