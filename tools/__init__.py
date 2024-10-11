import os
import importlib
import logging
from typing import List, Dict, Any
from .base_tool import BaseTool

def load_tools() -> List[Dict[str, Any]]:
    tools = []
    tools_dir = os.path.dirname(__file__)
    
    for filename in os.listdir(tools_dir):
        if filename.endswith('.py') and filename != '__init__.py' and filename != 'base_tool.py':
            module_name = filename[:-3]  # Remove .py extension
            module = importlib.import_module(f'.{module_name}', package='tools')
            
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, BaseTool) and attr != BaseTool:
                    tool_instance = attr()
                    tools.append({
                        "type": "function",
                        "name": tool_instance.name,
                        "description": tool_instance.description,
                        "parameters": tool_instance.parameters
                    })
    
    logging.info(f"Loaded tools: {[tool['name'] for tool in tools]}")
    return tools

async def execute_tool(tool_name: str, **kwargs):
    tools_dir = os.path.dirname(__file__)
    
    for filename in os.listdir(tools_dir):
        if filename.endswith('.py') and filename != '__init__.py' and filename != 'base_tool.py':
            module_name = filename[:-3]
            module = importlib.import_module(f'.{module_name}', package='tools')
            
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, BaseTool) and attr != BaseTool:
                    tool_instance = attr()
                    if tool_instance.name == tool_name:
                        print(f"Executing tool: {tool_name} with args: {kwargs}")  # Enhanced debugging
                        return await tool_instance.execute(**kwargs)
    
    print(f"Tool '{tool_name}' not found")  # Add this line for debugging
    raise ValueError(f"Tool '{tool_name}' not found")
