import { useState } from "react";
import { MessageCircle, X } from "lucide-react";
import FloatingElements from "@/components/travel/FloatingElements";
import TravelPlannerForm from "@/components/travel/TravelPlannerForm";
import ChatSidebar from "@/components/travel/ChatSidebar";
import { Header } from "@/components/Header";
import { Button } from "@/components/ui/button";
import { TravelFormProvider } from "@/contexts/TravelFormContext";
import { cn } from "@/lib/utils";

const Index = () => {
  const [isChatOpen, setIsChatOpen] = useState(true);

  return (
    <TravelFormProvider>
      <div className="min-h-screen relative overflow-hidden">
        <Header />
        {/* Floating decorative elements */}
        <FloatingElements />
        
        {/* Main layout */}
        <div className="relative z-10 flex min-h-screen pt-16">
        {/* Main content area */}
        <main className={cn(
          "flex-1 transition-all duration-500 ease-out",
          isChatOpen ? "lg:mr-[400px]" : ""
        )}>
          <div className="max-w-4xl mx-auto px-6 py-12 lg:py-20">
            <TravelPlannerForm />
          </div>
        </main>
        
        {/* Chat sidebar - Desktop */}
        <aside className={cn(
          "fixed right-0 top-16 bottom-0 w-[400px] hidden lg:block transition-transform duration-500 ease-out",
          isChatOpen ? "translate-x-0" : "translate-x-full"
        )}>
          <ChatSidebar />
        </aside>
        
        {/* Chat toggle button - Desktop */}
        <Button
          onClick={() => setIsChatOpen(!isChatOpen)}
          size="icon"
          className={cn(
            "fixed top-20 z-50 hidden lg:flex w-11 h-11 rounded-full transition-all duration-500 border border-gold/30",
            "bg-midnight-light/80 backdrop-blur-sm hover:bg-gold/20 text-gold hover:text-gold-light",
            isChatOpen ? "right-[415px]" : "right-6",
            "hover:border-gold/50"
          )}
        >
          {isChatOpen ? <X className="w-5 h-5" /> : <MessageCircle className="w-5 h-5" />}
        </Button>
        
        {/* Mobile chat drawer */}
        <div className={cn(
          "fixed inset-0 z-50 lg:hidden transition-all duration-300",
          isChatOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
        )}>
          {/* Backdrop */}
          <div 
            className="absolute inset-0 bg-midnight/80 backdrop-blur-sm"
            onClick={() => setIsChatOpen(false)}
          />
          
          {/* Chat panel */}
          <div className={cn(
            "absolute right-0 top-16 bottom-0 w-full max-w-md transition-transform duration-300",
            isChatOpen ? "translate-x-0" : "translate-x-full"
          )}>
            <Button
              onClick={() => setIsChatOpen(false)}
              size="icon"
              variant="ghost"
              className="absolute top-4 right-4 z-10 text-fog hover:text-gold"
            >
              <X className="w-5 h-5" />
            </Button>
            <ChatSidebar />
          </div>
        </div>
        
        {/* Mobile chat FAB */}
        <Button
          onClick={() => setIsChatOpen(true)}
          size="icon"
          className={cn(
            "fixed bottom-6 right-6 z-40 lg:hidden w-14 h-14 rounded-full border border-gold/30",
            "bg-midnight-light/90 backdrop-blur-sm hover:bg-gold/20 text-gold hover:text-gold-light",
            "animate-float glow-gold",
            isChatOpen && "hidden"
          )}
        >
          <MessageCircle className="w-6 h-6" />
        </Button>
      </div>
      </div>
    </TravelFormProvider>
  );
};

export default Index;
