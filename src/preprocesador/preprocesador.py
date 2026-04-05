"""
Preprocesador para archivos .asmc.
- Soporta #include y #define (sin parametros).
- Comentarios de linea: // y ;
- Devuelve texto preprocesado + mapa de lineas.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import os
import re


@dataclass
class SourceLine:
    path: str
    line: int


@dataclass
class PreprocessResult:
    text: str
    line_map: List[SourceLine]


class PreprocesadorError(Exception):
    pass


class IncludeError(PreprocesadorError):
    pass


class MacroError(PreprocesadorError):
    pass


class Preprocesador:
    def __init__(self, library_dir: Optional[str] = None, max_include_depth: int = 25, max_macro_expansion: int = 50):
        self.project_root = self._get_project_root()
        self.library_dir = self._resolve_library_dir(library_dir)
        self.max_include_depth = max_include_depth
        self.max_macro_expansion = max_macro_expansion
        self._defines: Dict[str, str] = {}
        self._define_pattern: Optional[re.Pattern[str]] = None
        self._include_stack: List[str] = []

    def preprocess_file(self, file_path: str) -> PreprocessResult:
        self._defines = {}
        self._define_pattern = None
        self._include_stack = []

        lines, line_map = self._process_file(file_path, depth=0)
        text = "\n".join(lines)
        if text:
            text += "\n"
        return PreprocessResult(text=text, line_map=line_map)

    def _process_file(self, file_path: str, depth: int) -> Tuple[List[str], List[SourceLine]]:
        if depth > self.max_include_depth:
            raise IncludeError("Max include depth exceeded")

        abs_path = os.path.abspath(file_path)
        if not os.path.isfile(abs_path):
            raise IncludeError(f"Include file not found: {abs_path}")

        if abs_path in self._include_stack:
            ciclo = " -> ".join(self._include_stack + [abs_path])
            raise IncludeError(f"Include cycle detected: {ciclo}")

        self._include_stack.append(abs_path)
        lines: List[str] = []
        line_map: List[SourceLine] = []

        try:
            with open(abs_path, "r", encoding="utf-8") as handle:
                for line_no, raw_line in enumerate(handle, start=1):
                    line = raw_line.rstrip("\n")
                    line = self._strip_comment(line)
                    if not line.strip():
                        continue

                    include_name = self._match_include(line)
                    if include_name:
                        include_path = self._resolve_include(include_name)
                        inc_lines, inc_map = self._process_file(include_path, depth + 1)
                        lines.extend(inc_lines)
                        line_map.extend(inc_map)
                        continue

                    define = self._match_define(line)
                    if define:
                        name, value = define
                        if not value:
                            value = "1"
                        self._defines[name] = value
                        self._define_pattern = None
                        continue

                    expanded = self._expand_defines(line)
                    if expanded.strip():
                        lines.append(expanded.rstrip())
                        line_map.append(SourceLine(path=abs_path, line=line_no))
        finally:
            self._include_stack.pop()

        return lines, line_map

    def _get_project_root(self) -> str:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    def _resolve_library_dir(self, library_dir: Optional[str]) -> str:
        if not library_dir:
            library_dir = os.path.join("src", "Libraries")

        if os.path.isabs(library_dir):
            return os.path.abspath(library_dir)

        return os.path.abspath(os.path.join(self.project_root, library_dir))

    def _resolve_include(self, include_name: str) -> str:
        include_path = os.path.abspath(os.path.join(self.library_dir, include_name))
        library_root = os.path.abspath(self.library_dir)

        if os.path.commonpath([include_path, library_root]) != library_root:
            raise IncludeError(f"Include outside library dir: {include_name}")

        if not os.path.isfile(include_path):
            raise IncludeError(f"Include file not found: {include_path}")

        return include_path

    def _match_include(self, line: str) -> Optional[str]:
        match = re.match(r"^\s*#include\s+\"([^\"]+)\"\s*$", line)
        if match:
            return match.group(1)
        return None

    def _match_define(self, line: str) -> Optional[Tuple[str, str]]:
        match = re.match(r"^\s*#define\s+([A-Za-z_][A-Za-z0-9_]*)\s*(.*)$", line)
        if match:
            return match.group(1), match.group(2).strip()
        return None

    def _expand_defines(self, line: str) -> str:
        if not self._defines:
            return line

        pattern = self._get_define_pattern()
        if pattern is None:
            return line

        current = line
        for _ in range(self.max_macro_expansion):
            updated = pattern.sub(lambda m: self._defines[m.group(1)], current)
            if updated == current:
                return current
            current = updated

        raise MacroError("Macro expansion limit exceeded")

    def _get_define_pattern(self) -> Optional[re.Pattern[str]]:
        if not self._defines:
            return None

        if self._define_pattern is None:
            names = sorted(self._defines.keys(), key=len, reverse=True)
            pattern = r"\\b(" + "|".join(re.escape(name) for name in names) + r")\\b"
            self._define_pattern = re.compile(pattern)

        return self._define_pattern

    def _strip_comment(self, line: str) -> str:
        idx = self._find_comment_start(line)
        if idx is None:
            return line
        return line[:idx]

    def _find_comment_start(self, line: str) -> Optional[int]:
        in_single = False
        in_double = False
        i = 0
        while i < len(line):
            ch = line[i]
            if ch == "'" and not in_double:
                in_single = not in_single
            elif ch == '"' and not in_single:
                in_double = not in_double
            elif not in_single and not in_double:
                if line.startswith("//", i):
                    return i
                if ch == ";":
                    return i
            i += 1
        return None
