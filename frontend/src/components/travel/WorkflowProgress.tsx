import { Check, MapPin, Plane, Building2, Calendar, Car, CreditCard, FileCheck } from 'lucide-react';
import { cn } from '@/lib/utils';

export type WorkflowStep = 'idle' | 'destinations' | 'flights' | 'hotels' | 'itineraries' | 'transport' | 'complete' | 'checkout' | 'confirmation';

interface WorkflowProgressProps {
  currentStep: WorkflowStep;
  onStepClick?: (step: WorkflowStep) => void;
  isEditing?: boolean; // When true, allows clicking on completed/current steps
}

const steps = [
  { key: 'destinations', label: 'Destination', icon: MapPin },
  { key: 'flights', label: 'Flights', icon: Plane },
  { key: 'hotels', label: 'Hotels', icon: Building2 },
  { key: 'itineraries', label: 'Itinerary', icon: Calendar },
  { key: 'transport', label: 'Transport', icon: Car },
  { key: 'checkout', label: 'Checkout', icon: CreditCard },
  { key: 'confirmation', label: 'Confirm', icon: FileCheck },
] as const;

// Map workflow steps to their index in the steps array
const getStepIndex = (step: WorkflowStep): number => {
  const stepKeyMap: Record<string, number> = {
    'destinations': 0,
    'flights': 1,
    'hotels': 2,
    'itineraries': 3,
    'transport': 4,
    'checkout': 5,
    'confirmation': 6,
  };
  
  // For 'idle', show all steps as future (greyed out)
  if (step === 'idle') {
    return -1;
  }
  
  // For 'complete', we've finished transport, so we're at index 4 (transport done, checkout is next)
  if (step === 'complete') {
    return 4;
  }
  
  return stepKeyMap[step] ?? -1;
};

export const WorkflowProgress = ({ currentStep, onStepClick, isEditing }: WorkflowProgressProps) => {
  const currentIndex = getStepIndex(currentStep);

  const handleStepClick = (stepKey: string, index: number) => {
    if (!onStepClick || !isEditing) return;
    
    // Only allow clicking on completed or current steps (not checkout/confirmation)
    const isClickable = index <= currentIndex && index < 5; // 5 is checkout index
    if (isClickable) {
      onStepClick(stepKey as WorkflowStep);
    }
  };

  return (
    <div className="w-full py-4 px-4 animate-fade-in">
      <div className="flex items-center justify-between max-w-5xl mx-auto">
        {steps.map((step, index) => {
          const isCompleted = currentIndex > index;
          const isCurrent = currentIndex === index;
          const isFuture = currentIndex < index;
          const Icon = step.icon;
          
          // Determine if this step is clickable
          const isClickable = isEditing && onStepClick && index <= currentIndex && index < 5;

          return (
            <div key={step.key} className="flex items-center flex-1 last:flex-none">
              {/* Step circle */}
              <div 
                className={cn(
                  "flex flex-col items-center",
                  isClickable && "cursor-pointer group"
                )}
                onClick={() => handleStepClick(step.key, index)}
              >
                <div
                  className={cn(
                    "w-10 h-10 rounded-full flex items-center justify-center transition-all duration-500",
                    isCompleted && "bg-gold text-midnight shadow-lg shadow-gold/30",
                    isCurrent && "bg-teal text-white shadow-lg shadow-teal/30 animate-pulse-gold",
                    isFuture && "bg-midnight/10 text-midnight/30 opacity-50",
                    !isCompleted && !isCurrent && !isFuture && "bg-midnight/10 text-midnight/40",
                    // Hover state for clickable steps
                    isClickable && "hover:ring-2 hover:ring-gold/50 hover:scale-110"
                  )}
                >
                  {isCompleted ? (
                    <Check className="w-5 h-5" />
                  ) : (
                    <Icon className={cn("w-5 h-5", isFuture && "opacity-50")} />
                  )}
                </div>
                <span
                  className={cn(
                    "text-xs mt-2 font-medium transition-colors duration-300",
                    isCompleted && "text-gold",
                    isCurrent && "text-teal",
                    isFuture && "text-midnight/30 opacity-50",
                    !isCompleted && !isCurrent && !isFuture && "text-midnight/40",
                    // Hover state for clickable steps
                    isClickable && "group-hover:text-gold"
                  )}
                >
                  {step.label}
                </span>
              </div>

              {/* Connector line */}
              {index < steps.length - 1 && (
                <div className="flex-1 h-0.5 mx-2 mt-[-20px]">
                  <div
                    className={cn(
                      "h-full transition-all duration-700",
                      currentIndex > index ? "bg-gold" : "bg-midnight/10",
                      isFuture && "opacity-30"
                    )}
                    style={{
                      transform: currentIndex > index ? 'scaleX(1)' : 'scaleX(0.3)',
                      transformOrigin: 'left',
                    }}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
