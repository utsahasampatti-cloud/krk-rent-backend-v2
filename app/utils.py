import json
import time
import uuid
from typing import Any, Dict


def now_ts() -> float:
    return time.time()


def new_job_id() -> str:
    return str(uuid.uuid4())


def dumps(obj: Dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def loads(s: str) -> Dict[str, Any]:
    return json.loads(s)
