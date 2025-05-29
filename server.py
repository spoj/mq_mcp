"""
MCP File Query Server

This server provides tools for querying files in a directory using LLMs:
 - 'directory_tree' recursively lists all files in the dir
 - 'ls' tool lists one level of a specified path. this is useful for iteratively exploring files when the directory contains too many files for the 'directory_tree' tool.
 - 'map_query_tool' runs a query against all files specified
 - 'map_query_tool_regex' is similar to 'map_query_tool' except it runs the query against all files whose filename matches a regex
 - 'map_query_tool_regex_sampled' is similar to 'map_query_tool_regex' except it takes a random sample (without replacement) of at most sample_size
 - 'get_overview' extracts a brief overview of at most 100 files in the directory. If number of files >100, then a random sample of files is chosen.

Systematic Methodology:

1. **Initial Discovery**
   - Use 'get_overview' to understand the general content of files
   - Use 'directory_tree' to see the structure and file organization
   - Note if the directory is large (>100 files) as overview will be sampled

2. **Targeted Analysis**
   - Use 'map_query_tool' with specific files to gather detailed information
   - For large directories, use 'map_query_tool_regex' to filter by file patterns
   - Use 'map_query_tool_regex_sampled' for sampling if there are many matches
   - Run multiple queries from different angles to be thorough

3. **Deep Investigation**
   - For specific files of interest, read them directly using the file resources
   - Cross-reference information between files
   - Look for patterns, inconsistencies, or missing information

4. **Synthesis**
   - Combine findings from all sources
   - If information is incomplete, ask clarifying questions
   - Provide a comprehensive answer based on the evidence found

Remember: Be thorough, avoid assumptions, and use multiple queries if needed to get complete information.
"""

import asyncio
import json
import mimetypes
import random
import re
from pathlib import Path
from typing import Any, Iterator

from google import genai
from google.genai import types
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent, EmbeddedResource, Resource
from tenacity import retry, stop_after_attempt

# Constants
MAX_CONCURRENT_TASKS = 50
MODEL_NAME = "gemini-2.5-flash-preview-05-20"
MAX_FILES_FOR_DIR_TREE = 100
OVERVIEW_MAX_FILES = 100
OVERVIEW_FILENAME = "_OVERVIEW.json"

# Initialize FastMCP server
mcp = FastMCP("file-query-server")


class FileQueryService:
    def __init__(self, root_directory: str):
        self.root_directory = Path(root_directory).resolve()
        if not self.root_directory.exists():
            raise ValueError(f"Directory {root_directory} does not exist")
        if not self.root_directory.is_dir():
            raise ValueError(f"{root_directory} is not a directory")

    def file_to_part(self, file_path: Path) -> types.Part | None:
        """Convert file to Gemini Part object."""
        try:
            with open(file_path, "rb") as f:
                bytes_content = f.read()
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if mime_type is None:
                mime_type = "application/octet-stream"
            return types.Part.from_bytes(data=bytes_content, mime_type=mime_type)
        except Exception:
            return None

    @retry(stop=stop_after_attempt(3))
    async def _process_single_file(
        self, file_path: Path, query: str, max_tokens: int = 4096
    ) -> str:
        """Process a single file against the query using Gemini."""
        try:
            part = self.file_to_part(file_path)
            if part is None:
                return f"Error: Could not read file {file_path}"

            messages = [
                part,
                "answer the following query about the preceding file. Use dense language to convey the most using fewest words. Your answer must be grounded in the document.",
                query,
            ]

            client = genai.Client()
            response = await client.aio.models.generate_content(
                model=MODEL_NAME,
                contents=messages,
                config=types.GenerateContentConfig(
                    max_output_tokens=max_tokens,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
            )
            return response.candidates[0].content.parts[0].text
        except Exception as e:
            return f"Error processing file {file_path}: {e}"

    def directory_tree_full(self) -> Iterator[str]:
        """Recursively list all files in the root directory."""
        if not self.root_directory.is_dir():
            return

        for item in self.root_directory.rglob("*"):
            if item.is_file():
                relative_path = str(item.relative_to(self.root_directory))
                if relative_path != OVERVIEW_FILENAME:
                    yield relative_path

    async def map_query_files(self, query: str, filenames: list[str]) -> dict[str, str]:
        """Process multiple files concurrently with a query."""
        if not isinstance(filenames, list):
            return {"error": "Filenames must be a list of strings"}

        target_files = []
        for filename in filenames:
            file_path = self.root_directory / filename
            if file_path.is_file():
                target_files.append(file_path)

        if not target_files:
            return {"error": "No valid target files found"}

        # Process files concurrently
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

        async def process_with_semaphore(file_path):
            async with semaphore:
                return await self._process_single_file(file_path, query)

        tasks = [
            asyncio.create_task(process_with_semaphore(file_path))
            for file_path in target_files
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Format results
        result_dict = {}
        for i, result in enumerate(results):
            relative_path = str(target_files[i].relative_to(self.root_directory))
            if isinstance(result, Exception):
                result_dict[relative_path] = f"Task failed: {result}"
            else:
                result_dict[relative_path] = result

        return result_dict


# Global service instance - will be set when server is configured
service: FileQueryService = None


@mcp.tool()
async def map_query_tool(query: str, filenames: list[str]) -> str:
    """
    Query multiple files concurrently using an LLM.

    Args:
        query: The question to ask about each file
        filenames: List of file paths relative to the configured directory
    """
    if service is None:
        return "Error: Server not configured with a directory"

    result = await service.map_query_files(query, filenames)
    return json.dumps(result, indent=2)


@mcp.tool()
async def map_query_tool_regex(query: str, filename_regex: str) -> str:
    """
    Query files matching a regex pattern using an LLM.

    Args:
        query: The question to ask about each file
        filename_regex: Regular expression pattern to match filenames
    """
    if service is None:
        return "Error: Server not configured with a directory"

    try:
        regex = re.compile(filename_regex)
        all_files = list(service.directory_tree_full())
        target_files = [f for f in all_files if regex.search(f)]

        result = await service.map_query_files(query, target_files)
        return json.dumps(result, indent=2)
    except re.error as e:
        return f"Error: Invalid regex pattern: {e}"


@mcp.tool()
async def map_query_tool_regex_sampled(
    query: str, filename_regex: str, sample_size: int
) -> str:
    """
    Query a random sample of files matching a regex pattern using an LLM.

    Args:
        query: The question to ask about each file
        filename_regex: Regular expression pattern to match filenames
        sample_size: Maximum number of files to sample
    """
    if service is None:
        return "Error: Server not configured with a directory"

    try:
        regex = re.compile(filename_regex)
        all_files = list(service.directory_tree_full())
        target_files = [f for f in all_files if regex.search(f)]

        # Random sample
        random.shuffle(target_files)
        sampled_files = target_files[:sample_size]

        result = await service.map_query_files(query, sampled_files)
        return json.dumps(result, indent=2)
    except re.error as e:
        return f"Error: Invalid regex pattern: {e}"


@mcp.tool()
def directory_tree() -> str:
    """
    List all files in the configured directory recursively.
    Returns a truncated list if there are too many files.
    """
    if service is None:
        return "Error: Server not configured with a directory"

    import itertools

    files = list(
        itertools.islice(service.directory_tree_full(), MAX_FILES_FOR_DIR_TREE)
    )
    result = {"truncated": len(files) == MAX_FILES_FOR_DIR_TREE, "files": files}
    return json.dumps(result, indent=2)


@mcp.tool()
def ls(path: str = "") -> str:
    """
    List files and directories in the specified path.

    Args:
        path: Relative path from the configured directory (empty for root)
    """
    if service is None:
        return "Error: Server not configured with a directory"

    target_path = service.root_directory / path
    if not target_path.is_dir():
        return f"Error: {target_path} is not a directory or does not exist"

    items = []
    try:
        for item in target_path.iterdir():
            if item.is_dir():
                items.append(f"{item.name}/")
            else:
                items.append(item.name)
    except PermissionError:
        return f"Error: Permission denied accessing {target_path}"

    return json.dumps(sorted(items), indent=2)


@mcp.tool()
async def get_overview() -> str:
    """
    Get a brief overview of files in the directory.
    Uses cached results if available, otherwise generates new overview.
    """
    if service is None:
        return "Error: Server not configured with a directory"

    overview_path = service.root_directory / OVERVIEW_FILENAME

    # Try to load existing overview
    try:
        with open(overview_path, "r") as f:
            overview_data = json.load(f)
        return json.dumps(overview_data, indent=2)
    except Exception as e:
        print(f"Could not load existing overview: {e}")
        # Remove corrupted file
        try:
            overview_path.unlink()
        except:
            pass

    # Generate new overview
    all_files = list(service.directory_tree_full())
    random.shuffle(all_files)
    selected_files = all_files[:OVERVIEW_MAX_FILES]

    result = await service.map_query_files("give overview. Use dense langauge so that fewest words carry most meaning.", selected_files)

    # Save overview
    try:
        with open(overview_path, "w") as f:
            json.dump(result, f, indent=4)
    except Exception as e:
        print(f"Error saving overview: {e}")

    return json.dumps(result, indent=2)


def main():
    """Main function to run the MCP server."""
    import sys
    import os

    # Get directory from environment or command line
    directory = os.getenv("FILE_QUERY_DIRECTORY")
    if not directory and len(sys.argv) > 1:
        directory = sys.argv[1]

    if not directory:
        print(
            "Error: Please specify directory via FILE_QUERY_DIRECTORY environment variable or command line argument"
        )
        sys.exit(1)

    # Initialize the service
    global service
    try:
        service = FileQueryService(directory)
        print(f"Initialized file query service for directory: {service.root_directory}")
    except Exception as e:
        print(f"Error initializing service: {e}")
        sys.exit(1)

    # Run the server
    mcp.run()


if __name__ == "__main__":
    main()
