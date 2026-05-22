import json

from app.parsers.naver_land_parser import NaverLandParser


def test_parse_article_list_from_json() -> None:
    payload = {
        "articleList": [
            {
                "articleNo": "1234567890",
                "tradeTypeName": "매매",
                "realEstateTypeName": "아파트",
                "complexName": "테스트단지",
                "buildingName": "101동",
                "floorInfo": "고/25",
                "direction": "남향",
                "area1": "84.97",
                "area2": "59.98",
                "dealOrWarrantPrc": "9억 500",
                "realtorName": "테스트공인중개사",
                "articleConfirmYmd": "20260522",
                "articleFeatureDesc": "샘플 설명",
            }
        ]
    }

    listings = NaverLandParser().parse(json.dumps(payload), source_url="https://land.naver.com")

    assert len(listings) == 1
    listing = listings[0]
    assert listing["article_no"] == "1234567890"
    assert listing["complex_name"] == "테스트단지"
    assert listing["exclusive_area_m2"] == 59.98
    assert listing["price_amount"] == 905_000_000
    assert listing["source_type"] == "NAVER_LAND"
