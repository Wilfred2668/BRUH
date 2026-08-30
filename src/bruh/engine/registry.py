"""Rule registry for loading and querying diagnostic rules."""

from typing import List, Dict, Type
from bruh.rules.base import BaseDiagnosticRule

# =============================================================================
# TIER 1 (Priority 95-80): Package Management & System Execution
# Specific package manager distributions, uninstalled modules, port collisions
# =============================================================================
from bruh.rules.domains.packages.package_not_found import PackageNotFoundRule
from bruh.rules.languages.typescript.modules.ts_module_not_found import TSModuleNotFoundRule
from bruh.rules.languages.python.imports.module_not_found import ModuleNotFoundRule
from bruh.rules.languages.javascript.imports.js_module_not_found import JSModuleNotFoundRule
from bruh.rules.languages.python.imports.import_error import ImportErrorRule
from bruh.rules.domains.networking.port_in_use import PortInUseRule
from bruh.rules.system.shell.command_not_found import CommandNotFoundRule

# =============================================================================
# TIER 2 (Priority 79-75): Domain & Infrastructure Errors
# Database connectivity/auth, HTTP endpoints, subprocess execution, JSON decode
# =============================================================================
from bruh.rules.languages.typescript.types.ts_null_undefined import TSNullUndefinedRule
from bruh.rules.languages.typescript.types.ts_readonly_assignment import TSReadonlyAssignmentRule
from bruh.rules.languages.typescript.compiler.ts_missing_return import TSMissingReturnRule
from bruh.rules.languages.typescript.compiler.ts_class_inheritance import TSClassInheritanceRule
from bruh.rules.languages.typescript.types.ts_type_constraint import TSTypeConstraintRule
from bruh.rules.languages.typescript.syntax.ts_async_await import TSAsyncAwaitRule
from bruh.rules.languages.typescript.types.ts_type_mismatch import TSTypeMismatchRule
from bruh.rules.languages.typescript.types.ts_property_not_found import TSPropertyNotFoundRule
from bruh.rules.languages.typescript.compiler.ts_cannot_find_name import TSCannotFindNameRule
from bruh.rules.languages.typescript.compiler.ts_argument_count import TSArgumentCountRule
from bruh.rules.languages.typescript.types.ts_implicit_any import TSImplicitAnyRule
from bruh.rules.languages.typescript.types.ts_element_implicit_any import TSElementImplicitAnyRule
from bruh.rules.languages.typescript.types.ts_unintentional_comparison import TSUnintentionalComparisonRule
from bruh.rules.languages.typescript.types.ts_index_signature_mismatch import TSIndexSignatureMismatchRule
from bruh.rules.languages.typescript.types.ts_missing_required_property import TSMissingRequiredPropertyRule
from bruh.rules.languages.typescript.syntax.ts_syntax_error import TSSyntaxErrorRule
from bruh.rules.languages.javascript.data.js_json_parse_error import JSJSONParseErrorRule
from bruh.rules.languages.javascript.runtime.js_reference_error import JSReferenceErrorRule
from bruh.rules.languages.javascript.runtime.js_type_error import JSTypeErrorRule
from bruh.rules.languages.javascript.syntax.js_syntax_error import JSSyntaxErrorRule
from bruh.rules.domains.database.database_error import DatabaseErrorRule
from bruh.rules.languages.python.data.json_decode_error import JSONDecodeErrorRule
from bruh.rules.languages.python.subprocess.subprocess_error import SubprocessErrorRule
from bruh.rules.languages.javascript.runtime.js_range_error import JSRangeErrorRule
from bruh.rules.languages.python.runtime.recursion_error import RecursionErrorRule
from bruh.rules.languages.python.runtime.zero_division_error import ZeroDivisionErrorRule
from bruh.rules.languages.python.runtime.key_error import KeyErrorRule
from bruh.rules.languages.python.runtime.index_error import IndexErrorRule
from bruh.rules.languages.python.runtime.name_error import NameErrorRule
from bruh.rules.domains.http.http_client_error import HttpClientErrorRule
from bruh.rules.domains.http.http_error import HttpErrorRule

# =============================================================================
# TIER 3 (Priority 74-60): General Runtime & Filesystem Errors
# Type/value mismatches, attribute lookups, connection resets, file/dir missing
# =============================================================================
from bruh.rules.languages.python.runtime.type_error import TypeErrorRule
from bruh.rules.languages.python.runtime.value_error import ValueErrorRule
from bruh.rules.languages.python.runtime.runtime_attribute_error import RuntimeAttributeErrorRule
from bruh.rules.domains.networking.connection_refused import ConnectionRefusedRule
from bruh.rules.system.permissions.permission_denied import PermissionDeniedRule
from bruh.rules.system.filesystem.directory_not_found import DirectoryNotFoundRule
from bruh.rules.system.filesystem.file_not_found import FileNotFoundRule

# =============================================================================
# TIER 4 (Priority 59-30): Parsing, Dependency Conflicts & Version Control
# Syntax errors, dependency tree resolution, git sync/merge/push conflicts
# =============================================================================
from bruh.rules.domains.packages.dependency_conflict import DependencyConflictRule
from bruh.rules.languages.python.syntax.syntax_error import SyntaxErrorRule
from bruh.rules.domains.git.git_errors import GitErrorRule

# Complete built-in rules ordered by priority tier
BUILTIN_RULES: List[Type[BaseDiagnosticRule]] = [
    PackageNotFoundRule,
    TSModuleNotFoundRule,
    ModuleNotFoundRule,
    JSModuleNotFoundRule,
    ImportErrorRule,
    PortInUseRule,
    CommandNotFoundRule,
    TSIndexSignatureMismatchRule,
    TSMissingRequiredPropertyRule,
    TSNullUndefinedRule,
    TSReadonlyAssignmentRule,
    TSClassInheritanceRule,
    TSAsyncAwaitRule,
    TSPropertyNotFoundRule,
    TSCannotFindNameRule,
    TSArgumentCountRule,
    TSImplicitAnyRule,
    TSElementImplicitAnyRule,
    TSUnintentionalComparisonRule,
    TSTypeConstraintRule,
    TSMissingReturnRule,
    TSSyntaxErrorRule,
    TSTypeMismatchRule,
    JSJSONParseErrorRule,
    JSReferenceErrorRule,
    JSTypeErrorRule,
    JSSyntaxErrorRule,
    DatabaseErrorRule,
    JSONDecodeErrorRule,
    SubprocessErrorRule,
    JSRangeErrorRule,
    RecursionErrorRule,
    ZeroDivisionErrorRule,
    KeyErrorRule,
    IndexErrorRule,
    NameErrorRule,
    HttpClientErrorRule,
    HttpErrorRule,
    TypeErrorRule,
    ValueErrorRule,
    RuntimeAttributeErrorRule,
    ConnectionRefusedRule,
    PermissionDeniedRule,
    DirectoryNotFoundRule,
    FileNotFoundRule,
    DependencyConflictRule,
    SyntaxErrorRule,
    GitErrorRule,
]

class RuleRegistry:
    """Registry that holds diagnostic rules ordered by priority."""

    def __init__(self, load_defaults: bool = True):
        self._rules: Dict[str, BaseDiagnosticRule] = {}
        if load_defaults:
            self.load_builtins()

    def register(self, rule: BaseDiagnosticRule) -> None:
        """Register a diagnostic rule instance."""
        self._rules[rule.rule_id] = rule

    def unregister(self, rule_id: str) -> None:
        """Unregister a rule by its ID."""
        self._rules.pop(rule_id, None)

    def get_rule(self, rule_id: str) -> BaseDiagnosticRule:
        """Retrieve a rule by its ID."""
        return self._rules.get(rule_id)

    def all_rules(self) -> List[BaseDiagnosticRule]:
        """Return all registered rules sorted by priority (highest priority first)."""
        return sorted(self._rules.values(), key=lambda r: r.priority, reverse=True)

    def load_builtins(self) -> None:
        """Instantiate and register all built-in rules."""
        for rule_cls in BUILTIN_RULES:
            instance = rule_cls()
            self.register(instance)

_default_registry = None

def get_default_registry() -> RuleRegistry:
    """Get or create the global default rule registry."""
    global _default_registry
    if _default_registry is None:
        _default_registry = RuleRegistry(load_defaults=True)
    return _default_registry
