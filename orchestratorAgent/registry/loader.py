import yaml
from pathlib import Path
from schemas.registry import ToolDefinition
from typing import Union, Dict, List

class ToolRegistry:
    def __init__(self, tools: List[ToolDefinition]):
        self.tools = tools
        self._by_name = {tool.name: tool for tool in tools}

    def get_by_name(self, name: str) -> ToolDefinition:
        return self._by_name.get(name)

    def list_tools(self) -> List[ToolDefinition]:
        return self.tools

    def list_capabilities(self) -> Dict[str, List[str]]:
        return {
            tool.name: tool.capabilities
            for tool in self.tools
        }


def load_tools_from_yaml(path: Union[str, Path]) -> Dict[str, ToolDefinition]:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Tool config not found: {path}")

    with open(path, "r") as f:
        raw = yaml.safe_load(f)

    if "tools" not in raw:
        raise ValueError("YAML must contain a top-level 'tools' key")

    tools = [ToolDefinition(**tool) for tool in raw["tools"]]

    return {tool.name: tool for tool in tools}
