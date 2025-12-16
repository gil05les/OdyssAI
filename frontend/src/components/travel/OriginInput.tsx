import { useState } from "react";
import { Plane } from "lucide-react";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

const ORIGIN_SUGGESTIONS = [
  "Zurich, Switzerland (ZRH)",
  "New York, USA (JFK)",
  "London, UK (LHR)",
  "Paris, France (CDG)",
  "Tokyo, Japan (NRT)",
  "Dubai, UAE (DXB)",
  "Singapore (SIN)",
  "Amsterdam, Netherlands (AMS)",
  "Frankfurt, Germany (FRA)",
  "Barcelona, Spain (BCN)",
];

interface OriginInputProps {
  value: string;
  onChange: (value: string) => void;
}

const OriginInput = ({ value, onChange }: OriginInputProps) => {
  const [inputValue, setInputValue] = useState(value);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const filteredSuggestions = ORIGIN_SUGGESTIONS.filter(
    (s) => s.toLowerCase().includes(inputValue.toLowerCase())
  );

  const handleSelect = (suggestion: string) => {
    setInputValue(suggestion);
    onChange(suggestion);
    setShowSuggestions(false);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setInputValue(newValue);
    onChange(newValue);
    setShowSuggestions(true);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && filteredSuggestions.length > 0) {
      e.preventDefault();
      handleSelect(filteredSuggestions[0]);
    }
  };

  return (
    <div className="space-y-4">
      <label className="block text-xs font-medium text-fog/70 tracking-widest uppercase">
        Departure From
      </label>

      <div className="relative">
        <Plane className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gold" />
        <Input
          value={inputValue}
          onChange={handleChange}
          onFocus={() => setShowSuggestions(true)}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
          onKeyDown={handleKeyDown}
          placeholder="Enter departure city or airport..."
          className="pl-12 h-14 border-fog/10 bg-midnight-light/30 focus:border-gold/30 text-fog placeholder:text-muted-foreground text-base"
        />
        
        {showSuggestions && filteredSuggestions.length > 0 && (
          <div className="absolute top-full left-0 right-0 mt-2 bg-midnight border border-fog/10 rounded-xl shadow-2xl z-50 overflow-hidden animate-fade-in">
            {filteredSuggestions.slice(0, 5).map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                onClick={() => handleSelect(suggestion)}
                className="w-full px-4 py-3 text-left hover:bg-midnight-light/50 transition-colors flex items-center gap-3 text-fog"
              >
                <Plane className="w-4 h-4 text-gold" />
                {suggestion}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default OriginInput;

