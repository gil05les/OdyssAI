from typing import Any, Optional

from amadeus import Client, ResponseError

from .cache import ttl_cache


class TransferServer:
    def __init__(self, client: Client):
        self.client = client

    def _safe_call(self, fn, **params):
        try:
            return fn.get(**params).data
        except ResponseError as err:
            return {"error": str(err), "params": params}

    def transfer_search(
        self,
        start_latitude: float,
        start_longitude: float,
        end_latitude: float,
        end_longitude: float,
        start_date_time: str,
        passengers: int = 1,
    ) -> Any:
        params = {
            "startLatitude": start_latitude,
            "startLongitude": start_longitude,
            "endLatitude": end_latitude,
            "endLongitude": end_longitude,
            "startDateTime": start_date_time,
            "passengers": passengers,
        }
        return self._safe_call(self.client.shopping.transfer_offers, **params)

    def transfer_booking(self, offer_id: str, traveler: dict, contact: dict) -> Any:
        payload = {
            "data": {"type": "transfer-booking", "transferOfferId": offer_id, "traveler": traveler, "contact": contact}
        }
        try:
            return self.client.booking.transfer_bookings.post(payload).data
        except ResponseError as err:
            return {"error": str(err)}

    def transfer_management(self, booking_id: str) -> Any:
        return self._safe_call(self.client.booking.transfer_bookings, bookingId=booking_id)








