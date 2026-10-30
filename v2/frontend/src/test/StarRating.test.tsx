import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { StarRating } from '../components/common/StarRating';

describe('StarRating Component', () => {
  it('renders 5 star buttons', () => {
    render(<StarRating initialRating={0} />);
    const buttons = screen.getAllByRole('button');
    expect(buttons).toHaveLength(5);
  });

  it('displays the rating value when clicked', () => {
    const handleRatingChange = vi.fn();
    render(<StarRating initialRating={0} onRatingChange={handleRatingChange} />);

    const fourStarButton = screen.getByLabelText('Rate 4 stars');
    fireEvent.click(fourStarButton);

    expect(handleRatingChange).toHaveBeenCalledWith(4);
    expect(screen.getByText('4.0 / 5')).toBeInTheDocument();
  });

  it('does not trigger onRatingChange when readOnly is true', () => {
    const handleRatingChange = vi.fn();
    render(<StarRating initialRating={3} onRatingChange={handleRatingChange} readOnly={true} />);

    const fiveStarButton = screen.getByLabelText('Rate 5 stars');
    fireEvent.click(fiveStarButton);

    expect(handleRatingChange).not.toHaveBeenCalled();
    expect(screen.getByText('3.0 / 5')).toBeInTheDocument();
  });
});
