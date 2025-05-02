# Contributing to BlenDR

First of all, thanks to everyone for taking the time to contribute to BlenDR. If you do - every fix, feature, and suggestion helps build a better tool for the modding community.

---

## Table of Contents

- [Before You Start](#before-you-start)
- [Project Setup](#project-setup)
- [Coding Guidelines](#coding-guidelines)
- [File Format Compliance](#file-format-compliance)
- [Submitting Changes](#submitting-changes)
- [Bug Reports](#bug-reports)
- [License](#license)
- [Contact](#contact)

---

## Before You Start

- BlenDR targets modding file formats like `.odr`, `.mesh`, `.wdr`, and `.col`. You should have working knowledge of at least one.
- Python 3.10+ is required. Blender must be version 3.0+ with the `bpy` module accessible.
- Use `git` for version control and fork this repository before making changes.

---

## Project Setup

To start development:

1. Clone your fork:

   ```bash
   git clone https://github.com/yourusername/BlenDR.git
   cd BlenDR
   ```

2. Open Blender and install the add-on:

   - Go to **Edit > Preferences > Add-ons > Install**.
   - Select the `.zip` or folder containing `__init__.py`.
   - Enable "BlenDR" in the Add-ons list.

3. Enable developer extras in Blender's preferences for easier debugging.

---

## Coding Guidelines

- **Do not use brevity**. Write code explicitly and clearly, even if verbose.
- Every function must have a clear purpose and complete implementation — no placeholder logic.
- Avoid vague names or comments like `// fix this later`. All code should be production-ready.
- `print()` statements are allowed for meaningful debug output, not filler. Label them properly or remove them before merging.
- Use `snake_case` for all variables and function names.
- Avoid hardcoding values. Use constants, enums, or config files when possible.
- Never rely on inferred behavior when parsing binary files — document all offsets and assumptions.
- Always validate inputs, especially when reading from raw file bytes or headers.

---

## File Format Compliance

When working with supported formats:

- `.odr` must maintain Rockstar's LOD layout and material naming conventions.
- `.mesh` should preserve vertex ordering and triangle integrity.
- `.wdr` binary parsing must account for header alignment, compressed blocks, and pointer-based jumps.
- Always test round-trip imports and exports: import, then export again, and verify binary consistency.

For WDR or COL contributions:
- Document all offsets and struct layouts clearly.
- Do not include speculative or unverified offset guesses in commit history.

---

## Submitting Changes

1. Fork the repository and create your branch:

   ```bash
   git checkout -b feature-name
   ```

2. Commit with clear messages:

   ```bash
   git commit -m "Add support for LOD radius parsing in ODR exporter"
   ```

3. Push to your fork and submit a pull request:

   ```bash
   git push origin feature-name
   ```

4. Use PR titles that reflect what your code *does* (not just "fix" or "update").

All PRs are reviewed for:
- Binary accuracy
- Compatibility with Rockstar formats
- Code clarity and structure
- Zero placeholder logic (unless in *rare* cases)

---

## Bug Reports

If you encounter issues:

1. Create a GitHub issue.
2. Include:
   - Game/platform (e.g. GTA IV, VCS)
   - File type and example file (attach or link if legal)
   - Blender version
   - Stack trace or console output if available

Please don’t post vague reports or AI guesses — include exact byte offsets, screenshots, or hex dumps where possible.

---

## License

This project is under the GNU GPLv3 license. By contributing, you agree to license your contributions under this license.

---

## Contact

Maintainer: [@spicybung](https://github.com/spicybung)

For advanced file format help or integration, open a GitHub issue or discussion thread.
