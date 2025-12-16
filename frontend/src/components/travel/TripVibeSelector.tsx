import { Coffee, Activity, Scale, Music } from "lucide-react";
import { cn } from "@/lib/utils";

type TripVibeType = "relaxing" | "active" | "balanced" | "party";

interface TripVibeSelectorProps {
  value: TripVibeType | null;
  onChange: (value: TripVibeType) => void;
}

const VIBES = [
  { id: "relaxing", label: "Relaxing/Slow-paced", icon: Coffee },
  { id: "active", label: "Active/Adventurous", icon: Activity },
  { id: "balanced", label: "Balanced", icon: Scale },
  { id: "party", label: "Party/Vibrant", icon: Music },
] as const;

const TripVibeSelector = ({ value, onChange }: TripVibeSelectorProps) => {
  return (
    <div className="space-y-4">
      <label className="block text-xs font-medium text-fog/70 tracking-widest uppercase">
        Trip Vibe & Pace
      </label>
      
      <div className="flex flex-wrap gap-3">
        {VIBES.map((vibe, index) => {
          const Icon = vibe.icon;
          const isSelected = value === vibe.id;
          
          return (
            <button
              key={vibe.id}
              type="button"
              onClick={() => onChange(vibe.id)}
              className={cn(
                "flex items-center gap-2.5 px-5 py-3 rounded-full border transition-all duration-300 hover-lift group",
                isSelected 
                  ? "border-teal bg-teal text-fog glow-teal" 
                  : "border-fog/10 bg-midnight-light/30 hover:border-teal/50 text-fog"
              )}
              style={{ animationDelay: `${index * 50}ms` }}
            >
              <Icon className={cn(
                "w-4 h-4 transition-transform duration-300",
                isSelected ? "scale-110" : "group-hover:scale-110"
              )} />
              <span className="text-sm">{vibe.label}</span>
              
              {isSelected && (
                <span className="w-1.5 h-1.5 bg-fog rounded-full animate-scale-in" />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default TripVibeSelector;

