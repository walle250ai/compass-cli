from pathlib import Path
from rich.console import Console
from rich.table import Table

QUERY_TEMPLATE = """业务背景：
请在此处描述任务的业务背景和上下文。

任务目标：
请在此处明确任务的具体目标和预期结果。

建议步骤（≥3条）：
1. 步骤一描述
2. 步骤二描述
3. 步骤三描述

基准时间（as_of = YYYY-MM-DD）：
as_of = 

输入范围：
请在此处描述输入数据的范围和限制。

约束条件：
请在此处列出任务执行过程中需要遵守的约束条件。

成功标准：
请在此处定义任务完成的成功标准和验收条件。
"""

README_TEMPLATE = """# 输入文件说明

此目录用于存放任务执行所需的所有输入文件。

## 文件角色说明

- 每个文件都有其特定的用途和格式要求
- 请确保所有输入文件都放置在此目录中
- 文件命名应清晰反映其内容和用途
"""

EXPERT_NOTES_TEMPLATE = """A. 关键指标口径与公式
请在此处描述关键指标的定义、计算口径和计算公式。

B. 关键文件专业判断点
请在此处列出关键文件中需要专业判断的要点。

C. 行业惯例/平台规则
请在此处说明相关的行业惯例或平台规则。

D. 专业陷阱（至少5条）
1. 陷阱一描述
2. 陷阱二描述
3. 陷阱三描述
4. 陷阱四描述
5. 陷阱五描述

E. 评分点候选清单
请在此处列出评分时需要考虑的关键点。
"""


def create_task_directory(name: str, console: Console) -> int:
    task_path = Path(name)
    
    if task_path.exists():
        console.print(f"[bold red]Error:[/bold red] Directory '{name}' already exists.")
        return 1
    
    task_path.mkdir()
    
    (task_path / "query.txt").write_text(QUERY_TEMPLATE, encoding="utf-8")
    
    inputs_dir = task_path / "inputs"
    inputs_dir.mkdir()
    (inputs_dir / "00_README.md").write_text(README_TEMPLATE, encoding="utf-8")
    
    golden_solution_dir = task_path / "golden_solution"
    golden_solution_dir.mkdir()
    (golden_solution_dir / ".gitkeep").write_text("", encoding="utf-8")
    
    (task_path / "expert_notes.txt").write_text(EXPERT_NOTES_TEMPLATE, encoding="utf-8")
    
    table = Table(title="Created Task Files")
    table.add_column("File/Directory", style="cyan")
    table.add_column("Purpose", style="green")
    
    table.add_row(f"{name}/", "Task root directory")
    table.add_row(f"{name}/query.txt", "Task query with 7 required sections")
    table.add_row(f"{name}/inputs/", "Input files directory")
    table.add_row(f"{name}/inputs/00_README.md", "Input files documentation")
    table.add_row(f"{name}/golden_solution/", "Golden solution directory")
    table.add_row(f"{name}/golden_solution/.gitkeep", "Git placeholder file")
    table.add_row(f"{name}/expert_notes.txt", "Expert notes with 5 required sections")
    
    console.print(table)
    console.print(f"\n[bold green]Success:[/bold green] Task '{name}' created successfully.")
    
    return 0
