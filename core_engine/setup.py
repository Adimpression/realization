"""Distribution assembly for the canonical root-hosted governed engine."""

from pathlib import Path
import shutil

from setuptools import setup
from setuptools.command.build_py import build_py
from setuptools.command.sdist import sdist


PROJECT_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = PROJECT_ROOT.parent
MODULE_MANIFEST = PROJECT_ROOT / "module_manifest.txt"
PACKAGED_MODULE_ROOT = PROJECT_ROOT / "_canonical_modules"
EGG_INFO_ROOT = PROJECT_ROOT / ".build"
EGG_INFO_ROOT.mkdir(exist_ok=True)


def _canonical_modules() -> list[str]:
    return [
        line
        for raw_line in MODULE_MANIFEST.read_text(encoding="utf-8").splitlines()
        if (line := raw_line.strip()) and not line.startswith("#")
    ]


def _canonical_source_root(modules: list[str]) -> Path:
    for candidate in (REPOSITORY_ROOT, PACKAGED_MODULE_ROOT):
        if all((candidate / f"{module}.py").is_file() for module in modules):
            return candidate
    raise FileNotFoundError("canonical engine modules are unavailable")


CANONICAL_MODULES = _canonical_modules()
CANONICAL_SOURCE_ROOT = _canonical_source_root(CANONICAL_MODULES)
CANONICAL_PACKAGE_DIR = (
    ".."
    if CANONICAL_SOURCE_ROOT == REPOSITORY_ROOT
    else PACKAGED_MODULE_ROOT.name
)


class CleanBuildPy(build_py):
    """Prevent removed manifest modules from leaking out of a stale build tree."""

    def run(self) -> None:
        shutil.rmtree(self.build_lib, ignore_errors=True)
        super().run()


class CanonicalSdist(sdist):
    """Embed the root-hosted engine modules in a self-contained source archive."""

    def make_release_tree(self, base_dir: str, files: list[str]) -> None:
        project_files = [path for path in files if not str(path).startswith("../")]
        super().make_release_tree(base_dir, project_files)

        release_root = Path(base_dir)
        module_root = release_root / PACKAGED_MODULE_ROOT.name
        module_root.mkdir(exist_ok=True)
        for module in CANONICAL_MODULES:
            shutil.copy2(
                CANONICAL_SOURCE_ROOT / f"{module}.py",
                module_root / f"{module}.py",
            )
        shutil.copy2(MODULE_MANIFEST, release_root / MODULE_MANIFEST.name)


setup(
    packages=["realized_core_engine"],
    py_modules=CANONICAL_MODULES,
    package_dir={
        "": CANONICAL_PACKAGE_DIR,
        "realized_core_engine": "src/realized_core_engine",
    },
    package_data={"realized_core_engine": ["py.typed"]},
    cmdclass={"build_py": CleanBuildPy, "sdist": CanonicalSdist},
    options={"egg_info": {"egg_base": str(EGG_INFO_ROOT)}},
)
