import { Compass, Plane, MapPin, Star, Sparkles, Globe } from "lucide-react";

const FloatingElements = () => {
  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
      {/* Ambient light glow */}
      <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-gold/5 rounded-full blur-[120px]" />
      <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-teal/10 rounded-full blur-[100px]" />
      
      {/* Floating compass */}
      <div className="absolute top-20 left-[10%] animate-float opacity-30">
        <Compass className="w-10 h-10 text-gold" />
      </div>
      
      {/* Drifting plane */}
      <div className="absolute top-32 animate-drift opacity-20">
        <Plane className="w-6 h-6 text-sand rotate-45" />
      </div>
      
      {/* Floating map pin */}
      <div className="absolute top-[40%] left-[5%] animate-float-delayed opacity-25">
        <MapPin className="w-8 h-8 text-gold" />
      </div>
      
      {/* Globe */}
      <div className="absolute top-[20%] right-[8%] animate-float-slow opacity-20">
        <Globe className="w-12 h-12 text-teal" />
      </div>
      
      {/* Stars scattered */}
      <div className="absolute top-[15%] right-[25%] animate-float-slow opacity-30">
        <Star className="w-5 h-5 text-gold fill-gold/50" />
      </div>
      
      <div className="absolute top-[60%] left-[8%] animate-float opacity-25">
        <Star className="w-4 h-4 text-sand fill-sand/30" />
      </div>
      
      {/* Sparkles */}
      <div className="absolute top-[25%] left-[20%] animate-pulse-gold opacity-40">
        <Sparkles className="w-4 h-4 text-gold" />
      </div>
      
      <div className="absolute bottom-[30%] left-[12%] animate-float-delayed opacity-25">
        <Sparkles className="w-5 h-5 text-teal" />
      </div>
      
      {/* Reverse drifting plane */}
      <div className="absolute top-[70%] animate-drift-reverse opacity-15">
        <Plane className="w-5 h-5 text-fog -rotate-45" />
      </div>
      
      {/* Decorative orbital rings */}
      <div className="absolute top-[50%] left-[3%] w-32 h-32 rounded-full border border-gold/10 animate-spin-slow" />
      <div className="absolute bottom-[20%] left-[6%] w-20 h-20 rounded-full border border-teal/15 animate-spin-slow" style={{ animationDirection: 'reverse' }} />
      
      {/* Subtle grid pattern overlay */}
      <div 
        className="absolute inset-0 opacity-[0.02]"
        style={{
          backgroundImage: `linear-gradient(hsl(var(--fog)) 1px, transparent 1px), linear-gradient(90deg, hsl(var(--fog)) 1px, transparent 1px)`,
          backgroundSize: '60px 60px'
        }}
      />
    </div>
  );
};

export default FloatingElements;
