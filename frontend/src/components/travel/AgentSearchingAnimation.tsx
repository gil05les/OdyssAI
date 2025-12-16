import { useEffect, useState } from 'react';
import { Plane, MapPin, Building2, Calendar, Car } from 'lucide-react';

interface AgentSearchingAnimationProps {
  agentType: 'destination' | 'flight' | 'hotel' | 'itinerary' | 'transport';
  searchText: string;
}

const agentIcons = {
  destination: MapPin,
  flight: Plane,
  hotel: Building2,
  itinerary: Calendar,
  transport: Car,
};

const agentColors = {
  destination: 'from-teal-400 to-teal-600',
  flight: 'from-gold to-sand',
  hotel: 'from-purple-400 to-purple-600',
  itinerary: 'from-emerald-400 to-emerald-600',
  transport: 'from-blue-400 to-blue-600',
};

export const AgentSearchingAnimation = ({ agentType, searchText }: AgentSearchingAnimationProps) => {
  const [displayText, setDisplayText] = useState('');
  const [showCursor, setShowCursor] = useState(true);
  const Icon = agentIcons[agentType];

  // Typing animation
  useEffect(() => {
    let index = 0;
    const interval = setInterval(() => {
      if (index <= searchText.length) {
        setDisplayText(searchText.slice(0, index));
        index++;
      } else {
        clearInterval(interval);
      }
    }, 50);
    return () => clearInterval(interval);
  }, [searchText]);

  // Cursor blink
  useEffect(() => {
    const interval = setInterval(() => {
      setShowCursor(prev => !prev);
    }, 530);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center py-16 animate-fade-in">
      {/* Animated rings container */}
      <div className="relative w-40 h-40 mb-8">
        {/* Outer pulsing rings */}
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="absolute inset-0 rounded-full border-2 border-teal/30 animate-ring-pulse"
            style={{
              animationDelay: `${i * 0.5}s`,
              animationDuration: '2s',
            }}
          />
        ))}

        {/* Orbiting particles */}
        <div className="absolute inset-0 animate-orbit">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3 h-3 rounded-full bg-gold shadow-lg shadow-gold/50" />
        </div>
        <div className="absolute inset-0 animate-orbit" style={{ animationDelay: '-1s', animationDuration: '4s' }}>
          <div className="absolute top-1/2 right-0 -translate-y-1/2 w-2 h-2 rounded-full bg-teal shadow-lg shadow-teal/50" />
        </div>
        <div className="absolute inset-0 animate-orbit" style={{ animationDelay: '-2s', animationDuration: '5s' }}>
          <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-2.5 h-2.5 rounded-full bg-sand shadow-lg shadow-sand/50" />
        </div>

        {/* Center icon */}
        <div className={`absolute inset-4 rounded-full bg-gradient-to-br ${agentColors[agentType]} flex items-center justify-center shadow-2xl animate-pulse-gold`}>
          <Icon className="w-12 h-12 text-white drop-shadow-lg" />
        </div>
      </div>

      {/* Typing text */}
      <div className="text-center">
        <p className="text-xl text-fog font-medium mb-2">
          {displayText}
          <span className={`inline-block w-0.5 h-5 bg-gold ml-1 ${showCursor ? 'opacity-100' : 'opacity-0'}`} />
        </p>
        <p className="text-sand/60 text-sm">AI Agent is working for you</p>
      </div>

      {/* Loading dots */}
      <div className="flex gap-2 mt-6">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="w-2 h-2 rounded-full bg-teal animate-bounce"
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </div>
    </div>
  );
};
