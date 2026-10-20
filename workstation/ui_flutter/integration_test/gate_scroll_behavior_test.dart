import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:workstation_ui/src/generated/workstation/grpc/definitions/subject_workflow.pb.dart'
    as subject;
import 'package:workstation_ui/src/textual/layout.dart' as shell_spec;
import 'package:workstation_ui/src/textual_desktop_subject_shell.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets(
    'current step and status panes scroll independently while gate actions stay pinned',
    (tester) async {
      addTearDown(() => tester.binding.setSurfaceSize(null));
      await tester.binding.setSurfaceSize(const Size(1680, 1000));

      const whyText =
          'This gate body is intentionally long so the Current Step pane must scroll without dragging the status pane with it.';
      final layout = await _testLayout();

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SizedBox.expand(
              child: TextualDesktopSubjectShell(
                layout: layout,
                tabs: layout.tabs,
                currentTabKey: 'research',
                activeShellStateKey: 'gather.main',
                subjects: const <subject.SubjectScenarioSummary>[],
                selectedScenarioKey: '',
                selectedScenarioLabel: 'Gate Scroll Subject',
                onSubjectSelected: (_) {},
                statusText: 'Connected to workstation-root.',
                onShellStateSelected: (_) {},
                onTabSelected: (_) {},
                snapshot: _snapshot(whyText),
                subjectBusy: false,
                onAction: (_, {String? actionLabel}) async {},
                onInteraction:
                    (
                      _, {
                      int delta = 0,
                      String? targetId,
                      bool previewOnly = false,
                    }) async {},
              ),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      final gateScrollFinder = find.byKey(
        const ValueKey<String>('gate-current-step-scroll'),
      );
      final statusScrollFinder = find.byKey(
        const ValueKey<String>('gate-status-scroll'),
      );
      final whyFinder = find.text(whyText);
      final statusFinder = find.text('Gate status 01');
      final lowerStatusFinder = find.text('Gate status 10');
      final actionFinder = find.widgetWithText(
        OutlinedButton,
        'Import Markdown File',
      );

      expect(gateScrollFinder, findsOneWidget);
      expect(statusScrollFinder, findsOneWidget);
      expect(whyFinder, findsOneWidget);
      expect(statusFinder, findsOneWidget);
      expect(lowerStatusFinder, findsOneWidget);
      expect(actionFinder, findsOneWidget);

      final initialWhyTop = tester.getTopLeft(whyFinder).dy;
      final initialStatusTop = tester.getTopLeft(statusFinder).dy;
      final initialActionTop = tester.getTopLeft(actionFinder).dy;

      await tester.drag(gateScrollFinder, const Offset(0, -140));
      await tester.pumpAndSettle();

      final updatedWhyTop = tester.getTopLeft(whyFinder).dy;
      final updatedStatusTop = tester.getTopLeft(statusFinder).dy;
      final updatedActionTop = tester.getTopLeft(actionFinder).dy;

      expect(
        updatedWhyTop,
        lessThan(initialWhyTop - 20),
        reason: 'The Current Step body should move inside its own viewport.',
      );
      expect(
        updatedStatusTop,
        closeTo(initialStatusTop, 0.5),
        reason:
            'Scrolling Current Step must not move the right-hand status pane.',
      );
      expect(
        updatedActionTop,
        closeTo(initialActionTop, 0.5),
        reason:
            'Gate action buttons must stay pinned while the Current Step body scrolls.',
      );

      final statusBeforeStatusScroll = tester.getTopLeft(lowerStatusFinder).dy;
      final whyBeforeStatusScroll = tester.getTopLeft(whyFinder).dy;
      final actionBeforeStatusScroll = tester.getTopLeft(actionFinder).dy;

      await tester.drag(statusScrollFinder, const Offset(0, -140));
      await tester.pumpAndSettle();

      final statusAfterStatusScroll = tester.getTopLeft(lowerStatusFinder).dy;
      final whyAfterStatusScroll = tester.getTopLeft(whyFinder).dy;
      final actionAfterStatusScroll = tester.getTopLeft(actionFinder).dy;

      expect(
        statusAfterStatusScroll,
        lessThan(statusBeforeStatusScroll - 20),
        reason:
            'The right-hand status pane should move inside its own viewport.',
      );
      expect(
        whyAfterStatusScroll,
        closeTo(whyBeforeStatusScroll, 0.5),
        reason:
            'Scrolling the status pane must not move the Current Step body.',
      );
      expect(
        actionAfterStatusScroll,
        closeTo(actionBeforeStatusScroll, 0.5),
        reason:
            'Gate action buttons must stay pinned while the status pane scrolls.',
      );
      expect(tester.takeException(), isNull);
    },
  );
}

Future<shell_spec.WorkstationLayoutSpec> _testLayout() async {
  final payload = await rootBundle.loadString('assets/workstation_layout.json');
  return shell_spec.WorkstationLayoutSpec.fromJson(
    jsonDecode(payload) as Map<String, dynamic>,
  );
}

subject.SubjectWorkflowSnapshotView _snapshot(String whyText) {
  final detailLines = <String>[
    for (var index = 1; index <= 18; index++)
      '- evidence line ${index.toString().padLeft(2, '0')}',
  ];
  return subject.SubjectWorkflowSnapshotView()
    ..phaseView = (subject.SubjectPhaseView()
      ..phase = 'research'
      ..phaseTitle = 'Gather'
      ..preferredPhase = 'research'
      ..scenario = _scenario()
      ..currentStep = (subject.SubjectCurrentStepView()
        ..title = 'Scroll the step body only'
        ..status =
            'The Current Step body is intentionally taller than its viewport.'
        ..why = whyText
        ..detailLines.addAll(detailLines)
        ..actions.addAll(<subject.SubjectGateAction>[
          _gateAction('use_markdown_ingress', 'Import Markdown File'),
          _gateAction('use_url_ingress', 'Learn URL'),
        ]))
      ..statusView = (subject.SubjectStatusView()
        ..title = 'Subject Status'
        ..rows.addAll(<subject.KeyValueRow>[
          _statusRow('Gate status 01', 'top row should stay fixed'),
          _statusRow('Gate status 02', 'second row should stay fixed'),
          _statusRow('Gate status 03', 'status panes should scroll vertically'),
          _statusRow('Gate status 04', 'status panes should scroll vertically'),
          _statusRow('Gate status 05', 'status panes should scroll vertically'),
          _statusRow('Gate status 06', 'status panes should scroll vertically'),
          _statusRow('Gate status 07', 'status panes should scroll vertically'),
          _statusRow('Gate status 08', 'status panes should scroll vertically'),
          _statusRow('Gate status 09', 'status panes should scroll vertically'),
          _statusRow(
            'Gate status 10',
            'lower row should move when status scrolls',
          ),
          _statusRow('Corpus root', '/tmp/workstation-root/corpus'),
          _statusRow('Gather', '1 source, 1 delta, 1 item'),
          _statusRow('Reasoning Scope', '3 support items from 1 subject'),
          _statusRow('Review', 'no maintained subject projections yet'),
          _statusRow('Publication', 'no publication projections yet'),
        ]))
      ..journeyLines.addAll(const <String>[
        '1. Gather',
        '2. Itemize',
        '3. Draft',
        '4. Review',
        '5. Publication',
      ])
      ..workspaceView = (subject.TextSection()
        ..title = 'Workspace'
        ..lines.addAll(const <String>[
          'Root: /tmp/workstation-root',
          'Phase: Gather',
        ])))
    ..controlBundle = (subject.SubjectControlBundleView()
      ..phase = 'research'
      ..moreActions.add(_actionSpec('refresh_subjects', 'Refresh Subjects')))
    ..paneBundle = (subject.SubjectPaneBundleView()
      ..phase = 'research'
      ..panes.addAll(<subject.SubjectPaneView>[
        (subject.SubjectPaneView()
          ..key = 'research_sources'
          ..title = 'Source Sets'
          ..lines.addAll(const <String>[
            'Current source state',
            'No source material has been imported yet.',
            'This panel will show the latest source file, delta application, and support state.',
          ])),
        (subject.SubjectPaneView()
          ..key = 'research_observation'
          ..title = 'Learned Snapshot'
          ..lines.addAll(const <String>[
            'Subject summary',
            'No learned snapshot exists yet.',
            'After intake, this panel will show the subject summary, items, and item kinds.',
          ])),
      ]));
}

subject.SubjectScenarioSummary _scenario() {
  return subject.SubjectScenarioSummary()
    ..key = 'gate-scroll-subject'
    ..subjectId = 'gate-scroll-subject'
    ..title = 'Gate Scroll Subject'
    ..summary = 'Synthetic subject for gate-row layout regression coverage.'
    ..governanceStatus = 'ready';
}

subject.SubjectGateAction _gateAction(String key, String label) {
  return subject.SubjectGateAction()
    ..displayKind = subject.SubjectGateAction_DisplayKind.BUTTON
    ..actionKind = 'subject_action'
    ..key = key
    ..label = label
    ..enabled = true;
}

subject.SubjectActionSpec _actionSpec(String key, String label) {
  return subject.SubjectActionSpec()
    ..key = key
    ..label = label
    ..enabled = true;
}

subject.KeyValueRow _statusRow(String label, String value) {
  return subject.KeyValueRow()
    ..label = label
    ..value = value;
}
