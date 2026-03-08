#!/bin/bash
################################################################################
# Code-Sarthi EC2 Deployment Script
# AWS AI for Bharat Hackathon - March 8, 2026
#
# This script automates the deployment of Code-Sarthi on Ubuntu EC2 instances
# with IAM role-based authentication (no hardcoded credentials)
################################################################################

set -e  # Exit on any error

echo "=================================="
echo "Code-Sarthi EC2 Deployment"
echo "=================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    print_error "Please do not run this script as root"
    exit 1
fi

# Step 1: Update system packages
print_status "Updating system packages..."
sudo apt-get update -y
sudo apt-get upgrade -y

# Step 2: Install Python 3 and pip
print_status "Installing Python 3 and pip..."
sudo apt-get install -y python3 python3-pip python3-venv

# Verify Python installation
PYTHON_VERSION=$(python3 --version)
print_status "Python installed: $PYTHON_VERSION"

# Step 3: Install system dependencies
print_status "Installing system dependencies..."
sudo apt-get install -y \
    git \
    tmux \
    curl \
    wget \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev

# Step 4: Install AWS CLI (if not already installed)
if ! command -v aws &> /dev/null; then
    print_status "Installing AWS CLI..."
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip -q awscliv2.zip
    sudo ./aws/install
    rm -rf aws awscliv2.zip
    print_status "AWS CLI installed successfully"
else
    print_status "AWS CLI already installed"
fi

# Step 5: Verify IAM role is attached to EC2 instance
print_status "Verifying IAM role authentication..."
if aws sts get-caller-identity &> /dev/null; then
    print_status "IAM role authentication successful"
    aws sts get-caller-identity
else
    print_error "IAM role not configured. Please attach an IAM role to this EC2 instance."
    print_warning "Required permissions: bedrock:InvokeModel, kendra:Query, s3:GetObject, s3:PutObject"
    exit 1
fi

# Step 6: Clone or update repository (if not already present)
if [ ! -d "code-sarthi" ]; then
    print_status "Cloning Code-Sarthi repository..."
    # Replace with your actual repository URL
    # git clone https://github.com/your-username/code-sarthi.git
    print_warning "Repository already present in current directory"
else
    print_status "Repository already exists"
fi

# Navigate to application directory
cd "$(dirname "$0")"
print_status "Working directory: $(pwd)"

# Step 7: Install Python dependencies
print_status "Installing Python dependencies..."
# Using --break-system-packages for Ubuntu 23.04+ where externally-managed-environment exists
pip3 install -r requirements.txt --break-system-packages --upgrade

# Verify critical packages
print_status "Verifying critical packages..."
python3 -c "import streamlit; print(f'Streamlit: {streamlit.__version__}')"
python3 -c "import boto3; print(f'Boto3: {boto3.__version__}')"
python3 -c "import tiktoken; print(f'Tiktoken: {tiktoken.__version__}')"
python3 -c "import tenacity; print(f'Tenacity: {tenacity.__version__}')"

# Step 8: Set environment variables
print_status "Setting environment variables..."
export USE_AWS=True
export AWS_REGION=${AWS_REGION:-us-east-1}
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Make environment variables persistent
cat > .env << EOF
USE_AWS=True
AWS_REGION=${AWS_REGION:-us-east-1}
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
EOF

print_status "Environment variables configured"

# Step 9: Configure Streamlit
print_status "Configuring Streamlit..."
mkdir -p ~/.streamlit

cat > ~/.streamlit/config.toml << EOF
[server]
port = 8501
address = "0.0.0.0"
headless = true
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
serverAddress = "0.0.0.0"
serverPort = 8501

[theme]
base = "dark"
primaryColor = "#FF8A00"
EOF

print_status "Streamlit configuration complete"

# Step 10: Create systemd service (optional - for production)
print_status "Creating systemd service..."
sudo tee /etc/systemd/system/code-sarthi.service > /dev/null << EOF
[Unit]
Description=Code-Sarthi Streamlit Application
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment="USE_AWS=True"
Environment="AWS_REGION=${AWS_REGION:-us-east-1}"
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/local/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
print_status "Systemd service created (not started yet)"

# Step 11: Check if tmux session already exists
print_status "Checking for existing tmux sessions..."
if tmux has-session -t code-sarthi 2>/dev/null; then
    print_warning "Tmux session 'code-sarthi' already exists"
    print_warning "To kill it: tmux kill-session -t code-sarthi"
    print_warning "To attach: tmux attach -t code-sarthi"
else
    # Step 12: Launch application in tmux
    print_status "Launching Code-Sarthi in tmux session..."
    tmux new-session -d -s code-sarthi "streamlit run app.py --server.port=8501 --server.address=0.0.0.0"
    sleep 3
    print_status "Application launched in tmux session 'code-sarthi'"
fi

# Step 13: Display deployment information
echo ""
echo "=================================="
echo "Deployment Complete!"
echo "=================================="
echo ""
print_status "Application is running on port 8501"
print_status "Tmux session: code-sarthi"
echo ""
echo "Useful Commands:"
echo "  - View logs:        tmux attach -t code-sarthi"
echo "  - Detach from tmux: Ctrl+B, then D"
echo "  - Kill session:     tmux kill-session -t code-sarthi"
echo "  - Restart app:      ./deploy.sh"
echo ""
echo "Systemd Service (Alternative):"
echo "  - Start:   sudo systemctl start code-sarthi"
echo "  - Stop:    sudo systemctl stop code-sarthi"
echo "  - Status:  sudo systemctl status code-sarthi"
echo "  - Enable:  sudo systemctl enable code-sarthi"
echo ""
echo "Access Application:"
echo "  - Local:   http://localhost:8501"
echo "  - Public:  http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8501"
echo ""
print_warning "Ensure Security Group allows inbound traffic on port 8501"
echo ""
echo "=================================="
