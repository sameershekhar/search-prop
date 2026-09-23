from app.domain.models import Listing


def listing_from_dict(item: dict) -> Listing:
    """Maps a raw JSON dict (feed field names) to a Listing domain object."""
    return Listing(
        id=item["id"],
        source=item["source"],
        address=item["address"],
        city=item["city"],
        state=item["state"],
        zip=item["zip"],
        price=item["price"],
        bedrooms=item["bedrooms"],
        bathrooms=item["bathrooms"],
        sqft=item["sqft"],
        latitude=item["latitude"],
        longitude=item["longitude"],
        listed_date=item["listedDate"],
        status=item["status"],
        description=item["description"],
    )
