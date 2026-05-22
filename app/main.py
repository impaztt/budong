from __future__ import annotations

from typing import Optional

import typer
from loguru import logger

from app.config.logging_config import configure_logging
from app.repositories.supabase_client import SupabaseConfigurationError
from app.services.crawl_orchestrator import CrawlOrchestrator
from app.services.export_service import ExportService
from app.services.source_url_service import SourceUrlService


app = typer.Typer(help="Real Estate Listing Collector CLI")


def _setup() -> None:
    configure_logging()


def _handle_error(exc: Exception) -> None:
    logger.exception("command failed")
    typer.echo(f"ERROR: {exc}", err=True)
    raise typer.Exit(code=1) from exc


@app.command("register-url")
def register_url(
    url: str,
    memo: Optional[str] = typer.Option(None, "--memo", help="URL memo"),
) -> None:
    """Register a source URL."""
    _setup()
    try:
        source = SourceUrlService().register_url(url, memo=memo)
        typer.echo(
            f"registered id={source.get('id')} type={source.get('source_type')} "
            f"status={source.get('crawl_status')}"
        )
        typer.echo(f"resolved_url={source.get('resolved_url')}")
    except (ValueError, SupabaseConfigurationError) as exc:
        _handle_error(exc)


@app.command("list-urls")
def list_urls(
    active_only: bool = typer.Option(False, "--active-only", help="Only active URLs"),
) -> None:
    """List registered source URLs."""
    _setup()
    try:
        rows = SourceUrlService().list_source_urls(active_only=active_only)
        if not rows:
            typer.echo("No source URLs found.")
            return

        header = (
            "ID | ACTIVE | STATUS | TYPE | LAST_CRAWLED_AT | LAST_ERROR | SOURCE_URL"
        )
        typer.echo(header)
        typer.echo("-" * len(header))
        for row in rows:
            typer.echo(
                f"{row.get('id')} | {row.get('active_yn')} | {row.get('crawl_status')} | "
                f"{row.get('source_type')} | {row.get('last_crawled_at') or '-'} | "
                f"{row.get('last_error_message') or '-'} | {row.get('source_url')}"
            )
    except SupabaseConfigurationError as exc:
        _handle_error(exc)


@app.command("crawl")
def crawl(
    source_id: int = typer.Option(..., "--source-id", help="source_urls.id"),
) -> None:
    """Crawl a registered source URL."""
    _setup()
    try:
        result = CrawlOrchestrator().crawl_source(source_id)
        typer.echo(result)
    except (ValueError, SupabaseConfigurationError) as exc:
        _handle_error(exc)


@app.command("crawl-url")
def crawl_url(
    url: str,
    memo: Optional[str] = typer.Option(None, "--memo", help="URL memo"),
) -> None:
    """Register a URL if needed, then crawl it."""
    _setup()
    try:
        result = CrawlOrchestrator().crawl_url(url, memo=memo)
        typer.echo(result)
    except (ValueError, SupabaseConfigurationError) as exc:
        _handle_error(exc)


@app.command("crawl-active")
def crawl_active() -> None:
    """Crawl active URLs sequentially."""
    _setup()
    try:
        results = CrawlOrchestrator().crawl_active()
        for result in results:
            typer.echo(result)
    except SupabaseConfigurationError as exc:
        _handle_error(exc)


@app.command("crawl-pending")
def crawl_pending() -> None:
    """Crawl active URLs with PENDING status sequentially."""
    _setup()
    try:
        results = CrawlOrchestrator().crawl_pending()
        for result in results:
            typer.echo(result)
    except SupabaseConfigurationError as exc:
        _handle_error(exc)


@app.command("export")
def export(
    source_id: Optional[int] = typer.Option(None, "--source-id", help="source_urls.id"),
    all_records: bool = typer.Option(False, "--all", help="Export all listings"),
    from_date: Optional[str] = typer.Option(None, "--from-date", help="YYYY-MM-DD"),
    to_date: Optional[str] = typer.Option(None, "--to-date", help="YYYY-MM-DD"),
) -> None:
    """Export listings to xlsx."""
    _setup()
    try:
        path = ExportService().export(
            source_id=source_id,
            all_records=all_records,
            from_date=from_date,
            to_date=to_date,
        )
        typer.echo(f"exported: {path}")
    except (ValueError, SupabaseConfigurationError) as exc:
        _handle_error(exc)


@app.command("serve")
def serve(
    host: str = typer.Option("127.0.0.1", "--host", help="Bind host"),
    port: int = typer.Option(8000, "--port", help="Bind port"),
    reload: bool = typer.Option(False, "--reload", help="Reload on code changes"),
) -> None:
    """Run the local JSON API server."""
    _setup()
    try:
        import uvicorn
    except ImportError as exc:
        _handle_error(
            RuntimeError("uvicorn is not installed. Run pip install -r requirements.txt.")
        )
        raise typer.Exit(code=1) from exc

    uvicorn.run("app.web:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    app()
