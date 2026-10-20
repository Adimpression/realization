import 'dart:async';
import 'dart:convert';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:grpc/service_api.dart' as grpc_service;
import 'package:url_launcher/url_launcher.dart';

import 'src/generated/workstation/grpc/definitions/subject_workflow.pb.dart'
    as subject;
import 'src/generated/workstation/grpc/definitions/subject_workflow.pbgrpc.dart'
    as subject_grpc;
import 'src/generated/workstation/grpc/definitions/workstation_assets.pb.dart'
    as assets;
import 'src/generated/workstation/grpc/definitions/workstation_assets.pbgrpc.dart'
    as assets_grpc;
import 'src/generated/workstation/grpc/definitions/workstation_bootstrap.pb.dart'
    as bootstrap;
import 'src/generated/workstation/grpc/definitions/workstation_bootstrap.pbgrpc.dart'
    as bootstrap_grpc;
import 'src/generated/workstation/grpc/definitions/workstation_shell.pb.dart'
    as shell;
import 'src/generated/workstation/grpc/definitions/workstation_shell.pbgrpc.dart'
    as shell_grpc;
import 'src/grpc_channel_factory.dart';
import 'src/textual/chat_ui.dart';
import 'src/textual/layout.dart' as shell_spec;

const _stateSentinel = Object();
const _subjectPhaseTabs = <String>{
  'research',
  'itemize',
  'draft',
  'review',
  'publication',
};

const _flutterDisabledSubjectActionKeys = <String>{
  'open_release_packet',
  'release_open_folder',
};

bool _isFlutterDisabledSubjectAction(String actionKey) {
  return _flutterDisabledSubjectActionKeys.contains(actionKey.trim());
}

bool _isFlutterSupportedArtifact(assets.ArtifactRef artifact) {
  return artifact.mimeType != 'inode/directory';
}

const bool _disableArtifactAutoOpen = bool.fromEnvironment(
  'WORKSTATION_DISABLE_AUTO_OPEN_ARTIFACTS',
);

void main() {
  runApp(const ProviderScope(child: WorkstationApp()));
}

final workstationLayoutProvider =
    FutureProvider<shell_spec.WorkstationLayoutSpec>((ref) async {
      final payload = await rootBundle.loadString(
        'assets/workstation_layout.json',
      );
      return shell_spec.WorkstationLayoutSpec.fromJson(
        jsonDecode(payload) as Map<String, dynamic>,
      );
    });

final workstationControllerProvider =
    NotifierProvider<WorkstationController, WorkstationState>(
      WorkstationController.new,
    );

final workstationRouterProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/',
    routes: <RouteBase>[
      GoRoute(path: '/', builder: (context, state) => const BootstrapScreen()),
      GoRoute(
        path: '/workstation/:tabKey',
        builder: (context, state) =>
            WorkstationScreen(tabKey: state.pathParameters['tabKey'] ?? 'chat'),
      ),
    ],
  );
});

class WorkstationApp extends ConsumerWidget {
  const WorkstationApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(workstationRouterProvider);
    final theme = ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      colorScheme: ColorScheme.fromSeed(
        seedColor: const Color(0xFF3AC7C3),
        brightness: Brightness.dark,
        surface: const Color(0xFF081114),
        primary: const Color(0xFF66E7E2),
        secondary: const Color(0xFF8AE4FF),
      ),
      scaffoldBackgroundColor: const Color(0xFF020709),
      cardTheme: const CardThemeData(
        color: Color(0xFF081114),
        elevation: 0,
        margin: EdgeInsets.zero,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: Color(0xFF020709),
        foregroundColor: Color(0xFFE7FFFF),
      ),
      snackBarTheme: const SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
      ),
    );
    return MaterialApp.router(
      debugShowCheckedModeBanner: false,
      title: 'Workstation',
      theme: theme,
      routerConfig: router,
    );
  }
}

class EndpointConfig {
  const EndpointConfig({
    required this.grpcHost,
    required this.grpcPort,
    required this.grpcWebUrl,
  });

  final String grpcHost;
  final int grpcPort;
  final String grpcWebUrl;

  grpc_service.ClientChannel buildChannel() {
    return createWorkstationGrpcChannel(
      grpcHost: grpcHost,
      grpcPort: grpcPort,
      grpcWebUrl: grpcWebUrl,
    );
  }

  EndpointConfig copyWith({
    String? grpcHost,
    int? grpcPort,
    String? grpcWebUrl,
  }) {
    return EndpointConfig(
      grpcHost: grpcHost ?? this.grpcHost,
      grpcPort: grpcPort ?? this.grpcPort,
      grpcWebUrl: grpcWebUrl ?? this.grpcWebUrl,
    );
  }
}

class WorkstationState {
  const WorkstationState({
    required this.endpoint,
    this.loadingRoots = false,
    this.openingRoot = false,
    this.chatBusy = false,
    this.subjectBusy = false,
    this.markdownIngressBusy = false,
    this.roots = const <bootstrap.WorkstationRootDescriptor>[],
    this.selectedRootPath = '',
    this.clientSessionId = '',
    this.chatSnapshot,
    this.activityView,
    this.permissionsView,
    this.skillsView,
    this.preparedPromptTarget,
    this.subjects = const <subject.SubjectScenarioSummary>[],
    this.selectedScenarioKey = '',
    this.currentTabKey = 'chat',
    this.subjectSnapshot,
    this.stagedMarkdownPath = '',
    this.markdownStatusText = '',
    this.latestArtifacts = const <assets.ArtifactRef>[],
    this.statusText = '',
    this.errorText,
  });

  final EndpointConfig endpoint;
  final bool loadingRoots;
  final bool openingRoot;
  final bool chatBusy;
  final bool subjectBusy;
  final bool markdownIngressBusy;
  final List<bootstrap.WorkstationRootDescriptor> roots;
  final String selectedRootPath;
  final String clientSessionId;
  final shell.ChatSnapshotResponse? chatSnapshot;
  final shell.ShellTextView? activityView;
  final shell.ShellTextView? permissionsView;
  final shell.ShellTextView? skillsView;
  final shell.PrepareChatPromptTargetResponse? preparedPromptTarget;
  final List<subject.SubjectScenarioSummary> subjects;
  final String selectedScenarioKey;
  final String currentTabKey;
  final subject.SubjectWorkflowSnapshotView? subjectSnapshot;
  final String stagedMarkdownPath;
  final String markdownStatusText;
  final List<assets.ArtifactRef> latestArtifacts;
  final String statusText;
  final String? errorText;

  bool get connected =>
      selectedRootPath.isNotEmpty && clientSessionId.isNotEmpty;
  bool get hasSelectedSubject => selectedScenarioKey.isNotEmpty;

  WorkstationState copyWith({
    EndpointConfig? endpoint,
    bool? loadingRoots,
    bool? openingRoot,
    bool? chatBusy,
    bool? subjectBusy,
    bool? markdownIngressBusy,
    List<bootstrap.WorkstationRootDescriptor>? roots,
    String? selectedRootPath,
    String? clientSessionId,
    Object? chatSnapshot = _stateSentinel,
    Object? activityView = _stateSentinel,
    Object? permissionsView = _stateSentinel,
    Object? skillsView = _stateSentinel,
    Object? preparedPromptTarget = _stateSentinel,
    List<subject.SubjectScenarioSummary>? subjects,
    String? selectedScenarioKey,
    String? currentTabKey,
    Object? subjectSnapshot = _stateSentinel,
    String? stagedMarkdownPath,
    String? markdownStatusText,
    List<assets.ArtifactRef>? latestArtifacts,
    String? statusText,
    Object? errorText = _stateSentinel,
  }) {
    return WorkstationState(
      endpoint: endpoint ?? this.endpoint,
      loadingRoots: loadingRoots ?? this.loadingRoots,
      openingRoot: openingRoot ?? this.openingRoot,
      chatBusy: chatBusy ?? this.chatBusy,
      subjectBusy: subjectBusy ?? this.subjectBusy,
      markdownIngressBusy: markdownIngressBusy ?? this.markdownIngressBusy,
      roots: roots ?? this.roots,
      selectedRootPath: selectedRootPath ?? this.selectedRootPath,
      clientSessionId: clientSessionId ?? this.clientSessionId,
      chatSnapshot: identical(chatSnapshot, _stateSentinel)
          ? this.chatSnapshot
          : chatSnapshot as shell.ChatSnapshotResponse?,
      activityView: identical(activityView, _stateSentinel)
          ? this.activityView
          : activityView as shell.ShellTextView?,
      permissionsView: identical(permissionsView, _stateSentinel)
          ? this.permissionsView
          : permissionsView as shell.ShellTextView?,
      skillsView: identical(skillsView, _stateSentinel)
          ? this.skillsView
          : skillsView as shell.ShellTextView?,
      preparedPromptTarget: identical(preparedPromptTarget, _stateSentinel)
          ? this.preparedPromptTarget
          : preparedPromptTarget as shell.PrepareChatPromptTargetResponse?,
      subjects: subjects ?? this.subjects,
      selectedScenarioKey: selectedScenarioKey ?? this.selectedScenarioKey,
      currentTabKey: currentTabKey ?? this.currentTabKey,
      subjectSnapshot: identical(subjectSnapshot, _stateSentinel)
          ? this.subjectSnapshot
          : subjectSnapshot as subject.SubjectWorkflowSnapshotView?,
      stagedMarkdownPath: stagedMarkdownPath ?? this.stagedMarkdownPath,
      markdownStatusText: markdownStatusText ?? this.markdownStatusText,
      latestArtifacts: latestArtifacts ?? this.latestArtifacts,
      statusText: statusText ?? this.statusText,
      errorText: identical(errorText, _stateSentinel)
          ? this.errorText
          : errorText as String?,
    );
  }
}

class WorkstationController extends Notifier<WorkstationState> {
  grpc_service.ClientChannel? _channel;
  bootstrap_grpc.WorkstationBootstrapServiceClient? _bootstrapClient;
  assets_grpc.WorkstationAssetServiceClient? _assetClient;
  shell_grpc.WorkstationShellServiceClient? _shellClient;
  subject_grpc.SubjectWorkflowServiceClient? _subjectClient;
  StreamSubscription<shell.WorkstationShellWatchEvent>? _shellWatchSubscription;
  StreamSubscription<subject.SubjectWorkflowSnapshotUpdate>?
  _subjectWatchSubscription;
  int _shellWatchGeneration = 0;
  int _subjectWatchGeneration = 0;

  @override
  WorkstationState build() {
    ref.onDispose(_disposeTransport);
    return WorkstationState(
      endpoint: EndpointConfig(
        grpcHost: const String.fromEnvironment(
          'WORKSTATION_GRPC_HOST',
          defaultValue: '127.0.0.1',
        ),
        grpcPort: const int.fromEnvironment(
          'WORKSTATION_GRPC_PORT',
          defaultValue: 50051,
        ),
        grpcWebUrl: const String.fromEnvironment(
          'WORKSTATION_GRPCWEB_URL',
          defaultValue: 'http://127.0.0.1:8080',
        ),
      ),
    );
  }

  Future<void> loadRoots(EndpointConfig endpoint) async {
    state = state.copyWith(
      endpoint: endpoint,
      loadingRoots: true,
      errorText: null,
      statusText: 'Connecting to workstation host...',
      roots: const <bootstrap.WorkstationRootDescriptor>[],
    );
    await _disposeTransport();
    try {
      _channel = endpoint.buildChannel();
      _bootstrapClient = bootstrap_grpc.WorkstationBootstrapServiceClient(
        _channel!,
      );
      _assetClient = assets_grpc.WorkstationAssetServiceClient(_channel!);
      _shellClient = shell_grpc.WorkstationShellServiceClient(_channel!);
      _subjectClient = subject_grpc.SubjectWorkflowServiceClient(_channel!);
      final response = await _bootstrapClient!.listWorkstationRoots(
        bootstrap.ListWorkstationRootsRequest(),
      );
      final roots = response.roots.toList(growable: false);
      final defaultRoot = roots
          .cast<bootstrap.WorkstationRootDescriptor?>()
          .firstWhere(
            (root) => root?.isDefault ?? false,
            orElse: () {
              if (roots.isEmpty) {
                return null;
              }
              return roots.first;
            },
          );
      state = state.copyWith(
        loadingRoots: false,
        roots: roots,
        selectedRootPath: defaultRoot?.rootPath ?? '',
        statusText: roots.isEmpty
            ? 'Connected, but the host is not advertising any workstation roots.'
            : 'Discovered ${roots.length} workstation root${roots.length == 1 ? '' : 's'}.',
      );
    } catch (error) {
      await _disposeTransport();
      state = state.copyWith(
        loadingRoots: false,
        errorText: '$error',
        statusText: 'Failed to connect to the workstation host.',
      );
    }
  }

  void selectRoot(String rootPath) {
    state = state.copyWith(selectedRootPath: rootPath);
  }

  Future<bool> openSelectedRoot() async {
    final shellClient = _shellClient;
    final selectedRootPath = state.selectedRootPath;
    if (shellClient == null || selectedRootPath.isEmpty) {
      return false;
    }
    state = state.copyWith(
      openingRoot: true,
      errorText: null,
      statusText: 'Opening workstation root...',
    );
    try {
      final sessionId =
          'flutter-shell-${DateTime.now().millisecondsSinceEpoch}';
      final response = await shellClient.openClientSession(
        shell.ClientSessionRequest()
          ..rootPath = selectedRootPath
          ..clientSessionId = sessionId,
      );
      state = state.copyWith(
        clientSessionId: response.clientSessionId,
        statusText: 'Loading workstation projections...',
      );
      final shellRefreshIssues = await _refreshShellViews();
      await showTab(state.currentTabKey);
      _startShellWatch();
      state = state.copyWith(
        openingRoot: false,
        statusText: shellRefreshIssues.isEmpty
            ? 'Connected to ${_basename(selectedRootPath)}.'
            : 'Connected to ${_basename(selectedRootPath)}, but some panels need a refresh.',
      );
      return true;
    } catch (error) {
      state = state.copyWith(
        openingRoot: false,
        errorText: '$error',
        statusText: 'Failed to open the workstation root.',
      );
      return false;
    }
  }

  Future<void> showTab(String tabKey) async {
    final normalized = _normalizeTabKey(tabKey);
    state = state.copyWith(currentTabKey: normalized, errorText: null);
    final phase = _subjectPhaseForTab(normalized);
    if (phase == null) {
      await _subjectWatchSubscription?.cancel();
      _subjectWatchSubscription = null;
      return;
    }
    await _refreshSubjectList();
    if (state.selectedScenarioKey.isNotEmpty) {
      await _refreshSubjectSnapshot(phase);
      _startSubjectWatch(phase);
      return;
    }
    await _subjectWatchSubscription?.cancel();
    _subjectWatchSubscription = null;
    state = state.copyWith(subjectSnapshot: null);
  }

  Future<void> selectSubject(String scenarioKey) async {
    state = state.copyWith(
      selectedScenarioKey: scenarioKey,
      latestArtifacts: const <assets.ArtifactRef>[],
    );
    final phase = _subjectPhaseForTab(state.currentTabKey);
    if (phase != null) {
      await _refreshSubjectSnapshot(phase);
      _startSubjectWatch(phase);
    }
  }

  Future<void> preparePrompt(String promptText) async {
    final shellClient = _shellClient;
    if (shellClient == null || !state.connected) {
      return;
    }
    if (promptText.trim().isEmpty) {
      state = state.copyWith(preparedPromptTarget: null);
      return;
    }
    try {
      final response = await shellClient.prepareChatPromptTarget(
        shell.PrepareChatPromptTargetRequest()
          ..rootPath = state.selectedRootPath
          ..clientSessionId = state.clientSessionId
          ..promptText = promptText,
      );
      state = state.copyWith(preparedPromptTarget: response);
    } catch (error) {
      state = state.copyWith(errorText: '$error');
    }
  }

  Future<void> submitPrompt(String promptText) async {
    final shellClient = _shellClient;
    if (shellClient == null || !state.connected || promptText.trim().isEmpty) {
      return;
    }
    state = state.copyWith(
      chatBusy: true,
      errorText: null,
      statusText: 'Sending chat prompt...',
    );
    try {
      final response = await shellClient.submitChatInput(
        shell.SubmitChatInputRequest()
          ..rootPath = state.selectedRootPath
          ..clientSessionId = state.clientSessionId
          ..promptText = promptText
          ..maxToolRounds = 8,
      );
      state = state.copyWith(
        chatBusy: false,
        statusText: response.statusText.isEmpty
            ? 'Prompt completed.'
            : response.statusText,
        preparedPromptTarget: null,
      );
      await _refreshShellViews();
    } catch (error) {
      state = state.copyWith(
        chatBusy: false,
        errorText: '$error',
        statusText: 'Prompt execution failed.',
      );
    }
  }

  Future<String?> stageMarkdownUpload(
    String filename,
    Uint8List content,
  ) async {
    final assetClient = _assetClient;
    if (assetClient == null || !state.connected) {
      return null;
    }
    state = state.copyWith(
      subjectBusy: true,
      markdownIngressBusy: false,
      errorText: null,
      statusText: 'Uploading markdown into the workstation...',
    );
    try {
      final response = await assetClient.stageMarkdownUpload(
        assets.StageMarkdownUploadRequest()
          ..rootPath = state.selectedRootPath
          ..clientSessionId = state.clientSessionId
          ..filename = filename
          ..content = content,
      );
      state = state.copyWith(
        subjectBusy: true,
        markdownIngressBusy: true,
        stagedMarkdownPath: response.stagedPath,
        markdownStatusText: 'Markdown upload staged.',
        statusText: 'Markdown upload staged.',
      );
      final phase = _subjectPhaseForTab(state.currentTabKey);
      if (phase != null) {
        await _refreshSubjectList();
        if (state.selectedScenarioKey.isNotEmpty) {
          await _refreshSubjectSnapshot(phase);
        }
      }
      final nextTab = await applyAction('use_markdown_ingress');
      if (nextTab == null && state.errorText == null) {
        state = state.copyWith(
          subjectBusy: false,
          markdownIngressBusy: false,
          errorText:
              'The Gather workflow did not expose a selectable subject scenario.',
          statusText:
              'Markdown upload staged, but workflow intake did not start.',
        );
      }
      return nextTab;
    } catch (error) {
      state = state.copyWith(
        subjectBusy: false,
        markdownIngressBusy: false,
        errorText: '$error',
        statusText: 'Markdown upload failed.',
      );
      return null;
    }
  }

  Future<String?> applyAction(
    String actionKey, {
    String assistantMessageText = '',
  }) async {
    final subjectClient = _subjectClient;
    final phase = _subjectPhaseForTab(state.currentTabKey);
    if (subjectClient == null || !state.connected || phase == null) {
      return null;
    }
    if (state.selectedScenarioKey.isEmpty) {
      await _refreshSubjectList();
    }
    if (state.selectedScenarioKey.isEmpty) {
      state = state.copyWith(
        errorText: 'No subject workflow scenario is available for this action.',
        statusText: 'Workflow action could not start.',
      );
      return null;
    }
    state = state.copyWith(
      subjectBusy: true,
      markdownIngressBusy: actionKey == 'use_markdown_ingress'
          ? state.stagedMarkdownPath.isNotEmpty
          : state.markdownIngressBusy,
      errorText: null,
      statusText: 'Applying workflow action...',
    );
    try {
      final response = await subjectClient.applySubjectAction(
        subject.ApplySubjectActionRequest()
          ..rootPath = state.selectedRootPath
          ..subjectId = state.selectedScenarioKey
          ..phase = phase
          ..actionKey = actionKey
          ..assistantMessageText = assistantMessageText
          ..clientSessionId = state.clientSessionId
          ..projectionContext = _projectionContext(),
      );
      var openArtifacts = response.result.openArtifacts.toList(growable: false);
      if (openArtifacts.isEmpty && response.result.openPaths.isNotEmpty) {
        openArtifacts = await _resolveArtifacts(response.result.openPaths);
      }
      final latestArtifacts = openArtifacts
          .where(_isFlutterSupportedArtifact)
          .toList(growable: false);
      final recommendedTab = _nextTabFromActionResult(
        response.result,
        response.view,
      );
      final actionStatusText = switch (actionKey) {
        'use_markdown_ingress' || 'use_url_ingress' =>
          response.result.timelineText.isEmpty
              ? response.result.statusText
              : response.result.timelineText,
        _ => response.result.statusText,
      };
      state = state.copyWith(
        subjectBusy: false,
        markdownIngressBusy: false,
        stagedMarkdownPath: actionKey == 'use_markdown_ingress'
            ? ''
            : state.stagedMarkdownPath,
        markdownStatusText: actionKey == 'use_markdown_ingress'
            ? ''
            : state.markdownStatusText,
        latestArtifacts: latestArtifacts,
        statusText: actionStatusText.isEmpty
            ? 'Action completed.'
            : actionStatusText,
      );
      if (!_disableArtifactAutoOpen && latestArtifacts.isNotEmpty) {
        await _openReturnedArtifacts(latestArtifacts);
      }
      if (response.result.reloadSubjects ||
          response.result.preferredSubjectKey.isNotEmpty) {
        await _refreshSubjectList(
          preferredScenarioKey: response.result.preferredSubjectKey,
        );
      }
      final nextPhase = _subjectPhaseForTab(recommendedTab);
      if (nextPhase != null) {
        await _refreshSubjectSnapshot(
          nextPhase,
          preferredScenarioKey: response.result.preferredSubjectKey,
        );
        _startSubjectWatch(nextPhase);
      }
      return recommendedTab;
    } catch (error) {
      state = state.copyWith(
        subjectBusy: false,
        markdownIngressBusy: false,
        errorText: '$error',
        statusText: 'Workflow action failed.',
      );
      return null;
    }
  }

  Future<List<assets.ArtifactRef>> _resolveArtifacts(
    Iterable<String> serverPaths,
  ) async {
    final assetClient = _assetClient;
    if (assetClient == null || !state.connected) {
      return const <assets.ArtifactRef>[];
    }
    final normalizedPaths = serverPaths
        .map((item) => item.trim())
        .where((item) => item.isNotEmpty)
        .toList(growable: false);
    if (normalizedPaths.isEmpty) {
      return const <assets.ArtifactRef>[];
    }
    try {
      final response = await assetClient.resolveArtifacts(
        assets.ResolveArtifactsRequest()
          ..rootPath = state.selectedRootPath
          ..clientSessionId = state.clientSessionId
          ..serverPaths.addAll(normalizedPaths),
      );
      return response.artifacts.toList(growable: false);
    } catch (_) {
      return const <assets.ArtifactRef>[];
    }
  }

  Future<void> _openReturnedArtifacts(
    List<assets.ArtifactRef> artifacts,
  ) async {
    for (final artifact in artifacts) {
      if (!_isFlutterSupportedArtifact(artifact)) {
        continue;
      }
      try {
        await openArtifact(artifact);
      } catch (_) {
        // Keep the artifact visible in the UI even if the host cannot launch it.
      }
    }
  }

  Future<void> applyInteraction(
    String interactionKey, {
    int delta = 0,
    String? targetId,
    bool previewOnly = false,
  }) async {
    final subjectClient = _subjectClient;
    final phase = _subjectPhaseForTab(state.currentTabKey);
    if (subjectClient == null || !state.connected || phase == null) {
      return;
    }
    if (state.selectedScenarioKey.isEmpty) {
      await _refreshSubjectList();
    }
    if (state.selectedScenarioKey.isEmpty) {
      state = state.copyWith(
        errorText:
            'No subject workflow scenario is available for this interaction.',
        statusText: 'Workflow interaction could not start.',
      );
      return;
    }
    state = state.copyWith(
      subjectBusy: true,
      errorText: null,
      statusText: 'Applying workflow interaction...',
    );
    try {
      final response = await subjectClient.applySubjectInteraction(
        subject.ApplySubjectInteractionRequest()
          ..rootPath = state.selectedRootPath
          ..subjectId = state.selectedScenarioKey
          ..phase = phase
          ..interactionKey = interactionKey
          ..delta = delta
          ..targetId = targetId ?? ''
          ..previewOnly = previewOnly
          ..clientSessionId = state.clientSessionId
          ..projectionContext = _projectionContext(),
      );
      state = state.copyWith(
        subjectBusy: false,
        subjectSnapshot: response.snapshot,
        statusText: 'Interaction applied.',
      );
    } catch (error) {
      state = state.copyWith(
        subjectBusy: false,
        errorText: '$error',
        statusText: 'Workflow interaction failed.',
      );
    }
  }

  Future<void> openArtifact(assets.ArtifactRef artifact) async {
    if (!_isFlutterSupportedArtifact(artifact)) {
      return;
    }
    final localUri = artifact.canOpenLocally && artifact.serverPath.isNotEmpty
        ? Uri.file(artifact.serverPath)
        : null;
    if (!kIsWeb && localUri != null) {
      final opened = await launchUrl(
        localUri,
        mode: LaunchMode.externalApplication,
      );
      if (opened) {
        return;
      }
    }
    if (artifact.downloadUrl.isNotEmpty) {
      await launchUrl(
        Uri.parse(artifact.downloadUrl),
        mode: LaunchMode.externalApplication,
      );
    }
  }

  Future<List<String>> _refreshShellViews() async {
    final shellClient = _shellClient;
    if (shellClient == null || !state.connected) {
      return const <String>[];
    }
    final rootPath = state.selectedRootPath;
    final sessionId = state.clientSessionId;
    final issues = <String>[];
    shell.ChatSnapshotResponse? chatSnapshot = state.chatSnapshot;
    shell.ShellTextView? activityView = state.activityView;
    shell.ShellTextView? permissionsView = state.permissionsView;
    shell.ShellTextView? skillsView = state.skillsView;

    Future<void> loadChatSnapshot() async {
      chatSnapshot = await shellClient.getChatSnapshot(
        shell.ChatSnapshotRequest()
          ..rootPath = rootPath
          ..clientSessionId = sessionId
          ..limit = 120,
      );
    }

    Future<void> loadActivityView() async {
      activityView = await shellClient.getActivityView(
        shell.ActivityViewRequest()
          ..rootPath = rootPath
          ..clientSessionId = sessionId
          ..limit = 120,
      );
    }

    Future<void> loadPermissionsView() async {
      permissionsView = await shellClient.getPermissionsView(
        shell.PermissionsViewRequest()
          ..rootPath = rootPath
          ..clientSessionId = sessionId,
      );
    }

    Future<void> loadSkillsView() async {
      skillsView = await shellClient.getSkillsView(
        shell.SkillsViewRequest()
          ..rootPath = rootPath
          ..clientSessionId = sessionId
          ..query = '',
      );
    }

    for (final request in <({String label, Future<void> Function() invoke})>[
      (label: 'chat transcript', invoke: loadChatSnapshot),
      (label: 'activity feed', invoke: loadActivityView),
      (label: 'permissions view', invoke: loadPermissionsView),
      (label: 'skills view', invoke: loadSkillsView),
    ]) {
      try {
        await request.invoke();
      } catch (error) {
        issues.add('${request.label}: $error');
      }
    }

    state = state.copyWith(
      chatSnapshot: chatSnapshot,
      activityView: activityView,
      permissionsView: permissionsView,
      skillsView: skillsView,
    );
    if (issues.isNotEmpty) {
      debugPrint('Shell projection refresh issues:\n${issues.join('\n')}');
    }
    return issues;
  }

  Future<void> _refreshSubjectList({String preferredScenarioKey = ''}) async {
    final subjectClient = _subjectClient;
    if (subjectClient == null || !state.connected) {
      return;
    }
    final response = await subjectClient.listSubjects(
      subject.ListSubjectsRequest()..rootPath = state.selectedRootPath,
    );
    final subjects = response.subjects.toList(growable: false);
    final preferredKey = preferredScenarioKey.isNotEmpty
        ? preferredScenarioKey
        : state.selectedScenarioKey;
    final selectedScenarioKey =
        subjects.any((item) => _scenarioIdentity(item) == preferredKey)
        ? preferredKey
        : (subjects.isEmpty ? '' : _scenarioIdentity(subjects.first));
    state = state.copyWith(
      subjects: subjects,
      selectedScenarioKey: selectedScenarioKey,
    );
  }

  Future<void> _refreshSubjectSnapshot(
    String phase, {
    String preferredScenarioKey = '',
  }) async {
    final subjectClient = _subjectClient;
    final targetScenarioKey = preferredScenarioKey.isNotEmpty
        ? preferredScenarioKey
        : state.selectedScenarioKey;
    if (subjectClient == null ||
        !state.connected ||
        targetScenarioKey.isEmpty) {
      return;
    }
    state = state.copyWith(subjectBusy: true);
    try {
      final response = await subjectClient.getSubjectWorkflowSnapshot(
        subject.GetSubjectWorkflowSnapshotRequest()
          ..rootPath = state.selectedRootPath
          ..subjectId = targetScenarioKey
          ..phase = phase
          ..clientSessionId = state.clientSessionId
          ..projectionContext = _projectionContext(),
      );
      state = state.copyWith(
        subjectBusy: false,
        selectedScenarioKey: targetScenarioKey,
        subjectSnapshot: response.snapshot,
      );
    } catch (error) {
      state = state.copyWith(subjectBusy: false, errorText: '$error');
    }
  }

  subject.SubjectPhaseProjectionContext _projectionContext() {
    return subject.SubjectPhaseProjectionContext()
      ..canCaptureAssistant = true
      ..markdownSelectedPath = state.stagedMarkdownPath
      ..markdownStatusText = state.markdownStatusText
      ..markdownBusy = state.markdownIngressBusy;
  }

  void _startShellWatch() {
    final shellClient = _shellClient;
    if (shellClient == null || !state.connected) {
      return;
    }
    _shellWatchGeneration += 1;
    final watchGeneration = _shellWatchGeneration;
    _shellWatchSubscription?.cancel();
    _shellWatchSubscription = shellClient
        .watchWorkstationShell(
          shell.WatchWorkstationShellRequest()
            ..rootPath = state.selectedRootPath
            ..clientSessionId = state.clientSessionId
            ..lastSeenVersion = state.chatSnapshot?.snapshotVersion ?? '',
        )
        .listen(
          (event) {
            if (watchGeneration != _shellWatchGeneration || !state.connected) {
              return;
            }
            switch (event.whichPayload()) {
              case shell.WorkstationShellWatchEvent_Payload.chatSnapshot:
                state = state.copyWith(chatSnapshot: event.chatSnapshot);
                break;
              case shell.WorkstationShellWatchEvent_Payload.activityView:
                state = state.copyWith(activityView: event.activityView);
                break;
              case shell.WorkstationShellWatchEvent_Payload.permissionsView:
                state = state.copyWith(permissionsView: event.permissionsView);
                break;
              case shell.WorkstationShellWatchEvent_Payload.skillsView:
                state = state.copyWith(skillsView: event.skillsView);
                break;
              default:
                break;
            }
          },
          onError: (Object error) {
            if (watchGeneration != _shellWatchGeneration ||
                isIgnorableWorkstationWatchError(error)) {
              debugPrint('Ignoring shell watch error: $error');
              return;
            }
            state = state.copyWith(errorText: '$error');
          },
        );
  }

  void _startSubjectWatch(String phase) {
    final subjectClient = _subjectClient;
    final targetScenarioKey = state.selectedScenarioKey;
    if (subjectClient == null ||
        !state.connected ||
        targetScenarioKey.isEmpty) {
      return;
    }
    _subjectWatchGeneration += 1;
    final watchGeneration = _subjectWatchGeneration;
    _subjectWatchSubscription?.cancel();
    _subjectWatchSubscription = subjectClient
        .watchSubjectWorkflow(
          subject.WatchSubjectWorkflowRequest()
            ..rootPath = state.selectedRootPath
            ..subjectId = targetScenarioKey
            ..phase = phase
            ..clientSessionId = state.clientSessionId
            ..projectionContext = _projectionContext(),
        )
        .listen(
          (event) {
            if (watchGeneration != _subjectWatchGeneration ||
                !state.connected ||
                state.selectedScenarioKey != targetScenarioKey ||
                _subjectPhaseForTab(state.currentTabKey) != phase) {
              return;
            }
            state = state.copyWith(subjectSnapshot: event.snapshot);
          },
          onError: (Object error) {
            if (watchGeneration != _subjectWatchGeneration ||
                isIgnorableWorkstationWatchError(error)) {
              debugPrint('Ignoring subject watch error: $error');
              return;
            }
            state = state.copyWith(errorText: '$error');
          },
        );
  }

  Future<void> _disposeTransport() async {
    _shellWatchGeneration += 1;
    _subjectWatchGeneration += 1;
    await _shellWatchSubscription?.cancel();
    await _subjectWatchSubscription?.cancel();
    _shellWatchSubscription = null;
    _subjectWatchSubscription = null;
    await _channel?.shutdown();
    _channel = null;
    _bootstrapClient = null;
    _assetClient = null;
    _shellClient = null;
    _subjectClient = null;
  }
}

class BootstrapScreen extends ConsumerStatefulWidget {
  const BootstrapScreen({super.key});

  @override
  ConsumerState<BootstrapScreen> createState() => _BootstrapScreenState();
}

class _BootstrapScreenState extends ConsumerState<BootstrapScreen> {
  late final TextEditingController _hostController;
  late final TextEditingController _portController;
  late final TextEditingController _grpcWebUrlController;

  @override
  void initState() {
    super.initState();
    final endpoint = ref.read(workstationControllerProvider).endpoint;
    _hostController = TextEditingController(text: endpoint.grpcHost);
    _portController = TextEditingController(text: endpoint.grpcPort.toString());
    _grpcWebUrlController = TextEditingController(text: endpoint.grpcWebUrl);
  }

  @override
  void dispose() {
    _hostController.dispose();
    _portController.dispose();
    _grpcWebUrlController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(workstationControllerProvider);
    final controller = ref.read(workstationControllerProvider.notifier);
    return Scaffold(
      appBar: AppBar(title: const Text('Workstation Bootstrap')),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 840),
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: ListView(
                children: <Widget>[
                  _SurfaceCard(
                    title: 'Connect',
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          'Connect to the combined workstation gRPC host, discover served roots, and then open one root into the Material 3 shell.',
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                        const SizedBox(height: 20),
                        if (kIsWeb) ...<Widget>[
                          TextField(
                            controller: _grpcWebUrlController,
                            decoration: const InputDecoration(
                              labelText: 'gRPC-Web endpoint',
                              hintText: 'http://127.0.0.1:8080',
                            ),
                          ),
                        ] else ...<Widget>[
                          Row(
                            children: <Widget>[
                              Expanded(
                                child: TextField(
                                  controller: _hostController,
                                  decoration: const InputDecoration(
                                    labelText: 'gRPC host',
                                    hintText: '127.0.0.1',
                                  ),
                                ),
                              ),
                              const SizedBox(width: 16),
                              SizedBox(
                                width: 160,
                                child: TextField(
                                  controller: _portController,
                                  keyboardType: TextInputType.number,
                                  decoration: const InputDecoration(
                                    labelText: 'gRPC port',
                                    hintText: '50051',
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ],
                        const SizedBox(height: 20),
                        FilledButton.icon(
                          onPressed: state.loadingRoots
                              ? null
                              : () async {
                                  final endpoint = EndpointConfig(
                                    grpcHost: _hostController.text.trim(),
                                    grpcPort:
                                        int.tryParse(
                                          _portController.text.trim(),
                                        ) ??
                                        50051,
                                    grpcWebUrl: _grpcWebUrlController.text
                                        .trim(),
                                  );
                                  await controller.loadRoots(endpoint);
                                },
                          icon: state.loadingRoots
                              ? const SizedBox.square(
                                  dimension: 16,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                  ),
                                )
                              : const Icon(Icons.hub_outlined),
                          label: const Text('Load Served Roots'),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),
                  _SurfaceCard(
                    title: 'Advertised Roots',
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        if (state.roots.isEmpty)
                          const Text('No workstation roots discovered yet.')
                        else ...<Widget>[
                          DropdownButtonFormField<String>(
                            key: ValueKey<String>(
                              'root-selector:${state.selectedRootPath}:${state.roots.length}',
                            ),
                            initialValue: state.selectedRootPath.isEmpty
                                ? null
                                : state.selectedRootPath,
                            items: state.roots
                                .map(
                                  (root) => DropdownMenuItem<String>(
                                    value: root.rootPath,
                                    child: Text(
                                      '${root.label} (${root.workspaceName})',
                                    ),
                                  ),
                                )
                                .toList(growable: false),
                            onChanged: (value) {
                              if (value != null) {
                                controller.selectRoot(value);
                              }
                            },
                            decoration: const InputDecoration(
                              labelText: 'Workstation root',
                            ),
                          ),
                          const SizedBox(height: 16),
                          FilledButton.icon(
                            onPressed:
                                state.openingRoot ||
                                    state.selectedRootPath.isEmpty
                                ? null
                                : () async {
                                    final opened = await controller
                                        .openSelectedRoot();
                                    if (!mounted || !opened) {
                                      return;
                                    }
                                    if (context.mounted) {
                                      context.go(
                                        '/workstation/${_normalizeTabKey(ref.read(workstationControllerProvider).currentTabKey)}',
                                      );
                                    }
                                  },
                            icon: state.openingRoot
                                ? const SizedBox.square(
                                    dimension: 16,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                    ),
                                  )
                                : const Icon(Icons.launch),
                            label: const Text('Open Workstation'),
                          ),
                        ],
                      ],
                    ),
                  ),
                  if (state.statusText.isNotEmpty) ...<Widget>[
                    const SizedBox(height: 20),
                    _InfoBanner(
                      text: state.statusText,
                      errorText: state.errorText,
                    ),
                  ],
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class WorkstationScreen extends ConsumerStatefulWidget {
  const WorkstationScreen({super.key, required this.tabKey});

  final String tabKey;

  @override
  ConsumerState<WorkstationScreen> createState() => _WorkstationScreenState();
}

class _WorkstationScreenState extends ConsumerState<WorkstationScreen> {
  final TextEditingController _composerController = TextEditingController();
  Timer? _prepareDebounce;
  bool _restoreAttempted = false;
  String? _desktopShellStateKey;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(workstationControllerProvider.notifier).showTab(widget.tabKey);
    });
  }

  @override
  void didUpdateWidget(covariant WorkstationScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.tabKey != widget.tabKey) {
      _desktopShellStateKey = null;
      _restoreAttempted = false;
      WidgetsBinding.instance.addPostFrameCallback((_) {
        ref.read(workstationControllerProvider.notifier).showTab(widget.tabKey);
      });
    }
  }

  @override
  void dispose() {
    _prepareDebounce?.cancel();
    _composerController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(workstationControllerProvider);
    if (!state.connected) {
      _maybeRestoreDisconnectedWorkstation(
        ref.read(workstationControllerProvider.notifier),
      );
      return const BootstrapScreen();
    }
    _restoreAttempted = false;
    final layoutAsync = ref.watch(workstationLayoutProvider);
    return layoutAsync.when(
      data: (layout) => _buildConnectedShell(context, ref, state, layout),
      loading: () =>
          const Scaffold(body: Center(child: CircularProgressIndicator())),
      error: (error, stackTrace) => Scaffold(
        body: Center(child: Text('Failed to load layout artifact: $error')),
      ),
    );
  }

  void _maybeRestoreDisconnectedWorkstation(WorkstationController controller) {
    if (_restoreAttempted) {
      return;
    }
    _restoreAttempted = true;
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      if (!mounted) {
        return;
      }
      var current = ref.read(workstationControllerProvider);
      if (current.connected) {
        _restoreAttempted = false;
        return;
      }
      if (!current.loadingRoots &&
          current.roots.isEmpty &&
          current.errorText == null) {
        await controller.loadRoots(current.endpoint);
      }
      if (!mounted) {
        return;
      }
      current = ref.read(workstationControllerProvider);
      if (current.connected ||
          current.openingRoot ||
          current.roots.isEmpty ||
          current.selectedRootPath.isEmpty) {
        return;
      }
      final opened = await controller.openSelectedRoot();
      if (!mounted || !opened) {
        return;
      }
      await controller.showTab(widget.tabKey);
    });
  }

  Future<void> _navigateAfterAction(String? nextTab) async {
    if (!mounted || nextTab == null) {
      return;
    }
    final normalizedNextTab = _normalizeTabKey(nextTab);
    if (!context.mounted ||
        normalizedNextTab == _normalizeTabKey(widget.tabKey)) {
      return;
    }
    context.go('/workstation/$normalizedNextTab');
  }

  Future<void> _runMarkdownImportFlow(WorkstationController controller) async {
    final picked = await FilePicker.platform.pickFiles(
      withData: true,
      type: FileType.custom,
      allowedExtensions: const <String>['md', 'markdown', 'txt'],
    );
    if (picked == null ||
        picked.files.isEmpty ||
        picked.files.single.bytes == null) {
      return;
    }
    final nextTab = await controller.stageMarkdownUpload(
      picked.files.single.name,
      Uint8List.fromList(picked.files.single.bytes!),
    );
    await _navigateAfterAction(nextTab);
  }

  Future<String?> _promptForUrl(BuildContext context) async {
    final controller = TextEditingController();
    try {
      return await showDialog<String>(
        context: context,
        builder: (dialogContext) {
          return AlertDialog(
            title: const Text('Import URL'),
            content: TextField(
              controller: controller,
              autofocus: true,
              decoration: const InputDecoration(
                labelText: 'Source URL',
                hintText: 'https://example.com/article',
              ),
              onSubmitted: (value) {
                Navigator.of(dialogContext).pop(value.trim());
              },
            ),
            actions: <Widget>[
              TextButton(
                onPressed: () => Navigator.of(dialogContext).pop(),
                child: const Text('Cancel'),
              ),
              FilledButton(
                onPressed: () =>
                    Navigator.of(dialogContext).pop(controller.text.trim()),
                child: const Text('Learn URL'),
              ),
            ],
          );
        },
      );
    } finally {
      controller.dispose();
    }
  }

  Future<void> _runSubjectUiAction(
    BuildContext context,
    WorkstationController controller,
    String actionKey, {
    String? actionLabel,
  }) async {
    switch (actionKey) {
      case 'use_markdown_ingress':
        await _runMarkdownImportFlow(controller);
        return;
      case 'use_url_ingress':
        final selectedUrl = await _promptForUrl(context);
        if (selectedUrl == null || selectedUrl.trim().isEmpty) {
          return;
        }
        await _navigateAfterAction(
          await controller.applyAction(
            actionKey,
            assistantMessageText: selectedUrl.trim(),
          ),
        );
        return;
      default:
        final preferredTabKey = _preferredActionTabKey(
          actionKey,
          actionLabel: actionLabel,
        );
        final currentTabKey = ref
            .read(workstationControllerProvider)
            .currentTabKey;
        if (preferredTabKey != null && preferredTabKey != currentTabKey) {
          await controller.showTab(preferredTabKey);
        }
        final nextTab = await controller.applyAction(actionKey);
        _updateDesktopShellStateForAction(actionKey);
        await _navigateAfterAction(nextTab);
        return;
    }
  }

  String? _preferredActionTabKey(String actionKey, {String? actionLabel}) {
    final prefix = _actionLabelPrefix(actionLabel);
    if (prefix != null) {
      return switch (prefix.toLowerCase()) {
        'gather' => 'research',
        'itemize' => 'itemize',
        'draft' => 'draft',
        'review' => 'review',
        'publication' => 'publication',
        'chat' => 'chat',
        _ => null,
      };
    }
    return switch (actionKey) {
      'open_draft_model_view' ||
      'open_draft_model_frame_view' ||
      'open_draft_model_model_view' ||
      'open_draft_model_explore_view' ||
      'open_draft_compose_view' => 'draft',
      _ => null,
    };
  }

  String? _actionLabelPrefix(String? actionLabel) {
    final normalized =
        actionLabel?.trim().replaceAll(RegExp(r'\s+'), ' ') ?? '';
    if (normalized.isEmpty || !normalized.contains(':')) {
      return null;
    }
    final separator = normalized.indexOf(':');
    if (separator <= 0) {
      return null;
    }
    final prefix = normalized.substring(0, separator).trim();
    return prefix.isEmpty ? null : prefix;
  }

  void _updateDesktopShellStateForAction(String actionKey) {
    final shellStateKey = switch (actionKey) {
      'open_draft_model_view' || 'open_draft_model_model_view' => 'draft.model',
      'open_draft_model_frame_view' => 'draft.frame',
      'open_draft_model_explore_view' => 'draft.explore',
      'open_draft_compose_view' => 'draft.compose',
      _ => null,
    };
    if (!mounted || shellStateKey == null) {
      return;
    }
    setState(() {
      _desktopShellStateKey = shellStateKey;
    });
  }

  String _defaultShellStateForTab(String routeTabKey) {
    return switch (routeTabKey) {
      'research' => 'gather.main',
      'itemize' => 'itemize.main',
      'draft' => 'draft.compose',
      'review' => 'review.main',
      'publication' => 'publication.main',
      _ => 'gather.main',
    };
  }

  String _tabKeyForShellState(String shellStateKey) {
    if (shellStateKey.startsWith('gather.')) {
      return 'research';
    }
    if (shellStateKey.startsWith('itemize.')) {
      return 'itemize';
    }
    if (shellStateKey.startsWith('draft.')) {
      return 'draft';
    }
    if (shellStateKey.startsWith('review.')) {
      return 'review';
    }
    if (shellStateKey.startsWith('publication.')) {
      return 'publication';
    }
    return 'research';
  }

  String _activeDesktopShellStateKey(
    shell_spec.WorkstationLayoutSpec layout,
    String routeTabKey,
    subject.SubjectWorkflowSnapshotView? snapshot,
  ) {
    if (routeTabKey == 'draft' && snapshot != null) {
      final draftShellStateKey = _draftShellStateKeyFromSnapshot(snapshot);
      if (draftShellStateKey != null &&
          layout.shellStates.any((state) => state.key == draftShellStateKey)) {
        return draftShellStateKey;
      }
    }
    final candidate = _desktopShellStateKey;
    if (candidate != null &&
        _tabKeyForShellState(candidate) == routeTabKey &&
        layout.shellStates.any((state) => state.key == candidate)) {
      return candidate;
    }
    return _defaultShellStateForTab(routeTabKey);
  }

  String? _draftShellStateKeyFromSnapshot(
    subject.SubjectWorkflowSnapshotView snapshot,
  ) {
    subject.SubjectPaneView? modelPane;
    for (final pane in snapshot.paneBundle.panes) {
      if (pane.key == 'draft_model_main') {
        modelPane = pane;
        break;
      }
    }
    final modelTitle = modelPane?.title.trim() ?? '';
    return switch (modelTitle) {
      'Case Frame' => 'draft.frame',
      'Explore Alternatives' => 'draft.explore',
      'Transformation Model' => 'draft.model',
      _ => 'draft.compose',
    };
  }

  String _selectedScenarioLabel(WorkstationState state) {
    if (state.selectedScenarioKey.isNotEmpty) {
      for (final scenario in state.subjects) {
        if (_scenarioIdentity(scenario) == state.selectedScenarioKey) {
          return _scenarioLabel(scenario);
        }
      }
    }
    final scenario = state.subjectSnapshot?.phaseView.scenario;
    if (scenario != null) {
      if (scenario.title.isNotEmpty) {
        return scenario.title;
      }
      if (scenario.subjectId.isNotEmpty) {
        return scenario.subjectId;
      }
    }
    return 'No Subject';
  }

  Widget _buildConnectedShell(
    BuildContext context,
    WidgetRef ref,
    WorkstationState state,
    shell_spec.WorkstationLayoutSpec layout,
  ) {
    final controller = ref.read(workstationControllerProvider.notifier);
    final normalizedTab = _normalizeTabKey(widget.tabKey);
    final useTextualDesktopShell = _subjectPhaseForTab(normalizedTab) != null;

    if (useTextualDesktopShell) {
      final snapshot = state.subjectSnapshot;
      if (snapshot == null) {
        return Scaffold(
          body: Container(
            color: Colors.black,
            alignment: Alignment.center,
            child: state.subjectBusy
                ? const CircularProgressIndicator()
                : const Text(
                    'No subject snapshot is loaded for this phase.',
                    style: TextStyle(color: Colors.white),
                  ),
          ),
        );
      }
      final activeShellStateKey = _activeDesktopShellStateKey(
        layout,
        normalizedTab,
        snapshot,
      );
      return Scaffold(
        body: SafeArea(
          child: TextualDesktopSubjectShell(
            layout: layout,
            tabs: layout.tabs,
            currentTabKey: normalizedTab,
            activeShellStateKey: activeShellStateKey,
            subjects: state.subjects,
            selectedScenarioKey: state.selectedScenarioKey,
            selectedScenarioLabel: _selectedScenarioLabel(state),
            onSubjectSelected: (scenarioKey) {
              unawaited(controller.selectSubject(scenarioKey));
            },
            statusText: subjectShellLastActionText(
              statusText: state.statusText,
              markdownIngressBusy: state.markdownIngressBusy,
              subjectBusy: state.subjectBusy,
            ),
            onShellStateSelected: (shellStateKey) {
              final tabKey = _tabKeyForShellState(shellStateKey);
              if (tabKey != normalizedTab) {
                context.go('/workstation/$tabKey');
                return;
              }
              setState(() {
                _desktopShellStateKey = shellStateKey;
              });
            },
            onTabSelected: (tabKey) {
              context.go('/workstation/$tabKey');
            },
            snapshot: snapshot,
            subjectBusy: state.subjectBusy,
            onAction: (actionKey, {actionLabel}) => _runSubjectUiAction(
              context,
              controller,
              actionKey,
              actionLabel: actionLabel,
            ),
            onInteraction:
                (
                  interactionKey, {
                  int delta = 0,
                  String? targetId,
                  bool previewOnly = false,
                }) => controller.applyInteraction(
                  interactionKey,
                  delta: delta,
                  targetId: targetId,
                  previewOnly: previewOnly,
                ),
          ),
        ),
      );
    }

    final screenWidth = MediaQuery.of(context).size.width;
    final tabIndex = layout.tabs.indexWhere((tab) => tab.key == normalizedTab);
    final selectedIndex = tabIndex >= 0 ? tabIndex : 0;
    final useRail = screenWidth >= 1180;
    final tabSpec = layout.tabForKey(normalizedTab);
    final body = _buildTabBody(context, ref, state, layout, tabSpec);

    final destinations = layout.tabs
        .map(
          (tab) => NavigationRailDestination(
            icon: const Icon(Icons.circle_outlined),
            label: Text(tab.title),
          ),
        )
        .toList(growable: false);
    final navDestinations = layout.tabs
        .map(
          (tab) => NavigationDestination(
            icon: const Icon(Icons.circle_outlined),
            label: tab.title,
          ),
        )
        .toList(growable: false);

    return Scaffold(
      appBar: AppBar(
        title: Text('Workstation · ${tabSpec.title}'),
        actions: <Widget>[
          if (_subjectPhaseForTab(normalizedTab) != null)
            SizedBox(
              width: 260,
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 8),
                child: DropdownButtonFormField<String>(
                  key: ValueKey<String>(
                    'subject-selector:$normalizedTab:${state.selectedScenarioKey}:${state.subjects.length}',
                  ),
                  isExpanded: true,
                  initialValue: state.selectedScenarioKey.isEmpty
                      ? null
                      : state.selectedScenarioKey,
                  items: state.subjects
                      .map(
                        (item) => DropdownMenuItem<String>(
                          value: _scenarioIdentity(item),
                          child: Text(_scenarioLabel(item)),
                        ),
                      )
                      .toList(growable: false),
                  onChanged: (value) {
                    if (value != null) {
                      controller.selectSubject(value);
                    }
                  },
                  decoration: const InputDecoration(
                    labelText: 'Subject',
                    contentPadding: EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 8,
                    ),
                  ),
                ),
              ),
            ),
          if (normalizedTab == 'research')
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8),
              child: TextButton.icon(
                onPressed: state.subjectBusy
                    ? null
                    : () => _runMarkdownImportFlow(controller),
                icon: const Icon(Icons.upload_file_outlined),
                label: const Text('Import Markdown'),
              ),
            ),
          IconButton(
            onPressed: () => controller.showTab(normalizedTab),
            tooltip: 'Refresh',
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: SafeArea(
        child: Row(
          children: <Widget>[
            if (useRail)
              NavigationRail(
                selectedIndex: selectedIndex,
                labelType: NavigationRailLabelType.all,
                onDestinationSelected: (index) {
                  context.go('/workstation/${layout.tabs[index].key}');
                },
                destinations: destinations,
              ),
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  children: <Widget>[
                    if (_shouldShowConnectedShellBanner(state)) ...<Widget>[
                      _InfoBanner(
                        text: state.statusText,
                        errorText: state.errorText,
                      ),
                      const SizedBox(height: 16),
                    ],
                    Expanded(child: body),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
      bottomNavigationBar: useRail
          ? null
          : NavigationBar(
              selectedIndex: selectedIndex,
              destinations: navDestinations,
              onDestinationSelected: (index) {
                context.go('/workstation/${layout.tabs[index].key}');
              },
            ),
    );
  }

  Widget _buildTabBody(
    BuildContext context,
    WidgetRef ref,
    WorkstationState state,
    shell_spec.WorkstationLayoutSpec layout,
    shell_spec.WorkstationTabSpec tabSpec,
  ) {
    switch (tabSpec.key) {
      case 'chat':
        return _buildChatTab(context, ref, state, tabSpec);
      case 'permissions':
        return _buildTextPanelTab(
          tabSpec,
          state.permissionsView?.text ?? 'Permissions view unavailable.',
        );
      case 'activity':
        return _buildTextPanelTab(
          tabSpec,
          state.activityView?.text ?? 'Activity view unavailable.',
        );
      case 'skills':
        return _buildTextPanelTab(
          tabSpec,
          state.skillsView?.text ?? 'Skills view unavailable.',
        );
      default:
        return _buildSubjectTab(context, ref, state, tabSpec);
    }
  }

  Widget _buildChatTab(
    BuildContext context,
    WidgetRef ref,
    WorkstationState state,
    shell_spec.WorkstationTabSpec tabSpec,
  ) {
    final controller = ref.read(workstationControllerProvider.notifier);
    final transcriptMessages =
        state.chatSnapshot?.messages ?? const <shell.WorkstationChatMessage>[];
    final suggestionText =
        state.preparedPromptTarget?.shellText ??
        'Type in the composer to preview shell routing.';
    final hintText = state.preparedPromptTarget == null
        ? 'The shell routing hint appears here.'
        : '${state.preparedPromptTarget!.targetKind} · ${state.preparedPromptTarget!.preparedPrompt}';
    final sendButton = FilledButton.icon(
      onPressed: state.chatBusy
          ? null
          : () async {
              final prompt = _composerController.text.trim();
              if (prompt.isEmpty) {
                return;
              }
              await controller.submitPrompt(prompt);
              _composerController.clear();
            },
      icon: state.chatBusy
          ? const SizedBox.square(
              dimension: 18,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
          : const Icon(Icons.send),
      label: const Text('Send'),
    );
    return LayoutBuilder(
      builder: (context, constraints) {
        final useWideRail = constraints.maxWidth >= 1440;
        final useSupportRow = constraints.maxWidth >= 1040;
        final useTwoColumnFooter = constraints.maxWidth >= 1120;
        final statusCard = _SurfaceCard(
          title: _paneTitle(tabSpec, 'status', fallback: 'Status'),
          child: Text(state.chatSnapshot?.sessionStatus ?? 'unknown'),
        );
        final activityCard = _SurfaceCard(
          title: _paneTitle(tabSpec, 'activity', fallback: 'Activity'),
          child: Text(state.activityView?.text ?? 'No recent activity.'),
        );
        final suggestionsCard = _SurfaceCard(
          title: _paneTitle(tabSpec, 'suggestions', fallback: 'Suggestions'),
          child: Text(suggestionText),
        );
        final hintCard = _SurfaceCard(
          title: _paneTitle(tabSpec, 'hint', fallback: 'Hint'),
          child: Text(hintText),
        );
        final mainColumn = <Widget>[
          if (useSupportRow)
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Expanded(child: statusCard),
                const SizedBox(width: 12),
                Expanded(child: activityCard),
              ],
            )
          else ...<Widget>[
            statusCard,
            const SizedBox(height: 12),
            activityCard,
          ],
          const SizedBox(height: 12),
          Expanded(
            child: _SurfaceCard(
              title: _paneTitle(tabSpec, 'transcript', fallback: 'Transcript'),
              expandChild: true,
              child: transcriptMessages.isEmpty
                  ? const Center(child: Text('No shell transcript yet.'))
                  : ListView.separated(
                      itemBuilder: (context, index) =>
                          _ChatMessageTile(message: transcriptMessages[index]),
                      separatorBuilder: (context, index) =>
                          const SizedBox(height: 8),
                      itemCount: transcriptMessages.length,
                    ),
            ),
          ),
          const SizedBox(height: 12),
          _SurfaceCard(
            title: _paneTitle(tabSpec, 'composer', fallback: 'Composer'),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                TextField(
                  controller: _composerController,
                  minLines: 3,
                  maxLines: 6,
                  onChanged: (value) {
                    _prepareDebounce?.cancel();
                    _prepareDebounce = Timer(
                      const Duration(milliseconds: 250),
                      () => controller.preparePrompt(value),
                    );
                  },
                  decoration: const InputDecoration(
                    hintText:
                        'Ask the shell to inspect, route, or operate on the workstation.',
                  ),
                ),
                const SizedBox(height: 12),
                if (useTwoColumnFooter)
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: <Widget>[
                      Expanded(
                        child: Text(
                          hintText,
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ),
                      const SizedBox(width: 12),
                      sendButton,
                    ],
                  )
                else ...<Widget>[
                  Text(hintText, style: Theme.of(context).textTheme.bodySmall),
                  const SizedBox(height: 12),
                  Align(alignment: Alignment.centerRight, child: sendButton),
                ],
              ],
            ),
          ),
        ];
        if (useWideRail) {
          return Row(
            children: <Widget>[
              Expanded(child: Column(children: mainColumn)),
              const SizedBox(width: 16),
              SizedBox(
                width: 340,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: <Widget>[
                    Expanded(flex: 2, child: suggestionsCard),
                    const SizedBox(height: 12),
                    Expanded(child: hintCard),
                  ],
                ),
              ),
            ],
          );
        }
        return Column(
          children: <Widget>[
            ...mainColumn,
            const SizedBox(height: 12),
            if (useSupportRow)
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Expanded(child: suggestionsCard),
                  const SizedBox(width: 12),
                  Expanded(child: hintCard),
                ],
              )
            else
              _SurfaceCard(
                title: _paneTitle(
                  tabSpec,
                  'suggestions',
                  fallback: 'Suggestions',
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(suggestionText),
                    const SizedBox(height: 12),
                    Text(
                      hintText,
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ),
              ),
          ],
        );
      },
    );
  }

  Widget _buildTextPanelTab(
    shell_spec.WorkstationTabSpec tabSpec,
    String text,
  ) {
    return SizedBox.expand(
      child: _SurfaceCard(
        title: tabSpec.title,
        expandChild: true,
        child: _ScrollableSurfaceBody(
          child: Align(
            alignment: Alignment.topLeft,
            child: SizedBox(
              width: double.infinity,
              child: SelectableText(text),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildSubjectTab(
    BuildContext context,
    WidgetRef ref,
    WorkstationState state,
    shell_spec.WorkstationTabSpec tabSpec,
  ) {
    final controller = ref.read(workstationControllerProvider.notifier);
    final snapshot = state.subjectSnapshot;
    if (snapshot == null) {
      return const Center(
        child: Text('No subject snapshot is loaded for this phase.'),
      );
    }
    final phaseView = snapshot.phaseView;
    final controlBundle = snapshot.controlBundle;
    final panes = snapshot.paneBundle.panes;
    return LayoutBuilder(
      builder: (context, constraints) {
        final desktop = constraints.maxWidth >= 1120;
        final boundedHeight = constraints.maxHeight.isFinite
            ? constraints.maxHeight
            : 960.0;
        final actionButtons = <Widget>[
          ...phaseView.currentStep.actions.map(
            (action) => FilledButton(
              onPressed:
                  (!action.enabled ||
                      state.subjectBusy ||
                      _isFlutterDisabledSubjectAction(action.key))
                  ? null
                  : () async {
                      await _runSubjectUiAction(
                        context,
                        controller,
                        action.key,
                        actionLabel: action.label,
                      );
                    },
              child: Text(action.label),
            ),
          ),
          ...controlBundle.moreActions.map(
            (action) => OutlinedButton(
              onPressed:
                  (!action.enabled ||
                      state.subjectBusy ||
                      _isFlutterDisabledSubjectAction(action.key))
                  ? null
                  : () async {
                      await _runSubjectUiAction(
                        context,
                        controller,
                        action.key,
                        actionLabel: action.label,
                      );
                    },
              child: Text(action.label),
            ),
          ),
        ];

        final actionCard = _SurfaceCard(
          title: _paneTitle(tabSpec, 'actions', fallback: 'Actions'),
          expandChild: desktop,
          child: desktop
              ? _ScrollableSurfaceBody(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Text(
                        phaseView.currentStep.title,
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 8),
                      Text(phaseView.currentStep.status),
                      if (phaseView.currentStep.why.isNotEmpty) ...<Widget>[
                        const SizedBox(height: 8),
                        Text(phaseView.currentStep.why),
                      ],
                      if (phaseView
                          .currentStep
                          .detailLines
                          .isNotEmpty) ...<Widget>[
                        const SizedBox(height: 12),
                        ...phaseView.currentStep.detailLines.map(
                          (line) => Text(line),
                        ),
                      ],
                      if (actionButtons.isNotEmpty) ...<Widget>[
                        const SizedBox(height: 16),
                        Wrap(
                          spacing: 12,
                          runSpacing: 12,
                          children: actionButtons,
                        ),
                      ],
                      if (controlBundle.selects.isNotEmpty ||
                          controlBundle.switches.isNotEmpty ||
                          controlBundle.selectionLists.isNotEmpty ||
                          controlBundle.tables.isNotEmpty) ...<Widget>[
                        const SizedBox(height: 16),
                        _ControlSummaryBundle(bundle: controlBundle),
                      ],
                    ],
                  ),
                )
              : Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      phaseView.currentStep.title,
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                    const SizedBox(height: 8),
                    Text(phaseView.currentStep.status),
                    if (phaseView.currentStep.why.isNotEmpty) ...<Widget>[
                      const SizedBox(height: 8),
                      Text(phaseView.currentStep.why),
                    ],
                    if (phaseView
                        .currentStep
                        .detailLines
                        .isNotEmpty) ...<Widget>[
                      const SizedBox(height: 12),
                      ...phaseView.currentStep.detailLines.map(
                        (line) => Text(line),
                      ),
                    ],
                    if (actionButtons.isNotEmpty) ...<Widget>[
                      const SizedBox(height: 16),
                      Wrap(
                        spacing: 12,
                        runSpacing: 12,
                        children: actionButtons,
                      ),
                    ],
                    if (controlBundle.selects.isNotEmpty ||
                        controlBundle.switches.isNotEmpty ||
                        controlBundle.selectionLists.isNotEmpty ||
                        controlBundle.tables.isNotEmpty) ...<Widget>[
                      const SizedBox(height: 16),
                      _ControlSummaryBundle(bundle: controlBundle),
                    ],
                  ],
                ),
        );
        final progressCard = _SurfaceCard(
          title: _paneTitle(tabSpec, 'progress', fallback: 'Progress'),
          expandChild: desktop,
          child: desktop
              ? _ScrollableSurfaceBody(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      ...phaseView.statusView.rows.map(
                        (row) =>
                            _KeyValueLine(label: row.label, value: row.value),
                      ),
                      if (state.markdownStatusText.isNotEmpty) ...<Widget>[
                        const SizedBox(height: 12),
                        Text(state.markdownStatusText),
                      ],
                      if (state.latestArtifacts.isNotEmpty) ...<Widget>[
                        const SizedBox(height: 16),
                        Text(
                          'Artifacts',
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        const SizedBox(height: 8),
                        Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children: state.latestArtifacts
                              .map(
                                (artifact) => OutlinedButton.icon(
                                  onPressed: () =>
                                      controller.openArtifact(artifact),
                                  icon: const Icon(Icons.open_in_new),
                                  label: Text(artifact.label),
                                ),
                              )
                              .toList(growable: false),
                        ),
                      ],
                    ],
                  ),
                )
              : Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    ...phaseView.statusView.rows.map(
                      (row) =>
                          _KeyValueLine(label: row.label, value: row.value),
                    ),
                    if (state.markdownStatusText.isNotEmpty) ...<Widget>[
                      const SizedBox(height: 12),
                      Text(state.markdownStatusText),
                    ],
                    if (state.latestArtifacts.isNotEmpty) ...<Widget>[
                      const SizedBox(height: 16),
                      Text(
                        'Artifacts',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 8),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: state.latestArtifacts
                            .map(
                              (artifact) => OutlinedButton.icon(
                                onPressed: () =>
                                    controller.openArtifact(artifact),
                                icon: const Icon(Icons.open_in_new),
                                label: Text(artifact.label),
                              ),
                            )
                            .toList(growable: false),
                      ),
                    ],
                  ],
                ),
        );

        final actionCards = <Widget>[
          actionCard,
          const SizedBox(height: 16),
          progressCard,
        ];

        final learningSummaryCard = _SurfaceCard(
          title: _paneTitle(tabSpec, 'learning', fallback: 'Learning'),
          expandChild: desktop,
          child: desktop
              ? _ScrollableSurfaceBody(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Text(
                        phaseView.scenario.title.isEmpty
                            ? phaseView.scenario.subjectId
                            : phaseView.scenario.title,
                        style: Theme.of(context).textTheme.headlineSmall,
                      ),
                      const SizedBox(height: 8),
                      Text(phaseView.scenario.summary),
                      if (phaseView.journeyLines.isNotEmpty) ...<Widget>[
                        const SizedBox(height: 16),
                        Text(
                          'Journey',
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        const SizedBox(height: 8),
                        ...phaseView.journeyLines.map((line) => Text(line)),
                      ],
                      if (phaseView.workspaceView.lines.isNotEmpty) ...<Widget>[
                        const SizedBox(height: 16),
                        Text(
                          phaseView.workspaceView.title,
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        const SizedBox(height: 8),
                        ...phaseView.workspaceView.lines.map(
                          (line) => Text(line),
                        ),
                      ],
                    ],
                  ),
                )
              : Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      phaseView.scenario.title.isEmpty
                          ? phaseView.scenario.subjectId
                          : phaseView.scenario.title,
                      style: Theme.of(context).textTheme.headlineSmall,
                    ),
                    const SizedBox(height: 8),
                    Text(phaseView.scenario.summary),
                    if (phaseView.journeyLines.isNotEmpty) ...<Widget>[
                      const SizedBox(height: 16),
                      Text(
                        'Journey',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 8),
                      ...phaseView.journeyLines.map((line) => Text(line)),
                    ],
                    if (phaseView.workspaceView.lines.isNotEmpty) ...<Widget>[
                      const SizedBox(height: 16),
                      Text(
                        phaseView.workspaceView.title,
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 8),
                      ...phaseView.workspaceView.lines.map(
                        (line) => Text(line),
                      ),
                    ],
                  ],
                ),
        );

        final paneCards = panes
            .map((pane) => _SubjectPaneCard(pane: pane))
            .toList(growable: false);

        if (desktop) {
          final leftColumnWidth = constraints.maxWidth >= 1520 ? 420.0 : 388.0;
          final columnGap = 16.0;
          final halfPageHeight = (boundedHeight - columnGap) / 2;
          final learningHeight = boundedHeight * 0.25;
          final rightPaneCrossAxisCount =
              constraints.maxWidth >= 1500 && paneCards.length > 1 ? 2 : 1;
          final paneAspectRatio = rightPaneCrossAxisCount == 2 ? 1.35 : 1.85;
          final lowerPaneCards = paneCards;

          return SizedBox.expand(
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                SizedBox(
                  width: leftColumnWidth,
                  child: Column(
                    children: <Widget>[
                      SizedBox(height: halfPageHeight, child: actionCard),
                      const SizedBox(height: 16),
                      SizedBox(height: halfPageHeight, child: progressCard),
                    ],
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    children: <Widget>[
                      SizedBox(
                        height: learningHeight,
                        child: learningSummaryCard,
                      ),
                      if (lowerPaneCards.isNotEmpty) ...<Widget>[
                        const SizedBox(height: 16),
                        Expanded(
                          child: GridView.count(
                            crossAxisCount: rightPaneCrossAxisCount,
                            crossAxisSpacing: 16,
                            mainAxisSpacing: 16,
                            childAspectRatio: paneAspectRatio,
                            children: lowerPaneCards,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ],
            ),
          );
        }
        return ListView(
          children: <Widget>[
            ...actionCards,
            const SizedBox(height: 16),
            learningSummaryCard,
            if (paneCards.isNotEmpty) ...<Widget>[
              for (
                var index = 0;
                index < paneCards.length;
                index++
              ) ...<Widget>[const SizedBox(height: 16), paneCards[index]],
            ],
          ],
        );
      },
    );
  }
}

class _SurfaceCard extends StatelessWidget {
  const _SurfaceCard({
    required this.title,
    required this.child,
    this.expandChild = false,
  });

  final String title;
  final Widget child;
  final bool expandChild;

  @override
  Widget build(BuildContext context) {
    return Card(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: BorderSide(
          color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.18),
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: LayoutBuilder(
          builder: (BuildContext context, BoxConstraints constraints) {
            final useExpanded = expandChild && constraints.maxHeight.isFinite;
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                if (title.isNotEmpty) ...<Widget>[
                  Text(
                    title,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      color: Theme.of(context).colorScheme.secondary,
                    ),
                  ),
                  const SizedBox(height: 16),
                ],
                if (useExpanded) Expanded(child: child) else child,
              ],
            );
          },
        ),
      ),
    );
  }
}

class _InfoBanner extends StatelessWidget {
  const _InfoBanner({required this.text, required this.errorText});

  final String text;
  final String? errorText;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final hasError = errorText != null && errorText!.isNotEmpty;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: hasError
            ? scheme.errorContainer
            : scheme.surfaceContainerHighest.withValues(alpha: 0.42),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          if (text.isNotEmpty) Text(text),
          if (hasError) ...<Widget>[
            if (text.isNotEmpty) const SizedBox(height: 8),
            Text(errorText!),
          ],
        ],
      ),
    );
  }
}

class _ChatMessageTile extends StatelessWidget {
  const _ChatMessageTile({required this.message});

  final shell.WorkstationChatMessage message;

  @override
  Widget build(BuildContext context) {
    final role = message.role;
    final background = switch (role) {
      'assistant' => Theme.of(
        context,
      ).colorScheme.primary.withValues(alpha: 0.12),
      'shell' => Theme.of(
        context,
      ).colorScheme.secondary.withValues(alpha: 0.12),
      _ => Theme.of(
        context,
      ).colorScheme.surfaceContainerHighest.withValues(alpha: 0.28),
    };
    final timestamp = message.timestampEpochMs == 0
        ? ''
        : TimeOfDay.fromDateTime(
            DateTime.fromMillisecondsSinceEpoch(
              message.timestampEpochMs.toInt(),
            ),
          ).format(context);
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              Text(role),
              if (timestamp.isNotEmpty) ...<Widget>[
                const SizedBox(width: 8),
                Text(timestamp, style: Theme.of(context).textTheme.bodySmall),
              ],
            ],
          ),
          const SizedBox(height: 8),
          SelectableText(message.content),
        ],
      ),
    );
  }
}

class _KeyValueLine extends StatelessWidget {
  const _KeyValueLine({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          SizedBox(
            width: 180,
            child: Text(
              label,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: Theme.of(context).colorScheme.secondary,
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }
}

class _ControlSummaryBundle extends StatelessWidget {
  const _ControlSummaryBundle({required this.bundle});

  final subject.SubjectControlBundleView bundle;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        if (bundle.selects.isNotEmpty) ...<Widget>[
          Text('Selectors', style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 8),
          ...bundle.selects.map(
            (item) => _KeyValueLine(label: item.label, value: item.value),
          ),
        ],
        if (bundle.switches.isNotEmpty) ...<Widget>[
          Text('Switches', style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 8),
          ...bundle.switches.map(
            (item) => _KeyValueLine(
              label: item.label,
              value: item.value ? 'Enabled' : 'Disabled',
            ),
          ),
        ],
        if (bundle.selectionLists.isNotEmpty) ...<Widget>[
          Text('Selections', style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 8),
          ...bundle.selectionLists.map(
            (item) => _KeyValueLine(
              label: item.label,
              value: item.options
                  .where((option) => option.selected)
                  .map((option) => option.label)
                  .join(', '),
            ),
          ),
        ],
        if (bundle.tables.isNotEmpty) ...<Widget>[
          Text('Tables', style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 8),
          ...bundle.tables.map(
            (item) => _KeyValueLine(
              label: item.label,
              value: '${item.rows.length} row(s)',
            ),
          ),
        ],
      ],
    );
  }
}

class _SubjectPaneCard extends StatelessWidget {
  const _SubjectPaneCard({required this.pane});

  final subject.SubjectPaneView pane;

  @override
  Widget build(BuildContext context) {
    return _SurfaceCard(
      title: pane.title.isEmpty ? pane.key : pane.title,
      expandChild: true,
      child: _ScrollableSurfaceBody(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            if (pane.rows.isNotEmpty)
              ...pane.rows.map(
                (row) => _KeyValueLine(label: row.label, value: row.value),
              ),
            if (pane.lines.isNotEmpty) ...<Widget>[
              if (pane.rows.isNotEmpty) const SizedBox(height: 12),
              ...pane.lines.map(
                (line) => Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: SelectableText(line),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _ScrollableSurfaceBody extends StatefulWidget {
  const _ScrollableSurfaceBody({required this.child});

  final Widget child;

  @override
  State<_ScrollableSurfaceBody> createState() => _ScrollableSurfaceBodyState();
}

class _ScrollableSurfaceBodyState extends State<_ScrollableSurfaceBody> {
  late final ScrollController _scrollController;

  @override
  void initState() {
    super.initState();
    _scrollController = ScrollController();
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scrollbar(
      controller: _scrollController,
      thumbVisibility: true,
      child: SingleChildScrollView(
        controller: _scrollController,
        primary: false,
        child: widget.child,
      ),
    );
  }
}

@visibleForTesting
bool isIgnorableWorkstationWatchError(Object error) {
  final message = error.toString().toLowerCase();
  final cancelledCode = RegExp(r'code[: ]+1\b').hasMatch(message);
  return message.contains('request failed with status: 0') ||
      cancelledCode ||
      message.contains('codename: cancelled') ||
      message.contains('abort') ||
      message.contains('cancelled');
}

@visibleForTesting
bool shouldShowConnectedShellBanner({
  required String statusText,
  String? errorText,
  required bool markdownIngressBusy,
  required bool subjectBusy,
}) {
  final normalizedStatus = statusText.trim();
  if ((errorText ?? '').trim().isNotEmpty) {
    return true;
  }
  if (normalizedStatus.isEmpty) {
    return false;
  }
  if (normalizedStatus.startsWith('Connected to ')) {
    return false;
  }
  if (!markdownIngressBusy &&
      !subjectBusy &&
      (normalizedStatus.startsWith('Staged ') ||
          normalizedStatus == 'Markdown upload staged.')) {
    return false;
  }
  return true;
}

@visibleForTesting
String subjectShellLastActionText({
  required String statusText,
  required bool markdownIngressBusy,
  required bool subjectBusy,
}) {
  final normalizedStatus = statusText.trim();
  if (normalizedStatus.isEmpty) {
    return '';
  }
  if (normalizedStatus.startsWith('Connected to ')) {
    return '';
  }
  if (!markdownIngressBusy &&
      !subjectBusy &&
      (normalizedStatus.startsWith('Staged ') ||
          normalizedStatus == 'Markdown upload staged.')) {
    return '';
  }
  return normalizedStatus;
}

bool _shouldShowConnectedShellBanner(WorkstationState state) {
  return shouldShowConnectedShellBanner(
    statusText: state.statusText,
    errorText: state.errorText,
    markdownIngressBusy: state.markdownIngressBusy,
    subjectBusy: state.subjectBusy,
  );
}

String _normalizeTabKey(String tabKey) {
  switch (tabKey) {
    case 'learn':
    case 'learn_markdown':
      return 'research';
    default:
      return tabKey;
  }
}

String _normalizedOptionalToken(String value) {
  final normalized = value.trim();
  if (normalized.isEmpty || normalized.toLowerCase() == 'none') {
    return '';
  }
  return normalized;
}

String? _subjectPhaseForTab(String tabKey) {
  return _subjectPhaseTabs.contains(tabKey) ? tabKey : null;
}

String _phaseToTabKey(String phase) {
  return switch (phase) {
    'itemize' => 'itemize',
    'draft' => 'draft',
    'review' => 'review',
    'publication' => 'publication',
    _ => 'research',
  };
}

String _nextTabFromActionResult(
  subject.SubjectActionResult result,
  subject.SubjectPhaseView view,
) {
  final nextTab = _normalizedOptionalToken(result.nextTab);
  if (nextTab.isNotEmpty) {
    return _normalizeTabKey(nextTab);
  }
  final nextPhase = _normalizedOptionalToken(result.nextPhase);
  if (nextPhase.isNotEmpty) {
    return _phaseToTabKey(nextPhase);
  }
  final preferredPhase = _normalizedOptionalToken(view.preferredPhase);
  if (preferredPhase.isNotEmpty) {
    return _phaseToTabKey(preferredPhase);
  }
  return _phaseToTabKey(view.phase);
}

String _scenarioIdentity(subject.SubjectScenarioSummary scenario) {
  return scenario.key.isNotEmpty ? scenario.key : scenario.subjectId;
}

String _scenarioLabel(subject.SubjectScenarioSummary scenario) {
  if (scenario.title.isNotEmpty) {
    return scenario.title;
  }
  final identity = _scenarioIdentity(scenario);
  return identity.isEmpty ? 'Unnamed Scenario' : identity;
}

String _paneTitle(
  shell_spec.WorkstationTabSpec tabSpec,
  String paneKey, {
  required String fallback,
}) {
  for (final pane in tabSpec.panes) {
    if (pane.key == paneKey) {
      return pane.title.isEmpty ? fallback : pane.title;
    }
  }
  return fallback;
}

String _basename(String path) {
  final normalized = path.replaceAll('\\', '/');
  if (normalized.isEmpty) {
    return path;
  }
  final segments = normalized
      .split('/')
      .where((segment) => segment.isNotEmpty)
      .toList(growable: false);
  return segments.isEmpty ? normalized : segments.last;
}
