import { 
  Mountain, 
  Waves, 
  Landmark, 
  UtensilsCrossed, 
  Music, 
  TreePine,
  Camera,
  ShoppingBag,
  Heart,
  Dumbbell
} from "lucide-react";
import { cn } from "@/lib/utils";

type ExperienceType = 
  | "adventure" 
  | "relaxation" 
  | "cultural" 
  | "food" 
  | "nightlife" 
  | "nature"
  | "photography"
  | "shopping"
  | "romance"
  | "wellness";

interface ExperienceChipsProps {
  selected: ExperienceType[];
  onChange: (selected: ExperienceType[]) => void;
}

const EXPERIENCES = [
  { id: "adventure", label: "Adventure", icon: Mountain },
  { id: "relaxation", label: "Relaxation", icon: Waves },
  { id: "cultural", label: "Cultural", icon: Landmark },
  { id: "food", label: "Food & Dining", icon: UtensilsCrossed },
  { id: "nightlife", label: "Nightlife", icon: Music },
  { id: "nature", label: "Nature", icon: TreePine },
  { id: "photography", label: "Photography", icon: Camera },
  { id: "shopping", label: "Shopping", icon: ShoppingBag },
  { id: "romance", label: "Romance", icon: Heart },
  { id: "wellness", label: "Wellness", icon: Dumbbell },
] as const;

const ExperienceChips = ({ selected, onChange }: ExperienceChipsProps) => {
  const toggleExperience = (id: ExperienceType) => {
    if (selected.includes(id)) {
      onChange(selected.filter((e) => e !== id));
    } else {
      onChange([...selected, id]);
    }
  };

  return (
    <div className="space-y-4">
      <label className="block text-xs font-medium text-fog/70 tracking-widest uppercase">
        Experiences & Activities
      </label>
      
      <div className="flex flex-wrap gap-3">
        {EXPERIENCES.map((experience, index) => {
          const Icon = experience.icon;
          const isSelected = selected.includes(experience.id);
          
          return (
            <button
              key={experience.id}
              type="button"
              onClick={() => toggleExperience(experience.id)}
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
              <span className="text-sm">{experience.label}</span>
              
              {isSelected && (
                <span className="w-1.5 h-1.5 bg-fog rounded-full animate-scale-in" />
              )}
            </button>
          );
        })}
      </div>
      
      {selected.length > 0 && (
        <p className="text-sm text-muted-foreground animate-fade-in">
          {selected.length} experience{selected.length > 1 ? 's' : ''} selected
        </p>
      )}
    </div>
  );
};

export default ExperienceChips;
