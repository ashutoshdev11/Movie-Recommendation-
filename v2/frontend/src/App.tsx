import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { Navbar } from './components/common/Navbar';
import { AuthModal } from './components/common/AuthModal';
import { Home } from './pages/Home';
import { Catalog } from './pages/Catalog';
import { MovieDetails } from './pages/MovieDetails';
import { Recommendations } from './pages/Recommendations';
import { ProfileBuilder } from './pages/ProfileBuilder';
import { Watchlist } from './pages/Watchlist';
import { Profile } from './pages/Profile';
import { Film, ShieldCheck } from 'lucide-react';

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen flex flex-col bg-[#030712] text-slate-100 font-['Outfit',sans-serif] selection:bg-cyan-500 selection:text-black">
          {/* Top Navbar */}
          <Navbar />

          {/* Global Auth Modal */}
          <AuthModal />

          {/* Main Content Area */}
          <main className="flex-grow">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/catalog" element={<Catalog />} />
              <Route path="/movies/:id" element={<MovieDetails />} />
              <Route path="/recommendations" element={<Recommendations />} />
              <Route path="/profile-builder" element={<ProfileBuilder />} />
              <Route path="/watchlist" element={<Watchlist />} />
              <Route path="/profile" element={<Profile />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>

          {/* Futuristic Footer */}
          <footer className="border-t border-cyan-500/15 bg-[#02050e] py-10 mt-auto">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-6">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-purple-600 flex items-center justify-center">
                  <Film className="w-4 h-4 text-black stroke-[2.5]" />
                </div>
                <div>
                  <span className="text-base font-bold text-holo-gradient font-['Space_Grotesk',sans-serif]">
                    MovieRec V2
                  </span>
                  <p className="text-[11px] text-slate-500">
                    Standalone 3D Cinematic Discovery • Powered by MovieLens 1M & SVD (k=30)
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-4 text-xs text-slate-400">
                <span className="flex items-center gap-1.5 text-cyan-400">
                  <ShieldCheck className="w-4 h-4" />
                  Argon2id + HTTP-Only Cookie Session
                </span>
                <span>•</span>
                <span>Version 2.0.0</span>
              </div>
            </div>
          </footer>
        </div>
      </Router>
    </AuthProvider>
  );
};

export default App;
