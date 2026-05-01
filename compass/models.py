from datetime import date
from pathlib import Path

from pydantic import BaseModel


class TaskManifest(BaseModel):
    name: str
    as_of: date
    domain: str
    query_path: Path
    inputs_dir: Path
    golden_solution_dir: Path
    expert_notes_path: Path
