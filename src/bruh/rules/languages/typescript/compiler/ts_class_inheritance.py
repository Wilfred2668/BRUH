"""Diagnostic rule for TypeScript class inheritance and interface implementation errors (TS2420, TS2515, TS2416)."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

TS_CLASS_INHERITANCE_REGEX = re.compile(
    r"error\s+TS(?P<code>2420|2515|2416):\s*(?:Class\s+'(?P<cls1>[^']+)'\s+incorrectly implements interface\s+'(?P<iface>[^']+)'|"
    r"Non-abstract class\s+'(?P<cls2>[^']+)'\s+does not implement inherited abstract member\s+(?P<abstract_member>[^\s]+)\s+from class\s+'(?P<base_cls>[^']+)'|"
    r"Property\s+'(?P<prop>[^']+)'\s+in type\s+'(?P<sub_cls>[^']+)'\s+is not assignable to the same property in base type\s+'(?P<parent_cls>[^']+)')",
    re.IGNORECASE
)

class TSClassInheritanceRule(BaseDiagnosticRule):
    """Diagnoses TypeScript class inheritance, abstract method implementation, and interface contract errors (TS2420, TS2515, TS2416)."""

    rule_id = "ts-class-inheritance"
    name = "TypeScript Class Inheritance / Implementation"
    category = "compiler"
    priority = 84

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        if exit_code == 0:
            return None

        match = TS_CLASS_INHERITANCE_REGEX.search(cleaned_output)
        if match:
            code = match.group("code")
            cls_name = match.group("cls1") or match.group("cls2") or match.group("sub_cls") or "Class"
            iface = match.group("iface")
            abstract_member = match.group("abstract_member")
            base_cls = match.group("base_cls") or match.group("parent_cls")
            prop = match.group("prop")
            raw_err = match.group(0).strip()

            if code == "2420":
                title = f"💀 Class '{cls_name}' incorrectly implements interface '{iface}' (TS2420)"
            elif code == "2515":
                title = f"💀 Class '{cls_name}' does not implement abstract member '{abstract_member}' (TS2515)"
            else:
                title = f"💀 Property '{prop}' in '{cls_name}' is incompatible with base '{base_cls}' (TS2416)"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={
                    "code": code,
                    "cls_name": cls_name,
                    "iface": iface,
                    "abstract_member": abstract_member,
                    "base_cls": base_cls,
                    "prop": prop,
                    "raw": raw_err
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        code = vars.get("code")
        cls_name = vars.get("cls_name", "Class")

        if code == "2420":
            iface = vars.get("iface", "interface")
            return f"Class '{cls_name}' declares that it implements '{iface}', but is missing required methods/properties or has incompatible member signatures."
        elif code == "2515":
            abstract_member = vars.get("abstract_member", "member")
            base_cls = vars.get("base_cls", "base class")
            return f"Class '{cls_name}' extends abstract class '{base_cls}', but does not implement the required abstract member '{abstract_member}'."

        prop = vars.get("prop", "property")
        base_cls = vars.get("base_cls", "base class")
        return f"Property or method '{prop}' in derived class '{cls_name}' overrides '{base_cls}', but its type signature is incompatible with the parent."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        code = vars.get("code")
        cls_name = vars.get("cls_name", "Class")

        if code == "2420":
            iface = vars.get("iface", "interface")
            return [
                f"Implement all missing properties and methods defined in interface `{iface}` inside class `{cls_name}`.",
                f"Ensure method parameter and return types in `{cls_name}` match the signatures defined in `{iface}`.",
                f"Remove `implements {iface}` if the class is not intended to satisfy the entire interface contract."
            ]
        elif code == "2515":
            abstract_member = vars.get("abstract_member", "member")
            return [
                f"Define and implement method `{abstract_member}` on class `{cls_name}`.",
                f"Mark class `{cls_name}` as `abstract` if it is not intended to be directly instantiated: `abstract class {cls_name} ...`."
            ]

        prop = vars.get("prop", "property")
        return [
            f"Adjust the type or return value of `{prop}` in `{cls_name}` to match or be a subtype of the parent class definition.",
            f"Update the base class declaration if the new type signature should apply across all subclasses."
        ]
