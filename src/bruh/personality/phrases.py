"""Centralized strings, titles, and layout constants for Bruh."""

# Section titles & branding
TITLE_BRAND = "BRUH"
TITLE_UNKNOWN = "⚠️  I don't recognize this error yet."
TITLE_WHERE = "📍 Where"
TITLE_WHAT_HAPPENED = "🤨 Bruh, what happened?"
TITLE_TRY_THIS = "🔧 Try this"

# First-run & Setup banners
WELCOME_SUBTITLE = "Because your terminal clearly isn't going to explain itself."
SETUP_FEATURES = [
    "✓ Local-first (100% offline)",
    "✓ Zero telemetry or tracking",
    "✓ No account or API keys required",
    "✓ Fast pattern-based diagnostics",
]

# No error detected / last command succeeded
NO_ERROR_DETECTED_TITLE = "✓ You're good."
NO_ERROR_DETECTED_MESSAGE = (
    "The last command completed successfully.\nNothing new to diagnose."
)

NO_SESSION_FOUND_TITLE = "👀 No previous command found."
NO_SESSION_FOUND_MESSAGE = (
    "Bruh didn't find a recorded command. Run a command in your terminal first."
)

UNRELIABLE_CAPTURE_TITLE = "⚠️ Bruh couldn't capture the previous command reliably."
UNRELIABLE_CAPTURE_MESSAGE = (
    "The previous command appeared to be an interactive or multiline construct.\n"
    "Run `bruh explain \"<error>\"` or pipe the output (`command | bruh`)."
)
