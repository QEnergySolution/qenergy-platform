#!/bin/bash

# QEnergy Platform - One-Click Installation Script
# Supports macOS and Linux (Ubuntu/Debian)

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    else
        echo "unknown"
    fi
}

# Function to install Homebrew (macOS)
install_homebrew() {
    if ! command_exists brew; then
        print_status "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        print_success "Homebrew installed successfully"
    else
        print_status "Homebrew already installed"
    fi
}

# Function to install dependencies on macOS
install_macos_deps() {
    print_status "Installing macOS dependencies..."
    
    # Install Homebrew if not exists
    install_homebrew
    
    # Install Node.js and pnpm
    if ! command_exists node; then
        print_status "Installing Node.js..."
        brew install node
    fi
    
    if ! command_exists pnpm; then
        print_status "Installing pnpm..."
        npm install -g pnpm
    fi
    
    # Install PostgreSQL
    if ! command_exists psql; then
        print_status "Installing PostgreSQL..."
        brew install postgresql@14
        brew services start postgresql@14
    fi
    
    # Install Miniforge (Conda)
    if ! command_exists conda; then
        print_status "Installing Miniforge..."
        brew install miniforge
        conda init zsh
        source ~/.zshrc
    fi
    
    print_success "macOS dependencies installed"
}

# Function to install dependencies on Linux
install_linux_deps() {
    print_status "Installing Linux dependencies..."
    
    # Update package list
    sudo apt update
    
    # Install Node.js
    if ! command_exists node; then
        print_status "Installing Node.js..."
        curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
        sudo apt-get install -y nodejs
    fi
    
    # Install pnpm
    if ! command_exists pnpm; then
        print_status "Installing pnpm..."
        npm install -g pnpm
    fi
    
    # Install PostgreSQL and additional tools
    if ! command_exists psql; then
        print_status "Installing PostgreSQL..."
        sudo apt-get install -y postgresql postgresql-contrib
        sudo systemctl start postgresql
        sudo systemctl enable postgresql
    fi

    # Install lsof (for service checking)
    if ! command_exists lsof; then
        print_status "Installing lsof..."
        sudo apt-get install -y lsof
    fi
    
    # Install Miniforge
    if ! command_exists conda; then
        print_status "Installing Miniforge..."
        wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
        bash Miniforge3-Linux-x86_64.sh -b -p $HOME/miniforge3
        rm Miniforge3-Linux-x86_64.sh
        echo 'export PATH="$HOME/miniforge3/bin:$PATH"' >> ~/.bashrc
        source ~/.bashrc
    fi
    
    print_success "Linux dependencies installed"
}

# Function to setup database
setup_database() {
    print_status "Setting up database..."
    
    # Create database and user
    if [[ "$(detect_os)" == "macos" ]]; then
        # macOS: Create user and database
        createuser -s qenergy_user 2>/dev/null || true
        createdb -O qenergy_user qenergy_platform 2>/dev/null || true
    else
        # Linux: Switch to postgres user and create
        sudo -u postgres psql -c "CREATE USER qenergy_user WITH SUPERUSER PASSWORD 'qenergy_password';" 2>/dev/null || true
        sudo -u postgres createdb -O qenergy_user qenergy_platform 2>/dev/null || true
    fi
    
    # Import schema
    if [[ -f "backend/setup-database.sql" ]]; then
        psql -h localhost -U qenergy_user -d qenergy_platform -f backend/setup-database.sql
        print_success "Database schema imported"
    else
        print_error "Database schema file not found"
        exit 1
    fi
}

# Function to setup backend
setup_backend() {
    print_status "Setting up backend..."
    
    cd backend
    
    # Create conda environment
    conda env create -f environment.yml || conda env update -f environment.yml
    
    # Activate environment and install dependencies
    conda activate qenergy-backend
    pip install -r requirements.txt
    
    # Copy environment file
    if [[ ! -f ".env" ]]; then
        cp env.example .env
        print_warning "Please update backend/.env with your database credentials"
    fi
    
    cd ..
    print_success "Backend setup completed"
}

# Function to setup frontend
setup_frontend() {
    print_status "Setting up frontend..."
    
    # Install dependencies
    pnpm install
    
    # Create environment file if not exists
    if [[ ! -f ".env.local" ]]; then
        cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8002/api
EOF
        print_success "Frontend environment file created"
    fi
    
    print_success "Frontend setup completed"
}

# Function to verify installation
verify_installation() {
    print_status "Verifying installation..."
    
    # Check Node.js
    if command_exists node; then
        print_success "Node.js: $(node --version)"
    else
        print_error "Node.js not found"
    fi
    
    # Check pnpm
    if command_exists pnpm; then
        print_success "pnpm: $(pnpm --version)"
    else
        print_error "pnpm not found"
    fi
    
    # Check PostgreSQL
    if command_exists psql; then
        print_success "PostgreSQL: $(psql --version)"
    else
        print_error "PostgreSQL not found"
    fi
    
    # Check Conda
    if command_exists conda; then
        print_success "Conda: $(conda --version)"
    else
        print_error "Conda not found"
    fi
    
    # Check database connection
    if psql -h localhost -U qenergy_user -d qenergy_platform -c "SELECT COUNT(*) FROM projects;" >/dev/null 2>&1; then
        print_success "Database connection: OK"
    else
        print_warning "Database connection: Please check credentials"
    fi

    # Check Azure OpenAI configuration
    if [[ -f "backend/.env" ]]; then
        if grep -q "AZURE_OPENAI_API_KEY" backend/.env && grep -q "AZURE_OPENAI_ENDPOINT" backend/.env; then
            print_success "Azure OpenAI configuration: Found"
        else
            print_warning "Azure OpenAI configuration: Please add AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT to backend/.env"
        fi
    else
        print_warning "Backend environment file not found: Please copy backend/env.example to backend/.env and configure"
    fi
}

# Main installation function
main() {
    echo "=========================================="
    echo "  QEnergy Platform - Installation Script"
    echo "=========================================="
    echo
    
    OS=$(detect_os)
    print_status "Detected OS: $OS"
    
    if [[ "$OS" == "unknown" ]]; then
        print_error "Unsupported operating system"
        exit 1
    fi
    
    # Install OS-specific dependencies
    if [[ "$OS" == "macos" ]]; then
        install_macos_deps
    else
        install_linux_deps
    fi
    
    # Setup database
    setup_database
    
    # Setup backend
    setup_backend
    
    # Setup frontend
    setup_frontend
    
    # Verify installation
    verify_installation
    
    echo
    echo "=========================================="
    print_success "Installation completed successfully!"
    echo "=========================================="
    echo
    echo "Next steps:"
    echo "1. Update backend/.env with your database credentials and Azure OpenAI keys"
    echo "2. Start the backend: cd backend && conda activate qenergy-backend && uvicorn app.main:app --reload --port 8002"
    echo "3. Start the frontend: pnpm dev"
    echo "4. Open http://localhost:3000 in your browser"
    echo
    echo "For more information, see README.md"
}

# Run main function
main "$@"
