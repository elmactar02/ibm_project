"""
tools/file_tools.py — File system tools used by DevOps and Developer agents.
Every tool logs its invocation and result.
"""

import os
import shutil
from langchain_core.tools import tool
from core.logger import log_tool_call, log_tool_result, log_error


@tool
def write_file(path: str, content: str) -> str:
    """Write (or overwrite) a file, creating parent directories as needed."""
    log_tool_call("developer", "write_file", {"path": path, "content_length": f"{len(content)} chars"})
    try:
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        result = f"✓ Written {len(content)} chars → {path}"
        log_tool_result("write_file", result)
        return result
    except Exception as e:
        log_error("developer", str(e))
        return f"ERROR: {e}"


@tool
def read_file(path: str) -> str:
    """Read and return the full content of a file."""
    log_tool_call("developer", "read_file", {"path": path})
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
        log_tool_result("read_file", f"{len(content)} chars read from {path}")
        return content
    except Exception as e:
        log_error("developer", str(e))
        return f"ERROR: {e}"


@tool
def list_directory(path: str) -> str:
    """Recursively list all files in a directory."""
    log_tool_call("devops", "list_directory", {"path": path})
    try:
        result = []
        for root, dirs, files in os.walk(path):
            # Skip hidden dirs
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for file in files:
                result.append(os.path.relpath(os.path.join(root, file), path))
        output = "\n".join(sorted(result))
        log_tool_result("list_directory", f"{len(result)} files found")
        return output
    except Exception as e:
        log_error("devops", str(e))
        return f"ERROR: {e}"


@tool
def create_directory(path: str) -> str:
    """Create a directory (and all parent directories) if it does not exist."""
    log_tool_call("devops", "create_directory", {"path": path})
    try:
        os.makedirs(path, exist_ok=True)
        result = f"✓ Directory ready: {path}"
        log_tool_result("create_directory", result)
        return result
    except Exception as e:
        log_error("devops", str(e))
        return f"ERROR: {e}"


@tool
def delete_file(path: str) -> str:
    """Delete a file or empty directory."""
    log_tool_call("qa", "delete_file", {"path": path})
    try:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        result = f"✓ Deleted: {path}"
        log_tool_result("delete_file", result)
        return result
    except Exception as e:
        log_error("qa", str(e))
        return f"ERROR: {e}"