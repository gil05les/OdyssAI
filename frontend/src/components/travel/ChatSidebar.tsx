import { useState } from "react";
import { Send, Sparkles, User, Bot, CheckCircle2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { chatWithAssistant, ChatMessage } from "@/services/api";
import { useTravelForm } from "@/contexts/TravelFormContext";

interface Message {
  id: string;
  role: "assistant" | "user";
  content: string;
  updatedFields?: string[];
}

const INITIAL_MESSAGES: Message[] = [
  {
    id: "1",
    role: "assistant",
    content: "Welcome to Voyager! ✨ I'm your personal travel concierge. Tell me about your dream vacation, and I'll help craft the perfect itinerary.",
  },
  {
    id: "2",
    role: "assistant",
    content: "You can fill out the form on the left, or simply tell me what you're looking for. I can help with destination recommendations, activity planning, and more.",
  },
];

const ChatSidebar = () => {
  const [messages, setMessages] = useState<Message[]>(INITIAL_MESSAGES);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  
  const { formState, updateFormState } = useTravelForm();

  const handleSend = async () => {
    if (!input.trim()) return;
    
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
    };
    
    setMessages((prev) => [...prev, userMessage]);
    const userInput = input;
    setInput("");
    setIsTyping(true);
    
    try {
      // Convert messages to ChatMessage format for API
      const conversationHistory: ChatMessage[] = messages
        .filter(msg => msg.id !== "1" && msg.id !== "2") // Exclude initial welcome messages
        .map(msg => ({
          role: msg.role,
          content: msg.content,
        }));
      
      // Convert form state to API format
      const currentFormState = {
        origin: formState.origin,
        destinations: formState.destinations,
        surprise_me: formState.surpriseMe,
        date_ranges: formState.dateRanges
          .filter(range => range.from && range.to)
          .map(range => ({
            from: range.from!.toISOString().split('T')[0],
            to: range.to!.toISOString().split('T')[0],
          })),
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
      
      // Call the chat API
      const response = await chatWithAssistant(userInput, conversationHistory, currentFormState);
      
      // Update form fields if any were returned
      if (response.form_updates && Object.keys(response.form_updates).length > 0) {
        const updates: any = {};
        
        // Map backend field names to frontend state
        if (response.form_updates.origin !== undefined) {
          updates.origin = response.form_updates.origin;
        }
        if (response.form_updates.destinations !== undefined) {
          updates.destinations = response.form_updates.destinations;
        }
        if (response.form_updates.surprise_me !== undefined) {
          updates.surpriseMe = response.form_updates.surprise_me;
        }
        if (response.form_updates.date_ranges !== undefined) {
          // Convert date strings back to DateRange objects
          updates.dateRanges = response.form_updates.date_ranges.map((dr: any) => ({
            from: dr.from ? new Date(dr.from) : undefined,
            to: dr.to ? new Date(dr.to) : undefined,
          }));
        }
        if (response.form_updates.duration !== undefined) {
          updates.duration = response.form_updates.duration;
        }
        if (response.form_updates.traveler_type !== undefined) {
          updates.travelerType = response.form_updates.traveler_type;
        }
        if (response.form_updates.group_size !== undefined) {
          updates.groupSize = response.form_updates.group_size;
        }
        if (response.form_updates.budget !== undefined) {
          updates.budget = response.form_updates.budget;
        }
        if (response.form_updates.environments !== undefined) {
          updates.environments = response.form_updates.environments;
        }
        if (response.form_updates.climate !== undefined) {
          updates.climate = response.form_updates.climate;
        }
        if (response.form_updates.trip_vibe !== undefined) {
          updates.tripVibe = response.form_updates.trip_vibe;
        }
        if (response.form_updates.distance_preference !== undefined) {
          updates.distancePreference = response.form_updates.distance_preference;
        }
        if (response.form_updates.trip_purpose !== undefined) {
          updates.tripPurpose = response.form_updates.trip_purpose;
        }
        if (response.form_updates.experiences !== undefined) {
          updates.experiences = response.form_updates.experiences;
        }
        
        updateFormState(updates);
      }
      
      // Add assistant response to messages
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.response,
        updatedFields: response.updated_fields,
      };
      
      setMessages((prev) => [...prev, aiMessage]);
      
      // If clarification is needed, add the question as a follow-up message
      if (response.needs_clarification && response.clarification_question) {
        setTimeout(() => {
          const clarificationMessage: Message = {
            id: (Date.now() + 2).toString(),
            role: "assistant",
            content: response.clarification_question,
          };
          setMessages((prev) => [...prev, clarificationMessage]);
        }, 500);
      }
      
    } catch (error) {
      console.error("Error chatting with assistant:", error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "I apologize, but I encountered an error. Could you please try rephrasing your message?",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex flex-col h-full w-full glass overflow-hidden">
      {/* Header */}
      <div className="p-5 border-b border-fog/10">
        <div className="flex items-center gap-4">
          <div className="relative">
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-teal to-teal-light flex items-center justify-center animate-glow">
              <Bot className="w-6 h-6 text-fog" />
            </div>
            <div className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-emerald-500 rounded-full border-2 border-midnight" />
          </div>
          <div>
            <h3 className="font-display text-xl text-fog">Travel Concierge</h3>
            <p className="text-xs text-muted-foreground">Powered by AI • Always here to help</p>
          </div>
        </div>
      </div>
      
      {/* Messages */}
      <ScrollArea className="flex-1 p-5">
        <div className="space-y-5">
          {messages.map((message, index) => (
            <div
              key={message.id}
              className={cn(
                "flex gap-3 animate-fade-in",
                message.role === "user" ? "flex-row-reverse" : ""
              )}
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className={cn(
                "w-9 h-9 rounded-full flex items-center justify-center shrink-0",
                message.role === "assistant" 
                  ? "bg-gradient-to-br from-teal to-teal-light" 
                  : "bg-gradient-to-br from-gold to-gold-light"
              )}>
                {message.role === "assistant" ? (
                  <Bot className="w-4 h-4 text-fog" />
                ) : (
                  <User className="w-4 h-4 text-midnight" />
                )}
              </div>
              
              <div className={cn(
                "max-w-[80%] p-4 rounded-2xl text-sm leading-relaxed",
                message.role === "assistant" 
                  ? "bg-sand/90 text-midnight rounded-tl-sm" 
                  : "bg-gradient-to-br from-gold to-gold-light text-midnight rounded-tr-sm"
              )}>
                <div>{message.content}</div>
                {message.updatedFields && message.updatedFields.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-midnight/20">
                    <div className="flex items-center gap-2 text-xs text-midnight/70 mb-2">
                      <CheckCircle2 className="w-3.5 h-3.5 text-teal" />
                      <span className="font-medium">Updated fields:</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {message.updatedFields.map((field, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 bg-teal/20 text-teal rounded-full text-xs"
                        >
                          {field.replace(/_/g, ' ')}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
          
          {isTyping && (
            <div className="flex gap-3 animate-fade-in">
              <div className="w-9 h-9 rounded-full bg-gradient-to-br from-teal to-teal-light flex items-center justify-center">
                <Bot className="w-4 h-4 text-fog" />
              </div>
            <div className="bg-sand/90 p-4 rounded-2xl rounded-tl-sm">
                <div className="flex gap-1.5">
                  <div className="w-2 h-2 bg-teal rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                  <div className="w-2 h-2 bg-teal rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                  <div className="w-2 h-2 bg-teal rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>
      
      {/* Input */}
      <div className="p-5 border-t border-fog/10">
        <div className="flex gap-3">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Ask me anything..."
            className="flex-1 h-12 bg-midnight-light/50 border-fog/10 text-fog placeholder:text-muted-foreground focus:border-teal/50 rounded-xl"
          />
          <Button 
            onClick={handleSend}
            size="icon"
            className="h-12 w-12 rounded-xl bg-gradient-to-br from-teal to-teal-light hover:from-teal-light hover:to-teal text-fog shrink-0 hover-glow transition-all duration-300"
          >
            <Send className="w-5 h-5" />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ChatSidebar;
