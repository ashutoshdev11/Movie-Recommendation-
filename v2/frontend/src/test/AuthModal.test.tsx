import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { AuthModal } from '../components/common/AuthModal';
import { AuthProvider, useAuth } from '../context/AuthContext';
import React from 'react';

const TestAuthModalLauncher: React.FC = () => {
  const { openAuthModal } = useAuth();
  return (
    <div>
      <button onClick={() => openAuthModal('login')}>Open Login Modal</button>
      <button onClick={() => openAuthModal('register')}>Open Register Modal</button>
      <AuthModal />
    </div>
  );
};

describe('AuthModal Component', () => {
  it('opens and switches between Sign In and Create Account modes', () => {
    render(
      <AuthProvider>
        <TestAuthModalLauncher />
      </AuthProvider>
    );

    // Click to open login
    fireEvent.click(screen.getByText('Open Login Modal'));
    expect(screen.getByRole('heading', { name: /Welcome Back/i })).toBeInTheDocument();
    
    // There are 2 "Sign In" buttons: the tab switch and the form submit button
    const signInButtons = screen.getAllByRole('button', { name: /^Sign In$/i });
    expect(signInButtons.length).toBeGreaterThanOrEqual(1);

    // Click Create Account tab
    const createAccountTab = screen.getByRole('button', { name: /^Create Account$/i });
    fireEvent.click(createAccountTab);

    expect(screen.getByRole('heading', { name: /Join MovieRec Universe/i })).toBeInTheDocument();
    expect(screen.getByPlaceholderText('you@galaxy.com')).toBeInTheDocument();
  });
});
