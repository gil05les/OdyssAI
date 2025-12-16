import { Wine, Laptop, Heart, Users } from "lucide-react";
import { cn } from "@/lib/utils";

type PurposeType = "vacation" | "workation" | "honeymoon" | "reunion";

interface PurposeSelectorProps {
  value: PurposeType | null;
  onChange: (value: PurposeType) => void;
}

const PURPOSES = [
  { id: "vacation", label: "Pure Vacation", icon: Wine },
  { id: "workation", label: "Workation", icon: Laptop },
  { id: "honeymoon", label: "Honeymoon/Special Occasion", icon: Heart },
  { id: "reunion", label: "Family Reunion", icon: Users },
] as const;

const PurposeSelector = ({ value, onChange }: PurposeSelectorProps) => {
  return (
    <div className="space-y-4">
      <label className="block text-xs font-medium text-fog/70 tracking-widest uppercase">
        Primary Purpose
      </label>
      
      <div className="flex flex-wrap gap-3">
        {PURPOSES.map((purpose, index) => {
          const Icon = purpose.icon;
          const isSelected = value === purpose.id;
          
          return (
            <button
              key={purpose.id}
              type="button"
              onClick={() => onChange(purpose.id)}
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
              <span className="text-sm">{purpose.label}</span>
              
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

export default PurposeSelector;

