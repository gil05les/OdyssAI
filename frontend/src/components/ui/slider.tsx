import * as React from "react";
import * as SliderPrimitive from "@radix-ui/react-slider";
import { cn } from "@/lib/utils";

const Slider = React.forwardRef<
  React.ElementRef<typeof SliderPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof SliderPrimitive.Root>
>(({ className, ...props }, ref) => (
  <SliderPrimitive.Root
    ref={ref}
    className={cn("relative flex w-full touch-none select-none items-center", className)}
    {...props}
  >
    <SliderPrimitive.Track className="relative h-2 w-full grow overflow-hidden rounded-full bg-midnight-light">
      <SliderPrimitive.Range className="absolute h-full bg-gradient-to-r from-gold to-gold-light" />
    </SliderPrimitive.Track>
    {(props.value || props.defaultValue || [0]).map((_, index) => (
      <SliderPrimitive.Thumb
        key={index}
        className="block h-5 w-5 rounded-full border-2 border-gold bg-midnight ring-offset-background transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:scale-110 hover:shadow-lg cursor-grab active:cursor-grabbing"
        style={{ boxShadow: '0 0 20px hsl(34 50% 66% / 0.4)' }}
      />
    ))}
  </SliderPrimitive.Root>
));
Slider.displayName = SliderPrimitive.Root.displayName;

export { Slider };
