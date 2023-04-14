# v0.3.0 - 2023-04-14

  - Add error when bad file path given
      - \#19 PR
  - Add `--no-distribution` and ensure exactly one of this an `--distribution`
    are specified
      - \#18 PR

# v0.2.1 - 2023-04-09

  - Add repository URL to package metadata
      - \#16 PR

# v0.2.0 - 2023-01-15

  - Add license
      - \#13 PR
  - Add ability to read from configuration file
      - \#11 PR
  - Remove (somewhat) magic distribution detection
      - \#10 PR
  - Make specifying a distribution optional.
      - \#6 PR
  - Add some file discovery so users can specify which files are included in a
    distribution, rather than trying to read this from package metadata
      - \#5 PR
  - Add some dogfeeding by including a run of `py-unused-deps` on itself in CI
      - \#4 PR

# v0.1.0 - 2022-11-06

  - Change distribution name from `unused-deps` to `py-unused-deps`
      - \#3 PR

# v0.0.1 - 2022-11-06

  - Initial release
