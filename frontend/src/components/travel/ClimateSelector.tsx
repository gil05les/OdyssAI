import { Sun, Cloud, Snowflake, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

type ClimateType = "tropical" | "mild" | "cold" | "any";

interface ClimateSelectorProps {
  value: ClimateType | null;
  onChange: (value: ClimateType) => void;
}

const CLIMATES = [
  { id: "tropical", label: "Tropical/Warm", icon: Sun },
  { id: "mild", label: "Mild/Mediterranean", icon: Cloud },
  { id: "cold", label: "Cold/Winter", icon: Snowflake },
  { id: "any", label: "Any/Flexible", icon: Sparkles },
] as const;

const ClimateSelector = ({ value, onChange }: ClimateSelectorProps) => {
  return (
    <div className="space-y-4">
      <label className="block text-xs font-medium text-fog/70 tracking-widest uppercase">
        Climate Preference
      </label>
      
      <div className="flex flex-wrap gap-3">
        {CLIMATES.map((climate, index) => {
          const Icon = climate.icon;
          const isSelected = value === climate.id;
          
          return (
            <button
              key={climate.id}
              type="button"
              onClick={() => onChange(climate.id)}
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
              <span className="text-sm">{climate.label}</span>
              
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

export default ClimateSelector;

