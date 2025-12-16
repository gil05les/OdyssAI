import { Building2, Home, Castle, Palmtree } from "lucide-react";
import { cn } from "@/lib/utils";

type AccommodationType = "hotel" | "boutique" | "resort" | "villa";

interface AccommodationSelectorProps {
  value: AccommodationType | null;
  onChange: (value: AccommodationType) => void;
}

const ACCOMMODATIONS = [
  { 
    id: "hotel", 
    label: "Hotels", 
    description: "Classic comfort & service",
    icon: Building2 
  },
  { 
    id: "boutique", 
    label: "Boutique", 
    description: "Unique & charming stays",
    icon: Home 
  },
  { 
    id: "resort", 
    label: "Resort", 
    description: "All-inclusive luxury",
    icon: Castle 
  },
  { 
    id: "villa", 
    label: "Villa", 
    description: "Private & exclusive",
    icon: Palmtree 
  },
] as const;

const AccommodationSelector = ({ value, onChange }: AccommodationSelectorProps) => {
  return (
    <div className="space-y-4">
      <label className="block text-xs font-medium text-fog/70 tracking-widest uppercase">
        Accommodation Style
      </label>
      
      <div className="grid grid-cols-2 gap-4">
        {ACCOMMODATIONS.map((accommodation, index) => {
          const Icon = accommodation.icon;
          const isSelected = value === accommodation.id;
          
          return (
            <button
              key={accommodation.id}
              type="button"
              onClick={() => onChange(accommodation.id)}
              className={cn(
                "relative p-5 rounded-xl border text-left transition-all duration-300 hover-lift group overflow-hidden",
                isSelected 
                  ? "border-gold bg-gradient-to-br from-gold/15 to-gold/5 glow-gold" 
                  : "border-fog/10 bg-midnight-light/30 hover:border-gold/30"
              )}
              style={{ animationDelay: `${index * 100}ms` }}
            >
              {/* Background glow */}
              <div className={cn(
                "absolute -right-6 -bottom-6 w-28 h-28 rounded-full transition-all duration-500 blur-2xl",
                isSelected ? "bg-gold/20" : "bg-transparent group-hover:bg-gold/10"
              )} />
              
              <Icon className={cn(
                "w-8 h-8 mb-3 transition-all duration-300 relative z-10",
                isSelected ? "text-gold scale-110" : "text-muted-foreground group-hover:text-gold"
              )} />
              
              <h4 className={cn(
                "font-display text-lg mb-1 relative z-10 transition-colors",
                isSelected ? "text-gold" : "text-fog"
              )}>
                {accommodation.label}
              </h4>
              
              <p className="text-sm text-muted-foreground relative z-10">
                {accommodation.description}
              </p>
              
              {isSelected && (
                <div className="absolute top-3 right-3 w-2 h-2 bg-gold rounded-full animate-pulse-gold" />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default AccommodationSelector;
