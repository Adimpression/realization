import 'package:grpc/grpc.dart' as grpc;
import 'package:grpc/service_api.dart' as grpc_service;

grpc_service.ClientChannel createWorkstationGrpcChannel({
  required String grpcHost,
  required int grpcPort,
  required String grpcWebUrl,
}) {
  return grpc.ClientChannel(
    grpcHost,
    port: grpcPort,
    options: const grpc.ChannelOptions(
      credentials: grpc.ChannelCredentials.insecure(),
    ),
  );
}
