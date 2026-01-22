# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [0.1.4] - 2026-01-21

Increasing the default clipboard size limit.

### Added

### Changed

### Fixed

## [0.1.3] - 2026-01-21

This release is only there to push the new logo.

### Added

### Changed

### Fixed

## [0.1.2] - 2026-01-19

Fix annoying bug, easy sub-tree export, and starting backwards compatibilty.

### Added

Backwards compatibility is now a goal.
Starting with this version, matching major, smaller-or-equal minor, and any path version can be imported.

Note that this doesn't (yet) change the strict Blender version requirement.

### Changed

The tree that is currently visible is the one being exported, not the root tree.
This makes it more intuitive and easier to export sub-trees.

### Fixed

If the editor displayed a sub-tree, the import still happened on the root (parent) tree.

## [0.1.1] - 2026-01-08

Minor fixes and improvements.

### Added

Addon preferences for max clipboard size and advanced options.

### Changed

The export and import have one less pop-up to click through if the advanced options are hidden.
This is the default.
The import still has one if there are external items to be set.

### Fixed

- Clipboard size limit check makes crashes with very large exports less likely.
- Fixed wrong export of the "Subsurface IOR" default value.

## [0.1.0] - 2026-01-06

Initial release of the extension and package.

### Added

### Changed

### Fixed