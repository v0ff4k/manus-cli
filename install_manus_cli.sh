#!/bin/bash

# --- Configuration ---
INSTALL_DIR="$HOME/.manus-cli"
SCRIPT_NAME="manus.py"
BIN_PATH="/usr/local/bin/manus"

# --- Helper Functions ---

# Function to check for required commands
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo "Error: The required command '$1' is not installed. Please install it and try again."
        exit 1
    fi
}

# Function to check for and set the API key in the shell profile
set_api_key() {
    local rc_file
    # Check for Zsh first, then Bash
    if [ -f "$HOME/.zshrc" ]; then
        rc_file="$HOME/.zshrc"
    elif [ -f "$HOME/.bashrc" ]; then
        rc_file="$HOME/.bashrc"
    else
        echo "Warning: Could not find .bashrc or .zshrc. You will need to manually set the MANUS_API_KEY environment variable."
        return
    fi

    echo "Updating shell profile ($rc_file) to set MANUS_API_KEY..."

    # Check if the key is already set
    if grep -q "export MANUS_API_KEY=" "$rc_file"; then
        # Key exists, update it
        sed -i "/export MANUS_API_KEY=/c\export MANUS_API_KEY=\"$1\"" "$rc_file"
        echo "Existing MANUS_API_KEY updated."
    else
        # Key does not exist, append it
        echo -e "\n# Manus CLI API Key" >> "$rc_file"
        echo "export MANUS_API_KEY=\"$1\"" >> "$rc_file"
        echo "MANUS_API_KEY added to $rc_file."
    fi
}

# --- Main Installation ---

echo "--- Manus CLI Automated Installation ---"

# 1. Check for prerequisites
check_command "python3"
check_command "pip3"

# 2. Get API Key from user
read -r -p "Please enter your OpenAI or Manus API Key: " API_KEY

if [ -z "$API_KEY" ]; then
    echo "Error: API Key cannot be empty. Aborting installation."
    exit 1
fi

# 3. Check for manus.py
if [ ! -f "$SCRIPT_NAME" ]; then
    echo "Error: '$SCRIPT_NAME' not found. Please ensure the 'manus.py' file is in the same directory as this script."
    exit 1
fi

# 4. Create installation directory
echo "Creating installation directory: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

# 5. Copy the script
echo "Copying $SCRIPT_NAME to $INSTALL_DIR"
cp "$SCRIPT_NAME" "$INSTALL_DIR/$SCRIPT_NAME"

# 6. Install dependencies in a dedicated virtual environment
echo "Setting up dedicated virtual environment and installing Python dependencies..."
python3 -m venv "$INSTALL_DIR/venv"
source "$INSTALL_DIR/venv/bin/activate"
pip install openai python-dotenv
deactivate

# 7. Create the wrapper script for global execution
echo "Creating global wrapper script at $BIN_PATH"
echo "#!/bin/bash" | sudo tee "$BIN_PATH" > /dev/null
echo "source \"$INSTALL_DIR/venv/bin/activate\"" | sudo tee -a "$BIN_PATH" > /dev/null
echo "python3 \"$INSTALL_DIR/$SCRIPT_NAME\" \"\$@\"" | sudo tee -a "$BIN_PATH" > /dev/null
echo "deactivate" | sudo tee -a "$BIN_PATH" > /dev/null

# 8. Make the wrapper executable
echo "Making the wrapper script executable..."
sudo chmod +x "$BIN_PATH"

# 9. Set API Key
set_api_key "$API_KEY"

# 10. Final confirmation
echo ""
echo "--- Installation Complete! ---"
echo "The Manus CLI is now installed and available globally as 'manus'."
echo "Your API key has been saved to your shell profile."
echo ""
echo "To start using it, please run: source ~/.bashrc (or source ~/.zshrc) in your current terminal."
echo "Then, navigate to a project directory and run: manus --init"
echo "Finally, ask for assistance: manus \"Explain the main function in this file.\""
echo "-----------------------------"
