import { useState, useEffect, useMemo } from 'react';
import {
  DndContext,
  DragEndEvent,
  DragOverlay,
  PointerSensor,
  KeyboardSensor,
  useSensor,
  useSensors,
  closestCenter,
} from '@dnd-kit/core';
import {
  SortableContext,
  arrayMove,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { AgentSearchingAnimation } from '../AgentSearchingAnimation';
import { Activity, Destination } from '@/data/mockAgentData';
import { Button } from '@/components/ui/button';
import { ArrowRight, ArrowLeft, X as XIcon } from 'lucide-react';
import { generateItinerary, ItineraryDayResponse, ItineraryActivityResponse, TripRequest } from '@/services/api';
import { ItineraryActivityPool } from './ItineraryActivityPool';
import { ItineraryDayColumn } from './ItineraryDayColumn';
import { ItineraryActivityCard } from './ItineraryActivityCard';
import { CustomActivityDialog } from './CustomActivityDialog';

interface ItineraryAgentProps {
  destination: Destination;
  tripRequest: TripRequest;
  onSelect: (activities: Activity[]) => void;
  onBack: () => void;
}

// Map backend activity to frontend Activity format
const mapActivityToFrontend = (backendActivity: ItineraryActivityResponse): Activity => {
  const categoryImages: Record<string, string> = {
    'Culture': 'https://images.unsplash.com/photo-1603565816030-6b389eeb23cb?w=400',
    'Food': 'https://images.unsplash.com/photo-1544124499-58912cbddaad?w=400',
    'Adventure': 'https://images.unsplash.com/photo-1500514966906-fe245eea9344?w=400',
    'Nature': 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=400',
    'Wellness': 'https://images.unsplash.com/photo-1544161515-4ab6ce6db874?w=400',
    'Shopping': 'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400',
    'Entertainment': 'https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=400',
  };
  
  const image = backendActivity.image || categoryImages[backendActivity.category] || 'https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=400';
  
  return {
    id: backendActivity.id,
    name: backendActivity.name,
    description: backendActivity.description,
    duration: backendActivity.duration,
    price: backendActivity.estimated_price,
    image: image,
    category: backendActivity.category,
  };
};

export const ItineraryAgent = ({ destination, tripRequest, onSelect, onBack }: ItineraryAgentProps) => {
  const [isSearching, setIsSearching] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [itineraryDays, setItineraryDays] = useState<ItineraryDayResponse[]>([]);
  
  // Drag-and-drop state
  const [activityPool, setActivityPool] = useState<Map<string, Activity>>(new Map());
  const [dayAssignments, setDayAssignments] = useState<Map<number, string[]>>(new Map());
  const [customActivityIds, setCustomActivityIds] = useState<Set<string>>(new Set());
  const [activeId, setActiveId] = useState<string | null>(null);
  const [customDialogOpen, setCustomDialogOpen] = useState(false);
  const [customDialogTargetDay, setCustomDialogTargetDay] = useState<number | undefined>();
  const [editingActivity, setEditingActivity] = useState<Activity | undefined>();

  // Sensors for drag and drop
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor)
  );

  // Calculate number of days
  const numDays = useMemo(() => {
    if (tripRequest.date_ranges && tripRequest.date_ranges.length > 0) {
      const dateRange = tripRequest.date_ranges[0];
      if (dateRange.from && dateRange.to) {
        const from = new Date(dateRange.from);
        const to = new Date(dateRange.to);
        const diffTime = Math.abs(to.getTime() - from.getTime());
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        return Math.max(1, diffDays);
      }
    }
    return tripRequest.duration[1] || 3;
  }, [tripRequest]);

  // Fetch itinerary from backend
  useEffect(() => {
    const fetchItinerary = async () => {
      try {
        setIsSearching(true);
        setError(null);

        const days = await generateItinerary({
          destination: destination.name,
          country: destination.country,
          num_days: numDays,
          experiences: tripRequest.experiences || [],
          budget: tripRequest.budget,
          traveler_type: tripRequest.traveler_type,
          group_size: tripRequest.group_size,
        });

        setItineraryDays(days);
        
        // Extract all activities to pool
        const pool = new Map<string, Activity>();
        days.forEach((day) => {
          day.suggested_activities.forEach((backendActivity) => {
            const activity = mapActivityToFrontend(backendActivity);
            pool.set(activity.id, activity);
          });
        });
        
        setActivityPool(pool);
        // Initialize day assignments with AI suggestions (pre-populate the plan)
        const assignments = new Map<number, string[]>();
        days.forEach((day) => {
          const activityIds = day.suggested_activities.map((a) => a.id);
          assignments.set(day.day, activityIds);
        });
        setDayAssignments(assignments);
      } catch (err) {
        console.error('Failed to generate itinerary:', err);
        setError(err instanceof Error ? err.message : 'Failed to generate itinerary');
      } finally {
        setIsSearching(false);
      }
    };

    fetchItinerary();
  }, [destination, tripRequest, numDays]);

  // Get activities in pool (not assigned to any day)
  const poolActivities = useMemo(() => {
    const assignedIds = new Set<string>();
    dayAssignments.forEach((ids) => {
      ids.forEach((id) => assignedIds.add(id));
    });
    
    return Array.from(activityPool.values()).filter(
      (activity) => !assignedIds.has(activity.id)
    );
  }, [activityPool, dayAssignments]);

  // Get activities for a specific day
  const getDayActivities = (day: number): Activity[] => {
    const activityIds = dayAssignments.get(day) || [];
    return activityIds
      .map((id) => activityPool.get(id))
      .filter((a): a is Activity => a !== undefined);
  };

  // Handle drag end
  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveId(null);

    if (!over) return;

    const activityId = active.id as string;
    const source = active.data.current?.source; // 'pool' | number
    const destination = over.data.current?.destination; // 'pool' | number

    // Pool → Day: Add to day
    if (source === 'pool' && typeof destination === 'number') {
      const currentDayActivities = dayAssignments.get(destination) || [];
      if (!currentDayActivities.includes(activityId)) {
        setDayAssignments((prev) => {
          const next = new Map(prev);
          next.set(destination, [...currentDayActivities, activityId]);
          return next;
        });
      }
    }
    // Day → Day: Move between days or reorder
    else if (typeof source === 'number' && typeof destination === 'number') {
      if (source === destination) {
        // Reorder within same day
        const sourceActivities = dayAssignments.get(source) || [];
        const overId = over.id as string;
        const sourceIndex = sourceActivities.indexOf(activityId);
        const overIndex = sourceActivities.indexOf(overId);
        
        if (sourceIndex !== -1 && overIndex !== -1 && sourceIndex !== overIndex) {
          setDayAssignments((prev) => {
            const next = new Map(prev);
            const activities = next.get(source) || [];
            next.set(source, arrayMove(activities, sourceIndex, overIndex));
            return next;
          });
        }
      } else {
        // Move to different day
        setDayAssignments((prev) => {
          const next = new Map(prev);
          const sourceActivities = next.get(source) || [];
          const destActivities = next.get(destination) || [];
          
          next.set(source, sourceActivities.filter((id) => id !== activityId));
          if (!destActivities.includes(activityId)) {
            next.set(destination, [...destActivities, activityId]);
          }
          return next;
        });
      }
    }
    // Day → Pool: Remove from day
    else if (typeof source === 'number' && destination === 'pool') {
      setDayAssignments((prev) => {
        const next = new Map(prev);
        const dayActivities = next.get(source) || [];
        next.set(source, dayActivities.filter((id) => id !== activityId));
        return next;
      });
    }
  };

  // Handle reorder within day (handled by SortableContext automatically)

  // Add custom activity
  const handleAddCustomActivity = (activity: Activity, targetDay?: number) => {
    setActivityPool((prev) => {
      const next = new Map(prev);
      next.set(activity.id, activity);
      return next;
    });
    setCustomActivityIds((prev) => new Set(prev).add(activity.id));

    if (targetDay !== undefined) {
      // Add directly to day
      const dayActivities = dayAssignments.get(targetDay) || [];
      setDayAssignments((prev) => {
        const next = new Map(prev);
        next.set(targetDay, [...dayActivities, activity.id]);
        return next;
      });
    }
  };

  // Edit custom activity
  const handleEditActivity = (activity: Activity) => {
    setEditingActivity(activity);
    setCustomDialogOpen(true);
  };

  // Save edited activity
  const handleSaveEditedActivity = (activity: Activity) => {
    setActivityPool((prev) => {
      const next = new Map(prev);
      next.set(activity.id, activity);
      return next;
    });
    setEditingActivity(undefined);
  };

  // Remove activity from pool
  const handleRemoveFromPool = (activityId: string) => {
    setActivityPool((prev) => {
      const next = new Map(prev);
      next.delete(activityId);
      return next;
    });
    setCustomActivityIds((prev) => {
      const next = new Set(prev);
      next.delete(activityId);
      return next;
    });
  };

  // Remove activity from day
  const handleRemoveFromDay = (activityId: string, day: number) => {
    setDayAssignments((prev) => {
      const next = new Map(prev);
      const dayActivities = next.get(day) || [];
      next.set(day, dayActivities.filter((id) => id !== activityId));
      return next;
    });
  };

  // Get all selected activities for workflow
  const getSelectedActivities = (): Activity[] => {
    const activities: Activity[] = [];
    dayAssignments.forEach((activityIds) => {
      activityIds.forEach((id) => {
        const activity = activityPool.get(id);
        if (activity) {
          activities.push(activity);
        }
      });
    });
    return activities;
  };

  const handleContinue = () => {
    const selected = getSelectedActivities();
    onSelect(selected);
  };

  const activeActivity = activeId ? activityPool.get(activeId) : null;

  if (isSearching) {
    return (
      <AgentSearchingAnimation
        agentType="itinerary"
        searchText={`Crafting your perfect ${destination.name} experience...`}
      />
    );
  }

  if (error) {
    return (
      <div className="animate-fade-in max-w-2xl mx-auto">
        <div className="text-center p-8 rounded-2xl glass-sand">
          <XIcon className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-serif text-fog mb-2">Itinerary Generation Failed</h2>
          <p className="text-fog/70 mb-6">{error}</p>
          <div className="flex justify-center gap-4">
            <Button
              variant="ghost"
              onClick={onBack}
              className="text-fog/80 hover:text-fog"
            >
              <ArrowLeft className="w-4 h-4 mr-2" /> Back
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (itineraryDays.length === 0) {
    return (
      <div className="animate-fade-in max-w-2xl mx-auto">
        <div className="text-center p-8 rounded-2xl glass-sand">
          <h2 className="text-xl font-serif text-fog mb-2">No Itinerary Generated</h2>
          <p className="text-fog/70 mb-6">Unable to generate itinerary suggestions.</p>
          <Button
            variant="ghost"
            onClick={onBack}
            className="text-fog/80 hover:text-fog"
          >
            <ArrowLeft className="w-4 h-4 mr-2" /> Back
          </Button>
        </div>
      </div>
    );
  }

  const totalSelected = Array.from(dayAssignments.values()).reduce(
    (sum, ids) => sum + ids.length,
    0
  );

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={(event) => setActiveId(event.active.id as string)}
      onDragEnd={handleDragEnd}
    >
      <div className="animate-fade-in flex flex-col min-h-[600px]">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-serif text-fog mb-2">Your Curated Itinerary</h2>
          <p className="text-fog/90">
            We've planned your {numDays}-day trip! Drag to reorder, remove, or add custom activities.
          </p>
        </div>

        <div className="flex-1 flex gap-4 min-h-[500px]">
          {/* Activity Pool Sidebar */}
          <ItineraryActivityPool
            activities={poolActivities}
            customActivityIds={customActivityIds}
            onRemove={handleRemoveFromPool}
            onEdit={handleEditActivity}
            onAddCustom={() => {
              setCustomDialogTargetDay(undefined);
              setCustomDialogOpen(true);
            }}
          />

          {/* Days Area - Vertical Stack */}
          <div className="flex-1 overflow-y-auto">
            <div className="space-y-4 pb-4">
              {itineraryDays.map((day) => {
                const dayActivities = getDayActivities(day.day);
                return (
                  <ItineraryDayColumn
                    key={day.day}
                    day={day.day}
                    dateLabel={day.date_label}
                    activities={dayActivities}
                    customActivityIds={customActivityIds}
                    onRemove={handleRemoveFromDay}
                    onEdit={handleEditActivity}
                    onAddCustom={(dayNum) => {
                      setCustomDialogTargetDay(dayNum);
                      setCustomDialogOpen(true);
                    }}
                  />
                );
              })}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-between items-center mt-6 pt-4 border-t border-fog/20">
          <Button
            variant="ghost"
            onClick={onBack}
            className="text-fog/80 hover:text-fog"
          >
            <ArrowLeft className="w-4 h-4 mr-2" /> Back
          </Button>
          <div className="flex items-center gap-4">
            <span className="text-sm text-fog/60">
              {totalSelected} activity{totalSelected !== 1 ? 'ies' : ''} selected
            </span>
            <Button
              onClick={handleContinue}
              disabled={totalSelected === 0}
              className="bg-gold hover:bg-gold/90 text-midnight px-8"
            >
              Continue to Transport <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        </div>
      </div>

      {/* Drag Overlay */}
      <DragOverlay>
        {activeActivity ? (
          <div className="opacity-90">
            <ItineraryActivityCard
              activity={activeActivity}
              source={
                Array.from(dayAssignments.entries()).find(([, ids]) =>
                  ids.includes(activeActivity.id)
                )?.[0] || 'pool'
              }
              compact={true}
            />
          </div>
        ) : null}
      </DragOverlay>

      {/* Custom Activity Dialog */}
      <CustomActivityDialog
        open={customDialogOpen}
        onOpenChange={(open) => {
          setCustomDialogOpen(open);
          if (!open) {
            setEditingActivity(undefined);
            setCustomDialogTargetDay(undefined);
          }
        }}
        onSave={(activity) => {
          if (editingActivity) {
            handleSaveEditedActivity(activity);
          } else {
            handleAddCustomActivity(activity, customDialogTargetDay);
          }
        }}
        targetDay={customDialogTargetDay}
        existingActivity={editingActivity}
      />
    </DndContext>
  );
};
