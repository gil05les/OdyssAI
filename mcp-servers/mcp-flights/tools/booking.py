"""
Book flight tool.
MOCKED: Returns a mock booking confirmation for testing purposes.
In production, this would create a flight booking (PNR) using Amadeus Flight Create Orders API.
"""
import time
import json
import uuid
import random
from typing import Dict, Any, List, Optional

from logger import get_logger


def book_flight(
    priced_offer_id: str,
    priced_offer_data: Dict[str, Any],
    passengers: List[Dict[str, Any]],
    contact_email: str,
    client: Optional[Any] = None  # Not used in mock, but kept for API compatibility
) -> Dict[str, Any]:
    """
    MOCKED: Book a flight using a priced offer.
    
    This is a mock implementation that returns a fake booking confirmation.
    In production, this would create a real booking via Amadeus API.
    
    Args:
        priced_offer_id: Identifier for the priced offer (for logging)
        priced_offer_data: Full priced offer object from price_flight_offer
        passengers: List of passenger information dictionaries
            Each passenger should have: firstName, lastName, dateOfBirth, gender, contact
        contact_email: Contact email address
        client: Amadeus client wrapper instance (not used in mock)
    
    Returns:
        Dictionary with mock booking confirmation including PNR
    
    Example:
        Input: {
            "priced_offer_id": "OFFER_123",
            "priced_offer_data": {...},
            "passengers": [
                {
                    "firstName": "John",
                    "lastName": "Doe",
                    "dateOfBirth": "1990-01-01",
                    "gender": "MALE",
                    "contact": {
                        "emailAddress": "john.doe@example.com",
                        "phones": [{"deviceType": "MOBILE", "countryCallingCode": "1", "number": "5551234567"}]
                    }
                }
            ],
            "contact_email": "user@mail.com"
        }
        Output: {
            "booking_id": "MOCK_ABC12345",
            "pnr": "XYZ789",
            "status": "CONFIRMED (MOCK)",
            "mock": true,
            "passengers": 1
        }
    """
    request_id = f"book_{int(time.time() * 1000)}"
    logger = get_logger("book_flight", request_id)
    
    try:
        logger.info(f"[MOCK] Booking flight with offer: {priced_offer_id}")
        logger.debug(f"Number of passengers: {len(passengers)}")
        logger.debug(f"Contact email: {contact_email}")
        
        # Validate inputs
        if not passengers:
            raise ValueError("At least one passenger is required")
        
        if not contact_email:
            raise ValueError("Contact email is required")
        
        # Generate mock booking confirmation
        # PNR: 6-character alphanumeric code (typical format)
        mock_pnr = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))
        
        # Booking ID: MOCK_ prefix + 8-character hex
        mock_booking_id = f"MOCK_{uuid.uuid4().hex[:8].upper()}"
        
        # Simulate API call delay
        time.sleep(0.1)
        
        logger.info(f"[MOCK] Booking confirmed - ID: {mock_booking_id}, PNR: {mock_pnr}")
        
        return {
            'booking_id': mock_booking_id,
            'pnr': mock_pnr,
            'status': 'CONFIRMED (MOCK)',
            'mock': True,
            'passengers': len(passengers),
            'contact_email': contact_email,
            'priced_offer_id': priced_offer_id
        }
        
    except ValueError as error:
        logger.error(f"Validation error: {str(error)}")
        raise
    except Exception as error:
        error_str = str(error)
        error_type = type(error).__name__
        
        logger.error(f"Unexpected error: {error_type}: {error_str}", exc_info=True)
        raise Exception(f"Failed to book flight: {error_type}: {error_str}")

