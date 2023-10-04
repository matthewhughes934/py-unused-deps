# Changelog

## 0.4.0 - 2023-10-04

### Fixed

  - Fix `--exclude` not being respected both as an arg and in config (\#29)

### Removed

  - **Breaking** dropped support for Python 3.7 (\#28)

## 0.3.0 - 2023-04-14

### Changed

  - Add error when bad file path given (\#19)
  - Add `--no-distribution` and ensure exactly one of this an `--distribution`
    are specified (\#18)

## 0.2.1 - 2023-04-09

### Added

  - Add repository URL to package metadata (\#16)

## 0.2.0 - 2023-01-15

### Added

  - Add license (\#13)
  - Add ability to read from configuration file (\#11)
  - Add some file discovery so users can specify which files are included in a
    distribution, rather than trying to read this from package metadata (\#5)
  - Add some dogfeeding by including a run of `py-unused-deps` on itself in CI
    (\#4)

### Removed

  - Remove (somewhat) magic distribution detection (\#10)

### Changed

  - Make specifying a distribution optional (\#6)

## 0.1.0 - 2022-11-06

### Changed

  - Change distribution name from `unused-deps` to `py-unused-deps` (\#3)

## 0.0.1 - 2022-11-06

Initial release
