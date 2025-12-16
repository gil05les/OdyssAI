import { useState } from "react";
import { MapPin, Sparkles, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { cn } from "@/lib/utils";

const SUGGESTIONS = [
  "Paris, France",
  "Tokyo, Japan",
  "Santorini, Greece",
  "Bali, Indonesia",
  "Maldives",
  "Swiss Alps",
  "Amalfi Coast, Italy",
  "Kyoto, Japan",
];

interface DestinationInputProps {
  destinations: string[];
  onChange: (destinations: string[]) => void;
  surpriseMe: boolean;
  onSurpriseMeChange: (value: boolean) => void;
}

const DestinationInput = ({ 
  destinations, 
  onChange, 
  surpriseMe, 
  onSurpriseMeChange 
}: DestinationInputProps) => {
  const [inputValue, setInputValue] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(false);

  const filteredSuggestions = SUGGESTIONS.filter(
    (s) => 
      s.toLowerCase().includes(inputValue.toLowerCase()) &&
      !destinations.includes(s)
  );

  const addDestination = (dest: string) => {
    if (!destinations.includes(dest)) {
      onChange([...destinations, dest]);
    }
    setInputValue("");
    setShowSuggestions(false);
  };

  const removeDestination = (dest: string) => {
    onChange(destinations.filter((d) => d !== dest));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && inputValue.trim()) {
      e.preventDefault();
      addDestination(inputValue.trim());
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label className="block text-xs font-medium text-fog/70 tracking-widest uppercase">
          Destinations
        </label>
        <div className="flex items-center gap-3">
          <Sparkles className={cn(
            "w-4 h-4 transition-all duration-500",
            surpriseMe ? "text-teal animate-pulse-gold" : "text-muted-foreground"
          )} />
          <span className="text-sm text-muted-foreground">Surprise me</span>
          <Switch
            checked={surpriseMe}
            onCheckedChange={onSurpriseMeChange}
          />
        </div>
      </div>

      <div className={cn(
        "transition-all duration-500",
        surpriseMe && "opacity-50 pointer-events-none"
      )}>
        <div className="relative">
          <MapPin className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gold" />
          <Input
            value={inputValue}
            onChange={(e) => {
              setInputValue(e.target.value);
              setShowSuggestions(true);
            }}
            onFocus={() => setShowSuggestions(true)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
            onKeyDown={handleKeyDown}
            placeholder="Search destinations..."
            className="pl-12 h-14 border-fog/10 bg-midnight-light/30 focus:border-gold/30 text-fog placeholder:text-muted-foreground text-base"
          />
          
          {showSuggestions && filteredSuggestions.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-2 bg-midnight border border-fog/10 rounded-xl shadow-2xl z-50 overflow-hidden animate-fade-in">
              {filteredSuggestions.slice(0, 5).map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  onClick={() => addDestination(suggestion)}
                  className="w-full px-4 py-3 text-left hover:bg-midnight-light/50 transition-colors flex items-center gap-3 text-fog"
                >
                  <MapPin className="w-4 h-4 text-gold" />
                  {suggestion}
                </button>
              ))}
            </div>
          )}
        </div>

        {destinations.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-4">
            {destinations.map((dest) => (
              <Badge
                key={dest}
                className="px-4 py-2 text-sm hover-lift cursor-pointer group bg-gold/20 text-gold border-gold/30 hover:bg-gold/30"
              >
                {dest}
                <X 
                  className="w-3 h-3 ml-2 opacity-50 group-hover:opacity-100 transition-opacity cursor-pointer" 
                  onClick={() => removeDestination(dest)}
                />
              </Badge>
            ))}
          </div>
        )}
      </div>

      {surpriseMe && (
        <p className="text-sm text-teal italic animate-fade-in flex items-center gap-2">
          <Sparkles className="w-4 h-4" />
          We'll curate the perfect surprise destinations for you
        </p>
      )}
    </div>
  );
};

export default DestinationInput;
