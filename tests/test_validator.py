import os
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from compass.cli import app
from compass.validator import (
    validate_task,
    ValidationReport,
    ValidationStatus,
    ValidationResult,
)

runner = CliRunner()


@pytest.fixture(autouse=True)
def cleanup_test_dirs():
    yield
    test_dirs = [d for d in Path.cwd().iterdir() if d.is_dir() and d.name.startswith("test_validate_")]
    for test_dir in test_dirs:
        if test_dir.exists():
            shutil.rmtree(test_dir)


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


def test_valid_task_passes_all_checks():
    test_dir_name = "test_validate_valid_001"
    task_path = create_valid_task_dir(test_dir_name)
    
    result = runner.invoke(app, ["validate", test_dir_name])
    
    assert result.exit_code == 0
    assert "11 checks passed" in result.output or "passed" in result.output.lower()


def test_missing_query_txt_fails():
    test_dir_name = "test_validate_missing_query_001"
    task_path = Path(test_dir_name)
    task_path.mkdir()
    
    (task_path / "inputs").mkdir()
    (task_path / "golden_solution").mkdir()
    (task_path / "expert_notes.txt").write_text("test", encoding="utf-8")
    
    result = runner.invoke(app, ["validate", test_dir_name])
    
    assert result.exit_code == 1
    assert "query.txt exists" in result.output or "Missing" in result.output


def test_inputs_fewer_than_5_files_fails():
    test_dir_name = "test_validate_few_inputs_001"
    task_path = Path(test_dir_name)
    task_path.mkdir()
    
    query_content = """as_of = 2026-05-01
业务背景：测试
"""
    (task_path / "query.txt").write_text(query_content, encoding="utf-8")
    
    inputs_dir = task_path / "inputs"
    inputs_dir.mkdir()
    (inputs_dir / "00_README.md").write_text("# Input files", encoding="utf-8")
    
    for i in range(3):
        (inputs_dir / f"file_{i}.txt").write_text(f"content {i}", encoding="utf-8")
    
    (task_path / "golden_solution").mkdir()
    
    expert_notes_content = """A. 测试
B. 测试
C. 测试
D. 测试
E. 测试
"""
    (task_path / "expert_notes.txt").write_text(expert_notes_content, encoding="utf-8")
    
    result = runner.invoke(app, ["validate", test_dir_name])
    
    assert result.exit_code == 1
    assert "3 files" in result.output or "need at least 5" in result.output


def test_query_missing_as_of_date_fails():
    test_dir_name = "test_validate_missing_asof_001"
    task_path = Path(test_dir_name)
    task_path.mkdir()
    
    query_content = """业务背景：测试
任务目标：测试
建议步骤：
1. 步骤一
2. 步骤二
3. 步骤三

基准时间：
（没有as_of格式）

输入范围：测试
约束条件：测试
成功标准：测试
"""
    (task_path / "query.txt").write_text(query_content, encoding="utf-8")
    
    inputs_dir = task_path / "inputs"
    inputs_dir.mkdir()
    (inputs_dir / "00_README.md").write_text("# Input files", encoding="utf-8")
    
    for i in range(5):
        (inputs_dir / f"file_{i}.txt").write_text(f"content {i}", encoding="utf-8")
    
    (task_path / "golden_solution").mkdir()
    
    expert_notes_content = """A. 测试
B. 测试
C. 测试
D. 测试
E. 测试
"""
    (task_path / "expert_notes.txt").write_text(expert_notes_content, encoding="utf-8")
    
    result = runner.invoke(app, ["validate", test_dir_name])
    
    assert result.exit_code == 1
    assert "as_of" in result.output.lower() or "Missing" in result.output


def test_query_contains_forbidden_phrase_fails():
    test_dir_name = "test_validate_forbidden_phrase_001"
    task_path = Path(test_dir_name)
    task_path.mkdir()
    
    query_content = """业务背景：测试
任务目标：测试
建议步骤：
1. 步骤一
2. 步骤二
3. 步骤三

基准时间（as_of = YYYY-MM-DD）：
as_of = 2026-05-01

输入范围：今天的数据
约束条件：测试
成功标准：测试
"""
    (task_path / "query.txt").write_text(query_content, encoding="utf-8")
    
    inputs_dir = task_path / "inputs"
    inputs_dir.mkdir()
    (inputs_dir / "00_README.md").write_text("# Input files", encoding="utf-8")
    
    for i in range(5):
        (inputs_dir / f"file_{i}.txt").write_text(f"content {i}", encoding="utf-8")
    
    (task_path / "golden_solution").mkdir()
    
    expert_notes_content = """A. 测试
B. 测试
C. 测试
D. 测试
E. 测试
"""
    (task_path / "expert_notes.txt").write_text(expert_notes_content, encoding="utf-8")
    
    result = runner.invoke(app, ["validate", test_dir_name])
    
    assert result.exit_code == 1
    assert "今天" in result.output or "forbidden" in result.output.lower()


def test_validate_defaults_to_current_directory():
    test_dir_name = "test_validate_cwd_001"
    original_cwd = Path.cwd()
    
    try:
        task_path = create_valid_task_dir(test_dir_name)
        os.chdir(task_path)
        
        result = runner.invoke(app, ["validate"])
        
        assert result.exit_code == 0
    finally:
        os.chdir(original_cwd)
