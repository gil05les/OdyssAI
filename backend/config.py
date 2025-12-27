"""
Configuration management for the travel agent backend.
Handles environment variables and configuration settings.
"""
import os
import logging
from pathlib import Path
from typing import Optional

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    # Load .env from project root (one level up from backend/)
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Loaded environment variables from {env_path}")
except ImportError:
    # python-dotenv not installed, skip loading .env
    pass


class Config:
    """Configuration class for managing environment variables and settings."""
    
    # Amadeus API credentials
    # Support both naming conventions: AMADEUS_CLIENT_ID/AMADEUS_API_KEY
    AMADEUS_CLIENT_ID: Optional[str] = os.getenv('AMADEUS_CLIENT_ID') or os.getenv('AMADEUS_API_KEY')
    AMADEUS_CLIENT_SECRET: Optional[str] = os.getenv('AMADEUS_CLIENT_SECRET') or os.getenv('AMADEUS_API_SECRET')
    
    # Use AMADEUS_ENV to determine which API to use
    # AMADEUS_ENV=prod -> production API (api.amadeus.com)
    # AMADEUS_ENV=test -> test API (test.api.amadeus.com)
    # Default to test if not set
    amadeus_env = os.getenv('AMADEUS_ENV', 'test').lower()
    
    if amadeus_env == 'prod' or amadeus_env == 'production':
        AMADEUS_HOSTNAME: str = 'production'
    else:
        AMADEUS_HOSTNAME: str = 'test'  # default to test
    
    # OpenAI API (for agent)
    OPENAI_API_KEY: Optional[str] = os.getenv('OPENAI_API_KEY')
    
    # Unsplash API (for destination images)
    # Strip quotes if present (common when loading from .env files)
    _unsplash_key = os.getenv('UNSPLASH_ACCESS_KEY', '').strip()
    UNSPLASH_ACCESS_KEY: Optional[str] = _unsplash_key.strip('"\'') if _unsplash_key else None
    
    # OpenWeatherMap API (for temperature data)
    # Strip quotes if present (common when loading from .env files)
    _openweather_key = os.getenv('OPENWEATHERMAP_API_KEY', '').strip()
    OPENWEATHERMAP_API_KEY: Optional[str] = _openweather_key.strip('"\'' ) if _openweather_key else None
    
    # Yelp API (for activities/business search)
    # Strip quotes if present
    _yelp_key = os.getenv('YELP_API_KEY', '').strip()
    YELP_API_KEY: Optional[str] = _yelp_key.strip('"\'' ) if _yelp_key else None
    
    # Model configuration
    DEFAULT_MODEL: str = os.getenv('DEFAULT_MODEL', 'gpt-5.2')
    
    # MCP Server paths
    # When running in Docker, use HOST_PROJECT_ROOT env var for paths that Docker needs
    # (because Docker mounts need host paths, not container paths)
    # Always use absolute paths for Docker compatibility
    _project_root = os.getenv('HOST_PROJECT_ROOT', os.path.dirname(os.path.dirname(__file__)))
    _project_root = os.path.abspath(_project_root)  # Ensure absolute path
    
    # Log warning if HOST_PROJECT_ROOT is not set and we're likely in Docker
    if not os.getenv('HOST_PROJECT_ROOT') and os.path.exists('/mcp-servers'):
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            "HOST_PROJECT_ROOT not set! MCP servers may fail to mount volumes. "
            "Set HOST_PROJECT_ROOT environment variable in .env file or docker-compose.yml"
        )
    
    MCP_FLIGHTS_PATH: str = os.path.abspath(os.path.join(
        _project_root,
        'mcp-servers',
        'mcp-flights'
    ))
    
    MCP_HOTELS_PATH: str = os.path.abspath(os.path.join(
        _project_root,
        'mcp-servers',
        'mcp-hotels'
    ))
    
    MCP_CARS_PATH: str = os.path.abspath(os.path.join(
        _project_root,
        'mcp-servers',
        'mcp-cars'
    ))
    
    MCP_GEO_PATH: str = os.path.abspath(os.path.join(
        _project_root,
        'mcp-servers',
        'mcp-geo-destinations'
    ))
    
    MCP_ACTIVITIES_PATH: str = os.path.abspath(os.path.join(
        _project_root,
        'mcp-servers',
        'mcp-activities'
    ))
    
    MCP_TRANSPORT_PATH: str = os.path.abspath(os.path.join(
        _project_root,
        'mcp-servers',
        'mcp-transport'
    ))
    
    MCP_PREFERENCES_PATH: str = os.path.abspath(os.path.join(
        _project_root,
        'mcp-servers',
        'mcp-preferences'
    ))
    
    # Container names for long-running MCP servers
    MCP_FLIGHTS_CONTAINER: str = "odyssai-mcp-flights"
    MCP_HOTELS_CONTAINER: str = "odyssai-mcp-hotels"
    MCP_CARS_CONTAINER: str = "odyssai-mcp-cars"
    MCP_GEO_CONTAINER: str = "odyssai-mcp-geo"
    MCP_ACTIVITIES_CONTAINER: str = "odyssai-mcp-activities"
    MCP_TRANSPORT_CONTAINER: str = "odyssai-mcp-transport"
    MCP_PREFERENCES_CONTAINER: str = "odyssai-mcp-preferences"
    
    @classmethod
    def validate(cls) -> bool:
        """
        Validate that required configuration is present.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        required_vars = [
            ('AMADEUS_CLIENT_ID', cls.AMADEUS_CLIENT_ID),
            ('AMADEUS_CLIENT_SECRET', cls.AMADEUS_CLIENT_SECRET),
        ]
        
        missing = [var for var, value in required_vars if not value]
        
        if missing:
            print(f"Warning: Missing required environment variables: {', '.join(missing)}")
            return False
        
        return True
    
    @classmethod
    def get_amadeus_config(cls) -> dict:
        """Get Amadeus configuration dictionary."""
        return {
            'client_id': cls.AMADEUS_CLIENT_ID,
            'client_secret': cls.AMADEUS_CLIENT_SECRET,
            'hostname': cls.AMADEUS_HOSTNAME
        }
    
    @classmethod
    def get_amadeus_domain(cls) -> str:
        """Get Amadeus API domain based on hostname."""
        if cls.AMADEUS_HOSTNAME == 'production':
            return 'api.amadeus.com'
        else:
            return 'test.api.amadeus.com'
    
    @classmethod
    def get_postgres_ip(cls) -> str:
        """Get the PostgreSQL container's IP address for sandbox network access."""
        import subprocess
        try:
            result = subprocess.run(
                ["docker", "inspect", "-f", "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}", "odyssai-postgres"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                ip = result.stdout.strip()
                logger = logging.getLogger(__name__)
                logger.info(f"📡 Resolved postgres container IP: {ip}")
                return ip
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"⚠️  Failed to get postgres IP: {e}")
        return None
    
    @classmethod
    def get_runtime_permissions(cls):
        """Get runtime permissions for MCP servers."""
        from mcp_sandbox_openai_sdk import DomainPort, HostPort, EnvironmentVariable
        from ipaddress import IPv4Address
        
        amadeus_domain = cls.get_amadeus_domain()
        permissions = [
            # PyPI access for package installation
            DomainPort(domain='pypi.org', port=443),
            DomainPort(domain='files.pythonhosted.org', port=443),
            # Amadeus API access
            DomainPort(domain=amadeus_domain, port=443),
            EnvironmentVariable(name="AMADEUS_CLIENT_ID"),
            EnvironmentVariable(name="AMADEUS_CLIENT_SECRET"),
            # Yelp API access (for activities)
            DomainPort(domain='api.yelp.com', port=443),
            EnvironmentVariable(name="YELP_API_KEY"),
            # Google Maps API access
            DomainPort(domain='maps.googleapis.com', port=443),
            EnvironmentVariable(name="GOOGLE_MAPS_API_KEY"),
            # Note: Uber API integration disabled - using LLM fallback
            # No Uber API permissions needed
            # Database access for preferences MCP
            EnvironmentVariable(name="DATABASE_URL"),
        ]
        
        # Add PostgreSQL container IP to allowed connections
        # This allows MCP sandbox containers to connect to the database
        postgres_ip = cls.get_postgres_ip()
        if postgres_ip:
            try:
                permissions.append(HostPort(host=IPv4Address(postgres_ip), port=5432))
            except ValueError:
                # Invalid IP address, skip
                pass
        
        # Pass AMADEUS_ENV to the sandbox so it knows which API to use
        permissions.append(EnvironmentVariable(name="AMADEUS_ENV"))
        
        return permissions

