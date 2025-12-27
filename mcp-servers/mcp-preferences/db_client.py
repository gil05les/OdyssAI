"""
Read-only database client for user preferences.
Connects to PostgreSQL and retrieves user trip data.
"""
import os
import json
import re
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from typing import List, Dict, Any, Optional
from logger import get_logger


def get_database_url() -> str:
    """
    Get the database URL for sandbox environment.
    
    MCP sandbox containers are now on the same Docker network (odyssai-network)
    as PostgreSQL, so they can use the 'postgres' hostname directly.
    """
    default_url = "postgresql://odyssai:odyssai_password@postgres:5432/odyssai_db"
    url = os.getenv("DATABASE_URL", default_url)
    
    # If DATABASE_URL is provided but uses a different hostname, ensure we use 'postgres'
    # This handles cases where DATABASE_URL might have been set with a different hostname
    if '@postgres:' in url or '@postgres/' in url:
        # Already using postgres hostname, use as-is
        return url
    elif '@' in url:
        # Replace any hostname with 'postgres' since we're on the same network
        url = re.sub(r'@[^:/]+([:/])', r'@postgres\1', url)
    
    return url


# Get database URL with hostname transformation for sandbox
DATABASE_URL = get_database_url()

logger = get_logger("db_client")

# Log the resolved database URL (hiding password)
_safe_url = DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'hidden'
logger.info(f"Database URL resolved to: ...@{_safe_url}")


class PreferencesDBClient:
    """Read-only database client for extracting user preferences."""
    
    def __init__(self):
        """Initialize the database client."""
        try:
            # Create read-only engine
            self.engine = create_engine(
                DATABASE_URL,
                pool_pre_ping=True,  # Verify connections before using
                pool_size=5,
                max_overflow=10
            )
            self.SessionLocal = sessionmaker(bind=self.engine)
            logger.info(f"Database client initialized with URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'hidden'}")
        except Exception as e:
            logger.error(f"Failed to initialize database client: {e}")
            raise
    
    def get_user_trips(self, user_id: int, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all trips for a user (read-only).
        
        Args:
            user_id: The user ID to get trips for
            status: Optional status filter (planned, booked, completed)
        
        Returns:
            List of trip dictionaries with parsed trip_data
        """
        request_id = f"user_{user_id}"
        logger.info(f"Fetching trips for user {user_id}" + (f" (status: {status})" if status else ""))
        
        try:
            with self.SessionLocal() as session:
                if status:
                    query = text("""
                        SELECT id, status, trip_data, created_at, updated_at
                        FROM trips
                        WHERE user_id = :user_id AND status = :status
                        ORDER BY created_at DESC
                    """)
                    params = {"user_id": user_id, "status": status}
                else:
                    query = text("""
                        SELECT id, status, trip_data, created_at, updated_at
                        FROM trips
                        WHERE user_id = :user_id
                        ORDER BY created_at DESC
                    """)
                    params = {"user_id": user_id}
                
                result = session.execute(query, params)
                
                trips = []
                for row in result:
                    trip_data = row[2]  # trip_data column
                    
                    # Parse JSON if it's a string, otherwise use as-is
                    if isinstance(trip_data, str):
                        try:
                            trip_data = json.loads(trip_data)
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse trip_data JSON for trip {row[0]}")
                            trip_data = {}
                    elif trip_data is None:
                        trip_data = {}
                    
                    trips.append({
                        "id": row[0],
                        "status": row[1],
                        "trip_data": trip_data,
                        "created_at": str(row[3]) if row[3] else None,
                        "updated_at": str(row[4]) if row[4] else None
                    })
                
                logger.info(f"Retrieved {len(trips)} trips for user {user_id}")
                return trips
                
        except Exception as e:
            logger.error(f"Error fetching trips for user {user_id}: {e}", exc_info=True)
            raise Exception(f"Database query failed: {str(e)}")
    
    def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user profile (read-only).
        
        Args:
            user_id: The user ID to get profile for
        
        Returns:
            User profile dictionary or None if not found
        """
        logger.info(f"Fetching profile for user {user_id}")
        
        try:
            with self.SessionLocal() as session:
                query = text("""
                    SELECT full_name, visa_status, country
                    FROM user_profiles
                    WHERE user_id = :user_id
                """)
                result = session.execute(query, {"user_id": user_id}).first()
                
                if result:
                    profile = {
                        "full_name": result[0],
                        "visa_status": result[1],
                        "country": result[2]
                    }
                    logger.info(f"Retrieved profile for user {user_id}")
                    return profile
                else:
                    logger.info(f"No profile found for user {user_id}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching profile for user {user_id}: {e}", exc_info=True)
            return None

