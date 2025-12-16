import { useState } from "react";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { CalendarDays, X } from "lucide-react";
import { format, isWithinInterval, isSameDay, isAfter, isBefore } from "date-fns";
import { DateRange } from "react-day-picker";
import { cn } from "@/lib/utils";

interface DateRangePickerProps {
  value: DateRange[];
  onChange: (ranges: DateRange[]) => void;
}

const DateRangePicker = ({ value, onChange }: DateRangePickerProps) => {
  const [open, setOpen] = useState(false);
  const [pendingStart, setPendingStart] = useState<Date | null>(null);

  const handleDayClick = (day: Date) => {
    // Check if clicking on an already selected date - remove that range
    const existingRangeIndex = value.findIndex(range => {
      if (!range.from) return false;
      if (!range.to) return isSameDay(day, range.from);
      return isWithinInterval(day, { start: range.from, end: range.to });
    });

    if (existingRangeIndex !== -1) {
      // Remove the clicked range
      const newRanges = value.filter((_, i) => i !== existingRangeIndex);
      onChange(newRanges);
      setPendingStart(null);
      return;
    }

    if (pendingStart === null) {
      // Start a new range
      setPendingStart(day);
    } else {
      // Complete the range
      const newRange: DateRange = {
        from: isBefore(day, pendingStart) ? day : pendingStart,
        to: isAfter(day, pendingStart) ? day : pendingStart,
      };
      onChange([...value, newRange]);
      setPendingStart(null);
    }
  };

  const removeRange = (index: number) => {
    onChange(value.filter((_, i) => i !== index));
  };

  const clearAll = () => {
    onChange([]);
    setPendingStart(null);
  };

  // Build modifiers for highlighting
  const selectedDays = value.flatMap(range => {
    if (!range.from) return [];
    if (!range.to) return [range.from];
    const days: Date[] = [];
    let current = new Date(range.from);
    while (current <= range.to) {
      days.push(new Date(current));
      current.setDate(current.getDate() + 1);
    }
    return days;
  });

  const rangeStartDays = value.map(r => r.from).filter(Boolean) as Date[];
  const rangeEndDays = value.map(r => r.to).filter(Boolean) as Date[];

  return (
    <div className="space-y-3">
      <label className="block text-xs font-medium text-fog/70 tracking-widest uppercase">
        Travel Dates
      </label>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            className={cn(
              "w-full justify-start text-left font-normal min-h-14 border-fog/10 bg-midnight-light/30 hover:bg-midnight-light/50 hover:border-gold/30 transition-all duration-300 hover-lift group text-fog",
              value.length === 0 && !pendingStart && "text-muted-foreground"
            )}
          >
            <CalendarDays className="mr-3 h-5 w-5 text-gold group-hover:scale-110 transition-transform duration-300 shrink-0" />
            {value.length > 0 ? (
              <span className="text-sm">
                {value.length} travel window{value.length > 1 ? 's' : ''} selected
              </span>
            ) : pendingStart ? (
              <span className="text-sm">
                {format(pendingStart, "MMM d")} – Select end date
              </span>
            ) : (
              <span>Select your travel windows</span>
            )}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0 border-fog/10 bg-midnight shadow-2xl" align="start">
          <div className="p-4 space-y-4">
            <Calendar
              mode="multiple"
              selected={pendingStart ? [...selectedDays, pendingStart] : selectedDays}
              onDayClick={handleDayClick}
              numberOfMonths={2}
              className="pointer-events-auto"
              modifiers={{
                range_start: rangeStartDays,
                range_end: rangeEndDays,
                range_middle: selectedDays.filter(d => 
                  !rangeStartDays.some(s => isSameDay(d, s)) && 
                  !rangeEndDays.some(e => isSameDay(d, e))
                ),
                pending: pendingStart ? [pendingStart] : [],
              }}
              modifiersClassNames={{
                range_start: "rounded-l-md bg-gold text-midnight",
                range_end: "rounded-r-md bg-gold text-midnight",
                range_middle: "bg-gold/30 text-fog rounded-none",
                pending: "bg-teal text-midnight ring-2 ring-teal-light",
              }}
              disabled={(date) => date < new Date()}
            />
            
            {/* Selected ranges summary */}
            {value.length > 0 && (
              <div className="border-t border-fog/10 pt-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-fog/70 uppercase tracking-wide">
                    Selected Windows
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={clearAll}
                    className="text-xs text-fog/50 hover:text-fog h-6 px-2"
                  >
                    Clear All
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {value.map((range, index) => (
                    <div
                      key={index}
                      className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-gold/20 text-gold text-sm"
                    >
                      <span>
                        {range.from && format(range.from, "MMM d")}
                        {range.to && range.from && !isSameDay(range.from, range.to) && (
                          <> – {format(range.to, "MMM d")}</>
                        )}
                      </span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          removeRange(index);
                        }}
                        className="hover:bg-gold/30 rounded-full p-0.5 transition-colors"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {pendingStart && (
              <p className="text-xs text-teal-light text-center">
                Click another date to complete the range
              </p>
            )}
          </div>
        </PopoverContent>
      </Popover>
      
      {/* Display selected ranges below the button */}
      {value.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {value.map((range, index) => (
            <div
              key={index}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-gold/10 border border-gold/20 text-gold text-xs"
            >
              <span>
                {range.from && format(range.from, "MMM d")}
                {range.to && range.from && !isSameDay(range.from, range.to) && (
                  <> – {format(range.to, "MMM d")}</>
                )}
              </span>
              <button
                onClick={() => removeRange(index)}
                className="hover:bg-gold/20 rounded-full p-0.5 transition-colors"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default DateRangePicker;
