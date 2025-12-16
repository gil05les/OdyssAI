import { 
  Umbrella, 
  Mountain, 
  Building2, 
  Wheat, 
  Sun, 
  TreePalm
} from "lucide-react";
import { cn } from "@/lib/utils";

type EnvironmentType = 
  | "beach" 
  | "mountains" 
  | "city" 
  | "countryside" 
  | "desert"
  | "jungle";

interface EnvironmentSelectorProps {
  selected: EnvironmentType[];
  onChange: (selected: EnvironmentType[]) => void;
}

const ENVIRONMENTS = [
  { id: "beach", label: "Beach", icon: Umbrella },
  { id: "mountains", label: "Mountains", icon: Mountain },
  { id: "city", label: "City", icon: Building2 },
  { id: "countryside", label: "Countryside", icon: Wheat },
  { id: "desert", label: "Desert", icon: Sun },
  { id: "jungle", label: "Jungle/Rainforest", icon: TreePalm },
] as const;

const EnvironmentSelector = ({ selected, onChange }: EnvironmentSelectorProps) => {
  const toggleEnvironment = (id: EnvironmentType) => {
    if (selected.includes(id)) {
      onChange(selected.filter((e) => e !== id));
    } else {
      onChange([...selected, id]);
    }
  };

  return (
    <div className="space-y-4">
      <label className="block text-xs font-medium text-fog/70 tracking-widest uppercase">
        Environment & Landscape
      </label>
      
      <div className="flex flex-wrap gap-3">
        {ENVIRONMENTS.map((environment, index) => {
          const Icon = environment.icon;
          const isSelected = selected.includes(environment.id);
          
          return (
            <button
              key={environment.id}
              type="button"
              onClick={() => toggleEnvironment(environment.id)}
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
              <span className="text-sm">{environment.label}</span>
              
              {isSelected && (
                <span className="w-1.5 h-1.5 bg-fog rounded-full animate-scale-in" />
              )}
            </button>
          );
        })}
      </div>
      
      {selected.length > 0 && (
        <p className="text-sm text-muted-foreground animate-fade-in">
          {selected.length} environment{selected.length > 1 ? 's' : ''} selected
        </p>
      )}
    </div>
  );
};

export default EnvironmentSelector;

