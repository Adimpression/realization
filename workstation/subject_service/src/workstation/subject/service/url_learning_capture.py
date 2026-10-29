# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from dataclasses import dataclass
from email.message import Message
import hashlib
from html.parser import HTMLParser
import json
import mimetypes
from pathlib import Path
import re
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

try:
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright
except Exception:  # pragma: no cover - import availability depends on runtime
    PlaywrightError = RuntimeError

    class PlaywrightTimeoutError(Exception):
        pass

    sync_playwright = None

try:
    from trafilatura import bare_extraction as trafilatura_bare_extraction
    from trafilatura import extract as trafilatura_extract
except Exception:  # pragma: no cover - import availability depends on runtime
    trafilatura_bare_extraction = None
    trafilatura_extract = None

from realized_core_semantics.semantic_text import collapse_ws


_DEFAULT_USER_AGENT = "realized-url-learning/1.0"
_MAX_CAPTURE_BYTES = 8 * 1024 * 1024
_MAX_ASSET_BYTES = 4 * 1024 * 1024
_DEFAULT_TIMEOUT_SECONDS = 15.0
_DEFAULT_VIEWPORT_WIDTH = 1440
_DEFAULT_VIEWPORT_HEIGHT = 2200


@dataclass(frozen=True)
class CapturedUrlLearningBundle:
    requested_url: str
    final_url: str
    title: str
    media_type: str
    status_code: int
    fetched_at_epoch_ms: int
    markdown_text: str
    bundle_files: dict[str, bytes | str]
    metadata: dict[str, Any]
    elements: tuple[dict[str, Any], ...]
    asset_manifest: tuple[dict[str, Any], ...]

    @property
    def suggested_source_name(self) -> str:
        title = collapse_ws(self.title)
        if title:
            return title
        path_name = Path(urlparse(self.final_url or self.requested_url).path).stem
        return collapse_ws(path_name) or "learned-url"

    def source_bundle_override(self) -> dict[str, Any]:
        return {
            "source_kind": "url",
            "source_ref": self.requested_url,
            "media_type": self.media_type,
            "title": self.title or self.suggested_source_name,
            "metadata": dict(self.metadata),
            "bundle_files": dict(self.bundle_files),
        }

    def report(self) -> dict[str, Any]:
        return {
            "requested_url": self.requested_url,
            "final_url": self.final_url,
            "title": self.title,
            "media_type": self.media_type,
            "status_code": self.status_code,
            "fetched_at_epoch_ms": self.fetched_at_epoch_ms,
            "element_count": len(self.elements),
            "asset_count": len(self.asset_manifest),
            "bundle_files": sorted(self.bundle_files.keys()),
        }


@dataclass(frozen=True)
class _ResponsePayload:
    url: str
    status_code: int
    media_type: str
    charset: str
    body: bytes
    headers: dict[str, str]


@dataclass(frozen=True)
class _RenderedPagePayload:
    requested_url: str
    final_url: str
    status_code: int
    media_type: str
    html_text: str
    title: str
    screenshot_png: bytes
    headers: dict[str, str]


@dataclass(frozen=True)
class _CapturedElement:
    kind: str
    text: str = ""
    level: int = 0
    src: str = ""
    alt: str = ""
    mime_type: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"kind": self.kind}
        if self.text:
            payload["text"] = self.text
        if self.level:
            payload["level"] = self.level
        if self.src:
            payload["src"] = self.src
        if self.alt:
            payload["alt"] = self.alt
        if self.mime_type:
            payload["mime_type"] = self.mime_type
        return payload


class _StructuredHtmlParser(HTMLParser):
    _TEXT_CAPTURE_TAGS = {"title", "p", "li", "blockquote", "pre"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.elements: list[_CapturedElement] = []
        self._capture_stack: list[dict[str, Any]] = []
        self._suppressed_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized_tag = str(tag or "").lower()
        attrs_map = {str(key).lower(): str(value or "") for key, value in attrs}
        if normalized_tag in {"script", "style", "noscript"}:
            self._suppressed_depth += 1
            return
        if self._suppressed_depth:
            return
        if normalized_tag == "br" and self._capture_stack:
            self._capture_stack[-1]["parts"].append("\n")
            return
        if normalized_tag == "img":
            src = collapse_ws(attrs_map.get("src", ""))
            if src:
                self.elements.append(
                    _CapturedElement(
                        kind="image",
                        src=src,
                        alt=collapse_ws(attrs_map.get("alt", "")),
                    )
                )
            return
        heading_level = _heading_level(normalized_tag)
        if heading_level:
            self._capture_stack.append(
                {"tag": normalized_tag, "kind": "heading", "level": heading_level, "parts": []}
            )
            return
        if normalized_tag in self._TEXT_CAPTURE_TAGS:
            self._capture_stack.append({"tag": normalized_tag, "kind": normalized_tag, "parts": []})

    def handle_endtag(self, tag: str) -> None:
        normalized_tag = str(tag or "").lower()
        if normalized_tag in {"script", "style", "noscript"}:
            self._suppressed_depth = max(0, self._suppressed_depth - 1)
            return
        if self._suppressed_depth or not self._capture_stack:
            return
        if self._capture_stack[-1]["tag"] != normalized_tag:
            return
        capture = self._capture_stack.pop()
        kind = str(capture.get("kind", ""))
        raw_text = "".join(str(item) for item in capture.get("parts", []))
        text = _normalize_captured_text(raw_text, preserve_newlines=kind == "pre")
        if not text:
            return
        if self._capture_stack:
            self._capture_stack[-1]["parts"].append(text)
            self._capture_stack[-1]["parts"].append("\n")
        if kind == "heading":
            self.elements.append(_CapturedElement(kind="heading", text=text, level=int(capture.get("level", 0) or 0)))
        elif kind == "title":
            self.elements.append(_CapturedElement(kind="title", text=text))
        elif kind == "pre":
            self.elements.append(_CapturedElement(kind="code", text=text))
        elif kind == "li":
            self.elements.append(_CapturedElement(kind="list_item", text=text))
        elif kind == "blockquote":
            self.elements.append(_CapturedElement(kind="blockquote", text=text))
        else:
            self.elements.append(_CapturedElement(kind="paragraph", text=text))

    def handle_data(self, data: str) -> None:
        if self._suppressed_depth or not self._capture_stack:
            return
        self._capture_stack[-1]["parts"].append(str(data or ""))


def capture_url_learning_bundle(
    *,
    url: str,
    max_assets: int = 8,
    timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
) -> CapturedUrlLearningBundle:
    normalized_url = _normalize_learning_url(url)
    capture_warning = ""
    rendered_page: _RenderedPagePayload | None = None
    if sync_playwright is not None and trafilatura_extract is not None:
        try:
            rendered_page = _fetch_rendered_page_with_playwright(
                normalized_url,
                timeout_seconds=timeout_seconds,
            )
        except Exception as exc:
            capture_warning = collapse_ws(str(exc)) or "playwright_capture_failed"
    if rendered_page is not None and _looks_like_html_media_type(rendered_page.media_type):
        return _capture_rendered_html_bundle(
            rendered_page,
            timeout_seconds=timeout_seconds,
            max_assets=max_assets,
            warning=capture_warning,
        )
    return _capture_fallback_bundle(
        normalized_url,
        max_assets=max_assets,
        timeout_seconds=timeout_seconds,
        warning=capture_warning,
    )


def _capture_rendered_html_bundle(
    rendered_page: _RenderedPagePayload,
    *,
    timeout_seconds: float,
    max_assets: int,
    warning: str,
) -> CapturedUrlLearningBundle:
    fetched_at_epoch_ms = int(time.time() * 1000)
    bundle_files: dict[str, bytes | str] = {
        "rendered.html": rendered_page.html_text,
        "screenshot.png": rendered_page.screenshot_png,
    }
    elements = _extract_structured_elements(rendered_page.html_text)
    markdown_text = _extract_markdown_from_html(
        rendered_page.html_text,
        page_url=rendered_page.final_url,
        title_hint=rendered_page.title,
        elements=elements,
    )
    bundle_files["elements.json"] = json.dumps(
        [element.to_dict() for element in elements],
        indent=2,
        sort_keys=True,
    )
    asset_manifest = _download_image_assets(
        page_url=rendered_page.final_url,
        elements=elements,
        bundle_files=bundle_files,
        max_assets=max_assets,
        timeout_seconds=timeout_seconds,
    )
    bundle_files["asset-manifest.json"] = json.dumps(asset_manifest, indent=2, sort_keys=True)
    title = (
        collapse_ws(rendered_page.title)
        or _capture_title_from_elements(elements)
        or _first_markdown_heading(markdown_text)
        or _title_from_url(rendered_page.final_url)
    )
    metadata = {
        "requested_url": rendered_page.requested_url,
        "final_url": rendered_page.final_url,
        "fetch_method": "playwright",
        "extract_method": "trafilatura",
        "fetch_timestamp_epoch_ms": fetched_at_epoch_ms,
        "status_code": rendered_page.status_code,
        "media_type": rendered_page.media_type,
        "capture_kind": "rendered_html",
        "rendered_relpath": "rendered.html",
        "screenshot_relpath": "screenshot.png",
        "elements_relpath": "elements.json",
        "asset_manifest_relpath": "asset-manifest.json",
        "asset_count": len(asset_manifest),
        "capture_stack": ["playwright", "trafilatura", "html.parser"],
        "response_headers": dict(rendered_page.headers),
        "content_hash": hashlib.sha256(rendered_page.html_text.encode("utf-8")).hexdigest(),
    }
    if warning:
        metadata["capture_warning"] = warning
    return CapturedUrlLearningBundle(
        requested_url=rendered_page.requested_url,
        final_url=rendered_page.final_url,
        title=title,
        media_type=rendered_page.media_type,
        status_code=rendered_page.status_code,
        fetched_at_epoch_ms=fetched_at_epoch_ms,
        markdown_text=markdown_text,
        bundle_files=bundle_files,
        metadata=metadata,
        elements=tuple(element.to_dict() for element in elements),
        asset_manifest=tuple(asset_manifest),
    )


def _capture_fallback_bundle(
    normalized_url: str,
    *,
    max_assets: int,
    timeout_seconds: float,
    warning: str,
) -> CapturedUrlLearningBundle:
    page = _fetch_url_payload(normalized_url, timeout_seconds=timeout_seconds)
    fetched_at_epoch_ms = int(time.time() * 1000)
    bundle_files: dict[str, bytes | str] = {}
    if _looks_like_html_media_type(page.media_type):
        html_text = _decode_response_body(page.body, charset=page.charset)
        elements = _extract_structured_elements(html_text)
        markdown_text = _elements_to_markdown(elements, fallback_url=page.url)
        bundle_files["rendered.html"] = html_text
        bundle_files["elements.json"] = json.dumps(
            [element.to_dict() for element in elements],
            indent=2,
            sort_keys=True,
        )
        asset_manifest = _download_image_assets(
            page_url=page.url,
            elements=elements,
            bundle_files=bundle_files,
            max_assets=max_assets,
            timeout_seconds=timeout_seconds,
        )
        bundle_files["asset-manifest.json"] = json.dumps(asset_manifest, indent=2, sort_keys=True)
        metadata = {
            "requested_url": normalized_url,
            "final_url": page.url,
            "fetch_method": "urllib_request",
            "extract_method": "html_parser_fallback",
            "fetch_timestamp_epoch_ms": fetched_at_epoch_ms,
            "status_code": page.status_code,
            "media_type": page.media_type,
            "capture_kind": "raw_html",
            "rendered_relpath": "rendered.html",
            "elements_relpath": "elements.json",
            "asset_manifest_relpath": "asset-manifest.json",
            "asset_count": len(asset_manifest),
            "screenshot_relpath": "",
            "capture_stack": ["urllib.request", "html.parser"],
            "response_headers": dict(page.headers),
            "content_hash": hashlib.sha256(page.body).hexdigest(),
        }
        if warning:
            metadata["capture_warning"] = warning
        return CapturedUrlLearningBundle(
            requested_url=normalized_url,
            final_url=page.url,
            title=_capture_title_from_elements(elements) or _title_from_url(page.url),
            media_type=page.media_type,
            status_code=page.status_code,
            fetched_at_epoch_ms=fetched_at_epoch_ms,
            markdown_text=markdown_text,
            bundle_files=bundle_files,
            metadata=metadata,
            elements=tuple(element.to_dict() for element in elements),
            asset_manifest=tuple(asset_manifest),
        )
    decoded_text = _decode_response_body(page.body, charset=page.charset)
    markdown_text = _non_html_markdown_text(decoded_text, fallback_url=page.url)
    title = _first_markdown_heading(markdown_text) or _title_from_url(page.url)
    sidecar_name = "source.md" if "markdown" in page.media_type else "source.txt"
    bundle_files[sidecar_name] = decoded_text
    metadata = {
        "requested_url": normalized_url,
        "final_url": page.url,
        "fetch_method": "urllib_request",
        "extract_method": "plain_text_fallback",
        "fetch_timestamp_epoch_ms": fetched_at_epoch_ms,
        "status_code": page.status_code,
        "media_type": page.media_type,
        "capture_kind": "raw_text",
        "source_capture_relpath": sidecar_name,
        "asset_count": 0,
        "screenshot_relpath": "",
        "capture_stack": ["urllib.request"],
        "response_headers": dict(page.headers),
        "content_hash": hashlib.sha256(page.body).hexdigest(),
    }
    if warning:
        metadata["capture_warning"] = warning
    return CapturedUrlLearningBundle(
        requested_url=normalized_url,
        final_url=page.url,
        title=title,
        media_type=page.media_type,
        status_code=page.status_code,
        fetched_at_epoch_ms=fetched_at_epoch_ms,
        markdown_text=markdown_text,
        bundle_files=bundle_files,
        metadata=metadata,
        elements=(),
        asset_manifest=(),
    )


def _normalize_learning_url(url: str) -> str:
    normalized = collapse_ws(str(url or ""))
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not collapse_ws(parsed.netloc):
        raise ValueError("Enter a full http:// or https:// URL.")
    return normalized


def _fetch_rendered_page_with_playwright(
    url: str,
    *,
    timeout_seconds: float,
) -> _RenderedPagePayload:
    if sync_playwright is None:
        raise ValueError("playwright is not available")
    timeout_ms = max(1, int(float(timeout_seconds) * 1000))
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page(
                user_agent=_DEFAULT_USER_AGENT,
                viewport={"width": _DEFAULT_VIEWPORT_WIDTH, "height": _DEFAULT_VIEWPORT_HEIGHT},
            )
            response = page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            if response is None:
                raise ValueError(f"browser navigation returned no response: {url}")
            try:
                page.wait_for_load_state("networkidle", timeout=timeout_ms)
            except PlaywrightTimeoutError:
                pass
            headers = _playwright_response_headers(response)
            media_type = _playwright_response_media_type(headers)
            if not _looks_like_html_media_type(media_type):
                raise ValueError(f"non-html content type from browser navigation: {media_type}")
            html_text = page.content()
            screenshot_png = page.screenshot(type="png", full_page=True)
            return _RenderedPagePayload(
                requested_url=url,
                final_url=collapse_ws(page.url) or url,
                status_code=int(getattr(response, "status", 200) or 200),
                media_type=media_type,
                html_text=html_text,
                title=collapse_ws(page.title() or ""),
                screenshot_png=screenshot_png,
                headers=headers,
            )
        except PlaywrightError as exc:
            raise ValueError(f"playwright capture failed: {collapse_ws(str(exc)) or url}") from exc
        finally:
            browser.close()


def _playwright_response_headers(response: Any) -> dict[str, str]:
    raw_headers: Any
    all_headers = getattr(response, "all_headers", None)
    if callable(all_headers):
        raw_headers = all_headers()
    else:
        raw_headers = getattr(response, "headers", {}) or {}
    if not isinstance(raw_headers, dict):
        return {}
    return {
        str(key): collapse_ws(str(value))
        for key, value in raw_headers.items()
        if collapse_ws(str(key)) and collapse_ws(str(value))
    }


def _playwright_response_media_type(headers: dict[str, str]) -> str:
    content_type = collapse_ws(headers.get("content-type", ""))
    if not content_type:
        return "text/html"
    return collapse_ws(content_type.split(";", 1)[0]) or "text/html"


def _extract_structured_elements(html_text: str) -> list[_CapturedElement]:
    parser = _StructuredHtmlParser()
    parser.feed(html_text)
    parser.close()
    return list(parser.elements)


def _extract_markdown_from_html(
    html_text: str,
    *,
    page_url: str,
    title_hint: str,
    elements: list[_CapturedElement],
) -> str:
    markdown_text = ""
    if trafilatura_extract is not None:
        try:
            markdown_text = str(
                trafilatura_extract(
                    html_text,
                    url=page_url,
                    output_format="markdown",
                    include_tables=True,
                    include_images=True,
                    include_links=True,
                    favor_precision=True,
                    with_metadata=False,
                )
                or ""
            )
        except Exception:
            markdown_text = ""
    markdown_text = markdown_text.strip()
    if markdown_text:
        rendered = markdown_text
        if title_hint and not rendered.lstrip().startswith("#"):
            rendered = f"# {title_hint}\n\n{rendered}"
        return rendered if rendered.endswith("\n") else rendered + "\n"
    return _elements_to_markdown(elements, fallback_url=page_url)


def _fetch_url_payload(url: str, *, timeout_seconds: float) -> _ResponsePayload:
    request = Request(url, headers={"User-Agent": _DEFAULT_USER_AGENT})
    try:
        with urlopen(request, timeout=float(timeout_seconds)) as response:
            body = response.read(_MAX_CAPTURE_BYTES + 1)
            if len(body) > _MAX_CAPTURE_BYTES:
                raise ValueError("URL capture exceeded the maximum supported size.")
            headers = _response_headers_map(getattr(response, "headers", None) or response.info())
            media_type = _response_media_type(getattr(response, "headers", None) or response.info())
            charset = _response_charset(getattr(response, "headers", None) or response.info())
            return _ResponsePayload(
                url=str(getattr(response, "geturl", lambda: url)()),
                status_code=int(getattr(response, "status", getattr(response, "code", 200)) or 200),
                media_type=media_type,
                charset=charset,
                body=body,
                headers=headers,
            )
    except HTTPError as exc:
        raise ValueError(f"URL fetch failed with HTTP {exc.code}: {url}") from exc
    except URLError as exc:
        raise ValueError(f"URL fetch failed: {collapse_ws(str(exc.reason)) or url}") from exc


def _decode_response_body(body: bytes, *, charset: str) -> str:
    normalized_charset = collapse_ws(charset) or "utf-8"
    try:
        return body.decode(normalized_charset, errors="replace")
    except LookupError:
        return body.decode("utf-8", errors="replace")


def _response_headers_map(headers: Message) -> dict[str, str]:
    return {
        str(key): collapse_ws(str(value))
        for key, value in headers.items()
        if collapse_ws(str(key)) and collapse_ws(str(value))
    }


def _response_media_type(headers: Message) -> str:
    try:
        media_type = collapse_ws(headers.get_content_type())
    except Exception:
        media_type = ""
    return media_type or "application/octet-stream"


def _response_charset(headers: Message) -> str:
    try:
        charset = collapse_ws(str(headers.get_content_charset() or ""))
    except Exception:
        charset = ""
    return charset or "utf-8"


def _looks_like_html_media_type(media_type: str) -> bool:
    normalized = collapse_ws(media_type).lower()
    return normalized in {"text/html", "application/xhtml+xml"} or normalized.endswith("+html")


def _heading_level(tag: str) -> int:
    if len(tag) == 2 and tag.startswith("h") and tag[1].isdigit():
        value = int(tag[1])
        if 1 <= value <= 6:
            return value
    return 0


def _normalize_captured_text(text: str, *, preserve_newlines: bool) -> str:
    if preserve_newlines:
        lines = [line.rstrip() for line in str(text or "").splitlines()]
        while lines and not collapse_ws(lines[0]):
            lines.pop(0)
        while lines and not collapse_ws(lines[-1]):
            lines.pop()
        return "\n".join(lines).strip()
    normalized = re.sub(r"\s+", " ", str(text or "")).strip()
    return normalized


def _elements_to_markdown(elements: list[_CapturedElement], *, fallback_url: str) -> str:
    lines: list[str] = []
    title = _capture_title_from_elements(elements) or _title_from_url(fallback_url)
    if title:
        lines.append(f"# {title}")
        lines.append("")
    used_title = False
    last_rendered = ""
    for element in elements:
        if element.kind == "title":
            if not used_title:
                used_title = True
            continue
        if element.kind == "heading":
            prefix = "#" * max(1, min(6, element.level or 1))
            rendered = f"{prefix} {element.text}"
        elif element.kind == "paragraph":
            rendered = element.text
        elif element.kind == "list_item":
            rendered = f"- {element.text}"
        elif element.kind == "blockquote":
            rendered = f"> {element.text}"
        elif element.kind == "code":
            rendered = f"```\n{element.text}\n```"
        elif element.kind == "image":
            image_target = collapse_ws(element.src)
            alt_text = collapse_ws(element.alt) or "image"
            rendered = f"![{alt_text}]({image_target})"
        else:
            continue
        if collapse_ws(rendered) and collapse_ws(rendered) != collapse_ws(last_rendered):
            if lines and lines[-1] != "":
                lines.append("")
            lines.append(rendered)
            last_rendered = rendered
    rendered_text = "\n".join(lines).strip()
    if rendered_text:
        return rendered_text + "\n"
    return f"# {_title_from_url(fallback_url)}\n\nSource URL: {fallback_url}\n"


def _capture_title_from_elements(elements: list[_CapturedElement]) -> str:
    for element in elements:
        if element.kind == "title" and collapse_ws(element.text):
            return collapse_ws(element.text)
    for element in elements:
        if element.kind == "heading" and collapse_ws(element.text):
            return collapse_ws(element.text)
    return ""


def _title_from_url(url: str) -> str:
    parsed = urlparse(url)
    name = Path(parsed.path or "").stem
    if collapse_ws(name):
        return collapse_ws(name.replace("-", " ").replace("_", " "))
    return collapse_ws(parsed.netloc) or "Learned URL"


def _first_markdown_heading(markdown_text: str) -> str:
    for line in str(markdown_text or "").splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return collapse_ws(stripped.lstrip("#").strip())
    return ""


def _non_html_markdown_text(text: str, *, fallback_url: str) -> str:
    stripped = str(text or "").strip()
    if not stripped:
        return f"# {_title_from_url(fallback_url)}\n\nSource URL: {fallback_url}\n"
    if stripped.lstrip().startswith("#"):
        return stripped + ("\n" if not stripped.endswith("\n") else "")
    return f"# {_title_from_url(fallback_url)}\n\n{stripped}\n"


def _download_image_assets(
    *,
    page_url: str,
    elements: list[_CapturedElement],
    bundle_files: dict[str, bytes | str],
    max_assets: int,
    timeout_seconds: float,
) -> list[dict[str, Any]]:
    manifest: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    downloaded = 0
    for element in elements:
        if element.kind != "image":
            continue
        asset_url = urljoin(page_url, element.src)
        if not collapse_ws(asset_url) or asset_url in seen_urls:
            continue
        seen_urls.add(asset_url)
        entry: dict[str, Any] = {
            "asset_url": asset_url,
            "alt_text": collapse_ws(element.alt),
            "status": "skipped",
        }
        if downloaded >= max_assets:
            entry["reason"] = "max_assets_reached"
            manifest.append(entry)
            continue
        try:
            payload = _fetch_binary_asset(asset_url, timeout_seconds=timeout_seconds)
        except Exception as exc:
            entry["reason"] = collapse_ws(str(exc)) or "fetch_failed"
            manifest.append(entry)
            continue
        extension = _asset_extension(asset_url, payload.media_type)
        local_relpath = f"assets/image-{downloaded + 1:03d}{extension}"
        bundle_files[local_relpath] = payload.body
        entry.update(
            {
                "status": "downloaded",
                "local_relpath": local_relpath,
                "media_type": payload.media_type,
                "content_hash": hashlib.sha256(payload.body).hexdigest(),
                "size_bytes": len(payload.body),
            }
        )
        manifest.append(entry)
        downloaded += 1
    return manifest


def _fetch_binary_asset(url: str, *, timeout_seconds: float) -> _ResponsePayload:
    request = Request(url, headers={"User-Agent": _DEFAULT_USER_AGENT})
    try:
        with urlopen(request, timeout=float(timeout_seconds)) as response:
            body = response.read(_MAX_ASSET_BYTES + 1)
            if len(body) > _MAX_ASSET_BYTES:
                raise ValueError("asset exceeded max size")
            headers = getattr(response, "headers", None) or response.info()
            return _ResponsePayload(
                url=str(getattr(response, "geturl", lambda: url)()),
                status_code=int(getattr(response, "status", getattr(response, "code", 200)) or 200),
                media_type=_response_media_type(headers),
                charset=_response_charset(headers),
                body=body,
                headers=_response_headers_map(headers),
            )
    except Exception as exc:
        raise ValueError(f"asset fetch failed: {collapse_ws(str(exc)) or url}") from exc


def _asset_extension(asset_url: str, media_type: str) -> str:
    suffix = Path(urlparse(asset_url).path).suffix
    if suffix:
        return suffix
    guessed = mimetypes.guess_extension(media_type or "")
    if guessed:
        return guessed
    return ".bin"
