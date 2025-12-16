from typing import Any, Dict, Optional

from amadeus import Client, ResponseError

from .cache import ttl_cache


class AirServer:
    def __init__(self, client: Client):
        self.client = client

    def _safe_call(self, fn, **params):
        try:
            return fn.get(**params).data
        except ResponseError as err:
            return {"error": str(err), "params": params}

    def flight_offers_search(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        adults: int = 1,
        return_date: Optional[str] = None,
        currency: Optional[str] = None,
        max_results: int = 50,
        travel_class: Optional[str] = None,
    ) -> Any:
        params: Dict[str, Any] = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "adults": adults,
            "max": max_results,
        }
        if return_date:
            params["returnDate"] = return_date
        if currency:
            params["currencyCode"] = currency
        if travel_class:
            params["travelClass"] = travel_class
        return self._safe_call(self.client.shopping.flight_offers_search, **params)

    def flight_offers_price(self, flight_offer: dict) -> Any:
        try:
            return self.client.shopping.flight_offers.pricing.post(flight_offer).data
        except ResponseError as err:
            return {"error": str(err)}

    def flight_create_order(self, flight_offer: dict, traveler: dict) -> Any:
        payload = {"type": "flight-order", "flightOffers": [flight_offer], "travelers": [traveler]}
        try:
            return self.client.booking.flight_orders.post(payload).data
        except ResponseError as err:
            return {"error": str(err)}

    def flight_order_management(self, order_id: str) -> Any:
        return self._safe_call(self.client.booking.flight_orders, orderId=order_id)

    def seatmap_display(self, flight_offer: dict) -> Any:
        try:
            return self.client.shopping.seatmaps.post(flight_offer).data
        except ResponseError as err:
            return {"error": str(err)}

    def branded_fares_upsell(self, flight_offer: dict) -> Any:
        try:
            return self.client.shopping.flight_offers.upselling.post(flight_offer).data
        except ResponseError as err:
            return {"error": str(err)}

    def flight_inspiration_search(self, origin: str, one_way: bool = False) -> Any:
        params = {"origin": origin}
        if one_way:
            params["oneWay"] = "true"
        return self._safe_call(self.client.shopping.flight_destinations, **params)

    def flight_cheapest_date_search(self, origin: str, destination: str) -> Any:
        params = {"origin": origin, "destination": destination}
        return self._safe_call(self.client.shopping.flight_dates, **params)

    def flight_availabilities_search(self, payload: dict) -> Any:
        try:
            return self.client.shopping.availability.flight_availabilities.post(payload).data
        except ResponseError as err:
            return {"error": str(err)}

    def travel_recommendations(self, city_code: str) -> Any:
        return self._safe_call(self.client.reference_data.recommended_locations, cityCode=city_code)

    def tours_and_activities(self, latitude: float, longitude: float, radius: int = 5) -> Any:
        params = {"latitude": latitude, "longitude": longitude, "radius": radius}
        return self._safe_call(self.client.shopping.activities, **params)

    @ttl_cache()
    def city_search(self, keyword: str, country_code: Optional[str] = None) -> Any:
        params = {"keyword": keyword, "subType": "CITY"}
        if country_code:
            params["countryCode"] = country_code
        return self._safe_call(self.client.reference_data.locations, **params)

    def on_demand_flight_status(self, flight_number: str, date: str) -> Any:
        params = {"flightNumber": flight_number, "scheduledDepartureDate": date}
        return self._safe_call(self.client.schedule.flights, **params)

    @ttl_cache()
    def airport_city_search(self, keyword: str, sub_type: str = "AIRPORT,CITY") -> Any:
        params = {"keyword": keyword, "subType": sub_type}
        return self._safe_call(self.client.reference_data.locations, **params)

    @ttl_cache()
    def airport_nearest(self, latitude: float, longitude: float, radius_km: int = 50) -> Any:
        params = {"latitude": latitude, "longitude": longitude, "radius": radius_km}
        return self._safe_call(self.client.reference_data.locations.airports, **params)

    def airport_routes(self, departure_iata: str) -> Any:
        return self._safe_call(self.client.airport.direct_destinations, departure_iata=departure_iata)

    def flight_most_traveled_destinations(self, origin_city_code: str, period: str = "2017-01") -> Any:
        params = {"originCityCode": origin_city_code, "period": period}
        return self._safe_call(self.client.travel.analytics.air_traffic.traveled, **params)

    def flight_most_booked_destinations(self, origin_city_code: str, period: str = "2017-01") -> Any:
        params = {"originCityCode": origin_city_code, "period": period}
        return self._safe_call(self.client.travel.analytics.air_traffic.booked, **params)

    def flight_busiest_traveling_period(self, city_code: str, period: str = "2017") -> Any:
        params = {"cityCode": city_code, "period": period}
        return self._safe_call(self.client.travel.analytics.air_traffic.busiest_period, **params)

    @ttl_cache()
    def flight_checkin_links(self, airline_code: str) -> Any:
        return self._safe_call(self.client.reference_data.urls.checkin_links, airlineCode=airline_code)

    @ttl_cache()
    def airline_code_lookup(self, airline_codes: str) -> Any:
        params = {"airlineCodes": airline_codes}
        return self._safe_call(self.client.reference_data.airlines, **params)

    def airline_routes(self, airline_code: str) -> Any:
        params = {"airlineCode": airline_code}
        return self._safe_call(self.client.airline.destinations, **params)








