import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:integration_test/integration_test.dart';
import 'package:workstation_ui/main.dart' as app;

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets(
    'clean direct v10 upload reaches built publication with preview action',
    (tester) async {
      app.main();
      await tester.pumpAndSettle();

      final ProviderContainer container = ProviderScope.containerOf(
        tester.element(find.byType(app.WorkstationApp)),
        listen: false,
      );
      final app.WorkstationController controller = container.read(
        app.workstationControllerProvider.notifier,
      );
      final GoRouter router = container.read(app.workstationRouterProvider);

      await controller.loadRoots(_state(container).endpoint);
      await _pumpUntil(
        tester,
        () =>
            !_state(container).loadingRoots && _state(container).roots.isNotEmpty,
        failureMessage:
            'The workstation host did not advertise any served roots.',
      );

      final opened = await controller.openSelectedRoot();
      expect(opened, isTrue);
      await _pumpUntil(
        tester,
        () => _state(container).connected && !_state(container).openingRoot,
        failureMessage: 'The workstation root did not open successfully.',
      );

      await _settleSubjectTab(
        tester,
        router,
        container,
        tabKey: 'research',
        shellTitle: 'Current Step',
      );

      final markdown = await rootBundle.loadString(
        'assets/integration/city_bus_ticketing_modernization.md',
      );
      final nextTab = await controller.stageMarkdownUpload(
        'city_bus_ticketing_modernization.md',
        Uint8List.fromList(utf8.encode(markdown)),
      );

      await _pumpUntil(
        tester,
        () {
          final state = _state(container);
          return !state.subjectBusy &&
              !state.markdownIngressBusy &&
              state.selectedScenarioKey.isNotEmpty &&
              state.subjectSnapshot != null;
        },
        timeout: const Duration(seconds: 120),
        failureMessage:
            'Markdown import did not settle into a renderable subject snapshot.',
      );

      if (nextTab != null && nextTab.isNotEmpty) {
        router.go('/workstation/$nextTab');
        await tester.pumpAndSettle();
      }

      await _settleSubjectTab(
        tester,
        router,
        container,
        tabKey: 'research',
        shellTitle: 'Current Step',
      );

      await _applyActionAndNavigate(
        tester,
        router,
        controller,
        'open_context',
      );
      await _applyActionAndNavigate(
        tester,
        router,
        controller,
        'compare_projections',
      );
      await _applyActionAndNavigate(
        tester,
        router,
        controller,
        'generate_itemization',
      );
      await _applyActionAndNavigate(
        tester,
        router,
        controller,
        'suggest_transformation_constructs',
      );
      await _applyActionAndNavigate(
        tester,
        router,
        controller,
        'refresh_review_composition',
      );
      await _settleSubjectTab(
        tester,
        router,
        container,
        tabKey: 'draft',
        shellTitle: 'Current Step',
      );
      await _waitForAction(
        tester,
        'Start Decision Analysis',
        timeout: const Duration(seconds: 120),
      );
      await _applyActionAndNavigate(
        tester,
        router,
        controller,
        'create_decision_frame_from_selected_draft_item',
      );
      await _waitForAction(
        tester,
        'Run Decision Analysis',
        timeout: const Duration(seconds: 120),
      );
      await _applyActionAndNavigate(
        tester,
        router,
        controller,
        'analyze_decision_frame',
      );

      await _settleSubjectTab(
        tester,
        router,
        container,
        tabKey: 'review',
        shellTitle: 'Current Step',
      );
      await _waitForAction(
        tester,
        'Approve For Report',
        timeout: const Duration(seconds: 120),
      );
      await _applyActionAndNavigate(
        tester,
        router,
        controller,
        'approve_review',
      );

      await _settleSubjectTab(
        tester,
        router,
        container,
        tabKey: 'publication',
        shellTitle: 'Current Step',
      );
      await _waitForAction(
        tester,
        'Lock Report Inputs',
        timeout: const Duration(seconds: 120),
      );
      await _applyActionAndNavigate(
        tester,
        router,
        controller,
        'lock_publication',
      );
      await _waitForAction(
        tester,
        'Build Report',
        timeout: const Duration(seconds: 120),
      );
      await _applyActionAndNavigate(
        tester,
        router,
        controller,
        'build_report',
      );
      await _pumpUntil(
        tester,
        () =>
            _enabledOutlinedButtonFinder('Preview report.pdf')
                .evaluate()
                .isNotEmpty &&
            _enabledOutlinedButtonFinder('Build Report').evaluate().isEmpty,
        timeout: const Duration(seconds: 180),
        failureMessage:
            'The clean direct v10 flow did not reach the built publication preview state.',
      );
    },
  );
}

app.WorkstationState _state(ProviderContainer container) {
  return container.read(app.workstationControllerProvider);
}

Future<void> _applyActionAndNavigate(
  WidgetTester tester,
  GoRouter router,
  app.WorkstationController controller,
  String actionKey,
) async {
  final nextTab = await controller.applyAction(actionKey);
  if (nextTab != null && nextTab.isNotEmpty) {
    router.go('/workstation/$nextTab');
    await controller.showTab(nextTab);
  }
  await tester.pumpAndSettle();
}

Future<void> _settleSubjectTab(
  WidgetTester tester,
  GoRouter router,
  ProviderContainer container, {
  required String tabKey,
  required String shellTitle,
}) async {
  router.go('/workstation/$tabKey');
  await _pumpUntil(
    tester,
    () {
      final state = _state(container);
      if (state.currentTabKey != tabKey ||
          state.subjectBusy ||
          state.subjectSnapshot == null) {
        return false;
      }
      return find.textContaining(shellTitle).evaluate().isNotEmpty;
    },
    failureMessage:
        'The $tabKey tab did not settle into the expected shell state.',
  );
}

Finder _enabledOutlinedButtonFinder(String label) {
  return find.byWidgetPredicate((widget) {
    if (widget is! OutlinedButton || widget.onPressed == null) {
      return false;
    }
    final child = widget.child;
    if (child is Text) {
      final data = child.data ?? child.textSpan?.toPlainText() ?? '';
      return data == label;
    }
    return false;
  }, description: 'enabled outlined button "$label"');
}

Future<void> _waitForAction(
  WidgetTester tester,
  String label, {
  Duration timeout = const Duration(seconds: 60),
}) async {
  await _pumpUntil(
    tester,
    () => _enabledOutlinedButtonFinder(label).evaluate().isNotEmpty,
    timeout: timeout,
    failureMessage: 'The workflow did not expose "$label".',
  );
}

Future<void> _pumpUntil(
  WidgetTester tester,
  bool Function() predicate, {
  Duration timeout = const Duration(seconds: 60),
  Duration step = const Duration(milliseconds: 100),
  required String failureMessage,
}) async {
  final deadline = DateTime.now().add(timeout);
  while (DateTime.now().isBefore(deadline)) {
    await tester.pump(step);
    if (predicate()) {
      await tester.pumpAndSettle();
      return;
    }
  }
  fail(failureMessage);
}
