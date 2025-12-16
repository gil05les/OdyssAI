import os
from pprint import pprint

from amadeus_mcp import (
    AirServer,
    AmadeusClientConfig,
    ContentServer,
    HotelServer,
    TransferServer,
    build_amadeus,
)


def main():
    cfg = AmadeusClientConfig.from_env()
    amadeus = build_amadeus(cfg)

    air = AirServer(amadeus)
    hotels = HotelServer(amadeus)
    transfers = TransferServer(amadeus)
    content = ContentServer(amadeus)

    print("=== Flight Offers Search (sample) ===")
    offers = air.flight_offers_search(origin="MAD", destination="LHR", departure_date="2025-12-20", adults=1, max_results=3)
    pprint(offers)

    print("=== Hotel Search (sample) ===")
    hotel_offers = hotels.hotel_search(latitude=40.4168, longitude=-3.7038, radius=5, adults=1)
    pprint(hotel_offers)

    print("=== Transfer Search (sample) ===")
    transfer_offers = transfers.transfer_search(
        start_latitude=40.4168,
        start_longitude=-3.7038,
        end_latitude=40.4531,
        end_longitude=-3.6883,
        start_date_time="2025-12-20T10:00:00",
    )
    pprint(transfer_offers)

    print("=== Travel Recommendations (sample) ===")
    recs = content.travel_recommendations(city_code="MAD")
    pprint(recs)


if __name__ == "__main__":
    missing = [v for v in ["AMADEUS_CLIENT_ID", "AMADEUS_CLIENT_SECRET"] if not os.environ.get(v)]
    if missing:
        raise SystemExit(f"Set required env vars: {', '.join(missing)}")
    main()

