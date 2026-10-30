import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});

// Mock HTMLCanvasElement.getContext for Three.js in test environments
HTMLCanvasElement.prototype.getContext = (() => {
  return null;
}) as any;

// Mock Axios API calls for tests
vi.mock('../services/api', () => ({
  apiClient: {
    get: vi.fn().mockResolvedValue({ data: {} }),
    post: vi.fn().mockResolvedValue({ data: {} }),
    delete: vi.fn().mockResolvedValue({ data: {} }),
  },
  api: {
    auth: {
      getMe: vi.fn().mockRejectedValue(new Error('Unauthenticated')),
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn().mockResolvedValue({ message: 'Logged out' }),
    },
    movies: {
      getCatalog: vi.fn().mockResolvedValue({ movies: [], total: 0, page: 1, page_size: 20, total_pages: 1 }),
      getMovie: vi.fn(),
      getSimilar: vi.fn().mockResolvedValue([]),
      getTrending: vi.fn().mockResolvedValue([]),
      getTopRated: vi.fn().mockResolvedValue([]),
    },
    ratings: {
      getMyRatings: vi.fn().mockResolvedValue([]),
      submitRating: vi.fn(),
      deleteRating: vi.fn(),
    },
    watchlist: {
      getWatchlist: vi.fn().mockResolvedValue([]),
      addToWatchlist: vi.fn(),
      removeFromWatchlist: vi.fn(),
    },
    recommendations: {
      getPersonalized: vi.fn().mockResolvedValue({ strategy: 'popularity_fallback', model_name: 'damped_popularity_m50', items: [] }),
      getProfileBuilder: vi.fn().mockResolvedValue({ strategy: 'svd_folding_in', model_name: 'svd_k30', items: [] }),
      getHistoricalUser: vi.fn().mockResolvedValue({ user_id: 1, strategy: 'svd_offline', items: [] }),
    },
    posters: {
      getUrl: (id: number) => `/api/v1/posters/${id}`,
    },
  },
}));
