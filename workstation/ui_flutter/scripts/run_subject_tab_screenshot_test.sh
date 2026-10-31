#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UI_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${UI_DIR}/../.." && pwd)"

WORK_ROOT="${WORKSTATION_SCREENSHOT_ROOT:-/tmp/workstation-ui-screenshots-root}"
GRPC_HOST="${WORKSTATION_SCREENSHOT_GRPC_HOST:-127.0.0.1}"
GRPC_PORT="${WORKSTATION_SCREENSHOT_GRPC_PORT:-50061}"
GRPCWEB_PORT="${WORKSTATION_SCREENSHOT_GRPCWEB_PORT:-8081}"
ASSET_PORT="${WORKSTATION_SCREENSHOT_ASSET_PORT:-8091}"
ENVOY_ADMIN_PORT="${WORKSTATION_SCREENSHOT_ENVOY_ADMIN_PORT:-9902}"
WEBDRIVER_PORT="${WORKSTATION_SCREENSHOT_WEBDRIVER_PORT:-4444}"
BROWSER_DIMENSION="${WORKSTATION_SCREENSHOT_BROWSER_DIMENSION:-1680x1100}"
CHROME_BINARY="${WORKSTATION_SCREENSHOT_CHROME_BINARY:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"

BUILD_DIR="${UI_DIR}/build"
SCREENSHOT_DIR="${UI_DIR}/build/integration_test_screenshots"
LOG_DIR="${UI_DIR}/build/integration_test_logs"
ENVOY_CONFIG_PATH="${LOG_DIR}/workstation_grpc_web.integration.yaml"
INTEGRATION_TARGET="${WORKSTATION_INTEGRATION_TARGET:-integration_test/subject_tabs_screenshot_test.dart}"

mkdir -p "${SCREENSHOT_DIR}" "${LOG_DIR}"
rm -rf "${WORK_ROOT}" "${SCREENSHOT_DIR}"
mkdir -p "${SCREENSHOT_DIR}"

cleanup() {
  if [[ -n "${CHROMEDRIVER_PID:-}" ]]; then
    kill "${CHROMEDRIVER_PID}" >/dev/null 2>&1 || true
  fi
  if [[ -n "${ENVOY_PID:-}" ]]; then
    kill "${ENVOY_PID}" >/dev/null 2>&1 || true
  fi
  if [[ -n "${HOST_PID:-}" ]]; then
    kill "${HOST_PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

wait_for_port() {
  local host="$1"
  local port="$2"
  local label="$3"
  python3 - "$host" "$port" "$label" <<'PY'
import socket
import sys
import time

host = sys.argv[1]
port = int(sys.argv[2])
label = sys.argv[3]
deadline = time.time() + 30
last_error = None

while time.time() < deadline:
    sock = socket.socket()
    sock.settimeout(0.5)
    try:
        sock.connect((host, port))
        sock.close()
        sys.exit(0)
    except OSError as exc:
        last_error = exc
        time.sleep(0.2)

raise SystemExit(f"{label} did not become ready on {host}:{port}: {last_error}")
PY
}

resolve_chromedriver() {
  if [[ -n "${WORKSTATION_SCREENSHOT_CHROMEDRIVER_BINARY:-}" ]]; then
    echo "${WORKSTATION_SCREENSHOT_CHROMEDRIVER_BINARY}"
    return
  fi

  if command -v chromedriver >/dev/null 2>&1; then
    command -v chromedriver
    return
  fi

  if [[ ! -x "${CHROME_BINARY}" ]]; then
    echo "Chrome binary not found at ${CHROME_BINARY}, and chromedriver is not installed." >&2
    return 1
  fi

  local chrome_version
  chrome_version="$("${CHROME_BINARY}" --version | awk '{print $3}')"
  if [[ -z "${chrome_version}" ]]; then
    echo "Unable to determine the local Chrome version from ${CHROME_BINARY}." >&2
    return 1
  fi

  local platform
  case "$(uname -s)-$(uname -m)" in
    Darwin-arm64) platform="mac-arm64" ;;
    Darwin-x86_64) platform="mac-x64" ;;
    Linux-x86_64) platform="linux64" ;;
    *)
      echo "Unsupported platform for automatic chromedriver provisioning: $(uname -s)-$(uname -m)" >&2
      return 1
      ;;
  esac

  local cache_root="${BUILD_DIR}/tools/chromedriver/${platform}"
  mkdir -p "${cache_root}"

  local version_candidate="${chrome_version}"
  local archive_path
  local extract_dir
  local binary_path
  local download_url

  archive_path="${cache_root}/chromedriver-${version_candidate}.zip"
  extract_dir="${cache_root}/${version_candidate}"
  binary_path="${extract_dir}/chromedriver-${platform}/chromedriver"
  download_url="https://storage.googleapis.com/chrome-for-testing-public/${version_candidate}/${platform}/chromedriver-${platform}.zip"

  if [[ ! -x "${binary_path}" ]]; then
    if ! curl -fsSL "${download_url}" -o "${archive_path}"; then
      local version_prefix="${chrome_version%.*}"
      version_candidate="$(curl -fsSL "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${version_prefix}")"
      archive_path="${cache_root}/chromedriver-${version_candidate}.zip"
      extract_dir="${cache_root}/${version_candidate}"
      binary_path="${extract_dir}/chromedriver-${platform}/chromedriver"
      download_url="https://storage.googleapis.com/chrome-for-testing-public/${version_candidate}/${platform}/chromedriver-${platform}.zip"
      if [[ ! -x "${binary_path}" ]]; then
        curl -fsSL "${download_url}" -o "${archive_path}"
      fi
    fi

    if [[ ! -x "${binary_path}" ]]; then
      rm -rf "${extract_dir}"
      python3 - "${archive_path}" "${extract_dir}" <<'PY'
import pathlib
import sys
import zipfile

archive = pathlib.Path(sys.argv[1])
target = pathlib.Path(sys.argv[2])
target.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(archive) as zf:
    zf.extractall(target)
PY
      chmod +x "${binary_path}"
    fi
  fi

  echo "${binary_path}"
}

cat >"${ENVOY_CONFIG_PATH}" <<EOF
static_resources:
  listeners:
    - name: workstation_grpc_web_listener
      address:
        socket_address:
          address: 0.0.0.0
          port_value: ${GRPCWEB_PORT}
      filter_chains:
        - filters:
            - name: envoy.filters.network.http_connection_manager
              typed_config:
                "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
                codec_type: AUTO
                stat_prefix: workstation_grpc_web
                route_config:
                  name: workstation_grpc_web_routes
                  virtual_hosts:
                    - name: workstation_grpc_backend
                      domains: ["*"]
                      cors:
                        allow_origin_string_match:
                          - prefix: "http://localhost"
                          - prefix: "http://127.0.0.1"
                        allow_methods: "GET, POST, OPTIONS"
                        allow_headers: "x-user-agent,keep-alive,user-agent,cache-control,content-type,content-transfer-encoding,x-accept-content-transfer-encoding,x-accept-response-streaming,x-grpc-web,grpc-timeout"
                        expose_headers: "grpc-status,grpc-message,grpc-status-details-bin"
                        max_age: "86400"
                      routes:
                        - match:
                            prefix: "/"
                          route:
                            cluster: workstation_grpc
                            max_stream_duration:
                              grpc_timeout_header_max: 0s
                http_filters:
                  - name: envoy.filters.http.grpc_web
                    typed_config:
                      "@type": type.googleapis.com/envoy.extensions.filters.http.grpc_web.v3.GrpcWeb
                  - name: envoy.filters.http.cors
                    typed_config:
                      "@type": type.googleapis.com/envoy.extensions.filters.http.cors.v3.Cors
                  - name: envoy.filters.http.router
                    typed_config:
                      "@type": type.googleapis.com/envoy.extensions.filters.http.router.v3.Router

  clusters:
    - name: workstation_grpc
      connect_timeout: 5s
      type: LOGICAL_DNS
      http2_protocol_options: {}
      load_assignment:
        cluster_name: workstation_grpc
        endpoints:
          - lb_endpoints:
              - endpoint:
                  address:
                    socket_address:
                      address: ${GRPC_HOST}
                      port_value: ${GRPC_PORT}

admin:
  access_log_path: ${LOG_DIR}/envoy-admin.log
  address:
    socket_address:
      address: 127.0.0.1
      port_value: ${ENVOY_ADMIN_PORT}
EOF

(
  cd "${REPO_ROOT}"
  uv run realized-workstation grpc-host \
    --serve-root "${WORK_ROOT}" \
    --default-root "${WORK_ROOT}" \
    --host "${GRPC_HOST}" \
    --port "${GRPC_PORT}" \
    --asset-host "${GRPC_HOST}" \
    --asset-port "${ASSET_PORT}" \
    --asset-base-url "http://${GRPC_HOST}:${ASSET_PORT}" \
    --allow-local-path-open \
    >"${LOG_DIR}/grpc-host.log" 2>&1
) &
HOST_PID=$!
wait_for_port "${GRPC_HOST}" "${GRPC_PORT}" "workstation gRPC host"

envoy -c "${ENVOY_CONFIG_PATH}" >"${LOG_DIR}/envoy.log" 2>&1 &
ENVOY_PID=$!
wait_for_port "${GRPC_HOST}" "${GRPCWEB_PORT}" "Envoy grpc-web bridge"

CHROMEDRIVER_BINARY="$(resolve_chromedriver)"
"${CHROMEDRIVER_BINARY}" --port="${WEBDRIVER_PORT}" >"${LOG_DIR}/chromedriver.log" 2>&1 &
CHROMEDRIVER_PID=$!
wait_for_port "${GRPC_HOST}" "${WEBDRIVER_PORT}" "chromedriver"

(
  cd "${UI_DIR}"
  flutter pub get
  WORKSTATION_SCREENSHOT_OUTPUT_DIR="${SCREENSHOT_DIR}" \
    flutter drive \
      --driver=test_driver/integration_test.dart \
      --target="${INTEGRATION_TARGET}" \
      --driver-port="${WEBDRIVER_PORT}" \
      --browser-name=chrome \
      --browser-dimension="${BROWSER_DIMENSION}" \
      --dart-define=WORKSTATION_DISABLE_AUTO_OPEN_ARTIFACTS=true \
      --dart-define=WORKSTATION_GRPC_HOST="${GRPC_HOST}" \
      --dart-define=WORKSTATION_GRPC_PORT="${GRPC_PORT}" \
      --dart-define=WORKSTATION_GRPCWEB_URL="http://${GRPC_HOST}:${GRPCWEB_PORT}" \
      --timeout=240 \
      -d web-server
)

echo "Saved screenshots to ${SCREENSHOT_DIR}"
