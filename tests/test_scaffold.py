import os
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from compass.cli import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def cleanup_test_dirs():
    yield
    test_dirs = [d for d in Path.cwd().iterdir() if d.is_dir() and d.name.startswith("test_task_")]
    for test_dir in test_dirs:
        if test_dir.exists():
            shutil.rmtree(test_dir)


def test_new_command_creates_directory_structure():
    test_dir_name = "test_task_001"
    
    result = runner.invoke(app, ["new", test_dir_name])
    
    assert result.exit_code == 0
    assert Path(test_dir_name).exists()
    assert Path(test_dir_name).is_dir()
    
    assert (Path(test_dir_name) / "query.txt").exists()
    assert (Path(test_dir_name) / "inputs").exists()
    assert (Path(test_dir_name) / "inputs").is_dir()
    assert (Path(test_dir_name) / "inputs" / "00_README.md").exists()
    assert (Path(test_dir_name) / "golden_solution").exists()
    assert (Path(test_dir_name) / "golden_solution").is_dir()
    assert (Path(test_dir_name) / "golden_solution" / ".gitkeep").exists()
    assert (Path(test_dir_name) / "expert_notes.txt").exists()


def test_new_command_fails_on_existing_directory():
    test_dir_name = "test_task_002"
    
    Path(test_dir_name).mkdir()
    
    result = runner.invoke(app, ["new", test_dir_name])
    
    assert result.exit_code == 1
    assert "already exists" in result.output.lower()
