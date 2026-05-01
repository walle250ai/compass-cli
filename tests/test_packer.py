import os
import shutil
import zipfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from compass.cli import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def cleanup_test_dirs():
    yield
    test_dirs = [d for d in Path.cwd().iterdir() if d.is_dir() and d.name.startswith("test_pack_")]
    for test_dir in test_dirs:
        if test_dir.exists():
            shutil.rmtree(test_dir)
    
    test_zips = [f for f in Path.cwd().iterdir() if f.is_file() and f.name.startswith("test_pack_") and f.suffix == ".zip"]
    for test_zip in test_zips:
        if test_zip.exists():
            test_zip.unlink()


def create_valid_task_dir(dir_name: str) -> Path:
    task_path = Path(dir_name)
    task_path.mkdir()
    
    query_content = """业务背景：
测试任务

任务目标：
测试目标

建议步骤（≥3条）：
1. 步骤一
2. 步骤二
3. 步骤三

基准时间（as_of = YYYY-MM-DD）：
as_of = 2026-05-01

输入范围：
测试范围

约束条件：
无

成功标准：
通过
"""
    (task_path / "query.txt").write_text(query_content, encoding="utf-8")
    
    inputs_dir = task_path / "inputs"
    inputs_dir.mkdir()
    (inputs_dir / "00_README.md").write_text("# Input files", encoding="utf-8")
    
    for i in range(5):
        (inputs_dir / f"file_{i}.txt").write_text(f"content {i}", encoding="utf-8")
    
    golden_dir = task_path / "golden_solution"
    golden_dir.mkdir()
    (golden_dir / ".gitkeep").write_text("", encoding="utf-8")
    
    expert_notes_content = """A. 关键指标口径与公式
测试内容

B. 关键文件专业判断点
测试内容

C. 行业惯例/平台规则
测试内容

D. 专业陷阱（至少5条）
1. 陷阱一
2. 陷阱二
3. 陷阱三
4. 陷阱四
5. 陷阱五

E. 评分点候选清单
测试内容
"""
    (task_path / "expert_notes.txt").write_text(expert_notes_content, encoding="utf-8")
    
    return task_path


def test_pack_valid_task_creates_zip():
    test_dir_name = "test_pack_valid_001"
    task_path = create_valid_task_dir(test_dir_name)
    
    expected_zip_name = f"{test_dir_name}_2026-05-01.zip"
    expected_zip_path = Path.cwd() / expected_zip_name
    
    if expected_zip_path.exists():
        expected_zip_path.unlink()
    
    result = runner.invoke(app, ["pack", test_dir_name])
    
    assert result.exit_code == 0
    assert expected_zip_path.exists()
    
    with zipfile.ZipFile(expected_zip_path, 'r') as zipf:
        zip_contents = zipf.namelist()
        
        assert "query.txt" in zip_contents
        assert "expert_notes.txt" in zip_contents
        assert "inputs/00_README.md" in zip_contents
        for i in range(5):
            assert f"inputs/file_{i}.txt" in zip_contents
        assert "golden_solution/.gitkeep" in zip_contents
        
        total_files = len([f for f in zip_contents if not f.endswith('/')])
        assert total_files >= 8
    
    if expected_zip_path.exists():
        expected_zip_path.unlink()


def test_pack_invalid_task_aborts_with_error():
    test_dir_name = "test_pack_invalid_001"
    task_path = Path(test_dir_name)
    task_path.mkdir()
    
    (task_path / "inputs").mkdir()
    (task_path / "golden_solution").mkdir()
    (task_path / "expert_notes.txt").write_text("test", encoding="utf-8")
    
    result = runner.invoke(app, ["pack", test_dir_name])
    
    assert result.exit_code == 1
    assert "Validation failed" in result.output
    assert "query.txt" in result.output.lower() or "missing" in result.output.lower()


def test_pack_custom_output_path():
    test_dir_name = "test_pack_custom_output_001"
    task_path = create_valid_task_dir(test_dir_name)
    
    custom_output_path = Path.cwd() / "test_pack_custom_output.zip"
    
    if custom_output_path.exists():
        custom_output_path.unlink()
    
    result = runner.invoke(app, ["pack", test_dir_name, "--output", str(custom_output_path)])
    
    assert result.exit_code == 0
    assert custom_output_path.exists()
    
    with zipfile.ZipFile(custom_output_path, 'r') as zipf:
        zip_contents = zipf.namelist()
        assert "query.txt" in zip_contents
    
    if custom_output_path.exists():
        custom_output_path.unlink()
