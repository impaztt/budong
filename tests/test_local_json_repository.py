from app.repositories.local_json_repository import LocalJsonRepository


def test_local_json_repository_stores_sources_and_listings(tmp_path) -> None:
    repository = LocalJsonRepository(tmp_path / "preview_store.json")

    source = repository.upsert_source(
        source_url="https://example.com/a",
        resolved_url="https://example.com/a",
        source_type="UNKNOWN",
        memo="sample",
        status="RUNNING",
    )
    repository.upsert_listings(
        source["id"],
        [
            {
                "source_url_id": source["id"],
                "article_no": "123",
                "price_text": "1억",
            }
        ],
    )
    repository.update_source(source["id"], {"crawl_status": "SUCCESS"})

    sources = repository.list_sources()
    listings = repository.list_listings(source_id=source["id"])

    assert sources[0]["crawl_status"] == "SUCCESS"
    assert listings[0]["article_no"] == "123"
