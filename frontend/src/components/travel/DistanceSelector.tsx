import { MapPin, Plane, Compass, X } from "lucide-react";
import { cn } from "@/lib/utils";

type DistanceType = "close" | "far" | "offbeat" | "any";

interface DistanceSelectorProps {
  value: DistanceType | null;
  onChange: (value: DistanceType) => void;
}

const DISTANCES = [
  { id: "close", label: "Stay Close", icon: MapPin },
  { id: "far", label: "Go Far", icon: Plane },
  { id: "offbeat", label: "Off the Beaten Path", icon: Compass },
  { id: "any", label: "No Preference", icon: X },
] as const;

const DistanceSelector = ({ value, onChange }: DistanceSelectorProps) => {
  return (
    <div className="space-y-4">
      <label className="block text-xs font-medium text-fog/70 tracking-widest uppercase">
        Distance & Region Preference
      </label>
      
      <div className="flex flex-wrap gap-3">
        {DISTANCES.map((distance, index) => {
          const Icon = distance.icon;
          const isSelected = value === distance.id;
          
          return (
            <button
              key={distance.id}
              type="button"
              onClick={() => onChange(distance.id)}
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
              <span className="text-sm">{distance.label}</span>
              
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

export default DistanceSelector;

