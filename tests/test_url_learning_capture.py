# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import os
from email.message import Message
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from learning_context import learning_source_bundle_root, load_learning_source
from main import BSSCController, SystemState
from url_learning_capture import capture_url_learning_bundle


class _FakeUrlResponse:
    def __init__(self, *, url: str, media_type: str, body: bytes, status: int = 200) -> None:
        self._url = url
        self._body = body
        self.status = status
        self.headers = Message()
        self.headers["Content-Type"] = media_type

    def read(self, size: int = -1) -> bytes:
        if size is None or size < 0:
            return self._body
        return self._body[:size]

    def info(self) -> Message:
        return self.headers

    def geturl(self) -> str:
        return self._url

    def __enter__(self) -> _FakeUrlResponse:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        del exc_type, exc, tb
        return None


class _FakePlaywrightResponse:
    def __init__(self, *, status: int = 200, headers: dict[str, str] | None = None) -> None:
        self.status = status
        self._headers = dict(headers or {"content-type": "text/html; charset=utf-8"})

    def all_headers(self) -> dict[str, str]:
        return dict(self._headers)


class _FakePlaywrightPage:
    def __init__(
        self,
        *,
        final_url: str,
        html_text: str,
        title: str,
        screenshot_png: bytes,
        response: _FakePlaywrightResponse,
    ) -> None:
        self.url = final_url
        self._html_text = html_text
        self._title = title
        self._screenshot_png = screenshot_png
        self._response = response
        self.goto_calls: list[dict[str, object]] = []
        self.wait_calls: list[dict[str, object]] = []

    def goto(self, url: str, *, wait_until: str, timeout: int):
        self.goto_calls.append({"url": url, "wait_until": wait_until, "timeout": timeout})
        return self._response

    def wait_for_load_state(self, state: str, *, timeout: int) -> None:
        self.wait_calls.append({"state": state, "timeout": timeout})

    def content(self) -> str:
        return self._html_text

    def screenshot(self, *, type: str, full_page: bool) -> bytes:
        if type != "png" or not full_page:
            raise AssertionError("unexpected screenshot options")
        return self._screenshot_png

    def title(self) -> str:
        return self._title


class _FakePlaywrightBrowser:
    def __init__(self, page: _FakePlaywrightPage) -> None:
        self._page = page
        self.new_page_calls: list[dict[str, object]] = []
        self.closed = False

    def new_page(self, **kwargs):
        self.new_page_calls.append(dict(kwargs))
        return self._page

    def close(self) -> None:
        self.closed = True


class _FakePlaywrightChromium:
    def __init__(self, browser: _FakePlaywrightBrowser) -> None:
        self._browser = browser
        self.launch_calls: list[dict[str, object]] = []

    def launch(self, *, headless: bool):
        self.launch_calls.append({"headless": headless})
        return self._browser


class _FakePlaywrightContextManager:
    def __init__(self, browser: _FakePlaywrightBrowser) -> None:
        self._chromium = _FakePlaywrightChromium(browser)

    def __enter__(self):
        return SimpleNamespace(chromium=self._chromium)

    def __exit__(self, exc_type, exc, tb) -> None:
        del exc_type, exc, tb
        return None


class UrlLearningCaptureTests(unittest.TestCase):
    def test_capture_url_learning_bundle_extracts_markdown_and_assets_from_html(self) -> None:
        page_url = "https://example.test/article"
        image_url = "https://example.test/assets/figure.png"
        html = """
        <html>
          <head><title>Example Article</title></head>
          <body>
            <article>
              <h1>Example Article</h1>
              <p>First paragraph.</p>
              <h2>Key Points</h2>
              <ul><li>One</li><li>Two</li></ul>
              <img src="/assets/figure.png" alt="Figure one" />
            </article>
          </body>
        </html>
        """.strip().encode("utf-8")

        def _fake_urlopen(request, timeout=0):
            del timeout
            request_url = request.full_url if hasattr(request, "full_url") else str(request)
            if request_url == page_url:
                return _FakeUrlResponse(url=page_url, media_type="text/html; charset=utf-8", body=html)
            if request_url == image_url:
                return _FakeUrlResponse(url=image_url, media_type="image/png", body=b"\x89PNG\r\n")
            raise AssertionError(f"unexpected URL: {request_url}")

        with patch("url_learning_capture.sync_playwright", new=None), patch(
            "url_learning_capture.urlopen",
            side_effect=_fake_urlopen,
        ):
            capture = capture_url_learning_bundle(url=page_url, max_assets=2)

        self.assertEqual(capture.requested_url, page_url)
        self.assertEqual(capture.final_url, page_url)
        self.assertEqual(capture.title, "Example Article")
        self.assertIn("# Example Article", capture.markdown_text)
        self.assertIn("First paragraph.", capture.markdown_text)
        self.assertIn("- One", capture.markdown_text)
        self.assertIn("![Figure one](/assets/figure.png)", capture.markdown_text)
        self.assertIn("rendered.html", capture.bundle_files)
        self.assertIn("elements.json", capture.bundle_files)
        self.assertIn("asset-manifest.json", capture.bundle_files)
        self.assertIn("assets/image-001.png", capture.bundle_files)
        self.assertEqual(capture.metadata["capture_kind"], "raw_html")
        self.assertEqual(capture.metadata["asset_count"], 1)
        self.assertEqual(capture.report()["asset_count"], 1)

    def test_capture_url_learning_bundle_prefers_playwright_and_trafilatura_for_html(self) -> None:
        page_url = "https://example.test/article"
        final_url = "https://example.test/rendered-article"
        html_text = """
        <html>
          <head><title>Rendered Example</title></head>
          <body>
            <article>
              <h1>Rendered Example</h1>
              <p>Rendered paragraph.</p>
              <img src="/assets/figure.png" alt="Figure one" />
            </article>
          </body>
        </html>
        """.strip()
        page = _FakePlaywrightPage(
            final_url=final_url,
            html_text=html_text,
            title="Rendered Example",
            screenshot_png=b"\x89PNG-rendered",
            response=_FakePlaywrightResponse(),
        )
        browser = _FakePlaywrightBrowser(page)
        extract_mock = Mock(return_value="Rendered paragraph.")

        def _fake_asset_download(*, page_url, elements, bundle_files, max_assets, timeout_seconds):
            del page_url, elements, max_assets, timeout_seconds
            bundle_files["assets/image-001.png"] = b"\x89PNG-asset"
            return [
                {
                    "asset_url": "https://example.test/assets/figure.png",
                    "local_relpath": "assets/image-001.png",
                    "status": "downloaded",
                    "alt_text": "Figure one",
                }
            ]

        with patch(
            "url_learning_capture.sync_playwright",
            return_value=_FakePlaywrightContextManager(browser),
        ), patch(
            "url_learning_capture.trafilatura_extract",
            extract_mock,
        ), patch(
            "url_learning_capture._download_image_assets",
            side_effect=_fake_asset_download,
        ):
            capture = capture_url_learning_bundle(url=page_url, max_assets=2)

        self.assertEqual(capture.requested_url, page_url)
        self.assertEqual(capture.final_url, final_url)
        self.assertEqual(capture.title, "Rendered Example")
        self.assertTrue(capture.markdown_text.startswith("# Rendered Example\n\nRendered paragraph."))
        self.assertIn("rendered.html", capture.bundle_files)
        self.assertIn("screenshot.png", capture.bundle_files)
        self.assertIn("elements.json", capture.bundle_files)
        self.assertIn("asset-manifest.json", capture.bundle_files)
        self.assertIn("assets/image-001.png", capture.bundle_files)
        self.assertEqual(capture.metadata["fetch_method"], "playwright")
        self.assertEqual(capture.metadata["extract_method"], "trafilatura")
        self.assertEqual(capture.metadata["capture_kind"], "rendered_html")
        self.assertEqual(capture.metadata["screenshot_relpath"], "screenshot.png")
        self.assertEqual(capture.metadata["asset_count"], 1)
        extract_mock.assert_called_once()
        self.assertEqual(browser.new_page_calls[0]["viewport"]["width"], 1440)
        self.assertEqual(browser.new_page_calls[0]["viewport"]["height"], 2200)
        self.assertTrue(browser.closed)

    def test_capture_url_learning_bundle_falls_back_when_browser_capture_fails(self) -> None:
        page_url = "https://example.test/article"
        html = "<html><body><h1>Fallback Title</h1><p>Fallback paragraph.</p></body></html>".encode("utf-8")

        def _fake_urlopen(request, timeout=0):
            del timeout
            request_url = request.full_url if hasattr(request, "full_url") else str(request)
            if request_url != page_url:
                raise AssertionError(f"unexpected URL: {request_url}")
            return _FakeUrlResponse(url=page_url, media_type="text/html; charset=utf-8", body=html)

        with patch(
            "url_learning_capture._fetch_rendered_page_with_playwright",
            side_effect=ValueError("browser crashed"),
        ), patch("url_learning_capture.urlopen", side_effect=_fake_urlopen):
            capture = capture_url_learning_bundle(url=page_url, max_assets=1)

        self.assertEqual(capture.metadata["fetch_method"], "urllib_request")
        self.assertEqual(capture.metadata["extract_method"], "html_parser_fallback")
        self.assertEqual(capture.metadata["capture_warning"], "browser crashed")
        self.assertIn("# Fallback Title", capture.markdown_text)

    def test_controller_markdown_learning_can_persist_url_origin_source_bundle(self) -> None:
        controller = BSSCController(SystemState.bootstrap("learn from captured url"), llm_policy="off")
        with tempfile.TemporaryDirectory() as tempdir_text:
            root = Path(tempdir_text) / "root"
            root.mkdir(parents=True, exist_ok=True)
            markdown_path = Path(tempdir_text) / "source.md"
            markdown_path.write_text(
                "# Kinematics URL Demo\n\nVelocity is displacement per unit time.\n",
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"LEARNING_CONTEXT_ROOT": str(root)}, clear=False):
                report = controller.learn_from_markdown_document(
                    markdown_path,
                    max_artifacts=4,
                    source_bundle_override={
                        "source_kind": "url",
                        "source_ref": "https://example.test/article",
                        "media_type": "text/html",
                        "title": "Example Article",
                        "metadata": {
                            "requested_url": "https://example.test/article",
                            "final_url": "https://example.test/article",
                            "asset_count": 0,
                        },
                        "bundle_files": {
                            "rendered.html": "<html><body>Example Article</body></html>",
                            "elements.json": "[]",
                            "asset-manifest.json": "[]",
                        },
                    },
                )

            learning_context_report = report["learning_context"]
            self.assertEqual(learning_context_report["source_kind"], "url")
            subject_id = str(learning_context_report["subject_id"])
            source_id = str(learning_context_report["source_id"])
            source = load_learning_source(root, subject_id, source_id)
            self.assertEqual(source.source_kind, "url")
            self.assertEqual(source.source_ref, "https://example.test/article")
            bundle_root = learning_source_bundle_root(root, subject_id, source_id)
            self.assertTrue((bundle_root / "rendered.html").exists())
            self.assertTrue((bundle_root / "elements.json").exists())
            self.assertTrue((bundle_root / "asset-manifest.json").exists())
            self.assertEqual(
                source.metadata.get("bundle_root_relpath"),
                f"sources/{source_id}",
            )


if __name__ == "__main__":
    unittest.main()
