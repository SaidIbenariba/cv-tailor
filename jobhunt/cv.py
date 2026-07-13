"""CV attachment providers.

`MasterCVProvider` compiles the LaTeX CV once and attaches the same PDF to
every application. `CVProvider` is the seam where per-job tailoring (via the
vendored resume-tailoring skill) can plug in later without touching draft.py.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

from jobhunt.models import JobRecord

log = logging.getLogger(__name__)


class CVProvider(ABC):
    @abstractmethod
    def get_attachment(self, job: JobRecord) -> Path | None:
        """Return a path to the CV to attach, or None if unavailable."""


class MasterCVProvider(CVProvider):
    """Builds the master CV PDF from LaTeX, cached for the whole run."""

    def __init__(self, tex_path: str | Path, build_dir: str | Path = "build"):
        self.tex_path = Path(tex_path)
        self.build_dir = Path(build_dir)
        self._cached: Path | None = None
        self._attempted = False

    def get_attachment(self, job: JobRecord) -> Path | None:
        if self._attempted:
            return self._cached
        self._attempted = True
        self._cached = self._build()
        return self._cached

    def _build(self) -> Path | None:
        if not self.tex_path.exists():
            log.warning("CV source %s not found; drafting without attachment", self.tex_path)
            return None
        # Prefer tectonic (self-fetches packages, single command); fall back to
        # pdflatex. tectonic resolves reruns internally, so one invocation.
        if shutil.which("tectonic") is not None:
            commands = [[
                "tectonic", "--outdir", str(self.build_dir),
                "--keep-logs", str(self.tex_path),
            ]]
            engine = "tectonic"
        elif shutil.which("pdflatex") is not None:
            commands = [[  # second pass resolves tabularx/hyperref layout
                "pdflatex", "-interaction=nonstopmode", "-halt-on-error",
                "-output-directory", str(self.build_dir), str(self.tex_path),
            ]] * 2
            engine = "pdflatex"
        else:
            log.warning(
                "No LaTeX engine found; drafting without CV attachment. "
                "Install tectonic (`brew install tectonic`) or MacTeX to attach the CV."
            )
            return None

        self.build_dir.mkdir(parents=True, exist_ok=True)
        pdf = self.build_dir / (self.tex_path.stem + ".pdf")
        try:
            for cmd in commands:
                subprocess.run(cmd, check=True, capture_output=True, timeout=120)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            log.warning("%s failed (%s); drafting without attachment", engine, exc)
            return None

        return pdf if pdf.exists() and pdf.stat().st_size > 0 else None
