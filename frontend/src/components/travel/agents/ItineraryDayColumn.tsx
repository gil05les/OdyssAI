import { useDroppable } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy, useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Activity } from '@/data/mockAgentData';
import { ItineraryActivityCard } from './ItineraryActivityCard';
import { Button } from '@/components/ui/button';
import { Plus, X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ItineraryDayColumnProps {
  day: number;
  dateLabel: string;
  activities: Activity[];
  customActivityIds: Set<string>;
  onRemove: (activityId: string, day: number) => void;
  onEdit: (activity: Activity) => void;
  onAddCustom: (day: number) => void;
}

interface SortableActivityItemProps {
  activity: Activity;
  day: number;
  customActivityIds: Set<string>;
  onRemove: (activityId: string, day: number) => void;
  onEdit: (activity: Activity) => void;
}

const SortableActivityItem = ({
  activity,
  day,
  customActivityIds,
  onRemove,
  onEdit,
}: SortableActivityItemProps) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: activity.id,
    data: {
      activity,
      source: day,
    },
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      className={cn(
        isDragging && 'opacity-50 z-50',
        !isDragging && 'cursor-grab active:cursor-grabbing'
      )}
    >
      <ItineraryActivityCard
        activity={activity}
        source={day}
        isCustom={customActivityIds.has(activity.id)}
        onEdit={onEdit}
        onRemove={(id) => onRemove(id, day)}
        showRemove={true}
        isSortable={true}
      />
    </div>
  );
};

const TIME_SLOTS = [
  { id: 'morning', label: 'Morning', color: 'bg-gold/5' },
  { id: 'afternoon', label: 'Afternoon', color: 'bg-teal/5' },
  { id: 'evening', label: 'Evening', color: 'bg-fog/5' },
];

export const ItineraryDayColumn = ({
  day,
  dateLabel,
  activities,
  customActivityIds,
  onRemove,
  onEdit,
  onAddCustom,
}: ItineraryDayColumnProps) => {
  const { setNodeRef, isOver } = useDroppable({
    id: `day-${day}`,
    data: {
      destination: day,
    },
  });

  // Group activities by time of day (if available) or distribute evenly
  const activitiesByTimeSlot = activities.reduce(
    (acc, activity, index) => {
      // Try to infer time slot from activity data or distribute evenly
      let slot = 'afternoon'; // default
      if (index < activities.length / 3) {
        slot = 'morning';
      } else if (index < (activities.length * 2) / 3) {
        slot = 'afternoon';
      } else {
        slot = 'evening';
      }

      if (!acc[slot]) {
        acc[slot] = [];
      }
      acc[slot].push(activity);
      return acc;
    },
    {} as Record<string, Activity[]>
  );

  const activityIds = activities.map((a) => a.id);

  return (
    <div
      ref={setNodeRef}
      className={cn(
        'w-full p-4 rounded-2xl glass-sand border-2 transition-all',
        isOver && 'border-gold/50 bg-gold/5'
      )}
    >
      {/* Day Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-gold/20 flex items-center justify-center text-sm font-semibold text-gold">
            {day}
          </div>
          <h3 className="text-lg font-serif text-fog">{dateLabel}</h3>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onAddCustom(day)}
          className="text-fog/60 hover:text-gold"
          title="Add custom activity"
        >
          <Plus className="w-4 h-4" />
        </Button>
      </div>

      {/* Activities by Time Slot */}
      {activities.length > 0 ? (
        <SortableContext
          items={activityIds}
          strategy={verticalListSortingStrategy}
        >
          <div className="space-y-4">
            {TIME_SLOTS.map((slot) => {
              const slotActivities = activitiesByTimeSlot[slot.id] || [];
              if (slotActivities.length === 0 && activities.length > 0) {
                return null; // Don't show empty slots if there are activities
              }

              return (
                <div key={slot.id} className="space-y-2">
                  <div
                    className={cn(
                      'px-3 py-1.5 rounded-lg text-xs font-semibold text-fog/80 uppercase tracking-wider',
                      slot.color
                    )}
                  >
                    {slot.label}
                  </div>
                  <div className="space-y-2 pl-2">
                    {slotActivities.map((activity) => (
                      <SortableActivityItem
                        key={activity.id}
                        activity={activity}
                        day={day}
                        customActivityIds={customActivityIds}
                        onRemove={onRemove}
                        onEdit={onEdit}
                      />
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </SortableContext>
      ) : (
        <div className="text-center py-12 text-fog/60 border-2 border-dashed border-fog/20 rounded-xl">
          <p className="text-sm mb-2">Drag activities here</p>
          <p className="text-xs">or add custom activities</p>
        </div>
      )}
    </div>
  );
};

