import { Slider } from "@/components/ui/slider";
import { DollarSign } from "lucide-react";
import { cn } from "@/lib/utils";

interface BudgetSliderProps {
  value: [number, number];
  onChange: (value: [number, number]) => void;
}

const BUDGET_TIERS = [
  { label: "Budget", max: 2000, color: "text-muted-foreground" },
  { label: "Moderate", max: 5000, color: "text-fog" },
  { label: "Luxury", max: 10000, color: "text-gold" },
  { label: "Ultra Luxury", max: 25000, color: "text-teal" },
];

const BudgetSlider = ({ value, onChange }: BudgetSliderProps) => {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-CH", {
      style: "currency",
      currency: "CHF",
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const getCurrentTier = () => {
    const avg = (value[0] + value[1]) / 2;
    return BUDGET_TIERS.find((tier) => avg <= tier.max) || BUDGET_TIERS[BUDGET_TIERS.length - 1];
  };

  const currentTier = getCurrentTier();

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label className="block text-xs font-medium text-fog/70 tracking-widest uppercase">
          Budget Range
        </label>
        <div className={cn("flex items-center gap-1 font-display text-lg", currentTier.color)}>
          <DollarSign className="w-4 h-4" />
          <span>{formatCurrency(value[0])} – {formatCurrency(value[1])}</span>
        </div>
      </div>

      <div className="pt-2 pb-4">
        <Slider
          value={value}
          onValueChange={(v) => onChange(v as [number, number])}
          min={500}
          max={25000}
          step={500}
          className="w-full"
        />
      </div>

      <div className="flex justify-between items-center">
        <span className="text-xs text-muted-foreground">CHF 500</span>
        <div className={cn(
          "px-4 py-1.5 rounded-full text-sm transition-all duration-300",
          currentTier.color,
          "bg-midnight-light/50 border border-current/20"
        )}>
          {currentTier.label}
        </div>
        <span className="text-xs text-muted-foreground">CHF 25,000+</span>
      </div>
    </div>
  );
};

export default BudgetSlider;
