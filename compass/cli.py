import typer
from rich.console import Console

app = typer.Typer()
console = Console()


@app.command()
def new():
    console.print("not implemented yet")


@app.command()
def validate():
    console.print("not implemented yet")


@app.command()
def pack():
    console.print("not implemented yet")


if __name__ == "__main__":
    app()
