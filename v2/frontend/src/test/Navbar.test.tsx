import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect } from 'vitest';
import { Navbar } from '../components/common/Navbar';
import { AuthProvider } from '../context/AuthContext';

describe('Navbar Component', () => {
  it('renders branding and primary navigation links', () => {
    render(
      <AuthProvider>
        <BrowserRouter>
          <Navbar />
        </BrowserRouter>
      </AuthProvider>
    );

    expect(screen.getByText('MovieRec')).toBeInTheDocument();
    expect(screen.getByText('V2 • 3D ENGINE')).toBeInTheDocument();
    expect(screen.getByText('Catalog')).toBeInTheDocument();
    expect(screen.getByText('AI Recs')).toBeInTheDocument();
    expect(screen.getByText('Profile Builder')).toBeInTheDocument();
    expect(screen.getByText('Watchlist')).toBeInTheDocument();
  });

  it('renders Sign In button when unauthenticated', () => {
    render(
      <AuthProvider>
        <BrowserRouter>
          <Navbar />
        </BrowserRouter>
      </AuthProvider>
    );

    expect(screen.getByText('Sign In')).toBeInTheDocument();
  });
});
