"""
Standardized tool set for agentic AI benchmarking.
All tools are implemented as simple Python functions with consistent interfaces.
"""

from tools.search import search
from tools.web_lookup import web_lookup
from tools.calculator import calculator
from tools.python_exec import python_exec
from tools.shell_exec import shell_exec
from tools.http_request import http_request
from tools.database_query import database_query
from tools.file_ops import read_file, write_file, list_files

# Tool registry: name -> (function, description, parameter schema)
# Used by framework adapters to register tools with each framework's API.
TOOL_REGISTRY = {
    "search": {
        "function": search,
        "description": "Search a knowledge base by keyword query. Returns a list of relevant text snippets.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query string"}
            },
            "required": ["query"],
        },
    },
    "web_lookup": {
        "function": web_lookup,
        "description": "Look up a pre-cached document on a given topic. Returns the document text.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "The topic to look up"}
            },
            "required": ["topic"],
        },
    },
    "calculator": {
        "function": calculator,
        "description": "Evaluate a mathematical expression. Supports +, -, *, /, **, %, sqrt, abs, round, int, float. Returns the numeric result.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "The mathematical expression to evaluate"}
            },
            "required": ["expression"],
        },
    },
    "python_exec": {
        "function": python_exec,
        "description": "Execute Python code and return stdout and stderr. Code runs in an isolated subprocess.",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python code to execute"}
            },
            "required": ["code"],
        },
    },
    "shell_exec": {
        "function": shell_exec,
        "description": "Execute a shell command (sandboxed, whitelisted commands only). Returns stdout and stderr.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command to run"}
            },
            "required": ["command"],
        },
    },
    "http_request": {
        "function": http_request,
        "description": "Make an HTTP request to the local mock API server. Returns status code and response body.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL to request (e.g., http://127.0.0.1:8100/api/products)"},
                "method": {"type": "string", "description": "HTTP method: GET, POST, PUT, DELETE", "default": "GET"},
                "headers": {"type": "object", "description": "Optional HTTP headers", "default": {}},
                "body": {"type": "string", "description": "Optional request body (JSON string)", "default": ""},
            },
            "required": ["url"],
        },
    },
    "database_query": {
        "function": database_query,
        "description": "Execute a SQL query on the benchmark SQLite database. Returns rows as a list of dicts for SELECT, or affected row count for INSERT/UPDATE/DELETE.",
        "parameters": {
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "The SQL query to execute"}
            },
            "required": ["sql"],
        },
    },
    "read_file": {
        "function": read_file,
        "description": "Read the contents of a file from the sandbox directory. Returns file content as a string.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative path within the sandbox directory"}
            },
            "required": ["path"],
        },
    },
    "write_file": {
        "function": write_file,
        "description": "Write content to a file in the sandbox directory. Creates parent directories if needed.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative path within the sandbox directory"},
                "content": {"type": "string", "description": "The content to write"},
            },
            "required": ["path", "content"],
        },
    },
    "list_files": {
        "function": list_files,
        "description": "List files and directories in a sandbox directory path. Returns a list of names.",
        "parameters": {
            "type": "object",
            "properties": {
                "directory": {"type": "string", "description": "Relative directory path within the sandbox (use '.' for root)", "default": "."}
            },
            "required": [],
        },
    },
}
