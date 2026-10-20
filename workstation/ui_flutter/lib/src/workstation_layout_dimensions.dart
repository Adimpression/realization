import 'package:flutter/widgets.dart';

/// Snapshot of the Flutter workstation layout dimensions as of 2026-05-07.
///
/// This file is intentionally an inventory first. It does not drive layout yet;
/// the existing callers still use their current hard-coded values. The goal is
/// to capture today's sizing contract in one place before a visual refactor
/// migrates the widgets onto shared tokens.
///
/// Landscape-only assumption:
/// - percentage sizing in this file is defined against a landscape reference
///   viewport and is not intended for portrait/mobile layouts.
final class WorkstationLayoutDimensions {
  const WorkstationLayoutDimensions._();

  static const double terminalHeightUnitPx = 24.0;
  static const double currentViewportFallbackHeight = 960.0;

  static const double borderThin = 1.0;
  static const double borderActive = 2.0;

  static const double radiusCard = 20.0;
  static const double radiusPanel = 16.0;

  static const double titleSizeCompact = 14.0;
  static const double titleSizeRegular = 16.0;
  static const double titleSizeHero = 18.0;

  static const double bodyTextSizeCompact = 13.0;
  static const double bodyTextSizeRegular = 14.0;
  static const double bodyTextSizeSmall = 12.0;
}

final class WorkstationReferenceViewport {
  const WorkstationReferenceViewport._();

  /// Matches the current screenshot harness browser dimension.
  static const Size landscape = Size(1680, 1100);
  static const double landscapeWidth = 1680.0;
  static const double landscapeHeight = 1100.0;
}

final class WorkstationLayoutInsets {
  const WorkstationLayoutInsets._();

  static const EdgeInsets shellPage = EdgeInsets.all(20);

  static const EdgeInsets tabStrip =
      EdgeInsets.symmetric(horizontal: 12, vertical: 10);
  static const EdgeInsets subjectSelector =
      EdgeInsets.symmetric(horizontal: 12, vertical: 4);

  static const EdgeInsets paneFrameCompact = EdgeInsets.all(12);
  static const EdgeInsets paneFrameRegular = EdgeInsets.all(18);
  static const EdgeInsets surfaceCard = EdgeInsets.all(18);
  static const EdgeInsets infoBanner = EdgeInsets.all(16);
  static const EdgeInsets chatTile = EdgeInsets.all(14);
  static const EdgeInsets compactGateSection = EdgeInsets.all(12);

  static const EdgeInsets actionButtonCompact =
      EdgeInsets.symmetric(horizontal: 18, vertical: 12);
  static const EdgeInsets actionButtonRegular =
      EdgeInsets.symmetric(horizontal: 22, vertical: 16);

  static const EdgeInsets selectControlValue =
      EdgeInsets.symmetric(horizontal: 14, vertical: 14);
  static const EdgeInsets selectionSummaryValue =
      EdgeInsets.symmetric(horizontal: 14, vertical: 12);

  static const EdgeInsets inlinePill =
      EdgeInsets.symmetric(horizontal: 6, vertical: 2);
}

final class WorkstationLayoutSpacing {
  const WorkstationLayoutSpacing._();

  static const double xSmall = 4.0;
  static const double small = 6.0;
  static const double compact = 8.0;
  static const double tight = 10.0;
  static const double standard = 12.0;
  static const double roomy = 14.0;
  static const double section = 16.0;
  static const double shell = 18.0;
  static const double page = 20.0;

  static const double tabGap = 16.0;
  static const double paneGap = 16.0;
  static const double gridGap = 16.0;
  static const double controlWrapGap = 18.0;
  static const double controlWrapRunGap = 12.0;
  static const double actionWrapGap = 14.0;
  static const double actionWrapRunGap = 14.0;

  static const double gateHeaderGap = 12.0;
  static const double gateActionTitleGap = 10.0;
  static const double gatePanelGap = 18.0;

  static const double cardTitleGap = 16.0;
  static const double messageGap = 8.0;
  static const double keyValueGap = 12.0;
  static const double keyValueRowGap = 8.0;
}

final class WorkstationLayoutBreakpoints {
  const WorkstationLayoutBreakpoints._();

  static const double subjectTabSelectorWide = 1480.0;
  static const double subjectTabSelectorMedium = 1240.0;

  static const double gateStatusStack = 980.0;
  static const double gateActionTwoColumn = 390.0;

  static const double utilitySupportRow = 1040.0;
  static const double utilityDesktop = 1120.0;
  static const double utilityTwoColumnFooter = 1120.0;
  static const double utilityWideRail = 1440.0;

  static const double subjectDesktop = 1120.0;
  static const double subjectPaneTwoColumn = 1500.0;
  static const double subjectLeftRailWide = 1520.0;

  static const double statusRowsStack = 540.0;
  static const double detailRowsStack = 520.0;
  static const double compactPaneChromeHeight = 140.0;
}

final class WorkstationLayoutWidths {
  const WorkstationLayoutWidths._();

  static const double bootstrapMax = 840.0;
  static const double bootstrapPortField = 160.0;

  static const double subjectSelectorMin = 240.0;
  static const double subjectSelectorPreferredNarrow = 280.0;
  static const double subjectSelectorPreferredMedium = 320.0;
  static const double subjectSelectorMax = 360.0;
  static const double subjectSelectorMenuMaxHeight = 420.0;

  static const double utilityWideRail = 340.0;
  static const double utilitySupportRail = 260.0;

  static const double subjectLeftRailNarrow = 388.0;
  static const double subjectLeftRailWide = 420.0;

  static const double selectControlMin = 220.0;
  static const double selectControlMax = 340.0;
  static const double switchControlMin = 140.0;
  static const double switchControlMax = 220.0;
  static const double selectionSummaryMin = 260.0;
  static const double selectionSummaryMax = 420.0;

  static const double keyValueLabel = 180.0;
  static const double currentStepLabel = 240.0;
  static const double detailLabel = 148.0;
  static const double inlineDetailLabel = 210.0;
  static const double toggleMarker = 42.0;
}

final class WorkstationLayoutHeights {
  const WorkstationLayoutHeights._();

  static const double gateStatusRowMin = 196.0;
  static const double gateStatusRowMax = 248.0;
  static const double gateStatusStack = 128.0;

  static const double gateBase = 68.0;
  static const double gatePrimaryStepContent = 60.0;
  static const double gateActionSectionTitle = 40.0;
  static const double gateActionSlot = 48.0;
  static const double gatePrefixedActionSlot = 64.0;

  static const double sourceDetailPreviewMax = 216.0;

  static const double toggleFrame = 54.0;
  static const double toggleThumb = 24.0;

  static const double compactButtonRail = 18.0;
}

final class WorkstationLayoutSizes {
  const WorkstationLayoutSizes._();

  static const Size switchFrame = Size(86, 54);
  static const Size switchThumb = Size(32, 24);
}

final class WorkstationLayoutFractions {
  const WorkstationLayoutFractions._();

  /// Existing live token already expressed as a height fraction.
  static const double learningRailHeight = 0.25;

  /// Width candidates that can be resolved from viewport width and then clamped.
  static const double bootstrapMaxWidth =
      840.0 / WorkstationReferenceViewport.landscapeWidth;
  static const double utilityWideRailWidth =
      340.0 / WorkstationReferenceViewport.landscapeWidth;
  static const double utilitySupportRailWidth =
      260.0 / WorkstationReferenceViewport.landscapeWidth;
  static const double subjectSelectorWidthNarrow =
      280.0 / WorkstationReferenceViewport.landscapeWidth;
  static const double subjectSelectorWidthMedium =
      320.0 / WorkstationReferenceViewport.landscapeWidth;
  static const double subjectSelectorWidthWide =
      360.0 / WorkstationReferenceViewport.landscapeWidth;
  static const double subjectLeftRailWidthNarrow =
      388.0 / WorkstationReferenceViewport.landscapeWidth;
  static const double subjectLeftRailWidthWide =
      420.0 / WorkstationReferenceViewport.landscapeWidth;
  static const double keyValueLabelWidth =
      180.0 / WorkstationReferenceViewport.landscapeWidth;
  static const double currentStepLabelWidth =
      240.0 / WorkstationReferenceViewport.landscapeWidth;
  static const double detailLabelWidth =
      148.0 / WorkstationReferenceViewport.landscapeWidth;
  static const double inlineDetailLabelWidth =
      210.0 / WorkstationReferenceViewport.landscapeWidth;

  /// Height candidates that can be resolved from viewport height and then clamped.
  static const double gateStatusRowMinHeight =
      196.0 / WorkstationReferenceViewport.landscapeHeight;
  static const double gateStatusRowMaxHeight =
      248.0 / WorkstationReferenceViewport.landscapeHeight;
  static const double gateStatusStackHeight =
      128.0 / WorkstationReferenceViewport.landscapeHeight;
  static const double gateBaseHeight =
      68.0 / WorkstationReferenceViewport.landscapeHeight;
  static const double gatePrimaryStepContentHeight =
      60.0 / WorkstationReferenceViewport.landscapeHeight;
  static const double gateActionSectionTitleHeight =
      40.0 / WorkstationReferenceViewport.landscapeHeight;
  static const double gateActionSlotHeight =
      48.0 / WorkstationReferenceViewport.landscapeHeight;
  static const double gatePrefixedActionSlotHeight =
      64.0 / WorkstationReferenceViewport.landscapeHeight;
  static const double sourceDetailPreviewMaxHeight =
      216.0 / WorkstationReferenceViewport.landscapeHeight;

  /// These ratios already describe content geometry instead of fixed px.
  static const double paneAspectRatioSingleColumn = 1.85;
  static const double paneAspectRatioTwoColumn = 1.35;
}

/// Helper methods for the next refactor pass where width and height are driven
/// by viewport percentages instead of duplicated local hard-coded values.
///
/// Not every token should become a percentage:
/// - keep typography, border widths, icon sizes, and small control padding
///   absolute for readability and stable hit targets
/// - prefer percentage sizing for large rails, gate sections, preview regions,
///   and other macro layout blocks
final class WorkstationViewportSizing {
  const WorkstationViewportSizing._();

  static double bootstrapMaxWidth(double viewportWidth) =>
      viewportWidth * WorkstationLayoutFractions.bootstrapMaxWidth;

  static double subjectSelectorWidth(double viewportWidth) {
    final preferred = viewportWidth >= WorkstationLayoutBreakpoints.subjectTabSelectorWide
        ? viewportWidth * WorkstationLayoutFractions.subjectSelectorWidthWide
        : viewportWidth >= WorkstationLayoutBreakpoints.subjectTabSelectorMedium
        ? viewportWidth * WorkstationLayoutFractions.subjectSelectorWidthMedium
        : viewportWidth * WorkstationLayoutFractions.subjectSelectorWidthNarrow;
    return preferred.clamp(
      WorkstationLayoutWidths.subjectSelectorMin,
      WorkstationLayoutWidths.subjectSelectorMax,
    );
  }

  static double utilityRailWidth(double viewportWidth) =>
      (viewportWidth * WorkstationLayoutFractions.utilityWideRailWidth).clamp(
        WorkstationLayoutWidths.utilitySupportRail,
        WorkstationLayoutWidths.utilityWideRail,
      );

  static double subjectLeftRailWidth(
    double viewportWidth, {
    required bool wide,
  }) => (viewportWidth *
          (wide
              ? WorkstationLayoutFractions.subjectLeftRailWidthWide
              : WorkstationLayoutFractions.subjectLeftRailWidthNarrow))
      .clamp(
        WorkstationLayoutWidths.subjectLeftRailNarrow,
        WorkstationLayoutWidths.subjectLeftRailWide,
      );

  static double gateStatusRowHeight(double viewportHeight) =>
      (viewportHeight * WorkstationLayoutFractions.gateStatusRowMinHeight).clamp(
        WorkstationLayoutHeights.gateStatusRowMin,
        WorkstationLayoutHeights.gateStatusRowMax,
      );

  static double gateStatusStackHeight(double viewportHeight) =>
      (viewportHeight * WorkstationLayoutFractions.gateStatusStackHeight)
          .clamp(
            WorkstationLayoutHeights.gateStatusStack,
            WorkstationLayoutHeights.gateStatusRowMin,
          );

  static double sourceDetailPreviewMaxHeight(double viewportHeight) =>
      viewportHeight * WorkstationLayoutFractions.sourceDetailPreviewMaxHeight;

  static double learningRailHeight(double viewportHeight) =>
      viewportHeight * WorkstationLayoutFractions.learningRailHeight;
}
