import { Slider } from "@/components/ui/slider";
import { Clock } from "lucide-react";

interface DurationSliderProps {
  value: [number, number];
  onChange: (value: [number, number]) => void;
}

const DurationSlider = ({ value, onChange }: DurationSliderProps) => {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label className="block text-xs font-medium text-fog/70 tracking-widest uppercase">
          Trip Duration
        </label>
        <div className="flex items-center gap-2 text-gold font-display text-lg">
          <Clock className="w-4 h-4" />
          <span>{value[0]} – {value[1]} days</span>
        </div>
      </div>
      
      <div className="pt-2 pb-4">
        <Slider
          value={value}
          onValueChange={(v) => onChange(v as [number, number])}
          min={1}
          max={30}
          step={1}
          className="w-full"
        />
      </div>
      
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>1 day</span>
        <span>30 days</span>
      </div>
    </div>
  );
};

export default DurationSlider;
