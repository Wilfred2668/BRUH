"""Command-line interface for Bruh."""

import argparse
import sys
import os
import time
import stat
from pathlib import Path
from bruh import __version__
from bruh.config import LAST_SESSION_FILE, ensure_bruh_dir
from bruh.capture.context import CommandContext
from bruh.capture.session import SessionStore
from bruh.capture.history import get_last_command_from_history
from bruh.engine.matcher import DiagnosticEngine
from bruh.presentation.renderer import TerminalRenderer
from bruh.presentation.banner import render_welcome_screen, render_ready_screen
from bruh.presentation.ansi import bold, cyan, green, red, yellow, dim, divider
from bruh.shell.detector import ShellDetector
from bruh.shell.integration import ShellIntegration
from bruh.personality.phrases import (
    NO_ERROR_DETECTED_TITLE,
    NO_ERROR_DETECTED_MESSAGE,
    NO_SESSION_FOUND_TITLE,
    NO_SESSION_FOUND_MESSAGE
)

def has_piped_input() -> bool:
    """Check if stdin has piped data available without blocking."""
    try:
        if sys.stdin.isatty():
            return False

        if sys.platform == "win32":
            import msvcrt, ctypes
            from ctypes import wintypes
            try:
                handle = msvcrt.get_osfhandle(sys.stdin.fileno())
                avail = wintypes.DWORD()
                if ctypes.windll.kernel32.PeekNamedPipe(handle, None, 0, None, ctypes.byref(avail), None):
                    return avail.value > 0
            except Exception:
                return False

        # Unix / POSIX systems
        mode = os.fstat(sys.stdin.fileno()).st_mode
        if stat.S_ISFIFO(mode):
            import select
            r, _, _ = select.select([sys.stdin], [], [], 0.0)
            return bool(r)
        elif stat.S_ISREG(mode):
            return os.fstat(sys.stdin.fileno()).st_size > 0
    except Exception:
        pass
    return False

def run_diagnose(output_text: str, command: str = "", exit_code: int = 1) -> int:
    """Run diagnostic engine on output text and print rendered result."""
    engine = DiagnosticEngine()
    result = engine.diagnose(raw_output=output_text, command=command, exit_code=exit_code)
    rendered = TerminalRenderer.render(result)
    print(rendered)
    return 0

def handle_default(args: argparse.Namespace) -> int:
    """Handle default 'bruh' invocation."""
    # 1. Check direct text argument if passed via --text
    if getattr(args, "text", None):
        return run_diagnose(args.text, command="<direct-input>", exit_code=1)

    # 2. Check if input is piped into stdin
    if getattr(args, "pipe", False) or has_piped_input():
        try:
            piped_input = sys.stdin.read()
            if piped_input.strip():
                return run_diagnose(piped_input, command="<piped-input>", exit_code=1)
        except Exception:
            pass

    # 3. Read recorded shell session and latest shell history
    store = SessionStore(LAST_SESSION_FILE)
    session = store.load()
    last_hist_cmd, hist_mtime = get_last_command_from_history()

    target_cmd = None
    target_output = ""
    target_exit_code = 1
    target_cwd = os.getcwd()

    now = time.time()
    session_is_fresh = bool(session and (now - session.timestamp) < 300.0)

    from bruh.capture.history import isolate_command_before_bruh, is_multiline_fragment

    if session and session_is_fresh and session.command:
        clean_session_cmd = isolate_command_before_bruh(session.command)
        clean_hist_cmd = isolate_command_before_bruh(last_hist_cmd) if last_hist_cmd else None

        # If history contains a different, strictly newer command than recorded session (> 1.0s newer)
        if clean_hist_cmd and (hist_mtime - session.timestamp) > 1.0 and clean_hist_cmd != clean_session_cmd:
            target_cmd = clean_hist_cmd
            target_output = ""
            target_exit_code = 1
            target_cwd = os.getcwd()
        else:
            target_cmd = clean_session_cmd
            target_output = session.output.strip()
            target_exit_code = session.exit_code
            target_cwd = session.cwd or os.getcwd()
    elif last_hist_cmd:
        target_cmd = isolate_command_before_bruh(last_hist_cmd)
        target_cwd = os.getcwd()

    if target_cmd:
        target_cmd = isolate_command_before_bruh(target_cmd)
        if target_cmd and (target_cmd.startswith('"@') or target_cmd.startswith("'@")):
            reconstructed, _ = get_last_command_from_history()
            if reconstructed and (reconstructed.startswith('@"') or reconstructed.startswith("@'")):
                target_cmd = reconstructed

    if not target_cmd:
        print(divider())
        print(f"\n   {bold(yellow(NO_SESSION_FOUND_TITLE))}\n")
        print(f"   {NO_SESSION_FOUND_MESSAGE}\n")
        print(divider())
        return 0

    # Check if output contains an explicit HTTP failure (e.g. HTTP/1.1 502 Bad Gateway, 401 Unauthorized, etc.)
    import re
    is_http_failure = bool(re.search(r"HTTP/[123](?:\.\d)?\s+[45]\d{2}\b", target_output, re.I))

    # Fast path: If active shell session recorded exit code 0 without errors, it succeeded!
    success_markers = ["everything up-to-date", "everything up to date", "on branch", "already up to date", "nothing to commit"]
    out_lower = target_output.lower()
    if session and session_is_fresh and session.exit_code == 0 and not is_http_failure:
        if not target_output or any(m in out_lower for m in success_markers) or not any(err_kw in out_lower for err_kw in ["error:", "fatal:", "failed", "enoent", "exception"]):
            print(TerminalRenderer.render_success(command=target_cmd))
            return 0

    # If the captured string is an unparseable multiline fragment that failed, fail safely
    if is_multiline_fragment(target_cmd):
        print(TerminalRenderer.render_unreliable_capture(command=target_cmd))
        return 0

    # If output is missing, execute target_cmd in sandbox to determine live exit code & error
    if not target_output:
        try:
            import subprocess
            is_pwsh_cmd = (
                (session and session.shell == "powershell")
                or "\n" in target_cmd
                or "'" in target_cmd
                or target_cmd.startswith('@"')
                or target_cmd.startswith("@'")
                or "Set-Content" in target_cmd
                or "|" in target_cmd
                or "$" in target_cmd
            )
            use_pwsh = sys.platform == "win32" and is_pwsh_cmd
            if use_pwsh:
                proc = subprocess.run(
                    ["powershell", "-NoProfile", "-NonInteractive", "-Command", target_cmd],
                    capture_output=True,
                    text=True,
                    timeout=6,
                    cwd=target_cwd if target_cwd and Path(target_cwd).exists() else None
                )
            else:
                proc = subprocess.run(
                    target_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=6,
                    cwd=target_cwd if target_cwd and Path(target_cwd).exists() else None
                )
            out_captured = (proc.stderr + "\n" + proc.stdout).strip()
            if out_captured:
                target_output = out_captured
            # Preserve failure exit code from real interactive session
            if session and session.command == target_cmd and session.exit_code != 0:
                target_exit_code = session.exit_code
            else:
                target_exit_code = proc.returncode

            store.save(CommandContext(
                command=target_cmd,
                exit_code=target_exit_code,
                output=target_output,
                cwd=target_cwd
            ))
        except Exception:
            pass

    # Re-check HTTP failure in captured output
    is_http_failure = bool(re.search(r"HTTP/[123](?:\.\d)?\s+[45]\d{2}\b", target_output, re.I))

    # Exit code 0 means success ONLY when no explicit HTTP failure or error is present
    out_lower = target_output.lower()
    if not is_http_failure and target_exit_code == 0:
        if (not target_output) or any(m in out_lower for m in success_markers) or not any(err_kw in out_lower for err_kw in ["error:", "fatal:", "failed", "enoent", "exception", "could not resolve", "econnrefused", "timeouterror", "connectionrefused"]):
            print(TerminalRenderer.render_success(command=target_cmd))
            return 0

    if not target_output:
        target_output = f"Command '{target_cmd}' failed with exit status {target_exit_code}"

    return run_diagnose(target_output, command=target_cmd, exit_code=target_exit_code)

def handle_setup(args: argparse.Namespace) -> int:
    """Handle 'bruh setup' command with polished first-run welcome experience."""
    detected_shell, profile_path = ShellDetector.detect_shell()
    welcome_banner = render_welcome_screen(detected_shell)
    print(welcome_banner)

    # Interactive prompt if in terminal and not forced with -y
    if sys.stdin.isatty() and not getattr(args, "yes", False):
        try:
            input("\n   Press Enter to set up Bruh (or Ctrl+C to cancel)... ")
        except (KeyboardInterrupt, EOFError):
            print("\nSetup cancelled.")
            return 1

    success, msg = ShellIntegration.install(detected_shell)
    if success:
        print(f"\n   {green(msg)}\n")
        print(render_ready_screen())
        return 0
    else:
        print(f"\n   {red('Notice:')} {msg}\n")
        print(f"   You can manually add this hook to your shell profile:\n")
        script = ShellIntegration.get_init_script(detected_shell)
        print(f"   {dim(script)}\n")
        return 1

def handle_init(args: argparse.Namespace) -> int:
    """Handle 'bruh init <shell>' command to print hook script for eval."""
    shell = args.shell or ShellDetector.detect_shell()[0]
    script = ShellIntegration.get_init_script(shell)
    print(script)
    return 0

def handle_record(args: argparse.Namespace) -> int:
    """Record command execution outcome (used by shell hooks)."""
    output_content = ""
    if args.output:
        output_content = args.output
    elif args.file and Path(args.file).exists():
        try:
            output_content = Path(args.file).read_text(encoding="utf-8", errors="replace")
        except Exception:
            pass

    ctx = CommandContext(
        command=args.command or "",
        exit_code=int(args.exit_code) if args.exit_code is not None else 1,
        output=output_content,
        cwd=args.cwd or os.getcwd(),
        shell=args.shell or ""
    )
    store = SessionStore(LAST_SESSION_FILE)
    success = store.save(ctx)
    return 0 if success else 1

def handle_check(args: argparse.Namespace) -> int:
    """Display diagnostic tool status, detected shell, and registry rules."""
    detected_shell, profile_path = ShellDetector.detect_shell()
    engine = DiagnosticEngine()
    rules = engine.registry.all_rules()

    print(divider())
    print(f"   {bold(cyan('Bruh Diagnostic Status'))} (v{__version__})\n")
    print(f"   • Detected Shell:       {bold(detected_shell)}")
    print(f"   • Shell Profile Path:   {profile_path or 'Not found'}")
    print(f"   • Session File Path:    {LAST_SESSION_FILE}")
    print(f"   • Registered Patterns:  {len(rules)} active diagnostic rules\n")
    print("   Active Rules:")
    for r in rules:
        print(f"     - [{r.category:10s}] {r.rule_id:24s} (priority {r.priority})")
    print(divider())
    return 0

def create_parser() -> argparse.ArgumentParser:
    """Construct CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="bruh",
        description="Because your terminal clearly isn't going to explain itself.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("-v", "--version", action="version", version=f"bruh {__version__}")
    parser.add_argument("-t", "--text", help="Directly diagnose an error string", type=str)
    parser.add_argument("-p", "--pipe", action="store_true", help="Read error output directly from stdin pipe")

    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # setup
    setup_parser = subparsers.add_parser("setup", help="Interactive first-run setup & shell integration")
    setup_parser.add_argument("-y", "--yes", action="store_true", help="Non-interactive setup")

    # init
    init_parser = subparsers.add_parser("init", help="Generate shell integration script for eval/sourcing")
    init_parser.add_argument("shell", nargs="?", default="powershell", help="Target shell (powershell, bash, zsh)")

    # check / status
    subparsers.add_parser("check", help="Check Bruh status and registered rules")
    subparsers.add_parser("status", help="Check Bruh status and registered rules")

    # explain
    explain_parser = subparsers.add_parser("explain", help="Explain an error text passed as argument")
    explain_parser.add_argument("error_text", nargs="+", help="The raw error text or stack trace to explain")

    # record
    record_parser = subparsers.add_parser("record", help="Internal command for recording shell failures")
    record_parser.add_argument("--command", "-c", type=str, default="")
    record_parser.add_argument("--exit-code", "-e", type=int, default=1)
    record_parser.add_argument("--output", "-o", type=str, default="")
    record_parser.add_argument("--file", "-f", type=str, default="")
    record_parser.add_argument("--cwd", type=str, default="")
    record_parser.add_argument("--shell", type=str, default="")

    return parser

def handle_exec_command(cmd_args: list) -> int:
    """Execute a command directly and explain any diagnostic failure immediately."""
    import subprocess
    cmd_str = " ".join(cmd_args)
    cwd = os.getcwd()

    is_pwsh_cmd = (
        sys.platform == "win32"
        and (
            "'" in cmd_str
            or "\n" in cmd_str
            or cmd_str.startswith('@"')
            or cmd_str.startswith("@'")
            or "Set-Content" in cmd_str
            or "|" in cmd_str
            or "$" in cmd_str
        )
    )

    try:
        if is_pwsh_cmd:
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd_str],
                capture_output=True,
                text=True
            )
        else:
            proc = subprocess.run(
                cmd_args if sys.platform != "win32" else cmd_str,
                shell=(sys.platform == "win32"),
                capture_output=True,
                text=True
            )

        combined_output = (proc.stderr + "\n" + proc.stdout).strip()
        exit_code = proc.returncode

        # Save session so subsequent 'bruh' also remembers
        store = SessionStore(LAST_SESSION_FILE)
        store.save(CommandContext(
            command=cmd_str,
            exit_code=exit_code,
            output=combined_output,
            cwd=cwd
        ))

        if exit_code == 0:
            print(TerminalRenderer.render_success(command=cmd_str))
            return 0
        else:
            return run_diagnose(combined_output or f"Command failed with exit code {exit_code}", command=cmd_str, exit_code=exit_code)

    except Exception as e:
        print(divider())
        print(f"\n   {bold(red('Error executing command:'))} {e}\n")
        print(divider())
        return 1

def main() -> int:
    """Main entry point."""
    # Ensure stdout/stderr handle UTF-8 cleanly across Windows terminals
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    # Check if arguments represent a direct command invocation (e.g. bruh python app.py)
    KNOWN_COMMANDS = {"setup", "init", "check", "status", "explain", "record"}
    if len(sys.argv) > 1:
        first_arg = sys.argv[1]
        if first_arg not in KNOWN_COMMANDS and not first_arg.startswith("-"):
            return handle_exec_command(sys.argv[1:])

    parser = create_parser()
    args = parser.parse_args()

    if args.subcommand == "setup":
        return handle_setup(args)
    elif args.subcommand == "init":
        return handle_init(args)
    elif args.subcommand in ("check", "status"):
        return handle_check(args)
    elif args.subcommand == "explain":
        text = " ".join(args.error_text) if isinstance(args.error_text, list) else args.error_text
        return run_diagnose(text, command="<explicit-input>", exit_code=1)
    elif args.subcommand == "record":
        return handle_record(args)
    else:
        return handle_default(args)

if __name__ == "__main__":
    sys.exit(main())
