# Bruh

```
   ██████╗ ██████╗ ██╗   ██╗██╗  ██╗
   ██╔══██╗██╔══██╗██║   ██║██║  ██║
   ██████╔╝██████╔╝██║   ██║███████║
   ██╔══██╗██╔══██╗██║   ██║██╔══██║
   ██████╔╝██║  ██║╚██████╔╝██║  ██║
   ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝
```

> **Bruh — because your terminal clearly isn't going to explain itself.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](#supported-platforms)
[![Privacy: 100% Local](https://img.shields.io/badge/privacy-100%25%20local-green.svg)](#privacy--architecture)

**BRUH** is a local developer error-diagnostic CLI that turns confusing compiler, runtime, system, and tooling errors into clear explanations and actionable suggestions.

---

## The Experience

Run your commands normally. If anything breaks, simply type `bruh`:

```bash
$ python app.py
# ...command fails with an error...

$ bruh
```

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                                BRUH                                

💀 ModuleNotFoundError

   No module named 'pandas'

📍 Where
   app.py:15

🤨 Bruh, what happened?

   Python tried to import 'pandas', but it isn't available in the
   active Python environment.

🔧 Try this

   1. Check the import statement for typos: 'pandas'.
   2. Make sure your virtual environment (venv/conda) is activated.
   3. If not installed, install it: `pip install pandas`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Features

- **48 Built-In Diagnostic Rules**: Comprehensive diagnostic coverage across TypeScript compiler errors, Python exceptions, Node.js runtimes, Git conflicts, networking, and system errors.
- **Deterministic & Instant**: Pure local pattern recognition with zero external runtime dependencies, zero network latency, and sub-millisecond execution.
- **Zero Hallucination Policy**: If an error is unknown or ambiguous, BRUH reports verified facts (file, line number, exception type) rather than guessing a root cause.
- **100% Local & Privacy-First**: Zero telemetry, zero tracking, no cloud APIs, and zero LLM dependencies.
- **Seamless Shell Integration**: Automatic hooks for PowerShell, Bash, and Zsh that capture the last failed command context without requiring piping.
- **Dual Distribution**: Available via PyPI (`pip` / `pipx`) for cross-platform workflows and as a standalone Windows executable (`bruh.exe`) requiring zero Python installation.

---

## Installation

### Option A: Install via pipx (Recommended for Python Users)

Install in an isolated global environment with [pipx](https://pypa.github.io/pipx/):

```bash
pipx install bruh
```

Or via standard `pip`:

```bash
pip install bruh
```

---

### Option B: Standalone Windows Executable (Zero Python Required)

For Windows users without a Python environment:

1. Download `bruh.exe` from the latest [GitHub Releases](https://github.com/Wilfred2668/BRUH/releases).
2. Place `bruh.exe` into any directory on your system `PATH` (e.g. `C:\Users\<User>\bin` or `C:\Program Files\bruh`).
3. Verify in PowerShell or Command Prompt:

```powershell
bruh --help
```

---

### Shell Hook Setup (Optional but Recommended)

Enable automatic failure capture for your interactive shell:

```bash
bruh setup
```

BRUH automatically detects your shell (**PowerShell**, **Bash**, or **Zsh**) and installs a lightweight local hook into your shell profile.

---

## Usage Modes

BRUH supports several intuitive ways to diagnose errors:

### 1. Default Post-Hoc Diagnostic
Run commands normally. If anything fails, type `bruh` to diagnose the last failure:

```bash
python app.py
bruh
```

### 2. Direct Command Wrapper
Execute any script or compiler directly through `bruh`. If it fails, BRUH diagnoses it immediately:

```bash
bruh python script.py
bruh npm run build
bruh npx tsc app.ts --noEmit
```

### 3. Direct Error Explanation
Pass any raw error message or stack trace string:

```bash
bruh explain "TypeError: Cannot read properties of undefined (reading 'id')"
bruh explain "test.ts(2,5): error TS2322: Type 'string' is not assignable to type 'number'."
```

### 4. Piped Standard Input
Pipe build logs or compiler outputs directly:

```bash
cat error.log | bruh
npx tsc | bruh
```

### 5. Check Health & Active Patterns
Verify your installation and active diagnostic rules:

```bash
bruh check
```

---

## Supported Diagnostics

BRUH currently contains **48 deterministic diagnostic rules**:

- **TypeScript Compiler (tsc)**:
  - Type mismatches (`TS2322`, `TS2345`), property not found (`TS2339`), cannot find name (`TS2304`, `TS2552`)
  - Missing modules & `@types` (`TS2307`, `TS2792`), argument count mismatches (`TS2554`, `TS2555`)
  - Implicit any (`TS7006`, `TS7005`, `TS7008`, `TS7034`, `TS7053`), missing return paths (`TS2355`, `TS2366`, `TS7030`)
  - Null/undefined checks (`TS18047`, `TS18048`, `TS2531`, `TS2532`), readonly/const assignment (`TS2540`, `TS2588`)
  - Interface inheritance & abstract members (`TS2420`, `TS2515`, `TS2416`), index signatures (`TS2411`), syntax & async/await (`TS1005`, `TS1308`, `TS1375`)
- **Python Runtime & Syntax**:
  - `ModuleNotFoundError`, `ImportError`, circular imports
  - `TypeError`, `ValueError`, `KeyError`, `IndexError`, `NameError`, `UnboundLocalError`, `ZeroDivisionError`
  - `SyntaxError`, `IndentationError`, `JSONDecodeError`, subprocess failures
- **JavaScript / Node.js**:
  - `ReferenceError` (including Temporal Dead Zone), `TypeError` (null/undefined/non-callable), `RangeError`
  - `SyntaxError` (unexpected tokens, JSON.parse errors), `MODULE_NOT_FOUND` (local files and npm packages)
- **Domain Subsystems**:
  - **Git**: Push rejections, unrelated histories, detached HEAD, missing repositories
  - **Networking & Databases**: `ECONNREFUSED`, port conflicts (`EADDRINUSE`), PostgreSQL, MySQL, Redis, SQLite locks
  - **Package Managers**: npm peer dependency conflicts (`ERESOLVE`), pip missing distribution errors
  - **HTTP**: `502 Bad Gateway`, `504 Gateway Timeout`, `401 Unauthorized`, client timeouts
- **System**:
  - Command not found (PowerShell, Bash, CMD), file not found (`ENOENT`, `Errno 2`), permission denied (`EACCES`, `Errno 13`)

---

## How It Works

BRUH operates via a simple 3-stage local pipeline:

```text
┌─────────────────────────┐     ┌─────────────────────────┐     ┌─────────────────────────┐
│   1. Local Capture      │ ──► │  2. Match & Extract     │ ──► │  3. Format & Render     │
│  Shell hook / wrapper / │     │  Deterministic priority │     │  Clean dark-mode ANSI   │
│  stdin pipeline / input │     │  variable extraction    │     │  explanation & fixes    │
└─────────────────────────┘     └─────────────────────────┘     └─────────────────────────┘
```

1. **Capture**: Reads command exit status and error streams from the local session (`~/.bruh/last_session.json`), direct execution wrapper, or standard input.
2. **Match & Extract**: Evaluates inputs against priority-tiered diagnostic rules, extracting dynamic variables (filenames, line numbers, missing packages, types, ports).
3. **Render**: Produces formatted terminal output explaining what happened and providing concrete remediation steps.

---

## Supported Platforms

- **Windows** (PowerShell 5.1+, PowerShell 7+, Command Prompt, Windows Terminal)
- **Linux** (Bash, Zsh)
- **macOS** (Zsh, Bash)

*Note: The standalone `bruh.exe` executable is Windows-native. Python/PyPI installations (`pip` / `pipx`) are fully cross-platform across Windows, Linux, and macOS.*

---

## Privacy & Architecture

- **100% Local**: No network requests, no remote logging, no cloud dependencies.
- **Zero Telemetry**: No tracking, metrics, or usage analytics.
- **Zero Runtime Dependencies**: The core Python package runs exclusively on the standard library.
- **Deterministic**: Pure pattern-matching rules ensure consistent, repeatable diagnoses.

---

## Development

```bash
# Clone the repository
git clone https://github.com/Wilfred2668/BRUH.git
cd BRUH

# Install in editable mode
pip install -e .

# Run the complete test suite (238 tests)
python -m unittest discover -s tests -p "test_*.py" -v
```

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
