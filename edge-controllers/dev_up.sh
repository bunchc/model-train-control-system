#!/bin/bash
# Edge controller dev environment bring-up script
# Usage: ./dev_up.sh

# Activate the Python virtual environment
source ~/pi-env/bin/activate

# Start tmux session with two windows
SESSION="edge-dev"

# Kill any existing session with the same name
if tmux has-session -t $SESSION 2>/dev/null; then
    tmux kill-session -t $SESSION
fi

# Create new tmux session and start the app in window 1
# Window 1: Start the edge controller app
# Window 2: Shell for manual commands

tmux new-session -d -s $SESSION "cd $(dirname $0)/pi-template/app && python main.py"
tmux new-window -t $SESSION:2 -n shell "cd $(dirname $0)/pi-template/app; bash"

tmux select-window -t $SESSION:1

echo "Tmux session '$SESSION' started."
echo "Window 1: edge controller app running."
echo "Window 2: shell for manual commands."
echo "To attach: tmux attach -t $SESSION"
