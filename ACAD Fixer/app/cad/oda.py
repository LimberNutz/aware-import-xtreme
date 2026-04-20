import subprocess
import os
import logging
from pathlib import Path


class ODAConverter:
    """Wrapper for ODA File Converter (Windows GUI subprocess).

    IMPORTANT: ODA's GUI process deadlocks with subprocess capture_output=True.
    Always redirect stdout/stderr to a file and use shell=True.
    """

    def __init__(self, exe_path: str, log_dir: str = None, timeout: int = 300):
        self.exe_path = exe_path
        self.log_dir = Path(log_dir) if log_dir else None
        self.timeout = timeout

    def _run(self, input_dir: str, output_dir: str, out_ext: str, in_ext: str,
             version: str = "ACAD2018") -> bool:
        os.makedirs(output_dir, exist_ok=True)
        filter_arg = f"*.{in_ext.upper()}"
        cmd = (
            f'"{self.exe_path}" "{input_dir}" "{output_dir}" '
            f'{version} {out_ext.upper()} 0 1 "{filter_arg}"'
        )
        log_path = None
        if self.log_dir:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            log_path = self.log_dir / f"oda_{in_ext}_to_{out_ext}.log"
        logging.info(f"ODA: {in_ext.upper()} -> {out_ext.upper()} | {input_dir} -> {output_dir}")
        try:
            if log_path:
                with open(log_path, "a", encoding="utf-8") as logf:
                    logf.write(f"\n==== CMD: {cmd}\n")
                    logf.flush()
                    result = subprocess.run(
                        cmd, shell=True, stdout=logf, stderr=logf,
                        timeout=self.timeout
                    )
            else:
                result = subprocess.run(
                    cmd, shell=True,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    timeout=self.timeout
                )
            if result.returncode != 0:
                logging.error(f"ODA returned {result.returncode} (see log: {log_path})")
                return False
            return True
        except subprocess.TimeoutExpired:
            logging.error(f"ODA timed out after {self.timeout}s")
            return False
        except Exception as e:
            logging.error(f"Failed to run ODA: {e}")
            return False

    def dwg_to_dxf(self, input_dir: str, output_dir: str, version: str = "ACAD2018") -> bool:
        return self._run(input_dir, output_dir, "DXF", "DWG", version)

    def dxf_to_dwg(self, input_dir: str, output_dir: str, version: str = "ACAD2018") -> bool:
        return self._run(input_dir, output_dir, "DWG", "DXF", version)
