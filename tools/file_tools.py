import os
import shutil
from typing import Dict, Any
from .base_tool import BaseTool

SCRATCH_PAD_DIR = os.getenv("SCRATCH_PAD_DIR", "./scratchpad")

class CreateFileTool(BaseTool):
    @property
    def name(self) -> str:
        return "create_file"

    @property
    def description(self) -> str:
        return "Creates a new file with the given content."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_name": {
                    "type": "string",
                    "description": "The name of the file to create.",
                },
                "content": {
                    "type": "string",
                    "description": "The content to write to the file.",
                },
            },
            "required": ["file_name", "content"],
        }

    async def execute(self, file_name: str, content: str) -> Dict[str, str]:
        os.makedirs(SCRATCH_PAD_DIR, exist_ok=True)
        file_path = os.path.join(SCRATCH_PAD_DIR, file_name)

        if os.path.exists(file_path):
            return {"status": "error", "message": "File already exists"}

        with open(file_path, "w") as f:
            f.write(content)

        return {"status": "success", "message": f"File '{file_name}' created successfully"}

class UpdateFileTool(BaseTool):
    @property
    def name(self) -> str:
        return "update_file"

    @property
    def description(self) -> str:
        return "Updates an existing file with new content or renames it."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_name": {
                    "type": "string",
                    "description": "The name of the file to update.",
                },
                "new_content": {
                    "type": "string",
                    "description": "The new content to write to the file. If empty, the file content won't be changed.",
                },
                "new_name": {
                    "type": "string",
                    "description": "The new name for the file if it needs to be renamed.",
                },
            },
            "required": ["file_name"],
        }

    async def execute(self, file_name: str, new_content: str = None, new_name: str = None) -> Dict[str, str]:
        file_path = os.path.join(SCRATCH_PAD_DIR, file_name)

        if not os.path.exists(file_path):
            return {"status": "error", "message": "File not found"}

        if new_content is not None:
            with open(file_path, "w") as f:
                f.write(new_content)

        if new_name:
            new_file_path = os.path.join(SCRATCH_PAD_DIR, new_name)
            os.rename(file_path, new_file_path)
            return {"status": "success", "message": f"File renamed to '{new_name}' and updated"}

        return {"status": "success", "message": f"File '{file_name}' updated successfully"}

class DeleteFileTool(BaseTool):
    @property
    def name(self) -> str:
        return "delete_file"

    @property
    def description(self) -> str:
        return "Deletes a file based on the file name."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_name": {
                    "type": "string",
                    "description": "The name of the file to delete.",
                },
            },
            "required": ["file_name"],
        }

    async def execute(self, file_name: str) -> Dict[str, str]:
        file_path = os.path.join(SCRATCH_PAD_DIR, file_name)

        if not os.path.exists(file_path):
            return {"status": "error", "message": "File not found"}

        os.remove(file_path)
        return {"status": "success", "message": f"File '{file_name}' deleted successfully"}