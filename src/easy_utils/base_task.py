# base_task.py
from pathlib import Path
from abc import ABC, abstractmethod
from typing import List
import os

class BaseTask(ABC):
    # force: bool = False  # 외부에서 주입 가능 -> io.force로 대체
    io = None  # 외부에서 주입 가능

    @abstractmethod
    def expected_outputs(self) -> List[Path]:
        """이 태스크가 '성공 시' 만들어야 하는 파일 경로 리스트"""
        ...

    @abstractmethod
    def run_impl(self, **kwargs):
        """실제 작업 로직"""
        ...

    def run(self, **kwargs):
        outs = self.expected_outputs()
        # outs 를 for문으로 돌면서, Path(p) 로 변환
        outs = [Path(p) for p in outs if p]
        # self.io.force 가 없으면 False로 설정
        if not hasattr(self.io, 'force'):
            self.io.force = False
        # 모두 존재하고, force가 아니면 스킵
        if (not self.io.force) and outs and all(p.exists() for p in outs):
            return {"skipped": True, "reason": "outputs_exist", "outputs": outs, "io": self.io}
        # 없거나 force=True면 실행
        self._prepare_dirs(outs)
        result = self.run_impl(**kwargs)
        # 실행 후 검증
        if not all(p.exists() for p in outs):
            # raise warning
            print(f"Task finished but some outputs missing: {outs}")
            missing_outs = [p for p in outs if not p.exists()]
            print(f"Missing outputs: {missing_outs}")
            return {"skipped": False, "outputs": outs, "missing_outputs": missing_outs, "result": result, "io": self.io}
            # raise RuntimeError(f"Task finished but some outputs missing: {outs}")
        return {"skipped": False, "outputs": outs, "result": result, "io": self.io}

    def _prepare_dirs(self, outs: List[Path]):
        for p in outs:
            p.parent.mkdir(parents=True, exist_ok=True)