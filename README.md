# Map Query MCP Server

This is an example MCP server that allows you to query files in a specified directory using a language model.

## Usage

1.  Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

2.  Set the `GEMINI_API_KEY` environment variable to your Gemini API key.

3.  Run the server:

    ```bash
    python server.py <gemini_api_key> <root_directory>
    ```

    Replace `<gemini_api_key>` with your actual Gemini API key and `<root_directory>` with the path to the directory you want to query.

## Tools

The server provides the following tools:

*   `map_query`: Answers a query about individual files loaded from a specified directory.
*   `directory_tree`: Recursively lists all files in the root directory, with paths relative to root.

## Configuration

*   `MODEL_NAME`: Specifies the name of the Gemini model to use (default: "gemini-2.5-flash-preview-04-17").
*   `MAX_CONCURRENT_TASKS`: Specifies the maximum number of concurrent tasks (default: 50).