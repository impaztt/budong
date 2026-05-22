from app.utils.area_parser import parse_area_m2


def test_parse_area_m2() -> None:
    assert parse_area_m2("49㎡") == 49.0
    assert parse_area_m2("84.97㎡") == 84.97
    assert parse_area_m2("전용 59.98㎡") == 59.98
    assert parse_area_m2(None) is None
