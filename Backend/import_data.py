import json
from pathlib import Path

from database import Base, SessionLocal, engine
from models import Location

DATA_DIR = Path(__file__).resolve().parent / "data"
JSON_FILES = sorted(DATA_DIR.glob("부산_*.json"))


def to_float(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def import_json_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    inserted = 0
    updated = 0

    try:
        for file_path in JSON_FILES:
            with file_path.open("r", encoding="utf-8") as file:
                data = json.load(file)

            region = data.get("region", "부산")
            category = data.get("contentType", "기타")
            items = data.get("items", [])

            print(f"[적재] {file_path.name}: {len(items)}건")

            for item in items:
                content_id = str(item.get("contentid", "")).strip()
                title = str(item.get("title", "")).strip()
                if not content_id or not title:
                    continue

                location = (
                    db.query(Location)
                    .filter(Location.content_id == content_id)
                    .first()
                )

                if location is None:
                    location = Location(content_id=content_id)
                    db.add(location)
                    inserted += 1
                else:
                    updated += 1

                location.region = region
                location.category = category
                location.content_type_id = str(item.get("contenttypeid", ""))
                location.title = title
                location.address = item.get("addr1", "")
                location.address_detail = item.get("addr2", "")
                location.zipcode = item.get("zipcode", "")
                location.telephone = item.get("tel", "")
                location.longitude = to_float(item.get("mapx"))
                location.latitude = to_float(item.get("mapy"))
                location.image_url = item.get("firstimage", "")
                location.thumbnail_url = item.get("firstimage2", "")
                location.copyright_type = item.get("cpyrhtDivCd", "")
                location.created_time = item.get("createdtime", "")
                location.modified_time = item.get("modifiedtime", "")

            db.commit()

        print(f"완료: 신규 {inserted}건 / 갱신 {updated}건")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import_json_data()
