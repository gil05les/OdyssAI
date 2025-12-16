from typing import Any

from amadeus import Client, ResponseError

from .cache import ttl_cache


class ContentServer:
    def __init__(self, client: Client):
        self.client = client

    def _safe_call(self, fn, **params):
        try:
            return fn.get(**params).data
        except ResponseError as err:
            return {"error": str(err), "params": params}

    @ttl_cache()
    def travel_recommendations(self, city_code: str) -> Any:
        return self._safe_call(self.client.reference_data.recommended_locations, cityCode=city_code)

    @ttl_cache()
    def points_of_interest(self, latitude: float, longitude: float, radius: int = 1) -> Any:
        params = {"latitude": latitude, "longitude": longitude, "radius": radius}
        return self._safe_call(self.client.reference_data.locations.points_of_interest, **params)

    @ttl_cache()
    def travel_guides(self, latitude: float, longitude: float, radius: int = 1) -> Any:
        params = {"latitude": latitude, "longitude": longitude, "radius": radius}
        return self._safe_call(self.client.reference_data.locations.points_of_interest.by_square, **params)








