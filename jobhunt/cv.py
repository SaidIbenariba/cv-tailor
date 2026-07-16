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

class TailoredCVProvider(MasterCVProvider):
    """
    Dynamically alters the LaTeX source code to match the job's title,
    updates the Awesome-CV footer, and compiles a unique PDF per application.
    """

    def _escape_latex(self, text: str) -> str:
        """Safely escapes LaTeX special control characters inside job metadata."""
        replacements = {
            "&": r"\&",
            "%": r"\%",
            "$": r"\$",
            "#": r"\#",
            "_": r"\_",
            "{": r"\{",
            "}": r"\}",
            "~": r"\textasciitilde{}",
            "^": r"\textasciicircum{}",
        }
        return "".join(replacements.get(c, c) for c in text)

    def get_attachment(self, job: JobRecord) -> Path | None:
        log.info(f"Tailoring CV for: {job.title} at {job.company}")
        
        if not self.tex_path.exists():
            log.warning("Template %s missing, cannot tailor CV.", self.tex_path)
            return None

        with open(self.tex_path, "r", encoding="utf-8") as f:
            latex_content = f.read()

        # 1. Clean & match target position title (Awesome-CV format)
        # Standardize "Ingénieur IA" or "Data Scientist" based on the actual posting
        target_title = self._escape_latex(job.title)
        
        # Pattern matching \position{...}
        latex_content = re.sub(
            r"\\position\{[^}]+\}",
            f"\\position{{{target_title}}}",
            latex_content
        )

        # 2. Update the Footer meta-text \makecvfooter{\today}{...}{\thepage}
        escaped_company = self._escape_latex(job.company)
        new_footer = f"\\makecvfooter{{\\today}}{{Said Ibenariba~~~·~~~CV — {target_title} @ {escaped_company}}}{{\\thepage}}"
        latex_content = re.sub(
            r"\\makecvfooter\{\\today\}\{[^}]+\}\{\\thepage\}",
            new_footer,
            latex_content
        )

        # 3. Save as temporary job-specific .tex file
        self.build_dir.mkdir(parents=True, exist_ok=True)
        tailored_tex_path = self.build_dir / f"cv_tailored_{job.id}.tex"
        
        with open(tailored_tex_path, "w", encoding="utf-8") as f:
            f.write(latex_content)

        # 4. Compile the customized LaTeX
        pdf_name = f"cv_{escaped_company.replace(' ', '_')}_{job.id[:8]}"
        compiled_pdf = self._build(tailored_tex_path, pdf_name)

        # Clean up the temporary .tex and log files to keep build clean
        try:
            tailored_tex_path.unlink()
            for ext in [".log", ".out", ".aux", ".xdv"]:
                log_file = tailored_tex_path.with_suffix(ext)
                if log_file.exists():
                    log_file.unlink()
        except OSError:
            pass

        return compiled_pdf
