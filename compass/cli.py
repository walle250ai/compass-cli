import typer
from rich.console import Console

from compass.scaffold import create_task_directory

app = typer.Typer()
console = Console()


@app.command()
def new(name: str):
    exit_code = create_task_directory(name, console)
    raise typer.Exit(code=exit_code)


@app.command()
def validate():
    console.print("not implemented yet")


@app.command()
def pack():
    console.print("not implemented yet")


if __name__ == "__main__":
    app()
