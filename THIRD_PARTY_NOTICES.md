# Third-Party And Generated Material

Realization's project source is licensed under Apache License 2.0 as described
in `LICENSE`. The following included material has an upstream or tool-generated
origin that should not be obscured by the project license.

## Flutter Project Scaffold

`workstation/ui_flutter/` contains platform scaffold, generated plugin
registrants, and default launcher or launch assets created by Flutter tooling.
The generating Flutter revision is recorded in
`workstation/ui_flutter/.metadata` as
`2c9eb20739dfec95e2c74bd3dfa4601b0a8a36aa`. Flutter is distributed under the
BSD 3-Clause License. Project-specific modifications remain covered by the
project license to the extent applicable.

Upstream: <https://github.com/flutter/flutter>

## Protocol Buffer And gRPC Generation

Files matching
`workstation/grpc_definitions/src/workstation/grpc/definitions/*_pb2.py` and
`*_pb2_grpc.py` are generated from the adjacent project-owned `.proto` files.
The checked-in headers identify Protocol Buffers Python generator version
6.31.1. Protocol Buffers is BSD-3-Clause licensed and gRPC is Apache-2.0
licensed. These notices describe the generating tools; the interface
definitions themselves are Realization project material.

Upstream: <https://github.com/protocolbuffers/protobuf> and
<https://github.com/grpc/grpc>

## Gradle Wrapper Binary

The working repository contains
`workstation/ui_flutter/android/gradle/wrapper/gradle-wrapper.jar`, but the
initial staged source release excludes it. Its embedded implementation version
does not match the distribution configured by `gradle-wrapper.properties`, so
its exact provenance has not been established. Gradle is Apache-2.0 licensed;
the wrapper should be regenerated from a verified Gradle distribution before
it is redistributed.

Upstream: <https://github.com/gradle/gradle>

## Resolved Dependencies

`uv.lock`, `workstation/ui_flutter/pubspec.lock`, and `.terraform.lock.hcl`
describe externally resolved dependencies and integrity data. They do not
vendor those dependencies or replace their licenses. Anyone distributing a
binary, container, application bundle, optional WASM runtime, or platform
package must produce notices for the exact resolved artifacts in that binary.
