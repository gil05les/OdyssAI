import { useState, useEffect } from 'react';
import { AgentSearchingAnimation } from '../AgentSearchingAnimation';
import { mockTransportLegs, TransportLeg, TransportOption } from '@/data/mockAgentData';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Check, MapPin, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { API_BASE_URL } from '@/services/api';

interface TransportAgentProps {
  onComplete: (choices: Record<string, TransportOption | null>) => void;
  onBack: () => void;
}

export const TransportAgent = ({ onComplete, onBack }: TransportAgentProps) => {
  const [isSearching, setIsSearching] = useState(true);
  const [choices, setChoices] = useState<Record<string, TransportOption | null>>({});
  const [declined, setDeclined] = useState<Set<string>>(new Set());
  const [transportLegs, setTransportLegs] = useState<TransportLeg[]>(mockTransportLegs);

  // Fetch images for transport options
  useEffect(() => {
    const fetchTransportImages = async () => {
      const updatedLegs = await Promise.all(
        mockTransportLegs.map(async (leg) => {
          const updatedOptions = await Promise.all(
            leg.options.map(async (option) => {
              if (option.image) {
                return option; // Already has image
              }
              try {
                // Fetch image from backend API
                const response = await fetch(
                  `${API_BASE_URL}/images/transport?name=${encodeURIComponent(option.name)}&type=${encodeURIComponent(option.type)}`
                );
                if (response.ok) {
                  const data = await response.json();
                  return { ...option, image: data.image_url };
                }
              } catch (error) {
                console.warn(`Failed to fetch image for ${option.name}:`, error);
              }
              return option;
            })
          );
          return { ...leg, options: updatedOptions };
        })
      );
      setTransportLegs(updatedLegs);
    };

    fetchTransportImages();
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsSearching(false);
    }, 2400);
    return () => clearTimeout(timer);
  }, []);

  const selectOption = (legId: string, option: TransportOption) => {
    setChoices(prev => ({ ...prev, [legId]: option }));
    setDeclined(prev => {
      const next = new Set(prev);
      next.delete(legId);
      return next;
    });
  };

  const declineLeg = (legId: string) => {
    setChoices(prev => ({ ...prev, [legId]: null }));
    setDeclined(prev => new Set(prev).add(legId));
  };

  const handleComplete = () => {
    onComplete(choices);
  };

  const allLegsDecided = transportLegs.every(
    leg => choices[leg.id] !== undefined || declined.has(leg.id)
  );

  if (isSearching) {
    return (
      <AgentSearchingAnimation
        agentType="transport"
        searchText="Finding transport options for your journey..."
      />
    );
  }

  return (
    <div className="animate-fade-in">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-serif text-fog mb-2">Transport Options</h2>
        <p className="text-fog/90">Choose or decline transport for each leg of your journey</p>
      </div>

      <div className="max-w-3xl mx-auto space-y-6">
        {transportLegs.map((leg, legIndex) => {
          const isDeclined = declined.has(leg.id);
          const selectedOption = choices[leg.id];

          return (
            <div
              key={leg.id}
              className="animate-slide-up p-6 rounded-2xl glass-sand"
              style={{ animationDelay: `${legIndex * 100}ms`, animationFillMode: 'forwards' }}
            >
              {/* Route header */}
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-teal/20 flex items-center justify-center">
                  <MapPin className="w-5 h-5 text-teal" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 text-sm text-fog">
                    <span className="font-medium">{leg.from}</span>
                    <span className="text-fog/60">→</span>
                    <span className="font-medium">{leg.to}</span>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => declineLeg(leg.id)}
                  className={cn(
                    "text-xs",
                    isDeclined ? "text-red-500" : "text-fog/60 hover:text-red-500"
                  )}
                >
                  {isDeclined ? (
                    <>
                      <X className="w-3 h-3 mr-1" /> Declined
                    </>
                  ) : (
                    "I'll arrange myself"
                  )}
                </Button>
              </div>

              {/* Transport options */}
              <div className={cn(
                "grid grid-cols-1 sm:grid-cols-3 gap-3 transition-opacity",
                isDeclined && "opacity-30 pointer-events-none"
              )}>
                {leg.options.map(option => {
                  const isSelected = selectedOption?.id === option.id;
                  return (
                    <button
                      key={option.id}
                      onClick={() => selectOption(leg.id, option)}
                      className={cn(
                        "p-4 rounded-xl border-2 transition-all duration-300 text-left",
                        "hover:scale-[1.02] hover:shadow-md overflow-hidden",
                        isSelected
                          ? "border-gold bg-gold/10 shadow-md"
                          : "border-fog/20 bg-white/50 hover:border-gold/50"
                      )}
                    >
                      {/* Image background or Icon */}
                      <div 
                        className="relative w-full h-24 mb-2 rounded-lg overflow-hidden"
                        style={{
                          backgroundImage: option.image ? `url(${option.image})` : 'none',
                          backgroundSize: 'cover',
                          backgroundPosition: 'center',
                          backgroundColor: option.image ? 'transparent' : 'rgba(255, 255, 255, 0.05)'
                        }}
                      >
                        {/* Dark overlay for better text readability */}
                        {option.image && (
                          <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/20 to-transparent" />
                        )}
                        {/* Icon fallback if no image */}
                        {!option.image && (
                          <div className="w-full h-full flex items-center justify-center">
                            <span className="text-4xl">{option.icon}</span>
                          </div>
                        )}
                        {isSelected && (
                          <div className="absolute top-2 right-2 w-5 h-5 rounded-full bg-gold flex items-center justify-center z-10 shadow-lg">
                            <Check className="w-3 h-3 text-midnight" />
                          </div>
                        )}
                      </div>
                      <p className={cn(
                        "font-medium text-sm",
                        option.image ? "text-white drop-shadow-lg" : "text-fog"
                      )}>{option.name}</p>
                      <div className={cn(
                        "flex items-center justify-between mt-2 text-xs",
                        option.image ? "text-white/90 drop-shadow" : "text-fog/80"
                      )}>
                        <span>{option.duration}</span>
                        <span className="font-semibold text-gold drop-shadow">
                          {option.price === 0 ? 'Free' : `CHF ${option.price}`}
                        </span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      <div className="flex justify-between mt-8 max-w-3xl mx-auto">
        <Button
          variant="ghost"
          onClick={onBack}
          className="text-fog/80 hover:text-fog"
        >
          <ArrowLeft className="w-4 h-4 mr-2" /> Back
        </Button>
        <Button
          onClick={handleComplete}
          disabled={!allLegsDecided}
          className="bg-gold hover:bg-gold/90 text-midnight px-8"
        >
          Complete Trip Planning
        </Button>
      </div>
    </div>
  );
};
