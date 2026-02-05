import os
import re
import shutil
import subprocess
import json
from typing import List, Dict, Any
from .base import BaseRunner

class PHPRunner(BaseRunner):

    def __init__(self):
        super().__init__()
        self.php_path = shutil.which("php")
        self.composer_path = shutil.which("composer")
        if not self.php_path:
            raise RuntimeError("PHP is not installed or not available in PATH")

    def get_dependencies(self, code: str) -> List[str]:
        """Analyzes PHP code to extract Composer package dependencies."""
        dependencies = set()
        patterns = [
            r"use\s+([a-zA-Z0-9_\\\\]+);",
            r"require[_once]*\s*\(\s*[\'\"]([^\'\"/][^\'\"]+)[\'\"]\s*\)",
            r"include[_once]*\s*\(\s*[\'\"]([^\'\"/][^\'\"]+)[\'\"]\s*\)"
        ]
        composer_pattern = re.compile(
            r"^[a-z0-9]([_.-]?[a-z0-9]+)*/[a-z0-9]([_.-]?[a-z0-9]+)*$",
            re.IGNORECASE
        )

        for pattern in patterns:
            for match in re.finditer(pattern, code):
                dep = match.group(1).replace("\\\\", "/").lower()
                if composer_pattern.match(dep):
                    dependencies.add(dep)

        return list(dependencies)

    def install_dependencies(self, dependencies: List[str], venv_path: str):
        """Installs PHP dependencies using Composer."""
        if not dependencies or not self.composer_path:
            return

        composer_json = {
            "require": {dep: "*" for dep in dependencies}
        }

        composer_json_path = os.path.join(venv_path, "composer.json")
        with open(composer_json_path, "w") as f:
            json.dump(composer_json, f)

        result = subprocess.run(
            [self.composer_path, "install", "--no-interaction"],
            cwd=venv_path,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"Composer install failed: {result.stderr}")

    def _get_file_extension(self) -> str:
        return ".php"

    def _prepare_code(
        self,
        code: str,
        inputs: Dict[str, Any],
        env_vars: Dict[str, str]
    ) -> str:
        """Prepares the PHP code by injecting inputs and environment variables."""

        env_code = "\n".join(
            [f"putenv('{k}={v}');" for k, v in env_vars.items()]
        )
        if env_code:
            code = f"{env_code}\n{code}"

        input_code = "\n".join(
            [f"${k} = {json.dumps(v)};" for k, v in inputs.items()]
        )
        if input_code:
            code = f"{input_code}\n{code}"

        code += """
// Result wrapper
$result = null;
try {
    if (isset($output)) {
        $result = $output;
    }
} catch (Exception $e) {
    fwrite(STDERR, 'Error capturing result: ' . $e->getMessage() . PHP_EOL);
}

echo '__RESULT_START__' . PHP_EOL;
echo json_encode($result) . PHP_EOL;
echo '__RESULT_END__' . PHP_EOL;
"""
        return code

    def _run_directly(
        self,
        code_file_path: str,
        inputs: Dict[str, Any],
        env_vars: Dict[str, str],
        execution_timeout: int
    ) -> subprocess.CompletedProcess:
        """Runs PHP code directly without dependencies."""
        return subprocess.run(
            [self.php_path, code_file_path],
            capture_output=True,
            text=True,
            timeout=execution_timeout,
            env={**os.environ, **env_vars}
        )

    def _run_with_dependencies(
        self,
        code_file_path: str,
        dependencies: List[str],
        inputs: Dict[str, Any],
        env_vars: Dict[str, str],
        execution_timeout: int
    ) -> subprocess.CompletedProcess:
        """Runs PHP code with Composer dependencies."""
        venv_dir = os.path.dirname(code_file_path)
        self.install_dependencies(dependencies, venv_dir)

        autoloader_path = os.path.join(venv_dir, "vendor/autoload.php")
        if os.path.exists(autoloader_path):
            wrapper_path = os.path.join(venv_dir, "wrapper.php")
            try:
                wrapper_code = f"""<?php
require_once '{autoloader_path}';
require_once '{code_file_path}';
"""
                with open(wrapper_path, "w") as f:
                    f.write(wrapper_code)

                return subprocess.run(
                    [self.php_path, wrapper_path],
                    capture_output=True,
                    text=True,
                    timeout=execution_timeout,
                    env={**os.environ, **env_vars}
                )
            finally:
                if os.path.exists(wrapper_path):
                    os.remove(wrapper_path)

        return self._run_directly(
            code_file_path,
            inputs,
            env_vars,
            execution_timeout
        )

    def _process_output(self, stdout: str) -> tuple[str, Dict[str, Any]]:
        """Extracts normal output and structured result."""
        try:
            parts = stdout.split("__RESULT_START__")
            if len(parts) != 2:
                return stdout, {}

            normal_output = parts[0].strip()
            result_part = parts[1].split("__RESULT_END__")[0].strip()

            try:
                result_data = json.loads(result_part) if result_part else {}
            except json.JSONDecodeError:
                result_data = {}

            return normal_output, result_data
        except Exception:
            return stdout, {}
