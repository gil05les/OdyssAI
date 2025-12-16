from typing import Any, Optional

from amadeus import Client, ResponseError

from .cache import ttl_cache


class HotelServer:
    def __init__(self, client: Client):
        self.client = client

    def _safe_call(self, fn, **params):
        try:
            return fn.get(**params).data
        except ResponseError as err:
            return {"error": str(err), "params": params}

    def hotel_list(self, city_code: str, radius: int = 5, radius_unit: str = "KM") -> Any:
        params = {"cityCode": city_code, "radius": radius, "radiusUnit": radius_unit}
        return self._safe_call(self.client.reference_data.locations.hotels.by_city, **params)

    def hotel_search(
        self,
        latitude: float,
        longitude: float,
        radius: int = 5,
        adults: int = 1,
        check_in_date: Optional[str] = None,
        check_out_date: Optional[str] = None,
        board_type: Optional[str] = None,
        room_quantity: Optional[int] = None,
    ) -> Any:
        params = {"latitude": latitude, "longitude": longitude, "radius": radius, "adults": adults}
        if check_in_date:
            params["checkInDate"] = check_in_date
        if check_out_date:
            params["checkOutDate"] = check_out_date
        if board_type:
            params["boardType"] = board_type
        if room_quantity:
            params["roomQuantity"] = room_quantity
        return self._safe_call(self.client.shopping.hotel_offers, **params)

    def hotel_booking(self, offer_id: str, guest: dict) -> Any:
        payload = {"data": {"offerId": offer_id, "guests": [guest], "payments": []}}
        try:
            return self.client.booking.hotel_bookings.post(payload).data
        except ResponseError as err:
            return {"error": str(err)}

    @ttl_cache()
    def hotel_ratings(self, hotel_id: str) -> Any:
        return self._safe_call(self.client.e_reputation.hotel_sentiments, hotelIds=hotel_id)

    @ttl_cache()
    def hotel_name_autocomplete(self, keyword: str) -> Any:
        params = {"keyword": keyword, "subType": "HOTEL_GDS"}
        return self._safe_call(self.client.reference_data.locations, **params)








