# Map Query MCP Server

A Model Context Protocol (MCP) server that enables querying files in a directory using Google's Gemini AI models. This server provides powerful tools for analyzing, searching, and understanding file contents through natural language queries.

## Features

- **Concurrent File Processing**: Query multiple files simultaneously with configurable concurrency limits
- **Regex Pattern Matching**: Filter files using regular expressions for targeted analysis
- **Sampling Support**: Process random samples of large file sets to manage performance
- **Directory Overview**: Generate intelligent summaries of directory contents
- **File Resources**: Direct access to individual files through MCP resources
- **Caching**: Automatic caching of directory overviews for improved performance

## Installation

### Using uv (Recommended)

```bash
uvx mq-mcp /path/to/directory
```

### Manual Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd mq-mcp
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Set up your Gemini API key:
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```

4. Run the server:
   ```bash
   uv run mq-mcp /path/to/directory
   ```

## Usage

### Command Line

```bash
# Using uvx (installs and runs)
uvx mq-mcp /path/to/directory

# Using environment variable
export FILE_QUERY_DIRECTORY="/path/to/directory"
uv run mq-mcp

# Direct command line argument
uv run mq-mcp /path/to/directory
```

### MCP Client Configuration

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "map-query": {
      "command": "uvx",
      "args": ["mq-mcp", "/path/to/your/directory"]
    }
  }
}
```

## Tools

### Core Query Tools

- **`map_query_tool`**: Query specific files by filename
  - Args: `query` (string), `filenames` (array of strings)
  - Processes multiple files concurrently with the same query

- **`map_query_tool_regex`**: Query files matching a regex pattern
  - Args: `query` (string), `filename_regex` (string)
  - Useful for filtering by file extensions or naming patterns

- **`map_query_tool_regex_sampled`**: Query a random sample of matching files
  - Args: `query` (string), `filename_regex` (string), `sample_size` (integer)
  - Ideal for large directories where full processing would be too slow

### Directory Navigation Tools

- **`directory_tree`**: List all files recursively (up to 100 files)
  - Returns: JSON with file list and truncation status
  - Provides overview of directory structure

- **`ls`**: List contents of a specific directory
  - Args: `path` (string, optional - defaults to root)
  - Useful for iterative exploration of large directories

- **`get_overview`**: Generate or retrieve cached directory overview
  - Analyzes up to 100 random files to provide content summary
  - Results are cached for performance

## Resources

- **`file://{path}`**: Read individual files as resources
  - Direct access to file contents for detailed examination
  - Supports UTF-8 text files with error handling

- **`overview://directory`**: Access directory overview as a resource
  - Provides the same data as `get_overview` tool in resource format

## Prompts

- **`file_analysis_prompt`**: Systematic analysis template
  - Args: `focus` (string, optional)
  - Provides structured approach for comprehensive file analysis

## Configuration

### Environment Variables

- `GEMINI_API_KEY`: Your Google Gemini API key (required)
- `FILE_QUERY_DIRECTORY`: Default directory to analyze (optional)

### Constants (configurable in code)

- `MAX_CONCURRENT_TASKS`: Maximum concurrent file processing (default: 50)
- `MODEL_NAME`: Gemini model to use (default: "gemini-2.5-flash-preview-05-20")
- `MAX_FILES_FOR_DIR_TREE`: File limit for directory tree (default: 100)
- `OVERVIEW_MAX_FILES`: Files to sample for overview (default: 100)

## Systematic Analysis Methodology

The server is designed to support a systematic approach to file analysis:

1. **Initial Discovery**
   - Use `get_overview` to understand general content
   - Use `directory_tree` to see structure and organization
   - Note if directory is large (>100 files) as overview will be sampled

2. **Targeted Analysis**
   - Use `map_query_tool` with specific files for detailed information
   - Use `map_query_tool_regex` to filter by file patterns
   - Use `map_query_tool_regex_sampled` for sampling large sets
   - Run multiple queries from different angles

3. **Deep Investigation**
   - Access individual files via `file://` resources for detailed examination
   - Cross-reference information between files
   - Look for patterns, inconsistencies, or missing information

4. **Synthesis**
   - Combine findings from all sources
   - Provide comprehensive insights based on analysis

## Requirements

- Python ≥ 3.12
- Google Gemini API access
- Dependencies: `google-genai`, `mcp[cli]`, `httpx`, `tenacity`

## License

[Add your license information here]