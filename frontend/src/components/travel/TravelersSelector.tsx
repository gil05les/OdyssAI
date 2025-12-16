import { User, Users, Heart, UserPlus, Minus, Plus } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

type TravelerType = "solo" | "couple" | "family" | "group";

interface TravelersSelectorProps {
  type: TravelerType;
  onTypeChange: (type: TravelerType) => void;
  groupSize: number;
  onGroupSizeChange: (size: number) => void;
}

const TRAVELER_OPTIONS = [
  { id: "solo", label: "Solo", icon: User },
  { id: "couple", label: "Couple", icon: Heart },
  { id: "family", label: "Family", icon: Users },
  { id: "group", label: "Group", icon: UserPlus },
] as const;

const TravelersSelector = ({ 
  type, 
  onTypeChange, 
  groupSize, 
  onGroupSizeChange 
}: TravelersSelectorProps) => {
  return (
    <div className="space-y-4">
      <label className="block text-xs font-medium text-fog/70 tracking-widest uppercase">
        Travel Companions
      </label>
      
      <div className="grid grid-cols-4 gap-3">
        {TRAVELER_OPTIONS.map((option) => {
          const Icon = option.icon;
          const isSelected = type === option.id;
          
          return (
            <button
              key={option.id}
              type="button"
              onClick={() => onTypeChange(option.id)}
              className={cn(
                "relative flex flex-col items-center justify-center p-4 rounded-xl border transition-all duration-300 hover-lift group",
                isSelected 
                  ? "border-gold bg-gold/15 glow-gold" 
                  : "border-fog/10 bg-midnight-light/30 hover:border-gold/30"
              )}
            >
              <Icon className={cn(
                "w-6 h-6 mb-2 transition-all duration-300",
                isSelected ? "text-gold scale-110" : "text-muted-foreground group-hover:text-gold"
              )} />
              <span className={cn(
                "text-sm transition-colors",
                isSelected ? "text-gold" : "text-fog"
              )}>
                {option.label}
              </span>
              
              {isSelected && (
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-gold rounded-full animate-scale-in" />
              )}
            </button>
          );
        })}
      </div>

      {(type === "family" || type === "group") && (
        <div className="flex items-center justify-between p-4 rounded-xl border border-fog/10 bg-midnight-light/20 animate-fade-in">
          <span className="text-muted-foreground">Number of travelers</span>
          <div className="flex items-center gap-4">
            <Button
              type="button"
              variant="outline"
              size="icon"
              onClick={() => onGroupSizeChange(Math.max(2, groupSize - 1))}
              className="h-9 w-9 rounded-full border-fog/20 hover:border-gold/50 bg-transparent text-fog hover:text-gold"
            >
              <Minus className="w-4 h-4" />
            </Button>
            <span className="font-display text-2xl text-gold w-8 text-center">
              {groupSize}
            </span>
            <Button
              type="button"
              variant="outline"
              size="icon"
              onClick={() => onGroupSizeChange(Math.min(20, groupSize + 1))}
              className="h-9 w-9 rounded-full border-fog/20 hover:border-gold/50 bg-transparent text-fog hover:text-gold"
            >
              <Plus className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default TravelersSelector;
