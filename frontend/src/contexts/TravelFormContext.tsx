import { createContext, useContext, useState, ReactNode } from "react";
import { DateRange } from "react-day-picker";

type TravelerType = "solo" | "couple" | "family" | "group";
type AccommodationType = "hotel" | "boutique" | "resort" | "villa";
type EnvironmentType = "beach" | "mountains" | "city" | "countryside" | "desert" | "jungle";
type ClimateType = "tropical" | "mild" | "cold" | "any";
type TripVibeType = "relaxing" | "active" | "balanced" | "party";
type DistanceType = "close" | "far" | "offbeat" | "any";
type PurposeType = "vacation" | "workation" | "honeymoon" | "reunion";
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

interface TravelFormState {
  origin: string;
  dateRanges: DateRange[];
  duration: [number, number];
  destinations: string[];
  surpriseMe: boolean;
  travelerType: TravelerType;
  groupSize: number;
  budget: [number, number];
  accommodation: AccommodationType | null;
  environments: EnvironmentType[];
  climate: ClimateType | null;
  tripVibe: TripVibeType | null;
  distancePreference: DistanceType | null;
  tripPurpose: PurposeType | null;
  experiences: ExperienceType[];
}

interface TravelFormContextType {
  formState: TravelFormState;
  updateFormState: (updates: Partial<TravelFormState>) => void;
  setOrigin: (origin: string) => void;
  setDateRanges: (ranges: DateRange[]) => void;
  setDuration: (duration: [number, number]) => void;
  setDestinations: (destinations: string[]) => void;
  setSurpriseMe: (surprise: boolean) => void;
  setTravelerType: (type: TravelerType) => void;
  setGroupSize: (size: number) => void;
  setBudget: (budget: [number, number]) => void;
  setAccommodation: (accommodation: AccommodationType | null) => void;
  setEnvironments: (environments: EnvironmentType[]) => void;
  setClimate: (climate: ClimateType | null) => void;
  setTripVibe: (tripVibe: TripVibeType | null) => void;
  setDistancePreference: (distancePreference: DistanceType | null) => void;
  setTripPurpose: (tripPurpose: PurposeType | null) => void;
  setExperiences: (experiences: ExperienceType[]) => void;
}

const defaultState: TravelFormState = {
  origin: "",
  dateRanges: [],
  duration: [5, 10],
  destinations: [],
  surpriseMe: false,
  travelerType: "couple",
  groupSize: 4,
  budget: [3000, 8000],
  accommodation: null,
  environments: [],
  climate: null,
  tripVibe: null,
  distancePreference: null,
  tripPurpose: null,
  experiences: [],
};

const TravelFormContext = createContext<TravelFormContextType | undefined>(undefined);

export const TravelFormProvider = ({ children }: { children: ReactNode }) => {
  const [formState, setFormState] = useState<TravelFormState>(defaultState);

  const updateFormState = (updates: Partial<TravelFormState>) => {
    setFormState(prev => ({ ...prev, ...updates }));
  };

  return (
    <TravelFormContext.Provider
      value={{
        formState,
        updateFormState,
        setOrigin: (origin) => updateFormState({ origin }),
        setDateRanges: (ranges) => updateFormState({ dateRanges: ranges }),
        setDuration: (duration) => updateFormState({ duration }),
        setDestinations: (destinations) => updateFormState({ destinations }),
        setSurpriseMe: (surprise) => updateFormState({ surpriseMe: surprise }),
        setTravelerType: (type) => updateFormState({ travelerType: type }),
        setGroupSize: (size) => updateFormState({ groupSize: size }),
        setBudget: (budget) => updateFormState({ budget }),
        setAccommodation: (accommodation) => updateFormState({ accommodation }),
        setEnvironments: (environments) => updateFormState({ environments }),
        setClimate: (climate) => updateFormState({ climate }),
        setTripVibe: (tripVibe) => updateFormState({ tripVibe }),
        setDistancePreference: (distancePreference) => updateFormState({ distancePreference }),
        setTripPurpose: (tripPurpose) => updateFormState({ tripPurpose }),
        setExperiences: (experiences) => updateFormState({ experiences }),
      }}
    >
      {children}
    </TravelFormContext.Provider>
  );
};

export const useTravelForm = () => {
  const context = useContext(TravelFormContext);
  if (!context) {
    throw new Error("useTravelForm must be used within TravelFormProvider");
  }
  return context;
};






