# Manus CLI: Context-Aware Developer Assistant

Simple: Claude code like, cli assistant made for Manus users.

The **Manus CLI** is a Python-based command-line interface designed to bring the power of a context-aware AI assistant, similar to tools like Cursor or Claude Code, directly into your Linux development workflow. It uses the OpenAI-compatible API to interact with large language models, feeding them your project's code context (while respecting ignore rules) to provide highly relevant code generation, debugging, and architectural advice.

## Features

*   **Context-Aware:** Automatically gathers the content of your project files and includes them in the prompt, excluding files specified in a `.manusignore` file.
*   **Configurable:** Customize the AI model, system prompt (the "role" of the assistant), and ignore rules via a simple `manus.json` configuration file.
*   **Easy Setup:** Simple installation and a built-in initialization command to get started quickly.
*   **Streaming Output:** Provides real-time output from the AI model for a responsive experience.

## Installation

The Manus CLI is a single Python script with minimal dependencies.

### Prerequisites

*   Python 3.8+
*   `pip` (Python package installer)

### Steps

1.  **Clone the repository (or create the directory):**
    \`\`\`bash
    git clone https://github.com/your-username/manus-cli.git # If hosted on GitHub
    # OR
    mkdir manus-cli
    cd manus-cli
    \`\`\`

2.  **Set up a virtual environment and install dependencies:**
    \`\`\`bash
    python3 -m venv venv
    source venv/bin/activate
    pip install openai python-dotenv
    \`\`\`

3.  **Make the script executable and add it to your PATH:**
    (Assuming the main script is named `manus.py` and you are in the `manus-cli` directory)
    \`\`\`bash
    chmod +x manus.py
    # For global access (requires sudo)
    sudo ln -s "$(pwd)/manus.py" /usr/local/bin/manus
    \`\`\`
    You can now run the assistant from any directory using the `manus` command.

## Configuration

The CLI uses two files for configuration:

1.  **Environment Variable:** Your API key must be set as an environment variable.
    *   **`MANUS_API_KEY`** (Preferred) or **`OPENAI_API_KEY`**

2.  **`manus.json`:** Defines the model and the assistant's behavior.
3.  **`.manusignore`:** Defines files and directories to exclude from the project context.

### Initialization

Navigate to the root of your project and run the initialization command:

\`\`\`bash
manus --init
\`\`\`

This will create a sample `manus.json` and `.manusignore` file in your current directory.

### `manus.json` Example

\`\`\`json
{
    "model": "gpt-4.1-mini",
    "system_prompt": "You are a senior TypeScript engineer specializing in React and Next.js. Your responses must be concise, professional, and only contain code blocks when writing code.",
    "ignore_files": [
        "dist/",
        "build/",
        "coverage/"
    ]
}
\`\`\`

### `.manusignore` Example

\`\`\`
# Ignore all log files
*.log

# Ignore the temporary directory
/tmp/

# Ignore a specific file
src/legacy_code.js
\`\`\`

## Usage

The primary usage is to pass your request as an argument to the `manus` command.

### Basic Command

\`\`\`bash
manus "Explain how the authentication flow works in this project."
\`\`\`

### Code Generation

The system prompt is configured to encourage the model to output only code when requested.

\`\`\`bash
manus "Write a new React component called 'UserProfile' that displays the user's name and email from the props."
\`\`\`

### Overriding the Model

You can temporarily override the model specified in `manus.json` using the `-m` flag.

\`\`\`bash
manus -m gpt-4.1-nano "Refactor the 'utils.py' file for better performance."
\`\`\`

## Core Logic Overview

The CLI performs the following steps for every command:

1.  **API Key Check:** Ensures `MANUS_API_KEY` or `OPENAI_API_KEY` is set.
2.  **Configuration Load:** Loads `manus.json` and `.manusignore` from the current directory, merging them with default settings.
3.  **Context Gathering:** Recursively scans the current directory, reading the content of all non-ignored files. Each file's content is prepended with its path.
4.  **Prompt Construction:** Combines the `system_prompt` (your custom role), the gathered project context, and your user prompt into a single, powerful request for the AI.
5.  **API Call:** Calls the OpenAI-compatible API and streams the response directly to your terminal.

This setup ensures that the AI assistant is always aware of your project's structure and existing code, making its suggestions highly relevant and accurate.
