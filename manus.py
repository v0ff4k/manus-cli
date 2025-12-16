import os
import sys
import argparse
import json
from pathlib import Path
from fnmatch import fnmatch
from openai import OpenAI
from dotenv import load_dotenv

# --- Configuration and Setup ---

# Load environment variables from .env file in the current directory
load_dotenv()

# Default configuration
DEFAULT_CONFIG = {
    "model": "gpt-4.1-mini",
    "system_prompt": "You are a world-class full-stack developer assistant named Manus. Your goal is to help the user with their coding tasks. You are working on a project described by the following file contents. Analyze the context and provide concise, actionable code or advice. If you are asked to write code, only output the code block and nothing else.",
    "ignore_files": [
        ".git/",
        "node_modules/",
        "venv/",
        "__pycache__/",
        "*.log",
        "*.sqlite3",
        "*.env",
        ".manusignore",
        "manus.json",
        "manus.py"
    ]
}

def load_config(project_root: Path) -> dict:
    """Loads configuration from manus.json and .manusignore, merging with defaults."""
    """Loads configuration from manus.json, merging with defaults."""
    config = DEFAULT_CONFIG.copy()
    
    # 1. Load manus.json
    config_path = project_root / "manus.json"
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                project_config = json.load(f)
                config.update(project_config)
        except json.JSONDecodeError:
            print(f"Warning: Could not parse {config_path}. Using default configuration.", file=sys.stderr)

    # 2. Load .manusignore
    ignore_path = project_root / ".manusignore"
    ignore_patterns = []
    if ignore_path.exists():
        try:
            with open(ignore_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        ignore_patterns.append(line)
        except Exception as e:
            print(f"Warning: Could not read {ignore_path}: {e}", file=sys.stderr)

    # 3. Merge ignore lists
    # The final ignore list is: DEFAULT_CONFIG + manus.json's ignore_files + .manusignore
    final_ignore_list = DEFAULT_CONFIG["ignore_files"]
    if "ignore_files" in config and isinstance(config["ignore_files"], list):
        final_ignore_list.extend(config["ignore_files"])
    final_ignore_list.extend(ignore_patterns)
    
    config["ignore_files"] = list(set(final_ignore_list)) # Use set to remove duplicates
    
    return config

def get_api_key() -> str:
    """Retrieves the API key from environment variables."""
    api_key = os.getenv("MANUS_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: API key not found. Please set MANUS_API_KEY or OPENAI_API_KEY environment variable.", file=sys.stderr)
        sys.exit(1)
    return api_key

# --- Context Gathering ---

def is_ignored(path: Path, ignore_patterns: list, project_root: Path) -> bool:
    """Checks if a path should be ignored based on the patterns."""
    relative_path = path.relative_to(project_root).as_posix()
    for pattern in ignore_patterns:
        if pattern.endswith('/') and path.is_dir():
            pattern = pattern.rstrip('/')
        if fnmatch(relative_path, pattern) or fnmatch(relative_path, pattern + '/*'):
            return True
    return False

def gather_context(project_root: Path, ignore_patterns: list) -> str:
    """Recursively gathers content of non-ignored files."""
    context = []
    for path in project_root.rglob('*'):
        if path.is_file() and not is_ignored(path, ignore_patterns, project_root):
            try:
                # Simple check to skip binary files
                if path.suffix in ['.png', '.jpg', '.jpeg', '.bin', '.zip', '.tar', '.gz', '.ico']:
                    continue
                
                content = path.read_text(encoding='utf-8')
                
                # Skip files that are too large (e.g., large logs, minified JS)
                if len(content) > 100000:
                    continue

                relative_path = path.relative_to(project_root).as_posix()
                context.append(f"--- FILE: {relative_path} ---\n{content}\n--- END FILE: {relative_path} ---\n")
            except UnicodeDecodeError:
                # Skip non-text files that weren't caught by suffix check
                continue
            except Exception as e:
                print(f"Warning: Could not read file {path}: {e}", file=sys.stderr)

    return "\n".join(context)

# --- Main CLI Logic ---

def main():
    parser = argparse.ArgumentParser(
        description="Manus CLI: A context-aware full-stack developer assistant.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "prompt",
        nargs='?',
        help="The task or question for the assistant."
    )
    parser.add_argument(
        "-m", "--model",
        help="Override the model specified in manus.json (e.g., gpt-4.1-mini)."
    )
    parser.add_argument(
        "-i", "--init",
        action="store_true",
        help="Initialize the current directory with a sample manus.json and .manusignore."
    )
    
    args = parser.parse_args()
    
    project_root = Path.cwd()
    
    if args.init:
        init_project(project_root)
        return

    if not args.prompt:
        parser.print_help()
        sys.exit(1)

    # Check for API key early
    get_api_key()

    # 1. Load Configuration
    config = load_config(project_root)
    
    # Override model if provided via CLI
    model = args.model or config["model"]

    # 2. Gather Context
    context_string = gather_context(project_root, config["ignore_files"])
    
    # 3. Construct Messages
    system_message = config["system_prompt"] + "\n\n" + "PROJECT CONTEXT:\n" + context_string
    
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": args.prompt}
    ]

    # 4. Call API
    try:
        client = OpenAI(api_key=get_api_key())
        
        print(f"--- Manus ({model}) is thinking... ---", file=sys.stderr)
        
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
        )
        
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content is not None:
                print(content, end="", flush=True)
        
        print("\n--- End of Manus response ---", file=sys.stderr)

    except Exception as e:
        print(f"\nAn API error occurred: {e}", file=sys.stderr)
        sys.exit(1)

def init_project(project_root: Path):
    """Creates sample configuration files."""
    manus_json_path = project_root / "manus.json"
    manus_ignore_path = project_root / ".manusignore"
    
    if manus_json_path.exists() or manus_ignore_path.exists():
        print("Configuration files already exist. Aborting initialization.", file=sys.stderr)
        return

    sample_config = {
        "model": "gpt-4.1-mini",
        "system_prompt": "You are a React/Node.js expert. Focus on writing clean, modern TypeScript code. When asked to create a new file, wrap the content in a markdown code block with the filename as the title, e.g., ```filename.ts\\n...code...\\n```",
        "ignore_files": [
            "dist/",
            "build/",
            "coverage/"
        ]
    }
    
    try:
        with open(manus_json_path, 'w') as f:
            json.dump(sample_config, f, indent=4)
        print(f"Created sample configuration file: {manus_json_path}", file=sys.stderr)

        with open(manus_ignore_path, 'w') as f:
            f.write("# Add files or directories to ignore when gathering project context.\n")
            f.write("# Patterns are glob-style (e.g., *.log, /tmp/, src/test.js)\n")
            f.write("*.tmp\n")
            f.write("temp/\n")
        print(f"Created sample ignore file: {manus_ignore_path}", file=sys.stderr)
        
        print("\nInitialization complete. Edit manus.json and .manusignore to customize your assistant.", file=sys.stderr)

    except Exception as e:
        print(f"Error during initialization: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
