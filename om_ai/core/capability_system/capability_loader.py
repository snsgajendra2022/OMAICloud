"""Load built-in capability catalog."""
from __future__ import annotations

from .tool_schema import ToolSchema


class CapabilityLoader:
    BUILTIN = [
        ToolSchema("browser", "Browser", "web", "Open URLs / search", risk="medium", requires_permission=True),
        ToolSchema("files", "Files", "fs", "Read/write files", risk="high", requires_permission=True),
        ToolSchema("terminal", "Terminal", "shell", "Run shell commands", risk="high", requires_permission=True),
        ToolSchema("vscode", "VS Code", "ide", "Open projects in editor", risk="low"),
        ToolSchema("database", "Database", "data", "Query databases", risk="high", requires_permission=True),
        ToolSchema("git", "Git", "vcs", "Git status / commit / push", risk="medium", requires_permission=True),
        ToolSchema("email", "Email", "comms", "Draft / send email", risk="high", requires_permission=True),
        ToolSchema("calendar", "Calendar", "comms", "Calendar events", risk="medium", requires_permission=True),
        ToolSchema("crm", "CRM", "business", "CRM lookups", risk="medium", requires_permission=True),
        ToolSchema("erp", "ERP", "business", "ERP queries", risk="medium", requires_permission=True),
        ToolSchema("apis", "APIs", "net", "Call external APIs", risk="medium", requires_permission=True),
        ToolSchema("volume", "Volume", "device", "System volume", risk="low"),
        ToolSchema("apps", "Apps", "device", "Launch applications", risk="medium", requires_permission=True),
    ]

    def load(self) -> list[ToolSchema]:
        return list(self.BUILTIN)
