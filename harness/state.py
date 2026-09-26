from dataclasses import dataclass, field, asdict
import json
from pathlib import Path

@dataclass
class TaskState:
    issue: str
    repo: str
    status: str = 'RUNNING'
    reason: str = ''
    plan: list = field(default_factory=list)
    findings: list = field(default_factory=list)
    failures: list = field(default_factory=list)
    baseline_failures: list = field(default_factory=list)
    tests: list = field(default_factory=list)
    verification: str = 'NOT_RUN'
    steps: int = 0
    llm_calls: int = 0
    tool_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    usage_estimated: bool = False
    candidate_context_tokens: int = 0
    sent_context_tokens: int = 0
    recoveries: int = 0
    successful_recoveries: int = 0

    def save(self, path: Path):
        temp = path.with_suffix('.tmp')
        temp.write_text(json.dumps(asdict(self), indent=2))
        temp.replace(path)
