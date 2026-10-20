# Workstation Flutter UI

Material 3 workstation client for the shared workstation gRPC/proto surface.

This app consumes:
- `WorkstationBootstrapService` to discover served workstation roots
- `WorkstationShellService` for chat, activity, permissions, and skills
- `SubjectWorkflowService` for Gather, Itemize, Draft, Review, and Publication
- `WorkstationAssetService` for markdown upload staging and artifact resolution

The app does not import Textual Python helpers. Its desktop subject shell is rendered through Flutter-side `src/textual/...` modules that consume generated gRPC/protobuf clients plus the shared Textual-derived layout artifact at `assets/workstation_layout.json`.

## Prerequisites

- `uv`
- Flutter SDK on your `PATH`
- Envoy on your `PATH` for web runs

## Regenerate protobuf and gRPC clients

From the repository root:

```bash
uv run python scripts/generate_workstation_protos.py
```

This refreshes:
- Python gRPC/protobuf outputs under `workstation/grpc_definitions/src/workstation/grpc/definitions`
- Dart gRPC/protobuf outputs under `workstation/ui_flutter/lib/src/generated`

## Start the native gRPC workstation host

Create a workstation directory:

```bash
mkdir -p /tmp/workstation-root
rm -rf /tmp/workstation-root
```

From the repository root:

```bash
PROJECT_HOME=/Users/ravindranathakila/service/realized/
cd $PROJECT_HOME && \
  uv run python controller_entrypoints.py workstation-grpc-host \
  --serve-root /tmp/workstation-root \
  --default-root /tmp/workstation-root \
  --host 127.0.0.1 \
  --port 50051 \
  --asset-host 127.0.0.1 \
  --asset-port 8090 \
  --asset-base-url http://127.0.0.1:8090 \
  --allow-local-path-open
```

Notes:
- Repeat `--serve-root` to advertise more than one workstation root.
- `--asset-base-url` is what the backend returns inside `ArtifactRef.download_url`.
- `--allow-local-path-open` is useful for same-machine desktop runs, where `ArtifactRef.can_open_locally=true` can still open local files directly.
- If one advertised root does not already contain workstation session files, the host will initialize it on first open so the Flutter bootstrap flow can proceed without a separate `workstation-launch` step.

## Start the gRPC-Web bridge for Flutter web

From the repository root:

```bash
PROJECT_HOME=/Users/ravindranathakila/service/realized/
cd $PROJECT_HOME && (killall -9 envoy || true) && envoy -c workstation/ui_flutter/envoy/workstation_grpc_web.yaml
```

Default ports in the committed Envoy config:
- gRPC-Web listener: `http://127.0.0.1:8080`
- Envoy admin: `http://127.0.0.1:9901`
- Upstream native gRPC backend: `127.0.0.1:50051`

If you change the gRPC host port, update `workstation/ui_flutter/envoy/workstation_grpc_web.yaml` to match.

## Install Flutter dependencies

From `workstation/ui_flutter`:

```bash
flutter pub get
```
## Run in Chrome

From `workstation/ui_flutter`:

```bash
flutter run -d chrome \
  --dart-define=WORKSTATION_GRPC_HOST=127.0.0.1 \
  --dart-define=WORKSTATION_GRPC_PORT=50051 \
  --dart-define=WORKSTATION_GRPCWEB_URL=http://127.0.0.1:8080
```

For web, the app ignores the native TCP host/port at runtime and uses `WORKSTATION_GRPCWEB_URL` through `GrpcWebClientChannel`.

## Run on native desktop or mobile

From `workstation/ui_flutter`:

```bash
flutter run \
  --dart-define=WORKSTATION_GRPC_HOST=127.0.0.1 \
  --dart-define=WORKSTATION_GRPC_PORT=50051 \
  --dart-define=WORKSTATION_GRPCWEB_URL=http://127.0.0.1:8080
```

For native platforms, the app uses `WORKSTATION_GRPC_HOST` and `WORKSTATION_GRPC_PORT`.
`WORKSTATION_GRPCWEB_URL` is still accepted so the same build contract can be reused across targets, but native runs use direct gRPC over TCP.


## Test

From `workstation/ui_flutter`:

```bash
flutter analyze
flutter test
```

## Capture named post-import web screenshots

This project now includes a real `integration_test` harness for Flutter web
running through `flutter drive` and ChromeDriver. It imports a deterministic
markdown fixture through the real workstation gRPC workflow, then captures named
screenshots for the full desktop Textual-parity shell states after import:

- `01-gather-main.png`
- `02-gather-source-detail.png`
- `03-gather-journal.png`
- `04-itemize-main.png`
- `05-draft-compose.png`
- `06-draft-frame.png`
- `07-draft-model.png`
- `08-draft-explore.png`
- `09-review-main.png`
- `10-review-journal.png`
- `11-publication-main.png`

The simplest repeatable path is:

```bash
cd workstation/ui_flutter
./scripts/run_subject_tab_screenshot_test.sh
```

That script will:
- start an isolated workstation gRPC host on `127.0.0.1:50061`
- start an isolated Envoy grpc-web bridge on `127.0.0.1:8081`
- start ChromeDriver on `127.0.0.1:4444`
- run `flutter drive -d web-server` against
  `integration_test/subject_tabs_screenshot_test.dart`
- write screenshots to `workstation/ui_flutter/build/integration_test_screenshots/`

If `chromedriver` is not already installed on the machine, the wrapper script
will download a matching Chrome-for-Testing driver into
`workstation/ui_flutter/build/tools/chromedriver/` and reuse it on later runs.

Useful environment overrides:

```bash
WORKSTATION_SCREENSHOT_ROOT=/tmp/my-root
WORKSTATION_SCREENSHOT_BROWSER_DIMENSION=1680x1100
WORKSTATION_SCREENSHOT_GRPC_PORT=50061
WORKSTATION_SCREENSHOT_GRPCWEB_PORT=8081
WORKSTATION_SCREENSHOT_ASSET_PORT=8091
WORKSTATION_SCREENSHOT_ENVOY_ADMIN_PORT=9902
WORKSTATION_SCREENSHOT_WEBDRIVER_PORT=4444
```

If you want to run the pieces manually instead of using the wrapper script:

```bash
cd workstation/ui_flutter
flutter pub get
chromedriver --port 4444
flutter drive \
  --driver=test_driver/integration_test.dart \
  --target=integration_test/subject_tabs_screenshot_test.dart \
  --driver-port=4444 \
  --browser-name=chrome \
  --browser-dimension=1680x1100 \
  --dart-define=WORKSTATION_GRPC_HOST=127.0.0.1 \
  --dart-define=WORKSTATION_GRPC_PORT=50061 \
  --dart-define=WORKSTATION_GRPCWEB_URL=http://127.0.0.1:8081 \
  --timeout=240 \
  -d web-server
```

From the repository root, run the Python-side contract tests that cover the new bootstrap and asset surface:

```bash
uv run python -m unittest -v \
  workstation.tests.test_workstation_proto_documentation \
  workstation.tests.test_workstation_layout \
  workstation.tests.test_workstation_bootstrap_assets
```
