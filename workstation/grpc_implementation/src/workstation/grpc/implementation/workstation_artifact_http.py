# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import mimetypes
import shutil
import tempfile
import threading
from urllib.parse import urlparse


class WorkstationArtifactDownloadRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._token_to_path: dict[str, Path] = {}
        self._path_to_token: dict[str, str] = {}

    def register(self, path: Path) -> str:
        resolved = Path(path).expanduser().resolve()
        path_key = str(resolved)
        with self._lock:
            token = self._path_to_token.get(path_key)
            if token:
                self._token_to_path[token] = resolved
                return token
            token = f"artifact-{abs(hash(path_key)) & 0xFFFFFFFFFFFFFFFF:016x}"
            self._path_to_token[path_key] = token
            self._token_to_path[token] = resolved
            return token

    def resolve(self, token: str) -> Path | None:
        with self._lock:
            return self._token_to_path.get(str(token or ""))


@dataclass
class WorkstationArtifactHttpServerHandle:
    server: ThreadingHTTPServer
    thread: threading.Thread
    registry: WorkstationArtifactDownloadRegistry
    base_url: str

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


def start_workstation_artifact_http_server(
    *,
    host: str = "127.0.0.1",
    port: int = 8787,
    registry: WorkstationArtifactDownloadRegistry | None = None,
) -> WorkstationArtifactHttpServerHandle:
    download_registry = registry or WorkstationArtifactDownloadRegistry()

    class _ArtifactRequestHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            path_parts = [segment for segment in parsed.path.split("/") if segment]
            if len(path_parts) < 2 or path_parts[0] != "artifacts":
                self.send_error(404, "Unknown artifact path.")
                return
            artifact_path = download_registry.resolve(path_parts[1])
            if artifact_path is None or not artifact_path.exists():
                self.send_error(404, "Artifact not found.")
                return
            if artifact_path.is_dir():
                with tempfile.TemporaryDirectory(prefix="workstation-artifact-") as tempdir:
                    archive_base = Path(tempdir) / artifact_path.name
                    archive_path = Path(shutil.make_archive(str(archive_base), "zip", root_dir=artifact_path))
                    self._send_file(archive_path, download_name=f"{artifact_path.name}.zip", mime_type="application/zip")
                return
            mime_type, _ = mimetypes.guess_type(str(artifact_path))
            self._send_file(
                artifact_path,
                download_name=artifact_path.name,
                mime_type=mime_type or "application/octet-stream",
            )

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            del format
            del args

        def _send_file(self, path: Path, *, download_name: str, mime_type: str) -> None:
            payload = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Content-Disposition", f'inline; filename="{download_name}"')
            self.end_headers()
            self.wfile.write(payload)

    server = ThreadingHTTPServer((host, int(port)), _ArtifactRequestHandler)
    actual_host, actual_port = server.server_address[:2]
    base_url = f"http://{actual_host}:{actual_port}"
    thread = threading.Thread(target=server.serve_forever, name="workstation-artifact-http", daemon=True)
    thread.start()
    return WorkstationArtifactHttpServerHandle(
        server=server,
        thread=thread,
        registry=download_registry,
        base_url=base_url,
    )
