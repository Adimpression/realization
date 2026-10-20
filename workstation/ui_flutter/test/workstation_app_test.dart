import 'dart:convert';
import 'dart:io';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:workstation_ui/main.dart';
import 'package:workstation_ui/src/generated/workstation/grpc/definitions/subject_workflow.pb.dart'
    as subject;
import 'package:workstation_ui/src/generated/workstation/grpc/definitions/workstation_assets.pb.dart'
    as assets;
import 'package:workstation_ui/src/generated/workstation/grpc/definitions/workstation_bootstrap.pb.dart'
    as bootstrap;
import 'package:workstation_ui/src/generated/workstation/grpc/definitions/workstation_shell.pb.dart'
    as shell;
import 'package:workstation_ui/src/textual/layout.dart' as shell_spec;

Finder _desktopTabFinder(String title) {
  const tabKeys = <String, String>{
    'Chat': 'chat',
    'Gather': 'research',
    'Itemize': 'itemize',
    'Draft': 'draft',
    'Review': 'review',
    'Publication': 'publication',
    'Permissions': 'permissions',
    'Activity': 'activity',
    'Skills': 'skills',
  };
  final tabKey = tabKeys[title];
  if (tabKey == null) {
    throw ArgumentError.value(
      title,
      'title',
      'Unknown desktop workstation tab',
    );
  }
  return find.byKey(ValueKey<String>('desktop-tab:$tabKey'));
}

Finder _textContaining(String snippet) {
  return find.byWidgetPredicate((widget) {
    if (widget is! RichText) {
      return false;
    }
    final data = widget.text.toPlainText();
    return data.contains(snippet);
  }, description: 'text containing "$snippet"');
}

Finder _interactivePaneRowFinder(String paneKey, int index) {
  return find.byKey(ValueKey<String>('interactive-pane-row:$paneKey:$index'));
}

Finder _paneFrameFinder(String paneId) {
  return find.byKey(ValueKey<String>('pane-frame:$paneId'));
}

Finder _paneScrollFinder(String paneId) {
  return find.byKey(ValueKey<String>('pane-scroll-y:$paneId'));
}

Finder _desktopSubjectSelectorControlFinder() {
  return find.byKey(const ValueKey<String>('desktop-subject-selector-control'));
}

Finder _selectControlFinder(String key) {
  return find.byKey(ValueKey<String>('select-control:$key'));
}

Finder _switchControlFinder(String key) {
  return find.byKey(ValueKey<String>('switch-control:$key'));
}

Finder _gateActionFinder(String label) {
  return find.widgetWithText(OutlinedButton, label);
}

Future<void> _tapVisible(WidgetTester tester, Finder finder) async {
  await tester.ensureVisible(finder);
  await tester.tap(finder);
  await tester.pumpAndSettle();
}

Future<void> _tapGateAction(WidgetTester tester, String label) async {
  await _tapVisible(tester, _gateActionFinder(label).first);
}

Future<void> _tapDesktopTab(WidgetTester tester, String title) async {
  await _tapVisible(tester, _desktopTabFinder(title));
}

Future<void> _selectDesktopSubject(
  WidgetTester tester,
  String subjectLabel,
) async {
  await _tapVisible(tester, _desktopSubjectSelectorControlFinder());
  await _tapVisible(tester, find.text(subjectLabel).last);
}

Future<void> _selectControlValue(
  WidgetTester tester,
  String controlKey,
  String optionLabel,
) async {
  await _tapVisible(tester, _selectControlFinder(controlKey));
  await _tapVisible(tester, find.text(optionLabel).last);
}

Future<void> _toggleSwitchControl(
  WidgetTester tester,
  String controlKey,
) async {
  await _tapVisible(tester, _switchControlFinder(controlKey));
}

void _expectGateActionDisabled(WidgetTester tester, String label) {
  final button = tester.widget<OutlinedButton>(_gateActionFinder(label).first);
  expect(button.onPressed, isNull);
}

void _expectActionOrderLeftToRight(
  WidgetTester tester,
  String firstLabel,
  String secondLabel,
) {
  final firstOffset = tester.getTopLeft(_gateActionFinder(firstLabel).first);
  final secondOffset = tester.getTopLeft(_gateActionFinder(secondLabel).first);
  expect(firstOffset.dy, secondOffset.dy);
  expect(firstOffset.dx, lessThan(secondOffset.dx));
}

void main() {
  testWidgets('renders the bootstrap connection shell', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: WorkstationApp()));
    await tester.pumpAndSettle();

    expect(find.text('Workstation Bootstrap'), findsOneWidget);
    expect(find.text('Load Served Roots'), findsOneWidget);
    expect(find.text('Advertised Roots'), findsOneWidget);
  });

  testWidgets(
    'bootstrap can still manually open a workstation root from the landing route',
    (tester) async {
      await _pumpWorkstation(
        tester,
        controller: _BootstrapRoutingController(),
        initialLocation: '/',
        size: const Size(1480, 1000),
      );

      expect(find.text('Workstation Bootstrap'), findsOneWidget);
      await tester.tap(find.widgetWithText(FilledButton, 'Open Workstation'));
      await tester.pumpAndSettle();

      expect(find.text('Workstation · Chat'), findsOneWidget);
    },
  );

  testWidgets(
    'workstation routes auto-reconnect after a browser-style reload without losing the requested tab',
    (tester) async {
      await _pumpWorkstation(
        tester,
        controller: _DisconnectedResumeController(),
        initialLocation: '/workstation/research',
        size: const Size(1480, 1000),
      );

      await tester.pump();
      await tester.pumpAndSettle();

      expect(_desktopTabFinder('Gather'), findsOneWidget);
      expect(_textContaining('Create the first subject'), findsOneWidget);
      expect(find.text('Connected to workstation-root.'), findsNothing);
    },
  );

  testWidgets('chat bdd previews routing and submits prompts', (tester) async {
    await _pumpWorkstation(
      tester,
      controller: _ChatBddController(),
      initialLocation: '/workstation/chat',
      size: const Size(1680, 1100),
    );

    expect(find.text('Workstation · Chat'), findsOneWidget);
    expect(find.text('Transcript'), findsOneWidget);
    expect(find.text('Composer'), findsOneWidget);

    await tester.enterText(find.byType(TextField).first, 'inspect the repo');
    await tester.pump(const Duration(milliseconds: 300));
    await tester.pumpAndSettle();

    expect(find.textContaining('repo search preview'), findsOneWidget);

    await tester.tap(find.widgetWithText(FilledButton, 'Send'));
    await tester.pumpAndSettle();

    expect(find.text('Prompt completed.'), findsOneWidget);
    expect(find.text('user'), findsOneWidget);
    expect(find.text('assistant'), findsOneWidget);
    expect(find.textContaining('inspected the repo'), findsOneWidget);
    expect(find.textContaining('chat prompt submitted'), findsOneWidget);
  });

  testWidgets(
    'subject tabs render placeholder workflow states instead of blank fallbacks',
    (tester) async {
      await _pumpWorkstation(
        tester,
        controller: _PlaceholderPhaseController(),
        initialLocation: '/workstation/research',
        size: const Size(1600, 1100),
      );

      expect(_desktopTabFinder('Gather'), findsOneWidget);
      expect(_textContaining('Create the first subject'), findsOneWidget);
      expect(
        find.text('No subject snapshot is loaded for this phase.'),
        findsNothing,
      );

      await _tapDesktopTab(tester, 'Itemize');
      expect(_desktopTabFinder('Itemize'), findsOneWidget);
      expect(
        _textContaining('Stage learning before itemization'),
        findsOneWidget,
      );
      expect(
        find.text('No subject snapshot is loaded for this phase.'),
        findsNothing,
      );

      await _tapDesktopTab(tester, 'Draft');
      expect(_desktopTabFinder('Draft'), findsOneWidget);
      expect(
        _textContaining('Draft waits for itemized support'),
        findsOneWidget,
      );

      await _tapDesktopTab(tester, 'Review');
      expect(_desktopTabFinder('Review'), findsOneWidget);
      expect(
        _textContaining('Review opens after draft material exists'),
        findsOneWidget,
      );

      await _tapDesktopTab(tester, 'Publication');
      expect(_desktopTabFinder('Publication'), findsOneWidget);
      expect(_textContaining('Publication remains optional'), findsOneWidget);
    },
  );

  testWidgets(
    'gather markdown import bdd stages then advances through the workflow',
    (tester) async {
      FilePicker.platform = _FakeFilePicker.singleFile(
        name: 'bus-notes.md',
        bytes: Uint8List.fromList('# Bus Notes'.codeUnits),
      );

      await _pumpWorkstation(
        tester,
        controller: _MarkdownIngressController(success: true),
        initialLocation: '/workstation/research',
        size: const Size(1600, 1100),
      );

      expect(_textContaining('Create the first subject'), findsOneWidget);
      await _tapVisible(tester, find.text('Import Markdown File').first);

      expect(_desktopTabFinder('Review'), findsOneWidget);
      expect(
        _textContaining('Imported markdown into Bus Network Notes.'),
        findsOneWidget,
      );
      expect(_textContaining('Inspect the imported subject'), findsOneWidget);
      expect(find.text('Bus Network Notes'), findsWidgets);
    },
  );

  testWidgets(
    'gather in-panel import action uses the picker flow instead of a dead-end guidance action',
    (tester) async {
      FilePicker.platform = _FakeFilePicker.singleFile(
        name: 'panel-import.md',
        bytes: Uint8List.fromList('# Panel Import'.codeUnits),
      );

      await _pumpWorkstation(
        tester,
        controller: _MarkdownIngressController(success: true),
        initialLocation: '/workstation/research',
        size: const Size(1600, 1100),
      );

      expect(_textContaining('Create the first subject'), findsOneWidget);
      await _tapVisible(tester, find.text('Import Markdown File').last);

      expect(_desktopTabFinder('Review'), findsOneWidget);
      expect(
        find.text(
          'Use Select Markdown File to choose a markdown document for subject intake.',
        ),
        findsNothing,
      );
      expect(find.text('Last Action'), findsOneWidget);
      expect(
        find.text('Imported markdown into Bus Network Notes.'),
        findsWidgets,
      );
      expect(find.text('Do this now'), findsOneWidget);
      expect(find.text('Inspect the imported subject'), findsOneWidget);
    },
  );

  testWidgets(
    'gather markdown import failure keeps gather renderable and retryable',
    (tester) async {
      FilePicker.platform = _FakeFilePicker.singleFile(
        name: 'broken-notes.md',
        bytes: Uint8List.fromList('# Broken Notes'.codeUnits),
      );

      await _pumpWorkstation(
        tester,
        controller: _MarkdownIngressController(success: false),
        initialLocation: '/workstation/research',
        size: const Size(1600, 1100),
      );

      await _tapVisible(tester, find.text('Import Markdown File').first);

      expect(_desktopTabFinder('Gather'), findsOneWidget);
      expect(find.text('Last Action'), findsOneWidget);
      expect(find.text('Markdown upload failed.'), findsOneWidget);
      expect(find.text('Do this now'), findsOneWidget);
      expect(find.text('Markdown ingress is running'), findsOneWidget);
      expect(
        find.text('No subject snapshot is loaded for this phase.'),
        findsNothing,
      );
    },
  );

  testWidgets('flutter gather flow mirrors the textual import approval BDD', (
    tester,
  ) async {
    await _pumpWorkstation(
      tester,
      controller: _ImportApprovalTestController(),
      initialLocation: '/workstation/research',
      size: const Size(1680, 1100),
    );

    expect(_desktopTabFinder('Gather'), findsOneWidget);
    expect(find.text('Check Maintained Files'), findsOneWidget);
    expect(find.text('Select As Import Source'), findsOneWidget);

    await _tapVisible(tester, find.text('Select As Import Source').first);

    expect(find.text('Last Action'), findsOneWidget);
    expect(find.text('Import source selected.'), findsWidgets);
    expect(find.text('Selected Import Source'), findsOneWidget);
    expect(find.text('Import Source Demo'), findsWidgets);

    await _selectDesktopSubject(tester, 'Target Subject Demo');

    expect(find.text('Target Subject Demo'), findsWidgets);
    expect(find.text('Do this now'), findsOneWidget);
    expect(find.text('Create import from the selected source'), findsOneWidget);
    expect(find.text('Create Import From Selected Source'), findsOneWidget);

    await _tapVisible(
      tester,
      find.text('Create Import From Selected Source').first,
    );

    expect(_desktopTabFinder('Review'), findsOneWidget);
    expect(find.text('Preview Pending Import'), findsOneWidget);

    await _tapVisible(tester, find.text('Preview Pending Import').first);

    expect(_desktopTabFinder('Gather'), findsOneWidget);
    expect(find.text('Approve Import'), findsOneWidget);

    await _tapVisible(tester, find.text('Approve Import').first);

    expect(find.text('Last Action'), findsOneWidget);
    expect(find.text('Subject import approved.'), findsWidgets);
    expect(find.text('Reasoning Scope'), findsOneWidget);
    expect(find.text('1 support items from 1'), findsOneWidget);
  });

  testWidgets('gather empty-state follow-up action switches to chat', (
    tester,
  ) async {
    await _pumpWorkstation(
      tester,
      controller: _EmptyStateFollowUpController(),
      initialLocation: '/workstation/research',
      size: const Size(1680, 1100),
    );

    expect(_desktopTabFinder('Gather'), findsOneWidget);
    expect(_gateActionFinder('Ask Follow-up In Chat'), findsOneWidget);

    await _tapGateAction(tester, 'Ask Follow-up In Chat');

    expect(find.text('Workstation · Chat'), findsOneWidget);
    expect(
      find.textContaining('Moved to Chat for a follow-up question.'),
      findsWidgets,
    );
  });

  testWidgets(
    'gather maintained-files check can advance directly to review when the report plan is next',
    (tester) async {
      await _pumpWorkstation(
        tester,
        controller: _CheckMaintainedToReviewController(),
        initialLocation: '/workstation/research',
        size: const Size(1680, 1100),
      );

      expect(_desktopTabFinder('Gather'), findsOneWidget);
      expect(_gateActionFinder('Check Maintained Files'), findsOneWidget);

      await _tapGateAction(tester, 'Check Maintained Files');

      expect(_desktopTabFinder('Review'), findsOneWidget);
      expect(_textContaining('Create the report plan'), findsOneWidget);
      expect(
        _textContaining(
          'The maintained-files check completed and the files are aligned.',
        ),
        findsOneWidget,
      );
      expect(_gateActionFinder('Create Report Plan'), findsOneWidget);
    },
  );

  testWidgets(
    'approved import flow exposes publication import controls after refreshing the report plan',
    (tester) async {
      await _pumpWorkstation(
        tester,
        controller: _PublicationImportBddController(),
        initialLocation: '/workstation/research',
        size: const Size(1680, 1100),
      );

      expect(_desktopTabFinder('Gather'), findsOneWidget);
      await _tapVisible(tester, find.text('Select As Import Source').first);

      await _selectDesktopSubject(tester, 'Meet Greet Depart');
      await _tapVisible(
        tester,
        find.text('Create Import From Selected Source').first,
      );

      expect(_desktopTabFinder('Review'), findsOneWidget);
      await _tapVisible(tester, find.text('Preview Pending Import').first);

      expect(_desktopTabFinder('Gather'), findsOneWidget);
      await _tapVisible(tester, find.text('Approve Import').first);

      await _tapDesktopTab(tester, 'Itemize');
      await _tapGateAction(tester, 'Generate Itemization');

      await _tapDesktopTab(tester, 'Draft');
      await _tapGateAction(tester, 'Create Draft Composition');

      await _tapDesktopTab(tester, 'Review');
      await _tapGateAction(tester, 'Compare Report Plans');

      await _tapDesktopTab(tester, 'Publication');
      await _tapGateAction(tester, 'Refresh Report Plan');

      expect(_selectControlFinder('publication_import_target'), findsOneWidget);
      expect(
        _switchControlFinder('publication_import_included'),
        findsOneWidget,
      );
      expect(_selectControlFinder('publication_import_usage'), findsOneWidget);
      expect(_textContaining('import target | Einstein'), findsWidgets);
      expect(_textContaining('import included | yes'), findsWidgets);
      expect(_textContaining('import usage | dependency_only'), findsWidgets);
    },
  );

  testWidgets(
    'publication import widgets update selected import target included state and usage',
    (tester) async {
      await _pumpWorkstation(
        tester,
        controller: _PublicationImportBddController.multiImportReady(),
        initialLocation: '/workstation/publication',
        size: const Size(1680, 1100),
      );

      expect(_desktopTabFinder('Publication'), findsOneWidget);
      expect(_textContaining('import target | Einstein'), findsWidgets);
      expect(_textContaining('import included | yes'), findsWidgets);
      expect(_textContaining('import usage | dependency_only'), findsWidgets);

      await _selectControlValue(
        tester,
        'publication_import_target',
        'Wikipedia',
      );
      expect(_textContaining('import target | Wikipedia'), findsWidgets);

      await _toggleSwitchControl(tester, 'publication_import_included');
      expect(_textContaining('import included | no'), findsWidgets);

      await _selectControlValue(
        tester,
        'publication_import_usage',
        'Direct quote',
      );
      expect(_textContaining('import usage | direct_quote'), findsWidgets);
    },
  );

  testWidgets('utility tabs render long content without overflow', (
    tester,
  ) async {
    await _pumpWorkstation(
      tester,
      controller: _UtilityTabsController(),
      initialLocation: '/workstation/permissions',
      size: const Size(1480, 1000),
    );

    expect(find.text('Workstation · Permissions'), findsOneWidget);
    expect(find.textContaining('Granted session capabilities'), findsOneWidget);
    expect(
      tester.getSize(find.byType(SelectableText).first).width,
      greaterThan(700),
    );
    expect(tester.takeException(), isNull);

    await tester.tap(find.text('Activity'));
    await tester.pumpAndSettle();
    expect(find.text('Workstation · Activity'), findsOneWidget);
    expect(find.textContaining('Activity feed entry'), findsOneWidget);
    expect(tester.takeException(), isNull);

    await tester.tap(find.text('Skills'));
    await tester.pumpAndSettle();
    expect(find.text('Workstation · Skills'), findsOneWidget);
    expect(find.textContaining('Imported skill 048'), findsOneWidget);
    // Temporary diagnostic: leave rendering exceptions uncaught so Flutter
    // prints the exact overflow site while tightening the narrow-width layout.
  });

  testWidgets(
    'steady-state shells hide persistent connected and stale markdown staging banners',
    (tester) async {
      await _pumpWorkstation(
        tester,
        controller: _SteadyStateBannerController(),
        initialLocation: '/workstation/research',
        size: const Size(1480, 1000),
      );

      expect(_desktopTabFinder('Gather'), findsOneWidget);
      expect(
        find.text('Staged workstation-import.md into imported.'),
        findsNothing,
      );
      expect(find.text('Connected to workstation-root.'), findsNothing);
      expect(find.text('Do this now'), findsOneWidget);
      expect(find.text('Activate this subject'), findsOneWidget);
    },
  );

  testWidgets('layout remains stable on medium desktop widths', (tester) async {
    await _pumpWorkstation(
      tester,
      controller: _ChatBddController(),
      initialLocation: '/workstation/chat',
      size: const Size(1180, 900),
    );

    expect(find.text('Transcript'), findsOneWidget);
    expect(find.text('Suggestions'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('subject layout stacks cleanly on narrower widths', (
    tester,
  ) async {
    await _pumpWorkstation(
      tester,
      controller: _PlaceholderPhaseController(),
      initialLocation: '/workstation/research',
      size: const Size(900, 1100),
    );

    expect(_desktopTabFinder('Gather'), findsOneWidget);
    expect(_textContaining('Create the first subject'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('desktop gather shell renders the textual parity sections', (
    tester,
  ) async {
    await _pumpWorkstation(
      tester,
      controller: _SteadyStateBannerController(),
      initialLocation: '/workstation/research',
      size: const Size(1680, 1000),
    );

    expect(_desktopTabFinder('Gather'), findsOneWidget);
    expect(find.text('Current Step'), findsOneWidget);
    expect(find.text('Subject Status'), findsOneWidget);
    expect(find.text('More Actions'), findsOneWidget);
    expect(find.text('Source Sets'), findsWidgets);
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'structured itemize and draft panes match the textual inventory shell',
    (tester) async {
      await _pumpWorkstation(
        tester,
        controller: _StructuredPaneParityController(),
        initialLocation: '/workstation/itemize',
        size: const Size(1680, 1100),
      );

      expect(_desktopTabFinder('Itemize'), findsOneWidget);
      expect(find.text('Do this now'), findsOneWidget);
      expect(find.text('Orient the selected item'), findsOneWidget);
      expect(
        find.text('Current item: Smart City Travel [claim] status=candidate.'),
        findsOneWidget,
      );
      expect(
        _textContaining('> [c] actor - Banks and the payment processor'),
        findsOneWidget,
      );
      expect(
        _textContaining(
          '[c] objective - changes that can be implemented without disrupting daily service',
        ),
        findsOneWidget,
      );

      await _tapDesktopTab(tester, 'Draft');

      expect(_desktopTabFinder('Draft'), findsOneWidget);
      expect(find.text('Do this now'), findsOneWidget);
      expect(
        find.text('Accept this construct into decision analysis'),
        findsOneWidget,
      );
      expect(find.text('Draft Item Inventory'), findsOneWidget);
      expect(find.text('X'), findsWidgets);
      expect(find.text('Draft Item'), findsOneWidget);
      expect(find.text('Smart City Travel'), findsWidgets);
      expect(find.text('Banks and the payment processor'), findsWidgets);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'prefixed current-step actions execute against their home phase',
    (tester) async {
      await _pumpWorkstation(
        tester,
        controller: _CrossPhaseGateActionController(),
        initialLocation: '/workstation/itemize',
        size: const Size(1680, 1100),
      );

      expect(_desktopTabFinder('Itemize'), findsOneWidget);
      expect(find.text('Check Maintained Files'), findsOneWidget);

      await _tapVisible(
        tester,
        find.widgetWithText(OutlinedButton, 'Check Maintained Files'),
      );

      expect(_desktopTabFinder('Gather'), findsOneWidget);
      expect(find.text('Last Action'), findsOneWidget);
      expect(find.text('Maintained files compared.'), findsWidgets);
      expect(find.text('Itemization remains ready for Draft.'), findsWidgets);
    },
  );

  testWidgets(
    'weak prose v10 draft later row keeps start decision analysis primary',
    (tester) async {
      await _pumpWorkstation(
        tester,
        controller: _WorkflowBddParityController(
          _WorkflowBddScenario.weakProseV10DraftLaterRow,
        ),
        initialLocation: '/workstation/draft',
        size: const Size(1680, 1100),
      );

      expect(_desktopTabFinder('Draft'), findsOneWidget);
      expect(find.text('Start decision analysis'), findsOneWidget);
      expect(_gateActionFinder('Start Decision Analysis'), findsOneWidget);
      expect(_gateActionFinder('Include In Decision Analysis'), findsNothing);
      expect(_gateActionFinder('Run Decision Analysis'), findsNothing);
    },
  );

  testWidgets(
    'same-subject v2 then v10 draft later row keeps refresh dst analysis primary',
    (tester) async {
      await _pumpWorkstation(
        tester,
        controller: _WorkflowBddParityController(
          _WorkflowBddScenario.sameSubjectV2ThenV10DraftLaterNonincludedRow,
        ),
        initialLocation: '/workstation/draft',
        size: const Size(1680, 1100),
      );

      expect(_desktopTabFinder('Draft'), findsOneWidget);
      expect(
        _textContaining('Refresh the DST-backed decision analysis'),
        findsOneWidget,
      );
      expect(_gateActionFinder('Refresh DST Analysis'), findsOneWidget);
      expect(_gateActionFinder('Include In Decision Analysis'), findsNothing);
      expect(_gateActionFinder('Hand To Review'), findsNothing);
    },
  );

  testWidgets(
    'weak prose v10 review and publication route back to start decision analysis',
    (tester) async {
      await _pumpWorkstation(
        tester,
        controller: _WorkflowBddParityController(
          _WorkflowBddScenario.weakProseV10ReviewPublicationBeforeAnalysis,
        ),
        initialLocation: '/workstation/review',
        size: const Size(1680, 1100),
      );

      expect(_desktopTabFinder('Review'), findsOneWidget);
      expect(_textContaining('Start decision analysis'), findsOneWidget);
      expect(_gateActionFinder('Start Decision Analysis'), findsOneWidget);
      expect(_gateActionFinder('Approve For Report'), findsNothing);

      await _tapDesktopTab(tester, 'Publication');

      expect(_desktopTabFinder('Publication'), findsOneWidget);
      expect(_textContaining('Start decision analysis'), findsOneWidget);
      expect(_gateActionFinder('Start Decision Analysis'), findsOneWidget);
      expect(_gateActionFinder('Lock Report Inputs'), findsNothing);
      expect(_gateActionFinder('Build Report'), findsNothing);
    },
  );

  testWidgets(
    'same-subject v2 then v10 review and publication route back to refresh dst analysis',
    (tester) async {
      await _pumpWorkstation(
        tester,
        controller: _WorkflowBddParityController(
          _WorkflowBddScenario
              .sameSubjectV2ThenV10ReviewPublicationAfterPriorAnalysis,
        ),
        initialLocation: '/workstation/review',
        size: const Size(1680, 1100),
      );

      expect(_desktopTabFinder('Review'), findsOneWidget);
      expect(
        _textContaining('Refresh the DST-backed decision analysis'),
        findsOneWidget,
      );
      expect(_gateActionFinder('Refresh DST Analysis'), findsOneWidget);
      expect(_gateActionFinder('Approve For Report'), findsNothing);

      await _tapDesktopTab(tester, 'Publication');

      expect(_desktopTabFinder('Publication'), findsOneWidget);
      expect(
        _textContaining('Refresh the DST-backed decision analysis'),
        findsOneWidget,
      );
      expect(_gateActionFinder('Refresh DST Analysis'), findsOneWidget);
      expect(_gateActionFinder('Lock Report Inputs'), findsNothing);
      expect(_gateActionFinder('Build Report'), findsNothing);
    },
  );

  testWidgets(
    'weak prose after construct suggestion shows start decision analysis and open model',
    (tester) async {
      await _pumpWorkstation(
        tester,
        controller: _WorkflowBddParityController(
          _WorkflowBddScenario.weakProseAfterConstructSuggestion,
        ),
        initialLocation: '/workstation/draft',
        size: const Size(1680, 1100),
      );

      expect(_desktopTabFinder('Draft'), findsOneWidget);
      expect(find.text('Start decision analysis'), findsOneWidget);
      expect(_gateActionFinder('Start Decision Analysis'), findsOneWidget);
      expect(_gateActionFinder('Open Model'), findsOneWidget);
      _expectActionOrderLeftToRight(
        tester,
        'Start Decision Analysis',
        'Open Model',
      );
      expect(_gateActionFinder('Hand To Review'), findsNothing);
    },
  );

  testWidgets(
    'same-subject v2 then v10 draft toggle stays responsive on a later nonincluded row',
    (tester) async {
      await _pumpWorkstation(
        tester,
        controller: _WorkflowBddParityController(
          _WorkflowBddScenario.sameSubjectV2ThenV10DraftLaterNonincludedRow,
        ),
        initialLocation: '/workstation/draft',
        size: const Size(1680, 1100),
      );

      expect(find.text('Draft detail key: draft-v10-gap'), findsOneWidget);
      expect(
        find.byKey(const ValueKey<String>('row-checkbox:draft_scope_tree:0')),
        findsOneWidget,
      );

      await _tapVisible(
        tester,
        _interactivePaneRowFinder('draft_scope_tree', 2),
      );
      expect(find.text('Draft detail key: draft-v10-fallback'), findsOneWidget);
      expect(
        _textContaining('selected in decision frame | no'),
        findsOneWidget,
      );

      await tester.tap(find.text('Draft detail key: draft-v10-fallback'));
      await tester.pumpAndSettle();
      await tester.sendKeyEvent(LogicalKeyboardKey.keyD);
      await tester.pumpAndSettle();

      expect(
        _textContaining('selected in decision frame | yes'),
        findsOneWidget,
      );
      expect(
        find.descendant(
          of: find.byKey(
            const ValueKey<String>('row-checkbox:draft_scope_tree:0'),
          ),
          matching: find.byIcon(Icons.check_rounded),
        ),
        findsOneWidget,
      );
      expect(
        find.descendant(
          of: find.byKey(
            const ValueKey<String>('row-checkbox:draft_scope_tree:2'),
          ),
          matching: find.byIcon(Icons.check_rounded),
        ),
        findsOneWidget,
      );
      expect(
        find.descendant(
          of: find.byKey(
            const ValueKey<String>('row-checkbox:draft_scope_tree:1'),
          ),
          matching: find.byIcon(Icons.check_rounded),
        ),
        findsNothing,
      );
    },
  );

  testWidgets('dst happy path steps from start to run to approve for report', (
    tester,
  ) async {
    await _pumpWorkstation(
      tester,
      controller: _WorkflowBddParityController(
        _WorkflowBddScenario.dstHappyPath,
      ),
      initialLocation: '/workstation/draft',
      size: const Size(1680, 1100),
    );

    expect(_desktopTabFinder('Draft'), findsOneWidget);
    expect(_gateActionFinder('Start Decision Analysis'), findsOneWidget);
    expect(_gateActionFinder('Run Decision Analysis'), findsNothing);

    await _tapGateAction(tester, 'Start Decision Analysis');

    expect(_desktopTabFinder('Draft'), findsOneWidget);
    expect(_gateActionFinder('Run Decision Analysis'), findsOneWidget);
    expect(_gateActionFinder('Start Decision Analysis'), findsNothing);

    await _tapGateAction(tester, 'Run Decision Analysis');

    expect(_desktopTabFinder('Review'), findsOneWidget);
    expect(_gateActionFinder('Approve For Report'), findsOneWidget);
    expect(
      _textContaining('Approve the report and decision analysis'),
      findsOneWidget,
    );
  });

  testWidgets(
    'draft after decision analysis completion keeps rerun and open model available',
    (tester) async {
      await _pumpWorkstation(
        tester,
        controller: _WorkflowBddParityController(
          _WorkflowBddScenario.dstApprovedDraft,
        ),
        initialLocation: '/workstation/draft',
        size: const Size(1680, 1100),
      );

      expect(_desktopTabFinder('Draft'), findsOneWidget);
      expect(_textContaining('Decision analysis is ready'), findsOneWidget);
      expect(_gateActionFinder('Re-run Analysis (Balanced)'), findsOneWidget);
      expect(_gateActionFinder('Open Model'), findsOneWidget);
      _expectActionOrderLeftToRight(
        tester,
        'Re-run Analysis (Balanced)',
        'Open Model',
      );
      expect(find.textContaining('Role ('), findsNothing);

      await _tapGateAction(tester, 'Open Model');

      expect(find.text('Transformation Model'), findsWidgets);
      expect(find.text('Case Objects'), findsWidgets);
      expect(_textContaining('Moved Draft focus to Model.'), findsOneWidget);
    },
  );

  testWidgets(
    'review and publication keep open model as a draft phase-nav and return to draft compose',
    (tester) async {
      await _pumpWorkstation(
        tester,
        controller: _WorkflowBddParityController(
          _WorkflowBddScenario.dstReviewPublicationOpenModel,
        ),
        initialLocation: '/workstation/review',
        size: const Size(1680, 1100),
      );

      expect(_desktopTabFinder('Review'), findsOneWidget);
      expect(find.text('Draft'), findsOneWidget);
      expect(_gateActionFinder('Open Model'), findsOneWidget);
      expect(_gateActionFinder('Approve For Report'), findsOneWidget);

      await _tapGateAction(tester, 'Open Model');

      expect(_desktopTabFinder('Draft'), findsOneWidget);
      expect(find.text('Draft Item Inventory'), findsOneWidget);
      expect(find.text('Transformation Model'), findsNothing);
      expect(_textContaining('Moved Draft focus to Model.'), findsNothing);
      expect(_gateActionFinder('Open Model'), findsOneWidget);

      await _tapDesktopTab(tester, 'Publication');

      expect(_desktopTabFinder('Publication'), findsOneWidget);
      expect(find.text('Draft'), findsOneWidget);
      expect(_gateActionFinder('Open Model'), findsOneWidget);
      expect(_gateActionFinder('Build Report'), findsOneWidget);
      final buildReportTop = tester
          .getTopLeft(_gateActionFinder('Build Report').first)
          .dy;
      final openModelTop = tester
          .getTopLeft(_gateActionFinder('Open Model').first)
          .dy;
      expect(buildReportTop, openModelTop);

      await _tapGateAction(tester, 'Open Model');

      expect(_desktopTabFinder('Draft'), findsOneWidget);
      expect(find.text('Draft Item Inventory'), findsOneWidget);
      expect(find.text('Transformation Model'), findsNothing);
      expect(_textContaining('Moved Draft focus to Model.'), findsNothing);
      expect(_gateActionFinder('Open Model'), findsOneWidget);
    },
  );

  testWidgets(
    'built publication actions keep open model available with artifact actions',
    (tester) async {
      await _pumpWorkstation(
        tester,
        controller: _WorkflowBddParityController(
          _WorkflowBddScenario.dstBuiltPublicationOpenModel,
        ),
        initialLocation: '/workstation/publication',
        size: const Size(1680, 1100),
      );

      expect(_desktopTabFinder('Publication'), findsOneWidget);
      expect(find.text('Draft'), findsOneWidget);
      expect(_gateActionFinder('Open Model'), findsOneWidget);
      expect(find.text('Preview report.pdf'), findsOneWidget);
      expect(find.text('Open Release Folder'), findsOneWidget);
      expect(find.text('Rebuild Report'), findsOneWidget);
      _expectGateActionDisabled(tester, 'Open Release Folder');

      await _tapGateAction(tester, 'Open Model');

      expect(_desktopTabFinder('Draft'), findsOneWidget);
      expect(find.text('Draft Item Inventory'), findsOneWidget);
      expect(find.text('Transformation Model'), findsNothing);
      expect(_textContaining('Moved Draft focus to Model.'), findsNothing);
      expect(_gateActionFinder('Open Model'), findsOneWidget);
    },
  );

  testWidgets(
    'publication more actions keep build report visible when the action key is plain build_report',
    (tester) async {
      await _pumpWorkstation(
        tester,
        controller: _PublicationBuildMoreActionController(),
        initialLocation: '/workstation/publication',
        size: const Size(1680, 1100),
      );

      expect(_desktopTabFinder('Publication'), findsOneWidget);
      expect(_gateActionFinder('Build Report'), findsOneWidget);
      expect(_gateActionFinder('Preview Report Plan Diff'), findsOneWidget);
    },
  );

  testWidgets('draft lens tabs switch between frame model and explore shells', (
    tester,
  ) async {
    await _pumpWorkstation(
      tester,
      controller: _DraftLensTransitionController(),
      initialLocation: '/workstation/draft',
      size: const Size(1680, 1100),
    );

    expect(_desktopTabFinder('Draft'), findsOneWidget);
    await _tapVisible(
      tester,
      find.widgetWithText(OutlinedButton, 'Open Model'),
    );

    expect(
      find.byKey(const ValueKey<String>('draft-lens-model')),
      findsOneWidget,
    );
    expect(find.text('Transformation Model'), findsWidgets);

    final frameLens = find.byKey(const ValueKey<String>('draft-lens-frame'));
    await tester.ensureVisible(frameLens);
    await tester.tap(frameLens);
    await tester.pumpAndSettle();
    expect(find.text('Case Frame'), findsWidgets);

    final exploreLens = find.byKey(
      const ValueKey<String>('draft-lens-explore'),
    );
    await tester.ensureVisible(exploreLens);
    await tester.tap(exploreLens);
    await tester.pumpAndSettle();
    expect(find.text('Explore Alternatives'), findsWidgets);

    final modelLens = find.byKey(const ValueKey<String>('draft-lens-model'));
    await tester.ensureVisible(modelLens);
    await tester.tap(modelLens);
    await tester.pumpAndSettle();
    expect(find.text('Transformation Model'), findsWidgets);
    expect(find.text('Issues & Validation'), findsWidgets);
  });

  testWidgets(
    'itemize inventory rows and pane-scope shortcuts drive the detail pane',
    (tester) async {
      final controller = _InteractivePaneParityController();
      await _pumpWorkstation(
        tester,
        controller: controller,
        initialLocation: '/workstation/itemize',
        size: const Size(1680, 1100),
      );

      expect(find.text('Item detail key: itemize-banks'), findsOneWidget);
      await tester.tap(_interactivePaneRowFinder('itemize_inventory', 1));
      await tester.pumpAndSettle();
      expect(find.text('Item detail key: itemize-objective'), findsOneWidget);

      await tester.tap(find.text('Item detail key: itemize-objective'));
      await tester.pumpAndSettle();
      controller.clearLogs();
      await tester.sendKeyEvent(LogicalKeyboardKey.arrowDown);
      await tester.pumpAndSettle();
      expect(controller.lastInteractionKey, 'move_itemize_cursor');
      expect(controller.lastInteractionDelta, 1);
      expect(find.text('Item detail key: itemize-regulator'), findsOneWidget);

      controller.clearLogs();
      await tester.sendKeyEvent(LogicalKeyboardKey.enter);
      await tester.pumpAndSettle();
      expect(
        controller.appliedActionKeys.last,
        'preview_selected_itemized_item',
      );

      controller.clearLogs();
      await tester.sendKeyEvent(LogicalKeyboardKey.keyH);
      await tester.pumpAndSettle();
      expect(controller.appliedActionKeys.last, 'hold_selected_itemized_item');
    },
  );

  testWidgets(
    'draft compose inventory rows and pane-scope shortcuts drive the detail pane',
    (tester) async {
      final controller = _InteractivePaneParityController();
      await _pumpWorkstation(
        tester,
        controller: controller,
        initialLocation: '/workstation/draft',
        size: const Size(1680, 1100),
      );

      expect(find.text('Draft detail key: draft-transit'), findsOneWidget);
      await tester.tap(_interactivePaneRowFinder('draft_scope_tree', 1));
      await tester.pumpAndSettle();
      expect(find.text('Draft detail key: draft-banks'), findsOneWidget);

      await tester.tap(find.text('Draft detail key: draft-banks'));
      await tester.pumpAndSettle();
      controller.clearLogs();
      await tester.sendKeyEvent(LogicalKeyboardKey.arrowDown);
      await tester.pumpAndSettle();
      expect(controller.lastInteractionKey, 'move_draft_review_cursor');
      expect(controller.lastInteractionDelta, 1);
      expect(find.text('Draft detail key: draft-regulator'), findsOneWidget);

      controller.clearLogs();
      await tester.sendKeyDownEvent(LogicalKeyboardKey.shiftLeft);
      await tester.sendKeyEvent(LogicalKeyboardKey.arrowUp);
      await tester.sendKeyUpEvent(LogicalKeyboardKey.shiftLeft);
      await tester.pumpAndSettle();
      expect(
        controller.appliedActionKeys.last,
        'move_selected_draft_review_item_earlier',
      );

      controller.clearLogs();
      await tester.sendKeyEvent(LogicalKeyboardKey.keyD);
      await tester.pumpAndSettle();
      expect(
        controller.appliedActionKeys.last,
        'toggle_selected_draft_review_item_in_decision_frame',
      );
    },
  );

  testWidgets(
    'draft lens case objects stay interactive while the active lens changes',
    (tester) async {
      final controller = _InteractivePaneParityController();
      await _pumpWorkstation(
        tester,
        controller: controller,
        initialLocation: '/workstation/draft',
        size: const Size(1680, 1100),
      );

      await _tapVisible(
        tester,
        find.widgetWithText(OutlinedButton, 'Open Model'),
      );
      expect(find.text('Transformation Model'), findsWidgets);

      await _tapVisible(
        tester,
        _interactivePaneRowFinder('draft_scope_tree', 1),
      );
      expect(find.text('Case detail key: case-banks'), findsOneWidget);
      expect(find.text('Transformation Model'), findsWidgets);

      await tester.tap(find.byKey(const ValueKey<String>('draft-lens-frame')));
      await tester.pumpAndSettle();
      expect(find.text('Case Frame'), findsWidgets);
      expect(find.text('Case detail key: case-banks'), findsOneWidget);

      await _tapVisible(
        tester,
        _interactivePaneRowFinder('draft_scope_tree', 2),
      );
      expect(find.text('Case detail key: case-regulator'), findsOneWidget);
      expect(find.text('Case Frame'), findsWidgets);

      await tester.tap(
        find.byKey(const ValueKey<String>('draft-lens-explore')),
      );
      await tester.pumpAndSettle();
      expect(find.text('Explore Alternatives'), findsWidgets);
      expect(find.text('Case detail key: case-regulator'), findsOneWidget);
    },
  );

  testWidgets(
    'review scope rows and shared shortcuts drive selection details',
    (tester) async {
      final controller = _InteractivePaneParityController();
      await _pumpWorkstation(
        tester,
        controller: controller,
        initialLocation: '/workstation/review',
        size: const Size(1680, 1100),
      );

      expect(find.text('Review detail key: review-summary'), findsOneWidget);
      await tester.tap(_interactivePaneRowFinder('review_scope_tree', 1));
      await tester.pumpAndSettle();
      expect(find.text('Review detail key: review-actors'), findsOneWidget);

      await tester.tap(find.text('Review detail key: review-actors'));
      await tester.pumpAndSettle();
      controller.clearLogs();
      await tester.sendKeyEvent(LogicalKeyboardKey.arrowDown);
      await tester.pumpAndSettle();
      expect(controller.lastInteractionKey, 'move_report_scope_cursor');
      expect(controller.lastInteractionDelta, 1);
      expect(find.text('Review detail key: review-banks'), findsOneWidget);

      controller.clearLogs();
      await tester.sendKeyEvent(LogicalKeyboardKey.enter);
      await tester.pumpAndSettle();
      expect(
        controller.appliedActionKeys.last,
        'preview_selected_report_scope_item',
      );

      controller.clearLogs();
      await tester.sendKeyEvent(LogicalKeyboardKey.keyH);
      await tester.pumpAndSettle();
      expect(
        controller.appliedActionKeys.last,
        'hold_selected_report_scope_item',
      );

      controller.clearLogs();
      await tester.sendKeyEvent(LogicalKeyboardKey.keyX);
      await tester.pumpAndSettle();
      expect(
        controller.appliedActionKeys.last,
        'toggle_selected_report_scope_item',
      );

      controller.clearLogs();
      await tester.sendKeyEvent(LogicalKeyboardKey.keyR);
      await tester.pumpAndSettle();
      expect(
        controller.appliedActionKeys.last,
        'release_held_report_scope_items',
      );

      controller.clearLogs();
      await tester.sendKeyDownEvent(LogicalKeyboardKey.shiftLeft);
      await tester.sendKeyEvent(LogicalKeyboardKey.arrowUp);
      await tester.sendKeyUpEvent(LogicalKeyboardKey.shiftLeft);
      await tester.pumpAndSettle();
      expect(
        controller.lastInteractionKey,
        'preview_move_held_report_scope_items',
      );
      expect(controller.lastInteractionDelta, -1);

      controller.clearLogs();
      await tester.sendKeyEvent(LogicalKeyboardKey.keyJ);
      await tester.pumpAndSettle();
      expect(
        controller.lastInteractionKey,
        'preview_move_held_report_scope_items',
      );
      expect(controller.lastInteractionDelta, 1);
    },
  );

  testWidgets(
    'publication scope rows and shared shortcuts drive selection details',
    (tester) async {
      final controller = _InteractivePaneParityController();
      await _pumpWorkstation(
        tester,
        controller: controller,
        initialLocation: '/workstation/publication',
        size: const Size(1680, 1100),
      );

      expect(
        find.text('Publication detail key: publication-summary'),
        findsOneWidget,
      );
      await tester.tap(_interactivePaneRowFinder('publication_scope_tree', 1));
      await tester.pumpAndSettle();
      expect(
        find.text('Publication detail key: publication-support'),
        findsOneWidget,
      );

      await tester.tap(
        find.text('Publication detail key: publication-support'),
      );
      await tester.pumpAndSettle();
      controller.clearLogs();
      await tester.sendKeyEvent(LogicalKeyboardKey.arrowDown);
      await tester.pumpAndSettle();
      expect(controller.lastInteractionKey, 'move_report_scope_cursor');
      expect(controller.lastInteractionDelta, 1);
      expect(
        find.text('Publication detail key: publication-release'),
        findsOneWidget,
      );

      controller.clearLogs();
      await tester.sendKeyEvent(LogicalKeyboardKey.keyX);
      await tester.pumpAndSettle();
      expect(
        controller.appliedActionKeys.last,
        'toggle_selected_report_scope_item',
      );

      controller.clearLogs();
      await tester.sendKeyEvent(LogicalKeyboardKey.keyK);
      await tester.pumpAndSettle();
      expect(
        controller.lastInteractionKey,
        'preview_move_held_report_scope_items',
      );
      expect(controller.lastInteractionDelta, -1);
    },
  );

  testWidgets(
    'more actions select and switch controls dispatch existing workflow actions',
    (tester) async {
      final controller = _InteractiveControlParityController();
      await _pumpWorkstation(
        tester,
        controller: controller,
        initialLocation: '/workstation/draft',
        size: const Size(1680, 1100),
      );

      await tester.tap(
        find.byKey(
          const ValueKey<String>('select-control:draft_semantic_kind'),
        ),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.text('Definition').last);
      await tester.pumpAndSettle();
      expect(
        controller.appliedActionKeys,
        contains('set_selected_draft_review_semantic_kind:definition'),
      );

      await tester.tap(
        find.byKey(
          const ValueKey<String>('switch-control:draft_decision_included'),
        ),
      );
      await tester.pumpAndSettle();
      expect(
        controller.appliedActionKeys,
        contains('toggle_selected_draft_review_item_in_decision_frame'),
      );
    },
  );

  testWidgets(
    'draft pane checkbox toggles the selected item and stays in sync with the outer switch',
    (tester) async {
      final controller = _InteractiveControlParityController();
      await _pumpWorkstation(
        tester,
        controller: controller,
        initialLocation: '/workstation/draft',
        size: const Size(1680, 1100),
      );

      expect(
        find.descendant(
          of: find.byKey(
            const ValueKey<String>('switch-control:draft_decision_included'),
          ),
          matching: find.byIcon(Icons.check_rounded),
        ),
        findsOneWidget,
      );
      expect(
        find.descendant(
          of: find.byKey(
            const ValueKey<String>('row-checkbox:draft_scope_tree:0'),
          ),
          matching: find.byIcon(Icons.check_rounded),
        ),
        findsOneWidget,
      );

      await tester.tap(
        find.byKey(const ValueKey<String>('row-checkbox:draft_scope_tree:0')),
      );
      await tester.pumpAndSettle();

      expect(
        controller.appliedActionKeys.last,
        'toggle_selected_draft_review_item_in_decision_frame',
      );
      expect(
        find.descendant(
          of: find.byKey(
            const ValueKey<String>('switch-control:draft_decision_included'),
          ),
          matching: find.byIcon(Icons.check_rounded),
        ),
        findsNothing,
      );
      expect(
        find.descendant(
          of: find.byKey(
            const ValueKey<String>('row-checkbox:draft_scope_tree:0'),
          ),
          matching: find.byIcon(Icons.check_rounded),
        ),
        findsNothing,
      );
      expect(
        _textContaining('selected in decision frame | no'),
        findsOneWidget,
      );
    },
  );

  testWidgets(
    'draft pane checkbox on another row selects it first and then syncs the outer switch',
    (tester) async {
      final controller = _InteractiveControlParityController();
      await _pumpWorkstation(
        tester,
        controller: controller,
        initialLocation: '/workstation/draft',
        size: const Size(1680, 1100),
      );

      await tester.tap(
        find.byKey(const ValueKey<String>('row-checkbox:draft_scope_tree:1')),
      );
      await tester.pumpAndSettle();

      expect(
        controller.appliedActionKeys.last,
        'toggle_selected_draft_review_item_in_decision_frame',
      );
      expect(find.text('Banks and the payment processor'), findsWidgets);
      expect(
        find.descendant(
          of: find.byKey(
            const ValueKey<String>('switch-control:draft_decision_included'),
          ),
          matching: find.byIcon(Icons.check_rounded),
        ),
        findsOneWidget,
      );
      expect(
        find.descendant(
          of: find.byKey(
            const ValueKey<String>('row-checkbox:draft_scope_tree:1'),
          ),
          matching: find.byIcon(Icons.check_rounded),
        ),
        findsOneWidget,
      );
      expect(
        _textContaining('selected in decision frame | yes'),
        findsOneWidget,
      );
    },
  );

  testWidgets(
    'report scope pane checkbox selects the row and dispatches the report-scope toggle action',
    (tester) async {
      final controller = _InteractivePaneParityController();
      await _pumpWorkstation(
        tester,
        controller: controller,
        initialLocation: '/workstation/review',
        size: const Size(1680, 1100),
      );

      controller.clearLogs();
      await tester.tap(
        find.byKey(const ValueKey<String>('row-checkbox:review_scope_tree:1')),
      );
      await tester.pumpAndSettle();

      expect(controller.lastInteractionKey, 'move_report_scope_cursor');
      expect(controller.lastInteractionDelta, 1);
      expect(
        controller.appliedActionKeys.last,
        'toggle_selected_report_scope_item',
      );
      expect(find.text('Review detail key: review-actors'), findsOneWidget);
    },
  );

  testWidgets(
    'checkbox-like draft and report scope rows render inline checkbox widgets',
    (tester) async {
      await _pumpWorkstation(
        tester,
        controller: _InteractiveControlParityController(),
        initialLocation: '/workstation/draft',
        size: const Size(1680, 1100),
      );

      expect(
        find.byKey(const ValueKey<String>('row-checkbox:draft_scope_tree:0')),
        findsOneWidget,
      );
      expect(
        find.byKey(const ValueKey<String>('row-checkbox:draft_scope_tree:1')),
        findsOneWidget,
      );

      await _pumpWorkstation(
        tester,
        controller: _InteractivePaneParityController(),
        initialLocation: '/workstation/review',
        size: const Size(1680, 1100),
      );

      expect(find.byIcon(Icons.check_rounded), findsWidgets);
    },
  );

  testWidgets('current step gate section no longer renders a visible border', (
    tester,
  ) async {
    await _pumpWorkstation(
      tester,
      controller: _InteractiveControlParityController(),
      initialLocation: '/workstation/draft',
      size: const Size(1680, 1100),
    );

    final section = tester.widget<Container>(
      find.byKey(const ValueKey<String>('gate-section:Current Step')),
    );
    final decoration = section.decoration! as BoxDecoration;
    expect(decoration.border, isNotNull);
    final border = decoration.border! as Border;
    expect(border.top.color, Colors.transparent);
    expect(border.right.color, Colors.transparent);
    expect(border.bottom.color, Colors.transparent);
    expect(border.left.color, Colors.transparent);
  });

  test('layout spec parses pane height scroll and wrap metadata', () {
    final layout = _testLayout();
    final research = layout.tabForKey('research');
    final actions = research.paneForKey('actions')!;
    final progress = research.paneForKey('progress')!;
    final learning = research.paneForKey('learning')!;

    expect(actions.width, 'fill');
    expect(actions.heightMode, 'content');
    expect(actions.minHeightUnits, 4);
    expect(actions.scrollX, isFalse);
    expect(actions.scrollY, isFalse);
    expect(actions.wrap, isFalse);

    expect(progress.heightMode, 'content');
    expect(progress.minHeightUnits, 2);
    expect(progress.wrap, isTrue);

    expect(learning.heightMode, 'fill');
    expect(learning.scrollY, isTrue);
    expect(learning.wrap, isTrue);
  });

  testWidgets('wrapper focus drives maximize and info for the active pane', (
    tester,
  ) async {
    await _pumpWorkstation(
      tester,
      controller: _InteractivePaneParityController(),
      initialLocation: '/workstation/itemize',
      size: const Size(1680, 1100),
    );

    await _tapVisible(tester, _paneFrameFinder('itemize_detail'));
    await tester.sendKeyEvent(LogicalKeyboardKey.f8);
    await tester.pumpAndSettle();
    expect(_paneFrameFinder('itemize_inventory'), findsNothing);
    expect(_paneFrameFinder('itemize_detail'), findsOneWidget);

    await tester.sendKeyEvent(LogicalKeyboardKey.f8);
    await tester.pumpAndSettle();
    expect(_paneFrameFinder('itemize_inventory'), findsOneWidget);

    await _tapVisible(tester, _paneFrameFinder('itemize_inventory'));
    await tester.sendKeyEvent(LogicalKeyboardKey.keyI);
    await tester.pumpAndSettle();
    expect(find.text('Help · Item Inventory'), findsOneWidget);
    expect(
      _textContaining('Click a row to select it directly.'),
      findsOneWidget,
    );

    await tester.sendKeyEvent(LogicalKeyboardKey.keyI);
    await tester.pumpAndSettle();
    expect(find.text('Help · Item Inventory'), findsNothing);
    expect(find.text('Item Inventory'), findsWidgets);
  });

  testWidgets(
    'detached review scope pane stays interactive and restores selection details',
    (tester) async {
      await _pumpWorkstation(
        tester,
        controller: _InteractivePaneParityController(),
        initialLocation: '/workstation/review',
        size: const Size(1680, 1100),
      );

      await _tapVisible(tester, _paneFrameFinder('review_scope_tree'));
      await tester.sendKeyEvent(LogicalKeyboardKey.f8);
      await tester.pumpAndSettle();
      expect(_paneFrameFinder('review_scope_detail'), findsNothing);

      await _tapVisible(
        tester,
        _interactivePaneRowFinder('review_scope_tree', 1),
      );
      await tester.sendKeyEvent(LogicalKeyboardKey.f8);
      await tester.pumpAndSettle();

      expect(_paneFrameFinder('review_scope_detail'), findsOneWidget);
      expect(find.text('Review detail key: review-actors'), findsOneWidget);
    },
  );

  testWidgets(
    'draft model layout remains bounded with both upper and lower panes visible',
    (tester) async {
      await _pumpWorkstation(
        tester,
        controller: _InteractivePaneParityController(),
        initialLocation: '/workstation/draft',
        size: const Size(1680, 900),
      );

      await _tapVisible(
        tester,
        find.widgetWithText(OutlinedButton, 'Open Model'),
      );

      final scopeRect = tester.getRect(_paneFrameFinder('draft_scope_tree'));
      final issuesRect = tester.getRect(_paneFrameFinder('draft_result'));

      expect(find.text('Transformation Model'), findsWidgets);
      expect(find.text('Issues & Validation'), findsWidgets);
      expect(scopeRect.top, lessThan(issuesRect.top));
      expect(issuesRect.bottom, lessThanOrEqualTo(900));
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('review scope tree scroll stays local to its pane', (
    tester,
  ) async {
    await _pumpWorkstation(
      tester,
      controller: _InteractivePaneParityController(),
      initialLocation: '/workstation/review',
      size: const Size(1680, 680),
    );

    final scopeScrollableFinder = find.descendant(
      of: _paneScrollFinder('review_scope_tree'),
      matching: find.byType(Scrollable),
    );
    final detailScrollableFinder = find.descendant(
      of: _paneScrollFinder('review_scope_detail'),
      matching: find.byType(Scrollable),
    );

    final scopeScrollableBefore = tester.state<ScrollableState>(
      scopeScrollableFinder,
    );
    final detailScrollableBefore = tester.state<ScrollableState>(
      detailScrollableFinder,
    );

    expect(scopeScrollableBefore.position.pixels, 0);
    expect(detailScrollableBefore.position.pixels, 0);

    await tester.drag(
      _paneScrollFinder('review_scope_tree'),
      const Offset(0, -240),
    );
    await tester.pumpAndSettle();

    final scopeScrollableAfter = tester.state<ScrollableState>(
      scopeScrollableFinder,
    );
    final detailScrollableAfter = tester.state<ScrollableState>(
      detailScrollableFinder,
    );

    expect(scopeScrollableAfter.position.pixels, greaterThan(0));
    expect(detailScrollableAfter.position.pixels, 0);
  });

  test('watch-error filtering ignores expected browser abort noise', () {
    expect(
      isIgnorableWorkstationWatchError(
        'gRPC Error (code: 14, codeName: UNAVAILABLE, message: Request failed with status: 0, details: null, rawResponse: )',
      ),
      isTrue,
    );
    expect(
      isIgnorableWorkstationWatchError(
        'GrpcError: code 1, codeName: CANCELLED, message: stream cancelled',
      ),
      isTrue,
    );
    expect(
      isIgnorableWorkstationWatchError(
        'gRPC Error (code: 13, codeName: INTERNAL, message: database unavailable)',
      ),
      isFalse,
    );
  });

  test(
    'connected shell banner filtering hides only low-signal steady-state notices',
    () {
      expect(
        shouldShowConnectedShellBanner(
          statusText: 'Connected to workstation-root.',
          errorText: null,
          markdownIngressBusy: false,
          subjectBusy: false,
        ),
        isFalse,
      );
      expect(
        shouldShowConnectedShellBanner(
          statusText: 'Staged markdown source for Transit Signals.',
          errorText: null,
          markdownIngressBusy: false,
          subjectBusy: false,
        ),
        isFalse,
      );
      expect(
        shouldShowConnectedShellBanner(
          statusText: 'Staged workstation-import.md into imported.',
          errorText: null,
          markdownIngressBusy: false,
          subjectBusy: false,
        ),
        isFalse,
      );
      expect(
        shouldShowConnectedShellBanner(
          statusText: 'Markdown upload staged.',
          errorText: null,
          markdownIngressBusy: false,
          subjectBusy: false,
        ),
        isFalse,
      );
      expect(
        shouldShowConnectedShellBanner(
          statusText: 'Imported bus-notes.md into transit-signals.',
          errorText: null,
          markdownIngressBusy: false,
          subjectBusy: false,
        ),
        isTrue,
      );
      expect(
        shouldShowConnectedShellBanner(
          statusText: 'Connected to workstation-root.',
          errorText: 'workflow failed',
          markdownIngressBusy: false,
          subjectBusy: false,
        ),
        isTrue,
      );
    },
  );

  test(
    'subject shell last action text hides only low-signal steady-state notices',
    () {
      expect(
        subjectShellLastActionText(
          statusText: 'Connected to workstation-root.',
          markdownIngressBusy: false,
          subjectBusy: false,
        ),
        isEmpty,
      );
      expect(
        subjectShellLastActionText(
          statusText: 'Staged workstation-import.md into imported.',
          markdownIngressBusy: false,
          subjectBusy: false,
        ),
        isEmpty,
      );
      expect(
        subjectShellLastActionText(
          statusText: 'Markdown upload staged.',
          markdownIngressBusy: false,
          subjectBusy: false,
        ),
        isEmpty,
      );
      expect(
        subjectShellLastActionText(
          statusText: 'Applying workflow action...',
          markdownIngressBusy: false,
          subjectBusy: true,
        ),
        'Applying workflow action...',
      );
      expect(
        subjectShellLastActionText(
          statusText: 'Subject import approved.',
          markdownIngressBusy: false,
          subjectBusy: false,
        ),
        'Subject import approved.',
      );
    },
  );
}

Future<void> _pumpWorkstation(
  WidgetTester tester, {
  required WorkstationController controller,
  required String initialLocation,
  required Size size,
}) async {
  addTearDown(() => tester.binding.setSurfaceSize(null));
  await tester.binding.setSurfaceSize(size);
  final router = GoRouter(
    initialLocation: initialLocation,
    routes: <RouteBase>[
      GoRoute(path: '/', builder: (context, state) => const BootstrapScreen()),
      GoRoute(
        path: '/workstation/:tabKey',
        builder: (context, state) =>
            WorkstationScreen(tabKey: state.pathParameters['tabKey'] ?? 'chat'),
      ),
    ],
  );

  await tester.pumpWidget(
    ProviderScope(
      overrides: <Override>[
        workstationLayoutProvider.overrideWith((ref) async => _testLayout()),
        workstationControllerProvider.overrideWith(() => controller),
        workstationRouterProvider.overrideWith((ref) => router),
      ],
      child: const WorkstationApp(),
    ),
  );
  await tester.pumpAndSettle();
}

class _FakeFilePicker extends FilePicker {
  _FakeFilePicker(this._result);

  final FilePickerResult? _result;

  factory _FakeFilePicker.singleFile({
    required String name,
    required Uint8List bytes,
  }) {
    return _FakeFilePicker(
      FilePickerResult(<PlatformFile>[
        PlatformFile(name: name, size: bytes.length, bytes: bytes),
      ]),
    );
  }

  @override
  Future<FilePickerResult?> pickFiles({
    String? dialogTitle,
    String? initialDirectory,
    FileType type = FileType.any,
    List<String>? allowedExtensions,
    Function(FilePickerStatus)? onFileLoading,
    bool allowCompression = false,
    int compressionQuality = 0,
    bool allowMultiple = false,
    bool withData = false,
    bool withReadStream = false,
    bool lockParentWindow = false,
    bool readSequential = false,
  }) async {
    return _result;
  }
}

class _BootstrapRoutingController extends WorkstationController {
  static const String _rootPath = '/tmp/workstation-root';

  @override
  WorkstationState build() {
    return WorkstationState(
      endpoint: _endpoint(),
      roots: <bootstrap.WorkstationRootDescriptor>[_rootDescriptor(_rootPath)],
      selectedRootPath: _rootPath,
      currentTabKey: 'chat',
      statusText: 'Discovered 1 workstation root.',
      activityView: _textView('No activity yet.'),
      permissionsView: _textView('Permissions view unavailable.'),
      skillsView: _textView('Skills view unavailable.'),
    );
  }

  @override
  Future<void> showTab(String tabKey) async {
    state = state.copyWith(currentTabKey: _normalizeTestTabKey(tabKey));
  }

  @override
  Future<bool> openSelectedRoot() async {
    state = state.copyWith(
      clientSessionId: 'flutter-bootstrap-routing',
      statusText: 'Connected to workstation-root.',
      subjects: <subject.SubjectScenarioSummary>[_placeholderScenario()],
      selectedScenarioKey: _PlaceholderPhaseController._placeholderKey,
      subjectSnapshot: _placeholderSnapshot(state.currentTabKey),
      chatSnapshot: _chatSnapshot(
        status: 'ready',
        messages: <shell.WorkstationChatMessage>[],
      ),
    );
    return true;
  }
}

class _DisconnectedResumeController extends WorkstationController {
  static const String _rootPath = '/tmp/workstation-root';

  int loadRootsCalls = 0;
  int openRootCalls = 0;

  @override
  WorkstationState build() {
    return WorkstationState(
      endpoint: _endpoint(),
      currentTabKey: 'research',
      activityView: _textView('No activity yet.'),
      permissionsView: _textView('Permissions view unavailable.'),
      skillsView: _textView('Skills view unavailable.'),
    );
  }

  @override
  Future<void> showTab(String tabKey) async {
    final normalized = _normalizeTestTabKey(tabKey);
    state = state.copyWith(
      currentTabKey: normalized,
      subjectSnapshot: state.connected
          ? _placeholderSnapshot(normalized)
          : state.subjectSnapshot,
    );
  }

  @override
  Future<void> loadRoots(EndpointConfig endpoint) async {
    loadRootsCalls += 1;
    state = state.copyWith(
      endpoint: endpoint,
      roots: <bootstrap.WorkstationRootDescriptor>[_rootDescriptor(_rootPath)],
      selectedRootPath: _rootPath,
      loadingRoots: false,
      statusText: 'Discovered 1 workstation root.',
      errorText: null,
    );
  }

  @override
  Future<bool> openSelectedRoot() async {
    openRootCalls += 1;
    state = state.copyWith(
      clientSessionId: 'flutter-disconnected-resume',
      selectedScenarioKey: _PlaceholderPhaseController._placeholderKey,
      subjects: <subject.SubjectScenarioSummary>[_placeholderScenario()],
      subjectSnapshot: _placeholderSnapshot(state.currentTabKey),
      chatSnapshot: _chatSnapshot(
        status: 'ready',
        messages: const <shell.WorkstationChatMessage>[],
      ),
      statusText: 'Connected to workstation-root.',
      errorText: null,
    );
    return true;
  }
}

class _ChatBddController extends WorkstationController {
  static const String _rootPath = '/tmp/workstation-root';
  static const String _clientSessionId = 'flutter-shell-chat-bdd';

  @override
  WorkstationState build() {
    return WorkstationState(
      endpoint: _endpoint(),
      selectedRootPath: _rootPath,
      clientSessionId: _clientSessionId,
      currentTabKey: 'chat',
      statusText: 'Connected to workstation-root.',
      chatSnapshot: _chatSnapshot(
        status: 'ready',
        messages: <shell.WorkstationChatMessage>[],
      ),
      activityView: _textView('No activity yet.'),
      permissionsView: _textView('Permissions view unavailable.'),
      skillsView: _textView('Skills view unavailable.'),
    );
  }

  @override
  Future<void> showTab(String tabKey) async {
    state = state.copyWith(currentTabKey: _normalizeTestTabKey(tabKey));
  }

  @override
  Future<void> preparePrompt(String promptText) async {
    state = state.copyWith(
      preparedPromptTarget: promptText.trim().isEmpty
          ? null
          : (shell.PrepareChatPromptTargetResponse()
              ..targetKind = 'shell'
              ..preparedPrompt = 'repo search'
              ..shellText = 'repo search preview'),
    );
  }

  @override
  Future<void> submitPrompt(String promptText) async {
    final messages = <shell.WorkstationChatMessage>[
      _message(role: 'user', content: promptText),
      _message(role: 'assistant', content: 'inspected the repo'),
    ];
    state = state.copyWith(
      chatBusy: false,
      preparedPromptTarget: null,
      statusText: 'Prompt completed.',
      chatSnapshot: _chatSnapshot(status: 'ready', messages: messages),
      activityView: _textView('chat prompt submitted'),
    );
  }
}

class _PlaceholderPhaseController extends WorkstationController {
  static const String _rootPath = '/tmp/workstation-root';
  static const String _clientSessionId = 'flutter-shell-placeholder';
  static const String _placeholderKey = '__learning_context_empty__';

  @override
  WorkstationState build() {
    return WorkstationState(
      endpoint: _endpoint(),
      selectedRootPath: _rootPath,
      clientSessionId: _clientSessionId,
      currentTabKey: 'research',
      selectedScenarioKey: _placeholderKey,
      statusText: 'Connected to workstation-root.',
      subjects: <subject.SubjectScenarioSummary>[_placeholderScenario()],
      subjectSnapshot: _placeholderSnapshot('research'),
      activityView: _textView('No activity yet.'),
      permissionsView: _textView('Permissions view unavailable.'),
      skillsView: _textView('Skills view unavailable.'),
    );
  }

  @override
  Future<void> showTab(String tabKey) async {
    final normalized = _normalizeTestTabKey(tabKey);
    state = state.copyWith(
      currentTabKey: normalized,
      subjectSnapshot: _placeholderSnapshot(normalized),
    );
  }

  @override
  Future<void> selectSubject(String scenarioKey) async {
    state = state.copyWith(
      selectedScenarioKey: scenarioKey,
      subjectSnapshot: _placeholderSnapshot(state.currentTabKey),
    );
  }
}

class _MarkdownIngressController extends WorkstationController {
  _MarkdownIngressController({required this.success});

  final bool success;

  static const String _rootPath = '/tmp/workstation-root';
  static const String _clientSessionId = 'flutter-shell-markdown';
  static const String _placeholderKey = '__learning_context_empty__';
  static const String _subjectKey = 'bus-network-notes';

  @override
  WorkstationState build() {
    return WorkstationState(
      endpoint: _endpoint(),
      selectedRootPath: _rootPath,
      clientSessionId: _clientSessionId,
      currentTabKey: 'research',
      selectedScenarioKey: _placeholderKey,
      statusText: 'Connected to workstation-root.',
      subjects: <subject.SubjectScenarioSummary>[_placeholderScenario()],
      subjectSnapshot: _placeholderSnapshot('research'),
      activityView: _textView('No activity yet.'),
      permissionsView: _textView('Permissions view unavailable.'),
      skillsView: _textView('Skills view unavailable.'),
    );
  }

  @override
  Future<void> showTab(String tabKey) async {
    final normalized = _normalizeTestTabKey(tabKey);
    state = state.copyWith(
      currentTabKey: normalized,
      subjectSnapshot: _snapshotFor(normalized),
    );
  }

  @override
  Future<void> selectSubject(String scenarioKey) async {
    state = state.copyWith(
      selectedScenarioKey: scenarioKey,
      subjectSnapshot: _snapshotFor(state.currentTabKey),
    );
  }

  @override
  Future<String?> stageMarkdownUpload(
    String filename,
    Uint8List content,
  ) async {
    final stagedPath = '/tmp/workstation-root/uploads/$filename';
    state = state.copyWith(
      subjectBusy: true,
      stagedMarkdownPath: stagedPath,
      markdownStatusText: 'Markdown upload staged.',
      statusText: 'Markdown upload staged.',
      subjectSnapshot: _busyMarkdownSnapshot(),
      errorText: null,
    );
    if (!success) {
      state = state.copyWith(
        subjectBusy: false,
        errorText: 'Import failed after staging.',
        statusText: 'Markdown upload failed.',
        subjectSnapshot: _busyMarkdownSnapshot(),
      );
      return null;
    }
    state = state.copyWith(
      subjectBusy: false,
      stagedMarkdownPath: '',
      markdownStatusText: '',
      statusText: 'Imported markdown into Bus Network Notes.',
      selectedScenarioKey: _subjectKey,
      subjects: <subject.SubjectScenarioSummary>[
        _scenario(
          key: _subjectKey,
          subjectId: _subjectKey,
          title: 'Bus Network Notes',
          summary: 'Maintained subject imported from staged markdown.',
        ),
      ],
      subjectSnapshot: _importedMarkdownSnapshot('review'),
    );
    return 'review';
  }

  subject.SubjectWorkflowSnapshotView _snapshotFor(String tabKey) {
    if (state.selectedScenarioKey == _placeholderKey) {
      return _placeholderSnapshot(tabKey);
    }
    return _importedMarkdownSnapshot(tabKey);
  }
}

class _SteadyStateBannerController extends WorkstationController {
  static const String _rootPath = '/tmp/workstation-root';
  static const String _clientSessionId = 'flutter-shell-steady-banner';
  static const String _subjectKey = 'transit-signals';

  @override
  WorkstationState build() {
    return WorkstationState(
      endpoint: _endpoint(),
      selectedRootPath: _rootPath,
      clientSessionId: _clientSessionId,
      currentTabKey: 'research',
      selectedScenarioKey: _subjectKey,
      statusText: 'Staged workstation-import.md into imported.',
      subjects: <subject.SubjectScenarioSummary>[
        _scenario(
          key: _subjectKey,
          subjectId: _subjectKey,
          title: 'Transit Signals',
          summary: 'Singapore bus interchange redesign notes.',
        ),
      ],
      subjectSnapshot: _steadyStateGatherSnapshot(),
      activityView: _textView('No activity yet.'),
      permissionsView: _textView('Permissions view unavailable.'),
      skillsView: _textView('Skills view unavailable.'),
    );
  }

  @override
  Future<void> showTab(String tabKey) async {
    state = state.copyWith(currentTabKey: _normalizeTestTabKey(tabKey));
  }
}

class _ImportApprovalTestController extends WorkstationController {
  static const String _sourceSubjectId = 'import-source-demo';
  static const String _targetSubjectId = 'target-subject-demo';
  static const String _rootPath = '/tmp/workstation-root';
  static const String _clientSessionId = 'flutter-shell-import-bdd';

  String _selectedImportSourceId = '';
  bool _pendingImport = false;
  bool _approvedImport = false;

  @override
  WorkstationState build() {
    return WorkstationState(
      endpoint: _endpoint(),
      selectedRootPath: _rootPath,
      clientSessionId: _clientSessionId,
      currentTabKey: 'research',
      selectedScenarioKey: _sourceSubjectId,
      statusText: 'Connected to workstation-root.',
      subjects: _subjects(),
      subjectSnapshot: _snapshotFor(
        scenarioKey: _sourceSubjectId,
        tabKey: 'research',
      ),
    );
  }

  @override
  Future<void> showTab(String tabKey) async {
    final normalized = _normalizeTestTabKey(tabKey);
    state = state.copyWith(
      currentTabKey: normalized,
      subjectSnapshot: _snapshotFor(
        scenarioKey: state.selectedScenarioKey,
        tabKey: normalized,
      ),
      errorText: null,
    );
  }

  @override
  Future<void> selectSubject(String scenarioKey) async {
    state = state.copyWith(
      selectedScenarioKey: scenarioKey,
      latestArtifacts: const <assets.ArtifactRef>[],
      subjectSnapshot: _snapshotFor(
        scenarioKey: scenarioKey,
        tabKey: state.currentTabKey,
      ),
    );
  }

  @override
  Future<String?> applyAction(
    String actionKey, {
    String assistantMessageText = '',
  }) async {
    final scenarioKey = state.selectedScenarioKey;
    switch (actionKey) {
      case 'select_as_import_source':
        _selectedImportSourceId = scenarioKey;
        state = state.copyWith(
          statusText: 'Import source selected.',
          subjectSnapshot: _snapshotFor(
            scenarioKey: scenarioKey,
            tabKey: state.currentTabKey,
          ),
        );
        return state.currentTabKey;
      case 'create_import_from_selected_source':
        _pendingImport = true;
        state = state.copyWith(
          statusText: 'Pending subject import created.',
          subjectSnapshot: _snapshotFor(
            scenarioKey: scenarioKey,
            tabKey: 'review',
          ),
        );
        return 'review';
      case 'preview_pending_import':
        state = state.copyWith(
          statusText: 'Pending subject import previewed.',
          subjectSnapshot: _snapshotFor(
            scenarioKey: scenarioKey,
            tabKey: 'research',
          ),
        );
        return 'research';
      case 'approve_import':
        _pendingImport = false;
        _approvedImport = true;
        state = state.copyWith(
          statusText: 'Subject import approved.',
          subjectSnapshot: _snapshotFor(
            scenarioKey: scenarioKey,
            tabKey: 'research',
          ),
        );
        return 'research';
      case 'clear_import_source':
        _selectedImportSourceId = '';
        _pendingImport = false;
        _approvedImport = false;
        state = state.copyWith(
          statusText: 'Import source cleared.',
          subjectSnapshot: _snapshotFor(
            scenarioKey: scenarioKey,
            tabKey: state.currentTabKey,
          ),
        );
        return state.currentTabKey;
      default:
        return state.currentTabKey;
    }
  }

  List<subject.SubjectScenarioSummary> _subjects() {
    return <subject.SubjectScenarioSummary>[
      _scenario(
        key: _sourceSubjectId,
        subjectId: _sourceSubjectId,
        title: 'Import Source Demo',
        summary: 'Grouped counting is reusable support.',
      ),
      _scenario(
        key: _targetSubjectId,
        subjectId: _targetSubjectId,
        title: 'Target Subject Demo',
        summary: 'The target subject combines prior support.',
      ),
    ];
  }

  subject.SubjectWorkflowSnapshotView _snapshotFor({
    required String scenarioKey,
    required String tabKey,
  }) {
    final phase = _subjectPhaseForTestTab(tabKey);
    if (phase == 'review' &&
        scenarioKey == _targetSubjectId &&
        _pendingImport) {
      return _workflowSnapshot(
        phase: 'review',
        phaseTitle: 'Review',
        scenario: _scenario(
          key: _targetSubjectId,
          subjectId: _targetSubjectId,
          title: 'Target Subject Demo',
          summary: 'The target subject combines prior support.',
        ),
        status: 'Inspect the pending import',
        why:
            'Preview the staged import before approving it into the target subject.',
        actions: <subject.SubjectGateAction>[
          _gateAction('preview_pending_import', 'Preview Pending Import'),
        ],
        detailLines: <String>['- import source: Import Source Demo'],
        statusRows: <subject.KeyValueRow>[
          _statusRow('Mode', 'Live subject workflow'),
          _statusRow('Phase', 'Review'),
          _statusRow('Subject', 'Target Subject Demo'),
          _statusRow('Pending Imports', '1'),
        ],
      );
    }

    if (phase == 'research' &&
        scenarioKey == _targetSubjectId &&
        _pendingImport) {
      return _workflowSnapshot(
        phase: 'research',
        phaseTitle: 'Gather',
        scenario: _scenario(
          key: _targetSubjectId,
          subjectId: _targetSubjectId,
          title: 'Target Subject Demo',
          summary: 'The target subject combines prior support.',
        ),
        status: 'Inspect the pending import',
        why: 'Return to Gather to approve the staged import into this subject.',
        actions: <subject.SubjectGateAction>[
          _gateAction('preview_pending_import', 'Preview Pending Import'),
          _gateAction('approve_import', 'Approve Import'),
        ],
        detailLines: <String>['- import source: Import Source Demo'],
        statusRows: <subject.KeyValueRow>[
          _statusRow('Mode', 'Live subject workflow'),
          _statusRow('Phase', 'Gather'),
          _statusRow('Subject', 'Target Subject Demo'),
          _statusRow('Pending Imports', '1'),
        ],
      );
    }

    if (phase == 'research' &&
        scenarioKey == _targetSubjectId &&
        _approvedImport) {
      return _workflowSnapshot(
        phase: 'research',
        phaseTitle: 'Gather',
        scenario: _scenario(
          key: _targetSubjectId,
          subjectId: _targetSubjectId,
          title: 'Target Subject Demo',
          summary: 'The target subject combines prior support.',
        ),
        status: 'Approved import now contributes to the reasoning scope.',
        why:
            'The approved support now contributes to the target subject reasoning scope.',
        actions: <subject.SubjectGateAction>[
          _gateAction('check_maintained_files', 'Check Maintained Files'),
          _gateAction('generate_itemization', 'Generate Itemization'),
        ],
        statusRows: <subject.KeyValueRow>[
          _statusRow('Mode', 'Live subject workflow'),
          _statusRow('Phase', 'Gather'),
          _statusRow('Subject', 'Target Subject Demo'),
          _statusRow('Reasoning Scope', '1 support items from 1'),
        ],
      );
    }

    if (phase == 'research' &&
        scenarioKey == _targetSubjectId &&
        _selectedImportSourceId == _sourceSubjectId &&
        !_pendingImport &&
        !_approvedImport) {
      return _workflowSnapshot(
        phase: 'research',
        phaseTitle: 'Gather',
        scenario: _scenario(
          key: _targetSubjectId,
          subjectId: _targetSubjectId,
          title: 'Target Subject Demo',
          summary: 'The target subject combines prior support.',
        ),
        status: 'Create import from the selected source',
        why:
            'The selected import source is ready to be staged into the target subject.',
        actions: <subject.SubjectGateAction>[
          _gateAction(
            'create_import_from_selected_source',
            'Create Import From Selected Source',
          ),
          _gateAction('clear_import_source', 'Clear Import Source'),
        ],
        detailLines: <String>['- import source: Import Source Demo'],
        statusRows: <subject.KeyValueRow>[
          _statusRow('Mode', 'Live subject workflow'),
          _statusRow('Phase', 'Gather'),
          _statusRow('Subject', 'Target Subject Demo'),
          _statusRow('Selected Import Source', 'Import Source Demo'),
        ],
      );
    }

    if (phase == 'research' &&
        scenarioKey == _sourceSubjectId &&
        _selectedImportSourceId == _sourceSubjectId) {
      return _workflowSnapshot(
        phase: 'research',
        phaseTitle: 'Gather',
        scenario: _scenario(
          key: _sourceSubjectId,
          subjectId: _sourceSubjectId,
          title: 'Import Source Demo',
          summary: 'Grouped counting is reusable support.',
        ),
        status: 'Import source selected.',
        why:
            'Switch to the target subject and create the staged import from this source.',
        actions: <subject.SubjectGateAction>[
          _gateAction('check_maintained_files', 'Check Maintained Files'),
          _gateAction('select_as_import_source', 'Select As Import Source'),
          _gateAction('generate_itemization', 'Generate Itemization'),
        ],
        detailLines: <String>['- selected import source: Import Source Demo'],
        statusRows: <subject.KeyValueRow>[
          _statusRow('Mode', 'Live subject workflow'),
          _statusRow('Phase', 'Gather'),
          _statusRow('Subject', 'Import Source Demo'),
          _statusRow('Selected Import Source', 'Import Source Demo'),
        ],
      );
    }

    return _workflowSnapshot(
      phase: phase,
      phaseTitle: phase == 'review' ? 'Review' : 'Gather',
      scenario: _scenario(
        key: scenarioKey,
        subjectId: scenarioKey,
        title: scenarioKey == _sourceSubjectId
            ? 'Import Source Demo'
            : 'Target Subject Demo',
        summary: scenarioKey == _sourceSubjectId
            ? 'Grouped counting is reusable support.'
            : 'The target subject combines prior support.',
      ),
      status: 'Live subject workflow ready.',
      why: scenarioKey == _sourceSubjectId
          ? 'Run the maintained-files check or select this subject as the import source.'
          : 'Run the maintained-files check before drafting from this subject.',
      actions: <subject.SubjectGateAction>[
        _gateAction('check_maintained_files', 'Check Maintained Files'),
        if (scenarioKey == _sourceSubjectId)
          _gateAction('select_as_import_source', 'Select As Import Source'),
        _gateAction('generate_itemization', 'Generate Itemization'),
      ],
      statusRows: <subject.KeyValueRow>[
        _statusRow('Mode', 'Live subject workflow'),
        _statusRow('Phase', phase == 'review' ? 'Review' : 'Gather'),
        _statusRow(
          'Subject',
          scenarioKey == _sourceSubjectId
              ? 'Import Source Demo'
              : 'Target Subject Demo',
        ),
      ],
    );
  }
}

class _EmptyStateFollowUpController extends WorkstationController {
  static const String _rootPath = '/tmp/workstation-root';
  static const String _clientSessionId = 'flutter-shell-empty-follow-up';

  @override
  WorkstationState build() {
    return WorkstationState(
      endpoint: _endpoint(),
      selectedRootPath: _rootPath,
      clientSessionId: _clientSessionId,
      currentTabKey: 'research',
      selectedScenarioKey: _PlaceholderPhaseController._placeholderKey,
      statusText: 'Live subject workflow ready.',
      subjects: <subject.SubjectScenarioSummary>[_placeholderScenario()],
      subjectSnapshot: _placeholderSnapshot('research'),
      chatSnapshot: _chatSnapshot(
        status: 'ready',
        messages: const <shell.WorkstationChatMessage>[],
      ),
      activityView: _textView('No activity yet.'),
      permissionsView: _textView('Permissions view unavailable.'),
      skillsView: _textView('Skills view unavailable.'),
    );
  }

  @override
  Future<void> showTab(String tabKey) async {
    final normalized = _normalizeTestTabKey(tabKey);
    state = state.copyWith(
      currentTabKey: normalized,
      subjectSnapshot: normalized == 'chat'
          ? state.subjectSnapshot
          : _placeholderSnapshot(normalized),
    );
  }

  @override
  Future<String?> applyAction(
    String actionKey, {
    String assistantMessageText = '',
  }) async {
    if (actionKey != 'ask_follow_up') {
      return state.currentTabKey;
    }
    state = state.copyWith(
      currentTabKey: 'chat',
      statusText: 'Moved to Chat for a follow-up question.',
      chatSnapshot: _chatSnapshot(
        status: 'ready',
        messages: <shell.WorkstationChatMessage>[
          _message(
            role: 'assistant',
            content: 'Moved to Chat for a follow-up question.',
          ),
        ],
      ),
      activityView: _textView('follow-up routed to chat'),
    );
    return 'chat';
  }
}

class _CheckMaintainedToReviewController extends WorkstationController {
  static const String _rootPath = '/tmp/workstation-root';
  static const String _clientSessionId = 'flutter-shell-maintained-review';
  static const String _subjectKey = 'kinematics-demo';

  bool _compared = false;

  @override
  WorkstationState build() {
    return WorkstationState(
      endpoint: _endpoint(),
      selectedRootPath: _rootPath,
      clientSessionId: _clientSessionId,
      currentTabKey: 'research',
      selectedScenarioKey: _subjectKey,
      statusText: 'Live subject workflow ready.',
      subjects: <subject.SubjectScenarioSummary>[
        _scenario(
          key: _subjectKey,
          subjectId: _subjectKey,
          title: 'Kinematics Demo',
          summary: 'Maintained subject for introductory kinematics.',
        ),
      ],
      subjectSnapshot: _snapshotFor('research'),
      chatSnapshot: _chatSnapshot(
        status: 'ready',
        messages: const <shell.WorkstationChatMessage>[],
      ),
    );
  }

  @override
  Future<void> showTab(String tabKey) async {
    final normalized = _normalizeTestTabKey(tabKey);
    state = state.copyWith(
      currentTabKey: normalized,
      subjectSnapshot: _snapshotFor(normalized),
    );
  }

  @override
  Future<String?> applyAction(
    String actionKey, {
    String assistantMessageText = '',
  }) async {
    if (actionKey != 'compare_projections') {
      return state.currentTabKey;
    }
    _compared = true;
    state = state.copyWith(
      currentTabKey: 'review',
      statusText: 'Projection comparison aligned.',
      subjectSnapshot: _snapshotFor('review'),
    );
    return 'review';
  }

  subject.SubjectWorkflowSnapshotView _snapshotFor(String tabKey) {
    final scenario = _scenario(
      key: _subjectKey,
      subjectId: _subjectKey,
      title: 'Kinematics Demo',
      summary: 'Maintained subject for introductory kinematics.',
    );
    if (_compared || _subjectPhaseForTestTab(tabKey) == 'review') {
      return _workflowSnapshot(
        phase: 'review',
        phaseTitle: 'Review',
        scenario: scenario,
        status: '',
        stepTitle: 'Create the report plan',
        stepStatus:
            'The maintained-files check completed and the files are aligned.',
        why:
            'The maintained-files comparison completed and the next workflow step now lives in Review.',
        actions: <subject.SubjectGateAction>[
          _gateAction('refresh_publication_composition', 'Create Report Plan'),
        ],
        detailLines: const <String>[
          '- maintained files: aligned',
          '- last action: Projection comparison aligned.',
        ],
        statusRows: <subject.KeyValueRow>[
          _statusRow('Mode', 'Live subject workflow'),
          _statusRow('Phase', 'Review'),
          _statusRow('Subject', 'Kinematics Demo'),
        ],
      );
    }
    return _workflowSnapshot(
      phase: 'research',
      phaseTitle: 'Gather',
      scenario: scenario,
      status: '',
      stepTitle: 'Check maintained files',
      stepStatus:
          'The maintained subject is active and the generated files should be compared before continuing.',
      why:
          'This maintained-files check can advance directly to Review when the report plan is the next actionable step.',
      actions: <subject.SubjectGateAction>[
        _gateAction('compare_projections', 'Check Maintained Files'),
      ],
      statusRows: <subject.KeyValueRow>[
        _statusRow('Mode', 'Live subject workflow'),
        _statusRow('Phase', 'Gather'),
        _statusRow('Subject', 'Kinematics Demo'),
      ],
    );
  }
}

class _PublicationImportBddController extends WorkstationController {
  _PublicationImportBddController() : _multiImportReady = false;

  _PublicationImportBddController.multiImportReady() : _multiImportReady = true;

  final bool _multiImportReady;

  static const String _sourceAKey = 'source-einstein';
  static const String _sourceBKey = 'source-wikipedia';
  static const String _targetKey = 'target-meet-greet-depart';
  static const String _rootPath = '/tmp/workstation-root';
  static const String _clientSessionId = 'flutter-shell-publication-imports';

  String _selectedImportSourceId = '';
  final List<String> _approvedSourceIds = <String>[];
  bool _pendingImport = false;
  bool _itemizationGenerated = false;
  bool _draftCompositionReady = false;
  bool _reportPlanAligned = false;
  bool _publicationPlanReady = false;
  String _publicationImportTarget = _sourceAKey;
  bool _publicationImportIncluded = true;
  String _publicationImportUsage = 'dependency_only';

  @override
  WorkstationState build() {
    if (_multiImportReady) {
      _approvedSourceIds
        ..clear()
        ..addAll(<String>[_sourceAKey, _sourceBKey]);
      _itemizationGenerated = true;
      _draftCompositionReady = true;
      _reportPlanAligned = true;
      _publicationPlanReady = true;
      _publicationImportTarget = _sourceAKey;
    }
    return WorkstationState(
      endpoint: _endpoint(),
      selectedRootPath: _rootPath,
      clientSessionId: _clientSessionId,
      currentTabKey: _multiImportReady ? 'publication' : 'research',
      selectedScenarioKey: _multiImportReady ? _targetKey : _sourceAKey,
      statusText: 'Live subject workflow ready.',
      subjects: _subjects(),
      subjectSnapshot: _snapshotFor(
        scenarioKey: _multiImportReady ? _targetKey : _sourceAKey,
        tabKey: _multiImportReady ? 'publication' : 'research',
      ),
      chatSnapshot: _chatSnapshot(
        status: 'ready',
        messages: const <shell.WorkstationChatMessage>[],
      ),
    );
  }

  @override
  Future<void> showTab(String tabKey) async {
    final normalized = _normalizeTestTabKey(tabKey);
    state = state.copyWith(
      currentTabKey: normalized,
      subjectSnapshot: _snapshotFor(
        scenarioKey: state.selectedScenarioKey,
        tabKey: normalized,
      ),
    );
  }

  @override
  Future<void> selectSubject(String scenarioKey) async {
    state = state.copyWith(
      selectedScenarioKey: scenarioKey,
      subjectSnapshot: _snapshotFor(
        scenarioKey: scenarioKey,
        tabKey: state.currentTabKey,
      ),
    );
  }

  @override
  Future<String?> applyAction(
    String actionKey, {
    String assistantMessageText = '',
  }) async {
    final scenarioKey = state.selectedScenarioKey;
    switch (actionKey) {
      case 'select_as_import_source':
        _selectedImportSourceId = scenarioKey;
        state = state.copyWith(
          statusText: 'Import source selected.',
          subjectSnapshot: _snapshotFor(
            scenarioKey: scenarioKey,
            tabKey: state.currentTabKey,
          ),
        );
        return state.currentTabKey;
      case 'create_import_from_selected_source':
        _pendingImport = true;
        state = state.copyWith(
          statusText: 'Pending subject import created.',
          subjectSnapshot: _snapshotFor(
            scenarioKey: scenarioKey,
            tabKey: 'review',
          ),
        );
        return 'review';
      case 'preview_pending_import':
        state = state.copyWith(
          statusText: 'Pending subject import preview loaded.',
          subjectSnapshot: _snapshotFor(
            scenarioKey: scenarioKey,
            tabKey: 'research',
          ),
        );
        return 'research';
      case 'approve_import':
        _pendingImport = false;
        if (_selectedImportSourceId.isNotEmpty &&
            !_approvedSourceIds.contains(_selectedImportSourceId)) {
          _approvedSourceIds.add(_selectedImportSourceId);
        }
        state = state.copyWith(
          statusText: 'Subject import approved.',
          subjectSnapshot: _snapshotFor(
            scenarioKey: scenarioKey,
            tabKey: 'research',
          ),
        );
        return 'research';
      case 'generate_itemization':
        _itemizationGenerated = true;
        state = state.copyWith(
          statusText: 'Itemization generated.',
          subjectSnapshot: _snapshotFor(
            scenarioKey: scenarioKey,
            tabKey: state.currentTabKey,
          ),
        );
        return state.currentTabKey;
      case 'refresh_review_composition':
        _draftCompositionReady = true;
        state = state.copyWith(
          statusText: 'Draft composition refreshed.',
          subjectSnapshot: _snapshotFor(
            scenarioKey: scenarioKey,
            tabKey: state.currentTabKey,
          ),
        );
        return state.currentTabKey;
      case 'compare_projections':
        _reportPlanAligned = true;
        state = state.copyWith(
          statusText: 'Projection comparison aligned.',
          subjectSnapshot: _snapshotFor(
            scenarioKey: scenarioKey,
            tabKey: state.currentTabKey,
          ),
        );
        return state.currentTabKey;
      case 'refresh_publication_composition':
        _publicationPlanReady = true;
        state = state.copyWith(
          statusText: 'Report plan refreshed.',
          subjectSnapshot: _snapshotFor(
            scenarioKey: scenarioKey,
            tabKey: state.currentTabKey,
          ),
        );
        return state.currentTabKey;
      case 'toggle_selected_publication_import':
        _publicationImportIncluded = !_publicationImportIncluded;
        state = state.copyWith(
          statusText: 'Publication import inclusion updated.',
          subjectSnapshot: _snapshotFor(
            scenarioKey: scenarioKey,
            tabKey: state.currentTabKey,
          ),
        );
        return state.currentTabKey;
      default:
        if (actionKey.startsWith('set_publication_import_target:')) {
          _publicationImportTarget = actionKey.split(':').last;
          state = state.copyWith(
            statusText: 'Publication import target updated.',
            subjectSnapshot: _snapshotFor(
              scenarioKey: scenarioKey,
              tabKey: state.currentTabKey,
            ),
          );
          return state.currentTabKey;
        }
        if (actionKey.startsWith('set_selected_publication_import_usage_')) {
          _publicationImportUsage = actionKey.substring(
            'set_selected_publication_import_usage_'.length,
          );
          state = state.copyWith(
            statusText: 'Publication import usage updated.',
            subjectSnapshot: _snapshotFor(
              scenarioKey: scenarioKey,
              tabKey: state.currentTabKey,
            ),
          );
          return state.currentTabKey;
        }
        return state.currentTabKey;
    }
  }

  List<subject.SubjectScenarioSummary> _subjects() {
    return <subject.SubjectScenarioSummary>[
      _scenario(
        key: _sourceAKey,
        subjectId: _sourceAKey,
        title: 'Einstein',
        summary: 'Supporting import source about relativity.',
      ),
      _scenario(
        key: _sourceBKey,
        subjectId: _sourceBKey,
        title: 'Wikipedia',
        summary: 'Secondary supporting import source.',
      ),
      _scenario(
        key: _targetKey,
        subjectId: _targetKey,
        title: 'Meet Greet Depart',
        summary: 'Target subject that borrows imported support.',
      ),
    ];
  }

  subject.SubjectWorkflowSnapshotView _snapshotFor({
    required String scenarioKey,
    required String tabKey,
  }) {
    final phase = _subjectPhaseForTestTab(tabKey);
    if (phase == 'review' && scenarioKey == _targetKey && _pendingImport) {
      return _workflowSnapshot(
        phase: 'review',
        phaseTitle: 'Review',
        scenario: _targetScenario(),
        status: '',
        stepTitle: 'Inspect the pending import',
        stepStatus:
            'Preview the staged import before approving it into the target subject.',
        why:
            'The pending import should be checked before approval and report-plan refresh.',
        actions: <subject.SubjectGateAction>[
          _gateAction('preview_pending_import', 'Preview Pending Import'),
        ],
        detailLines: <String>[
          '- pending import source: ${_sourceTitle(_selectedImportSourceId)}',
        ],
        statusRows: <subject.KeyValueRow>[
          _statusRow('Mode', 'Publication import BDD'),
          _statusRow('Phase', 'Review'),
          _statusRow('Subject', 'Meet Greet Depart'),
          _statusRow('Pending Imports', '1'),
        ],
      );
    }

    if (phase == 'research' && scenarioKey == _targetKey && _pendingImport) {
      return _workflowSnapshot(
        phase: 'research',
        phaseTitle: 'Gather',
        scenario: _targetScenario(),
        status: '',
        stepTitle: 'Approve the pending import',
        stepStatus:
            'The staged import is ready to be approved into the target subject.',
        why:
            'Approve the import before refreshing the report plan in Publication.',
        actions: <subject.SubjectGateAction>[
          _gateAction('approve_import', 'Approve Import'),
        ],
        detailLines: <String>[
          '- pending import source: ${_sourceTitle(_selectedImportSourceId)}',
        ],
        statusRows: <subject.KeyValueRow>[
          _statusRow('Mode', 'Publication import BDD'),
          _statusRow('Phase', 'Gather'),
          _statusRow('Subject', 'Meet Greet Depart'),
          _statusRow('Pending Imports', '1'),
        ],
      );
    }

    if (phase == 'research' &&
        scenarioKey == _targetKey &&
        _selectedImportSourceId.isNotEmpty &&
        _approvedSourceIds.isEmpty &&
        !_pendingImport) {
      return _workflowSnapshot(
        phase: 'research',
        phaseTitle: 'Gather',
        scenario: _targetScenario(),
        status: '',
        stepTitle: 'Create import from the selected source',
        stepStatus:
            'The selected source is ready to be staged into the target subject.',
        why:
            'Stage the import before moving the target workflow toward Publication.',
        actions: <subject.SubjectGateAction>[
          _gateAction(
            'create_import_from_selected_source',
            'Create Import From Selected Source',
          ),
        ],
        detailLines: <String>[
          '- selected import source: ${_sourceTitle(_selectedImportSourceId)}',
        ],
        statusRows: <subject.KeyValueRow>[
          _statusRow('Mode', 'Publication import BDD'),
          _statusRow('Phase', 'Gather'),
          _statusRow('Subject', 'Meet Greet Depart'),
          _statusRow(
            'Selected Import Source',
            _sourceTitle(_selectedImportSourceId),
          ),
        ],
      );
    }

    if (phase == 'research' && scenarioKey != _targetKey) {
      return _workflowSnapshot(
        phase: 'research',
        phaseTitle: 'Gather',
        scenario: _sourceScenarioFor(scenarioKey),
        status: '',
        stepTitle: _selectedImportSourceId == scenarioKey
            ? 'Import source selected.'
            : 'Select this subject as the import source',
        stepStatus: _selectedImportSourceId == scenarioKey
            ? 'Switch to the target subject and create the staged import.'
            : 'Choose this source if the target report plan should borrow its support.',
        why:
            'Approved imports should remain visible in Publication after the plan refreshes.',
        actions: <subject.SubjectGateAction>[
          _gateAction('select_as_import_source', 'Select As Import Source'),
        ],
        statusRows: <subject.KeyValueRow>[
          _statusRow('Mode', 'Publication import BDD'),
          _statusRow('Phase', 'Gather'),
          _statusRow('Subject', _sourceTitle(scenarioKey)),
        ],
      );
    }

    if (phase == 'itemize') {
      return _workflowSnapshot(
        phase: 'itemize',
        phaseTitle: 'Itemize',
        scenario: _targetScenario(),
        status: '',
        stepTitle: _itemizationGenerated
            ? 'Itemization is current'
            : 'Generate the itemization inventory',
        stepStatus: _itemizationGenerated
            ? 'The approved import is now available to Draft and Publication planning.'
            : 'Generate the itemization inventory before creating the draft composition.',
        why:
            'Publication import controls only appear after the plan reaches Publication with current upstream projections.',
        actions: _itemizationGenerated
            ? const <subject.SubjectGateAction>[]
            : <subject.SubjectGateAction>[
                _gateAction('generate_itemization', 'Generate Itemization'),
              ],
        statusRows: <subject.KeyValueRow>[
          _statusRow('Mode', 'Publication import BDD'),
          _statusRow('Phase', 'Itemize'),
          _statusRow('Subject', 'Meet Greet Depart'),
          _statusRow(
            'Approved Imports',
            _approvedSourceIds.isEmpty ? '0' : '${_approvedSourceIds.length}',
          ),
        ],
      );
    }

    if (phase == 'draft') {
      return _workflowSnapshot(
        phase: 'draft',
        phaseTitle: 'Draft',
        scenario: _targetScenario(),
        status: '',
        stepTitle: _draftCompositionReady
            ? 'Draft composition is current'
            : 'Create the draft composition',
        stepStatus: _draftCompositionReady
            ? 'The draft composition already reflects the approved import.'
            : 'Create the draft composition before refreshing the report plan.',
        why:
            'The report plan in Publication depends on the current draft composition.',
        actions: _draftCompositionReady
            ? const <subject.SubjectGateAction>[]
            : <subject.SubjectGateAction>[
                _gateAction(
                  'refresh_review_composition',
                  'Create Draft Composition',
                ),
              ],
        statusRows: <subject.KeyValueRow>[
          _statusRow('Mode', 'Publication import BDD'),
          _statusRow('Phase', 'Draft'),
          _statusRow('Subject', 'Meet Greet Depart'),
          _statusRow(
            'Draft Composition',
            _draftCompositionReady ? 'current' : 'not generated yet',
          ),
        ],
      );
    }

    if (phase == 'review') {
      return _workflowSnapshot(
        phase: 'review',
        phaseTitle: 'Review',
        scenario: _targetScenario(),
        status: '',
        stepTitle: _reportPlanAligned
            ? 'Report plan alignment is current'
            : 'Compare the report plans',
        stepStatus: _reportPlanAligned
            ? 'Projection comparison aligned.'
            : 'Compare the report plans before Publication refreshes the import controls.',
        why:
            'Publication import controls belong to the current report plan and appear only after the review comparison step.',
        actions: _reportPlanAligned
            ? const <subject.SubjectGateAction>[]
            : <subject.SubjectGateAction>[
                _gateAction('compare_projections', 'Compare Report Plans'),
              ],
        statusRows: <subject.KeyValueRow>[
          _statusRow('Mode', 'Publication import BDD'),
          _statusRow('Phase', 'Review'),
          _statusRow('Subject', 'Meet Greet Depart'),
          _statusRow(
            'Report Plan',
            _reportPlanAligned ? 'aligned' : 'comparison pending',
          ),
        ],
      );
    }

    final snapshot = _workflowSnapshot(
      phase: 'publication',
      phaseTitle: 'Publication',
      scenario: _targetScenario(),
      status: '',
      stepTitle: _publicationPlanReady
          ? 'Publication import controls are ready'
          : 'Refresh the report plan',
      stepStatus: _publicationPlanReady
          ? 'The current report plan now exposes import target, inclusion, and usage controls.'
          : 'Refresh the report plan so Publication can expose the import controls.',
      why:
          'Imported support participates in the report plan only after Publication refreshes the current plan.',
      actions: _publicationPlanReady
          ? const <subject.SubjectGateAction>[]
          : <subject.SubjectGateAction>[
              _gateAction(
                'refresh_publication_composition',
                'Refresh Report Plan',
              ),
            ],
      detailLines: <String>[
        'import target | ${_sourceTitle(_publicationImportTarget)}',
        'import included | ${_publicationImportIncluded ? 'yes' : 'no'}',
        'import usage | $_publicationImportUsage',
      ],
      statusRows: <subject.KeyValueRow>[
        _statusRow('Mode', 'Publication import BDD'),
        _statusRow('Phase', 'Publication'),
        _statusRow('Subject', 'Meet Greet Depart'),
      ],
    );
    if (_publicationPlanReady) {
      snapshot.controlBundle = (subject.SubjectControlBundleView()
        ..phase = 'publication'
        ..selects.add(
          subject.SubjectSelectSpecView()
            ..key = 'publication_import_target'
            ..label = 'Support'
            ..value = _publicationImportTarget
            ..enabled = true
            ..options.addAll(
              _approvedSourceIds.map((sourceId) {
                return subject.SubjectOption()
                  ..label = _sourceTitle(sourceId)
                  ..value = sourceId;
              }),
            ),
        )
        ..selects.add(
          subject.SubjectSelectSpecView()
            ..key = 'publication_import_usage'
            ..label = 'Use'
            ..value = _publicationImportUsage
            ..enabled = true
            ..options.addAll(<subject.SubjectOption>[
              (subject.SubjectOption()
                ..label = 'Dependency only'
                ..value = 'dependency_only'),
              (subject.SubjectOption()
                ..label = 'Direct quote'
                ..value = 'direct_quote'),
            ]),
        )
        ..switches.add(
          subject.SubjectSwitchSpecView()
            ..key = 'publication_import_included'
            ..label = 'Include'
            ..value = _publicationImportIncluded
            ..enabled = true,
        )
        ..moreActions.add(_actionSpec('refresh_subjects', 'Refresh Subjects')));
    }
    snapshot.paneBundle.panes
      ..clear()
      ..addAll(<subject.SubjectPaneView>[
        (subject.SubjectPaneView()
          ..key = 'publication_scope_tree'
          ..title = 'Report Scope'
          ..lines.addAll(<String>[
            '> [x] Report summary',
            '  [x] Imported support appears in Publication controls',
          ])),
        (subject.SubjectPaneView()
          ..key = 'publication_scope_detail'
          ..title = 'Selection Details'
          ..lines.addAll(<String>[
            'import target | ${_sourceTitle(_publicationImportTarget)}',
            'import included | ${_publicationImportIncluded ? 'yes' : 'no'}',
            'import usage | $_publicationImportUsage',
          ])),
      ]);
    return snapshot;
  }

  subject.SubjectScenarioSummary _targetScenario() {
    return _scenario(
      key: _targetKey,
      subjectId: _targetKey,
      title: 'Meet Greet Depart',
      summary: 'Target subject that borrows imported support.',
    );
  }

  subject.SubjectScenarioSummary _sourceScenarioFor(String sourceKey) {
    return _scenario(
      key: sourceKey,
      subjectId: sourceKey,
      title: _sourceTitle(sourceKey),
      summary: sourceKey == _sourceAKey
          ? 'Supporting import source about relativity.'
          : 'Secondary supporting import source.',
    );
  }

  String _sourceTitle(String sourceKey) {
    return switch (sourceKey) {
      _sourceAKey => 'Einstein',
      _sourceBKey => 'Wikipedia',
      _ => 'Unknown Source',
    };
  }
}

class _UtilityTabsController extends WorkstationController {
  static const String _rootPath = '/tmp/workstation-root';
  static const String _clientSessionId = 'flutter-shell-utility';

  @override
  WorkstationState build() {
    return WorkstationState(
      endpoint: _endpoint(),
      selectedRootPath: _rootPath,
      clientSessionId: _clientSessionId,
      currentTabKey: 'permissions',
      statusText: 'Connected to workstation-root.',
      permissionsView: _textView(_longPermissionsText()),
      activityView: _textView(_longActivityText()),
      skillsView: _textView(_longSkillsText()),
      chatSnapshot: _chatSnapshot(
        status: 'ready',
        messages: <shell.WorkstationChatMessage>[],
      ),
    );
  }

  @override
  Future<void> showTab(String tabKey) async {
    state = state.copyWith(currentTabKey: _normalizeTestTabKey(tabKey));
  }
}

class _CrossPhaseGateActionController extends WorkstationController {
  static const String _rootPath = '/tmp/workstation-root';
  static const String _clientSessionId = 'flutter-shell-cross-phase';
  static const String _subjectKey = 'city-bus-ticketing';

  bool _maintainedCompared = false;

  @override
  WorkstationState build() {
    return WorkstationState(
      endpoint: _endpoint(),
      selectedRootPath: _rootPath,
      clientSessionId: _clientSessionId,
      currentTabKey: 'itemize',
      statusText: 'Connected to workstation-root.',
      subjects: <subject.SubjectScenarioSummary>[
        _scenario(
          key: _subjectKey,
          subjectId: _subjectKey,
          title: 'City bus ticketing modernization',
          summary: 'A city transit authority wants to modernize fare payment.',
        ),
      ],
      selectedScenarioKey: _subjectKey,
      subjectSnapshot: _snapshotFor('itemize'),
      chatSnapshot: _chatSnapshot(
        status: 'ready',
        messages: <shell.WorkstationChatMessage>[],
      ),
    );
  }

  @override
  Future<void> showTab(String tabKey) async {
    final normalized = _normalizeTestTabKey(tabKey);
    state = state.copyWith(
      currentTabKey: normalized,
      subjectSnapshot: _snapshotFor(normalized),
    );
  }

  @override
  Future<String?> applyAction(
    String actionKey, {
    String assistantMessageText = '',
  }) async {
    if (actionKey != 'compare_projections') {
      state = state.copyWith(statusText: 'No subject action was applied.');
      return state.currentTabKey;
    }
    if (state.currentTabKey != 'research') {
      state = state.copyWith(statusText: 'No subject action was applied.');
      return state.currentTabKey;
    }
    _maintainedCompared = true;
    state = state.copyWith(
      statusText: 'Maintained files compared.',
      subjectSnapshot: _snapshotFor('research'),
    );
    return 'research';
  }

  subject.SubjectWorkflowSnapshotView _snapshotFor(String tabKey) {
    final scenario = _scenario(
      key: _subjectKey,
      subjectId: _subjectKey,
      title: 'City bus ticketing modernization',
      summary: 'A city transit authority wants to modernize fare payment.',
    );
    if (tabKey == 'research') {
      final snapshot = _workflowSnapshot(
        phase: 'research',
        phaseTitle: 'Gather',
        scenario: scenario,
        status: '',
        stepTitle: 'Gather is current again',
        stepStatus:
            'Maintained files compared and the subject remains current.',
        why: 'The maintained-files check completed in its home phase.',
        detailLines: <String>[
          '- result: maintained files aligned',
          '- downstream: Itemization remains ready for Draft.',
        ],
        statusRows: <subject.KeyValueRow>[
          _statusRow('Mode', 'Live subject workflow'),
          _statusRow('Phase', 'Gather'),
          _statusRow('Subject', 'City bus ticketing modernization'),
          _statusRow(
            'Itemization',
            _maintainedCompared ? '5 items, ok, current' : 'not generated yet',
          ),
        ],
      );
      snapshot.paneBundle.panes
        ..clear()
        ..addAll(<subject.SubjectPaneView>[
          (subject.SubjectPaneView()
            ..key = 'research_sources'
            ..title = 'Source Sets'
            ..lines.addAll(<String>[
              'All Gather Sources',
              '1 source staged and ready.',
            ])),
          (subject.SubjectPaneView()
            ..key = 'research_observation'
            ..title = 'Learned Snapshot'
            ..lines.addAll(<String>[
              'Maintained files compared.',
              'Itemization remains ready for Draft.',
            ])),
        ]);
      return snapshot;
    }

    final snapshot = _workflowSnapshot(
      phase: 'itemize',
      phaseTitle: 'Itemize',
      scenario: scenario,
      status: '',
      stepTitle: 'Run the maintained-files check',
      stepStatus:
          'The maintained files have not been checked yet. This step compares the generated subject files; you do not edit them directly here.',
      why:
          'The report flow depends on subject.md and subject.typ staying aligned before a report plan can be approved.',
      actions: <subject.SubjectGateAction>[
        _gateAction('compare_projections', 'Gather: Check Maintained Files'),
      ],
      detailLines: <String>['- generated files: subject.md and subject.typ'],
      statusRows: <subject.KeyValueRow>[
        _statusRow('Mode', 'Live subject workflow'),
        _statusRow('Phase', 'Itemize'),
        _statusRow('Subject', 'City bus ticketing modernization'),
        _statusRow('Itemization', 'not generated yet'),
      ],
    );
    snapshot.paneBundle.panes
      ..clear()
      ..addAll(<subject.SubjectPaneView>[
        (subject.SubjectPaneView()
          ..key = 'itemize_inventory'
          ..title = 'Item Inventory'
          ..lines.addAll(<String>['No data for Item Inventory.'])),
        (subject.SubjectPaneView()
          ..key = 'itemize_detail'
          ..title = 'Item Detail'
          ..lines.addAll(<String>['No data for Item Detail.'])),
      ]);
    return snapshot;
  }
}

enum _WorkflowBddScenario {
  weakProseV10DraftLaterRow,
  sameSubjectV2ThenV10DraftLaterNonincludedRow,
  weakProseV10ReviewPublicationBeforeAnalysis,
  sameSubjectV2ThenV10ReviewPublicationAfterPriorAnalysis,
  weakProseAfterConstructSuggestion,
  dstHappyPath,
  dstApprovedDraft,
  dstReviewPublicationOpenModel,
  dstBuiltPublicationOpenModel,
}

class _WorkflowBddDraftRow {
  _WorkflowBddDraftRow({
    required this.label,
    required this.detailTitle,
    required this.detailKey,
    required this.included,
  });

  final String label;
  final String detailTitle;
  final String detailKey;
  bool included;
}

class _WorkflowBddParityController extends WorkstationController {
  _WorkflowBddParityController(this.scenario);

  final _WorkflowBddScenario scenario;

  static const String _rootPath = '/tmp/workstation-root';
  static const String _clientSessionId = 'flutter-shell-workflow-bdd';
  static const String _subjectKey = 'city-bus-prose';

  final List<_WorkflowBddDraftRow> _draftRows = <_WorkflowBddDraftRow>[];
  String _draftLens = 'compose';
  int _selectedDraftRow = 0;
  String? _phaseNavOriginTab;
  bool _decisionAnalysisStarted = false;
  bool _decisionAnalysisCompleted = false;

  @override
  WorkstationState build() {
    _seedScenarioState();
    final initialTabKey = _initialTabKey();
    return WorkstationState(
      endpoint: _endpoint(),
      selectedRootPath: _rootPath,
      clientSessionId: _clientSessionId,
      currentTabKey: initialTabKey,
      statusText: 'Workflow BDD parity ready.',
      subjects: <subject.SubjectScenarioSummary>[_scenarioSummary()],
      selectedScenarioKey: _subjectKey,
      subjectSnapshot: _snapshotFor(initialTabKey),
      chatSnapshot: _chatSnapshot(
        status: 'ready',
        messages: const <shell.WorkstationChatMessage>[],
      ),
    );
  }

  void _seedScenarioState() {
    _draftLens = 'compose';
    _phaseNavOriginTab = null;
    _decisionAnalysisStarted = false;
    _decisionAnalysisCompleted = false;
    _draftRows
      ..clear()
      ..addAll(<_WorkflowBddDraftRow>[
        _WorkflowBddDraftRow(
          label: 'City bus payment continuity',
          detailTitle: 'City bus payment continuity',
          detailKey: 'draft-v2-base',
          included: true,
        ),
        _WorkflowBddDraftRow(
          label: 'Late v10 dependency gap',
          detailTitle: 'Late v10 dependency gap',
          detailKey: 'draft-v10-gap',
          included: false,
        ),
        _WorkflowBddDraftRow(
          label: 'Operational fallback path',
          detailTitle: 'Operational fallback path',
          detailKey: 'draft-v10-fallback',
          included: false,
        ),
      ]);
    _selectedDraftRow = switch (scenario) {
      _WorkflowBddScenario.weakProseV10DraftLaterRow => 2,
      _WorkflowBddScenario.sameSubjectV2ThenV10DraftLaterNonincludedRow => 1,
      _ => 0,
    };
    if (scenario == _WorkflowBddScenario.dstHappyPath) {
      _selectedDraftRow = 0;
    }
  }

  String _initialTabKey() {
    return switch (scenario) {
      _WorkflowBddScenario.weakProseV10ReviewPublicationBeforeAnalysis ||
      _WorkflowBddScenario
          .sameSubjectV2ThenV10ReviewPublicationAfterPriorAnalysis ||
      _WorkflowBddScenario.dstReviewPublicationOpenModel => 'review',
      _WorkflowBddScenario.dstBuiltPublicationOpenModel => 'publication',
      _ => 'draft',
    };
  }

  @override
  Future<void> showTab(String tabKey) async {
    final normalized = _normalizeTestTabKey(tabKey);
    if (normalized != state.currentTabKey) {
      _phaseNavOriginTab = state.currentTabKey;
    }
    state = state.copyWith(
      currentTabKey: normalized,
      subjectSnapshot: _snapshotFor(normalized),
    );
  }

  @override
  Future<String?> applyAction(
    String actionKey, {
    String assistantMessageText = '',
  }) async {
    switch (actionKey) {
      case 'create_decision_frame_from_selected_draft_item':
        if (scenario == _WorkflowBddScenario.dstHappyPath) {
          _decisionAnalysisStarted = true;
          state = state.copyWith(
            statusText:
                'Decision analysis started from DST discovery. Report plan updated.',
            subjectSnapshot: _snapshotFor('draft'),
          );
          return 'draft';
        }
        return state.currentTabKey;
      case 'analyze_decision_frame':
        if (scenario == _WorkflowBddScenario.dstHappyPath) {
          _decisionAnalysisCompleted = true;
          state = state.copyWith(
            currentTabKey: 'review',
            statusText: 'Decision analysis completed. Report plan updated.',
            subjectSnapshot: _snapshotFor('review'),
          );
          return 'review';
        }
        return state.currentTabKey;
      case 'toggle_selected_draft_review_item_in_decision_frame':
        if (scenario ==
            _WorkflowBddScenario.sameSubjectV2ThenV10DraftLaterNonincludedRow) {
          final row = _draftRows[_selectedDraftRow];
          row.included = !row.included;
          state = state.copyWith(
            statusText: 'Decision-frame selection updated.',
            subjectSnapshot: _snapshotFor(state.currentTabKey),
          );
        }
        return state.currentTabKey;
      case 'open_draft_model_view':
        final phaseNavOrigin = _phaseNavOriginTab;
        _phaseNavOriginTab = null;
        if (phaseNavOrigin == 'review' || phaseNavOrigin == 'publication') {
          _draftLens = 'compose';
          state = state.copyWith(
            statusText: 'Returned to Draft compose.',
            subjectSnapshot: _snapshotFor('draft'),
          );
          return 'draft';
        }
        _draftLens = 'model';
        state = state.copyWith(
          statusText: 'Moved Draft focus to Model.',
          subjectSnapshot: _snapshotFor('draft'),
        );
        return 'draft';
      default:
        return state.currentTabKey;
    }
  }

  @override
  Future<void> applyInteraction(
    String interactionKey, {
    int delta = 0,
    String? targetId,
    bool previewOnly = false,
  }) async {
    if (interactionKey == 'move_draft_review_cursor') {
      _selectedDraftRow = (_selectedDraftRow + delta).clamp(
        0,
        _draftRows.length - 1,
      );
      state = state.copyWith(
        statusText: 'Draft selection moved.',
        subjectSnapshot: _snapshotFor(state.currentTabKey),
      );
    }
  }

  subject.SubjectWorkflowSnapshotView _snapshotFor(String tabKey) {
    return switch (scenario) {
      _WorkflowBddScenario.weakProseV10DraftLaterRow => _draftComposeSnapshot(
        title: 'Start decision analysis',
        status:
            'A later weak-prose draft row is focused, but decision analysis still has not started.',
        why:
            'Start decision analysis before including more support or handing the draft to Review.',
        actions: <subject.SubjectGateAction>[
          _gateAction(
            'create_decision_frame_from_selected_draft_item',
            'Start Decision Analysis',
          ),
        ],
      ),
      _WorkflowBddScenario.sameSubjectV2ThenV10DraftLaterNonincludedRow =>
        _draftComposeSnapshot(
          title: 'Refresh the DST-backed decision analysis',
          status:
              'A later v10 row is outside the prior decision frame and requires a refresh.',
          why: 'Refresh DST analysis before handing the draft back to Review.',
          actions: <subject.SubjectGateAction>[
            _gateAction('refresh_dst_analysis', 'Refresh DST Analysis'),
          ],
        ),
      _WorkflowBddScenario.weakProseV10ReviewPublicationBeforeAnalysis =>
        _routeBackSnapshot(tabKey, refresh: false),
      _WorkflowBddScenario
          .sameSubjectV2ThenV10ReviewPublicationAfterPriorAnalysis =>
        _routeBackSnapshot(tabKey, refresh: true),
      _WorkflowBddScenario.weakProseAfterConstructSuggestion =>
        _draftComposeSnapshot(
          title: 'Start decision analysis',
          status:
              'Construct suggestion completed, and the draft is ready for decision analysis.',
          why:
              'Start decision analysis now, or open the model to inspect the case frame first.',
          actions: <subject.SubjectGateAction>[
            _gateAction(
              'create_decision_frame_from_selected_draft_item',
              'Start Decision Analysis',
            ),
            _gateAction('open_draft_model_view', 'Open Model'),
          ],
        ),
      _WorkflowBddScenario.dstHappyPath => _dstHappyPathSnapshot(tabKey),
      _WorkflowBddScenario.dstApprovedDraft => _approvedDraftSnapshot(),
      _WorkflowBddScenario.dstReviewPublicationOpenModel =>
        _reviewPublicationOpenModelSnapshot(tabKey),
      _WorkflowBddScenario.dstBuiltPublicationOpenModel =>
        _builtPublicationSnapshot(tabKey),
    };
  }

  subject.SubjectWorkflowSnapshotView _draftComposeSnapshot({
    required String title,
    required String status,
    required String why,
    required List<subject.SubjectGateAction> actions,
  }) {
    final selectedRow = _draftRows[_selectedDraftRow];
    final snapshot = _workflowSnapshot(
      phase: 'draft',
      phaseTitle: 'Draft',
      scenario: _scenarioSummary(),
      status: '',
      stepTitle: title,
      stepStatus: status,
      why: why,
      actions: actions,
      detailLines: <String>[
        '- selected review row: ${_selectedDraftRow + 1}',
        '- selected in decision frame: ${selectedRow.included ? 'yes' : 'no'}',
      ],
      statusRows: <subject.KeyValueRow>[
        _statusRow('Mode', 'Workflow BDD parity test'),
        _statusRow('Phase', 'Draft'),
        _statusRow('Subject', 'City bus prose subject'),
      ],
    );
    snapshot.paneBundle.panes
      ..clear()
      ..addAll(<subject.SubjectPaneView>[
        (subject.SubjectPaneView()
          ..key = 'draft_scope_tree'
          ..title = 'Draft Item Inventory'
          ..items.addAll(<subject.SubjectPaneItemView>[
            for (var index = 0; index < _draftRows.length; index++)
              _paneItem(
                entryId: _draftRows[index].detailKey,
                entryKind: 'draft_review_item',
                label: _draftRows[index].label,
                ordinal: index,
                selected: index == _selectedDraftRow,
                toggleable: true,
                checkState: _draftRows[index].included
                    ? 'checked'
                    : 'unchecked',
                semanticKind: 'claim',
                renderKind: index == 0 ? 'paragraph' : 'citation_callout',
              ),
          ])
          ..lines.addAll(<String>[
            for (var index = 0; index < _draftRows.length; index++)
              '${index == _selectedDraftRow ? '> ' : '  '}[${_draftRows[index].included ? 'x' : ' '}][ ] ${_draftRows[index].label}',
          ])),
        (subject.SubjectPaneView()
          ..key = 'draft_detail'
          ..title = selectedRow.detailTitle
          ..lines.addAll(<String>[
            'Draft detail key: ${selectedRow.detailKey}',
            'selected in decision frame | ${selectedRow.included ? 'yes' : 'no'}',
            'Selected construct: ${selectedRow.detailTitle}',
          ])),
      ]);
    return snapshot;
  }

  subject.SubjectWorkflowSnapshotView _draftModelSnapshot({
    required String title,
    required String status,
    required String why,
  }) {
    final snapshot = _workflowSnapshot(
      phase: 'draft',
      phaseTitle: 'Draft',
      scenario: _scenarioSummary(),
      status: '',
      stepTitle: title,
      stepStatus: status,
      why: why,
      detailLines: const <String>['- active lens: model'],
      statusRows: <subject.KeyValueRow>[
        _statusRow('Mode', 'Workflow BDD parity test'),
        _statusRow('Phase', 'Draft'),
        _statusRow('Subject', 'City bus prose subject'),
      ],
    );
    snapshot.paneBundle.panes
      ..clear()
      ..addAll(<subject.SubjectPaneView>[
        (subject.SubjectPaneView()
          ..key = 'draft_scope_tree'
          ..title = 'Case Objects'
          ..items.addAll(<subject.SubjectPaneItemView>[
            _paneItem(
              entryId: 'case-fare-payment',
              entryKind: 'construct_candidate',
              label: 'Fare payment continuity / Situation',
              ordinal: 0,
              selected: true,
              status: 'accepted',
              sortKind: 'situation',
            ),
            _paneItem(
              entryId: 'case-city-transit-authority',
              entryKind: 'construct_candidate',
              label: 'City transit authority / Actor',
              ordinal: 1,
              status: 'accepted',
              sortKind: 'actor',
            ),
            _paneItem(
              entryId: 'case-banking-rails',
              entryKind: 'construct_candidate',
              label: 'Banking rails / Dependency',
              ordinal: 2,
              status: 'accepted',
              sortKind: 'dependency',
            ),
          ])
          ..lines.addAll(<String>[
            '> [a] Fare payment continuity / Situation',
            '  [a] City transit authority / Actor',
            '  [a] Banking rails / Dependency',
          ])),
        (subject.SubjectPaneView()
          ..key = 'draft_model_main'
          ..title = 'Transformation Model'
          ..lines.addAll(<String>[
            'Tabs: Capabilities | Dependencies | Constraints | States | Transitions',
            'Capabilities: 3',
            'Dependencies: 2',
            'Constraints: 1',
          ])),
        (subject.SubjectPaneView()
          ..key = 'draft_detail'
          ..title = 'Situation Inspector'
          ..lines.addAll(<String>[
            'Case detail key: case-fare-payment',
            'Selected object: Fare payment continuity / Situation',
          ])),
        (subject.SubjectPaneView()
          ..key = 'draft_result'
          ..title = 'Issues & Validation'
          ..lines.addAll(<String>[
            'Open issues: 0',
            'recommendation status: pending',
          ])),
      ]);
    return snapshot;
  }

  subject.SubjectWorkflowSnapshotView _routeBackSnapshot(
    String tabKey, {
    required bool refresh,
  }) {
    final phase = _subjectPhaseForTestTab(tabKey);
    final reviewPhase = phase == 'publication' ? 'publication' : 'review';
    final phaseTitle = reviewPhase == 'publication' ? 'Publication' : 'Review';
    final primaryLabel = refresh
        ? 'Refresh DST Analysis'
        : 'Start Decision Analysis';
    final stepTitle = refresh
        ? 'Refresh the DST-backed decision analysis'
        : 'Start decision analysis';
    final why = refresh
        ? 'Return to Draft and refresh the DST-backed decision analysis before continuing.'
        : 'Return to Draft and complete the decision-analysis step before continuing.';
    final snapshot = _workflowSnapshot(
      phase: reviewPhase,
      phaseTitle: phaseTitle,
      scenario: _scenarioSummary(),
      status: '',
      stepTitle: stepTitle,
      stepStatus: reviewPhase == 'review'
          ? 'Review is blocked until Draft completes the decision-analysis recovery step.'
          : 'Publication is blocked until Draft completes the decision-analysis recovery step.',
      why: why,
      actions: <subject.SubjectGateAction>[
        _gateAction(
          refresh
              ? 'refresh_dst_analysis'
              : 'create_decision_frame_from_selected_draft_item',
          'Draft: $primaryLabel',
        ),
      ],
      statusRows: <subject.KeyValueRow>[
        _statusRow('Mode', 'Workflow BDD parity test'),
        _statusRow('Phase', phaseTitle),
        _statusRow('Subject', 'City bus prose subject'),
      ],
    );
    snapshot.paneBundle.panes
      ..clear()
      ..addAll(<subject.SubjectPaneView>[
        (subject.SubjectPaneView()
          ..key = '${reviewPhase}_scope_tree'
          ..title = 'Report Scope'
          ..lines.addAll(<String>[
            '> [x] Executive Summary',
            '  [x] Dependencies',
          ])),
        (subject.SubjectPaneView()
          ..key = '${reviewPhase}_scope_detail'
          ..title = 'Selection Details'
          ..lines.addAll(<String>[
            'Return to Draft first.',
            'Visible route-back action: $primaryLabel',
          ])),
      ]);
    return snapshot;
  }

  subject.SubjectWorkflowSnapshotView _dstHappyPathSnapshot(String tabKey) {
    if (tabKey == 'review' || _decisionAnalysisCompleted) {
      return _workflowSnapshot(
          phase: 'review',
          phaseTitle: 'Review',
          scenario: _scenarioSummary(),
          status: '',
          stepTitle: 'Approve the report and decision analysis',
          stepStatus:
              'The decision analysis has completed and the report plan is ready for Review approval.',
          why:
              'Approve the report plan before handing the publication package forward.',
          actions: <subject.SubjectGateAction>[
            _gateAction('approve_review', 'Approve For Report'),
          ],
          detailLines: const <String>[
            '- last receipt: Decision analysis completed. Report plan updated.',
          ],
          statusRows: <subject.KeyValueRow>[
            _statusRow('Mode', 'Workflow BDD parity test'),
            _statusRow('Phase', 'Review'),
            _statusRow('Subject', 'City bus prose subject'),
          ],
        )
        ..paneBundle.panes.clear()
        ..paneBundle.panes.addAll(<subject.SubjectPaneView>[
          (subject.SubjectPaneView()
            ..key = 'review_scope_tree'
            ..title = 'Report Scope'
            ..lines.addAll(<String>[
              '> [x] Decision Recommendation',
              '  [x] Execution Guidance',
            ])),
          (subject.SubjectPaneView()
            ..key = 'review_scope_detail'
            ..title = 'Selection Details'
            ..lines.addAll(<String>[
              'Decision analysis completed. Report plan updated.',
            ])),
        ]);
    }
    if (_decisionAnalysisStarted) {
      return _draftComposeSnapshot(
        title: 'Run decision analysis',
        status:
            'The decision frame is ready. Run the analysis to generate the report plan update.',
        why: 'Run decision analysis before moving the draft to Review.',
        actions: <subject.SubjectGateAction>[
          _gateAction('analyze_decision_frame', 'Run Decision Analysis'),
          _gateAction('open_draft_model_view', 'Open Model'),
        ],
      );
    }
    return _draftComposeSnapshot(
      title: 'Start decision analysis',
      status:
          'The curated draft is ready to seed the decision frame from the selected row.',
      why: 'Start decision analysis before Review becomes available.',
      actions: <subject.SubjectGateAction>[
        _gateAction(
          'create_decision_frame_from_selected_draft_item',
          'Start Decision Analysis',
        ),
        _gateAction('open_draft_model_view', 'Open Model'),
      ],
    );
  }

  subject.SubjectWorkflowSnapshotView _approvedDraftSnapshot() {
    if (_draftLens == 'model') {
      return _draftModelSnapshot(
        title: 'Inspect the decision-analysis model',
        status: 'The model surface is open for the approved draft composition.',
        why:
            'Inspect the case frame, transformation model, and explore alternatives before rerunning.',
      );
    }
    return _draftComposeSnapshot(
      title: 'Decision analysis is ready',
      status:
          'The latest decision-analysis receipt is available. Hand the draft to Review unless you need to rerun the analysis under a different policy.',
      why:
          'Open the model to inspect the current frame, or rerun the analysis under the next policy.',
      actions: <subject.SubjectGateAction>[
        _gateAction('rerun_analysis_balanced', 'Re-run Analysis (Balanced)'),
        _gateAction('open_draft_model_view', 'Open Model'),
      ],
    );
  }

  subject.SubjectWorkflowSnapshotView _reviewPublicationOpenModelSnapshot(
    String tabKey,
  ) {
    if (tabKey == 'draft') {
      return _draftComposeSnapshot(
        title: 'Draft composition is approved',
        status:
            'The attached decision analysis is current. Refresh it only if the included draft items change.',
        why:
            'Return to Review or Publication after checking the draft composition.',
        actions: <subject.SubjectGateAction>[
          _gateAction('refresh_dst_analysis', 'Refresh DST Analysis'),
          _gateAction('open_draft_model_view', 'Open Model'),
        ],
      );
    }
    if (tabKey == 'publication') {
      final snapshot = _workflowSnapshot(
        phase: 'publication',
        phaseTitle: 'Publication',
        scenario: _scenarioSummary(),
        status: '',
        stepTitle: 'The attached decision analysis is ready for publication',
        stepStatus:
            'Publication keeps Draft available so the model can still be inspected before the final build.',
        why:
            'Build the report only after any last Draft inspection is complete.',
        actions: <subject.SubjectGateAction>[
          _gateAction('build_report', 'Build Report'),
          _gateAction('open_draft_model_view', 'Draft: Open Model'),
        ],
        statusRows: <subject.KeyValueRow>[
          _statusRow('Mode', 'Workflow BDD parity test'),
          _statusRow('Phase', 'Publication'),
          _statusRow('Subject', 'City bus prose subject'),
        ],
      );
      snapshot.paneBundle.panes
        ..clear()
        ..addAll(<subject.SubjectPaneView>[
          (subject.SubjectPaneView()
            ..key = 'publication_scope_tree'
            ..title = 'Report Scope'
            ..lines.addAll(<String>[
              '> [x] Decision Recommendation',
              '  [x] Release Notes',
            ])),
          (subject.SubjectPaneView()
            ..key = 'publication_scope_detail'
            ..title = 'Selection Details'
            ..lines.addAll(<String>[
              'Open Model remains available from Publication.',
            ])),
        ]);
      return snapshot;
    }
    final snapshot = _workflowSnapshot(
      phase: 'review',
      phaseTitle: 'Review',
      scenario: _scenarioSummary(),
      status: '',
      stepTitle: 'Approve the report and decision analysis',
      stepStatus:
          'Review keeps Draft available so the model can still be inspected before approval.',
      why:
          'Approve the report plan once Draft no longer needs model inspection.',
      actions: <subject.SubjectGateAction>[
        _gateAction('approve_review', 'Approve For Report'),
        _gateAction('open_draft_model_view', 'Draft: Open Model'),
      ],
      statusRows: <subject.KeyValueRow>[
        _statusRow('Mode', 'Workflow BDD parity test'),
        _statusRow('Phase', 'Review'),
        _statusRow('Subject', 'City bus prose subject'),
      ],
    );
    snapshot.paneBundle.panes
      ..clear()
      ..addAll(<subject.SubjectPaneView>[
        (subject.SubjectPaneView()
          ..key = 'review_scope_tree'
          ..title = 'Report Scope'
          ..lines.addAll(<String>[
            '> [x] Decision Recommendation',
            '  [x] Execution Guidance',
          ])),
        (subject.SubjectPaneView()
          ..key = 'review_scope_detail'
          ..title = 'Selection Details'
          ..lines.addAll(<String>[
            'Open Model remains available from Review.',
          ])),
      ]);
    return snapshot;
  }

  subject.SubjectWorkflowSnapshotView _builtPublicationSnapshot(String tabKey) {
    if (tabKey == 'draft') {
      return _draftComposeSnapshot(
        title: 'Draft composition is approved',
        status:
            'The built publication still allows a return to Draft compose for inspection.',
        why:
            'Use Open Model only as a phase-nav back to Draft compose from the built publication state.',
        actions: <subject.SubjectGateAction>[
          _gateAction('refresh_dst_analysis', 'Refresh DST Analysis'),
          _gateAction('open_draft_model_view', 'Open Model'),
        ],
      );
    }
    final snapshot = _workflowSnapshot(
      phase: 'publication',
      phaseTitle: 'Publication',
      scenario: _scenarioSummary(),
      status: '',
      stepTitle: 'Publication build is complete',
      stepStatus:
          'The release packet is built, but Draft remains reachable for model inspection.',
      why:
          'Keep Open Model available alongside the publication artifact actions.',
      actions: <subject.SubjectGateAction>[
        _gateAction('open_draft_model_view', 'Draft: Open Model'),
      ],
      statusRows: <subject.KeyValueRow>[
        _statusRow('Mode', 'Workflow BDD parity test'),
        _statusRow('Phase', 'Publication'),
        _statusRow('Subject', 'City bus prose subject'),
      ],
    );
    snapshot.controlBundle.moreActions
      ..clear()
      ..addAll(<subject.SubjectActionSpec>[
        _actionSpec('publication_preview_report_pdf', 'Preview report.pdf'),
        _actionSpec('release_open_folder', 'Open Release Folder'),
        _actionSpec('publication_rebuild_report', 'Rebuild Report'),
      ]);
    snapshot.paneBundle.panes
      ..clear()
      ..addAll(<subject.SubjectPaneView>[
        (subject.SubjectPaneView()
          ..key = 'publication_scope_tree'
          ..title = 'Report Scope'
          ..lines.addAll(<String>[
            '> [x] Release Packet',
            '  [x] Decision Recommendation',
          ])),
        (subject.SubjectPaneView()
          ..key = 'publication_scope_detail'
          ..title = 'Selection Details'
          ..lines.addAll(<String>[
            'Built publication actions remain available.',
          ])),
      ]);
    return snapshot;
  }

  subject.SubjectScenarioSummary _scenarioSummary() {
    return _scenario(
      key: _subjectKey,
      subjectId: _subjectKey,
      title: 'City bus prose subject',
      summary: 'Synthetic workflow state for Flutter-visible BDD parity.',
    );
  }
}

class _PublicationBuildMoreActionController extends WorkstationController {
  static const String _rootPath = '/tmp/workstation-root';
  static const String _clientSessionId = 'flutter-shell-publication-build-more';
  static const String _subjectKey = 'city-bus-prose';

  @override
  WorkstationState build() {
    final scenario = _scenario(
      key: _subjectKey,
      subjectId: _subjectKey,
      title: 'City bus prose subject',
      summary:
          'Synthetic publication snapshot with build_report in More Actions.',
    );
    final snapshot = _workflowSnapshot(
      phase: 'publication',
      phaseTitle: 'Publication',
      scenario: scenario,
      status: '',
      stepTitle: 'Run decision analysis',
      stepStatus:
          'Draft recovery is still visible, but the publication build remains available.',
      why:
          'Build Report must stay visible even when its action key is plain build_report.',
      actions: <subject.SubjectGateAction>[
        _gateAction('draft', 'Draft: Run Decision Analysis'),
      ],
      statusRows: <subject.KeyValueRow>[
        _statusRow('Mode', 'Workflow BDD parity test'),
        _statusRow('Phase', 'Publication'),
        _statusRow('Subject', 'City bus prose subject'),
      ],
    );
    snapshot.controlBundle.moreActions
      ..clear()
      ..addAll(<subject.SubjectActionSpec>[
        _actionSpec('build_report', 'Build Report'),
        _actionSpec(
          'preview_publication_composition_diff',
          'Preview Report Plan Diff',
        ),
      ]);
    snapshot.paneBundle.panes
      ..clear()
      ..addAll(<subject.SubjectPaneView>[
        (subject.SubjectPaneView()
          ..key = 'publication_scope_tree'
          ..title = 'Report Scope'
          ..lines.addAll(<String>[
            '> [x] Decision Recommendation',
            '  [x] Execution Guidance',
          ])),
        (subject.SubjectPaneView()
          ..key = 'publication_scope_detail'
          ..title = 'Selection Details'
          ..lines.addAll(<String>[
            'Build Report should remain visible from More Actions.',
          ])),
      ]);

    return WorkstationState(
      endpoint: _endpoint(),
      selectedRootPath: _rootPath,
      clientSessionId: _clientSessionId,
      currentTabKey: 'publication',
      statusText: 'Synthetic publication build state ready.',
      subjects: <subject.SubjectScenarioSummary>[scenario],
      selectedScenarioKey: _subjectKey,
      subjectSnapshot: snapshot,
    );
  }
}

class _DraftLensTransitionController extends WorkstationController {
  static const String _rootPath = '/tmp/workstation-root';
  static const String _clientSessionId = 'flutter-shell-draft-lens';
  static const String _subjectKey = 'smart-city-travel';

  String _lens = 'compose';

  @override
  WorkstationState build() {
    return WorkstationState(
      endpoint: _endpoint(),
      selectedRootPath: _rootPath,
      clientSessionId: _clientSessionId,
      currentTabKey: 'draft',
      statusText: 'Connected to workstation-root.',
      subjects: <subject.SubjectScenarioSummary>[
        _scenario(
          key: _subjectKey,
          subjectId: _subjectKey,
          title: 'Smart City Travel',
          summary: 'A city transit authority wants to modernize fare payment.',
        ),
      ],
      selectedScenarioKey: _subjectKey,
      subjectSnapshot: _snapshotFor('draft'),
      chatSnapshot: _chatSnapshot(
        status: 'ready',
        messages: <shell.WorkstationChatMessage>[],
      ),
    );
  }

  @override
  Future<void> showTab(String tabKey) async {
    final normalized = _normalizeTestTabKey(tabKey);
    state = state.copyWith(
      currentTabKey: normalized,
      subjectSnapshot: _snapshotFor(normalized),
    );
  }

  @override
  Future<String?> applyAction(
    String actionKey, {
    String assistantMessageText = '',
  }) async {
    switch (actionKey) {
      case 'open_draft_model_view':
      case 'open_draft_model_model_view':
        _lens = 'model';
        state = state.copyWith(
          statusText: 'Moved Draft focus to Model.',
          subjectSnapshot: _snapshotFor('draft'),
        );
        return 'draft';
      case 'open_draft_model_frame_view':
        _lens = 'frame';
        state = state.copyWith(
          statusText: 'Moved Draft focus to Frame.',
          subjectSnapshot: _snapshotFor('draft'),
        );
        return 'draft';
      case 'open_draft_model_explore_view':
        _lens = 'explore';
        state = state.copyWith(
          statusText: 'Moved Draft focus to Explore.',
          subjectSnapshot: _snapshotFor('draft'),
        );
        return 'draft';
      case 'open_draft_compose_view':
        _lens = 'compose';
        state = state.copyWith(
          statusText: 'Moved Draft focus to Compose.',
          subjectSnapshot: _snapshotFor('draft'),
        );
        return 'draft';
      default:
        return state.currentTabKey;
    }
  }

  subject.SubjectWorkflowSnapshotView _snapshotFor(String tabKey) {
    final scenario = _scenario(
      key: _subjectKey,
      subjectId: _subjectKey,
      title: 'Smart City Travel',
      summary: 'A city transit authority wants to modernize fare payment.',
    );
    if (tabKey != 'draft' || _lens == 'compose') {
      final snapshot = _draftParitySnapshot();
      snapshot.phaseView.scenario = scenario;
      snapshot.phaseView.currentStep
        ..title = 'Shape the draft composition'
        ..status = 'The current draft inventory is ready for decision analysis.'
        ..why =
            'Open Model to inspect the case frame, transformation model, and explore alternatives.'
        ..actions.clear()
        ..actions.add(_gateAction('open_draft_model_view', 'Open Model'));
      snapshot.phaseView.statusView.rows
        ..clear()
        ..addAll(<subject.KeyValueRow>[
          _statusRow('Mode', 'Live subject workflow'),
          _statusRow('Phase', 'Draft'),
          _statusRow('Subject', 'Smart City Travel'),
          _statusRow(
            'Draft Composition',
            '5 included / 5 items, draft, current',
          ),
        ]);
      return snapshot;
    }

    final mainTitle = switch (_lens) {
      'frame' => 'Case Frame',
      'explore' => 'Explore Alternatives',
      _ => 'Transformation Model',
    };
    final mainLines = switch (_lens) {
      'frame' => <String>[
        'Tabs: Context | Actors | Objectives',
        'Case: Smart City Travel',
        'Actors: Banks and the payment processor',
        'Objectives: reduce cash handling',
        'Recommendation status: pending',
      ],
      'explore' => <String>[
        'Tabs: Alternatives | Compare | Rationale',
        'Recommendation status: pending',
        'Candidate paths: card-first rollout, hybrid migration',
        'Blocker: <none>',
      ],
      _ => <String>[
        'Tabs: Capabilities | Dependencies | Constraints | States | Transitions',
        'Capabilities: 2',
        'Dependencies: 1',
        'Constraints: 1',
        'Recommendation status: pending',
      ],
    };

    final snapshot = _workflowSnapshot(
      phase: 'draft',
      phaseTitle: 'Draft',
      scenario: scenario,
      status: '',
      stepTitle: 'Inspect the draft model lens',
      stepStatus: 'The draft model lens is active for the selected construct.',
      why:
          'Switch between Frame, Model, and Explore without losing the selected construct context.',
      detailLines: <String>[
        '- selected construct: Smart City Travel / Situation',
        '- active lens: ${_lens[0].toUpperCase()}${_lens.substring(1)}',
      ],
      statusRows: <subject.KeyValueRow>[
        _statusRow('Mode', 'Live subject workflow'),
        _statusRow('Phase', 'Draft'),
        _statusRow('Subject', 'Smart City Travel'),
        _statusRow('Draft Composition', '5 included / 5 items, draft, current'),
      ],
    );
    snapshot.paneBundle.panes
      ..clear()
      ..addAll(<subject.SubjectPaneView>[
        (subject.SubjectPaneView()
          ..key = 'draft_scope_tree'
          ..title = 'Case Objects (3)'
          ..lines.addAll(<String>[
            '> [x][ ] Smart City Travel / Situation',
            '  [x][ ] Banks and the payment processor',
            '  [x][ ] city regulator',
          ])),
        (subject.SubjectPaneView()
          ..key = 'draft_model_main'
          ..title = mainTitle
          ..lines.addAll(mainLines)),
        (subject.SubjectPaneView()
          ..key = 'draft_detail'
          ..title = 'Situation Inspector'
          ..lines.addAll(<String>[
            'Inspector: Smart City Travel / Situation',
            'Status Snapshot: current',
            'Selected object: Smart City Travel / Situation',
          ])),
        (subject.SubjectPaneView()
          ..key = 'draft_result'
          ..title = 'Issues & Validation'
          ..lines.addAll(<String>[
            'Status Snapshot: current',
            'open issues: 0',
            'recommendation status: pending',
          ])),
      ]);
    return snapshot;
  }
}

class _StructuredPaneParityController extends WorkstationController {
  static const String _rootPath = '/tmp/workstation-root';
  static const String _clientSessionId = 'flutter-shell-structured';
  static const String _subjectKey = 'smart-city-travel';

  @override
  WorkstationState build() {
    return WorkstationState(
      endpoint: _endpoint(),
      selectedRootPath: _rootPath,
      clientSessionId: _clientSessionId,
      currentTabKey: 'itemize',
      statusText: 'Live subject workflow ready.',
      subjects: <subject.SubjectScenarioSummary>[
        _scenario(
          key: _subjectKey,
          subjectId: _subjectKey,
          title: 'Smart City Travel',
          summary: 'A city transit authority wants to modernize fare payment.',
        ),
      ],
      selectedScenarioKey: _subjectKey,
      subjectSnapshot: _snapshotFor('itemize'),
      chatSnapshot: _chatSnapshot(
        status: 'ready',
        messages: <shell.WorkstationChatMessage>[],
      ),
    );
  }

  @override
  Future<void> showTab(String tabKey) async {
    final normalized = _normalizeTestTabKey(tabKey);
    state = state.copyWith(
      currentTabKey: normalized,
      subjectSnapshot: _snapshotFor(normalized),
    );
  }

  subject.SubjectWorkflowSnapshotView _snapshotFor(String tabKey) {
    switch (_subjectPhaseForTestTab(tabKey)) {
      case 'draft':
        return _draftParitySnapshot();
      default:
        return _itemizeParitySnapshot();
    }
  }
}

class _InteractivePaneParityController extends WorkstationController {
  static const String _rootPath = '/tmp/workstation-root';
  static const String _clientSessionId =
      'flutter-shell-interactive-pane-parity';
  static const String _subjectKey = 'smart-city-travel';

  final List<String> appliedActionKeys = <String>[];
  final List<({String key, int delta, bool previewOnly})> appliedInteractions =
      <({String key, int delta, bool previewOnly})>[];

  String _draftLens = 'compose';
  int _itemizeIndex = 0;
  int _draftComposeIndex = 0;
  int _draftCaseObjectIndex = 0;
  int _reviewIndex = 0;
  int _publicationIndex = 0;

  String get lastInteractionKey => appliedInteractions.last.key;
  int get lastInteractionDelta => appliedInteractions.last.delta;

  void clearLogs() {
    appliedActionKeys.clear();
    appliedInteractions.clear();
  }

  @override
  WorkstationState build() {
    return WorkstationState(
      endpoint: _endpoint(),
      selectedRootPath: _rootPath,
      clientSessionId: _clientSessionId,
      currentTabKey: 'itemize',
      statusText: 'Interactive pane parity ready.',
      subjects: <subject.SubjectScenarioSummary>[
        _scenario(
          key: _subjectKey,
          subjectId: _subjectKey,
          title: 'Smart City Travel',
          summary: 'A city transit authority wants to modernize fare payment.',
        ),
      ],
      selectedScenarioKey: _subjectKey,
      subjectSnapshot: _snapshotFor('itemize'),
      chatSnapshot: _chatSnapshot(
        status: 'ready',
        messages: <shell.WorkstationChatMessage>[],
      ),
    );
  }

  @override
  Future<void> showTab(String tabKey) async {
    final normalized = _normalizeTestTabKey(tabKey);
    state = state.copyWith(
      currentTabKey: normalized,
      subjectSnapshot: _snapshotFor(normalized),
    );
  }

  @override
  Future<String?> applyAction(
    String actionKey, {
    String assistantMessageText = '',
  }) async {
    appliedActionKeys.add(actionKey);
    if (actionKey == 'open_draft_model_view' ||
        actionKey == 'open_draft_model_model_view') {
      _draftLens = 'model';
    } else if (actionKey == 'open_draft_model_frame_view') {
      _draftLens = 'frame';
    } else if (actionKey == 'open_draft_model_explore_view') {
      _draftLens = 'explore';
    } else if (actionKey == 'open_draft_compose_view') {
      _draftLens = 'compose';
    }
    _refreshState(statusText: 'Applied action: $actionKey');
    return state.currentTabKey;
  }

  @override
  Future<void> applyInteraction(
    String interactionKey, {
    int delta = 0,
    String? targetId,
    bool previewOnly = false,
  }) async {
    appliedInteractions.add((
      key: interactionKey,
      delta: delta,
      previewOnly: previewOnly,
    ));
    if (interactionKey == 'move_itemize_cursor') {
      _itemizeIndex = (_itemizeIndex + delta).clamp(
        0,
        _itemizeFixtures.length - 1,
      );
    } else if (interactionKey == 'move_draft_review_cursor') {
      if (_draftLens == 'compose') {
        _draftComposeIndex = (_draftComposeIndex + delta).clamp(
          0,
          _draftComposeFixtures.length - 1,
        );
      } else {
        _draftCaseObjectIndex = (_draftCaseObjectIndex + delta).clamp(
          0,
          _draftCaseObjectFixtures.length - 1,
        );
      }
    } else if (interactionKey == 'move_report_scope_cursor') {
      if (state.currentTabKey == 'publication') {
        _publicationIndex = (_publicationIndex + delta).clamp(
          0,
          _publicationFixtures.length - 1,
        );
      } else {
        _reviewIndex = (_reviewIndex + delta).clamp(
          0,
          _reviewFixtures.length - 1,
        );
      }
    }
    _refreshState(statusText: 'Applied interaction: $interactionKey');
  }

  void _refreshState({required String statusText}) {
    state = state.copyWith(
      statusText: statusText,
      subjectSnapshot: _snapshotFor(state.currentTabKey),
    );
  }

  subject.SubjectWorkflowSnapshotView _snapshotFor(String tabKey) {
    switch (_subjectPhaseForTestTab(tabKey)) {
      case 'draft':
        return _draftSnapshot();
      case 'review':
        return _reviewSnapshot();
      case 'publication':
        return _publicationSnapshot();
      default:
        return _itemizeSnapshot();
    }
  }

  subject.SubjectWorkflowSnapshotView _itemizeSnapshot() {
    final selected = _itemizeFixtures[_itemizeIndex];
    final snapshot = _workflowSnapshot(
      phase: 'itemize',
      phaseTitle: 'Itemize',
      scenario: _interactiveScenario(),
      status: '',
      stepTitle: 'Orient the selected item',
      stepStatus:
          'Current item: ${selected.detailTitle} [claim] status=candidate.',
      why: 'Use row selection to update the detail pane before Draft.',
      detailLines: <String>[
        '- selected index: $_itemizeIndex',
        '- interaction mode: itemize inventory',
      ],
      statusRows: <subject.KeyValueRow>[
        _statusRow('Mode', 'Interactive parity test'),
        _statusRow('Phase', 'Itemize'),
        _statusRow('Subject', 'Smart City Travel'),
      ],
    );
    snapshot.paneBundle.panes
      ..clear()
      ..addAll(<subject.SubjectPaneView>[
        (subject.SubjectPaneView()
          ..key = 'itemize_inventory'
          ..title = 'Item Inventory'
          ..items.addAll(<subject.SubjectPaneItemView>[
            for (var index = 0; index < _itemizeFixtures.length; index++)
              _paneItem(
                entryId: _itemizeFixtures[index].detailKey,
                entryKind: 'itemized_item',
                label: _itemizeFixtures[index].detailTitle,
                ordinal: index,
                selected: index == _itemizeIndex,
                status: 'candidate',
                semanticKind: 'claim',
                attributes: <subject.KeyValueRow>[
                  _statusRow(
                    'decision_role',
                    _itemizeFixtures[index].inventoryLabel.split(' - ').first,
                  ),
                ],
              ),
          ])
          ..lines.addAll(<String>[
            'Items (3)',
            for (var index = 0; index < _itemizeFixtures.length; index++)
              '${index == _itemizeIndex ? '> ' : '  '}[c] ${_itemizeFixtures[index].inventoryLabel}',
          ])),
        (subject.SubjectPaneView()
          ..key = 'itemize_detail'
          ..title = selected.detailTitle
          ..lines.addAll(<String>[
            'Decision role: candidate',
            'Item detail key: ${selected.detailKey}',
            'Selected item: ${selected.detailTitle}',
          ])),
      ]);
    return snapshot;
  }

  subject.SubjectWorkflowSnapshotView _draftSnapshot() {
    if (_draftLens == 'compose') {
      final selected = _draftComposeFixtures[_draftComposeIndex];
      final snapshot = _workflowSnapshot(
        phase: 'draft',
        phaseTitle: 'Draft',
        scenario: _interactiveScenario(),
        status: '',
        stepTitle: 'Accept this construct into decision analysis',
        stepStatus:
            'Current construct: ${selected.detailTitle} [support] status=candidate.',
        why: 'Draft row selection must drive the companion detail pane.',
        actions: <subject.SubjectGateAction>[
          _gateAction('open_draft_model_view', 'Open Model'),
        ],
        statusRows: <subject.KeyValueRow>[
          _statusRow('Mode', 'Interactive parity test'),
          _statusRow('Phase', 'Draft'),
          _statusRow('Subject', 'Smart City Travel'),
        ],
      );
      snapshot.paneBundle.panes
        ..clear()
        ..addAll(<subject.SubjectPaneView>[
          (subject.SubjectPaneView()
            ..key = 'draft_scope_tree'
            ..title = 'Draft Item Inventory'
            ..items.addAll(<subject.SubjectPaneItemView>[
              for (var index = 0; index < _draftComposeFixtures.length; index++)
                _paneItem(
                  entryId: _draftComposeFixtures[index].detailKey,
                  entryKind: 'draft_review_item',
                  label: _draftComposeFixtures[index].inventoryLabel,
                  ordinal: index,
                  selected: index == _draftComposeIndex,
                  toggleable: true,
                  checkState: 'checked',
                  semanticKind: 'claim',
                  renderKind: index == 0 ? 'paragraph' : 'citation_callout',
                ),
            ])
            ..lines.addAll(<String>[
              for (var index = 0; index < _draftComposeFixtures.length; index++)
                '${index == _draftComposeIndex ? '> ' : '  '}[x][ ] ${_draftComposeFixtures[index].inventoryLabel}',
            ])),
          (subject.SubjectPaneView()
            ..key = 'draft_detail'
            ..title = selected.detailTitle
            ..lines.addAll(<String>[
              'Draft detail key: ${selected.detailKey}',
              'Selected construct: ${selected.detailTitle}',
            ])),
        ]);
      return snapshot;
    }

    final selected = _draftCaseObjectFixtures[_draftCaseObjectIndex];
    final mainTitle = switch (_draftLens) {
      'frame' => 'Case Frame',
      'explore' => 'Explore Alternatives',
      _ => 'Transformation Model',
    };
    final mainLines = switch (_draftLens) {
      'frame' => <String>[
        'Focused object: ${selected.detailTitle}',
        'Frame detail: actor and objective alignment.',
      ],
      'explore' => <String>[
        'Focused object: ${selected.detailTitle}',
        'Explore detail: compare alternative rollout paths.',
      ],
      _ => <String>[
        'Focused object: ${selected.detailTitle}',
        'Model detail: dependencies and transitions.',
      ],
    };
    final snapshot = _workflowSnapshot(
      phase: 'draft',
      phaseTitle: 'Draft',
      scenario: _interactiveScenario(),
      status: '',
      stepTitle: 'Inspect the selected case object',
      stepStatus:
          'The ${_draftLens[0].toUpperCase()}${_draftLens.substring(1)} lens is active.',
      why: 'Case-object selection must persist while the lens changes.',
      detailLines: <String>['- active lens: $_draftLens'],
      statusRows: <subject.KeyValueRow>[
        _statusRow('Mode', 'Interactive parity test'),
        _statusRow('Phase', 'Draft'),
        _statusRow('Subject', 'Smart City Travel'),
      ],
    );
    snapshot.paneBundle.panes
      ..clear()
      ..addAll(<subject.SubjectPaneView>[
        (subject.SubjectPaneView()
          ..key = 'draft_scope_tree'
          ..title = 'Case Objects'
          ..items.addAll(<subject.SubjectPaneItemView>[
            for (
              var index = 0;
              index < _draftCaseObjectFixtures.length;
              index++
            )
              _paneItem(
                entryId: _draftCaseObjectFixtures[index].detailKey,
                entryKind: 'construct_candidate',
                label: _draftCaseObjectFixtures[index].inventoryLabel,
                ordinal: index,
                selected: index == _draftCaseObjectIndex,
                status: 'accepted',
                sortKind: _draftCaseObjectFixtures[index].inventoryLabel
                    .split(' / ')
                    .last
                    .toLowerCase(),
              ),
          ])
          ..lines.addAll(<String>[
            for (
              var index = 0;
              index < _draftCaseObjectFixtures.length;
              index++
            )
              '${index == _draftCaseObjectIndex ? '> ' : '  '}[a] ${_draftCaseObjectFixtures[index].inventoryLabel}',
          ])),
        (subject.SubjectPaneView()
          ..key = 'draft_model_main'
          ..title = mainTitle
          ..lines.addAll(mainLines)),
        (subject.SubjectPaneView()
          ..key = 'draft_detail'
          ..title = selected.detailTitle
          ..lines.addAll(<String>[
            'Case detail key: ${selected.detailKey}',
            'Selected object: ${selected.detailTitle}',
          ])),
        (subject.SubjectPaneView()
          ..key = 'draft_result'
          ..title = 'Issues & Validation'
          ..lines.addAll(<String>[
            'Open issues: 0',
            'Selected object: ${selected.detailTitle}',
          ])),
      ]);
    return snapshot;
  }

  subject.SubjectWorkflowSnapshotView _reviewSnapshot() {
    final selected = _reviewFixtures[_reviewIndex];
    final snapshot = _workflowSnapshot(
      phase: 'review',
      phaseTitle: 'Review',
      scenario: _interactiveScenario(),
      status: '',
      stepTitle: 'Inspect the selected report scope item',
      stepStatus: 'Current report scope item: ${selected.detailTitle}.',
      why: 'Review scope selection must drive Selection Details.',
      statusRows: <subject.KeyValueRow>[
        _statusRow('Mode', 'Interactive parity test'),
        _statusRow('Phase', 'Review'),
        _statusRow('Subject', 'Smart City Travel'),
      ],
    );
    snapshot.paneBundle.panes
      ..clear()
      ..addAll(<subject.SubjectPaneView>[
        (subject.SubjectPaneView()
          ..key = 'review_scope_tree'
          ..title = 'Report Scope'
          ..items.addAll(<subject.SubjectPaneItemView>[
            for (var index = 0; index < _reviewFixtures.length; index++)
              _paneItem(
                entryId: _reviewFixtures[index].detailKey,
                entryKind: 'report_scope_item',
                label: _reviewFixtures[index].inventoryLabel,
                ordinal: index,
                selected: index == _reviewIndex,
                toggleable: true,
                checkState: 'checked',
                held: _reviewFixtures[index].held,
                depth: _reviewFixtures[index].indent,
              ),
          ])
          ..lines.addAll(<String>[
            'Review Scope Tree',
            for (var index = 0; index < _reviewFixtures.length; index++)
              _reportScopeLine(
                selected: index == _reviewIndex,
                held: _reviewFixtures[index].held,
                indent: _reviewFixtures[index].indent,
                label: _reviewFixtures[index].inventoryLabel,
              ),
          ])),
        (subject.SubjectPaneView()
          ..key = 'review_scope_detail'
          ..title = selected.detailTitle
          ..lines.addAll(<String>[
            'Review detail key: ${selected.detailKey}',
            'Selected report scope item: ${selected.detailTitle}',
          ])),
      ]);
    return snapshot;
  }

  subject.SubjectWorkflowSnapshotView _publicationSnapshot() {
    final selected = _publicationFixtures[_publicationIndex];
    final snapshot = _workflowSnapshot(
      phase: 'publication',
      phaseTitle: 'Publication',
      scenario: _interactiveScenario(),
      status: '',
      stepTitle: 'Inspect the selected publication scope item',
      stepStatus: 'Current publication scope item: ${selected.detailTitle}.',
      why: 'Publication scope selection must drive Selection Details.',
      statusRows: <subject.KeyValueRow>[
        _statusRow('Mode', 'Interactive parity test'),
        _statusRow('Phase', 'Publication'),
        _statusRow('Subject', 'Smart City Travel'),
      ],
    );
    snapshot.paneBundle.panes
      ..clear()
      ..addAll(<subject.SubjectPaneView>[
        (subject.SubjectPaneView()
          ..key = 'publication_scope_tree'
          ..title = 'Report Scope'
          ..items.addAll(<subject.SubjectPaneItemView>[
            for (var index = 0; index < _publicationFixtures.length; index++)
              _paneItem(
                entryId: _publicationFixtures[index].detailKey,
                entryKind: 'report_scope_item',
                label: _publicationFixtures[index].inventoryLabel,
                ordinal: index,
                selected: index == _publicationIndex,
                toggleable: true,
                checkState: 'checked',
                held: _publicationFixtures[index].held,
                depth: _publicationFixtures[index].indent,
              ),
          ])
          ..lines.addAll(<String>[
            'Publication Scope Tree',
            for (var index = 0; index < _publicationFixtures.length; index++)
              _reportScopeLine(
                selected: index == _publicationIndex,
                held: _publicationFixtures[index].held,
                indent: _publicationFixtures[index].indent,
                label: _publicationFixtures[index].inventoryLabel,
              ),
          ])),
        (subject.SubjectPaneView()
          ..key = 'publication_scope_detail'
          ..title = selected.detailTitle
          ..lines.addAll(<String>[
            'Publication detail key: ${selected.detailKey}',
            'Selected publication scope item: ${selected.detailTitle}',
          ])),
      ]);
    return snapshot;
  }

  subject.SubjectScenarioSummary _interactiveScenario() {
    return _scenario(
      key: _subjectKey,
      subjectId: _subjectKey,
      title: 'Smart City Travel',
      summary: 'A city transit authority wants to modernize fare payment.',
    );
  }
}

class _InteractiveControlParityController extends WorkstationController {
  static const String _rootPath = '/tmp/workstation-root';
  static const String _clientSessionId =
      'flutter-shell-interactive-control-parity';
  static const String _subjectKey = 'smart-city-travel';

  final List<String> appliedActionKeys = <String>[];
  int _selectedDraftIndex = 0;
  String _selectedSemanticKind = 'claim';
  final List<bool> _draftIncludedStates = <bool>[true, false];

  @override
  WorkstationState build() {
    return WorkstationState(
      endpoint: _endpoint(),
      selectedRootPath: _rootPath,
      clientSessionId: _clientSessionId,
      currentTabKey: 'draft',
      statusText: 'Interactive controls ready.',
      subjects: <subject.SubjectScenarioSummary>[
        _scenario(
          key: _subjectKey,
          subjectId: _subjectKey,
          title: 'Smart City Travel',
          summary: 'A city transit authority wants to modernize fare payment.',
        ),
      ],
      selectedScenarioKey: _subjectKey,
      subjectSnapshot: _snapshot(),
      chatSnapshot: _chatSnapshot(
        status: 'ready',
        messages: <shell.WorkstationChatMessage>[],
      ),
    );
  }

  @override
  Future<String?> applyAction(
    String actionKey, {
    String assistantMessageText = '',
  }) async {
    appliedActionKeys.add(actionKey);
    if (actionKey == 'toggle_selected_draft_review_item_in_decision_frame') {
      _draftIncludedStates[_selectedDraftIndex] =
          !_draftIncludedStates[_selectedDraftIndex];
    } else if (actionKey.startsWith(
      'set_selected_draft_review_semantic_kind:',
    )) {
      _selectedSemanticKind = actionKey.split(':').last;
    }
    state = state.copyWith(
      statusText: 'Applied action: $actionKey',
      subjectSnapshot: _snapshot(),
    );
    return state.currentTabKey;
  }

  @override
  Future<void> applyInteraction(
    String interactionKey, {
    int delta = 0,
    String? targetId,
    bool previewOnly = false,
  }) async {
    if (interactionKey == 'move_draft_review_cursor') {
      _selectedDraftIndex = (_selectedDraftIndex + delta).clamp(0, 1);
      state = state.copyWith(
        statusText: 'Applied interaction: $interactionKey',
        subjectSnapshot: _snapshot(),
      );
    }
  }

  subject.SubjectWorkflowSnapshotView _snapshot() {
    final selectedIncluded = _draftIncludedStates[_selectedDraftIndex];
    final selectedTitle = _selectedDraftIndex == 0
        ? 'Smart City Travel'
        : 'Banks and the payment processor';
    final snapshot = _workflowSnapshot(
      phase: 'draft',
      phaseTitle: 'Draft',
      scenario: _scenario(
        key: _subjectKey,
        subjectId: _subjectKey,
        title: 'Smart City Travel',
        summary: 'A city transit authority wants to modernize fare payment.',
      ),
      status: '',
      stepTitle: 'Adjust the selected draft item',
      stepStatus: 'Use More Actions to change draft rendering metadata.',
      why: 'Selectors and switches must dispatch the same workflow actions.',
      statusRows: <subject.KeyValueRow>[
        _statusRow('Mode', 'Interactive control parity'),
        _statusRow('Phase', 'Draft'),
        _statusRow('Subject', 'Smart City Travel'),
      ],
    );
    snapshot.controlBundle = (subject.SubjectControlBundleView()
      ..phase = 'draft'
      ..selects.add(
        subject.SubjectSelectSpecView()
          ..key = 'draft_semantic_kind'
          ..label = 'Semantic Kind'
          ..value = _selectedSemanticKind
          ..enabled = true
          ..options.addAll(<subject.SubjectOption>[
            (subject.SubjectOption()
              ..label = 'Claim'
              ..value = 'claim'),
            (subject.SubjectOption()
              ..label = 'Definition'
              ..value = 'definition'),
          ]),
      )
      ..switches.add(
        subject.SubjectSwitchSpecView()
          ..key = 'draft_decision_included'
          ..label = 'In Decision'
          ..value = selectedIncluded
          ..enabled = true,
      ));
    snapshot.paneBundle.panes
      ..clear()
      ..addAll(<subject.SubjectPaneView>[
        (subject.SubjectPaneView()
          ..key = 'draft_scope_tree'
          ..title = 'Draft Item Inventory'
          ..items.addAll(<subject.SubjectPaneItemView>[
            _paneItem(
              entryId: 'draft-smart-city-travel',
              entryKind: 'draft_review_item',
              label: 'Smart City Travel',
              ordinal: 0,
              selected: _selectedDraftIndex == 0,
              toggleable: true,
              checkState: _draftIncludedStates[0] ? 'checked' : 'unchecked',
              semanticKind: _selectedDraftIndex == 0
                  ? _selectedSemanticKind
                  : 'claim',
              renderKind: 'paragraph',
            ),
            _paneItem(
              entryId: 'draft-banks',
              entryKind: 'draft_review_item',
              label: 'Banks and the payment processor',
              ordinal: 1,
              selected: _selectedDraftIndex == 1,
              toggleable: true,
              checkState: _draftIncludedStates[1] ? 'checked' : 'unchecked',
              semanticKind: _selectedDraftIndex == 1
                  ? _selectedSemanticKind
                  : 'claim',
              renderKind: 'citation_callout',
            ),
          ])
          ..lines.addAll(<String>[
            '${_selectedDraftIndex == 0 ? '> ' : '  '}[${_draftIncludedStates[0] ? 'x' : ' '}][ ] Smart City Travel',
            '${_selectedDraftIndex == 1 ? '> ' : '  '}[${_draftIncludedStates[1] ? 'x' : ' '}][ ] Banks and the payment processor',
          ])),
        (subject.SubjectPaneView()
          ..key = 'draft_detail'
          ..title = selectedTitle
          ..lines.addAll(<String>[
            'label: $selectedTitle',
            'semantic kind: ${_selectedSemanticKind == 'claim' ? 'Claim' : 'Definition'}',
            'included in draft composition: yes',
            'selected in decision frame | ${selectedIncluded ? 'yes' : 'no'}',
          ])),
      ]);
    return snapshot;
  }
}

class _InteractiveSelectionFixture {
  const _InteractiveSelectionFixture({
    required this.inventoryLabel,
    required this.detailTitle,
    required this.detailKey,
    this.indent = 0,
    this.held = false,
  });

  final String inventoryLabel;
  final String detailTitle;
  final String detailKey;
  final int indent;
  final bool held;
}

const List<_InteractiveSelectionFixture>
_itemizeFixtures = <_InteractiveSelectionFixture>[
  _InteractiveSelectionFixture(
    inventoryLabel: 'actor - Banks and the payment processor',
    detailTitle: 'Banks and the payment processor',
    detailKey: 'itemize-banks',
  ),
  _InteractiveSelectionFixture(
    inventoryLabel:
        'objective - changes that can be implemented without disrupting daily service',
    detailTitle:
        'changes that can be implemented without disrupting daily service',
    detailKey: 'itemize-objective',
  ),
  _InteractiveSelectionFixture(
    inventoryLabel: 'actor - city regulator',
    detailTitle: 'city regulator',
    detailKey: 'itemize-regulator',
  ),
];

const List<_InteractiveSelectionFixture> _draftComposeFixtures =
    <_InteractiveSelectionFixture>[
      _InteractiveSelectionFixture(
        inventoryLabel: 'Smart City Travel',
        detailTitle: 'Smart City Travel',
        detailKey: 'draft-transit',
      ),
      _InteractiveSelectionFixture(
        inventoryLabel: 'Banks and the payment processor',
        detailTitle: 'Banks and the payment processor',
        detailKey: 'draft-banks',
      ),
      _InteractiveSelectionFixture(
        inventoryLabel: 'city regulator',
        detailTitle: 'city regulator',
        detailKey: 'draft-regulator',
      ),
    ];

const List<_InteractiveSelectionFixture> _draftCaseObjectFixtures =
    <_InteractiveSelectionFixture>[
      _InteractiveSelectionFixture(
        inventoryLabel: 'Smart City Travel / Situation',
        detailTitle: 'Situation Inspector',
        detailKey: 'case-situation',
      ),
      _InteractiveSelectionFixture(
        inventoryLabel: 'Banks and the payment processor / Actor',
        detailTitle: 'Actor Inspector',
        detailKey: 'case-banks',
      ),
      _InteractiveSelectionFixture(
        inventoryLabel: 'city regulator / Constraint',
        detailTitle: 'Constraint Inspector',
        detailKey: 'case-regulator',
      ),
    ];

const List<_InteractiveSelectionFixture> _reviewFixtures =
    <_InteractiveSelectionFixture>[
      _InteractiveSelectionFixture(
        inventoryLabel: 'Executive Summary',
        detailTitle: 'Executive Summary',
        detailKey: 'review-summary',
      ),
      _InteractiveSelectionFixture(
        inventoryLabel: 'Payment Actors',
        detailTitle: 'Payment Actors',
        detailKey: 'review-actors',
        held: true,
      ),
      _InteractiveSelectionFixture(
        inventoryLabel: 'Banks and the payment processor',
        detailTitle: 'Banks and the payment processor',
        detailKey: 'review-banks',
        indent: 1,
      ),
      _InteractiveSelectionFixture(
        inventoryLabel: 'Operational Risks',
        detailTitle: 'Operational Risks',
        detailKey: 'review-risks',
      ),
      _InteractiveSelectionFixture(
        inventoryLabel: 'Fare Device Rollout',
        detailTitle: 'Fare Device Rollout',
        detailKey: 'review-rollout',
        indent: 1,
      ),
      _InteractiveSelectionFixture(
        inventoryLabel: 'Commuter Education',
        detailTitle: 'Commuter Education',
        detailKey: 'review-education',
        indent: 1,
      ),
      _InteractiveSelectionFixture(
        inventoryLabel: 'Settlement Timing',
        detailTitle: 'Settlement Timing',
        detailKey: 'review-settlement',
        indent: 1,
      ),
      _InteractiveSelectionFixture(
        inventoryLabel: 'Reconciliation Exceptions',
        detailTitle: 'Reconciliation Exceptions',
        detailKey: 'review-reconciliation',
      ),
      _InteractiveSelectionFixture(
        inventoryLabel: 'Passenger Support',
        detailTitle: 'Passenger Support',
        detailKey: 'review-support',
        indent: 1,
      ),
      _InteractiveSelectionFixture(
        inventoryLabel: 'Regulatory Assurances',
        detailTitle: 'Regulatory Assurances',
        detailKey: 'review-assurances',
      ),
      _InteractiveSelectionFixture(
        inventoryLabel: 'Contingency Timeline',
        detailTitle: 'Contingency Timeline',
        detailKey: 'review-contingency',
        indent: 1,
      ),
    ];

const List<_InteractiveSelectionFixture> _publicationFixtures =
    <_InteractiveSelectionFixture>[
      _InteractiveSelectionFixture(
        inventoryLabel: 'Summary Release',
        detailTitle: 'Summary Release',
        detailKey: 'publication-summary',
      ),
      _InteractiveSelectionFixture(
        inventoryLabel: 'Supporting Evidence',
        detailTitle: 'Supporting Evidence',
        detailKey: 'publication-support',
        held: true,
      ),
      _InteractiveSelectionFixture(
        inventoryLabel: 'Release Draft',
        detailTitle: 'Release Draft',
        detailKey: 'publication-release',
        indent: 1,
      ),
      _InteractiveSelectionFixture(
        inventoryLabel: 'Evidence Appendix',
        detailTitle: 'Evidence Appendix',
        detailKey: 'publication-appendix',
      ),
      _InteractiveSelectionFixture(
        inventoryLabel: 'Operational FAQ',
        detailTitle: 'Operational FAQ',
        detailKey: 'publication-faq',
        indent: 1,
      ),
      _InteractiveSelectionFixture(
        inventoryLabel: 'Partner Messaging',
        detailTitle: 'Partner Messaging',
        detailKey: 'publication-partners',
        indent: 1,
      ),
      _InteractiveSelectionFixture(
        inventoryLabel: 'Rollout Notice',
        detailTitle: 'Rollout Notice',
        detailKey: 'publication-rollout',
      ),
      _InteractiveSelectionFixture(
        inventoryLabel: 'Resident Advisory',
        detailTitle: 'Resident Advisory',
        detailKey: 'publication-advisory',
        indent: 1,
      ),
      _InteractiveSelectionFixture(
        inventoryLabel: 'Accessibility Notes',
        detailTitle: 'Accessibility Notes',
        detailKey: 'publication-accessibility',
      ),
      _InteractiveSelectionFixture(
        inventoryLabel: 'Change Calendar',
        detailTitle: 'Change Calendar',
        detailKey: 'publication-calendar',
        indent: 1,
      ),
      _InteractiveSelectionFixture(
        inventoryLabel: 'Distribution Checklist',
        detailTitle: 'Distribution Checklist',
        detailKey: 'publication-distribution',
      ),
    ];

String _reportScopeLine({
  required bool selected,
  required bool held,
  required int indent,
  required String label,
}) {
  final pointer = selected ? '> ' : '  ';
  final hold = held ? 'h ' : '  ';
  final indentation = List<String>.filled(indent, '  ').join();
  return '$pointer$hold$indentation[x] $label';
}

subject.SubjectPaneItemView _paneItem({
  required String entryId,
  required String entryKind,
  required String label,
  required int ordinal,
  bool selectable = true,
  bool selected = false,
  bool toggleable = false,
  String checkState = 'none',
  bool held = false,
  int depth = 0,
  String status = '',
  String semanticKind = '',
  String renderKind = '',
  String sortKind = '',
  List<subject.KeyValueRow> attributes = const <subject.KeyValueRow>[],
}) {
  return subject.SubjectPaneItemView()
    ..entryId = entryId
    ..entryKind = entryKind
    ..label = label
    ..ordinal = ordinal
    ..selectable = selectable
    ..selected = selected
    ..toggleable = toggleable
    ..checkState = checkState
    ..held = held
    ..depth = depth
    ..status = status
    ..semanticKind = semanticKind
    ..renderKind = renderKind
    ..sortKind = sortKind
    ..attributes.addAll(attributes);
}

EndpointConfig _endpoint() {
  return const EndpointConfig(
    grpcHost: '127.0.0.1',
    grpcPort: 50051,
    grpcWebUrl: 'http://127.0.0.1:8080',
  );
}

shell.ShellTextView _textView(String text) {
  return shell.ShellTextView()..text = text;
}

shell.ChatSnapshotResponse _chatSnapshot({
  required String status,
  required List<shell.WorkstationChatMessage> messages,
}) {
  return shell.ChatSnapshotResponse()
    ..sessionStatus = status
    ..messages.addAll(messages);
}

shell.WorkstationChatMessage _message({
  required String role,
  required String content,
}) {
  return shell.WorkstationChatMessage()
    ..role = role
    ..content = content;
}

bootstrap.WorkstationRootDescriptor _rootDescriptor(String rootPath) {
  return bootstrap.WorkstationRootDescriptor()
    ..rootId = 'workstation-root'
    ..label = 'Workstation Root'
    ..rootPath = rootPath
    ..workspaceName = 'workstation-root'
    ..isDefault = true;
}

subject.SubjectScenarioSummary _placeholderScenario() {
  return _scenario(
    key: '__learning_context_empty__',
    subjectId: '',
    title: 'No Subject Yet',
    summary:
        'Use Import Markdown File, Learn URL, or chat-backed capture to create the first subject-scoped corpus context.',
    isPlaceholder: true,
  );
}

subject.SubjectWorkflowSnapshotView _placeholderSnapshot(String tabKey) {
  final phase = _subjectPhaseForTestTab(tabKey);
  final scenario = _placeholderScenario();
  switch (phase) {
    case 'itemize':
      return _workflowSnapshot(
        phase: 'itemize',
        phaseTitle: 'Itemize',
        scenario: scenario,
        status: 'Stage learning before itemization',
        why: 'Itemization opens after the first subject is created in Gather.',
        actions: <subject.SubjectGateAction>[
          _gateAction('use_markdown_ingress', 'Import Markdown File'),
          _gateAction('use_url_ingress', 'Learn URL'),
          _gateAction('ask_follow_up', 'Ask Follow-up In Chat'),
        ],
        statusRows: <subject.KeyValueRow>[
          _statusRow('Mode', 'Placeholder workflow'),
          _statusRow('Phase', 'Itemize'),
          _statusRow('Subject', 'No Subject Yet'),
        ],
      );
    case 'draft':
      return _workflowSnapshot(
        phase: 'draft',
        phaseTitle: 'Draft',
        scenario: scenario,
        status: 'Draft waits for itemized support',
        why:
            'Draft opens after Gather and Itemize establish maintained support.',
        statusRows: <subject.KeyValueRow>[
          _statusRow('Mode', 'Placeholder workflow'),
          _statusRow('Phase', 'Draft'),
          _statusRow('Subject', 'No Subject Yet'),
        ],
      );
    case 'review':
      return _workflowSnapshot(
        phase: 'review',
        phaseTitle: 'Review',
        scenario: scenario,
        status: 'Review opens after draft material exists',
        why:
            'There is nothing to review until a subject is created and drafted.',
        statusRows: <subject.KeyValueRow>[
          _statusRow('Mode', 'Placeholder workflow'),
          _statusRow('Phase', 'Review'),
          _statusRow('Subject', 'No Subject Yet'),
        ],
      );
    case 'publication':
      return _workflowSnapshot(
        phase: 'publication',
        phaseTitle: 'Publication',
        scenario: scenario,
        status: 'Publication remains optional',
        why:
            'Publication becomes available after review, but it is never required.',
        statusRows: <subject.KeyValueRow>[
          _statusRow('Mode', 'Placeholder workflow'),
          _statusRow('Phase', 'Publication'),
          _statusRow('Subject', 'No Subject Yet'),
        ],
      );
    default:
      return _workflowSnapshot(
        phase: 'research',
        phaseTitle: 'Gather',
        scenario: scenario,
        status: 'Create the first subject',
        why:
            'Import Markdown, stage a URL, or use chat-backed capture to open the first subject workflow.',
        actions: <subject.SubjectGateAction>[
          _gateAction('use_markdown_ingress', 'Import Markdown File'),
          _gateAction('use_url_ingress', 'Learn URL'),
          _gateAction('ask_follow_up', 'Ask Follow-up In Chat'),
        ],
        statusRows: <subject.KeyValueRow>[
          _statusRow('Mode', 'Placeholder workflow'),
          _statusRow('Phase', 'Gather'),
          _statusRow('Subject', 'No Subject Yet'),
        ],
      );
  }
}

subject.SubjectWorkflowSnapshotView _busyMarkdownSnapshot() {
  return _workflowSnapshot(
    phase: 'research',
    phaseTitle: 'Gather',
    scenario: _placeholderScenario(),
    status: 'Markdown ingress is running',
    why:
        'The staged markdown is being learned through the canonical subject-workflow action.',
    detailLines: <String>['- source: bus-notes.md'],
    statusRows: <subject.KeyValueRow>[
      _statusRow('Mode', 'Live subject workflow'),
      _statusRow('Phase', 'Gather'),
      _statusRow('Markdown Busy', 'true'),
    ],
  );
}

subject.SubjectWorkflowSnapshotView _importedMarkdownSnapshot(String tabKey) {
  final phase = _subjectPhaseForTestTab(tabKey);
  final scenario = _scenario(
    key: 'bus-network-notes',
    subjectId: 'bus-network-notes',
    title: 'Bus Network Notes',
    summary: 'Maintained subject imported from staged markdown.',
  );
  if (phase == 'review') {
    return _workflowSnapshot(
      phase: 'review',
      phaseTitle: 'Review',
      scenario: scenario,
      status: 'Inspect the imported subject',
      why:
          'Gather completed through canonical markdown ingress and routed into Review.',
      actions: <subject.SubjectGateAction>[
        _gateAction('preview_pending_import', 'Preview Pending Import'),
      ],
      statusRows: <subject.KeyValueRow>[
        _statusRow('Mode', 'Live subject workflow'),
        _statusRow('Phase', 'Review'),
        _statusRow('Subject', 'Bus Network Notes'),
      ],
    );
  }
  return _workflowSnapshot(
    phase: phase,
    phaseTitle: phase == 'research'
        ? 'Gather'
        : phase[0].toUpperCase() + phase.substring(1),
    scenario: scenario,
    status: 'Imported markdown into Bus Network Notes.',
    why: 'The canonical markdown ingress created a maintained subject.',
    statusRows: <subject.KeyValueRow>[
      _statusRow('Mode', 'Live subject workflow'),
      _statusRow('Phase', phase == 'research' ? 'Gather' : phase),
      _statusRow('Subject', 'Bus Network Notes'),
    ],
  );
}

subject.SubjectWorkflowSnapshotView _steadyStateGatherSnapshot() {
  final scenario = _scenario(
    key: 'transit-signals',
    subjectId: 'transit-signals',
    title: 'Transit Signals',
    summary: 'Singapore bus interchange redesign notes.',
  );
  final snapshot = _workflowSnapshot(
    phase: 'research',
    phaseTitle: 'Gather',
    scenario: scenario,
    status: 'Activate this subject',
    why: 'The subject is selected but not yet active for workflow steps.',
    detailLines: <String>[
      'The checks, report plan, and publication flow all work from the active subject workflow.',
    ],
    actions: <subject.SubjectGateAction>[
      _gateAction('activate_subject', 'Activate Subject'),
      _gateAction('add_last_assistant', 'Add Last Assistant'),
    ],
    statusRows: <subject.KeyValueRow>[
      _statusRow('Mode', 'Live subject workflow'),
      _statusRow('Phase', 'Gather'),
      _statusRow('Subject', 'Transit Signals'),
    ],
  );
  snapshot.paneBundle.panes
    ..clear()
    ..addAll(<subject.SubjectPaneView>[
      (subject.SubjectPaneView()
        ..key = 'research_sources'
        ..title = 'All Gather Sources [1 source, no saved query]'
        ..lines.addAll(<String>[
          'current set: All Gather Sources',
          'included sources: 1',
          'notes: The staged source set for this subject before corpus admission.',
        ])),
      (subject.SubjectPaneView()
        ..key = 'research_observation'
        ..title = 'Learned Snapshot'
        ..lines.addAll(<String>[
          'subject summary',
          'Transit Signals',
          'learned now',
          '- items: 1',
        ])),
    ]);
  return snapshot;
}

subject.SubjectWorkflowSnapshotView _itemizeParitySnapshot() {
  final scenario = _scenario(
    key: 'smart-city-travel',
    subjectId: 'smart-city-travel',
    title: 'Smart City Travel',
    summary: 'A city transit authority wants to modernize fare payment.',
  );
  final snapshot = _workflowSnapshot(
    phase: 'itemize',
    phaseTitle: 'Itemize',
    scenario: scenario,
    status: '',
    stepTitle: 'Orient the selected item',
    stepStatus: 'Current item: Smart City Travel [claim] status=candidate.',
    why:
        'Promote, reject, split, merge, and assign decision roles here before Draft composition and later Review.',
    detailLines: <String>[
      '- decision role: <none>',
      '- held for merge: 0',
      '- source refs: 2',
      '- suggested constructs: 0',
    ],
    statusRows: <subject.KeyValueRow>[
      _statusRow('Mode', 'Live subject workflow'),
      _statusRow('Phase', 'Itemize'),
      _statusRow('Subject', 'Smart City Travel'),
    ],
  );
  snapshot.paneBundle.panes
    ..clear()
    ..addAll(<subject.SubjectPaneView>[
      (subject.SubjectPaneView()
        ..key = 'itemize_inventory'
        ..title = 'Item Inventory'
        ..items.addAll(<subject.SubjectPaneItemView>[
          _paneItem(
            entryId: 'itemize-banks',
            entryKind: 'itemized_item',
            label: 'Banks and the payment processor',
            ordinal: 0,
            selected: true,
            status: 'candidate',
            semanticKind: 'claim',
            attributes: <subject.KeyValueRow>[
              _statusRow('decision_role', 'actor'),
            ],
          ),
          _paneItem(
            entryId: 'itemize-objective',
            entryKind: 'itemized_item',
            label:
                'changes that can be implemented without disrupting daily service',
            ordinal: 1,
            status: 'candidate',
            semanticKind: 'claim',
            attributes: <subject.KeyValueRow>[
              _statusRow('decision_role', 'objective'),
            ],
          ),
          _paneItem(
            entryId: 'itemize-regulator',
            entryKind: 'itemized_item',
            label: 'city regulator',
            ordinal: 2,
            status: 'candidate',
            semanticKind: 'claim',
            attributes: <subject.KeyValueRow>[
              _statusRow('decision_role', 'actor'),
            ],
          ),
        ])
        ..lines.addAll(<String>[
          'Itemized Inventory',
          '',
          '- session: itemization_demo',
          '- freshness: current',
          '- validation: ok',
          '- item count: 25',
          '',
          'Kinds',
          '- decision_role_candidate: 22',
          '- claim: 1',
          '- entity: 1',
          '- glossary_term: 1',
          '',
          'Items (25)',
          '> [c] actor - Banks and the payment processor',
          '  [c] objective - changes that can be implemented without disrupting daily service',
          '  [c] actor - city regulator',
        ])),
      (subject.SubjectPaneView()
        ..key = 'itemize_detail'
        ..title = 'Banks and the payment processor'
        ..lines.addAll(<String>[
          'Kind: decision_role_candidate',
          'Status: candidate',
          'Confidence: 0.78',
          'Decision role: actor',
          'Summary: Banks and the payment processor must be ready to support the new payment model.',
        ])),
    ]);
  return snapshot;
}

subject.SubjectWorkflowSnapshotView _draftParitySnapshot() {
  final scenario = _scenario(
    key: 'smart-city-travel',
    subjectId: 'smart-city-travel',
    title: 'Smart City Travel',
    summary: 'A city transit authority wants to modernize fare payment.',
  );
  final snapshot = _workflowSnapshot(
    phase: 'draft',
    phaseTitle: 'Draft',
    scenario: scenario,
    status: '',
    stepTitle: 'Accept this construct into decision analysis',
    stepStatus:
        'Current construct: Banks and the payment processor [actor] status=candidate.',
    why:
        'Use the draft inventory to promote accepted support into decision analysis.',
    statusRows: <subject.KeyValueRow>[
      _statusRow('Mode', 'Live subject workflow'),
      _statusRow('Phase', 'Draft'),
      _statusRow('Subject', 'Smart City Travel'),
    ],
  );
  snapshot.paneBundle.panes
    ..clear()
    ..addAll(<subject.SubjectPaneView>[
      (subject.SubjectPaneView()
        ..key = 'draft_scope_tree'
        ..title = 'Draft Item Inventory'
        ..items.addAll(<subject.SubjectPaneItemView>[
          _paneItem(
            entryId: 'draft-transit',
            entryKind: 'draft_review_item',
            label: 'Smart City Travel',
            ordinal: 0,
            selected: true,
            toggleable: true,
            checkState: 'checked',
            semanticKind: 'claim',
            renderKind: 'paragraph',
          ),
          _paneItem(
            entryId: 'draft-banks',
            entryKind: 'draft_review_item',
            label: 'Banks and the payment processor',
            ordinal: 1,
            toggleable: true,
            checkState: 'checked',
            semanticKind: 'claim',
            renderKind: 'citation_callout',
          ),
          _paneItem(
            entryId: 'draft-regulator',
            entryKind: 'draft_review_item',
            label: 'city regulator',
            ordinal: 2,
            toggleable: true,
            checkState: 'checked',
            semanticKind: 'claim',
            renderKind: 'citation_callout',
          ),
        ])
        ..lines.addAll(<String>[
          '> [x][ ] Smart City Travel',
          '  [x][ ] Banks and the payment processor',
          '  [x][ ] city regulator',
        ])),
      (subject.SubjectPaneView()
        ..key = 'draft_detail'
        ..title = 'Banks and the payment processor'
        ..lines.addAll(<String>[
          'label: Banks and the payment processor',
          'ordering: 3',
          'included in draft: yes',
          'semantic kind: Claim',
          'render kind: Citation Callout',
          'transform mode: Keep',
        ])),
    ]);
  return snapshot;
}

shell_spec.WorkstationLayoutSpec _testLayout() {
  final payload = File('assets/workstation_layout.json').readAsStringSync();
  return shell_spec.WorkstationLayoutSpec.fromJson(
    jsonDecode(payload) as Map<String, dynamic>,
  );
}

subject.SubjectWorkflowSnapshotView _workflowSnapshot({
  required String phase,
  required String phaseTitle,
  required subject.SubjectScenarioSummary scenario,
  required String status,
  required String why,
  String? stepTitle,
  String stepStatus = '',
  List<subject.SubjectGateAction> actions = const <subject.SubjectGateAction>[],
  List<String> detailLines = const <String>[],
  List<subject.KeyValueRow> statusRows = const <subject.KeyValueRow>[],
}) {
  final normalizedStatus = status.trim();
  final effectiveTitle =
      stepTitle ??
      (normalizedStatus.startsWith('Last Action:') ? '' : normalizedStatus);
  final effectiveStatus = stepTitle != null
      ? stepStatus
      : (effectiveTitle.isEmpty ? normalizedStatus : '');
  return subject.SubjectWorkflowSnapshotView()
    ..phaseView = (subject.SubjectPhaseView()
      ..phase = phase
      ..phaseTitle = phaseTitle
      ..preferredPhase = phase
      ..scenario = scenario
      ..currentStep = (subject.SubjectCurrentStepView()
        ..title = effectiveTitle
        ..status = effectiveStatus
        ..why = why
        ..detailLines.addAll(detailLines)
        ..actions.addAll(actions))
      ..statusView = (subject.SubjectStatusView()
        ..title = 'Subject Status'
        ..rows.addAll(statusRows))
      ..journeyLines.addAll(<String>[
        '1. Gather',
        '2. Itemize',
        '3. Draft',
        '4. Review',
        '5. Publication',
      ])
      ..workspaceView = (subject.TextSection()
        ..title = 'Workspace'
        ..lines.addAll(<String>[
          'Root: /tmp/workstation-root',
          'Phase: $phaseTitle',
        ])))
    ..controlBundle = (subject.SubjectControlBundleView()
      ..phase = phase
      ..moreActions.add(_actionSpec('refresh_subjects', 'Refresh Subjects')))
    ..paneBundle = (subject.SubjectPaneBundleView()
      ..phase = phase
      ..panes.add(
        subject.SubjectPaneView()
          ..key = 'learning'
          ..title = 'Learning'
          ..lines.addAll(<String>[scenario.title, scenario.summary]),
      ));
}

subject.SubjectScenarioSummary _scenario({
  required String key,
  required String subjectId,
  required String title,
  required String summary,
  bool isPlaceholder = false,
}) {
  return subject.SubjectScenarioSummary()
    ..key = key
    ..subjectId = subjectId
    ..title = title
    ..summary = summary
    ..governanceStatus = isPlaceholder ? 'draft' : 'ready'
    ..isPlaceholder = isPlaceholder;
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

String _normalizeTestTabKey(String tabKey) {
  switch (tabKey) {
    case 'learn':
    case 'learn_markdown':
      return 'research';
    default:
      return tabKey;
  }
}

String _subjectPhaseForTestTab(String tabKey) {
  switch (_normalizeTestTabKey(tabKey)) {
    case 'itemize':
      return 'itemize';
    case 'draft':
      return 'draft';
    case 'review':
      return 'review';
    case 'publication':
      return 'publication';
    default:
      return 'research';
  }
}

String _longPermissionsText() {
  return [
    'Granted session capabilities:',
    for (var index = 1; index <= 40; index++) '- ws.capability.$index',
    '',
    'Available capabilities:',
    for (var index = 1; index <= 55; index++) '- ws.available.$index',
  ].join('\n');
}

String _longActivityText() {
  return [
    'Activity feed:',
    for (var index = 1; index <= 40; index++) 'Activity feed entry $index',
  ].join('\n');
}

String _longSkillsText() {
  return [
    'Built-in skills:',
    for (var index = 1; index <= 12; index++)
      'Built-in skill ${index.toString().padLeft(3, '0')}',
    '',
    'Imported skills:',
    for (var index = 1; index <= 60; index++)
      'Imported skill ${index.toString().padLeft(3, '0')}',
  ].join('\n');
}
