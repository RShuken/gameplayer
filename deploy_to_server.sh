#!/bin/bash
# Deploy and setup the Qwen2-VL server on TensorDock

set -e

echo "=========================================="
echo "DEPLOYING TO TENSORDOCK SERVER"
echo "=========================================="
echo ""

# Server details
SERVER_IP="91.150.160.37"
SSH_PORT="43001"
SSH_KEY="tensordock_key"

echo "Server: $SERVER_IP:$SSH_PORT"
echo ""

# Test SSH connection
echo "[1/4] Testing SSH connection..."
ssh -i "$SSH_KEY" -p "$SSH_PORT" -o StrictHostKeyChecking=no user@"$SERVER_IP" "echo 'Connection successful!'"

# Copy setup script to server
echo "[2/4] Copying setup script to server..."
scp -i "$SSH_KEY" -P "$SSH_PORT" -o StrictHostKeyChecking=no setup_server.sh user@"$SERVER_IP":~/

# Make setup script executable and run it
echo "[3/4] Running setup script on server..."
echo "This will take 10-15 minutes (system updates + model download)"
echo ""
ssh -i "$SSH_KEY" -p "$SSH_PORT" -o StrictHostKeyChecking=no user@"$SERVER_IP" "chmod +x ~/setup_server.sh && bash ~/setup_server.sh"

# Start the server in the background
echo "[4/4] Starting model server..."
ssh -i "$SSH_KEY" -p "$SSH_PORT" -o StrictHostKeyChecking=no user@"$SERVER_IP" << 'ENDSSH'
cd ~/lumine-agent
source venv/bin/activate
nohup python server.py > server.log 2>&1 &
echo $! > server.pid
echo "Server started with PID: $(cat server.pid)"
ENDSSH

echo ""
echo "=========================================="
echo "DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "Server is starting up..."
echo "It will take 2-3 minutes to load the model on first run."
echo ""
echo "API Endpoint: http://$SERVER_IP:43002"
echo ""
echo "To check server logs:"
echo "  ssh -i $SSH_KEY -p $SSH_PORT user@$SERVER_IP 'tail -f ~/lumine-agent/server.log'"
echo ""
echo "To stop the server:"
echo "  ssh -i $SSH_KEY -p $SSH_PORT user@$SERVER_IP 'kill \$(cat ~/lumine-agent/server.pid)'"
echo ""
