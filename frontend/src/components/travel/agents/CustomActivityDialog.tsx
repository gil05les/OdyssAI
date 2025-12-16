import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Activity } from '@/data/mockAgentData';

interface CustomActivityDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSave: (activity: Activity, targetDay?: number) => void;
  targetDay?: number; // If provided, add directly to this day
  existingActivity?: Activity; // If provided, edit mode
}

const CATEGORIES = [
  'Culture',
  'Food',
  'Adventure',
  'Nature',
  'Wellness',
  'Shopping',
  'Entertainment',
];

const TIME_OF_DAY_OPTIONS = ['morning', 'afternoon', 'evening', 'full day'];

export const CustomActivityDialog = ({
  open,
  onOpenChange,
  onSave,
  targetDay,
  existingActivity,
}: CustomActivityDialogProps) => {
  const [formData, setFormData] = useState({
    name: existingActivity?.name || '',
    description: existingActivity?.description || '',
    duration: existingActivity?.duration || '2 hours',
    price: existingActivity?.price?.toString() || '0',
    category: existingActivity?.category || 'Culture',
    time_of_day: 'afternoon',
    image: existingActivity?.image || '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const activity: Activity = {
      id: existingActivity?.id || `custom-${Date.now()}`,
      name: formData.name,
      description: formData.description,
      duration: formData.duration,
      price: parseFloat(formData.price) || 0,
      image:
        formData.image ||
        'https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=400',
      category: formData.category,
    };

    onSave(activity, targetDay);
    onOpenChange(false);

    // Reset form if not editing
    if (!existingActivity) {
      setFormData({
        name: '',
        description: '',
        duration: '2 hours',
        price: '0',
        category: 'Culture',
        time_of_day: 'afternoon',
        image: '',
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>
            {existingActivity ? 'Edit Activity' : 'Add Custom Activity'}
          </DialogTitle>
          <DialogDescription>
            {targetDay
              ? `Add a custom activity to Day ${targetDay}`
              : 'Create a custom activity to add to your itinerary'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Activity Name *</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) =>
                setFormData({ ...formData, name: e.target.value })
              }
              placeholder="e.g., Sunset Wine Tasting"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) =>
                setFormData({ ...formData, description: e.target.value })
              }
              placeholder="Brief description of the activity"
              rows={3}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="duration">Duration</Label>
              <Input
                id="duration"
                value={formData.duration}
                onChange={(e) =>
                  setFormData({ ...formData, duration: e.target.value })
                }
                placeholder="e.g., 2 hours"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="price">Price (CHF)</Label>
              <Input
                id="price"
                type="number"
                min="0"
                step="0.01"
                value={formData.price}
                onChange={(e) =>
                  setFormData({ ...formData, price: e.target.value })
                }
                placeholder="0"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="category">Category</Label>
              <Select
                value={formData.category}
                onValueChange={(value) =>
                  setFormData({ ...formData, category: value })
                }
              >
                <SelectTrigger id="category">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CATEGORIES.map((cat) => (
                    <SelectItem key={cat} value={cat}>
                      {cat}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="time_of_day">Time of Day</Label>
              <Select
                value={formData.time_of_day}
                onValueChange={(value) =>
                  setFormData({ ...formData, time_of_day: value })
                }
              >
                <SelectTrigger id="time_of_day">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TIME_OF_DAY_OPTIONS.map((time) => (
                    <SelectItem key={time} value={time}>
                      {time.charAt(0).toUpperCase() + time.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="image">Image URL (optional)</Label>
            <Input
              id="image"
              type="url"
              value={formData.image}
              onChange={(e) =>
                setFormData({ ...formData, image: e.target.value })
              }
              placeholder="https://..."
            />
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="ghost"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" className="bg-gold hover:bg-gold/90 text-midnight">
              {existingActivity ? 'Save Changes' : 'Add Activity'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

