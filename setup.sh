echo "🚀 Kerala Cleanup Platform - Setup Script"
echo "=========================================="
echo ""

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.11+ required. Found: $python_version"
    exit 1
fi
echo "✅ Python $python_version detected"
echo ""

# Check if Docker is installed
echo "📋 Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi
echo "✅ Docker detected"
echo ""

# Check if Docker Compose is installed
echo "📋 Checking Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo "⚠️  Docker Compose not found as standalone command"
    echo "   Checking for docker compose plugin..."
    if ! docker compose version &> /dev/null; then
        echo "❌ Docker Compose not found. Please install Docker Compose."
        exit 1
    fi
    echo "✅ Docker Compose plugin detected"
else
    echo "✅ Docker Compose detected"
fi
echo ""

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✅ pip upgraded"
echo ""

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt > /dev/null 2>&1
echo "✅ Dependencies installed"
echo ""

# Create .env file if it doesn't exist
echo "⚙️  Setting up environment variables..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    
    # Generate a secure JWT secret
    jwt_secret=$(openssl rand -hex 32)
    
    # Update .env with generated secret (macOS and Linux compatible)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/your-super-secret-key-change-this-in-production/$jwt_secret/" .env
    else
        # Linux
        sed -i "s/your-super-secret-key-change-this-in-production/$jwt_secret/" .env
    fi
    
    echo "✅ .env file created with secure JWT secret"
else
    echo "✅ .env file already exists"
fi
echo ""

# Create necessary directories
echo "📁 Creating project directories..."
mkdir -p app/core app/models app/repositories app/routers app/services scripts tests
echo "✅ Directories created"
echo ""

# Start Docker containers
echo "🐳 Starting Docker containers..."
docker-compose up -d
echo "✅ Docker containers started"
echo ""

# Wait for MongoDB to be ready
echo "⏳ Waiting for MongoDB to be ready..."
sleep 5

# Check if MongoDB is accessible
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker-compose exec -T mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
        echo "✅ MongoDB is ready"
        break
    fi
    attempt=$((attempt + 1))
    if [ $attempt -eq $max_attempts ]; then
        echo "❌ MongoDB failed to start"
        exit 1
    fi
    sleep 1
done
echo ""

# Load sample data
echo "📊 Loading sample data..."
if [ -f "sample_data.py" ]; then
    python sample_data.py
    echo "✅ Sample data loaded"
else
    echo "⚠️  Sample data script not found, skipping..."
fi
echo ""

# Run tests
echo "🧪 Running tests..."
pytest tests/ -v --tb=short
if [ $? -eq 0 ]; then
    echo "✅ All tests passed"
else
    echo "⚠️  Some tests failed, but setup is complete"
fi
echo ""

# Display success message
echo "=========================================="
echo "🎉 Setup completed successfully!"
echo "=========================================="
echo ""
echo "📝 Next steps:"
echo ""
echo "1. Start the API server:"
echo "   uvicorn app.main:app --reload"
echo ""
echo "2. Access the API documentation:"
echo "   http://localhost:8000/docs"
echo ""
echo "3. Test credentials:"
echo "   Volunteer: arjun@example.com / Password123"
echo "   Organizer: priya@example.com / Password123"
echo "   Admin: admin@example.com / Admin123"
echo ""
echo "4. View logs:"
echo "   docker-compose logs -f"
echo ""
echo "5. Stop services:"
echo "   docker-compose down"
echo ""
echo "🔒 Security reminder:"
echo "   - Change JWT_SECRET_KEY before deploying to production"
echo "   - Use strong passwords for all accounts"
echo "   - Enable HTTPS in production"
echo ""
echo "Happy coding! 🚀"