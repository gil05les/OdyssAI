import jsPDF from 'jspdf';
import { Destination, Flight, Hotel, Activity, TransportOption } from '@/data/mockAgentData';
import { TripRequest } from '@/services/api';

interface BookingData {
  formData: {
    fullName: string;
    email: string;
    phone: string;
    street: string;
    city: string;
    zip: string;
    country: string;
  };
  tripState: {
    destination: Destination | null;
    flight: Flight | null;
    hotel: Hotel | null;
    activities: Activity[];
    transport: Record<string, TransportOption | null>;
  };
  bookingReference: string;
}

// Generate a unique booking reference
export const generateBookingReference = (): string => {
  const date = new Date();
  const dateStr = date.toISOString().slice(0, 10).replace(/-/g, '');
  const random = Math.floor(Math.random() * 10000).toString().padStart(4, '0');
  return `ODY-${dateStr}-${random}`;
};

// Calculate total price
const calculateTotal = (bookingData: BookingData): number => {
  let total = 0;
  if (bookingData.tripState.flight) total += bookingData.tripState.flight.price;
  if (bookingData.tripState.hotel) {
    // Calculate nights from trip request or default to 3
    const nights = 3; // Could be calculated from tripRequest.date_ranges
    total += bookingData.tripState.hotel.pricePerNight * nights;
  }
  total += bookingData.tripState.activities.reduce((sum, a) => sum + a.price, 0);
  Object.values(bookingData.tripState.transport).forEach(opt => {
    if (opt) total += opt.price;
  });
  return total;
};

export const generateBookingPDF = (bookingData: BookingData, tripRequest: TripRequest): void => {
  const doc = new jsPDF();
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const margin = 20;
  const contentWidth = pageWidth - (margin * 2);
  let yPosition = margin;

  // Colors matching website design exactly (RGB values for jsPDF)
  // Midnight: hsl(210 61% 11%) ≈ RGB(15, 23, 42)
  const midnightColor = [15, 23, 42];
  // Gold: hsl(34 50% 66%) ≈ RGB(212, 175, 55)
  const goldColor = [212, 175, 55];
  // Teal: hsl(186 59% 30%) ≈ RGB(20, 184, 166)
  const tealColor = [20, 184, 166];
  // Teal Light: hsl(186 50% 40%) = RGB(51, 102, 102) - for labels
  const tealLightColor = [51, 102, 102];
  // Fog (light text): hsl(60 14% 96%) ≈ RGB(245, 244, 240)
  const fogColor = [245, 244, 240];
  // Fog with 80% opacity: for secondary text
  const fog80Color = [196, 195, 192];
  // Fog with 70% opacity: for tertiary text
  const fog70Color = [171, 170, 168];
  // Fog with 60% opacity: for subtle text
  const fog60Color = [147, 146, 144];
  // Fog with 10% opacity border: RGB approximation
  const fogBorderColor = [40, 40, 40];
  // Sand background: hsl(210 50% 15% / 0.85) ≈ RGB(30, 40, 50) with transparency effect
  const sandBgColor = [30, 40, 50];
  // Sand border: hsl(38 32% 85% / 0.2) ≈ RGB(217, 204, 180) with low opacity
  const sandBorderColor = [50, 45, 40];

  // Transport options (used in multiple sections)
  const transportOptions = Object.values(bookingData.tripState.transport).filter(Boolean) as TransportOption[];

  // Helper function to set page background
  const setPageBackground = () => {
    doc.setFillColor(...midnightColor);
    doc.rect(0, 0, pageWidth, pageHeight, 'F');
  };

  // Set background for first page
  setPageBackground();

  // Helper function to add a new page if needed
  const checkPageBreak = (requiredSpace: number) => {
    if (yPosition + requiredSpace > pageHeight - margin) {
      doc.addPage();
      setPageBackground();
      yPosition = margin;
      return true;
    }
    return false;
  };

  // Helper function to draw a section background (glass-sand effect matching rounded-2xl)
  const drawSectionBackground = (y: number, height: number) => {
    try {
      // Try roundedRect first (jsPDF 2.x supports it)
      // rounded-2xl = 16px border radius, scaled for PDF (16/72 ≈ 0.22 inches ≈ 5.6mm)
      const borderRadius = 5.6;
      doc.setFillColor(...sandBgColor);
      doc.setGState(doc.GState({ opacity: 0.85 }));
      doc.roundedRect(margin, y, contentWidth, height, borderRadius, borderRadius, 'F');
      // Add subtle border matching sand border color
      doc.setDrawColor(...sandBorderColor);
      doc.setLineWidth(0.3);
      doc.setGState(doc.GState({ opacity: 0.2 }));
      doc.roundedRect(margin, y, contentWidth, height, borderRadius, borderRadius, 'D');
      doc.setGState(doc.GState({ opacity: 1 }));
    } catch (e) {
      // Fallback to regular rect if roundedRect is not available
      doc.setFillColor(...sandBgColor);
      doc.setGState(doc.GState({ opacity: 0.85 }));
      doc.rect(margin, y, contentWidth, height, 'F');
      doc.setDrawColor(...sandBorderColor);
      doc.setLineWidth(0.3);
      doc.setGState(doc.GState({ opacity: 0.2 }));
      doc.rect(margin, y, contentWidth, height, 'D');
      doc.setGState(doc.GState({ opacity: 1 }));
    }
  };

  // Header with gradient-like effect matching website
  doc.setFillColor(...midnightColor);
  doc.rect(0, 0, pageWidth, 70, 'F');
  
  // Gold accent line at top
  doc.setFillColor(...goldColor);
  doc.rect(0, 0, pageWidth, 4, 'F');
  
  // Main title - serif-like styling
  doc.setTextColor(...fogColor);
  doc.setFontSize(32);
  doc.setFont('helvetica', 'bold');
  doc.text('OdyssAI', margin, 40);
  
  // Subtitle
  doc.setFontSize(11);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(...goldColor);
  doc.text('Booking Confirmation', margin, 52);

  // Booking Reference box (matching website style)
  const refBoxWidth = 80;
  const refBoxX = pageWidth - margin - refBoxWidth;
  doc.setFillColor(...sandBgColor);
  doc.setGState(doc.GState({ opacity: 0.3 }));
  doc.roundedRect(refBoxX, 25, refBoxWidth, 20, 3, 3, 'F');
  doc.setGState(doc.GState({ opacity: 1 }));
  doc.setDrawColor(...goldColor);
  doc.setLineWidth(0.5);
  doc.setGState(doc.GState({ opacity: 0.3 }));
  doc.roundedRect(refBoxX, 25, refBoxWidth, 20, 3, 3, 'D');
  doc.setGState(doc.GState({ opacity: 1 }));
  
  doc.setFontSize(7);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(...tealLightColor);
  doc.text('BOOKING REFERENCE', refBoxX + 3, 32, { align: 'left' });
  doc.setFontSize(12);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(...goldColor);
  doc.text(bookingData.bookingReference, refBoxX + refBoxWidth / 2, 42, { align: 'center' });
  
  const bookingDate = new Date().toLocaleDateString('en-US', { 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric' 
  });
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(...fogColor);
  doc.setFontSize(9);
  doc.text(`Date: ${bookingDate}`, pageWidth - margin, 58, { align: 'right' });

  yPosition = 80;

  // Customer Information Section
  checkPageBreak(50);
  const customerInfoStartY = yPosition;
  drawSectionBackground(yPosition - 5, 50);
  
  // Section header with serif-like styling (bold helvetica simulates Playfair Display)
  doc.setFontSize(18);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(...fogColor);
  doc.text('Customer Information', margin + 5, yPosition + 5);
  
  yPosition += 12;
  
  doc.setFontSize(7);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(...tealLightColor);
  // Add letter spacing effect (uppercase with wider tracking)
  doc.text('FULL NAME', margin + 5, yPosition);
  yPosition += 5;
  doc.setFontSize(10);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(...fogColor);
  doc.text(bookingData.formData.fullName, margin + 5, yPosition);
  yPosition += 8;
  
  doc.setFontSize(7);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(...tealLightColor);
  doc.text('EMAIL', margin + 5, yPosition);
  yPosition += 5;
  doc.setFontSize(10);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(...fogColor);
  doc.text(bookingData.formData.email, margin + 5, yPosition);
  yPosition += 8;
  
  if (bookingData.formData.phone) {
    doc.setFontSize(7);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(...tealLightColor);
    doc.text('PHONE', margin + 5, yPosition);
    yPosition += 5;
    doc.setFontSize(10);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...fogColor);
    doc.text(bookingData.formData.phone, margin + 5, yPosition);
    yPosition += 8;
  }
  
  if (bookingData.formData.street || bookingData.formData.city) {
    const addressParts = [
      bookingData.formData.street,
      bookingData.formData.city,
      bookingData.formData.zip,
      bookingData.formData.country
    ].filter(Boolean);
    
    if (addressParts.length > 0) {
      doc.setFontSize(7);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(...tealLightColor);
      doc.text('BILLING ADDRESS', margin + 5, yPosition);
      yPosition += 5;
      doc.setFontSize(10);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(...fogColor);
      doc.text(addressParts.join(', '), margin + 5, yPosition);
      yPosition += 8;
    }
  }

  yPosition += 5;

  // Trip Summary Section
  checkPageBreak(50);
  drawSectionBackground(yPosition - 5, 45);
  
  doc.setFontSize(18);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(...fogColor);
  doc.text('Trip Summary', margin + 5, yPosition + 5);
  
  yPosition += 12;

  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');

  if (bookingData.tripState.destination) {
    doc.setFontSize(7);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(...tealLightColor);
    doc.text('DESTINATION', margin + 5, yPosition);
    yPosition += 5;
    doc.setFontSize(10);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...fogColor);
    doc.text(`${bookingData.tripState.destination.name}, ${bookingData.tripState.destination.country}`, margin + 5, yPosition);
    yPosition += 8;
  }

  if (tripRequest.date_ranges && tripRequest.date_ranges.length > 0) {
    const dateRange = tripRequest.date_ranges[0];
    doc.setFontSize(7);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(...tealLightColor);
    doc.text('TRAVEL DATES', margin + 5, yPosition);
    yPosition += 5;
    doc.setFontSize(10);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...fogColor);
    doc.text(`${dateRange.from} to ${dateRange.to}`, margin + 5, yPosition);
    yPosition += 8;
  }

  doc.setFontSize(7);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(...tealLightColor);
  doc.text('TRAVELERS', margin + 5, yPosition);
  yPosition += 5;
  doc.setFontSize(10);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(...fogColor);
  doc.text(`${tripRequest.group_size} ${tripRequest.traveler_type}`, margin + 5, yPosition);
  yPosition += 10;

  // Flight Details
  if (bookingData.tripState.flight) {
    checkPageBreak(80);
    const flightStartY = yPosition;
    drawSectionBackground(yPosition - 5, 75);
    
    doc.setFontSize(18);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...fogColor);
    doc.text('Flight Details', margin + 5, yPosition + 5);
    
    yPosition += 12;

    const flight = bookingData.tripState.flight;
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');

    doc.setFontSize(7);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(...tealLightColor);
    doc.text('AIRLINE', margin + 5, yPosition);
    yPosition += 5;
    doc.setFontSize(10);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...fogColor);
    doc.text(`${flight.airline} • ${flight.class}`, margin + 5, yPosition);
    yPosition += 8;
    
    if (flight.flightNumber) {
      doc.setFontSize(7);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(...tealLightColor);
      doc.text('FLIGHT NUMBER', margin + 5, yPosition);
      yPosition += 5;
      doc.setFontSize(10);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(...fogColor);
      doc.text(flight.flightNumber, margin + 5, yPosition);
      yPosition += 8;
    }

    doc.setFontSize(7);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(...tealLightColor);
    doc.text('DEPARTURE', margin + 5, yPosition);
    yPosition += 5;
    doc.setFontSize(10);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...fogColor);
    doc.text(`${flight.departureTime} from ${flight.departureAirport}`, margin + 5, yPosition);
    yPosition += 8;
    
    doc.setFontSize(7);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(...tealLightColor);
    doc.text('ARRIVAL', margin + 5, yPosition);
    yPosition += 5;
    doc.setFontSize(10);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...fogColor);
    doc.text(`${flight.arrivalTime} at ${flight.arrivalAirport}`, margin + 5, yPosition);
    yPosition += 8;
    
    doc.setFontSize(7);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(...tealLightColor);
    doc.text('DURATION', margin + 5, yPosition);
    yPosition += 5;
    doc.setFontSize(10);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...fogColor);
    doc.text(flight.duration, margin + 5, yPosition);
    yPosition += 8;
    
    if (flight.stops > 0) {
      doc.setFontSize(7);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(...tealLightColor);
      doc.text('STOPS', margin + 5, yPosition);
      yPosition += 5;
      doc.setFontSize(10);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(...fogColor);
      doc.text(`${flight.stops}`, margin + 5, yPosition);
      yPosition += 8;
    }

    if (flight.returnFlightNumber) {
      yPosition += 3;
      doc.setDrawColor(...fogBorderColor);
      doc.setLineWidth(0.2);
      doc.setGState(doc.GState({ opacity: 0.1 }));
      doc.line(margin + 5, yPosition, pageWidth - margin - 5, yPosition);
      doc.setGState(doc.GState({ opacity: 1 }));
      yPosition += 8;
      doc.setFontSize(7);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(...tealLightColor);
      doc.text('RETURN FLIGHT', margin + 5, yPosition);
      yPosition += 5;
      doc.setFontSize(10);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(...fogColor);
      doc.text(`${flight.returnFlightNumber}`, margin + 5, yPosition);
      yPosition += 5;
      doc.setFontSize(9);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(...fog80Color);
      doc.text(`${flight.returnDepartureTime} → ${flight.returnArrivalTime}`, margin + 5, yPosition);
      yPosition += 8;
    }

    doc.setDrawColor(...fogBorderColor);
    doc.setLineWidth(0.2);
    doc.setGState(doc.GState({ opacity: 0.1 }));
    doc.line(margin + 5, yPosition, pageWidth - margin - 5, yPosition);
    doc.setGState(doc.GState({ opacity: 1 }));
    yPosition += 8;
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(10);
    doc.setTextColor(...goldColor);
    doc.text(`CHF ${flight.price.toFixed(2)}`, margin + 5, yPosition);
    yPosition += 10;
  }

  // Hotel Details
  if (bookingData.tripState.hotel) {
    checkPageBreak(70);
    drawSectionBackground(yPosition - 5, 65);
    
    doc.setFontSize(18);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...fogColor);
    doc.text('Accommodation', margin + 5, yPosition + 5);
    
    yPosition += 12;

    const hotel = bookingData.tripState.hotel;
    const nights = 3; // Could be calculated from dates
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');

    doc.setFontSize(7);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(...tealLightColor);
    doc.text('HOTEL', margin + 5, yPosition);
    yPosition += 5;
    doc.setFontSize(10);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...fogColor);
    doc.text(hotel.name, margin + 5, yPosition);
    yPosition += 8;
    
    doc.setFontSize(7);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(...tealLightColor);
    doc.text('LOCATION', margin + 5, yPosition);
    yPosition += 5;
    doc.setFontSize(10);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...fogColor);
    doc.text(hotel.location, margin + 5, yPosition);
    yPosition += 8;
    
    doc.setFontSize(7);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(...tealLightColor);
    doc.text('RATING', margin + 5, yPosition);
    yPosition += 5;
    doc.setFontSize(10);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...fogColor);
    doc.text(`${hotel.stars} stars`, margin + 5, yPosition);
    yPosition += 8;
    
    doc.setFontSize(7);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(...tealLightColor);
    doc.text('NIGHTS', margin + 5, yPosition);
    yPosition += 5;
    doc.setFontSize(10);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...fogColor);
    doc.text(`${nights} nights`, margin + 5, yPosition);
    yPosition += 8;
    
    if (hotel.amenities && hotel.amenities.length > 0) {
      doc.setFontSize(7);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(...tealLightColor);
      doc.text('AMENITIES', margin + 5, yPosition);
      yPosition += 5;
      doc.setFontSize(9);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(...fogColor);
      doc.text(hotel.amenities.slice(0, 5).join(', '), margin + 5, yPosition);
      yPosition += 8;
    }

    doc.setDrawColor(...fogBorderColor);
    doc.setLineWidth(0.2);
    doc.setGState(doc.GState({ opacity: 0.1 }));
    doc.line(margin + 5, yPosition, pageWidth - margin - 5, yPosition);
    doc.setGState(doc.GState({ opacity: 1 }));
    yPosition += 8;
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(10);
    doc.setTextColor(...goldColor);
    doc.text(`CHF ${(hotel.pricePerNight * nights).toFixed(2)}`, margin + 5, yPosition);
    yPosition += 10;
  }

  // Activities
  if (bookingData.tripState.activities.length > 0) {
    const activitiesHeight = 50 + (bookingData.tripState.activities.length * 15);
    checkPageBreak(activitiesHeight);
    drawSectionBackground(yPosition - 5, activitiesHeight - 10);
    
    doc.setFontSize(18);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...fogColor);
    doc.text('Activities & Experiences', margin + 5, yPosition + 5);
    
    yPosition += 12;

    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');

    bookingData.tripState.activities.forEach((activity, index) => {
      checkPageBreak(15);
      doc.setFontSize(10);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(...fogColor);
      doc.text(`${index + 1}. ${activity.name}`, margin + 5, yPosition);
      yPosition += 5;
      doc.setFontSize(9);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(...fog70Color);
      doc.text(`${activity.category} • ${activity.duration}`, margin + 5, yPosition);
      yPosition += 4;
      doc.setFontSize(9);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(...goldColor);
      doc.text(`CHF ${activity.price.toFixed(2)}`, margin + 5, yPosition);
      yPosition += 6;
      
      if (index < bookingData.tripState.activities.length - 1) {
        doc.setDrawColor(...fogBorderColor);
        doc.setLineWidth(0.2);
        doc.setGState(doc.GState({ opacity: 0.1 }));
        doc.line(margin + 5, yPosition, pageWidth - margin - 5, yPosition);
        doc.setGState(doc.GState({ opacity: 1 }));
        yPosition += 3;
      }
    });

    doc.setDrawColor(...fogBorderColor);
    doc.setLineWidth(0.2);
    doc.setGState(doc.GState({ opacity: 0.1 }));
    doc.line(margin + 5, yPosition, pageWidth - margin - 5, yPosition);
    doc.setGState(doc.GState({ opacity: 1 }));
    yPosition += 8;
    const activitiesTotal = bookingData.tripState.activities.reduce((sum, a) => sum + a.price, 0);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(10);
    doc.setTextColor(...goldColor);
    doc.text(`Total: CHF ${activitiesTotal.toFixed(2)}`, margin + 5, yPosition);
    yPosition += 10;
  }

  // Transport
  if (transportOptions.length > 0) {
    const transportHeight = 50 + (transportOptions.length * 15);
    checkPageBreak(transportHeight);
    drawSectionBackground(yPosition - 5, transportHeight - 10);
    
    doc.setFontSize(18);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...fogColor);
    doc.text('Transport', margin + 5, yPosition + 5);
    
    yPosition += 12;

    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');

    transportOptions.forEach((transport, index) => {
      checkPageBreak(15);
      doc.setFontSize(10);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(...fogColor);
      doc.text(`${index + 1}. ${transport.name} (${transport.type})`, margin + 5, yPosition);
      yPosition += 5;
      doc.setFontSize(9);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(...fog70Color);
      doc.text(`${transport.type} • ${transport.duration}`, margin + 5, yPosition);
      yPosition += 4;
      doc.setFontSize(9);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(...goldColor);
      doc.text(`CHF ${transport.price.toFixed(2)}`, margin + 5, yPosition);
      yPosition += 6;
      
      if (index < transportOptions.length - 1) {
        doc.setDrawColor(...fogBorderColor);
        doc.setLineWidth(0.2);
        doc.setGState(doc.GState({ opacity: 0.1 }));
        doc.line(margin + 5, yPosition, pageWidth - margin - 5, yPosition);
        doc.setGState(doc.GState({ opacity: 1 }));
        yPosition += 3;
      }
    });

    doc.setDrawColor(...fogBorderColor);
    doc.setLineWidth(0.2);
    doc.setGState(doc.GState({ opacity: 0.1 }));
    doc.line(margin + 5, yPosition, pageWidth - margin - 5, yPosition);
    doc.setGState(doc.GState({ opacity: 1 }));
    yPosition += 8;
    const transportTotal = transportOptions.reduce((sum, opt) => sum + opt.price, 0);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(10);
    doc.setTextColor(...goldColor);
    doc.text(`Total: CHF ${transportTotal.toFixed(2)}`, margin + 5, yPosition);
    yPosition += 10;
  }

  // Pricing Breakdown
  const pricingItems = [];
  let subtotal = 0;
  
  if (bookingData.tripState.flight) {
    pricingItems.push({ label: 'Flight', amount: bookingData.tripState.flight.price });
    subtotal += bookingData.tripState.flight.price;
  }
  if (bookingData.tripState.hotel) {
    const nights = 3;
    const hotelTotal = bookingData.tripState.hotel.pricePerNight * nights;
    pricingItems.push({ label: `Accommodation (${nights} nights)`, amount: hotelTotal });
    subtotal += hotelTotal;
  }
  if (bookingData.tripState.activities.length > 0) {
    const activitiesTotal = bookingData.tripState.activities.reduce((sum, a) => sum + a.price, 0);
    pricingItems.push({ label: 'Activities', amount: activitiesTotal });
    subtotal += activitiesTotal;
  }
  if (transportOptions.length > 0) {
    const transportTotal = transportOptions.reduce((sum, opt) => sum + opt.price, 0);
    pricingItems.push({ label: 'Transport', amount: transportTotal });
    subtotal += transportTotal;
  }

  checkPageBreak(50 + (pricingItems.length * 8));
  drawSectionBackground(yPosition - 5, 45 + (pricingItems.length * 8));
  
  doc.setFontSize(18);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(...fogColor);
  doc.text('Pricing Summary', margin + 5, yPosition + 5);
  
  yPosition += 12;

  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(...fog80Color);

  pricingItems.forEach((item) => {
    doc.text(item.label, margin + 5, yPosition);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...fogColor);
    doc.text(`CHF ${item.amount.toFixed(2)}`, pageWidth - margin - 5, yPosition, { align: 'right' });
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(...fog80Color);
    yPosition += 8;
  });

  yPosition += 3;
  doc.setDrawColor(...fogBorderColor);
  doc.setLineWidth(0.3);
  doc.setGState(doc.GState({ opacity: 0.1 }));
  doc.line(margin + 5, yPosition, pageWidth - margin - 5, yPosition);
  doc.setGState(doc.GState({ opacity: 1 }));
  yPosition += 8;

  doc.setFontSize(16);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(...fogColor);
  doc.text('Total', margin + 5, yPosition);
  doc.setFontSize(24);
  doc.setTextColor(...goldColor);
  doc.text(`CHF ${subtotal.toFixed(2)}`, pageWidth - margin - 5, yPosition, { align: 'right' });
  yPosition += 6;
  doc.setFontSize(8);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(...fog60Color);
  doc.text('All prices in USD', margin + 5, yPosition);
  yPosition += 10;

  // Footer
  checkPageBreak(40);
  doc.setDrawColor(...goldColor);
  doc.setLineWidth(0.5);
  doc.line(margin, yPosition, pageWidth - margin, yPosition);
  yPosition += 12;

  doc.setFontSize(9);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(...fogColor);
  doc.text('Thank you for choosing OdyssAI for your travel planning.', margin, yPosition, { align: 'center' });
  yPosition += 6;
  doc.setFontSize(8);
  doc.setTextColor(...fog60Color);
  doc.text('For any questions or changes to your booking, please contact us at support@odyssai.com', margin, yPosition, { align: 'center' });
  yPosition += 6;
  doc.text('This is a confirmation document. Please keep it for your records.', margin, yPosition, { align: 'center' });
  
  // Add footer accent
  doc.setFillColor(...goldColor);
  doc.rect(0, pageHeight - 4, pageWidth, 4, 'F');

  // Save the PDF
  const fileName = `booking-confirmation-${bookingData.bookingReference}.pdf`;
  doc.save(fileName);
};


