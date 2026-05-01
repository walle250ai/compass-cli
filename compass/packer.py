import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.table import Table

from compass.validator import validate_task, print_validation_report, ValidationReport


@dataclass
class PackResult:
    zip_path: Path
    total_files: int
    zip_size_mb: float


def extract_as_of_date(query_content: str) -> Optional[str]:
    as_of_pattern = r"as_of\s*=\s*(\d{4}-\d{2}-\d{2})"
    as_of_match = re.search(as_of_pattern, query_content)
    if as_of_match:
        return as_of_match.group(1)
    return None


def get_files_to_pack(task_dir: Path) -> List[Path]:
    files = []
    
    query_file = task_dir / "query.txt"
    if query_file.exists():
        files.append(query_file)
    
    expert_notes_file = task_dir / "expert_notes.txt"
    if expert_notes_file.exists():
        files.append(expert_notes_file)
    
    inputs_dir = task_dir / "inputs"
    if inputs_dir.exists() and inputs_dir.is_dir():
        for f in inputs_dir.rglob("*"):
            if f.is_file():
                files.append(f)
    
    golden_solution_dir = task_dir / "golden_solution"
    if golden_solution_dir.exists() and golden_solution_dir.is_dir():
        for f in golden_solution_dir.rglob("*"):
            if f.is_file():
                files.append(f)
    
    return files


def create_zip_archive(task_dir: Path, output_path: Path, files: List[Path]) -> None:
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in files:
            arcname = file_path.relative_to(task_dir)
            zipf.write(file_path, arcname)


def pack_task(
    task_dir: Optional[Path] = None,
    output_path: Optional[Path] = None,
    console: Optional[Console] = None
) -> tuple[Optional[PackResult], Optional[ValidationReport], int]:
    if console is None:
        console = Console()
    
    if task_dir is None:
        task_dir = Path.cwd()
    
    report = validate_task(task_dir)
    
    if not report.all_passed:
        print_validation_report(report, console)
        console.print("\n[bold red]Validation failed. Fix errors before packing.[/bold red]")
        return None, report, 1
    
    files = get_files_to_pack(task_dir)
    
    if output_path is None:
        query_content = (task_dir / "query.txt").read_text(encoding="utf-8")
        as_of_date = extract_as_of_date(query_content)
        task_name = task_dir.name
        if as_of_date:
            output_filename = f"{task_name}_{as_of_date}.zip"
        else:
            output_filename = f"{task_name}.zip"
        output_path = task_dir.parent / output_filename
    
    create_zip_archive(task_dir, output_path, files)
    
    zip_size_bytes = output_path.stat().st_size
    zip_size_mb = zip_size_bytes / (1024 * 1024)
    
    result = PackResult(
        zip_path=output_path,
        total_files=len(files),
        zip_size_mb=zip_size_mb
    )
    
    return result, report, 0


def print_pack_summary(result: PackResult, console: Console):
    table = Table(title="Pack Summary")
    table.add_column("Item", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Output zip path", str(result.zip_path))
    table.add_row("Total files packed", str(result.total_files))
    table.add_row("Zip file size", f"{result.zip_size_mb:.2f} MB")
    
    console.print(table)
    console.print(f"\n[bold green]Success:[/bold green] Task packed successfully to {result.zip_path}")
