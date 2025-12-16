"""
Chat Service for parsing user messages and extracting form fields.

Uses OpenAI to intelligently parse natural language travel preferences
and extract structured data to update the travel form.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import re

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from config import Config

logger = logging.getLogger(__name__)


class ChatService:
    """Service for parsing chat messages and extracting form field updates."""
    
    def __init__(self):
        """Initialize the chat service."""
        if not Config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required for chat service")
        
        if OpenAI is None:
            raise ImportError("openai package is required. Install with: pip install openai")
        
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.DEFAULT_MODEL
    
    async def process_message(
        self,
        message: str,
        conversation_history: List[Dict[str, str]],
        current_form_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user message and extract form field updates.
        
        Args:
            message: User's message
            conversation_history: Previous messages in the conversation
            current_form_state: Current state of the form fields
            
        Returns:
            Dictionary with:
            - response: AI response message
            - form_updates: Dictionary of field updates
            - needs_clarification: Whether clarification is needed
            - clarification_question: Question to ask if needed
            - updated_fields: List of field names that were updated
        """
        try:
            # Build the prompt for the LLM
            system_prompt = self._build_system_prompt(current_form_state)
            user_prompt = self._build_user_prompt(message, conversation_history, current_form_state)
            
            # Call OpenAI
            # Use gpt-4 or gpt-3.5-turbo for JSON mode support
            # If DEFAULT_MODEL doesn't support JSON mode, fallback to gpt-4-turbo-preview
            model = self.model
            if not any(x in model.lower() for x in ["gpt-4", "gpt-3.5"]):
                model = "gpt-4-turbo-preview"
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
            )
            
            # Parse the response
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI")
            
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {content[:200]}")
                # Try to extract JSON from markdown code blocks
                import re
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                else:
                    raise ValueError(f"Invalid JSON response: {str(e)}")
            
            # Process and validate the form updates
            form_updates = self._process_form_updates(result.get("form_updates", {}))
            updated_fields = list(form_updates.keys())
            
            return {
                "response": result.get("response", "I've updated your preferences!"),
                "form_updates": form_updates,
                "needs_clarification": result.get("needs_clarification", False),
                "clarification_question": result.get("clarification_question"),
                "updated_fields": updated_fields
            }
            
        except Exception as e:
            logger.error(f"Error processing chat message: {e}", exc_info=True)
            return {
                "response": "I apologize, but I encountered an error processing your message. Could you please try rephrasing it?",
                "form_updates": {},
                "needs_clarification": False,
                "clarification_question": None,
                "updated_fields": []
            }
    
    def _build_system_prompt(self, current_form_state: Optional[Dict[str, Any]]) -> str:
        """Build the system prompt for the LLM."""
        return f"""You are a helpful travel planning assistant. Your job is to:
1. Parse user messages to extract travel preferences
2. Update form fields based on what the user says
3. Ask clarifying questions when information is ambiguous or missing
4. Make reasonable assumptions when confident

Current form state:
{json.dumps(current_form_state or {}, indent=2)}

Available form fields and their possible values:
- origin: string (e.g., "Zurich, Switzerland (ZRH)")
- destinations: array of strings (city/country names)
- surprise_me: boolean
- date_ranges: array of {{"from": "YYYY-MM-DD", "to": "YYYY-MM-DD"}}
- duration: [min_days, max_days] (e.g., [5, 10])
- traveler_type: "solo" | "couple" | "family" | "group"
- group_size: integer
- budget: [min_amount, max_amount] (e.g., [3000, 8000])
- environments: array of "beach" | "mountains" | "city" | "countryside" | "desert" | "jungle"
- climate: "tropical" | "mild" | "cold" | "any"
- trip_vibe: "relaxing" | "active" | "balanced" | "party"
- distance_preference: "close" | "far" | "offbeat" | "any"
- trip_purpose: "vacation" | "workation" | "honeymoon" | "reunion"
- experiences: array of "adventure" | "relaxation" | "cultural" | "food" | "nightlife" | "nature" | "photography" | "shopping" | "romance" | "wellness"

Guidelines:
- Parse dates intelligently: "next month" = calculate next month, "summer 2025" = June-August 2025, etc.
- Extract budgets: "around $5000" → budget: [4500, 5500], "$3000-$5000" → budget: [3000, 5000]
- Map natural language to enums: "beach vacation" → environments: ["beach"], "tropical" → climate: "tropical"
- Only update fields that are mentioned or can be inferred
- Ask questions when ambiguous (e.g., multiple destinations mentioned, unclear dates)
- Make reasonable assumptions when confident (e.g., "beach vacation" → climate: "tropical")

Return a JSON object with:
{{
  "response": "Your conversational response to the user",
  "form_updates": {{"field_name": value, ...}},
  "needs_clarification": boolean,
  "clarification_question": "question string if needs_clarification is true"
}}

Only include fields in form_updates that should be updated. Use null to clear a field."""
    
    def _build_user_prompt(
        self,
        message: str,
        conversation_history: List[Dict[str, str]],
        current_form_state: Optional[Dict[str, Any]]
    ) -> str:
        """Build the user prompt with context."""
        prompt = f"User message: {message}\n\n"
        
        if conversation_history:
            prompt += "Previous conversation:\n"
            for msg in conversation_history[-5:]:  # Last 5 messages for context
                prompt += f"- {msg.get('role', 'user')}: {msg.get('content', '')}\n"
            prompt += "\n"
        
        prompt += "Extract any travel preferences from the user's message and update the form accordingly."
        
        return prompt
    
    def _process_form_updates(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate form updates."""
        processed = {}
        
        # Handle date parsing
        if "date_ranges" in updates:
            processed["date_ranges"] = self._parse_date_ranges(updates["date_ranges"])
        
        # Handle duration
        if "duration" in updates:
            processed["duration"] = self._parse_duration(updates["duration"])
        
        # Handle budget
        if "budget" in updates:
            processed["budget"] = self._parse_budget(updates["budget"])
        
        # Copy other fields as-is (with validation)
        for key, value in updates.items():
            if key not in ["date_ranges", "duration", "budget"]:
                if value is not None:  # Don't include null values
                    processed[key] = value
        
        return processed
    
    def _parse_date_ranges(self, date_ranges: Any) -> List[Dict[str, str]]:
        """Parse date ranges from various formats."""
        if not date_ranges:
            return []
        
        if isinstance(date_ranges, list):
            result = []
            for dr in date_ranges:
                if isinstance(dr, dict):
                    from_date = dr.get("from")
                    to_date = dr.get("to")
                    if from_date and to_date:
                        result.append({"from": from_date, "to": to_date})
            return result
        
        return []
    
    def _parse_duration(self, duration: Any) -> List[int]:
        """Parse duration from various formats."""
        if isinstance(duration, list) and len(duration) >= 2:
            return [int(duration[0]), int(duration[1])]
        elif isinstance(duration, (int, float)):
            days = int(duration)
            return [days, days]
        return [5, 10]  # Default
    
    def _parse_budget(self, budget: Any) -> List[int]:
        """Parse budget from various formats."""
        if isinstance(budget, list) and len(budget) >= 2:
            return [int(budget[0]), int(budget[1])]
        elif isinstance(budget, (int, float)):
            amount = int(budget)
            # Create a range around the amount (±10%)
            margin = int(amount * 0.1)
            return [amount - margin, amount + margin]
        return [3000, 8000]  # Default

