import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect } from 'vitest';
import { HolographicMovieCard } from '../components/common/HolographicMovieCard';
import { AuthProvider } from '../context/AuthContext';

const mockMovie = {
  movie_id: 1196,
  title: 'Star Wars: Episode V - The Empire Strikes Back (1980)',
  genres: ['Action', 'Adventure', 'Sci-Fi'],
  year: 1980,
  vote_count: 2990,
  mean_rating: 4.29,
};

describe('HolographicMovieCard Component', () => {
  it('renders title, year, and genre badges', () => {
    render(
      <AuthProvider>
        <BrowserRouter>
          <HolographicMovieCard movie={mockMovie} />
        </BrowserRouter>
      </AuthProvider>
    );

    expect(screen.getByText(mockMovie.title)).toBeInTheDocument();
    expect(screen.getByText('1980')).toBeInTheDocument();
    expect(screen.getByText('Action')).toBeInTheDocument();
    expect(screen.getByText('Adventure')).toBeInTheDocument();
  });

  it('renders score badge when showScore is true', () => {
    render(
      <AuthProvider>
        <BrowserRouter>
          <HolographicMovieCard
            movie={mockMovie}
            showScore={true}
            score={4.85}
            scoreLabel="Pred"
          />
        </BrowserRouter>
      </AuthProvider>
    );

    expect(screen.getByText('Pred: 4.85')).toBeInTheDocument();
  });

  it('renders custom badge when provided', () => {
    render(
      <AuthProvider>
        <BrowserRouter>
          <HolographicMovieCard movie={mockMovie} badge="#1 Match" />
        </BrowserRouter>
      </AuthProvider>
    );

    expect(screen.getByText('#1 Match')).toBeInTheDocument();
  });
});
