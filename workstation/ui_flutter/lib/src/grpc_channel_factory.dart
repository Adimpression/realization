import 'package:grpc/service_api.dart' as grpc_service;

import 'grpc_channel_factory_io.dart'
    if (dart.library.js_interop) 'grpc_channel_factory_web.dart' as impl;

grpc_service.ClientChannel createWorkstationGrpcChannel({
  required String grpcHost,
  required int grpcPort,
  required String grpcWebUrl,
}) {
  return impl.createWorkstationGrpcChannel(
    grpcHost: grpcHost,
    grpcPort: grpcPort,
    grpcWebUrl: grpcWebUrl,
  );
}
