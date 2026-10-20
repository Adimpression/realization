import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:integration_test/integration_test.dart';
import 'package:workstation_ui/main.dart' as app;
import 'package:workstation_ui/src/generated/workstation/grpc/definitions/subject_workflow.pb.dart'
    as subject;

void main() {
  final binding = IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('captures named textual parity screenshots after a real markdown import', (
    tester,
  ) async {
    _logStep('boot app');
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

    _logStep('load roots');
    await controller.loadRoots(_state(container).endpoint);
    await _pumpUntil(
      tester,
      () =>
          !_state(container).loadingRoots && _state(container).roots.isNotEmpty,
      failureMessage:
          'The workstation host did not advertise any served roots.',
    );

    _logStep('open selected root');
    final bool opened = await controller.openSelectedRoot();
    expect(opened, isTrue);
    await _pumpUntil(
      tester,
      () => _state(container).connected && !_state(container).openingRoot,
      failureMessage: 'The workstation root did not open successfully.',
    );

    _logStep('settle gather main before import');
    await _settleSubjectTab(
      tester,
      router,
      container,
      tabKey: 'research',
      shellTitle: 'Source Sets',
    );

    _logStep('stage markdown upload');
    final String markdown = await rootBundle.loadString(
      'assets/integration/city_bus_ticketing_modernization.md',
    );
    final String? nextTab = await controller.stageMarkdownUpload(
      'city_bus_ticketing_modernization.md',
      Uint8List.fromList(utf8.encode(markdown)),
    );

    _logStep('wait for imported subject snapshot');
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

    final settledState = _state(container);
    expect(
      settledState.errorText,
      isNull,
      reason: 'The import flow reported an error: ${settledState.errorText}',
    );
    expect(
      settledState.selectedScenarioKey,
      isNotEmpty,
      reason: 'The import flow did not select a subject scenario.',
    );

    if (nextTab != null && nextTab.isNotEmpty) {
      _logStep('route to backend-guided next tab: $nextTab');
      router.go('/workstation/$nextTab');
      await tester.pumpAndSettle();
    }

    _logStep('settle gather main after import');
    await _settleSubjectTab(
      tester,
      router,
      container,
      tabKey: 'research',
      shellTitle: 'Source Sets',
    );
    _logStep('capture gather main');
    await _capture(
      tester,
      binding,
      '01-gather-main',
      requiredTitles: const <String>[
        'Current Step',
        'Subject Status',
        'Source Sets',
        'Learned Snapshot',
      ],
    );

    _logStep('open gather source detail');
    await tester.tap(find.byKey(const ValueKey<String>('pane-icon:+')).at(0));
    await _pumpUntil(
      tester,
      () => find.textContaining('Source Detail').evaluate().isNotEmpty,
      failureMessage: 'The gather source detail shell did not open.',
    );
    _logStep('capture gather source detail');
    await _capture(
      tester,
      binding,
      '02-gather-source-detail',
      requiredTitles: const <String>['Source Detail'],
    );

    _logStep('restore gather main from source detail');
    await tester.tap(find.byKey(const ValueKey<String>('pane-icon:-')).first);
    await _pumpUntil(
      tester,
      () => find.textContaining('Source Sets').evaluate().isNotEmpty,
      failureMessage: 'The gather main shell did not restore after collapse.',
    );
    _logStep('open gather journal');
    await tester.tap(find.byKey(const ValueKey<String>('pane-icon:+')).at(1));
    await _pumpUntil(
      tester,
      () => find.textContaining('Gather Journal').evaluate().isNotEmpty,
      failureMessage: 'The gather journal shell did not open.',
    );
    _logStep('capture gather journal');
    await _capture(
      tester,
      binding,
      '03-gather-journal',
      requiredTitles: const <String>['Gather Journal'],
    );

    _logStep('settle itemize main');
    try {
      await _settleSubjectTab(
        tester,
        router,
        container,
        tabKey: 'itemize',
        shellTitle: 'Current Step',
      );
    } catch (error) {
      _logSubjectSnapshotDiagnostics(container, phaseLabel: 'itemize-route');
      await binding.takeScreenshot('04-itemize-route-debug');
      rethrow;
    }
    _logStep('activate subject if needed');
    await _applyIfPresent(
      tester,
      router,
      container,
      labelContains: const <String>['Activate Subject'],
    );
    _logStep('restore itemize after activation');
    await _settleSubjectTab(
      tester,
      router,
      container,
      tabKey: 'itemize',
      shellTitle: 'Current Step',
    );
    _logStep('check maintained files if needed');
    await _applyIfPresent(
      tester,
      router,
      container,
      labelContains: const <String>[
        'Check Maintained Files',
        'Compare Maintained Files',
      ],
    );
    _logStep('restore itemize after maintained-files check');
    await _settleSubjectTab(
      tester,
      router,
      container,
      tabKey: 'itemize',
      shellTitle: 'Current Step',
    );
    _logStep('generate itemization if needed');
    await _applyIfPresent(
      tester,
      router,
      container,
      labelContains: const <String>[
        'Generate Itemization',
        'Refresh Itemization',
      ],
    );
    _logStep('restore itemize after itemization generation');
    await _settleSubjectTab(
      tester,
      router,
      container,
      tabKey: 'itemize',
      shellTitle: 'Current Step',
    );
    _logStep('suggest dst constructs if present');
    await _applyWorkflowActionsUntil(
      tester,
      router,
      container,
      tabKey: 'itemize',
      isReady: () => !_isVisibleActionButtonPresent(
        labels: const <String>['Suggest DST Constructs'],
      ),
      actionPriority: const <List<String>>[
        <String>['Suggest DST Constructs'],
      ],
      maxRounds: 1,
    );
    _logStep('restore itemize after action sequence');
    await _settleSubjectTab(
      tester,
      router,
      container,
      tabKey: 'itemize',
      shellTitle: 'Current Step',
    );
    _logStep('wait for itemize rich shell');
    try {
      await _pumpUntil(
        tester,
        () =>
            !_state(container).subjectBusy &&
            !_statusValueContains(
              container,
              label: 'Itemization',
              fragment: 'not generated yet',
            ) &&
            find.textContaining('Decision Role').evaluate().isNotEmpty &&
            find.textContaining('Item Inventory').evaluate().isNotEmpty,
        timeout: const Duration(seconds: 120),
        failureMessage:
            'The itemize tab did not reach the rich inventory shell state.',
      );
    } catch (error) {
      _logSubjectSnapshotDiagnostics(container, phaseLabel: 'itemize-debug');
      await binding.takeScreenshot('04-itemize-debug');
      rethrow;
    }
    _logStep('verify itemize row interaction updates item detail');
    await _tapInteractiveRowAndWaitForPaneChange(
      tester,
      container,
      paneKey: 'itemize_inventory',
      rowIndex: 1,
      detailPaneKey: 'itemize_detail',
      failureMessage:
          'Selecting a different itemize inventory row did not update Item Detail.',
    );
    _logStep('capture itemize main');
    await _capture(
      tester,
      binding,
      '04-itemize-main',
      requiredTitles: const <String>[
        'Current Step',
        'Itemize Status',
        'More Actions',
        'Decision Role',
        'Item Inventory',
        'Item Detail',
      ],
    );
    _logStep('suggest DST constructs if present');
    await _applyIfPresent(
      tester,
      router,
      container,
      labelContains: const <String>['Suggest DST Constructs'],
    );

    _logStep('settle draft compose');
    await _settleSubjectTab(
      tester,
      router,
      container,
      tabKey: 'draft',
      shellTitle: 'Current Step',
    );
    _logStep('activate draft subject if needed');
    await _applyWorkflowActionsUntil(
      tester,
      router,
      container,
      tabKey: 'draft',
      isReady: () => !_statusValueContains(
        container,
        label: 'Draft Composition',
        fragment: 'not generated yet',
      ),
      actionPriority: const <List<String>>[
        <String>['Activate Subject'],
        <String>['Check Maintained Files'],
        <String>['Generate Itemization', 'Refresh Itemization'],
        <String>['Suggest DST Constructs'],
        <String>['Create Draft Composition', 'Refresh Draft Composition'],
      ],
    );
    _logStep('restore draft after activation');
    await _settleSubjectTab(
      tester,
      router,
      container,
      tabKey: 'draft',
      shellTitle: 'Current Step',
    );
    _logStep('restore draft after action sequence');
    await _settleSubjectTab(
      tester,
      router,
      container,
      tabKey: 'draft',
      shellTitle: 'Current Step',
    );
    _logStep('wait for draft compose shell');
    await _pumpUntil(
      tester,
      () =>
          !_state(container).subjectBusy &&
          !_statusValueContains(
            container,
            label: 'Draft Composition',
            fragment: 'not generated yet',
          ) &&
          find.textContaining('Selected Item').evaluate().isNotEmpty &&
          find.textContaining('Draft Item Inventory').evaluate().isNotEmpty &&
          _isVisibleActionButtonPresent(labels: const <String>['Open Model']),
      timeout: const Duration(seconds: 120),
      failureMessage: 'The draft tab did not reach the compose shell state.',
    );
    _logStep('verify draft compose row interaction updates draft detail');
    await _tapInteractiveRowAndWaitForPaneChange(
      tester,
      container,
      paneKey: 'draft_scope_tree',
      rowIndex: 1,
      detailPaneKey: 'draft_detail',
      failureMessage:
          'Selecting a different draft compose row did not update Draft Detail.',
    );
    _logStep('capture draft compose');
    await _capture(
      tester,
      binding,
      '05-draft-compose',
      focusTitle: 'Draft Item Inventory',
      requiredTitles: const <String>[
        'Current Step',
        'Draft Status',
        'More Actions',
        'Selected Item',
        'Draft Item Inventory',
      ],
      forbiddenTitles: const <String>[
        'View',
        'Case Objects',
        'Case Frame',
        'Transformation Model',
        'Explore Alternatives',
        'Issues & Validation',
      ],
    );

    _logStep('open draft model flow');
    await _applyIfPresent(
      tester,
      router,
      container,
      labelContains: const <String>['Open Model'],
    );
    _logStep('wait for draft lens tabs');
    await _pumpUntil(
      tester,
      () =>
          find.text('Frame').evaluate().isNotEmpty &&
          find.text('Model').evaluate().isNotEmpty &&
          find.text('Explore').evaluate().isNotEmpty,
      timeout: const Duration(seconds: 60),
      failureMessage: 'The draft model shell did not expose lens tabs.',
    );
    _logStep('verify draft model row interaction updates case detail');
    await _tapInteractiveRowAndWaitForPaneChange(
      tester,
      container,
      paneKey: 'draft_scope_tree',
      rowIndex: 1,
      detailPaneKey: 'draft_detail',
      failureMessage:
          'Selecting a different draft case object did not update Draft Detail.',
    );

    _logStep('switch draft lens to frame');
    try {
      await _tapDraftLensTab(tester, 'frame');
      await _pumpUntil(
        tester,
        () => find.textContaining('Case Frame').evaluate().isNotEmpty,
        failureMessage: 'The draft frame shell did not open.',
      );
    } catch (error) {
      _logSubjectSnapshotDiagnostics(container, phaseLabel: 'draft-frame');
      await binding.takeScreenshot('06-draft-frame-debug');
      rethrow;
    }
    _logStep('capture draft frame');
    await _capture(
      tester,
      binding,
      '06-draft-frame',
      focusTitle: 'Case Objects',
      requiredTitles: const <String>[
        'Case Objects',
        'Case Frame',
        'Issues & Validation',
      ],
    );

    _logStep('switch draft lens to model');
    try {
      await _tapDraftLensTab(tester, 'model');
      await _pumpUntil(
        tester,
        () => find.textContaining('Transformation Model').evaluate().isNotEmpty,
        failureMessage: 'The draft model shell did not open.',
      );
    } catch (error) {
      _logSubjectSnapshotDiagnostics(container, phaseLabel: 'draft-model');
      await binding.takeScreenshot('07-draft-model-debug');
      rethrow;
    }
    _logStep('capture draft model');
    await _capture(
      tester,
      binding,
      '07-draft-model',
      focusTitle: 'Case Objects',
      requiredTitles: const <String>[
        'Case Objects',
        'Transformation Model',
        'Issues & Validation',
      ],
    );

    _logStep('switch draft lens to explore');
    try {
      await _tapDraftLensTab(tester, 'explore');
      await _pumpUntil(
        tester,
        () => find.textContaining('Explore Alternatives').evaluate().isNotEmpty,
        failureMessage: 'The draft explore shell did not open.',
      );
    } catch (error) {
      _logSubjectSnapshotDiagnostics(container, phaseLabel: 'draft-explore');
      await binding.takeScreenshot('08-draft-explore-debug');
      rethrow;
    }
    _logStep('capture draft explore');
    await _capture(
      tester,
      binding,
      '08-draft-explore',
      focusTitle: 'Case Objects',
      requiredTitles: const <String>[
        'Case Objects',
        'Explore Alternatives',
        'Issues & Validation',
      ],
    );

    _logStep('return to draft compose before decision analysis');
    await _applyIfPresent(
      tester,
      router,
      container,
      labelContains: const <String>['Back To Compose'],
    );
    await _pumpUntil(
      tester,
      () =>
          !_state(container).subjectBusy &&
          find.textContaining('Draft Item Inventory').evaluate().isNotEmpty &&
          _isVisibleActionButtonPresent(
            labels: const <String>['Start Decision Analysis'],
          ),
      timeout: const Duration(seconds: 120),
      failureMessage:
          'The draft tab did not return to compose with Start Decision Analysis ready.',
    );

    _logStep('restore draft shell before decision analysis');
    await _settleSubjectTab(
      tester,
      router,
      container,
      tabKey: 'draft',
      shellTitle: 'Current Step',
    );
    _logStep('run maintained-files check before decision analysis if present');
    await _applyIfPresent(
      tester,
      router,
      container,
      labelContains: const <String>[
        'Check Maintained Files',
        'Compare Maintained Files',
      ],
    );
    _logStep('restore draft after maintained-files check');
    await _settleSubjectTab(
      tester,
      router,
      container,
      tabKey: 'draft',
      shellTitle: 'Current Step',
    );
    _logStep('start decision analysis if present');
    await _applyIfPresent(
      tester,
      router,
      container,
      labelContains: const <String>['Start Decision Analysis'],
    );
    _logStep('restore draft after starting decision analysis');
    await _settleSubjectTab(
      tester,
      router,
      container,
      tabKey: 'draft',
      shellTitle: 'Current Step',
    );
    _logStep('run decision analysis if present');
    await _applyIfPresent(
      tester,
      router,
      container,
      labelContains: const <String>['Run Decision Analysis'],
    );

    _logStep('settle review main');
    await _settleSubjectTab(
      tester,
      router,
      container,
      tabKey: 'review',
      shellTitle: 'Current Step',
    );
    _logStep('apply compare maintained files if present');
    await _applyIfPresent(
      tester,
      router,
      container,
      labelContains: const <String>['Compare Maintained Files'],
    );
    _logStep('apply preview report plan if present');
    await _applyIfPresent(
      tester,
      router,
      container,
      labelContains: const <String>['Preview Report Plan'],
    );
    _logStep('wait for review report-plan shell');
    await _pumpUntil(
      tester,
      () =>
          !_state(container).subjectBusy &&
          find.textContaining('Report Scope').evaluate().isNotEmpty &&
          find.textContaining('Selection Details').evaluate().isNotEmpty,
      timeout: const Duration(seconds: 120),
      failureMessage:
          'The review tab did not reach the report-plan shell state.',
    );
    _logStep('wait for approve-for-report action');
    await _pumpUntil(
      tester,
      () => _isVisibleActionButtonPresent(labels: const <String>['Approve For Report']),
      timeout: const Duration(seconds: 120),
      failureMessage:
          'The review tab did not expose Approve For Report after running decision analysis.',
    );
    _logStep('verify review scope interaction updates selection details');
    await _tapInteractiveRowAndWaitForPaneChange(
      tester,
      container,
      paneKey: 'review_scope_tree',
      rowIndex: 1,
      detailPaneKey: 'review_scope_detail',
      failureMessage:
          'Selecting a different review scope row did not update Selection Details.',
    );
    _logStep('capture review main');
    await _capture(
      tester,
      binding,
      '09-review-main',
      focusTitle: 'Report Scope',
      requiredTitles: const <String>[
        'Current Step',
        'Review Status',
        'More Actions',
        'Report Scope',
        'Selection Details',
      ],
    );

    _logStep('open review journal');
    await tester.tap(find.widgetWithText(OutlinedButton, 'Journal'));
    await _pumpUntil(
      tester,
      () => find.textContaining('Review Journal').evaluate().isNotEmpty,
      failureMessage: 'The review journal shell did not open.',
    );
    _logStep('capture review journal');
    await _capture(
      tester,
      binding,
      '10-review-journal',
      focusTitle: 'Review Journal',
      requiredTitles: const <String>['Review Journal', 'Review Status'],
    );

    _logStep('approve review for report');
    await _applyIfPresent(
      tester,
      router,
      container,
      labelContains: const <String>['Approve For Report'],
    );

    _logStep('settle publication main');
    await _settleSubjectTab(
      tester,
      router,
      container,
      tabKey: 'publication',
      shellTitle: 'Current Step',
    );
    _logStep('wait for publication report shell');
    await _pumpUntil(
      tester,
      () =>
          !_state(container).subjectBusy &&
          find.textContaining('Report Scope').evaluate().isNotEmpty &&
          find.textContaining('Selection Details').evaluate().isNotEmpty,
      timeout: const Duration(seconds: 120),
      failureMessage:
          'The publication tab did not reach the report shell state.',
    );
    _logStep('wait for lock-report-inputs action');
    await _pumpUntil(
      tester,
      () => _isVisibleActionButtonPresent(labels: const <String>['Lock Report Inputs']),
      timeout: const Duration(seconds: 120),
      failureMessage:
          'The publication tab did not expose Lock Report Inputs after review approval.',
    );
    _logStep('verify publication scope interaction updates selection details');
    await _tapInteractiveRowAndWaitForPaneChange(
      tester,
      container,
      paneKey: 'publication_scope_tree',
      rowIndex: 1,
      detailPaneKey: 'publication_scope_detail',
      failureMessage:
          'Selecting a different publication scope row did not update Selection Details.',
    );
    _logStep('capture publication main');
    await _capture(
      tester,
      binding,
      '11-publication-main',
      focusTitle: 'Report Scope',
      requiredTitles: const <String>[
        'Current Step',
        'Publication Status',
        'More Actions',
        'Report Scope',
        'Selection Details',
      ],
    );

    _logStep('lock publication inputs if present');
    await _applyIfPresent(
      tester,
      router,
      container,
      labelContains: const <String>['Lock Report Inputs'],
    );
    _logStep('wait for build-report action');
    await _pumpUntil(
      tester,
      () => _isVisibleActionButtonPresent(labels: const <String>['Build Report']),
      timeout: const Duration(seconds: 120),
      failureMessage:
          'The publication tab did not expose Build Report after locking report inputs.',
    );
    _logStep('build report if present');
    await _applyIfPresent(
      tester,
      router,
      container,
      labelContains: const <String>['Build Report'],
    );
    _logStep('wait for built publication outputs');
    await _pumpUntil(
      tester,
      () =>
          !_state(container).subjectBusy &&
          _isVisibleActionButtonPresent(labels: const <String>['Preview report.pdf']) &&
          !_isVisibleActionButtonPresent(labels: const <String>['Build Report']) &&
          find.textContaining('Report build completed').evaluate().isNotEmpty,
      timeout: const Duration(seconds: 180),
      failureMessage:
          'The real direct v10 browser flow did not reach the built publication output state.',
    );
  });
}

bool _isVisibleActionButtonPresent({required List<String> labels}) {
  for (final label in labels) {
    if (_enabledOutlinedButtonFinder(label).evaluate().isNotEmpty) {
      return true;
    }
  }
  return false;
}

Future<void> _applyWorkflowActionsUntil(
  WidgetTester tester,
  GoRouter router,
  ProviderContainer container, {
  required String tabKey,
  required bool Function() isReady,
  required List<List<String>> actionPriority,
  int maxRounds = 6,
}) async {
  for (var round = 0; round < maxRounds; round++) {
    if (isReady()) {
      return;
    }
    var acted = false;
    for (final labels in actionPriority) {
      final action = _findActionByLabel(container, labelContains: labels);
      if (action == null) {
        continue;
      }
      acted = true;
      _logStep('applied workflow action: ${labels.join(' / ')}');
      final controller = container.read(
        app.workstationControllerProvider.notifier,
      );
      final preferredTab = _preferredActionTabKey(action.label);
      if (preferredTab != null &&
          preferredTab != _state(container).currentTabKey) {
        await controller.showTab(preferredTab);
      }
      final nextTab = await controller.applyAction(action.key);
      if (nextTab != null && nextTab.isNotEmpty) {
        router.go('/workstation/$nextTab');
        await controller.showTab(nextTab);
      }
      await tester.pumpAndSettle();
      await controller.showTab(tabKey);
      router.go('/workstation/$tabKey');
      try {
        await _settleSubjectTab(
          tester,
          router,
          container,
          tabKey: tabKey,
          shellTitle: 'Current Step',
        );
      } catch (error) {
        _logSubjectSnapshotDiagnostics(
          container,
          phaseLabel: '$tabKey-after-${labels.join('_')}',
        );
        rethrow;
      }
      break;
    }
    if (!acted) {
      return;
    }
  }
}

bool _statusValueContains(
  ProviderContainer container, {
  required String label,
  required String fragment,
}) {
  final snapshot = _state(container).subjectSnapshot;
  if (snapshot == null) {
    return false;
  }
  final loweredLabel = label.toLowerCase();
  final loweredFragment = fragment.toLowerCase();
  for (final row in snapshot.phaseView.statusView.rows) {
    if (row.label.toLowerCase() != loweredLabel) {
      continue;
    }
    return row.value.toLowerCase().contains(loweredFragment);
  }
  return false;
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

Future<void> _applyIfPresent(
  WidgetTester tester,
  GoRouter router,
  ProviderContainer container, {
  required List<String> labelContains,
}) async {
  final action = _findActionByLabel(container, labelContains: labelContains);
  if (action == null) {
    return;
  }
  final controller = container.read(app.workstationControllerProvider.notifier);
  final preferredTab = _preferredActionTabKey(action.label);
  if (preferredTab != null && preferredTab != _state(container).currentTabKey) {
    await controller.showTab(preferredTab);
  }
  final nextTab = await controller.applyAction(action.key);
  if (nextTab != null && nextTab.isNotEmpty) {
    router.go('/workstation/$nextTab');
    await controller.showTab(nextTab);
  }
  await tester.pumpAndSettle();
}

({String key, String label})? _findActionByLabel(
  ProviderContainer container, {
  required List<String> labelContains,
}) {
  final snapshot = _state(container).subjectSnapshot;
  if (snapshot == null) {
    return null;
  }
  final loweredFragments = labelContains
      .map((fragment) => fragment.toLowerCase())
      .toList(growable: false);

  for (final action in snapshot.phaseView.currentStep.actions) {
    if (action.enabled && _matchesActionLabel(action.label, loweredFragments)) {
      return (key: action.key, label: action.label);
    }
  }
  for (final action in snapshot.controlBundle.moreActions) {
    if (action.enabled && _matchesActionLabel(action.label, loweredFragments)) {
      return (key: action.key, label: action.label);
    }
  }
  return null;
}

bool _matchesActionLabel(String label, List<String> loweredFragments) {
  final loweredLabel = label.toLowerCase();
  for (final fragment in loweredFragments) {
    if (loweredLabel.contains(fragment)) {
      return true;
    }
  }
  return false;
}

String? _preferredActionTabKey(String label) {
  final separator = label.indexOf(':');
  if (separator <= 0) {
    return null;
  }
  final prefix = label.substring(0, separator).trim().toLowerCase();
  return switch (prefix) {
    'gather' => 'research',
    'itemize' => 'itemize',
    'draft' => 'draft',
    'review' => 'review',
    'publication' => 'publication',
    'chat' => 'chat',
    _ => null,
  };
}

app.WorkstationState _state(ProviderContainer container) {
  return container.read(app.workstationControllerProvider);
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

Future<void> _capture(
  WidgetTester tester,
  IntegrationTestWidgetsFlutterBinding binding,
  String screenshotName, {
  String? focusTitle,
  required List<String> requiredTitles,
  List<String> forbiddenTitles = const <String>[],
}) async {
  _logStep('validate shell before screenshot: $screenshotName');
  await tester.pumpAndSettle();
  expect(
    find.byKey(const ValueKey<String>('desktop-subject-selector')),
    findsOneWidget,
  );
  expect(find.textContaining('Workstation · Gather'), findsNothing);
  expect(find.textContaining('Workstation · Itemize'), findsNothing);
  expect(find.textContaining('Workstation · Draft'), findsNothing);
  expect(find.textContaining('Workstation · Review'), findsNothing);
  expect(find.textContaining('Workstation · Publication'), findsNothing);
  for (final title in requiredTitles) {
    expect(
      find.textContaining(title),
      findsWidgets,
      reason: 'Expected to find "$title" before taking $screenshotName.',
    );
  }
  for (final title in forbiddenTitles) {
    expect(
      find.textContaining(title),
      findsNothing,
      reason: 'Did not expect to find "$title" before taking $screenshotName.',
    );
  }
  if (focusTitle != null) {
    final focusFinder = find.textContaining(focusTitle).first;
    await tester.ensureVisible(focusFinder);
    await tester.pumpAndSettle();
  }
  _logStep('take screenshot: $screenshotName');
  await binding.takeScreenshot(screenshotName);
  _logStep('screenshot captured: $screenshotName');
}

Future<void> _tapDraftLensTab(WidgetTester tester, String lens) async {
  final finder = find.byKey(ValueKey<String>('draft-lens-$lens'));
  expect(finder, findsOneWidget, reason: 'Expected draft lens tab "$lens".');
  await tester.ensureVisible(finder);
  await tester.pumpAndSettle();
  await tester.tap(finder);
  await tester.pump();
}

Future<void> _tapInteractiveRowAndWaitForPaneChange(
  WidgetTester tester,
  ProviderContainer container, {
  required String paneKey,
  required int rowIndex,
  required String detailPaneKey,
  required String failureMessage,
  Duration timeout = const Duration(seconds: 30),
}) async {
  final paneState = _interactivePaneState(container, paneKey);
  if (paneState.count <= 1) {
    _logStep(
      'skip interaction check for $paneKey: only ${paneState.count} selectable row(s) available',
    );
    return;
  }
  final targetIndex = _resolveInteractiveRowTarget(
    container,
    paneKey: paneKey,
    preferredRowIndex: rowIndex,
  );
  final rowFinder = find.byKey(
    ValueKey<String>('interactive-pane-row:$paneKey:$targetIndex'),
  );
  expect(
    rowFinder,
    findsOneWidget,
    reason:
        'Expected selectable row $targetIndex in $paneKey before validating interaction parity. '
        'count=${paneState.count} selectedIndex=${paneState.selectedIndex}',
  );
  final before = _paneSignature(container, detailPaneKey);
  await tester.ensureVisible(rowFinder);
  await tester.pumpAndSettle();
  await tester.tap(rowFinder);
  try {
    await _pumpUntil(
      tester,
      () =>
          !_state(container).subjectBusy &&
          _paneSignature(container, detailPaneKey) != before,
      timeout: timeout,
      failureMessage: failureMessage,
    );
  } catch (_) {
    final pane = _paneSignature(container, paneKey);
    final detailAfter = _paneSignature(container, detailPaneKey);
    fail(
      '$failureMessage\n'
      'paneKey=$paneKey targetIndex=$targetIndex selectedIndex=${paneState.selectedIndex} count=${paneState.count}\n'
      'pane=$pane\n'
      'detail.before=$before\n'
      'detail.after=$detailAfter',
    );
  }
}

int _resolveInteractiveRowTarget(
  ProviderContainer container, {
  required String paneKey,
  required int preferredRowIndex,
}) {
  final state = _interactivePaneState(container, paneKey);
  if (state.count <= 1) {
    return preferredRowIndex;
  }
  if (preferredRowIndex != state.selectedIndex &&
      preferredRowIndex >= 0 &&
      preferredRowIndex < state.count) {
    return preferredRowIndex;
  }
  if (state.selectedIndex == 0) {
    return 1;
  }
  return 0;
}

({int selectedIndex, int count}) _interactivePaneState(
  ProviderContainer container,
  String paneKey,
) {
  final snapshot = _state(container).subjectSnapshot;
  if (snapshot == null) {
    return (selectedIndex: -1, count: 0);
  }
  subject.SubjectPaneView? pane;
  for (final candidate in snapshot.paneBundle.panes) {
    if (candidate.key == paneKey) {
      pane = candidate;
      break;
    }
  }
  if (pane == null) {
    return (selectedIndex: -1, count: 0);
  }
  final itemizePattern = RegExp(
    r'^\s*(?<selected>>)?\s*(?:\[[^\]]*\]\s*)?\[[^\]]+\]\s+',
  );
  final draftPattern = RegExp(
    r'^\s*(?<selected>>)?\s*(?:\[[^\]]+\]\[[^\]]+\]|\[[^\]]+\])\s+',
  );
  final reportPattern = RegExp(
    r'^(?<pointer>> |  )(?<hold>h |  )(?<indent>(?:  )*)(?<marker>\[[^\]]+\])\s+',
  );

  var selectedIndex = -1;
  var count = 0;
  for (final rawLine in pane.lines) {
    final line = rawLine.replaceFirst(RegExp(r'\n+$'), '');
    RegExpMatch? match;
    if (paneKey == 'itemize_inventory') {
      match = itemizePattern.firstMatch(line);
    } else if (paneKey == 'draft_scope_tree') {
      match = draftPattern.firstMatch(line);
    } else {
      match = reportPattern.firstMatch(line);
    }
    if (match == null) {
      continue;
    }
    final isSelected =
        paneKey == 'review_scope_tree' || paneKey == 'publication_scope_tree'
        ? (match.namedGroup('pointer') ?? '') == '> '
        : (match.namedGroup('selected') ?? '') == '>';
    if (isSelected) {
      selectedIndex = count;
    }
    count += 1;
  }
  return (selectedIndex: selectedIndex, count: count);
}

String _paneSignature(ProviderContainer container, String paneKey) {
  final snapshot = _state(container).subjectSnapshot;
  if (snapshot == null) {
    return '';
  }
  for (final pane in snapshot.paneBundle.panes) {
    if (pane.key != paneKey) {
      continue;
    }
    return <String>[
      pane.title,
      ...pane.lines,
      for (final row in pane.rows) '${row.label}:${row.value}',
    ].join('\n');
  }
  return '';
}

Future<void> _pumpUntil(
  WidgetTester tester,
  bool Function() predicate, {
  Duration timeout = const Duration(seconds: 30),
  Duration step = const Duration(milliseconds: 150),
  required String failureMessage,
}) async {
  final DateTime deadline = DateTime.now().add(timeout);
  while (DateTime.now().isBefore(deadline)) {
    await tester.pump(step);
    if (predicate()) {
      await tester.pumpAndSettle();
      return;
    }
  }
  fail(failureMessage);
}

void _logStep(String message) {
  // ignore: avoid_print
  print('[subject-tabs] $message');
}

void _logSubjectSnapshotDiagnostics(
  ProviderContainer container, {
  required String phaseLabel,
}) {
  final state = _state(container);
  final snapshot = state.subjectSnapshot;
  final phaseView = snapshot?.phaseView;
  final currentStep = phaseView?.currentStep;
  final moreActionLabels = snapshot?.controlBundle.moreActions
      .map((action) => '${action.key}:${action.label}:${action.enabled}')
      .toList(growable: false);
  final selectLabels = snapshot?.controlBundle.selects
      .map((spec) => '${spec.key}:${spec.label}:${spec.value}')
      .toList(growable: false);
  final switchLabels = snapshot?.controlBundle.switches
      .map((spec) => '${spec.key}:${spec.label}:${spec.value}')
      .toList(growable: false);
  final paneTitles = snapshot?.paneBundle.panes
      .map((pane) => '${pane.key}:${pane.title}')
      .toList(growable: false);
  // ignore: avoid_print
  print('[subject-tabs][$phaseLabel] tab=${state.currentTabKey}');
  // ignore: avoid_print
  print('[subject-tabs][$phaseLabel] busy=${state.subjectBusy}');
  // ignore: avoid_print
  print('[subject-tabs][$phaseLabel] phase=${phaseView?.phase}');
  // ignore: avoid_print
  print('[subject-tabs][$phaseLabel] step.title=${currentStep?.title}');
  // ignore: avoid_print
  print('[subject-tabs][$phaseLabel] step.status=${currentStep?.status}');
  // ignore: avoid_print
  print(
    '[subject-tabs][$phaseLabel] step.actions=${currentStep?.actions.map((action) => '${action.key}:${action.label}:${action.enabled}').toList(growable: false)}',
  );
  // ignore: avoid_print
  print('[subject-tabs][$phaseLabel] moreActions=$moreActionLabels');
  // ignore: avoid_print
  print('[subject-tabs][$phaseLabel] selects=$selectLabels');
  // ignore: avoid_print
  print('[subject-tabs][$phaseLabel] switches=$switchLabels');
  // ignore: avoid_print
  print('[subject-tabs][$phaseLabel] panes=$paneTitles');
}
