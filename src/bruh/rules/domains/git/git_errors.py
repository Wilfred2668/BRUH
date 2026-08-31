"""Diagnostic rule for common Git version control errors."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

GIT_NOT_REPO = re.compile(r"fatal:\s*not a git repository", re.IGNORECASE)
GIT_UNRELATED = re.compile(r"fatal:\s*refusing to merge unrelated histories", re.IGNORECASE)
GIT_PUSH_REJECTED = re.compile(r"(?:error:\s*failed to push some refs|Updates were rejected because the remote contains work)", re.IGNORECASE)
GIT_DIR_EXISTS = re.compile(r"fatal:\s*destination path ['\"](?P<path>[^'\"]+)['\"]\s*already exists", re.IGNORECASE)
GIT_NO_REMOTE = re.compile(r"fatal:\s*'(?P<remote>[^']+)' does not appear to be a git repository", re.IGNORECASE)
GIT_LOCAL_CHANGES = re.compile(r"error:\s*Your local changes to the following files would be overwritten", re.IGNORECASE)
GIT_PATHSPEC = re.compile(r"fatal:\s*pathspec ['\"](?P<spec>[^'\"]+)['\"]\s*did not match any files", re.IGNORECASE)

class GitErrorRule(BaseDiagnosticRule):
    """Diagnoses common Git command and repository synchronization errors."""

    rule_id = "git-error"
    name = "Git Version Control Error"
    category = "vcs"
    priority = 60

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        if exit_code == 0:
            return None
        if not (command and "git" in command.lower()) and "fatal:" not in cleaned_output and "git" not in cleaned_output.lower():
            return None

        # 1. Not a git repo
        if GIT_NOT_REPO.search(cleaned_output):
            return RuleMatch(
                matched=True,
                title="💀 Git: Not a Git Repository",
                original_error="fatal: not a git repository (or any of the parent directories): .git",
                extracted_vars={"issue": "not_repo"}
            )

        # 2. Refusing to merge unrelated histories
        if GIT_UNRELATED.search(cleaned_output):
            return RuleMatch(
                matched=True,
                title="💀 Git: Refusing to Merge Unrelated Histories",
                original_error="fatal: refusing to merge unrelated histories",
                extracted_vars={"issue": "unrelated_histories"}
            )

        # 3. Push rejected / fetch first
        if GIT_PUSH_REJECTED.search(cleaned_output):
            return RuleMatch(
                matched=True,
                title="💀 Git: Push Rejected (Remote Ahead)",
                original_error="error: failed to push some refs (remote contains work you do not have locally)",
                extracted_vars={"issue": "push_rejected"}
            )

        # 4. Destination path already exists
        dir_match = GIT_DIR_EXISTS.search(cleaned_output)
        if dir_match:
            path = dir_match.group("path")
            return RuleMatch(
                matched=True,
                title=f"💀 Git: Destination Directory Exists ('{path}')",
                original_error=f"fatal: destination path '{path}' already exists and is not an empty directory.",
                extracted_vars={"issue": "dir_exists", "path": path}
            )

        # 5. Remote not found
        remote_match = GIT_NO_REMOTE.search(cleaned_output)
        if remote_match:
            remote = remote_match.group("remote")
            return RuleMatch(
                matched=True,
                title=f"💀 Git: Remote '{remote}' Not Found",
                original_error=f"fatal: '{remote}' does not appear to be a git repository",
                extracted_vars={"issue": "no_remote", "remote": remote}
            )

        # 6. Local changes overwritten
        if GIT_LOCAL_CHANGES.search(cleaned_output):
            return RuleMatch(
                matched=True,
                title="💀 Git: Local Changes Would Be Overwritten",
                original_error="error: Your local changes to files would be overwritten by checkout/merge",
                extracted_vars={"issue": "local_changes"}
            )

        # 7. Pathspec did not match
        spec_match = GIT_PATHSPEC.search(cleaned_output)
        if spec_match:
            spec = spec_match.group("spec")
            return RuleMatch(
                matched=True,
                title=f"💀 Git: Branch or File Not Found ('{spec}')",
                original_error=f"fatal: pathspec '{spec}' did not match any files",
                extracted_vars={"issue": "pathspec", "spec": spec}
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        issue = vars.get("issue", "")
        if issue == "not_repo":
            return "This directory is not initialized as a Git repository, and no parent directory contains a `.git` folder."
        elif issue == "unrelated_histories":
            return "Git prevented merging because the two branches or remote repo share no common commit history."
        elif issue == "push_rejected":
            return "The remote repository has commits that your local branch does not have. Git rejects overwriting them."
        elif issue == "dir_exists":
            path = vars.get("path", "folder")
            return f"Git clone failed because target directory '{path}' already exists and contains files."
        elif issue == "local_changes":
            return "You have modified files in your working directory that would be replaced by the incoming checkout or merge."
        elif issue == "pathspec":
            spec = vars.get("spec", "branch")
            return f"Git could not find a branch, commit, or file named '{spec}'."
        return "A Git version control operation failed."

    def generate_human_explanation(self, vars: Dict[str, Any]) -> str:
        issue = vars.get("issue", "")
        if issue == "not_repo":
            return "You're running git commands in a regular folder that isn't tracked by git yet."
        elif issue == "push_rejected":
            return (
                "Someone (or you on another machine) pushed commits to GitHub/GitLab.\n"
                "You need to pull their changes before you can push yours."
            )
        elif issue == "unrelated_histories":
            return "Git thinks these are two completely different projects and refused to blindly smash them together."
        elif issue == "local_changes":
            return "You have unstashed edits. Git is saving you from accidentally erasing your own work."
        return "Git stopped the operation to prevent data loss or because target resources could not be found."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        issue = vars.get("issue", "")
        if issue == "not_repo":
            return [
                "Initialize a new repository: `git init`",
                "Or navigate into the correct project subdirectory."
            ]
        elif issue == "push_rejected":
            return [
                "Pull the latest remote changes first: `git pull --rebase origin main` (or your branch name)",
                "Resolve any merge conflicts if they arise.",
                "Then push your changes: `git push`"
            ]
        elif issue == "unrelated_histories":
            return [
                "If you intentionally want to combine these repos: `git pull origin main --allow-unrelated-histories`",
                "Or verify that you have added the correct remote repository URL: `git remote -v`"
            ]
        elif issue == "dir_exists":
            path = vars.get("path", "folder")
            return [
                f"Clone into a different folder name: `git clone <url> my-new-folder`",
                f"Or delete/rename the existing '{path}' directory if it is no longer needed."
            ]
        elif issue == "local_changes":
            return [
                "Save your current changes to stash: `git stash`",
                "Perform your checkout/pull/merge operation.",
                "Re-apply your stashed changes: `git stash pop`",
                "Or discard local changes if you don't need them: `git restore .`"
            ]
        elif issue == "pathspec":
            spec = vars.get("spec", "branch")
            return [
                f"Check existing branches: `git branch -a`",
                f"Fetch remote branches from server: `git fetch --all`",
                f"Verify spelling of '{spec}'."
            ]
        return [
            "Check git status: `git status`",
            "Check remote repositories: `git remote -v`"
        ]
