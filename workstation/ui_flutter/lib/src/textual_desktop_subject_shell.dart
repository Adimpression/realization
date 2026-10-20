import 'dart:async';

import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'generated/workstation/grpc/definitions/subject_workflow.pb.dart'
    as subject;
import 'textual/layout.dart';

typedef SubjectActionCallback =
    Future<void> Function(String actionKey, {String? actionLabel});
typedef SubjectInteractionCallback =
    Future<void> Function(
      String interactionKey, {
      int delta,
      String? targetId,
      bool previewOnly,
    });

typedef _PaneShortcutHandler = Future<void> Function();

enum _PaneShortcut {
  moveUp,
  moveDown,
  activate,
  hold,
  toggle,
  release,
  decisionToggle,
  reorderEarlier,
  reorderLater,
  previewEarlier,
  previewLater,
}

enum _InteractivePaneRendererKind {
  itemizeInventory,
  draftScopeTree,
  reportScopeTree,
}

class _InteractivePaneSpec {
  const _InteractivePaneSpec({
    required this.paneKey,
    required this.rendererKind,
    required this.selectionInteractionKey,
    required this.companionPaneKey,
    required this.shortcuts,
  });

  final String paneKey;
  final _InteractivePaneRendererKind rendererKind;
  final String selectionInteractionKey;
  final String companionPaneKey;
  final Set<_PaneShortcut> shortcuts;
}

const Map<String, _InteractivePaneSpec> _interactivePaneSpecs = {
  'itemize_inventory': _InteractivePaneSpec(
    paneKey: 'itemize_inventory',
    rendererKind: _InteractivePaneRendererKind.itemizeInventory,
    selectionInteractionKey: 'move_itemize_cursor',
    companionPaneKey: 'itemize_detail',
    shortcuts: {
      _PaneShortcut.moveUp,
      _PaneShortcut.moveDown,
      _PaneShortcut.activate,
      _PaneShortcut.hold,
    },
  ),
  'draft_scope_tree': _InteractivePaneSpec(
    paneKey: 'draft_scope_tree',
    rendererKind: _InteractivePaneRendererKind.draftScopeTree,
    selectionInteractionKey: 'move_draft_review_cursor',
    companionPaneKey: 'draft_detail',
    shortcuts: {
      _PaneShortcut.moveUp,
      _PaneShortcut.moveDown,
      _PaneShortcut.decisionToggle,
      _PaneShortcut.reorderEarlier,
      _PaneShortcut.reorderLater,
    },
  ),
  'review_scope_tree': _InteractivePaneSpec(
    paneKey: 'review_scope_tree',
    rendererKind: _InteractivePaneRendererKind.reportScopeTree,
    selectionInteractionKey: 'move_report_scope_cursor',
    companionPaneKey: 'review_scope_detail',
    shortcuts: {
      _PaneShortcut.moveUp,
      _PaneShortcut.moveDown,
      _PaneShortcut.activate,
      _PaneShortcut.hold,
      _PaneShortcut.toggle,
      _PaneShortcut.release,
      _PaneShortcut.previewEarlier,
      _PaneShortcut.previewLater,
    },
  ),
  'publication_scope_tree': _InteractivePaneSpec(
    paneKey: 'publication_scope_tree',
    rendererKind: _InteractivePaneRendererKind.reportScopeTree,
    selectionInteractionKey: 'move_report_scope_cursor',
    companionPaneKey: 'publication_scope_detail',
    shortcuts: {
      _PaneShortcut.moveUp,
      _PaneShortcut.moveDown,
      _PaneShortcut.activate,
      _PaneShortcut.hold,
      _PaneShortcut.toggle,
      _PaneShortcut.release,
      _PaneShortcut.previewEarlier,
      _PaneShortcut.previewLater,
    },
  ),
};

const double _terminalHeightUnitPx = 24.0;

const _flutterDisabledSubjectActionKeys = <String>{
  'open_release_packet',
  'release_open_folder',
};

bool _isFlutterDisabledSubjectAction(String actionKey) {
  return _flutterDisabledSubjectActionKeys.contains(actionKey.trim());
}

enum _DetachedPaneMode { maximize, info }

class _DetachedPaneSpec {
  const _DetachedPaneSpec({required this.mode, required this.paneId});

  final _DetachedPaneMode mode;
  final String paneId;
}

class _PaneViewportBehavior {
  const _PaneViewportBehavior({
    required this.width,
    required this.heightMode,
    required this.heightUnits,
    required this.minHeightUnits,
    required this.scrollX,
    required this.scrollY,
    required this.wrap,
  });

  final String width;
  final String heightMode;
  final int? heightUnits;
  final int? minHeightUnits;
  final bool scrollX;
  final bool scrollY;
  final bool wrap;

  double get minHeightPx => (minHeightUnits ?? 0) * _terminalHeightUnitPx;
  double? get fixedHeightPx => heightMode == 'fixed' && heightUnits != null
      ? heightUnits! * _terminalHeightUnitPx
      : null;
  bool get fillHeight => heightMode == 'fill';

  factory _PaneViewportBehavior.fromSpec(WorkstationPaneSpec? spec) {
    return _PaneViewportBehavior(
      width: spec?.width ?? 'fill',
      heightMode: spec?.heightMode ?? 'content',
      heightUnits: spec?.heightUnits,
      minHeightUnits: spec?.minHeightUnits,
      scrollX: spec?.scrollX ?? false,
      scrollY: spec?.scrollY ?? false,
      wrap: spec?.wrap ?? true,
    );
  }
}

class _SubjectPaneLayoutHints {
  const _SubjectPaneLayoutHints({
    required this.actions,
    required this.progress,
    required this.learning,
  });

  final _PaneViewportBehavior actions;
  final _PaneViewportBehavior progress;
  final _PaneViewportBehavior learning;
}

class TextualDesktopSubjectShell extends StatefulWidget {
  const TextualDesktopSubjectShell({
    super.key,
    required this.layout,
    required this.tabs,
    required this.currentTabKey,
    required this.activeShellStateKey,
    required this.subjects,
    required this.selectedScenarioKey,
    required this.selectedScenarioLabel,
    required this.onSubjectSelected,
    required this.statusText,
    required this.onShellStateSelected,
    required this.onTabSelected,
    required this.snapshot,
    required this.subjectBusy,
    required this.onAction,
    required this.onInteraction,
  });

  final WorkstationLayoutSpec layout;
  final List<WorkstationTabSpec> tabs;
  final String currentTabKey;
  final String activeShellStateKey;
  final List<subject.SubjectScenarioSummary> subjects;
  final String selectedScenarioKey;
  final String selectedScenarioLabel;
  final ValueChanged<String> onSubjectSelected;
  final String statusText;
  final ValueChanged<String> onShellStateSelected;
  final ValueChanged<String> onTabSelected;
  final subject.SubjectWorkflowSnapshotView snapshot;
  final bool subjectBusy;
  final SubjectActionCallback onAction;
  final SubjectInteractionCallback onInteraction;

  @override
  State<TextualDesktopSubjectShell> createState() =>
      _TextualDesktopSubjectShellState();
}

class _TextualDesktopSubjectShellState
    extends State<TextualDesktopSubjectShell> {
  String? _activePaneId;
  _DetachedPaneSpec? _detachedPane;

  WorkstationLayoutSpec get layout => widget.layout;
  List<WorkstationTabSpec> get tabs => widget.tabs;
  String get currentTabKey => widget.currentTabKey;
  String get activeShellStateKey => widget.activeShellStateKey;
  List<subject.SubjectScenarioSummary> get subjects => widget.subjects;
  String get selectedScenarioKey => widget.selectedScenarioKey;
  String get selectedScenarioLabel => widget.selectedScenarioLabel;
  ValueChanged<String> get onSubjectSelected => widget.onSubjectSelected;
  String get statusText => widget.statusText;
  ValueChanged<String> get onShellStateSelected => widget.onShellStateSelected;
  ValueChanged<String> get onTabSelected => widget.onTabSelected;
  subject.SubjectWorkflowSnapshotView get snapshot => widget.snapshot;
  bool get subjectBusy => widget.subjectBusy;
  SubjectActionCallback get onAction => widget.onAction;
  SubjectInteractionCallback get onInteraction => widget.onInteraction;

  _SubjectPaneLayoutHints _layoutHintsForCurrentTab() {
    final tabSpec = layout.tabForKey(currentTabKey);
    return _SubjectPaneLayoutHints(
      actions: _PaneViewportBehavior.fromSpec(tabSpec.paneForKey('actions')),
      progress: _PaneViewportBehavior.fromSpec(tabSpec.paneForKey('progress')),
      learning: _PaneViewportBehavior.fromSpec(tabSpec.paneForKey('learning')),
    );
  }

  List<String> _visiblePaneIdsForState(
    WorkstationShellStateSpec shellState,
    Map<String, subject.SubjectPaneView> paneByKey,
  ) {
    final paneIds = <String>[];
    for (final section in shellState.sections) {
      final paneId = _paneKeyForSection(shellState.key, section.key);
      if (!paneByKey.containsKey(paneId)) {
        continue;
      }
      if (!paneIds.contains(paneId)) {
        paneIds.add(paneId);
      }
    }
    return paneIds;
  }

  String? _effectiveActivePaneId(List<String> visiblePaneIds) {
    if (_activePaneId != null && visiblePaneIds.contains(_activePaneId)) {
      return _activePaneId;
    }
    return visiblePaneIds.isEmpty ? null : visiblePaneIds.first;
  }

  _DetachedPaneSpec? _effectiveDetachedPane(List<String> visiblePaneIds) {
    final detachedPane = _detachedPane;
    if (detachedPane == null) {
      return null;
    }
    if (!visiblePaneIds.contains(detachedPane.paneId)) {
      return null;
    }
    return detachedPane;
  }

  void _activatePane(String paneId, VoidCallback requestFocus) {
    requestFocus();
    if (_activePaneId == paneId) {
      return;
    }
    setState(() {
      _activePaneId = paneId;
    });
  }

  void _toggleDetachedPane(_DetachedPaneMode mode, String? paneId) {
    if (paneId == null) {
      return;
    }
    setState(() {
      if (_detachedPane?.mode == mode && _detachedPane?.paneId == paneId) {
        _detachedPane = null;
        return;
      }
      _activePaneId = paneId;
      _detachedPane = _DetachedPaneSpec(mode: mode, paneId: paneId);
    });
  }

  void _dismissDetachedPane() {
    if (_detachedPane == null) {
      return;
    }
    setState(() {
      _detachedPane = null;
    });
  }

  Map<_PaneShortcut, _PaneShortcutHandler> _shortcutHandlersForShellState(
    WorkstationShellStateSpec shellState,
  ) {
    return switch (shellState.key) {
      'itemize.main' => _shortcutHandlersForPane(
        paneKey: 'itemize_inventory',
        activateActionKey: 'preview_selected_itemized_item',
        holdActionKey: 'hold_selected_itemized_item',
      ),
      'draft.compose' ||
      'draft.frame' ||
      'draft.model' ||
      'draft.explore' => _shortcutHandlersForPane(
        paneKey: 'draft_scope_tree',
        decisionActionKey:
            'toggle_selected_draft_review_item_in_decision_frame',
        reorderEarlierActionKey: 'move_selected_draft_review_item_earlier',
        reorderLaterActionKey: 'move_selected_draft_review_item_later',
      ),
      'review.main' || 'review.journal' => _shortcutHandlersForPane(
        paneKey: 'review_scope_tree',
        activateActionKey: 'preview_selected_report_scope_item',
        holdActionKey: 'hold_selected_report_scope_item',
        toggleActionKey: 'toggle_selected_report_scope_item',
        releaseActionKey: 'release_held_report_scope_items',
        previewInteractionKey: 'preview_move_held_report_scope_items',
      ),
      'publication.main' => _shortcutHandlersForPane(
        paneKey: 'publication_scope_tree',
        activateActionKey: 'preview_selected_report_scope_item',
        holdActionKey: 'hold_selected_report_scope_item',
        toggleActionKey: 'toggle_selected_report_scope_item',
        releaseActionKey: 'release_held_report_scope_items',
        previewInteractionKey: 'preview_move_held_report_scope_items',
      ),
      _ => const {},
    };
  }

  Widget _buildSelectControl(
    subject.SubjectSelectSpecView? spec, {
    double widthFactor = 1.0,
  }) {
    return _SelectControlBlock(
      spec: spec,
      widthFactor: widthFactor,
      interactionsEnabled: !subjectBusy,
      onAction: onAction,
    );
  }

  Widget _buildSwitchControl(subject.SubjectSwitchSpecView? spec) {
    return _SwitchControlBlock(
      spec: spec,
      interactionsEnabled: !subjectBusy,
      onAction: onAction,
    );
  }

  @override
  Widget build(BuildContext context) {
    final shellState = layout.shellStateForKey(activeShellStateKey);

    final phaseView = snapshot.phaseView;
    final controlBundle = snapshot.controlBundle;
    final paneByKey = {
      for (final pane in snapshot.paneBundle.panes) pane.key: pane,
    };
    final layoutHints = _layoutHintsForCurrentTab();
    final visiblePaneIds = _visiblePaneIdsForState(shellState, paneByKey);
    final activePaneId = _effectiveActivePaneId(visiblePaneIds);
    final detachedPane = _effectiveDetachedPane(visiblePaneIds);

    return Container(
      color: Colors.black,
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _TabStrip(
            tabs: tabs,
            currentTabKey: currentTabKey,
            subjects: subjects,
            selectedScenarioKey: selectedScenarioKey,
            selectedScenarioLabel: selectedScenarioLabel,
            subjectBusy: subjectBusy,
            onSubjectSelected: onSubjectSelected,
            onTabSelected: onTabSelected,
          ),
          const SizedBox(height: 18),
          Expanded(
            child: _WorkbenchKeyboardScope(
              enabled: !subjectBusy,
              handlers: _shortcutHandlersForShellState(shellState),
              onToggleInfo: () =>
                  _toggleDetachedPane(_DetachedPaneMode.info, activePaneId),
              onToggleMaximize: () =>
                  _toggleDetachedPane(_DetachedPaneMode.maximize, activePaneId),
              childBuilder: (requestFocus) => detachedPane != null
                  ? _buildDetachedPane(
                      shellState,
                      paneByKey,
                      detachedPane,
                      layoutHints,
                      activePaneId,
                      requestFocus,
                    )
                  : _buildShellState(
                      context,
                      shellState,
                      phaseView,
                      controlBundle,
                      paneByKey,
                      layoutHints,
                      activePaneId,
                      requestFocus,
                    ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildShellState(
    BuildContext context,
    WorkstationShellStateSpec shellState,
    subject.SubjectPhaseView phaseView,
    subject.SubjectControlBundleView controlBundle,
    Map<String, subject.SubjectPaneView> paneByKey,
    _SubjectPaneLayoutHints layoutHints,
    String? activePaneId,
    VoidCallback requestFocus,
  ) {
    switch (shellState.key) {
      case 'gather.main':
        return _buildGatherMain(
          phaseView,
          controlBundle,
          paneByKey,
          layoutHints,
          activePaneId,
          requestFocus,
        );
      case 'gather.journal':
      case 'review.journal':
        return _buildJournalState(
          shellState,
          paneByKey,
          layoutHints,
          activePaneId,
          requestFocus,
          shellState.key == 'gather.journal'
              ? 'research_observation'
              : 'review_scope_detail',
        );
      case 'gather.source_detail':
        return _buildSourceDetailState(
          shellState,
          paneByKey,
          layoutHints,
          activePaneId,
          requestFocus,
        );
      case 'itemize.main':
        return _buildItemizeMain(
          phaseView,
          controlBundle,
          paneByKey,
          layoutHints,
          activePaneId,
          requestFocus,
        );
      case 'draft.compose':
        return _buildDraftComposeState(
          phaseView,
          controlBundle,
          paneByKey,
          layoutHints,
          activePaneId,
          requestFocus,
        );
      case 'draft.frame':
      case 'draft.model':
      case 'draft.explore':
        return _buildDraftLensState(
          shellState,
          phaseView,
          controlBundle,
          paneByKey,
          layoutHints,
          activePaneId,
          requestFocus,
        );
      case 'review.main':
        return _buildReviewMain(
          phaseView,
          controlBundle,
          paneByKey,
          layoutHints,
          activePaneId,
          requestFocus,
        );
      case 'publication.main':
        return _buildPublicationMain(
          phaseView,
          controlBundle,
          paneByKey,
          layoutHints,
          activePaneId,
          requestFocus,
        );
      default:
        return _buildFallbackState(
          shellState,
          paneByKey,
          layoutHints,
          activePaneId,
          requestFocus,
        );
    }
  }

  Widget _buildDetachedPane(
    WorkstationShellStateSpec shellState,
    Map<String, subject.SubjectPaneView> paneByKey,
    _DetachedPaneSpec detachedPane,
    _SubjectPaneLayoutHints layoutHints,
    String? activePaneId,
    VoidCallback requestFocus,
  ) {
    final paneId = detachedPane.paneId;
    final baseTitle = _paneDisplayTitle(shellState, paneId, paneByKey);
    final child = detachedPane.mode == _DetachedPaneMode.info
        ? _TerminalLineListPane(
            lines: _paneHelpLines(shellState, paneId),
            dense: true,
            wrapText: true,
            preserveBlankLines: true,
          )
        : _PaneContent(
            pane: paneByKey[paneId],
            fallbackTitle: baseTitle,
            dense: true,
            wrapText: layoutHints.learning.wrap,
            interactionsEnabled: !subjectBusy,
            onFocusRequested: () => _activatePane(paneId, requestFocus),
            onSelectIndex: (targetIndex) => _selectPaneRow(
              paneByKey[paneId],
              targetIndex,
              titleHint: baseTitle,
            ),
            onToggleIndex: (targetIndex) => _togglePaneCheckbox(
              paneByKey[paneId],
              targetIndex,
              titleHint: baseTitle,
            ),
          );
    return _PaneFrame(
      paneId: paneId,
      active: activePaneId == paneId,
      onActivate: () => _activatePane(paneId, requestFocus),
      title: detachedPane.mode == _DetachedPaneMode.info
          ? 'Help · $baseTitle'
          : baseTitle,
      behavior: layoutHints.learning,
      trailing: _PaneChrome(
        infoActive: detachedPane.mode == _DetachedPaneMode.info,
        maximizeActive: detachedPane.mode == _DetachedPaneMode.maximize,
        onInfo: () => _toggleDetachedPane(_DetachedPaneMode.info, paneId),
        onMaximize: () =>
            _toggleDetachedPane(_DetachedPaneMode.maximize, paneId),
        onCollapse: _dismissDetachedPane,
      ),
      child: child,
    );
  }

  Widget _buildManagedPaneFrame({
    required WorkstationShellStateSpec shellState,
    required String paneId,
    required String title,
    required subject.SubjectPaneView? pane,
    required _PaneViewportBehavior behavior,
    required String? activePaneId,
    required VoidCallback requestFocus,
    Widget? trailing,
    bool dense = true,
    bool interactionsEnabled = false,
    String titleHint = '',
  }) {
    return _PaneFrame(
      paneId: paneId,
      active: activePaneId == paneId,
      onActivate: () => _activatePane(paneId, requestFocus),
      title: title,
      behavior: behavior,
      trailing:
          trailing ??
          _PaneChrome(
            infoActive:
                _detachedPane?.mode == _DetachedPaneMode.info &&
                _detachedPane?.paneId == paneId,
            maximizeActive:
                _detachedPane?.mode == _DetachedPaneMode.maximize &&
                _detachedPane?.paneId == paneId,
            onInfo: () => _toggleDetachedPane(_DetachedPaneMode.info, paneId),
            onMaximize: () =>
                _toggleDetachedPane(_DetachedPaneMode.maximize, paneId),
          ),
      child: _PaneContent(
        pane: pane,
        fallbackTitle: title,
        dense: dense,
        wrapText: behavior.wrap,
        interactionsEnabled: interactionsEnabled,
        onFocusRequested: () => _activatePane(paneId, requestFocus),
        onSelectIndex: interactionsEnabled
            ? (targetIndex) => _selectPaneRow(
                pane,
                targetIndex,
                titleHint: titleHint.isEmpty ? title : titleHint,
              )
            : null,
        onToggleIndex: interactionsEnabled
            ? (targetIndex) => _togglePaneCheckbox(
                pane,
                targetIndex,
                titleHint: titleHint.isEmpty ? title : titleHint,
              )
            : null,
      ),
    );
  }

  String _paneDisplayTitle(
    WorkstationShellStateSpec shellState,
    String paneId,
    Map<String, subject.SubjectPaneView> paneByKey,
  ) {
    final pane = paneByKey[paneId];
    final paneTitle = pane?.title.trim() ?? '';
    if (paneTitle.isNotEmpty) {
      return paneTitle;
    }
    return switch (paneId) {
      'research_sources' => 'Source Sets',
      'research_observation' =>
        shellState.key == 'gather.journal'
            ? 'Gather Journal'
            : 'Learned Snapshot',
      'research_target' => 'Source Detail',
      'itemize_inventory' => 'Item Inventory',
      'itemize_detail' => 'Item Detail',
      'draft_scope_tree' =>
        shellState.key == 'draft.compose'
            ? 'Draft Item Inventory'
            : 'Case Objects',
      'draft_model_main' => switch (shellState.key) {
        'draft.frame' => 'Case Frame',
        'draft.explore' => 'Explore Alternatives',
        _ => 'Transformation Model',
      },
      'draft_detail' => 'Draft Detail',
      'draft_result' => 'Issues & Validation',
      'review_scope_tree' || 'publication_scope_tree' => 'Report Scope',
      'review_scope_detail' =>
        shellState.key == 'review.journal'
            ? 'Review Journal'
            : 'Selection Details',
      'publication_scope_detail' => 'Selection Details',
      _ => paneId.replaceAll('_', ' ').trim(),
    };
  }

  List<String> _paneHelpLines(
    WorkstationShellStateSpec shellState,
    String paneId,
  ) {
    return switch (paneId) {
      'research_sources' => const <String>[
        'Source Sets',
        '',
        '- Shows the selected Gather source set and the staged-source inventory.',
        '- Use phase actions to change source-set context.',
        '- Click the pane body to focus it.',
      ],
      'research_observation' => const <String>[
        'Learned Snapshot',
        '',
        '- Shows the current learned snapshot for Gather.',
        '- Use the pane toggle to open the dedicated journal state.',
      ],
      'research_target' => const <String>[
        'Source Detail',
        '',
        '- Shows the currently selected staged source in Gather.',
        '- Collapse returns to the main Gather workbench.',
      ],
      'itemize_inventory' => const <String>[
        'Item Inventory',
        '',
        '- Up/Down moves the selected item without wrapping.',
        '- Enter previews the selected item.',
        '- H holds or unholds the selected item for merge.',
        '- Click a row to select it directly.',
      ],
      'itemize_detail' => const <String>[
        'Item Detail',
        '',
        '- Shows the currently selected item from Item Inventory.',
        '- Preview actions update this pane.',
      ],
      'draft_scope_tree' =>
        shellState.key == 'draft.compose'
            ? const <String>[
                'Draft Item Inventory',
                '',
                '- Up/Down moves the selected draft item without wrapping.',
                '- Shift+Up/Down reorders the selected draft item.',
                '- D toggles decision inclusion.',
                '- Click a row to select it directly.',
              ]
            : const <String>[
                'Case Objects',
                '',
                '- Up/Down moves the selected construct without wrapping.',
                '- Selection persists across Frame, Model, and Explore.',
                '- Click a row to select it directly.',
              ],
      'draft_model_main' => const <String>[
        'Lens View',
        '',
        '- Frame defines the case surface.',
        '- Model structures relations and bindings.',
        '- Explore shows alternatives, admissibility, and blockers.',
      ],
      'draft_detail' => const <String>[
        'Draft Detail',
        '',
        '- Shows the currently selected draft item or construct.',
        '- The active selection is shared across the draft workbench.',
      ],
      'draft_result' => const <String>[
        'Issues & Validation',
        '',
        '- Shows validation, issues, and draft-result journal lines.',
        '- This pane remains available across the draft lens states.',
      ],
      'review_scope_tree' => const <String>[
        'Report Scope',
        '',
        '- Up/Down moves the selected report-scope entry without wrapping.',
        '- Shift+Up/Down or K/J previews held-item movement.',
        '- H holds, X toggles, R releases, and Enter previews.',
        '- Click a selectable row to select it directly.',
      ],
      'review_scope_detail' =>
        shellState.key == 'review.journal'
            ? const <String>[
                'Review Journal',
                '',
                '- Shows the current review journal/log content.',
                '- Collapse returns to the main Review workbench.',
              ]
            : const <String>[
                'Selection Details',
                '',
                '- Shows the currently selected report-scope item in detail.',
              ],
      'publication_scope_tree' => const <String>[
        'Report Scope',
        '',
        '- Up/Down moves the selected report-scope entry without wrapping.',
        '- X toggles inclusion, Enter previews, and click selects directly.',
      ],
      'publication_scope_detail' => const <String>[
        'Selection Details',
        '',
        '- Shows the currently selected publication report-scope item.',
      ],
      _ => const <String>[
        'Pane Help',
        '',
        '- This pane has no additional interaction notes yet.',
      ],
    };
  }

  Widget _buildGatherMain(
    subject.SubjectPhaseView phaseView,
    subject.SubjectControlBundleView controlBundle,
    Map<String, subject.SubjectPaneView> paneByKey,
    _SubjectPaneLayoutHints layoutHints,
    String? activePaneId,
    VoidCallback requestFocus,
  ) {
    final gatherTopActions = _gatherTopActions(controlBundle);
    final sourceSet = _selectByKey(controlBundle, 'research_source_set');
    final revisionBaseline = _selectByKey(
      controlBundle,
      'research_revision_baseline',
    );
    final inSourceSet = _switchByKey(controlBundle, 'research_in_source_set');

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _GateStatusRow(
          currentStep: _CurrentStepBlock.fromPhaseView(
            phaseView,
            lastActionText: statusText,
          ),
          statusTitle: 'Subject Status',
          statusRows: phaseView.statusView.rows,
          onAction: onAction,
        ),
        if (gatherTopActions.isNotEmpty) ...[
          const SizedBox(height: 14),
          _ShellSectionBlock(
            minHeight: layoutHints.actions.minHeightPx,
            child: _MoreActionsBlock(
              actions: gatherTopActions,
              onAction: onAction,
            ),
          ),
        ],
        const SizedBox(height: 12),
        _ShellSectionBlock(
          minHeight: layoutHints.actions.minHeightPx,
          child: _ControlGrid(
            children: [
              _buildSelectControl(sourceSet, widthFactor: 1.5),
              _buildSelectControl(revisionBaseline, widthFactor: 1.5),
              _buildSwitchControl(inSourceSet),
            ],
          ),
        ),
        const SizedBox(height: 14),
        Expanded(
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Expanded(
                flex: 2,
                child: _buildManagedPaneFrame(
                  shellState: layout.shellStateForKey('gather.main'),
                  paneId: 'research_sources',
                  title: 'Source Sets',
                  pane: paneByKey['research_sources'],
                  behavior: layoutHints.learning,
                  activePaneId: activePaneId,
                  requestFocus: requestFocus,
                  trailing: _PaneChrome(
                    infoActive:
                        _detachedPane?.mode == _DetachedPaneMode.info &&
                        _detachedPane?.paneId == 'research_sources',
                    maximizeActive:
                        _detachedPane?.mode == _DetachedPaneMode.maximize &&
                        _detachedPane?.paneId == 'research_sources',
                    onInfo: () => _toggleDetachedPane(
                      _DetachedPaneMode.info,
                      'research_sources',
                    ),
                    onMaximize: () => _toggleDetachedPane(
                      _DetachedPaneMode.maximize,
                      'research_sources',
                    ),
                    onExpand: () =>
                        onShellStateSelected('gather.source_detail'),
                  ),
                ),
              ),
              const SizedBox(width: 18),
              Expanded(
                flex: 2,
                child: _buildManagedPaneFrame(
                  shellState: layout.shellStateForKey('gather.main'),
                  paneId: 'research_observation',
                  title: 'Learned Snapshot',
                  pane: paneByKey['research_observation'],
                  behavior: layoutHints.learning,
                  activePaneId: activePaneId,
                  requestFocus: requestFocus,
                  trailing: _PaneChrome(
                    infoActive:
                        _detachedPane?.mode == _DetachedPaneMode.info &&
                        _detachedPane?.paneId == 'research_observation',
                    maximizeActive:
                        _detachedPane?.mode == _DetachedPaneMode.maximize &&
                        _detachedPane?.paneId == 'research_observation',
                    onInfo: () => _toggleDetachedPane(
                      _DetachedPaneMode.info,
                      'research_observation',
                    ),
                    onMaximize: () => _toggleDetachedPane(
                      _DetachedPaneMode.maximize,
                      'research_observation',
                    ),
                    onExpand: () => onShellStateSelected('gather.journal'),
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildItemizeMain(
    subject.SubjectPhaseView phaseView,
    subject.SubjectControlBundleView controlBundle,
    Map<String, subject.SubjectPaneView> paneByKey,
    _SubjectPaneLayoutHints layoutHints,
    String? activePaneId,
    VoidCallback requestFocus,
  ) {
    final decisionRole = _selectByKey(controlBundle, 'itemize_decision_role');
    final holdForMerge = _switchByKey(controlBundle, 'itemize_hold');
    final inventoryPane = paneByKey['itemize_inventory'];
    final detailPane = paneByKey['itemize_detail'];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _GateStatusRow(
          currentStep: _CurrentStepBlock.fromPhaseView(
            phaseView,
            lastActionText: statusText,
          ),
          statusTitle: 'Itemize Status',
          statusRows: phaseView.statusView.rows,
          onAction: onAction,
        ),
        const SizedBox(height: 18),
        _ShellSectionBlock(
          minHeight: layoutHints.actions.minHeightPx,
          child: _BorderlessTerminalSection(
            title: 'More Actions',
            child: _ControlGrid(
              children: [
                _buildSelectControl(decisionRole, widthFactor: 1.6),
                _buildSwitchControl(holdForMerge),
              ],
            ),
          ),
        ),
        const SizedBox(height: 18),
        Expanded(
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Expanded(
                flex: 2,
                child: _buildManagedPaneFrame(
                  shellState: layout.shellStateForKey('itemize.main'),
                  paneId: 'itemize_inventory',
                  title: 'Item Inventory',
                  pane: inventoryPane,
                  behavior: layoutHints.learning,
                  activePaneId: activePaneId,
                  requestFocus: requestFocus,
                  interactionsEnabled: !subjectBusy,
                ),
              ),
              const SizedBox(width: 18),
              Expanded(
                flex: 2,
                child: _buildManagedPaneFrame(
                  shellState: layout.shellStateForKey('itemize.main'),
                  paneId: 'itemize_detail',
                  title: 'Item Detail',
                  pane: detailPane,
                  behavior: layoutHints.learning,
                  activePaneId: activePaneId,
                  requestFocus: requestFocus,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildDraftComposeState(
    subject.SubjectPhaseView phaseView,
    subject.SubjectControlBundleView controlBundle,
    Map<String, subject.SubjectPaneView> paneByKey,
    _SubjectPaneLayoutHints layoutHints,
    String? activePaneId,
    VoidCallback requestFocus,
  ) {
    final semanticKind = _selectByKey(controlBundle, 'draft_semantic_kind');
    final renderKind = _selectByKey(controlBundle, 'draft_render_kind');
    final evidenceMode = _selectByKey(controlBundle, 'draft_evidence_mode');
    final transformMode = _selectByKey(controlBundle, 'draft_transform_mode');
    final decisionIncluded = _switchByKey(
      controlBundle,
      'draft_decision_included',
    );
    final inventoryPane = paneByKey['draft_scope_tree'];
    final detailPane = paneByKey['draft_detail'];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _GateStatusRow(
          currentStep: _CurrentStepBlock.fromPhaseView(
            phaseView,
            lastActionText: statusText,
          ),
          statusTitle: 'Draft Status',
          statusRows: phaseView.statusView.rows,
          onAction: onAction,
        ),
        const SizedBox(height: 18),
        _ShellSectionBlock(
          minHeight: layoutHints.actions.minHeightPx,
          child: _BorderlessTerminalSection(
            title: 'More Actions',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const _TerminalSectionTitle('Selected Item'),
                const SizedBox(height: 8),
                _ControlGrid(
                  children: [
                    _buildSelectControl(semanticKind, widthFactor: 1.35),
                    _buildSelectControl(renderKind, widthFactor: 1.35),
                    _buildSelectControl(evidenceMode, widthFactor: 1.35),
                    _buildSelectControl(transformMode, widthFactor: 1.35),
                    _buildSwitchControl(decisionIncluded),
                  ],
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 18),
        Expanded(
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Expanded(
                flex: 2,
                child: _buildManagedPaneFrame(
                  shellState: layout.shellStateForKey('draft.compose'),
                  paneId: 'draft_scope_tree',
                  title: 'Draft Item Inventory',
                  pane: inventoryPane,
                  behavior: layoutHints.learning,
                  activePaneId: activePaneId,
                  requestFocus: requestFocus,
                  interactionsEnabled: !subjectBusy,
                  titleHint: 'Draft Item Inventory',
                ),
              ),
              const SizedBox(width: 18),
              Expanded(
                flex: 2,
                child: _buildManagedPaneFrame(
                  shellState: layout.shellStateForKey('draft.compose'),
                  paneId: 'draft_detail',
                  title: detailPane?.title.isNotEmpty == true
                      ? detailPane!.title
                      : 'Draft Detail',
                  pane: detailPane,
                  behavior: layoutHints.learning,
                  activePaneId: activePaneId,
                  requestFocus: requestFocus,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildDraftLensState(
    WorkstationShellStateSpec shellState,
    subject.SubjectPhaseView phaseView,
    subject.SubjectControlBundleView controlBundle,
    Map<String, subject.SubjectPaneView> paneByKey,
    _SubjectPaneLayoutHints layoutHints,
    String? activePaneId,
    VoidCallback requestFocus,
  ) {
    final selectedChange = _selectionListByKey(
      controlBundle,
      'draft_change_selection',
    );
    final changeType = _selectByKey(controlBundle, 'draft_change_type');
    final changeRole = _selectByKey(controlBundle, 'draft_change_role');
    final decisionPolicy = _selectByKey(controlBundle, 'draft_decision_policy');
    final lens = shellState.key.split('.').last;
    final inventoryPane = paneByKey['draft_scope_tree'];
    final modelPane = paneByKey['draft_model_main'];
    final detailPane = paneByKey['draft_detail'];
    final issuesPane = paneByKey['draft_result'];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _GateStatusRow(
          currentStep: _CurrentStepBlock.fromPhaseView(
            phaseView,
            lastActionText: statusText,
          ),
          statusTitle: 'Draft Status',
          statusRows: phaseView.statusView.rows,
          onAction: onAction,
        ),
        const SizedBox(height: 18),
        _ShellSectionBlock(
          minHeight: layoutHints.actions.minHeightPx,
          child: _BorderlessTerminalSection(
            title: 'More Actions',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const _TerminalSectionTitle('Selected Change'),
                const SizedBox(height: 8),
                _ControlGrid(
                  children: [
                    _SelectionListSummaryBlock(spec: selectedChange),
                    _buildSelectControl(changeType, widthFactor: 1.4),
                    _buildSelectControl(changeRole, widthFactor: 1.4),
                    _buildSelectControl(decisionPolicy, widthFactor: 1.4),
                  ],
                ),
                const SizedBox(height: 16),
                _TerminalSectionTitle('View'),
                const SizedBox(height: 8),
                _DraftLensStrip(
                  activeShellStateKey: shellState.key,
                  onShellStateSelected: onShellStateSelected,
                  onAction: onAction,
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 18),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Expanded(
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Expanded(
                      flex: 2,
                      child: _buildManagedPaneFrame(
                        shellState: shellState,
                        paneId: 'draft_scope_tree',
                        title: 'Case Objects',
                        pane: inventoryPane,
                        behavior: layoutHints.learning,
                        activePaneId: activePaneId,
                        requestFocus: requestFocus,
                        interactionsEnabled: !subjectBusy,
                        titleHint: 'Case Objects',
                      ),
                    ),
                    const SizedBox(width: 18),
                    Expanded(
                      flex: 2,
                      child: _buildManagedPaneFrame(
                        shellState: shellState,
                        paneId: 'draft_model_main',
                        title: _draftMainPaneTitle(lens),
                        pane: modelPane,
                        behavior: layoutHints.learning,
                        activePaneId: activePaneId,
                        requestFocus: requestFocus,
                      ),
                    ),
                    const SizedBox(width: 18),
                    Expanded(
                      flex: 2,
                      child: _buildManagedPaneFrame(
                        shellState: shellState,
                        paneId: 'draft_detail',
                        title: detailPane?.title.isNotEmpty == true
                            ? detailPane!.title
                            : 'Draft Detail',
                        pane: detailPane,
                        behavior: layoutHints.learning,
                        activePaneId: activePaneId,
                        requestFocus: requestFocus,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 18),
              Flexible(
                fit: FlexFit.loose,
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxHeight: 216),
                  child: _buildManagedPaneFrame(
                    shellState: shellState,
                    paneId: 'draft_result',
                    title: 'Issues & Validation',
                    pane: issuesPane,
                    behavior: layoutHints.learning,
                    activePaneId: activePaneId,
                    requestFocus: requestFocus,
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildReviewMain(
    subject.SubjectPhaseView phaseView,
    subject.SubjectControlBundleView controlBundle,
    Map<String, subject.SubjectPaneView> paneByKey,
    _SubjectPaneLayoutHints layoutHints,
    String? activePaneId,
    VoidCallback requestFocus,
  ) {
    final outputStyle = _selectByKey(controlBundle, 'review_output_style');
    final reportStructure = _selectByKey(
      controlBundle,
      'review_report_structure',
    );
    final diffBaseline = _selectByKey(controlBundle, 'review_diff_baseline');
    final selectedItem = _selectByKey(controlBundle, 'review_selected_item');
    final itemInReport = _switchByKey(controlBundle, 'review_item_in_report');
    final selectedSection = _selectByKey(
      controlBundle,
      'review_selected_section',
    );
    final sectionInReport = _switchByKey(
      controlBundle,
      'review_section_in_report',
    );
    final reviewMoreActions = controlBundle.moreActions.where((action) {
      final key = action.key;
      return key.contains('review') || key.contains('report_plan');
    }).toList();
    final hasReportPlanControls =
        outputStyle != null || reportStructure != null || diffBaseline != null;
    final hasSelectedItemControls =
        selectedItem != null || itemInReport != null;
    final hasSelectedSectionControls =
        selectedSection != null || sectionInReport != null;
    final scopePane = paneByKey['review_scope_tree'];
    final detailPane = paneByKey['review_scope_detail'];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _GateStatusRow(
          currentStep: _CurrentStepBlock.fromPhaseView(
            phaseView,
            lastActionText: statusText,
          ),
          statusTitle: 'Review Status',
          statusRows: phaseView.statusView.rows,
          onAction: onAction,
        ),
        const SizedBox(height: 14),
        _ShellSectionBlock(
          minHeight: layoutHints.actions.minHeightPx,
          child: _BorderlessTerminalSection(
            title: 'More Actions',
            trailing: _ActionButton(
              label: 'Journal',
              enabled: true,
              onPressed: () => onShellStateSelected('review.journal'),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                if (reviewMoreActions.isNotEmpty) ...[
                  _ActionRow(actions: reviewMoreActions, onAction: onAction),
                ],
                if (hasReportPlanControls) ...[
                  if (reviewMoreActions.isNotEmpty) const SizedBox(height: 14),
                  const _TerminalSectionTitle('Report Plan'),
                  const SizedBox(height: 6),
                  _ControlGrid(
                    children: [
                      _buildSelectControl(outputStyle, widthFactor: 1.4),
                      _buildSelectControl(reportStructure, widthFactor: 1.4),
                      _buildSelectControl(diffBaseline, widthFactor: 1.4),
                    ],
                  ),
                ],
                if (hasSelectedItemControls || hasSelectedSectionControls) ...[
                  if (reviewMoreActions.isNotEmpty || hasReportPlanControls)
                    const SizedBox(height: 14),
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      if (hasSelectedItemControls)
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const _TerminalSectionTitle('Selected Item'),
                              const SizedBox(height: 6),
                              _ControlGrid(
                                children: [
                                  _buildSelectControl(
                                    selectedItem,
                                    widthFactor: 1.5,
                                  ),
                                  _buildSwitchControl(itemInReport),
                                ],
                              ),
                            ],
                          ),
                        ),
                      if (hasSelectedItemControls && hasSelectedSectionControls)
                        const SizedBox(width: 18),
                      if (hasSelectedSectionControls)
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const _TerminalSectionTitle('Selected Section'),
                              const SizedBox(height: 6),
                              _ControlGrid(
                                children: [
                                  _buildSelectControl(
                                    selectedSection,
                                    widthFactor: 1.5,
                                  ),
                                  _buildSwitchControl(sectionInReport),
                                ],
                              ),
                            ],
                          ),
                        ),
                    ],
                  ),
                ],
              ],
            ),
          ),
        ),
        const SizedBox(height: 14),
        Expanded(
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Expanded(
                flex: 2,
                child: _buildManagedPaneFrame(
                  shellState: layout.shellStateForKey('review.main'),
                  paneId: 'review_scope_tree',
                  title: 'Report Scope',
                  pane: scopePane,
                  behavior: layoutHints.learning,
                  activePaneId: activePaneId,
                  requestFocus: requestFocus,
                  interactionsEnabled: !subjectBusy,
                ),
              ),
              const SizedBox(width: 18),
              Expanded(
                flex: 2,
                child: _buildManagedPaneFrame(
                  shellState: layout.shellStateForKey('review.main'),
                  paneId: 'review_scope_detail',
                  title: 'Selection Details',
                  pane: detailPane,
                  behavior: layoutHints.learning,
                  activePaneId: activePaneId,
                  requestFocus: requestFocus,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildPublicationMain(
    subject.SubjectPhaseView phaseView,
    subject.SubjectControlBundleView controlBundle,
    Map<String, subject.SubjectPaneView> paneByKey,
    _SubjectPaneLayoutHints layoutHints,
    String? activePaneId,
    VoidCallback requestFocus,
  ) {
    final outputStyle = _selectByKey(controlBundle, 'publication_output_style');
    final reportStructure = _selectByKey(
      controlBundle,
      'publication_report_structure',
    );
    final diffBaseline = _selectByKey(
      controlBundle,
      'publication_diff_baseline',
    );
    final importTarget =
        _selectByKey(controlBundle, 'publication_import_target') ??
        _selectByKey(controlBundle, 'publication_selected_support');
    final importIncluded =
        _switchByKey(controlBundle, 'publication_import_included') ??
        _switchByKey(controlBundle, 'publication_support_in_report');
    final importUsage =
        _selectByKey(controlBundle, 'publication_import_usage') ??
        _selectByKey(controlBundle, 'publication_support_use');
    final selectedItem = _selectByKey(
      controlBundle,
      'publication_selected_item',
    );
    final itemInReport = _switchByKey(
      controlBundle,
      'publication_item_in_report',
    );
    final selectedSection = _selectByKey(
      controlBundle,
      'publication_selected_section',
    );
    final sectionInReport = _switchByKey(
      controlBundle,
      'publication_section_in_report',
    );
    final publicationMoreActions = controlBundle.moreActions.where((action) {
      final key = action.key;
      return key.contains('publication') ||
          key.contains('release') ||
          key == 'build_report';
    }).toList();
    final hasReportPlanControls =
        outputStyle != null || reportStructure != null || diffBaseline != null;
    final hasImportControls =
        importTarget != null || importIncluded != null || importUsage != null;
    final hasSelectedItemControls =
        selectedItem != null || itemInReport != null;
    final hasSelectedSectionControls =
        selectedSection != null || sectionInReport != null;
    final scopePane = paneByKey['publication_scope_tree'];
    final detailPane = paneByKey['publication_scope_detail'];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _GateStatusRow(
          currentStep: _CurrentStepBlock.fromPhaseView(
            phaseView,
            lastActionText: statusText,
          ),
          statusTitle: 'Publication Status',
          statusRows: phaseView.statusView.rows,
          onAction: onAction,
        ),
        const SizedBox(height: 14),
        _ShellSectionBlock(
          minHeight: layoutHints.actions.minHeightPx,
          child: _BorderlessTerminalSection(
            title: 'More Actions',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                if (publicationMoreActions.isNotEmpty) ...[
                  _ActionRow(
                    actions: publicationMoreActions,
                    onAction: onAction,
                  ),
                ],
                if (hasReportPlanControls) ...[
                  if (publicationMoreActions.isNotEmpty)
                    const SizedBox(height: 14),
                  const _TerminalSectionTitle('Report Plan'),
                  const SizedBox(height: 6),
                  _ControlGrid(
                    children: [
                      _buildSelectControl(outputStyle, widthFactor: 1.4),
                      _buildSelectControl(reportStructure, widthFactor: 1.4),
                      _buildSelectControl(diffBaseline, widthFactor: 1.4),
                    ],
                  ),
                ],
                if (hasImportControls) ...[
                  if (publicationMoreActions.isNotEmpty ||
                      hasReportPlanControls)
                    const SizedBox(height: 14),
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const _TerminalSectionTitle('Selected Support'),
                            const SizedBox(height: 6),
                            _ControlGrid(
                              children: [
                                _buildSelectControl(
                                  importTarget,
                                  widthFactor: 1.4,
                                ),
                                _buildSwitchControl(importIncluded),
                                _buildSelectControl(
                                  importUsage,
                                  widthFactor: 1.4,
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ],
                if (hasSelectedItemControls || hasSelectedSectionControls) ...[
                  if (publicationMoreActions.isNotEmpty ||
                      hasReportPlanControls ||
                      hasImportControls)
                    const SizedBox(height: 14),
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      if (hasSelectedItemControls)
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const _TerminalSectionTitle('Selected Item'),
                              const SizedBox(height: 6),
                              _ControlGrid(
                                children: [
                                  _buildSelectControl(
                                    selectedItem,
                                    widthFactor: 1.5,
                                  ),
                                  _buildSwitchControl(itemInReport),
                                ],
                              ),
                            ],
                          ),
                        ),
                      if (hasSelectedItemControls && hasSelectedSectionControls)
                        const SizedBox(width: 18),
                      if (hasSelectedSectionControls)
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const _TerminalSectionTitle('Selected Section'),
                              const SizedBox(height: 6),
                              _ControlGrid(
                                children: [
                                  _buildSelectControl(
                                    selectedSection,
                                    widthFactor: 1.5,
                                  ),
                                  _buildSwitchControl(sectionInReport),
                                ],
                              ),
                            ],
                          ),
                        ),
                    ],
                  ),
                ],
              ],
            ),
          ),
        ),
        const SizedBox(height: 14),
        Expanded(
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Expanded(
                flex: 2,
                child: _buildManagedPaneFrame(
                  shellState: layout.shellStateForKey('publication.main'),
                  paneId: 'publication_scope_tree',
                  title: 'Report Scope',
                  pane: scopePane,
                  behavior: layoutHints.learning,
                  activePaneId: activePaneId,
                  requestFocus: requestFocus,
                  interactionsEnabled: !subjectBusy,
                ),
              ),
              const SizedBox(width: 18),
              Expanded(
                flex: 2,
                child: _buildManagedPaneFrame(
                  shellState: layout.shellStateForKey('publication.main'),
                  paneId: 'publication_scope_detail',
                  title: 'Selection Details',
                  pane: detailPane,
                  behavior: layoutHints.learning,
                  activePaneId: activePaneId,
                  requestFocus: requestFocus,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildJournalState(
    WorkstationShellStateSpec shellState,
    Map<String, subject.SubjectPaneView> paneByKey,
    _SubjectPaneLayoutHints layoutHints,
    String? activePaneId,
    VoidCallback requestFocus,
    String paneKey,
  ) {
    final pane = paneByKey[paneKey];
    final title = shellState.key.startsWith('review')
        ? 'Review Journal'
        : 'Gather Journal';
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Expanded(
          child: _buildManagedPaneFrame(
            shellState: shellState,
            paneId: paneKey,
            title: title,
            pane: pane,
            behavior: layoutHints.learning,
            activePaneId: activePaneId,
            requestFocus: requestFocus,
            trailing: _PaneChrome(
              infoActive:
                  _detachedPane?.mode == _DetachedPaneMode.info &&
                  _detachedPane?.paneId == paneKey,
              maximizeActive:
                  _detachedPane?.mode == _DetachedPaneMode.maximize &&
                  _detachedPane?.paneId == paneKey,
              onInfo: () =>
                  _toggleDetachedPane(_DetachedPaneMode.info, paneKey),
              onMaximize: () =>
                  _toggleDetachedPane(_DetachedPaneMode.maximize, paneKey),
              onCollapse: () =>
                  onShellStateSelected(_mainShellStateKeyFor(shellState.key)),
            ),
          ),
        ),
        if (shellState.key == 'review.journal') ...[
          const SizedBox(height: 18),
          ConstrainedBox(
            constraints: BoxConstraints(
              minHeight: layoutHints.progress.minHeightPx,
            ),
            child: _TerminalFrame(
              title: 'Review Status',
              child: _StatusRows(rows: snapshot.phaseView.statusView.rows),
            ),
          ),
        ],
      ],
    );
  }

  Widget _buildSourceDetailState(
    WorkstationShellStateSpec shellState,
    Map<String, subject.SubjectPaneView> paneByKey,
    _SubjectPaneLayoutHints layoutHints,
    String? activePaneId,
    VoidCallback requestFocus,
  ) {
    final pane = paneByKey['research_target'];
    return _buildManagedPaneFrame(
      shellState: shellState,
      paneId: 'research_target',
      title: 'Source Detail',
      pane: pane,
      behavior: layoutHints.learning,
      activePaneId: activePaneId,
      requestFocus: requestFocus,
      trailing: _PaneChrome(
        infoActive:
            _detachedPane?.mode == _DetachedPaneMode.info &&
            _detachedPane?.paneId == 'research_target',
        maximizeActive:
            _detachedPane?.mode == _DetachedPaneMode.maximize &&
            _detachedPane?.paneId == 'research_target',
        onInfo: () =>
            _toggleDetachedPane(_DetachedPaneMode.info, 'research_target'),
        onMaximize: () =>
            _toggleDetachedPane(_DetachedPaneMode.maximize, 'research_target'),
        onCollapse: () => onShellStateSelected('gather.main'),
      ),
    );
  }

  Widget _buildFallbackState(
    WorkstationShellStateSpec shellState,
    Map<String, subject.SubjectPaneView> paneByKey,
    _SubjectPaneLayoutHints layoutHints,
    String? activePaneId,
    VoidCallback requestFocus,
  ) {
    final paneFrames = <Widget>[];
    for (final section in shellState.sections) {
      final paneId = _paneKeyForSection(shellState.key, section.key);
      if (!paneByKey.containsKey(paneId)) {
        continue;
      }
      paneFrames.add(
        Expanded(
          child: _buildManagedPaneFrame(
            shellState: shellState,
            paneId: paneId,
            title: section.title,
            pane: paneByKey[paneId],
            behavior: layoutHints.learning,
            activePaneId: activePaneId,
            requestFocus: requestFocus,
          ),
        ),
      );
      paneFrames.add(const SizedBox(height: 16));
    }
    if (paneFrames.isNotEmpty) {
      paneFrames.removeLast();
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: paneFrames,
    );
  }

  static String _paneKeyForSection(String shellStateKey, String sectionKey) {
    final tab = shellStateKey.split('.').first;
    return switch ('$tab.$sectionKey') {
      'gather.source_sets' => 'research_sources',
      'gather.learned_snapshot' => 'research_observation',
      'gather.source_detail' => 'research_target',
      'itemize.item_inventory' => 'itemize_inventory',
      'itemize.item_detail' => 'itemize_detail',
      'draft.draft_inventory' => 'draft_scope_tree',
      'draft.case_objects' => 'draft_scope_tree',
      'draft.case_frame' => 'draft_model_main',
      'draft.transformation_model' => 'draft_model_main',
      'draft.explore_alternatives' => 'draft_model_main',
      'draft.draft_detail' => 'draft_detail',
      'draft.issues_validation' => 'draft_result',
      'review.report_scope' => 'review_scope_tree',
      'review.selection_details' => 'review_scope_detail',
      'publication.report_scope' => 'publication_scope_tree',
      'publication.selection_details' => 'publication_scope_detail',
      _ => sectionKey,
    };
  }

  Map<_PaneShortcut, _PaneShortcutHandler> _shortcutHandlersForPane({
    required String paneKey,
    String? activateActionKey,
    String? holdActionKey,
    String? toggleActionKey,
    String? releaseActionKey,
    String? decisionActionKey,
    String? reorderEarlierActionKey,
    String? reorderLaterActionKey,
    String? previewInteractionKey,
  }) {
    final spec = _interactivePaneSpecs[paneKey];
    if (spec == null) {
      return const {};
    }
    final handlers = <_PaneShortcut, _PaneShortcutHandler>{};
    if (spec.shortcuts.contains(_PaneShortcut.moveUp)) {
      handlers[_PaneShortcut.moveUp] = () =>
          onInteraction(spec.selectionInteractionKey, delta: -1);
    }
    if (spec.shortcuts.contains(_PaneShortcut.moveDown)) {
      handlers[_PaneShortcut.moveDown] = () =>
          onInteraction(spec.selectionInteractionKey, delta: 1);
    }
    if (activateActionKey != null &&
        spec.shortcuts.contains(_PaneShortcut.activate)) {
      handlers[_PaneShortcut.activate] = () => onAction(activateActionKey);
    }
    if (holdActionKey != null && spec.shortcuts.contains(_PaneShortcut.hold)) {
      handlers[_PaneShortcut.hold] = () => onAction(holdActionKey);
    }
    if (toggleActionKey != null &&
        spec.shortcuts.contains(_PaneShortcut.toggle)) {
      handlers[_PaneShortcut.toggle] = () => onAction(toggleActionKey);
    }
    if (releaseActionKey != null &&
        spec.shortcuts.contains(_PaneShortcut.release)) {
      handlers[_PaneShortcut.release] = () => onAction(releaseActionKey);
    }
    if (decisionActionKey != null &&
        spec.shortcuts.contains(_PaneShortcut.decisionToggle)) {
      handlers[_PaneShortcut.decisionToggle] = () =>
          onAction(decisionActionKey);
    }
    if (reorderEarlierActionKey != null &&
        spec.shortcuts.contains(_PaneShortcut.reorderEarlier)) {
      handlers[_PaneShortcut.reorderEarlier] = () =>
          onAction(reorderEarlierActionKey);
    }
    if (reorderLaterActionKey != null &&
        spec.shortcuts.contains(_PaneShortcut.reorderLater)) {
      handlers[_PaneShortcut.reorderLater] = () =>
          onAction(reorderLaterActionKey);
    }
    if (previewInteractionKey != null &&
        spec.shortcuts.contains(_PaneShortcut.previewEarlier)) {
      handlers[_PaneShortcut.previewEarlier] = () =>
          onInteraction(previewInteractionKey, delta: -1);
    }
    if (previewInteractionKey != null &&
        spec.shortcuts.contains(_PaneShortcut.previewLater)) {
      handlers[_PaneShortcut.previewLater] = () =>
          onInteraction(previewInteractionKey, delta: 1);
    }
    return handlers;
  }

  Future<void> _selectPaneRow(
    subject.SubjectPaneView? pane,
    int targetIndex, {
    String titleHint = '',
  }) async {
    final effectivePane = pane;
    if (effectivePane == null || targetIndex < 0) {
      return;
    }
    final spec = _interactivePaneSpecs[effectivePane.key];
    if (spec == null) {
      return;
    }
    final currentIndex = _selectedInteractiveRowIndex(
      effectivePane,
      titleHint: titleHint,
    );
    if (currentIndex == targetIndex) {
      return;
    }
    final baseIndex = currentIndex >= 0 ? currentIndex : 0;
    await onInteraction(
      spec.selectionInteractionKey,
      delta: targetIndex - baseIndex,
    );
  }

  String? _checkboxToggleActionKeyForPane(subject.SubjectPaneView pane) {
    final spec = _interactivePaneSpecs[pane.key];
    if (spec == null) {
      return null;
    }
    return switch (spec.rendererKind) {
      _InteractivePaneRendererKind.draftScopeTree =>
        'toggle_selected_draft_review_item_in_decision_frame',
      _InteractivePaneRendererKind.reportScopeTree =>
        'toggle_selected_report_scope_item',
      _InteractivePaneRendererKind.itemizeInventory => null,
    };
  }

  Future<void> _togglePaneCheckbox(
    subject.SubjectPaneView? pane,
    int targetIndex, {
    String titleHint = '',
  }) async {
    final effectivePane = pane;
    if (effectivePane == null || targetIndex < 0) {
      return;
    }
    final actionKey = _checkboxToggleActionKeyForPane(effectivePane);
    if (actionKey == null) {
      return;
    }
    await _selectPaneRow(effectivePane, targetIndex, titleHint: titleHint);
    await onAction(actionKey);
  }

  int _selectedInteractiveRowIndex(
    subject.SubjectPaneView pane, {
    String titleHint = '',
  }) {
    final spec = _interactivePaneSpecs[pane.key];
    if (spec == null) {
      return -1;
    }
    switch (spec.rendererKind) {
      case _InteractivePaneRendererKind.itemizeInventory:
        final parsed = _ItemizeInventoryData.fromPane(pane);
        return parsed.rows.indexWhere((row) => row.selected);
      case _InteractivePaneRendererKind.draftScopeTree:
        final parsed = _DraftScopeTableData.fromPane(
          pane,
          titleHint: titleHint.isEmpty ? pane.title : titleHint,
        );
        return parsed.rows.indexWhere((row) => row.selected);
      case _InteractivePaneRendererKind.reportScopeTree:
        final parsed = _ReportScopeTreeData.fromPane(pane);
        for (final row in parsed.rows) {
          if (row.selectable && row.selected) {
            return row.interactionIndex ?? -1;
          }
        }
        return -1;
    }
  }

  static subject.SubjectSelectSpecView? _selectByKey(
    subject.SubjectControlBundleView bundle,
    String key,
  ) {
    for (final select in bundle.selects) {
      if (select.key == key) {
        return select;
      }
    }
    return null;
  }

  static subject.SubjectSwitchSpecView? _switchByKey(
    subject.SubjectControlBundleView bundle,
    String key,
  ) {
    for (final control in bundle.switches) {
      if (control.key == key) {
        return control;
      }
    }
    return null;
  }

  static subject.SubjectSelectionListSpecView? _selectionListByKey(
    subject.SubjectControlBundleView bundle,
    String key,
  ) {
    for (final control in bundle.selectionLists) {
      if (control.key == key) {
        return control;
      }
    }
    return null;
  }

  static List<subject.SubjectActionSpec> _gatherTopActions(
    subject.SubjectControlBundleView bundle,
  ) {
    return bundle.moreActions.where((action) {
      final key = action.key;
      return key.contains('refresh_subjects') ||
          key.contains('import_markdown_file') ||
          key.contains('follow_up') ||
          key.contains('learn_markdown') ||
          key.contains('learn_url') ||
          key.contains('export') ||
          key.contains('view_subject_assets') ||
          key.contains('journal');
    }).toList();
  }

  static String _draftMainPaneTitle(String lens) {
    return switch (lens) {
      'frame' => 'Case Frame',
      'model' => 'Transformation Model',
      'explore' => 'Explore Alternatives',
      _ => 'Draft Detail',
    };
  }

  static String _mainShellStateKeyFor(String shellStateKey) {
    return switch (shellStateKey) {
      'gather.journal' || 'gather.source_detail' => 'gather.main',
      'review.journal' => 'review.main',
      _ => shellStateKey,
    };
  }
}

class _TabStrip extends StatelessWidget {
  const _TabStrip({
    required this.tabs,
    required this.currentTabKey,
    required this.subjects,
    required this.selectedScenarioKey,
    required this.selectedScenarioLabel,
    required this.subjectBusy,
    required this.onSubjectSelected,
    required this.onTabSelected,
  });

  final List<WorkstationTabSpec> tabs;
  final String currentTabKey;
  final List<subject.SubjectScenarioSummary> subjects;
  final String selectedScenarioKey;
  final String selectedScenarioLabel;
  final bool subjectBusy;
  final ValueChanged<String> onSubjectSelected;
  final ValueChanged<String> onTabSelected;

  @override
  Widget build(BuildContext context) {
    const selectorMinWidth = 220.0;
    const selectorMaxWidth = 320.0;
    return Container(
      decoration: BoxDecoration(border: Border.all(color: _terminalBorder)),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final selectorWidth = constraints.maxWidth >= 1480
              ? selectorMaxWidth
              : constraints.maxWidth >= 1240
              ? 292.0
              : 248.0;
          return Row(
            children: [
              Expanded(
                child: SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: [
                      for (var index = 0; index < tabs.length; index++) ...[
                        _TabChip(
                          key: ValueKey<String>(
                            'desktop-tab:${tabs[index].key}',
                          ),
                          label: '${index + 1}. ${tabs[index].title}',
                          selected: tabs[index].key == currentTabKey,
                          onTap: () => onTabSelected(tabs[index].key),
                        ),
                        if (index != tabs.length - 1) const SizedBox(width: 12),
                      ],
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 14),
              ConstrainedBox(
                constraints: const BoxConstraints(
                  minWidth: selectorMinWidth,
                  maxWidth: selectorMaxWidth,
                ),
                child: SizedBox(
                  width: selectorWidth,
                  child: _SubjectSelector(
                    subjects: subjects,
                    selectedScenarioKey: selectedScenarioKey,
                    selectedScenarioLabel: selectedScenarioLabel,
                    enabled: !subjectBusy && subjects.isNotEmpty,
                    onChanged: onSubjectSelected,
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _SubjectSelector extends StatelessWidget {
  const _SubjectSelector({
    required this.subjects,
    required this.selectedScenarioKey,
    required this.selectedScenarioLabel,
    required this.enabled,
    required this.onChanged,
  });

  final List<subject.SubjectScenarioSummary> subjects;
  final String selectedScenarioKey;
  final String selectedScenarioLabel;
  final bool enabled;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) {
    final hasSelectedSubject = subjects.any(
      (subjectScenario) =>
          _subjectScenarioIdentity(subjectScenario) == selectedScenarioKey,
    );
    final selectedValue = hasSelectedSubject ? selectedScenarioKey : null;
    final hintText = selectedScenarioLabel.trim().isEmpty
        ? 'No Subject'
        : selectedScenarioLabel.trim();
    return Container(
      key: const ValueKey<String>('desktop-subject-selector'),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 2),
      decoration: BoxDecoration(
        border: Border.all(color: _terminalBorder),
        color: Colors.transparent,
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          key: const ValueKey<String>('desktop-subject-selector-control'),
          value: selectedValue,
          isExpanded: true,
          menuMaxHeight: 420,
          dropdownColor: const Color(0xFF081114),
          iconEnabledColor: _terminalTextMuted,
          iconDisabledColor: _terminalTextMuted,
          style: const TextStyle(
            color: _terminalText,
            fontFamily: 'monospace',
            fontSize: 15,
            fontWeight: FontWeight.w600,
          ),
          hint: Text(
            hintText,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              color: _terminalTextMuted,
              fontFamily: 'monospace',
              fontSize: 15,
              fontWeight: FontWeight.w600,
            ),
          ),
          items: subjects
              .map(
                (subjectScenario) => DropdownMenuItem<String>(
                  value: _subjectScenarioIdentity(subjectScenario),
                  child: Text(
                    _subjectScenarioLabel(subjectScenario),
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: _terminalText,
                      fontFamily: 'monospace',
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              )
              .toList(growable: false),
          onChanged: enabled
              ? (value) {
                  if (value != null && value != selectedScenarioKey) {
                    onChanged(value);
                  }
                }
              : null,
        ),
      ),
    );
  }
}

class _TabChip extends StatelessWidget {
  const _TabChip({
    super.key,
    required this.label,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(
          color: selected ? _terminalAccent : Colors.transparent,
          border: Border.all(color: _terminalBorder),
        ),
        child: Text(
          selected ? '• $label' : label,
          style: TextStyle(
            color: selected ? Colors.white : _terminalTextMuted,
            fontFamily: 'monospace',
            fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
            fontSize: 15,
          ),
        ),
      ),
    );
  }
}

class _GateStatusRow extends StatelessWidget {
  const _GateStatusRow({
    required this.currentStep,
    required this.statusTitle,
    required this.statusRows,
    required this.onAction,
  });

  final _CurrentStepBlock currentStep;
  final String statusTitle;
  final List<subject.KeyValueRow> statusRows;
  final SubjectActionCallback onAction;

  int _gateActionColumnCountForWidth(double width) => width >= 390 ? 2 : 1;

  double _estimatedGateRowHeight(double maxWidth) {
    final columnCount = _gateActionColumnCountForWidth(maxWidth);
    final actionRows = currentStep.actions.isEmpty
        ? 0
        : ((currentStep.actions.length - 1) ~/ columnCount) + 1;
    final prefixedAction = currentStep.actions.any(
      (action) => _subjectActionLabelParts(action.label).$1.isNotEmpty,
    );
    final actionSlotHeight = prefixedAction ? 58.0 : 44.0;
    final actionsHeight = currentStep.actions.isEmpty
        ? 0.0
        : 34.0 + (actionRows * actionSlotHeight) + ((actionRows - 1) * 10.0);
    final currentStepHeight = currentStep.hasPrimaryStepContent ? 54.0 : 0.0;
    return (56.0 + currentStepHeight + actionsHeight).clamp(
      _gateStatusRowMinHeight,
      _gateStatusRowMaxHeight,
    );
  }

  @override
  Widget build(BuildContext context) {
    Widget buildCurrentStepPanel() {
      return _CompactGateSection(
        title: 'Current Step',
        showBorder: false,
        child: Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: ClipRect(
                  child: SingleChildScrollView(
                    key: const ValueKey<String>('gate-current-step-scroll'),
                    primary: false,
                    physics: const ClampingScrollPhysics(),
                    child: _CurrentStepPane(currentStep: currentStep),
                  ),
                ),
              ),
              if (currentStep.actions.isNotEmpty) ...[
                const SizedBox(height: 12),
                const Text(
                  'Actions',
                  style: TextStyle(
                    color: _terminalText,
                    fontFamily: 'monospace',
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 8),
                _GateActionRow(
                  actions: currentStep.actions
                      .map(
                        (action) => subject.SubjectActionSpec()
                          ..key = action.key
                          ..label = action.label
                          ..enabled =
                              action.enabled &&
                              !_isFlutterDisabledSubjectAction(action.key),
                      )
                      .toList(),
                  onAction: onAction,
                ),
              ],
            ],
          ),
        ),
      );
    }

    Widget buildStatusPanel() {
      return _CompactGateSection(
        title: statusTitle,
        child: Expanded(
          child: ClipRect(
            child: SingleChildScrollView(
              key: const ValueKey<String>('gate-status-scroll'),
              primary: false,
              physics: const ClampingScrollPhysics(),
              child: Align(
                alignment: Alignment.topLeft,
                child: _StatusRows(rows: statusRows),
              ),
            ),
          ),
        ),
      );
    }

    return LayoutBuilder(
      builder: (context, constraints) {
        final stacked = constraints.maxWidth < _gateStatusStackBreakpoint;
        final rowHeight = _estimatedGateRowHeight(constraints.maxWidth);
        if (stacked) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              SizedBox(height: rowHeight + 16, child: buildCurrentStepPanel()),
              const SizedBox(height: 18),
              SizedBox(
                height: _gateStatusStackHeight,
                child: buildStatusPanel(),
              ),
            ],
          );
        }
        return SizedBox(
          height: rowHeight,
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Expanded(flex: 2, child: buildCurrentStepPanel()),
              const SizedBox(width: 18),
              Expanded(flex: 2, child: buildStatusPanel()),
            ],
          ),
        );
      },
    );
  }
}

class _MoreActionsBlock extends StatelessWidget {
  const _MoreActionsBlock({required this.actions, required this.onAction});

  final List<subject.SubjectActionSpec> actions;
  final SubjectActionCallback onAction;

  @override
  Widget build(BuildContext context) {
    if (actions.isEmpty) {
      return const SizedBox.shrink();
    }
    return _BorderlessTerminalSection(
      title: 'More Actions',
      child: _ActionRow(actions: actions, onAction: onAction),
    );
  }
}

class _ActionRow extends StatelessWidget {
  const _ActionRow({required this.actions, required this.onAction});

  final List<subject.SubjectActionSpec> actions;
  final SubjectActionCallback onAction;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 12,
      runSpacing: 10,
      children: [
        for (final action in actions)
          _ActionButton(
            label: action.label,
            enabled:
                action.enabled && !_isFlutterDisabledSubjectAction(action.key),
            onPressed:
                action.enabled && !_isFlutterDisabledSubjectAction(action.key)
                ? () =>
                      unawaited(onAction(action.key, actionLabel: action.label))
                : null,
          ),
      ],
    );
  }
}

class _GateActionRow extends StatelessWidget {
  const _GateActionRow({required this.actions, required this.onAction});

  final List<subject.SubjectActionSpec> actions;
  final SubjectActionCallback onAction;

  @override
  Widget build(BuildContext context) {
    final reservePhaseLabelSpace = actions.any(
      (action) => _subjectActionLabelParts(action.label).$1.isNotEmpty,
    );
    return LayoutBuilder(
      builder: (context, constraints) {
        final maxWidth = constraints.maxWidth;
        final slotMinWidth = maxWidth >= 940
            ? 168.0
            : maxWidth >= 680
            ? 156.0
            : maxWidth;
        final slotMaxWidth = maxWidth >= 940
            ? 220.0
            : maxWidth >= 680
            ? 208.0
            : maxWidth;
        return Wrap(
          spacing: 14,
          runSpacing: 10,
          children: [
            for (final action in actions)
              ConstrainedBox(
                constraints: BoxConstraints(
                  minWidth: slotMinWidth.clamp(0.0, maxWidth),
                  maxWidth: slotMaxWidth.clamp(0.0, maxWidth),
                ),
                child: _GateActionSlot(
                  action: action,
                  onAction: onAction,
                  reservePhaseLabelSpace: reservePhaseLabelSpace,
                ),
              ),
          ],
        );
      },
    );
  }
}

class _GateActionSlot extends StatelessWidget {
  const _GateActionSlot({
    required this.action,
    required this.onAction,
    required this.reservePhaseLabelSpace,
  });

  final subject.SubjectActionSpec action;
  final SubjectActionCallback onAction;
  final bool reservePhaseLabelSpace;

  @override
  Widget build(BuildContext context) {
    final parts = _subjectActionLabelParts(action.label);
    final phaseLabel = parts.$1;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (reservePhaseLabelSpace) ...[
          SizedBox(
            height: 16,
            child: phaseLabel.isEmpty
                ? const SizedBox.shrink()
                : Text(
                    phaseLabel,
                    style: const TextStyle(
                      color: _terminalSection,
                      fontFamily: 'monospace',
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
          ),
          const SizedBox(height: 3),
        ],
        _ActionButton(
          label: parts.$2,
          enabled:
              action.enabled && !_isFlutterDisabledSubjectAction(action.key),
          compact: true,
          onPressed:
              action.enabled && !_isFlutterDisabledSubjectAction(action.key)
              ? () => unawaited(onAction(action.key, actionLabel: action.label))
              : null,
        ),
      ],
    );
  }
}

class _ActionButton extends StatelessWidget {
  const _ActionButton({
    required this.label,
    required this.enabled,
    this.compact = false,
    this.onPressed,
  });

  final String label;
  final bool enabled;
  final bool compact;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {
    final active = enabled && onPressed != null;
    return OutlinedButton(
      onPressed: active ? onPressed : null,
      style: OutlinedButton.styleFrom(
        backgroundColor: active ? _terminalAccent : Colors.transparent,
        foregroundColor: active ? Colors.white : _terminalTextMuted,
        side: const BorderSide(color: _terminalBorder),
        padding: compact
            ? const EdgeInsets.symmetric(horizontal: 16, vertical: 10)
            : const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
        minimumSize: Size(0, compact ? 40 : 44),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
        visualDensity: const VisualDensity(horizontal: -1, vertical: -1),
        textStyle: TextStyle(
          fontFamily: 'monospace',
          fontSize: compact ? 13 : 14,
          fontWeight: FontWeight.w700,
        ),
      ),
      child: Text(label, textAlign: TextAlign.center, softWrap: true),
    );
  }
}

class _CompactGateSection extends StatelessWidget {
  const _CompactGateSection({
    required this.title,
    required this.child,
    this.showBorder = true,
  });

  final String title;
  final Widget child;
  final bool showBorder;

  @override
  Widget build(BuildContext context) {
    return Container(
      key: ValueKey<String>('gate-section:$title'),
      decoration: BoxDecoration(
        color: Colors.transparent,
        border: Border.all(
          color: showBorder ? _terminalBorder : Colors.transparent,
        ),
      ),
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            title,
            style: const TextStyle(
              color: _terminalSection,
              fontFamily: 'monospace',
              fontSize: 15,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 10),
          child,
        ],
      ),
    );
  }
}

class _ControlGrid extends StatelessWidget {
  const _ControlGrid({required this.children});

  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 14,
      runSpacing: 10,
      crossAxisAlignment: WrapCrossAlignment.start,
      children: children,
    );
  }
}

String? _subjectSelectActionKey(
  subject.SubjectSelectSpecView spec,
  String nextValue,
) {
  if (nextValue.trim().isEmpty) {
    return null;
  }
  return switch (spec.key) {
    'itemize_decision_role' =>
      'set_selected_itemized_item_decision_role:$nextValue',
    'research_source_collection' => 'set_research_source_collection:$nextValue',
    'research_source_revision_baseline' =>
      'set_research_source_revision_baseline:$nextValue',
    'draft_semantic_kind' =>
      'set_selected_draft_review_semantic_kind:$nextValue',
    'draft_render_kind' => 'set_selected_draft_review_render_kind:$nextValue',
    'draft_evidence_mode' =>
      'set_selected_draft_review_evidence_mode:$nextValue',
    'draft_transform_mode' =>
      'set_selected_draft_review_transform_mode:$nextValue',
    'draft_model_construct_sort' =>
      'set_selected_draft_construct_sort:$nextValue',
    'draft_model_construct_lane' =>
      'set_selected_draft_construct_lane:$nextValue',
    'draft_model_transition_source' =>
      'set_selected_draft_construct_transition_source:$nextValue',
    'draft_model_transition_target' =>
      'set_selected_draft_construct_transition_target:$nextValue',
    'draft_model_policy_profile' => 'set_decision_policy_profile:$nextValue',
    'review_publication_output_mode' ||
    'publication_output_mode' => 'set_publication_output_mode:$nextValue',
    'review_publication_section_plan' ||
    'publication_section_plan' => 'set_publication_section_plan:$nextValue',
    'review_publication_diff_baseline' ||
    'publication_diff_baseline' => 'set_publication_diff_baseline:$nextValue',
    'review_composition_unit_target' || 'publication_composition_unit_target' =>
      'set_selected_composition_unit:$nextValue',
    'review_publication_section_target' || 'publication_section_target' =>
      'set_selected_publication_section:$nextValue',
    'publication_import_target' => 'set_publication_import_target:$nextValue',
    'publication_import_usage' =>
      'set_selected_publication_import_usage_$nextValue',
    _ => null,
  };
}

String? _subjectSwitchActionKey(subject.SubjectSwitchSpecView spec) {
  return switch (spec.key) {
    'research_selected_source_collection_membership' =>
      'toggle_selected_staged_source_in_collection',
    'itemize_hold' => 'hold_selected_itemized_item',
    'draft_decision_included' =>
      'toggle_selected_draft_review_item_in_decision_frame',
    'review_composition_unit_included' ||
    'publication_composition_unit_included' =>
      'toggle_selected_composition_unit',
    'review_publication_section_included' ||
    'publication_section_included' => 'toggle_selected_publication_section',
    'publication_import_included' => 'toggle_selected_publication_import',
    _ => null,
  };
}

bool? _checkboxStateFromToken(String token) {
  final normalized = token.trim().toLowerCase();
  if (normalized == 'x') {
    return true;
  }
  if (normalized.isEmpty) {
    return false;
  }
  return null;
}

bool? _checkboxStateFromMarker(String marker) {
  final normalized = marker.trim().toLowerCase();
  if (normalized == '[x]') {
    return true;
  }
  if (normalized == '[ ]') {
    return false;
  }
  return null;
}

class _TerminalInlineCheckbox extends StatelessWidget {
  const _TerminalInlineCheckbox({required this.checked, this.onTap, super.key});

  final bool checked;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final checkbox = Container(
      width: 14,
      height: 14,
      decoration: BoxDecoration(
        color: Colors.transparent,
        border: Border.all(color: _terminalText, width: 1),
      ),
      child: checked
          ? const Icon(Icons.check_rounded, size: 11, color: _terminalText)
          : null,
    );
    if (onTap == null) {
      return checkbox;
    }
    return MouseRegion(
      cursor: SystemMouseCursors.click,
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: onTap,
        child: checkbox,
      ),
    );
  }
}

class _SelectControlBlock extends StatelessWidget {
  const _SelectControlBlock({
    required this.spec,
    this.widthFactor = 1.0,
    this.interactionsEnabled = false,
    this.onAction,
  });

  final subject.SubjectSelectSpecView? spec;
  final double widthFactor;
  final bool interactionsEnabled;
  final SubjectActionCallback? onAction;

  @override
  Widget build(BuildContext context) {
    if (spec == null) {
      return const SizedBox.shrink();
    }
    final currentSpec = spec!;
    final selectedValue =
        currentSpec.options.any((option) => option.value == currentSpec.value)
        ? currentSpec.value
        : null;
    return ConstrainedBox(
      constraints: BoxConstraints(
        minWidth: 200 * widthFactor,
        maxWidth: 300 * widthFactor,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _TerminalSectionTitle(spec!.label),
          const SizedBox(height: 6),
          Container(
            decoration: BoxDecoration(
              color: _terminalAccent.withValues(alpha: 0.74),
              border: Border.all(color: _terminalBorder),
            ),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: DropdownButtonHideUnderline(
                child: DropdownButton<String>(
                  key: ValueKey<String>('select-control:${currentSpec.key}'),
                  isExpanded: true,
                  value: selectedValue,
                  dropdownColor: const Color(0xFF081114),
                  iconEnabledColor: Colors.white,
                  iconDisabledColor: _terminalTextMuted,
                  style: const TextStyle(
                    color: Colors.white,
                    fontFamily: 'monospace',
                    fontSize: 14,
                  ),
                  hint: Text(
                    currentSpec.label,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: Colors.white,
                      fontFamily: 'monospace',
                      fontSize: 14,
                    ),
                  ),
                  items: currentSpec.options
                      .map(
                        (option) => DropdownMenuItem<String>(
                          value: option.value,
                          child: Text(
                            option.label,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              color: Colors.white,
                              fontFamily: 'monospace',
                              fontSize: 14,
                            ),
                          ),
                        ),
                      )
                      .toList(growable: false),
                  onChanged:
                      interactionsEnabled &&
                          currentSpec.enabled &&
                          onAction != null
                      ? (nextValue) {
                          if (nextValue == null ||
                              nextValue == currentSpec.value) {
                            return;
                          }
                          final actionKey = _subjectSelectActionKey(
                            currentSpec,
                            nextValue,
                          );
                          if (actionKey == null) {
                            return;
                          }
                          unawaited(
                            onAction!(
                              actionKey,
                              actionLabel: currentSpec.label,
                            ),
                          );
                        }
                      : null,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _SwitchControlBlock extends StatelessWidget {
  const _SwitchControlBlock({
    required this.spec,
    this.interactionsEnabled = false,
    this.onAction,
  });

  final subject.SubjectSwitchSpecView? spec;
  final bool interactionsEnabled;
  final SubjectActionCallback? onAction;

  @override
  Widget build(BuildContext context) {
    if (spec == null) {
      return const SizedBox.shrink();
    }
    final currentSpec = spec!;
    final actionKey = _subjectSwitchActionKey(currentSpec);
    final enabled =
        interactionsEnabled &&
        currentSpec.enabled &&
        onAction != null &&
        actionKey != null;
    return ConstrainedBox(
      constraints: const BoxConstraints(minWidth: 128, maxWidth: 190),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _TerminalSectionTitle(spec!.label),
          const SizedBox(height: 6),
          InkWell(
            key: ValueKey<String>('switch-control:${currentSpec.key}'),
            onTap: enabled
                ? () => unawaited(
                    onAction!(actionKey, actionLabel: currentSpec.label),
                  )
                : null,
            child: Container(
              height: 46,
              width: 72,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: _terminalAccent.withValues(alpha: 0.74),
                border: Border.all(color: _terminalBorder),
              ),
              child: _TerminalInlineCheckbox(checked: currentSpec.value),
            ),
          ),
        ],
      ),
    );
  }
}

class _SelectionListSummaryBlock extends StatelessWidget {
  const _SelectionListSummaryBlock({required this.spec});

  final subject.SubjectSelectionListSpecView? spec;

  @override
  Widget build(BuildContext context) {
    if (spec == null) {
      return const SizedBox.shrink();
    }
    return ConstrainedBox(
      constraints: const BoxConstraints(minWidth: 220, maxWidth: 360),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _TerminalSectionTitle(spec!.label),
          const SizedBox(height: 6),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            decoration: BoxDecoration(
              color: _terminalAccent.withValues(alpha: 0.74),
              border: Border.all(color: _terminalBorder),
            ),
            child: Text(
              _PaneContent._selectedOptionsLabel(spec!),
              style: const TextStyle(
                color: Colors.white,
                fontFamily: 'monospace',
                fontSize: 14,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _DraftLensStrip extends StatelessWidget {
  const _DraftLensStrip({
    required this.activeShellStateKey,
    required this.onShellStateSelected,
    required this.onAction,
  });

  final String activeShellStateKey;
  final ValueChanged<String> onShellStateSelected;
  final SubjectActionCallback onAction;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 12,
      runSpacing: 8,
      children: [
        _LensTab(
          tapKey: const ValueKey('draft-lens-frame'),
          label: 'Frame',
          selected: activeShellStateKey == 'draft.frame',
          onTap: () {
            onShellStateSelected('draft.frame');
            unawaited(
              onAction(
                'open_draft_model_frame_view',
                actionLabel: 'Draft: Frame',
              ),
            );
          },
        ),
        _LensTab(
          tapKey: const ValueKey('draft-lens-model'),
          label: 'Model',
          selected: activeShellStateKey == 'draft.model',
          onTap: () {
            onShellStateSelected('draft.model');
            unawaited(
              onAction(
                'open_draft_model_model_view',
                actionLabel: 'Draft: Model',
              ),
            );
          },
        ),
        _LensTab(
          tapKey: const ValueKey('draft-lens-explore'),
          label: 'Explore',
          selected: activeShellStateKey == 'draft.explore',
          onTap: () {
            onShellStateSelected('draft.explore');
            unawaited(
              onAction(
                'open_draft_model_explore_view',
                actionLabel: 'Draft: Explore',
              ),
            );
          },
        ),
      ],
    );
  }
}

class _LensTab extends StatelessWidget {
  const _LensTab({
    this.tapKey,
    required this.label,
    required this.selected,
    required this.onTap,
  });

  final Key? tapKey;
  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      key: tapKey,
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.only(bottom: 6),
        child: Container(
          decoration: BoxDecoration(
            border: Border(
              bottom: BorderSide(
                color: selected ? const Color(0xFF3B82F6) : _terminalBorder,
                width: 3,
              ),
            ),
          ),
          padding: const EdgeInsets.only(bottom: 6),
          child: Text(
            label,
            style: TextStyle(
              color: selected ? Colors.white : _terminalTextMuted,
              fontFamily: 'monospace',
              fontSize: 14,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
      ),
    );
  }
}

ValueKey<String> _interactivePaneRowKey(String paneKey, int rowIndex) {
  return ValueKey<String>('interactive-pane-row:$paneKey:$rowIndex');
}

class _WorkbenchKeyboardScope extends StatefulWidget {
  const _WorkbenchKeyboardScope({
    required this.enabled,
    required this.handlers,
    required this.onToggleInfo,
    required this.onToggleMaximize,
    required this.childBuilder,
  });

  final bool enabled;
  final Map<_PaneShortcut, _PaneShortcutHandler> handlers;
  final VoidCallback onToggleInfo;
  final VoidCallback onToggleMaximize;
  final Widget Function(VoidCallback requestFocus) childBuilder;

  @override
  State<_WorkbenchKeyboardScope> createState() =>
      _WorkbenchKeyboardScopeState();
}

class _WorkbenchKeyboardScopeState extends State<_WorkbenchKeyboardScope> {
  late final FocusNode _focusNode;

  @override
  void initState() {
    super.initState();
    _focusNode = FocusNode(debugLabel: 'workbench-keyboard-scope');
  }

  @override
  void dispose() {
    _focusNode.dispose();
    super.dispose();
  }

  KeyEventResult _handleKeyEvent(FocusNode node, KeyEvent event) {
    if (!widget.enabled || event is! KeyDownEvent) {
      return KeyEventResult.ignored;
    }
    if (event.logicalKey == LogicalKeyboardKey.f8) {
      widget.onToggleMaximize();
      return KeyEventResult.handled;
    }
    if (event.logicalKey == LogicalKeyboardKey.keyI) {
      widget.onToggleInfo();
      return KeyEventResult.handled;
    }
    final shortcut = _shortcutForEvent(event);
    if (shortcut == null) {
      return KeyEventResult.ignored;
    }
    final handler = widget.handlers[shortcut];
    if (handler == null) {
      return KeyEventResult.ignored;
    }
    unawaited(handler());
    return KeyEventResult.handled;
  }

  _PaneShortcut? _shortcutForEvent(KeyEvent event) {
    final key = event.logicalKey;
    final shiftPressed = HardwareKeyboard.instance.isShiftPressed;
    if (key == LogicalKeyboardKey.arrowUp) {
      if (shiftPressed) {
        if (widget.handlers.containsKey(_PaneShortcut.reorderEarlier)) {
          return _PaneShortcut.reorderEarlier;
        }
        if (widget.handlers.containsKey(_PaneShortcut.previewEarlier)) {
          return _PaneShortcut.previewEarlier;
        }
      }
      return _PaneShortcut.moveUp;
    }
    if (key == LogicalKeyboardKey.arrowDown) {
      if (shiftPressed) {
        if (widget.handlers.containsKey(_PaneShortcut.reorderLater)) {
          return _PaneShortcut.reorderLater;
        }
        if (widget.handlers.containsKey(_PaneShortcut.previewLater)) {
          return _PaneShortcut.previewLater;
        }
      }
      return _PaneShortcut.moveDown;
    }
    if (key == LogicalKeyboardKey.enter ||
        key == LogicalKeyboardKey.numpadEnter) {
      return _PaneShortcut.activate;
    }
    if (key == LogicalKeyboardKey.keyH) {
      return _PaneShortcut.hold;
    }
    if (key == LogicalKeyboardKey.keyX) {
      return _PaneShortcut.toggle;
    }
    if (key == LogicalKeyboardKey.keyR) {
      return _PaneShortcut.release;
    }
    if (key == LogicalKeyboardKey.keyD) {
      return _PaneShortcut.decisionToggle;
    }
    if (key == LogicalKeyboardKey.keyK) {
      return _PaneShortcut.previewEarlier;
    }
    if (key == LogicalKeyboardKey.keyJ) {
      return _PaneShortcut.previewLater;
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    return Focus(
      focusNode: _focusNode,
      autofocus: true,
      onKeyEvent: _handleKeyEvent,
      child: widget.childBuilder(_focusNode.requestFocus),
    );
  }
}

class _PaneFrame extends StatelessWidget {
  const _PaneFrame({
    required this.paneId,
    required this.active,
    required this.onActivate,
    required this.title,
    required this.behavior,
    required this.child,
    this.trailing,
  });

  final String paneId;
  final bool active;
  final VoidCallback onActivate;
  final String title;
  final _PaneViewportBehavior behavior;
  final Widget child;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final compactChrome =
            constraints.hasBoundedHeight && constraints.maxHeight < 140;
        final framePadding = compactChrome ? 12.0 : 15.0;
        final headerGap = compactChrome ? 8.0 : 12.0;
        final trailingGap = compactChrome ? 8.0 : 10.0;
        final titleSize = compactChrome ? 14.0 : 15.0;
        final viewport = _PaneViewport(
          paneId: paneId,
          behavior: behavior,
          onActivate: onActivate,
          child: child,
        );
        final body = behavior.fixedHeightPx != null
            ? SizedBox(height: behavior.fixedHeightPx, child: viewport)
            : Expanded(child: viewport);

        return GestureDetector(
          key: ValueKey<String>('pane-frame:$paneId'),
          behavior: HitTestBehavior.translucent,
          onTap: onActivate,
          child: Container(
            decoration: BoxDecoration(
              color: Colors.transparent,
              border: Border.all(
                color: active ? _terminalSection : _terminalBorder,
                width: active ? 2 : 1,
              ),
            ),
            padding: EdgeInsets.all(framePadding),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        title,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          color: _terminalText,
                          fontFamily: 'monospace',
                          fontSize: titleSize,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                    if (trailing != null) ...[
                      SizedBox(width: trailingGap),
                      trailing!,
                    ],
                  ],
                ),
                SizedBox(height: headerGap),
                body,
              ],
            ),
          ),
        );
      },
    );
  }
}

class _PaneChrome extends StatelessWidget {
  const _PaneChrome({
    this.infoActive = false,
    this.maximizeActive = false,
    this.onInfo,
    this.onMaximize,
    this.onExpand,
    this.onCollapse,
  });

  final bool infoActive;
  final bool maximizeActive;
  final VoidCallback? onInfo;
  final VoidCallback? onMaximize;
  final VoidCallback? onExpand;
  final VoidCallback? onCollapse;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        const Text(
          '@llm',
          style: TextStyle(
            color: _terminalTextMuted,
            fontFamily: 'monospace',
            fontSize: 12,
          ),
        ),
        const SizedBox(width: 10),
        if (onInfo != null)
          _PaneIconButton(icon: '?', active: infoActive, onTap: onInfo!),
        if (onMaximize != null)
          _PaneIconButton(
            icon: '[ ]',
            active: maximizeActive,
            onTap: onMaximize!,
          ),
        if (onExpand != null) _PaneIconButton(icon: '+', onTap: onExpand!),
        if (onCollapse != null) _PaneIconButton(icon: '-', onTap: onCollapse!),
      ],
    );
  }
}

class _PaneIconButton extends StatelessWidget {
  const _PaneIconButton({
    required this.icon,
    required this.onTap,
    this.active = false,
  });

  final String icon;
  final VoidCallback onTap;
  final bool active;

  @override
  Widget build(BuildContext context) {
    final iconWidget = switch (icon) {
      '?' => const Icon(Icons.help_outline_rounded, size: 15),
      '[ ]' => const Icon(Icons.crop_square_rounded, size: 15),
      '+' => const Icon(Icons.open_in_full_rounded, size: 15),
      '-' => const Icon(Icons.close_fullscreen_rounded, size: 15),
      _ => Text(
        icon,
        style: const TextStyle(
          fontFamily: 'monospace',
          fontSize: 15,
          fontWeight: FontWeight.w700,
        ),
      ),
    };
    return InkWell(
      key: ValueKey<String>('pane-icon:$icon'),
      onTap: onTap,
      child: Container(
        color: active ? _terminalAccent : Colors.transparent,
        padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 3),
        child: IconTheme(
          data: IconThemeData(
            color: active ? Colors.white : _terminalTextMuted,
          ),
          child: DefaultTextStyle(
            style: TextStyle(color: active ? Colors.white : _terminalTextMuted),
            child: iconWidget,
          ),
        ),
      ),
    );
  }
}

class _PaneViewport extends StatefulWidget {
  const _PaneViewport({
    required this.paneId,
    required this.behavior,
    required this.onActivate,
    required this.child,
  });

  final String paneId;
  final _PaneViewportBehavior behavior;
  final VoidCallback onActivate;
  final Widget child;

  @override
  State<_PaneViewport> createState() => _PaneViewportState();
}

class _PaneViewportState extends State<_PaneViewport> {
  late final ScrollController _verticalController;
  late final ScrollController _horizontalController;

  @override
  void initState() {
    super.initState();
    _verticalController = ScrollController();
    _horizontalController = ScrollController();
  }

  @override
  void dispose() {
    _verticalController.dispose();
    _horizontalController.dispose();
    super.dispose();
  }

  void _handlePointerSignal(PointerSignalEvent signal) {
    if (signal is! PointerScrollEvent) {
      return;
    }
    widget.onActivate();
    if (widget.behavior.scrollY && _verticalController.hasClients) {
      final nextOffset =
          _verticalController.offset +
          signal.scrollDelta.dy.sign * (_terminalHeightUnitPx * 3);
      _verticalController.jumpTo(
        nextOffset.clamp(
          _verticalController.position.minScrollExtent,
          _verticalController.position.maxScrollExtent,
        ),
      );
      return;
    }
    if (widget.behavior.scrollX && _horizontalController.hasClients) {
      final nextOffset =
          _horizontalController.offset + signal.scrollDelta.dx.sign * 48;
      _horizontalController.jumpTo(
        nextOffset.clamp(
          _horizontalController.position.minScrollExtent,
          _horizontalController.position.maxScrollExtent,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    Widget content = Align(alignment: Alignment.topLeft, child: widget.child);
    if (widget.behavior.minHeightPx > 0) {
      content = ConstrainedBox(
        constraints: BoxConstraints(minHeight: widget.behavior.minHeightPx),
        child: content,
      );
    }
    Widget viewport = SingleChildScrollView(
      key: ValueKey<String>('pane-scroll-y:${widget.paneId}'),
      controller: _verticalController,
      physics: widget.behavior.scrollY
          ? const ClampingScrollPhysics()
          : const NeverScrollableScrollPhysics(),
      child: content,
    );
    if (widget.behavior.scrollX) {
      viewport = SingleChildScrollView(
        key: ValueKey<String>('pane-scroll-x:${widget.paneId}'),
        controller: _horizontalController,
        scrollDirection: Axis.horizontal,
        physics: const ClampingScrollPhysics(),
        child: viewport,
      );
    }
    return ClipRect(
      child: Listener(
        onPointerDown: (_) => widget.onActivate(),
        onPointerSignal: _handlePointerSignal,
        child: Container(
          key: ValueKey<String>('pane-viewport:${widget.paneId}'),
          alignment: Alignment.topLeft,
          child: viewport,
        ),
      ),
    );
  }
}

class _StatusRows extends StatelessWidget {
  const _StatusRows({required this.rows});

  final List<subject.KeyValueRow> rows;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (final row in rows)
          Padding(
            padding: const EdgeInsets.only(bottom: 3),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                SizedBox(
                  width: 172,
                  child: Text(
                    row.label,
                    style: const TextStyle(
                      color: _terminalText,
                      fontFamily: 'monospace',
                      fontSize: 14,
                      height: 1.3,
                    ),
                  ),
                ),
                Expanded(
                  child: Text(
                    row.value,
                    style: const TextStyle(
                      color: _terminalText,
                      fontFamily: 'monospace',
                      fontSize: 14,
                      height: 1.3,
                    ),
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }
}

class _ShellSectionBlock extends StatelessWidget {
  const _ShellSectionBlock({required this.minHeight, required this.child});

  final double minHeight;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return ConstrainedBox(
      constraints: BoxConstraints(minHeight: minHeight),
      child: child,
    );
  }
}

class _PaneContent extends StatelessWidget {
  const _PaneContent({
    required this.pane,
    required this.fallbackTitle,
    required this.dense,
    required this.wrapText,
    this.interactionsEnabled = false,
    this.onFocusRequested,
    this.onSelectIndex,
    this.onToggleIndex,
  });

  final subject.SubjectPaneView? pane;
  final String fallbackTitle;
  final bool dense;
  final bool wrapText;
  final bool interactionsEnabled;
  final VoidCallback? onFocusRequested;
  final Future<void> Function(int targetIndex)? onSelectIndex;
  final Future<void> Function(int targetIndex)? onToggleIndex;

  @override
  Widget build(BuildContext context) {
    final effectivePane = pane;
    if (effectivePane == null) {
      return Text(
        'No data for $fallbackTitle.',
        style: const TextStyle(
          color: _terminalTextMuted,
          fontFamily: 'monospace',
          fontSize: 14,
        ),
      );
    }

    final interactiveSpec = _interactivePaneSpecs[effectivePane.key];
    if (interactiveSpec != null) {
      switch (interactiveSpec.rendererKind) {
        case _InteractivePaneRendererKind.itemizeInventory:
          return _ItemizeInventoryPane(
            pane: effectivePane,
            dense: dense,
            wrapText: wrapText,
            interactionsEnabled: interactionsEnabled,
            onFocusRequested: onFocusRequested,
            onSelectIndex: onSelectIndex,
          );
        case _InteractivePaneRendererKind.draftScopeTree:
          return _DraftScopeTablePane(
            pane: effectivePane,
            dense: dense,
            titleHint: effectivePane.title.isNotEmpty
                ? effectivePane.title
                : fallbackTitle,
            wrapText: wrapText,
            interactionsEnabled: interactionsEnabled,
            onFocusRequested: onFocusRequested,
            onSelectIndex: onSelectIndex,
            onToggleIndex: onToggleIndex,
          );
        case _InteractivePaneRendererKind.reportScopeTree:
          return _ReportScopeTreePane(
            pane: effectivePane,
            dense: dense,
            wrapText: wrapText,
            interactionsEnabled: interactionsEnabled,
            onFocusRequested: onFocusRequested,
            onSelectIndex: onSelectIndex,
            onToggleIndex: onToggleIndex,
          );
      }
    }
    if (effectivePane.rows.isNotEmpty) {
      return _StructuredPaneView(
        pane: effectivePane,
        dense: dense,
        wrapText: wrapText,
      );
    }
    return _TerminalLineListPane(
      lines: effectivePane.lines,
      dense: dense,
      wrapText: wrapText,
    );
  }

  static String _selectedOptionsLabel(
    subject.SubjectSelectionListSpecView spec,
  ) {
    final selected = spec.options
        .where((option) => option.selected)
        .map((option) => option.label)
        .where((label) => label.isNotEmpty)
        .toList(growable: false);
    if (selected.isNotEmpty) {
      return selected.join(', ');
    }
    return spec.label;
  }
}

class _StructuredPaneView extends StatelessWidget {
  const _StructuredPaneView({
    required this.pane,
    required this.dense,
    required this.wrapText,
  });

  final subject.SubjectPaneView pane;
  final bool dense;
  final bool wrapText;

  @override
  Widget build(BuildContext context) {
    final explicitRows = pane.rows
        .map((row) => _StructuredPaneRow(row.label, row.value))
        .toList(growable: false);
    final rows = explicitRows;
    if (rows.isEmpty) {
      return _TerminalLineListPane(
        lines: pane.lines,
        dense: dense,
        wrapText: wrapText,
      );
    }
    return LayoutBuilder(
      builder: (context, constraints) {
        final stacked = constraints.maxWidth < 540;
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            for (final row in rows)
              Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: row.label.isEmpty
                    ? Text(
                        row.value,
                        softWrap: wrapText,
                        overflow: wrapText
                            ? TextOverflow.visible
                            : TextOverflow.fade,
                        maxLines: wrapText ? null : 1,
                        style: TextStyle(
                          color: _terminalText,
                          fontFamily: 'monospace',
                          fontSize: dense ? 13 : 14,
                          height: 1.35,
                        ),
                      )
                    : stacked
                    ? Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            row.label,
                            style: TextStyle(
                              color: _terminalText,
                              fontFamily: 'monospace',
                              fontSize: dense ? 13 : 14,
                              height: 1.35,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            row.value,
                            softWrap: wrapText,
                            overflow: wrapText
                                ? TextOverflow.visible
                                : TextOverflow.fade,
                            maxLines: wrapText ? null : 1,
                            style: TextStyle(
                              color: _terminalText,
                              fontFamily: 'monospace',
                              fontSize: dense ? 13 : 14,
                              height: 1.35,
                            ),
                          ),
                        ],
                      )
                    : Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          SizedBox(
                            width: 210,
                            child: Text(
                              row.label,
                              style: TextStyle(
                                color: _terminalText,
                                fontFamily: 'monospace',
                                fontSize: dense ? 13 : 14,
                                height: 1.35,
                              ),
                            ),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              row.value,
                              softWrap: wrapText,
                              overflow: wrapText
                                  ? TextOverflow.visible
                                  : TextOverflow.fade,
                              maxLines: wrapText ? null : 1,
                              style: TextStyle(
                                color: _terminalText,
                                fontFamily: 'monospace',
                                fontSize: dense ? 13 : 14,
                                height: 1.35,
                              ),
                            ),
                          ),
                        ],
                      ),
              ),
          ],
        );
      },
    );
  }
}

class _CurrentStepPane extends StatelessWidget {
  const _CurrentStepPane({required this.currentStep});

  final _CurrentStepBlock currentStep;

  @override
  Widget build(BuildContext context) {
    final widgets = <Widget>[];

    void addField(String label, String value) {
      final normalizedValue = value.trim();
      if (normalizedValue.isEmpty) {
        return;
      }
      if (widgets.isNotEmpty) {
        widgets.add(const SizedBox(height: 10));
      }
      widgets.add(_CurrentStepField(label: label, value: normalizedValue));
    }

    void addLine(String value) {
      final normalizedValue = value.trim();
      if (normalizedValue.isEmpty) {
        return;
      }
      if (widgets.isNotEmpty) {
        widgets.add(const SizedBox(height: 10));
      }
      widgets.add(
        Text(
          normalizedValue,
          style: const TextStyle(
            color: _terminalText,
            fontFamily: 'monospace',
            fontSize: 14,
            height: 1.3,
          ),
        ),
      );
    }

    addField('Last Action', currentStep.lastActionText);
    addField('Do this now', currentStep.title);
    addField('Status', currentStep.status);
    addField('Why', currentStep.why);

    for (final line in currentStep.detailLines) {
      addLine(line);
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: widgets,
    );
  }
}

class _CurrentStepField extends StatelessWidget {
  const _CurrentStepField({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final stacked = constraints.maxWidth < 520;
        final labelWidget = Text(
          label,
          style: const TextStyle(
            color: _terminalSection,
            fontFamily: 'monospace',
            fontSize: 14,
            fontWeight: FontWeight.w700,
          ),
        );
        final valueWidget = Text(
          value,
          style: const TextStyle(
            color: _terminalText,
            fontFamily: 'monospace',
            fontSize: 14,
            height: 1.3,
          ),
        );
        if (stacked) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [labelWidget, const SizedBox(height: 4), valueWidget],
          );
        }
        return Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SizedBox(width: 132, child: labelWidget),
            const SizedBox(width: 10),
            Expanded(child: valueWidget),
          ],
        );
      },
    );
  }
}

class _TerminalLineListPane extends StatelessWidget {
  const _TerminalLineListPane({
    required this.lines,
    required this.dense,
    this.wrapText = true,
    this.selectable = false,
    this.preserveSelectionPrefix = false,
    this.preserveBlankLines = false,
  });

  final Iterable<String> lines;
  final bool dense;
  final bool wrapText;
  final bool selectable;
  final bool preserveSelectionPrefix;
  final bool preserveBlankLines;

  @override
  Widget build(BuildContext context) {
    final renderedLines = lines
        .map(
          (rawLine) => _RenderedPaneLine.fromRaw(
            rawLine,
            preserveSelectionPrefix: preserveSelectionPrefix,
          ),
        )
        .where((line) => preserveBlankLines || line.text.isNotEmpty)
        .toList(growable: false);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (final line in renderedLines)
          line.text.isEmpty
              ? SizedBox(height: dense ? 10 : 14)
              : Container(
                  color: line.selected ? _terminalAccent : Colors.transparent,
                  padding: EdgeInsets.symmetric(
                    horizontal: line.selected ? 8 : 0,
                    vertical: 1,
                  ),
                  child: Text(
                    line.text,
                    softWrap: wrapText,
                    overflow: wrapText
                        ? TextOverflow.visible
                        : TextOverflow.fade,
                    maxLines: wrapText ? null : 1,
                    style: TextStyle(
                      color: _terminalText,
                      fontFamily: 'monospace',
                      fontSize: dense ? 13 : 14,
                      height: 1.3,
                    ),
                  ),
                ),
      ],
    );
  }
}

class _ItemizeInventoryPane extends StatelessWidget {
  const _ItemizeInventoryPane({
    required this.pane,
    required this.dense,
    required this.wrapText,
    required this.interactionsEnabled,
    this.onFocusRequested,
    this.onSelectIndex,
  });

  final subject.SubjectPaneView pane;
  final bool dense;
  final bool wrapText;
  final bool interactionsEnabled;
  final VoidCallback? onFocusRequested;
  final Future<void> Function(int targetIndex)? onSelectIndex;

  @override
  Widget build(BuildContext context) {
    final parsed = _ItemizeInventoryData.fromPane(pane);
    if (!parsed.hasInventoryRows) {
      return _TerminalLineListPane(
        lines: pane.lines,
        dense: dense,
        wrapText: wrapText,
        selectable: true,
        preserveSelectionPrefix: true,
        preserveBlankLines: true,
      );
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (parsed.preamble.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: _TerminalLineListPane(
              lines: parsed.preamble,
              dense: dense,
              wrapText: wrapText,
              preserveBlankLines: true,
            ),
          ),
        _SelectableInventoryList(
          paneKey: pane.key,
          rows: parsed.rows,
          dense: dense,
          interactionsEnabled: interactionsEnabled,
          onFocusRequested: onFocusRequested,
          onSelectIndex: onSelectIndex,
        ),
        if (parsed.trailing.isNotEmpty) ...[
          const SizedBox(height: 12),
          _TerminalLineListPane(
            lines: parsed.trailing,
            dense: dense,
            wrapText: wrapText,
            preserveBlankLines: true,
          ),
        ],
      ],
    );
  }
}

class _SelectableInventoryList extends StatelessWidget {
  const _SelectableInventoryList({
    required this.paneKey,
    required this.rows,
    required this.dense,
    required this.interactionsEnabled,
    this.onFocusRequested,
    this.onSelectIndex,
  });

  final String paneKey;
  final List<_SelectableInventoryRow> rows;
  final bool dense;
  final bool interactionsEnabled;
  final VoidCallback? onFocusRequested;
  final Future<void> Function(int targetIndex)? onSelectIndex;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (var index = 0; index < rows.length; index++)
          _InventoryRowSurface(
            rowKey: _interactivePaneRowKey(paneKey, index),
            selected: rows[index].selected,
            enabled: interactionsEnabled,
            onFocusRequested: onFocusRequested,
            onTap: onSelectIndex == null || rows[index].selected
                ? null
                : () => onSelectIndex!(index),
            child: RichText(
              text: TextSpan(
                style: TextStyle(
                  color: _terminalText,
                  fontFamily: 'monospace',
                  fontSize: dense ? 13 : 14,
                  height: 1.3,
                ),
                children: [
                  if (rows[index].prefix.isNotEmpty)
                    TextSpan(
                      text: '${rows[index].prefix} ',
                      style: const TextStyle(fontWeight: FontWeight.w700),
                    ),
                  TextSpan(text: rows[index].label),
                ],
              ),
            ),
          ),
      ],
    );
  }
}

class _InventoryRowSurface extends StatelessWidget {
  const _InventoryRowSurface({
    required this.selected,
    required this.enabled,
    required this.child,
    this.rowKey,
    this.onFocusRequested,
    this.onTap,
    this.horizontalPadding,
  });

  final Key? rowKey;
  final bool selected;
  final bool enabled;
  final Widget child;
  final VoidCallback? onFocusRequested;
  final Future<void> Function()? onTap;
  final double? horizontalPadding;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      key: rowKey,
      behavior: HitTestBehavior.opaque,
      onTap: () {
        onFocusRequested?.call();
        if (!enabled || onTap == null) {
          return;
        }
        unawaited(onTap!());
      },
      child: Container(
        color: selected ? _terminalAccent : Colors.transparent,
        padding: EdgeInsets.symmetric(
          horizontal: horizontalPadding ?? (selected ? 8 : 0),
          vertical: 2,
        ),
        child: child,
      ),
    );
  }
}

class _DraftScopeTablePane extends StatelessWidget {
  const _DraftScopeTablePane({
    required this.pane,
    required this.dense,
    required this.titleHint,
    required this.wrapText,
    required this.interactionsEnabled,
    this.onFocusRequested,
    this.onSelectIndex,
    this.onToggleIndex,
  });

  final subject.SubjectPaneView pane;
  final bool dense;
  final String titleHint;
  final bool wrapText;
  final bool interactionsEnabled;
  final VoidCallback? onFocusRequested;
  final Future<void> Function(int targetIndex)? onSelectIndex;
  final Future<void> Function(int targetIndex)? onToggleIndex;

  @override
  Widget build(BuildContext context) {
    final parsed = _DraftScopeTableData.fromPane(pane, titleHint: titleHint);
    if (parsed.mode == _DraftScopeTableMode.fallback) {
      return _TerminalLineListPane(
        lines: pane.lines,
        dense: dense,
        wrapText: wrapText,
        preserveBlankLines: true,
      );
    }
    return LayoutBuilder(
      builder: (context, constraints) {
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SizedBox(
                    width: 42,
                    child: Text(
                      parsed.indicatorTitle,
                      style: const TextStyle(
                        color: _terminalText,
                        fontFamily: 'monospace',
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                  Expanded(
                    child: Text(
                      parsed.valueTitle,
                      style: const TextStyle(
                        color: _terminalText,
                        fontFamily: 'monospace',
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            for (var index = 0; index < parsed.rows.length; index++)
              _InventoryRowSurface(
                rowKey: _interactivePaneRowKey(pane.key, index),
                selected: parsed.rows[index].selected,
                enabled: interactionsEnabled,
                onFocusRequested: onFocusRequested,
                onTap: onSelectIndex == null || parsed.rows[index].selected
                    ? null
                    : () => onSelectIndex!(index),
                horizontalPadding: parsed.rows[index].selected ? 5 : 0,
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    SizedBox(
                      width: 42,
                      child: Builder(
                        builder: (context) {
                          final checkboxState =
                              parsed.mode == _DraftScopeTableMode.review
                              ? _checkboxStateFromToken(
                                  parsed.rows[index].indicator,
                                )
                              : null;
                          if (checkboxState != null) {
                            return Align(
                              alignment: Alignment.topLeft,
                              child: _TerminalInlineCheckbox(
                                key: ValueKey<String>(
                                  'row-checkbox:${pane.key}:$index',
                                ),
                                checked: checkboxState,
                                onTap:
                                    interactionsEnabled && onToggleIndex != null
                                    ? () {
                                        onFocusRequested?.call();
                                        unawaited(onToggleIndex!(index));
                                      }
                                    : null,
                              ),
                            );
                          }
                          return Text(
                            parsed.rows[index].indicator,
                            softWrap: false,
                            style: TextStyle(
                              color: _terminalText,
                              fontFamily: 'monospace',
                              fontSize: dense ? 13 : 14,
                              height: 1.25,
                            ),
                          );
                        },
                      ),
                    ),
                    Expanded(
                      child: Text(
                        parsed.rows[index].label,
                        softWrap: wrapText,
                        overflow: wrapText
                            ? TextOverflow.visible
                            : TextOverflow.fade,
                        maxLines: wrapText ? null : 1,
                        style: TextStyle(
                          color: _terminalText,
                          fontFamily: 'monospace',
                          fontSize: dense ? 13 : 14,
                          height: 1.25,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
          ],
        );
      },
    );
  }
}

class _ReportScopeTreePane extends StatelessWidget {
  const _ReportScopeTreePane({
    required this.pane,
    required this.dense,
    required this.wrapText,
    required this.interactionsEnabled,
    this.onFocusRequested,
    this.onSelectIndex,
    this.onToggleIndex,
  });

  final subject.SubjectPaneView pane;
  final bool dense;
  final bool wrapText;
  final bool interactionsEnabled;
  final VoidCallback? onFocusRequested;
  final Future<void> Function(int targetIndex)? onSelectIndex;
  final Future<void> Function(int targetIndex)? onToggleIndex;

  @override
  Widget build(BuildContext context) {
    final parsed = _ReportScopeTreeData.fromPane(pane);
    if (parsed.rows.isEmpty) {
      return _TerminalLineListPane(
        lines: pane.lines,
        dense: dense,
        wrapText: wrapText,
        preserveBlankLines: true,
      );
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (var index = 0; index < parsed.rows.length; index++)
          _InventoryRowSurface(
            rowKey: parsed.rows[index].selectable
                ? _interactivePaneRowKey(
                    pane.key,
                    parsed.rows[index].interactionIndex!,
                  )
                : null,
            selected: parsed.rows[index].selected,
            enabled: interactionsEnabled && parsed.rows[index].selectable,
            onFocusRequested: onFocusRequested,
            onTap:
                onSelectIndex == null ||
                    parsed.rows[index].selected ||
                    !parsed.rows[index].selectable
                ? null
                : () => onSelectIndex!(parsed.rows[index].interactionIndex!),
            child: parsed.rows[index].selectable
                ? _ReportScopeTreeRowView(
                    row: parsed.rows[index],
                    dense: dense,
                    wrapText: wrapText,
                    checkboxKey: ValueKey<String>(
                      'row-checkbox:${pane.key}:${parsed.rows[index].interactionIndex}',
                    ),
                    onCheckboxTap:
                        interactionsEnabled &&
                            onToggleIndex != null &&
                            parsed.rows[index].interactionIndex != null
                        ? () {
                            onFocusRequested?.call();
                            unawaited(
                              onToggleIndex!(
                                parsed.rows[index].interactionIndex!,
                              ),
                            );
                          }
                        : null,
                  )
                : Text(
                    parsed.rows[index].text,
                    softWrap: wrapText,
                    overflow: wrapText
                        ? TextOverflow.visible
                        : TextOverflow.fade,
                    maxLines: wrapText ? null : 1,
                    style: TextStyle(
                      color: _terminalText,
                      fontFamily: 'monospace',
                      fontSize: dense ? 13 : 14,
                      height: 1.3,
                    ),
                  ),
          ),
      ],
    );
  }
}

class _ReportScopeTreeRow {
  const _ReportScopeTreeRow({
    required this.text,
    required this.selected,
    required this.selectable,
    required this.interactionIndex,
    this.pointer = '',
    this.hold = '',
    this.indentLevel = 0,
    this.marker = '',
    this.label = '',
  });

  final String text;
  final bool selected;
  final bool selectable;
  final int? interactionIndex;
  final String pointer;
  final String hold;
  final int indentLevel;
  final String marker;
  final String label;
}

class _ReportScopeTreeData {
  const _ReportScopeTreeData({required this.rows});

  final List<_ReportScopeTreeRow> rows;

  factory _ReportScopeTreeData.fromPane(subject.SubjectPaneView pane) {
    final rows = <_ReportScopeTreeRow>[];
    var nextInteractionIndex = 0;
    for (final item in pane.items) {
      final selectable = item.selectable;
      final marker = switch (item.checkState) {
        'checked' => item.toggleable ? '[x]' : '[-]',
        'unchecked' => '[ ]',
        _ => '',
      };
      rows.add(
        _ReportScopeTreeRow(
          text: item.label,
          selected: item.selected,
          selectable: selectable,
          interactionIndex: selectable ? nextInteractionIndex++ : null,
          pointer: item.selected ? '>' : '',
          hold: item.held ? 'h' : '',
          indentLevel: item.depth,
          marker: marker,
          label: item.label,
        ),
      );
    }
    return _ReportScopeTreeData(rows: rows);
  }
}

class _ReportScopeTreeRowView extends StatelessWidget {
  const _ReportScopeTreeRowView({
    required this.row,
    required this.dense,
    required this.wrapText,
    this.checkboxKey,
    this.onCheckboxTap,
  });

  final _ReportScopeTreeRow row;
  final bool dense;
  final bool wrapText;
  final Key? checkboxKey;
  final VoidCallback? onCheckboxTap;

  @override
  Widget build(BuildContext context) {
    final checkboxState = _checkboxStateFromMarker(row.marker);
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 18,
          child: Text(
            row.pointer.trim(),
            style: TextStyle(
              color: _terminalText,
              fontFamily: 'monospace',
              fontSize: dense ? 13 : 14,
              height: 1.3,
            ),
          ),
        ),
        SizedBox(
          width: 18,
          child: Text(
            row.hold.trim(),
            style: TextStyle(
              color: _terminalText,
              fontFamily: 'monospace',
              fontSize: dense ? 13 : 14,
              height: 1.3,
            ),
          ),
        ),
        SizedBox(width: row.indentLevel * 16.0),
        if (checkboxState != null)
          Padding(
            padding: const EdgeInsets.only(top: 1, right: 8),
            child: _TerminalInlineCheckbox(
              key: checkboxKey,
              checked: checkboxState,
              onTap: onCheckboxTap,
            ),
          )
        else ...[
          Text(
            row.marker,
            style: TextStyle(
              color: _terminalText,
              fontFamily: 'monospace',
              fontSize: dense ? 13 : 14,
              height: 1.3,
            ),
          ),
          const SizedBox(width: 8),
        ],
        Expanded(
          child: Text(
            row.label,
            softWrap: wrapText,
            overflow: wrapText ? TextOverflow.visible : TextOverflow.fade,
            maxLines: wrapText ? null : 1,
            style: TextStyle(
              color: _terminalText,
              fontFamily: 'monospace',
              fontSize: dense ? 13 : 14,
              height: 1.3,
            ),
          ),
        ),
      ],
    );
  }
}

class _StructuredPaneRow {
  const _StructuredPaneRow(this.label, this.value);

  final String label;
  final String value;
}

class _RenderedPaneLine {
  const _RenderedPaneLine({required this.text, required this.selected});

  final String text;
  final bool selected;

  factory _RenderedPaneLine.fromRaw(
    String rawLine, {
    bool preserveSelectionPrefix = false,
  }) {
    final line = rawLine.replaceFirst(RegExp(r'\n+$'), '');
    if (line.startsWith('> ')) {
      return _RenderedPaneLine(
        text: preserveSelectionPrefix ? line : line.substring(2),
        selected: true,
      );
    }
    return _RenderedPaneLine(text: line, selected: false);
  }
}

enum _DraftScopeTableMode { review, model, fallback }

class _DraftScopeTableRow {
  const _DraftScopeTableRow({
    required this.indicator,
    required this.label,
    required this.selected,
  });

  final String indicator;
  final String label;
  final bool selected;
}

class _DraftScopeTableData {
  const _DraftScopeTableData({
    required this.mode,
    required this.rows,
    required this.indicatorTitle,
    required this.valueTitle,
  });

  final _DraftScopeTableMode mode;
  final List<_DraftScopeTableRow> rows;
  final String indicatorTitle;
  final String valueTitle;

  factory _DraftScopeTableData.fromPane(
    subject.SubjectPaneView pane, {
    required String titleHint,
  }) {
    final reviewItems = pane.items
        .where((item) => item.entryKind == 'draft_review_item')
        .toList(growable: false);
    final modelItems = pane.items
        .where((item) => item.entryKind == 'construct_candidate')
        .toList(growable: false);
    final reviewRows = reviewItems
        .map(
          (item) => _DraftScopeTableRow(
            indicator: item.checkState == 'checked' ? 'x' : ' ',
            label:
                '${'  ' * item.depth}${item.label}'
                '${item.semanticKind.isNotEmpty || item.renderKind.isNotEmpty ? ' (${_displayToken(item.semanticKind)} -> ${_displayToken(item.renderKind)})' : ''}',
            selected: item.selected,
          ),
        )
        .toList(growable: false);
    final modelRows = modelItems
        .map(
          (item) => _DraftScopeTableRow(
            indicator: switch (item.status) {
              'candidate' => 'c',
              'accepted' => 'a',
              'rejected' => 'r',
              _ => '?',
            },
            label:
                '${item.label}${item.sortKind.isNotEmpty ? ' (${_displayToken(item.sortKind)})' : ''}',
            selected: item.selected,
          ),
        )
        .toList(growable: false);
    if (reviewRows.isNotEmpty) {
      return _DraftScopeTableData(
        mode: _DraftScopeTableMode.review,
        rows: reviewRows,
        indicatorTitle: 'X',
        valueTitle: 'Draft Item',
      );
    }
    if (modelRows.isNotEmpty) {
      return _DraftScopeTableData(
        mode: _DraftScopeTableMode.model,
        rows: modelRows,
        indicatorTitle: 'S',
        valueTitle: titleHint.contains('Case Object')
            ? 'Case Object'
            : 'Draft Item',
      );
    }
    return _DraftScopeTableData(
      mode: _DraftScopeTableMode.fallback,
      rows: const [],
      indicatorTitle: '',
      valueTitle: '',
    );
  }
}

class _SelectableInventoryRow {
  const _SelectableInventoryRow({
    required this.prefix,
    required this.label,
    required this.selected,
  });

  final String prefix;
  final String label;
  final bool selected;
}

class _ItemizeInventoryData {
  const _ItemizeInventoryData({
    required this.preamble,
    required this.rows,
    required this.trailing,
  });

  final List<String> preamble;
  final List<_SelectableInventoryRow> rows;
  final List<String> trailing;

  bool get hasInventoryRows => rows.isNotEmpty;

  factory _ItemizeInventoryData.fromPane(subject.SubjectPaneView pane) {
    final rows = pane.items
        .where((item) => item.entryKind == 'itemized_item')
        .map((item) {
          final status = switch (item.status) {
            'candidate' => 'c',
            'promoted' => 'p',
            'rejected' => 'r',
            'merged' => 'm',
            'split' => 's',
            _ => '?',
          };
          final decisionRole = _paneItemAttribute(item, 'decision_role');
          final prefixParts = <String>[
            if (item.selected) '>',
            if (item.held) '[h]',
            '[$status]',
          ];
          return _SelectableInventoryRow(
            prefix: prefixParts.join(' '),
            label: decisionRole.isNotEmpty
                ? '$decisionRole - ${item.label}'
                : '${item.label} (${item.semanticKind})',
            selected: item.selected,
          );
        })
        .toList(growable: false);

    return _ItemizeInventoryData(
      preamble: const [],
      rows: rows,
      trailing: const [],
    );
  }
}

String _displayToken(String value) {
  return value
      .split('_')
      .where((part) => part.isNotEmpty)
      .map((part) => '${part[0].toUpperCase()}${part.substring(1)}')
      .join(' ');
}

String _paneItemAttribute(subject.SubjectPaneItemView item, String key) {
  for (final attribute in item.attributes) {
    if (attribute.label == key) {
      return attribute.value;
    }
  }
  return '';
}

class _TerminalFrame extends StatelessWidget {
  const _TerminalFrame({required this.title, required this.child});

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.transparent,
        border: Border.all(color: _terminalBorder),
      ),
      padding: const EdgeInsets.all(15),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Text(
                title,
                style: const TextStyle(
                  color: _terminalSection,
                  fontFamily: 'monospace',
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          child,
        ],
      ),
    );
  }
}

class _TerminalSectionTitle extends StatelessWidget {
  const _TerminalSectionTitle(this.text);

  final String text;

  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style: const TextStyle(
        color: _terminalText,
        fontFamily: 'monospace',
        fontSize: 14,
        fontWeight: FontWeight.w700,
      ),
    );
  }
}

class _BorderlessTerminalSection extends StatelessWidget {
  const _BorderlessTerminalSection({
    required this.title,
    required this.child,
    this.trailing,
  });

  final String title;
  final Widget child;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Text(
                title,
                style: const TextStyle(
                  color: _terminalSection,
                  fontFamily: 'monospace',
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                ),
              ),
              if (trailing != null) ...[const Spacer(), trailing!],
            ],
          ),
          const SizedBox(height: 12),
          child,
        ],
      ),
    );
  }
}

class _CurrentStepBlock {
  _CurrentStepBlock({
    required this.lastActionText,
    required this.title,
    required this.status,
    required this.why,
    required this.detailLines,
    required this.actions,
  });

  final String lastActionText;
  final String title;
  final String status;
  final String why;
  final List<String> detailLines;
  final List<subject.SubjectGateAction> actions;

  bool get hasPrimaryStepContent =>
      title.isNotEmpty ||
      status.isNotEmpty ||
      why.isNotEmpty ||
      detailLines.any((line) => line.trim().isNotEmpty);

  factory _CurrentStepBlock.fromPhaseView(
    subject.SubjectPhaseView phaseView, {
    required String lastActionText,
  }) {
    final step = phaseView.currentStep;
    final normalizedTitle = step.title.trim();
    return _CurrentStepBlock(
      lastActionText: lastActionText.trim(),
      title: normalizedTitle.toLowerCase() == 'current step'
          ? ''
          : normalizedTitle,
      status: step.status,
      why: step.why,
      detailLines: step.detailLines,
      actions: step.actions,
    );
  }
}

(String, String) _subjectActionLabelParts(String label) {
  final normalizedLabel = label.trim().replaceAll(RegExp(r'\s+'), ' ');
  if (normalizedLabel.isEmpty || !normalizedLabel.contains(':')) {
    return ('', normalizedLabel);
  }
  final parts = normalizedLabel.split(':');
  if (parts.length < 2) {
    return ('', normalizedLabel);
  }
  final prefix = parts.first.trim();
  final suffix = parts.sublist(1).join(':').trim();
  if (prefix.isEmpty || suffix.isEmpty) {
    return ('', normalizedLabel);
  }
  return (prefix, suffix);
}

String _subjectScenarioIdentity(subject.SubjectScenarioSummary scenario) {
  return scenario.key.isNotEmpty ? scenario.key : scenario.subjectId;
}

String _subjectScenarioLabel(subject.SubjectScenarioSummary scenario) {
  if (scenario.title.isNotEmpty) {
    return scenario.title;
  }
  final identity = _subjectScenarioIdentity(scenario);
  return identity.isEmpty ? 'Unnamed Subject' : identity;
}

const _terminalBorder = Color(0xFF0E6B71);
const _terminalAccent = Color(0xFF2D6F74);
const _terminalSection = Color(0xFF2E8F95);
const _terminalText = Color(0xFFE8E8E8);
const _terminalTextMuted = Color(0xFFB0B0B0);
const double _gateStatusRowMinHeight = 176.0;
const double _gateStatusRowMaxHeight = 224.0;
const double _gateStatusStackBreakpoint = 980.0;
const double _gateStatusStackHeight = 120.0;
