class WorkstationPaneSpec {
  const WorkstationPaneSpec({
    required this.key,
    required this.title,
    required this.width,
    required this.heightMode,
    required this.heightUnits,
    required this.minHeightUnits,
    required this.scrollX,
    required this.scrollY,
    required this.textRole,
    required this.surfaceRole,
    required this.wrap,
  });

  final String key;
  final String title;
  final String width;
  final String heightMode;
  final int? heightUnits;
  final int? minHeightUnits;
  final bool scrollX;
  final bool scrollY;
  final String textRole;
  final String surfaceRole;
  final bool wrap;

  factory WorkstationPaneSpec.fromJson(Map<String, dynamic> json) {
    return WorkstationPaneSpec(
      key: json['key'] as String? ?? '',
      title: json['title'] as String? ?? '',
      width: json['width'] as String? ?? 'fill',
      heightMode: json['height_mode'] as String? ?? 'content',
      heightUnits: (json['height_units'] as num?)?.toInt(),
      minHeightUnits: (json['min_height_units'] as num?)?.toInt(),
      scrollX: json['scroll_x'] as bool? ?? false,
      scrollY: json['scroll_y'] as bool? ?? false,
      textRole: json['text_role'] as String? ?? 'default',
      surfaceRole: json['surface_role'] as String? ?? 'active',
      wrap: json['wrap'] as bool? ?? true,
    );
  }
}

class WorkstationTabSpec {
  const WorkstationTabSpec({
    required this.key,
    required this.title,
    required this.panes,
  });

  final String key;
  final String title;
  final List<WorkstationPaneSpec> panes;

  WorkstationPaneSpec? paneForKey(String paneKey) {
    for (final pane in panes) {
      if (pane.key == paneKey) {
        return pane;
      }
    }
    return null;
  }

  factory WorkstationTabSpec.fromJson(Map<String, dynamic> json) {
    return WorkstationTabSpec(
      key: json['key'] as String? ?? '',
      title: json['title'] as String? ?? '',
      panes: (json['panes'] as List<dynamic>? ?? const <dynamic>[])
          .map(
            (dynamic item) =>
                WorkstationPaneSpec.fromJson(item as Map<String, dynamic>),
          )
          .toList(growable: false),
    );
  }
}

class WorkstationShellSectionSpec {
  const WorkstationShellSectionSpec({
    required this.key,
    required this.title,
    required this.placement,
  });

  final String key;
  final String title;
  final String placement;

  factory WorkstationShellSectionSpec.fromJson(Map<String, dynamic> json) {
    return WorkstationShellSectionSpec(
      key: json['key'] as String? ?? '',
      title: json['title'] as String? ?? '',
      placement: json['placement'] as String? ?? '',
    );
  }
}

class WorkstationShellStateSpec {
  const WorkstationShellStateSpec({
    required this.key,
    required this.tabKey,
    required this.title,
    required this.sections,
  });

  final String key;
  final String tabKey;
  final String title;
  final List<WorkstationShellSectionSpec> sections;

  factory WorkstationShellStateSpec.fromJson(Map<String, dynamic> json) {
    return WorkstationShellStateSpec(
      key: json['key'] as String? ?? '',
      tabKey: json['tab_key'] as String? ?? '',
      title: json['title'] as String? ?? '',
      sections: (json['sections'] as List<dynamic>? ?? const <dynamic>[])
          .map(
            (dynamic item) => WorkstationShellSectionSpec.fromJson(
              item as Map<String, dynamic>,
            ),
          )
          .toList(growable: false),
    );
  }
}

class WorkstationLayoutSpec {
  const WorkstationLayoutSpec({required this.tabs, required this.shellStates});

  final List<WorkstationTabSpec> tabs;
  final List<WorkstationShellStateSpec> shellStates;

  factory WorkstationLayoutSpec.fromJson(Map<String, dynamic> json) {
    return WorkstationLayoutSpec(
      tabs: (json['tabs'] as List<dynamic>? ?? const <dynamic>[])
          .map(
            (dynamic item) =>
                WorkstationTabSpec.fromJson(item as Map<String, dynamic>),
          )
          .toList(growable: false),
      shellStates:
          (json['desktop_shell_states'] as List<dynamic>? ?? const <dynamic>[])
              .map(
                (dynamic item) => WorkstationShellStateSpec.fromJson(
                  item as Map<String, dynamic>,
                ),
              )
              .toList(growable: false),
    );
  }

  WorkstationTabSpec tabForKey(String key) {
    return tabs.firstWhere((tab) => tab.key == key, orElse: () => tabs.first);
  }

  WorkstationShellStateSpec shellStateForKey(String key) {
    return shellStates.firstWhere(
      (state) => state.key == key,
      orElse: () => shellStates.first,
    );
  }

  List<WorkstationShellStateSpec> shellStatesForTab(String tabKey) {
    return shellStates
        .where((state) => state.tabKey == tabKey)
        .toList(growable: false);
  }
}
