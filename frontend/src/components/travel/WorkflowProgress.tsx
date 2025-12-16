import { Check, MapPin, Plane, Building2, Calendar, Car, CreditCard, FileCheck } from 'lucide-react';
import { cn } from '@/lib/utils';

export type WorkflowStep = 'idle' | 'destinations' | 'flights' | 'hotels' | 'itineraries' | 'transport' | 'complete' | 'checkout' | 'confirmation';

interface WorkflowProgressProps {
  currentStep: WorkflowStep;
}

const steps = [
  { key: 'destinations', label: 'Destination', icon: MapPin },
  { key: 'flights', label: 'Flights', icon: Plane },
  { key: 'hotels', label: 'Hotels', icon: Building2 },
  { key: 'itineraries', label: 'Itinerary', icon: Calendar },
  { key: 'transport', label: 'Transport', icon: Car },
] as const;

const stepOrder: Record<WorkflowStep, number> = {
  idle: -1,
  destinations: 0,
  flights: 1,
  hotels: 2,
  itineraries: 3,
  transport: 4,
  complete: 5,
  checkout: 6,
  confirmation: 7,
};

export const WorkflowProgress = ({ currentStep }: WorkflowProgressProps) => {
  const currentIndex = stepOrder[currentStep];

  return (
    <div className="w-full py-6 px-4 animate-fade-in">
      <div className="flex items-center justify-between max-w-3xl mx-auto">
        {steps.map((step, index) => {
          const isCompleted = currentIndex > index;
          const isCurrent = currentIndex === index;
          const Icon = step.icon;

          return (
            <div key={step.key} className="flex items-center flex-1 last:flex-none">
              {/* Step circle */}
              <div className="flex flex-col items-center">
                <div
                  className={cn(
                    "w-10 h-10 rounded-full flex items-center justify-center transition-all duration-500",
                    isCompleted && "bg-gold text-midnight shadow-lg shadow-gold/30",
                    isCurrent && "bg-teal text-white shadow-lg shadow-teal/30 animate-pulse-gold",
                    !isCompleted && !isCurrent && "bg-midnight/10 text-midnight/40"
                  )}
                >
                  {isCompleted ? (
                    <Check className="w-5 h-5" />
                  ) : (
                    <Icon className="w-5 h-5" />
                  )}
                </div>
                <span
                  className={cn(
                    "text-xs mt-2 font-medium transition-colors duration-300",
                    isCompleted && "text-gold",
                    isCurrent && "text-teal",
                    !isCompleted && !isCurrent && "text-midnight/40"
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
                      currentIndex > index ? "bg-gold" : "bg-midnight/10"
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
