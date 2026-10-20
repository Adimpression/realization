import 'dart:io';

import 'package:flutter_driver/flutter_driver.dart';
import 'package:integration_test/integration_test_driver_extended.dart';

Future<void> main() async {
  final FlutterDriver driver = await FlutterDriver.connect();
  await integrationDriver(
    driver: driver,
    onScreenshot:
        (
          String screenshotName,
          List<int> screenshotBytes, [
          Map<String, Object?>? args,
        ]) async {
          final Directory outputDirectory = Directory(
            Platform.environment['WORKSTATION_SCREENSHOT_OUTPUT_DIR'] ??
                'build/integration_test_screenshots',
          );
          await outputDirectory.create(recursive: true);
          final String safeName = screenshotName
              .replaceAll(RegExp(r'[^A-Za-z0-9._-]+'), '-')
              .replaceAll(RegExp(r'-+'), '-')
              .replaceAll(RegExp(r'^-|-$'), '');
          final File outputFile = File('${outputDirectory.path}/$safeName.png');
          await outputFile.writeAsBytes(screenshotBytes, flush: true);
          stdout.writeln('wrote screenshot: ${outputFile.path}');
          return true;
        },
    writeResponseOnFailure: true,
  );
}
