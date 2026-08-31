"""Diagnostic rule for database connection, authentication, and query errors."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch
from bruh.engine.extractors import FactExtractor

DB_ERR_REGEX = re.compile(
    r"(?:(?:password authentication failed for user ['\"](?P<pg_user>[^'\"]+)['\"])|"
    r"(?:Access denied for user ['\"](?P<my_user>[^'\"]+)['\"]@)|"
    r"(?:database ['\"](?P<missing_db>[^'\"]+)['\"] does not exist)|"
    r"(?:Unknown database ['\"](?P<missing_my_db>[^'\"]+)['\"])|"
    r"(?:relation ['\"](?P<missing_table>[^'\"]+)['\"] does not exist)|"
    r"(?:Table ['\"](?P<missing_my_table>[^'\"]+)['\"] doesn't exist)|"
    r"(?:database is locked)|"
    r"(?:Redis connection to (?P<redis_host>[^\s]+) failed))",
    re.IGNORECASE
)

class DatabaseErrorRule(BaseDiagnosticRule):
    """Diagnoses database authentication, missing tables, and connection issues."""

    rule_id = "database-error"
    name = "Database Error"
    category = "database"
    priority = 78

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        if exit_code == 0:
            return None

        match = DB_ERR_REGEX.search(cleaned_output)
        if match:
            db_type = FactExtractor.extract_database_type(cleaned_output) or "Database"
            raw_err = match.group(0).strip()
            
            user = match.group("pg_user") or match.group("my_user")
            missing_db = match.group("missing_db") or match.group("missing_my_db")
            missing_table = match.group("missing_table") or match.group("missing_my_table")

            if user:
                title = f"💀 {db_type}: Authentication Failed"
            elif missing_db:
                title = f"💀 {db_type}: Database '{missing_db}' Not Found"
            elif missing_table:
                title = f"💀 {db_type}: Table '{missing_table}' Not Found"
            elif "locked" in raw_err.lower():
                title = f"💀 {db_type}: Database Is Locked"
            else:
                title = f"💀 {db_type} Connection Error"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={
                    "db_type": db_type,
                    "user": user,
                    "missing_db": missing_db,
                    "missing_table": missing_table,
                    "raw": raw_err
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        db = vars.get("db_type", "The database")
        user = vars.get("user")
        missing_db = vars.get("missing_db")
        missing_table = vars.get("missing_table")

        if "locked" in (vars.get("raw") or "").lower():
            return "Your program tried to write to SQLite while another connection was holding a lock."
        if user:
            return f"{db} rejected the password or username for '{user}'."
        if missing_db:
            return f"{db} cannot find the database '{missing_db}'."
        if missing_table:
            return f"{db} cannot find the table '{missing_table}'."
        return f"{db} refused the connection or encountered a query error."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        db = vars.get("db_type", "database")
        user = vars.get("user")
        missing_db = vars.get("missing_db")
        missing_table = vars.get("missing_table")

        if "locked" in (vars.get("raw") or "").lower():
            return [
                "Close the other program using the database.",
                "Make sure another connection is not keeping a transaction open.",
                "Add retry handling if simultaneous access is expected."
            ]
        if user:
            return [
                "Check the database username and password in your .env or configuration file.",
                f"Verify that user '{user}' exists and has permissions on the target database.",
                "Ensure your database server is running."
            ]
        if missing_db:
            return [
                f"Check for typos in the database name: '{missing_db}'.",
                f"Create the database before connecting (e.g. `CREATE DATABASE {missing_db};`).",
                "Check your .env or database connection URL."
            ]
        if missing_table:
            return [
                "Run your database migrations to create the missing tables.",
                f"Check for spelling errors in the table name '{missing_table}'.",
                "Verify that you connected to the correct database schema."
            ]
        return [
            f"Make sure your {db} server is running locally or in Docker.",
            "Verify your database host, port, and connection settings.",
            "Check database service logs for more details."
        ]
