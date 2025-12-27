import { Sparkles } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface PreferenceBadgeProps {
  score?: number | null;
  reasons?: string[];
  className?: string;
}

/**
 * PreferenceBadge component displays a visual indicator when an item
 * matches user preferences. Shows a tooltip with detailed reasons.
 * 
 * Only displays when score is >= 50 (indicating a meaningful match).
 */
export const PreferenceBadge = ({ 
  score, 
  reasons = [],
  className = ''
}: PreferenceBadgeProps) => {
  // Don't show badge if no score or score is too low
  if (!score || score < 50) return null;
  
  // Determine badge styling based on score
  const getBadgeStyle = () => {
    if (score >= 75) {
      return 'bg-teal/30 text-teal-light border-teal/40';
    } else {
      return 'bg-teal/20 text-teal-light/80 border-teal/30';
    }
  };
  
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div 
            className={`
              flex items-center gap-1 px-2 py-0.5 rounded-full 
              text-xs font-medium border cursor-help
              transition-all duration-200 hover:scale-105
              ${getBadgeStyle()}
              ${className}
            `}
          >
            <Sparkles className="w-3 h-3" />
            <span>For you</span>
          </div>
        </TooltipTrigger>
        <TooltipContent 
          side="top" 
          className="max-w-xs p-3 bg-midnight/95 border-fog/20 text-fog"
        >
          <p className="font-medium text-gold mb-2">Based on your preferences:</p>
          {reasons.length > 0 ? (
            <ul className="text-xs space-y-1">
              {reasons.map((reason, index) => (
                <li key={index} className="flex items-start gap-1.5">
                  <span className="text-teal-light mt-0.5">•</span>
                  <span className="text-fog/90">{reason}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-fog/70">
              This matches your travel preferences from previous trips.
            </p>
          )}
          {score && (
            <div className="mt-2 pt-2 border-t border-fog/10">
              <p className="text-xs text-fog/60">
                Match score: <span className="text-teal-light font-medium">{score}%</span>
              </p>
            </div>
          )}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

export default PreferenceBadge;

