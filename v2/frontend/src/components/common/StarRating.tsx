import React, { useState } from 'react';
import { Star } from 'lucide-react';

interface StarRatingProps {
  initialRating?: number;
  onRatingChange?: (rating: number) => void;
  readOnly?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const RATING_LABELS: Record<number, string> = {
  1: 'Disliked (1.0)',
  2: 'Fair (2.0)',
  3: 'Good (3.0)',
  4: 'Great (4.0)',
  5: 'Masterpiece (5.0)',
};

export const StarRating: React.FC<StarRatingProps> = ({
  initialRating = 0,
  onRatingChange,
  readOnly = false,
  size = 'md',
}) => {
  const [rating, setRating] = useState<number>(initialRating);
  const [hoverRating, setHoverRating] = useState<number>(0);

  const starSizes = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  const handleStarClick = (selected: number) => {
    if (readOnly) return;
    setRating(selected);
    if (onRatingChange) {
      onRatingChange(selected);
    }
  };

  const currentDisplayRating = hoverRating || rating;

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center gap-1.5" role="radiogroup" aria-label="Movie Rating">
        {[1, 2, 3, 4, 5].map((star) => {
          const isFilled = star <= currentDisplayRating;
          return (
            <button
              key={star}
              type="button"
              disabled={readOnly}
              onClick={() => handleStarClick(star)}
              onMouseEnter={() => !readOnly && setHoverRating(star)}
              onMouseLeave={() => !readOnly && setHoverRating(0)}
              aria-label={`Rate ${star} stars`}
              className={`transition-all duration-150 transform ${
                readOnly ? 'cursor-default' : 'hover:scale-125 cursor-pointer'
              }`}
            >
              <Star
                className={`${starSizes[size]} transition-colors duration-150 ${
                  isFilled
                    ? 'text-amber-400 fill-amber-400 drop-shadow-[0_0_8px_rgba(251,191,36,0.6)]'
                    : 'text-slate-600 hover:text-amber-200'
                }`}
              />
            </button>
          );
        })}

        {rating > 0 && (
          <span className="ml-2 text-sm font-semibold text-amber-300">
            {rating.toFixed(1)} / 5
          </span>
        )}
      </div>

      {!readOnly && currentDisplayRating > 0 && (
        <span className="text-xs text-cyan-400 font-medium">
          {RATING_LABELS[currentDisplayRating]}
        </span>
      )}
    </div>
  );
};
