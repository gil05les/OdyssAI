import { useState } from 'react';
import { AgentSearchingAnimation } from '../AgentSearchingAnimation';
import { AgentResultCard, DestinationCardContent } from '../AgentResultCard';
import { Destination } from '@/data/mockAgentData';
import { Button } from '@/components/ui/button';
import { ArrowRight, AlertCircle } from 'lucide-react';

interface DestinationAgentProps {
  destinations: Destination[];
  isLoading: boolean;
  error: string | null;
  onSelect: (destination: Destination) => void;
  onBack: () => void;
}

export const DestinationAgent = ({ destinations, isLoading, error, onSelect, onBack }: DestinationAgentProps) => {
  const [selected, setSelected] = useState<string | null>(null);

  const handleContinue = () => {
    const destination = destinations.find(d => d.id === selected);
    if (destination) {
      onSelect(destination);
    }
  };

  if (isLoading) {
    return (
      <AgentSearchingAnimation
        agentType="destination"
        searchText="Finding perfect destinations based on your preferences..."
      />
    );
  }

  if (error) {
    return (
      <div className="animate-fade-in max-w-3xl mx-auto">
        <div className="text-center mb-8">
          <div className="w-20 h-20 rounded-full bg-red-500/20 flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-10 h-10 text-red-500" />
          </div>
          <h2 className="text-2xl font-serif text-fog mb-2">Error Loading Destinations</h2>
          <p className="text-sand/70 mb-4">{error}</p>
          <Button
            onClick={onBack}
            variant="outline"
            className="border-gold/30 text-gold hover:bg-gold/10"
          >
            ← Back to Form
          </Button>
        </div>
      </div>
    );
  }

  if (destinations.length === 0) {
    return (
      <div className="animate-fade-in max-w-3xl mx-auto">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-serif text-fog mb-2">No Destinations Found</h2>
          <p className="text-sand/70 mb-4">We couldn't find any destinations matching your preferences.</p>
          <Button
            onClick={onBack}
            variant="outline"
            className="border-gold/30 text-gold hover:bg-gold/10"
          >
            ← Back to Form
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-serif text-fog mb-2">Choose Your Destination</h2>
        <p className="text-sand/70">Based on your preferences, I've found these perfect matches</p>
      </div>

      <div className="grid gap-4 max-w-3xl mx-auto">
        {destinations.map((dest, index) => (
          <AgentResultCard
            key={dest.id}
            selected={selected === dest.id}
            onClick={() => setSelected(dest.id)}
            delay={index * 100}
          >
            <DestinationCardContent
              name={dest.name}
              country={dest.country}
              description={dest.description}
              matchReason={dest.matchReason}
              image={dest.image}
              tempRange={dest.tempRange}
              iataCode={dest.iataCode}
              airportName={dest.airportName}
            />
          </AgentResultCard>
        ))}
      </div>

      <div className="flex justify-between mt-8 max-w-3xl mx-auto">
        <Button
          variant="ghost"
          onClick={onBack}
          className="text-sand/70 hover:text-fog"
        >
          ← Back to Form
        </Button>
        <Button
          onClick={handleContinue}
          disabled={!selected}
          className="bg-gold hover:bg-gold/90 text-midnight px-8"
        >
          Continue to Flights <ArrowRight className="w-4 h-4 ml-2" />
        </Button>
      </div>
    </div>
  );
};
