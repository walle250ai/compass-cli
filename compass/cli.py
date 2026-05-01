from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from compass.scaffold import create_task_directory
from compass.validator import validate_task, print_validation_report
from compass.packer import pack_task, print_pack_summary

app = typer.Typer()
console = Console()


@app.command()
def new(name: str):
    exit_code = create_task_directory(name, console)
    raise typer.Exit(code=exit_code)


@app.command()
def validate(task_dir: Optional[str] = typer.Argument(None, help="Task directory to validate (defaults to current directory)")):
    task_path = Path(task_dir) if task_dir else None
    report = validate_task(task_path)
    print_validation_report(report, console)
    exit_code = 0 if report.all_passed else 1
    raise typer.Exit(code=exit_code)


@app.command()
def pack(
    task_dir: Optional[str] = typer.Argument(None, help="Task directory to pack (defaults to current directory)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output zip file path")
):
    task_path = Path(task_dir) if task_dir else None
    output_path = Path(output) if output else None
    
    result, report, exit_code = pack_task(task_path, output_path, console)
    
    if result is not None:
        print_pack_summary(result, console)
    
    raise typer.Exit(code=exit_code)


if __name__ == "__main__":
    app()
