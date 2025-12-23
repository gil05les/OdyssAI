import { useDraggable } from '@dnd-kit/core';
import { Activity } from '@/data/mockAgentData';
import { Clock, DollarSign, Edit2, X, ExternalLink } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

interface ItineraryActivityCardProps {
  activity: Activity;
  source: 'pool' | number; // 'pool' or day number
  isCustom?: boolean;
  onEdit?: (activity: Activity) => void;
  onRemove?: (activityId: string) => void;
  showRemove?: boolean;
  compact?: boolean;
  isSortable?: boolean; // If true, don't use useDraggable (parent handles drag)
}

export const ItineraryActivityCard = ({
  activity,
  source,
  isCustom = false,
  onEdit,
  onRemove,
  showRemove = false,
  compact = false,
  isSortable = false,
}: ItineraryActivityCardProps) => {
  // Always call useDraggable (hooks must be called unconditionally)
  // But only use it if in pool (not in sortable context)
  const draggableResult = useDraggable({
    id: activity.id,
    data: {
      activity,
      source,
    },
    disabled: isSortable || source !== 'pool', // Disable if in sortable context
  });

  const draggable = !isSortable && source === 'pool' ? draggableResult : null;

  const style = draggable?.transform
    ? {
      transform: `translate3d(${draggable.transform.x}px, ${draggable.transform.y}px, 0)`,
    }
    : undefined;

  return (
    <div
      ref={draggable?.setNodeRef}
      style={style}
      {...(draggable?.listeners || {})}
      {...(draggable?.attributes || {})}
      className={cn(
        'relative group',
        draggable?.isDragging && 'opacity-50 z-50',
        !isSortable && !draggable?.isDragging && 'cursor-grab active:cursor-grabbing'
      )}
    >
      <div
        className={cn(
          'rounded-xl glass-sand border-2 transition-all duration-200',
          'hover:border-gold/50 hover:shadow-md',
          draggable?.isDragging && 'border-gold shadow-lg',
          compact ? 'p-2' : 'p-3'
        )}
      >
        <div className={cn('flex gap-3', compact && 'gap-2')}>
          {/* Thumbnail */}
          <div
            className={cn(
              'rounded-lg overflow-hidden flex-shrink-0',
              compact ? 'w-12 h-12' : 'w-16 h-16'
            )}
          >
            <img
              src={activity.image}
              alt={activity.name}
              className="w-full h-full object-cover"
            />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <h4
                  className={cn(
                    'font-medium text-fog truncate',
                    compact ? 'text-sm' : 'text-base'
                  )}
                >
                  {activity.name}
                </h4>
                {!compact && (
                  <p className="text-xs text-fog/70 mt-0.5 line-clamp-2">
                    {activity.description}
                  </p>
                )}
              </div>

              {/* Action buttons */}
              <div className="flex items-center gap-1 flex-shrink-0">
                {isCustom && onEdit && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={(e) => {
                      e.stopPropagation();
                      onEdit(activity);
                    }}
                    title="Edit activity"
                  >
                    <Edit2 className="w-3 h-3" />
                  </Button>
                )}
                {showRemove && onRemove && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity text-red-400 hover:text-red-500"
                    onClick={(e) => {
                      e.stopPropagation();
                      onRemove(activity.id);
                    }}
                    title="Remove activity"
                  >
                    <X className="w-3 h-3" />
                  </Button>
                )}
              </div>
            </div>

            {/* Metadata */}
            <div
              className={cn(
                'flex items-center gap-3 mt-2',
                compact ? 'gap-2 mt-1' : ''
              )}
            >
              <span
                className={cn(
                  'flex items-center gap-1 text-fog/80',
                  compact ? 'text-xs' : 'text-xs'
                )}
              >
                <Clock className="w-3 h-3" />
                {activity.duration}
              </span>
              <span
                className={cn(
                  'flex items-center gap-1 text-fog/80',
                  compact ? 'text-xs' : 'text-xs'
                )}
              >
                <DollarSign className="w-3 h-3" />
                {activity.price === 0 ? 'Included' : `CHF ${activity.price}`}
              </span>
              <span
                className={cn(
                  'px-2 py-0.5 bg-teal/10 text-teal-light rounded-full',
                  compact ? 'text-xs' : 'text-xs'
                )}
              >
                {activity.category}
              </span>
              {/* Yelp link badge */}
              {activity.url && (
                <a
                  href={activity.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className={cn(
                    'flex items-center gap-1 px-2 py-0.5 bg-red-500/20 text-red-400 rounded-full hover:bg-red-500/30 transition-colors',
                    compact ? 'text-xs' : 'text-xs'
                  )}
                >
                  <ExternalLink className="w-3 h-3" />
                  Yelp
                </a>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

