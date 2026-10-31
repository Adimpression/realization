# Realization Compatibility API

This distribution preserves explicitly supported historical Python import
identities and command adapters. New integrations should use the canonical
packages documented in `architecture/COMPATIBILITY_API.md`.

The compatibility distribution owns no canonical semantic, governance,
controller, runtime, exchange, or workstation behavior. Its public historical
modules alias or adapt those canonical owners under retained names. Private
command-support modules compose canonical parsers, handlers, and adapters for
the supported aggregate executable.
