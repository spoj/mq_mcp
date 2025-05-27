# server.py
import sys
from pathlib import Path
from mcp.server.fastmcp import FastMCP
import os

# Global variables
GEMINI_API_KEY = os.environ['GOOGLE_API_KEY']
ROOT_DIRECTORY = None

# Create an MCP server
mcp = FastMCP("map_query")


@mcp.tool()
def directory_tree() -> list[str]:
    """Recursively list all files in the root directory, with paths relative to root."""
    if not ROOT_DIRECTORY.is_dir():
        return [f"Error: {ROOT_DIRECTORY} is not a directory or does not exist."]
    
    files = []
    for item in ROOT_DIRECTORY.rglob("*"):
        if item.is_file():
            files.append("/" + str(item.relative_to(ROOT_DIRECTORY)))
    return files

def main():
    """Main entry point for the MCP server"""
    global GEMINI_API_KEY, ROOT_DIRECTORY
    
    if len(sys.argv) < 3:
        print("Usage: python server.py <gemini_api_key> <root_directory>")
        sys.exit(1)
    
    ROOT_DIRECTORY = Path(sys.argv[1])
    
    print(f"Root Directory: {ROOT_DIRECTORY}")
    
    mcp.run()

if __name__ == "__main__":
    main()