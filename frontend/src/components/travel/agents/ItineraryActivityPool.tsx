import { useState, useMemo } from 'react';
import { useDroppable } from '@dnd-kit/core';
import { Activity } from '@/data/mockAgentData';
import { ItineraryActivityCard } from './ItineraryActivityCard';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Plus, Search, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ScrollArea } from '@/components/ui/scroll-area';

interface ItineraryActivityPoolProps {
  activities: Activity[];
  customActivityIds: Set<string>;
  onRemove: (activityId: string) => void;
  onEdit: (activity: Activity) => void;
  onAddCustom: () => void;
}

export const ItineraryActivityPool = ({
  activities,
  customActivityIds,
  onRemove,
  onEdit,
  onAddCustom,
}: ItineraryActivityPoolProps) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const { setNodeRef, isOver } = useDroppable({
    id: 'pool',
    data: {
      destination: 'pool',
    },
  });

  const categories = useMemo(() => {
    const cats = new Set(activities.map((a) => a.category));
    return Array.from(cats);
  }, [activities]);

  const filteredActivities = useMemo(() => {
    return activities.filter((activity) => {
      const matchesSearch =
        searchQuery === '' ||
        activity.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        activity.description.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesCategory =
        selectedCategory === null || activity.category === selectedCategory;

      return matchesSearch && matchesCategory;
    });
  }, [activities, searchQuery, selectedCategory]);

  const aiActivities = filteredActivities.filter(
    (a) => !customActivityIds.has(a.id)
  );
  const customActivities = filteredActivities.filter((a) =>
    customActivityIds.has(a.id)
  );

  return (
    <div
      ref={setNodeRef}
      className={cn(
        'w-96 flex-shrink-0 flex flex-col border-r border-fog/20 bg-fog/5',
        isOver && 'bg-gold/10 border-gold/50'
      )}
    >
      {/* Header */}
      <div className="p-4 border-b border-fog/20">
        <h3 className="text-lg font-serif text-fog mb-3">Activity Pool</h3>

        {/* Search */}
        <div className="relative mb-3">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-fog/60" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search activities..."
            className="pl-9 bg-white/50 border-fog/20"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-fog/60 hover:text-fog"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Category Filter */}
        {categories.length > 0 && (
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setSelectedCategory(null)}
              className={cn(
                'px-2 py-1 rounded-md text-xs transition-colors',
                selectedCategory === null
                  ? 'bg-gold/20 text-gold border border-gold/40'
                  : 'bg-fog/10 text-fog/80 border border-fog/20 hover:bg-fog/20'
              )}
            >
              All
            </button>
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() =>
                  setSelectedCategory(
                    selectedCategory === cat ? null : cat
                  )
                }
                className={cn(
                  'px-2 py-1 rounded-md text-xs transition-colors',
                  selectedCategory === cat
                    ? 'bg-gold/20 text-gold border border-gold/40'
                    : 'bg-fog/10 text-fog/80 border border-fog/20 hover:bg-fog/20'
                )}
              >
                {cat}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Activities List */}
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-4">
          {/* AI Suggestions */}
          {aiActivities.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-teal-light uppercase tracking-wider mb-2">
                AI Suggestions ({aiActivities.length})
              </h4>
              <div className="space-y-2">
                {aiActivities.map((activity) => (
                  <ItineraryActivityCard
                    key={activity.id}
                    activity={activity}
                    source="pool"
                    isCustom={false}
                    onRemove={onRemove}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Custom Activities */}
          {customActivities.length > 0 && (
            <div className="mt-6">
              <h4 className="text-xs font-semibold text-gold uppercase tracking-wider mb-2">
                Custom Activities ({customActivities.length})
              </h4>
              <div className="space-y-2">
                {customActivities.map((activity) => (
                  <ItineraryActivityCard
                    key={activity.id}
                    activity={activity}
                    source="pool"
                    isCustom={true}
                    onEdit={onEdit}
                    onRemove={onRemove}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Empty State */}
          {filteredActivities.length === 0 && (
            <div className="text-center py-8 text-fog/60">
              <p className="text-sm">
                {searchQuery || selectedCategory
                  ? 'No activities match your filters'
                  : 'All activities are in your plan! Remove activities from days to see them here, or add custom activities.'}
              </p>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Add Custom Button */}
      <div className="p-4 border-t border-fog/20">
        <Button
          onClick={onAddCustom}
          className="w-full bg-gold hover:bg-gold/90 text-midnight"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Custom Activity
        </Button>
      </div>
    </div>
  );
};

