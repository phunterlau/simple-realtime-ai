import webbrowser
from typing import Dict, Any
from .base_tool import BaseTool

class OpenBrowserTool(BaseTool):
    @property
    def name(self) -> str:
        return "open_browser"

    @property
    def description(self) -> str:
        return "Opens a browser tab with the specified URL."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to open in the browser.",
                },
            },
            "required": ["url"],
        }

    async def execute(self, url: str) -> Dict[str, str]:
        try:
            webbrowser.open(url)
            return {"status": "Browser opened", "url": url}
        except Exception as e:
            return {"status": "Error", "message": str(e)}