import 'package:grpc/grpc_web.dart' as grpc_web;
import 'package:grpc/service_api.dart' as grpc_service;

grpc_service.ClientChannel createWorkstationGrpcChannel({
  required String grpcHost,
  required int grpcPort,
  required String grpcWebUrl,
}) {
  return grpc_web.GrpcWebClientChannel.xhr(Uri.parse(grpcWebUrl));
}
