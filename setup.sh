#!/bin/bash

echo "================================"
echo "Django RAG Chat Setup Script"
echo "================================"
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and add your API keys!"
fi

# Run migrations
echo ""
echo "Running database migrations..."
python manage.py makemigrations
python manage.py migrate

# Create superuser prompt
echo ""
read -p "Do you want to create a superuser? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    python manage.py createsuperuser
fi

echo ""
echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your API keys"
echo "2. Run: source venv/bin/activate"
echo "3. Run: python manage.py runserver"
echo "4. Visit: http://localhost:8000"
echo ""
