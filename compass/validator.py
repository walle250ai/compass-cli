import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.table import Table


class ValidationStatus(Enum):
    PASS = "pass"
    FAIL = "fail"


@dataclass
class ValidationResult:
    rule_number: int
    rule_description: str
    status: ValidationStatus
    detail: str
    is_hard_fail: bool = False


@dataclass
class ValidationReport:
    results: List[ValidationResult] = field(default_factory=list)
    hard_fail_encountered: bool = False
    
    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.results if r.status == ValidationStatus.PASS)
    
    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if r.status == ValidationStatus.FAIL)
    
    @property
    def all_passed(self) -> bool:
        return self.failed_count == 0 and not self.hard_fail_encountered
    
    def add_result(self, result: ValidationResult):
        self.results.append(result)
        if result.status == ValidationStatus.FAIL and result.is_hard_fail:
            self.hard_fail_encountered = True


FORBIDDEN_EXTENSIONS = {".psd", ".ai", ".sketch", ".fig", ".key", ".numbers", ".indd"}
FORBIDDEN_PHRASES = ["今天", "本周", "上个月", "最近", "当前", "实时", "现在的"]
REQUIRED_EXPERT_NOTES_SECTIONS = ["A.", "B.", "C.", "D.", "E."]
MAX_FILE_SIZE_MB = 20
MAX_TOTAL_SIZE_MB = 300
MIN_INPUT_FILES = 5


def validate_task(task_dir: Optional[Path] = None) -> ValidationReport:
    if task_dir is None:
        task_dir = Path.cwd()
    
    report = ValidationReport()
    
    validate_hard_rules(task_dir, report)
    
    if report.hard_fail_encountered:
        return report
    
    validate_file_rules(task_dir, report)
    validate_content_rules(task_dir, report)
    
    return report


def validate_hard_rules(task_dir: Path, report: ValidationReport):
    rules = [
        (1, "query.txt exists", lambda: (task_dir / "query.txt").exists()),
        (2, "inputs/ directory exists", lambda: (task_dir / "inputs").exists() and (task_dir / "inputs").is_dir()),
        (3, "golden_solution/ directory exists", lambda: (task_dir / "golden_solution").exists() and (task_dir / "golden_solution").is_dir()),
        (4, "expert_notes.txt exists", lambda: (task_dir / "expert_notes.txt").exists()),
    ]
    
    for rule_num, rule_desc, check_fn in rules:
        if check_fn():
            report.add_result(ValidationResult(
                rule_number=rule_num,
                rule_description=rule_desc,
                status=ValidationStatus.PASS,
                detail="Found",
                is_hard_fail=True
            ))
        else:
            report.add_result(ValidationResult(
                rule_number=rule_num,
                rule_description=rule_desc,
                status=ValidationStatus.FAIL,
                detail=f"Missing: {rule_desc.split(' exists')[0]}",
                is_hard_fail=True
            ))


def validate_file_rules(task_dir: Path, report: ValidationReport):
    inputs_dir = task_dir / "inputs"
    
    input_files = []
    for f in inputs_dir.rglob("*"):
        if f.is_file() and f.name != "00_README.md":
            input_files.append(f)
    
    report.add_result(ValidationResult(
        rule_number=5,
        rule_description=f"inputs/ contains at least {MIN_INPUT_FILES} files (excluding 00_README.md)",
        status=ValidationStatus.PASS if len(input_files) >= MIN_INPUT_FILES else ValidationStatus.FAIL,
        detail=f"Found {len(input_files)} files" if len(input_files) >= MIN_INPUT_FILES else f"Found only {len(input_files)} files, need at least {MIN_INPUT_FILES}",
        is_hard_fail=False
    ))
    
    forbidden_ext_files = []
    for f in input_files:
        if f.suffix.lower() in FORBIDDEN_EXTENSIONS:
            forbidden_ext_files.append(f.name)
    
    report.add_result(ValidationResult(
        rule_number=6,
        rule_description=f"No file in inputs/ has forbidden extension: {', '.join(FORBIDDEN_EXTENSIONS)}",
        status=ValidationStatus.PASS if not forbidden_ext_files else ValidationStatus.FAIL,
        detail="No forbidden extensions found" if not forbidden_ext_files else f"Forbidden extensions: {', '.join(forbidden_ext_files)}",
        is_hard_fail=False
    ))
    
    large_files = []
    for f in input_files:
        size_mb = f.stat().st_size / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            large_files.append(f"{f.name} ({size_mb:.2f}MB)")
    
    report.add_result(ValidationResult(
        rule_number=7,
        rule_description=f"No single file in inputs/ exceeds {MAX_FILE_SIZE_MB}MB",
        status=ValidationStatus.PASS if not large_files else ValidationStatus.FAIL,
        detail="All files under size limit" if not large_files else f"Files exceeding limit: {', '.join(large_files)}",
        is_hard_fail=False
    ))
    
    total_size_bytes = sum(f.stat().st_size for f in input_files)
    total_size_mb = total_size_bytes / (1024 * 1024)
    
    report.add_result(ValidationResult(
        rule_number=8,
        rule_description=f"Total size of inputs/ does not exceed {MAX_TOTAL_SIZE_MB}MB",
        status=ValidationStatus.PASS if total_size_mb <= MAX_TOTAL_SIZE_MB else ValidationStatus.FAIL,
        detail=f"Total size: {total_size_mb:.2f}MB" if total_size_mb <= MAX_TOTAL_SIZE_MB else f"Total size: {total_size_mb:.2f}MB exceeds limit of {MAX_TOTAL_SIZE_MB}MB",
        is_hard_fail=False
    ))


def validate_content_rules(task_dir: Path, report: ValidationReport):
    query_path = task_dir / "query.txt"
    query_content = query_path.read_text(encoding="utf-8")
    
    as_of_pattern = r"as_of\s*=\s*(\d{4}-\d{2}-\d{2})"
    as_of_match = re.search(as_of_pattern, query_content)
    
    report.add_result(ValidationResult(
        rule_number=9,
        rule_description='query.txt contains "as_of = " followed by YYYY-MM-DD date',
        status=ValidationStatus.PASS if as_of_match else ValidationStatus.FAIL,
        detail=f"Found as_of = {as_of_match.group(1)}" if as_of_match else 'Missing or invalid "as_of = YYYY-MM-DD" pattern',
        is_hard_fail=False
    ))
    
    found_forbidden = []
    for phrase in FORBIDDEN_PHRASES:
        if phrase in query_content:
            found_forbidden.append(phrase)
    
    report.add_result(ValidationResult(
        rule_number=10,
        rule_description=f'query.txt does not contain forbidden phrases: {", ".join(FORBIDDEN_PHRASES)}',
        status=ValidationStatus.PASS if not found_forbidden else ValidationStatus.FAIL,
        detail="No forbidden phrases found" if not found_forbidden else f"Found forbidden phrases: {', '.join(found_forbidden)}",
        is_hard_fail=False
    ))
    
    expert_notes_path = task_dir / "expert_notes.txt"
    expert_notes_content = expert_notes_path.read_text(encoding="utf-8")
    
    missing_sections = []
    for section in REQUIRED_EXPERT_NOTES_SECTIONS:
        if section not in expert_notes_content:
            missing_sections.append(section)
    
    report.add_result(ValidationResult(
        rule_number=11,
        rule_description=f'expert_notes.txt contains all 5 section headers: {", ".join(REQUIRED_EXPERT_NOTES_SECTIONS)}',
        status=ValidationStatus.PASS if not missing_sections else ValidationStatus.FAIL,
        detail="All sections found" if not missing_sections else f"Missing sections: {', '.join(missing_sections)}",
        is_hard_fail=False
    ))


def print_validation_report(report: ValidationReport, console: Console):
    table = Table(title="Validation Results")
    table.add_column("Rule", style="cyan", justify="right")
    table.add_column("Status", style="bold")
    table.add_column("Detail", style="green")
    
    for result in report.results:
        status_icon = "✅" if result.status == ValidationStatus.PASS else "❌"
        status_style = "green" if result.status == ValidationStatus.PASS else "red"
        detail_style = "green" if result.status == ValidationStatus.PASS else "red"
        
        table.add_row(
            str(result.rule_number),
            f"[{status_style}]{status_icon}[/{status_style}]",
            f"[{detail_style}]{result.detail}[/{detail_style}]"
        )
    
    console.print(table)
    
    if report.hard_fail_encountered:
        console.print("\n[bold red]Hard fail encountered. Stopped further validation.[/bold red]")
    
    console.print(f"\n[bold]{report.passed_count} checks passed, {report.failed_count} failed[/bold]")
