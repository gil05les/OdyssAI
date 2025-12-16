import { useState, useEffect } from "react";
import { Plane, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import DateRangePicker from "./DateRangePicker";
import DurationSlider from "./DurationSlider";
import OriginInput from "./OriginInput";
import DestinationInput from "./DestinationInput";
import TravelersSelector from "./TravelersSelector";
import BudgetSlider from "./BudgetSlider";
import EnvironmentSelector from "./EnvironmentSelector";
import ClimateSelector from "./ClimateSelector";
import TripVibeSelector from "./TripVibeSelector";
import DistanceSelector from "./DistanceSelector";
import PurposeSelector from "./PurposeSelector";
import ExperienceChips from "./ExperienceChips";
import { TripPlanningWorkflow } from "./TripPlanningWorkflow";
import { useTravelForm } from "@/contexts/TravelFormContext";
import { cn } from "@/lib/utils";

const TravelPlannerForm = () => {
  const {
    formState,
    setOrigin,
    setDateRanges,
    setDuration,
    setDestinations,
    setSurpriseMe,
    setTravelerType,
    setGroupSize,
    setBudget,
    setEnvironments,
    setClimate,
    setTripVibe,
    setDistancePreference,
    setTripPurpose,
    setExperiences,
  } = useTravelForm();
  
  const [showWorkflow, setShowWorkflow] = useState(false);
  const [tripRequest, setTripRequest] = useState<any>(null);

  // Test mode: Jump directly to transport step
  useEffect(() => {
    if (window.location.search.includes('test=transport')) {
      // Create a mock trip request
      const mockTripRequest = {
        origin: "Zurich, Switzerland (ZRH)",
        destinations: ["Santorini"],
        surprise_me: false,
        date_ranges: [{ from: "2025-12-22", to: "2025-12-29" }],
        duration: 7,
        traveler_type: "couple",
        group_size: 2,
        budget: 5000,
        environments: ["coastal"],
        climate: "warm",
        trip_vibe: "romantic",
        distance_preference: "medium",
        trip_purpose: "leisure",
        experiences: ["relaxation", "culture"]
      };
      setTripRequest(mockTripRequest);
      setShowWorkflow(true);
    }
  }, []);

  const handleSubmit = () => {
    // Convert date ranges to the format expected by the API
    const formattedDateRanges = formState.dateRanges
      .filter(range => range.from && range.to)
      .map(range => ({
        from: range.from!.toISOString().split('T')[0],
        to: range.to!.toISOString().split('T')[0],
      }));

    // Create trip request object
    const request = {
      origin: formState.origin || "Zurich, Switzerland (ZRH)", // Default if not specified
      destinations: formState.destinations,
      surprise_me: formState.surpriseMe,
      date_ranges: formattedDateRanges,
      duration: formState.duration,
      traveler_type: formState.travelerType,
      group_size: formState.groupSize,
      budget: formState.budget,
      environments: formState.environments,
      climate: formState.climate,
      trip_vibe: formState.tripVibe,
      distance_preference: formState.distancePreference,
      trip_purpose: formState.tripPurpose,
      experiences: formState.experiences,
    };

    setTripRequest(request);
    setShowWorkflow(true);
  };

  const handleReset = () => {
    setShowWorkflow(false);
    setTripRequest(null);
  };

  if (showWorkflow && tripRequest) {
    return <TripPlanningWorkflow tripRequest={tripRequest} onReset={handleReset} />;
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center space-y-6 animate-fade-up">
        <div className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full glass-teal text-teal-light text-sm font-medium tracking-wide">
          <Sparkles className="w-4 h-4 animate-pulse-gold" />
          <span>AI-Powered Planning</span>
        </div>
        <h1 className="font-display text-4xl md:text-5xl lg:text-6xl text-fog leading-tight">
          Plan Your Perfect
          <span className="block text-gradient-gold mt-2">Journey</span>
        </h1>
        <p className="text-muted-foreground text-lg max-w-xl mx-auto leading-relaxed">
          Tell us your travel dreams, and our AI will craft a personalized itinerary 
          tailored just for you.
        </p>
      </div>

      {/* Form Sections */}
      <div className="space-y-6">
        {/* Section 1: When */}
        <section className="p-6 rounded-2xl glass-sand animate-fade-up" style={{ animationDelay: "100ms" }}>
          <div className="grid md:grid-cols-2 gap-6">
            <DateRangePicker value={formState.dateRanges} onChange={setDateRanges} />
            <DurationSlider value={formState.duration} onChange={setDuration} />
          </div>
        </section>

        {/* Section 2: Where */}
        <section className="p-6 rounded-2xl glass-sand animate-fade-up relative z-20" style={{ animationDelay: "200ms" }}>
          <div className="space-y-6">
            <OriginInput value={formState.origin} onChange={setOrigin} />
            <DestinationInput 
              destinations={formState.destinations}
              onChange={setDestinations}
              surpriseMe={formState.surpriseMe}
              onSurpriseMeChange={setSurpriseMe}
            />
          </div>
        </section>

        {/* Section 3: Who & How Much */}
        <section className="p-6 rounded-2xl glass-sand animate-fade-up relative z-10" style={{ animationDelay: "300ms" }}>
          <div className="grid md:grid-cols-2 gap-8">
            <TravelersSelector 
              type={formState.travelerType}
              onTypeChange={setTravelerType}
              groupSize={formState.groupSize}
              onGroupSizeChange={setGroupSize}
            />
            <BudgetSlider value={formState.budget} onChange={setBudget} />
          </div>
        </section>

        {/* Section 4: Environment */}
        <section className="p-6 rounded-2xl glass-sand animate-fade-up" style={{ animationDelay: "400ms" }}>
          <EnvironmentSelector selected={formState.environments} onChange={setEnvironments} />
        </section>

        {/* Section 5: Preferences */}
        <section className="p-6 rounded-2xl glass-sand animate-fade-up" style={{ animationDelay: "500ms" }}>
          <div className="space-y-6">
            <ClimateSelector value={formState.climate} onChange={setClimate} />
            <TripVibeSelector value={formState.tripVibe} onChange={setTripVibe} />
            <DistanceSelector value={formState.distancePreference} onChange={setDistancePreference} />
            <PurposeSelector value={formState.tripPurpose} onChange={setTripPurpose} />
          </div>
        </section>

        {/* Section 6: Experience */}
        <section className="p-6 rounded-2xl glass-sand animate-fade-up" style={{ animationDelay: "600ms" }}>
          <ExperienceChips selected={formState.experiences} onChange={setExperiences} />
        </section>

        {/* Submit Button */}
        <div className="pt-6 animate-fade-up" style={{ animationDelay: "700ms" }}>
          <Button
            onClick={handleSubmit}
            size="lg"
            className={cn(
              "w-full h-16 text-lg font-display rounded-xl transition-all duration-500",
              "bg-gradient-to-r from-gold to-gold-light text-midnight hover:from-gold-light hover:to-gold",
              "hover-glow hover:scale-[1.02]"
            )}
          >
            <div className="flex items-center gap-3">
              <Plane className="w-5 h-5" />
              <span>Plan My Trip</span>
              <Sparkles className="w-5 h-5" />
            </div>
          </Button>
        </div>
      </div>
    </div>
  );
};

export default TravelPlannerForm;
