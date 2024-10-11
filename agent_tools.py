from tools import load_tools, execute_tool

# Load all tools
tools = load_tools()

# Update function_map to use execute_tool
async def execute_tool_wrapper(tool_name, **kwargs):
    print(f"Attempting to execute tool: {tool_name} with args: {kwargs}")  # Enhanced debugging
    return await execute_tool(tool_name, **kwargs)

function_map = {tool['name']: execute_tool_wrapper for tool in tools}

# Print loaded tools for debugging
print("Loaded tools:")
for tool in tools:
    print(f"- {tool['name']}")