# AI-Powered SEO YouTube Assistant

A comprehensive AI-powered assistant for YouTube channel analysis and SEO optimization. Built with FastAPI, Google Gemini AI, and YouTube Data API v3.

## 🚀 Features

- **AI-Powered Analysis**: Uses Google Gemini AI for intelligent video and channel analysis
- **YouTube Integration**: Full YouTube Data API v3 integration with OAuth authentication
- **SEO Optimization**: Comprehensive SEO recommendations and insights
- **Strategy Memory**: Local file-based storage for conversation history
- **Real-time Analytics**: Live channel statistics and performance metrics
- **Content Suggestions**: AI-generated content ideas based on channel performance
- **Multi-level Caching**: Memory, file, and Redis caching support
- **Comprehensive Logging**: Structured logging with correlation IDs
- **Rate Limiting**: Built-in rate limiting and quota management
- **Health Monitoring**: Health checks for all services

## 🏗️ Project Structure

```
TubeGPT/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── main.py          # FastAPI routes and endpoints
│   ├── core/
│   │   ├── config.py            # Centralized configuration
│   │   ├── exceptions.py        # Custom exception classes
│   │   ├── logging.py           # Structured logging setup
│   │   └── dependencies.py      # Dependency injection
│   ├── services/
│   │   ├── ai_service.py        # AI analysis service
│   │   ├── memory_service.py    # Strategy storage service
│   │   └── cache_service.py     # Multi-level caching
│   ├── clients/
│   │   ├── youtube_client.py    # YouTube API client
│   │   └── gemini_client.py     # Gemini AI client
│   ├── models/                  # Data models
│   ├── schemas/                 # Pydantic schemas
│   └── utils/
│       └── time_utils.py        # Time utilities
├── tests/
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── fixtures/                # Test fixtures
├── data/
│   ├── storage/                 # Local data storage
│   ├── templates/               # Prompt templates
│   └── fixtures/                # Test data
├── config/                      # Configuration files
├── docs/                        # Documentation
├── frontend/                    # Frontend assets
├── main.py                      # Application entry point
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## 🔧 Installation

### Prerequisites

- Python 3.9+
- Google Cloud Project with YouTube Data API v3 enabled
- Google Gemini AI API key

### Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd TubeGPT
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the project root:
   ```env
   # Application Settings
   DEBUG=true
   LOG_LEVEL=INFO
   HOST=127.0.0.1
   PORT=8000
   
   # YouTube API Configuration
   YOUTUBE_CREDENTIALS_FILE=config/credentials.json
   YOUTUBE_TOKEN_FILE=data/storage/token.json
   
   # Gemini AI Configuration
   GEMINI_API_KEY=your-gemini-api-key-here
   GEMINI_MODEL=gemini-pro
   
   # Storage Configuration
   STORAGE_PATH=data/storage
   STRATEGY_STORAGE_PATH=data/storage/strategies
   CACHE_PATH=data/storage/cache
   ```

5. **Set up Google APIs:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable YouTube Data API v3
   - Create OAuth 2.0 credentials
   - Download the credentials JSON file and save it as `config/credentials.json`

6. **Get Gemini API key:**
   - Go to [Google AI Studio](https://aistudio.google.com/)
   - Generate an API key
   - Add it to your `.env` file

## 🚀 Running the Application

### Development Mode

```bash
python main.py
```

The application will start on `http://localhost:8000` by default.

### Production Mode

```bash
uvicorn app.api.v1.main:app --host 0.0.0.0 --port 8000
```

### Using Docker (Optional)

```bash
docker build -t tubegpt .
docker run -p 8000:8000 --env-file .env tubegpt
```

## 📚 API Documentation

Once the application is running, you can access:

- **Interactive API Documentation**: `http://localhost:8000/docs`
- **Alternative API Documentation**: `http://localhost:8000/redoc`
- **Health Check**: `http://localhost:8000/health`

## 🔍 API Endpoints

### Core Endpoints

- `POST /ask` - Ask questions to the AI assistant
- `GET /health` - Health check for all services
- `GET /` - API information and available endpoints

### Strategy Management

- `GET /strategies` - List all stored strategies
- `GET /strategies/{strategy_id}` - Get specific strategy
- `DELETE /strategies/{strategy_id}` - Delete strategy
- `GET /strategies/search?q={query}` - Search strategies

### YouTube Integration

- `GET /youtube/overview` - Get channel overview with AI insights
- `GET /youtube/video/{video_id}/analyze` - Analyze specific video
- `GET /youtube/search?q={query}` - Search YouTube videos

### Analytics

- `GET /timeline?days={days}` - Get timeline of activities
- `GET /stats` - Get storage statistics

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/unit/test_ai_service.py

# Run integration tests
pytest tests/integration/
```

## 📊 Monitoring and Logging

The application includes comprehensive logging and monitoring:

- **Structured Logging**: All logs are structured with correlation IDs
- **Health Checks**: Built-in health checks for all services
- **Performance Tracking**: Request/response timing and performance metrics
- **Error Tracking**: Detailed error logging with context

## 🔒 Security Features

- **Rate Limiting**: Built-in rate limiting for API endpoints
- **Input Validation**: Comprehensive input validation using Pydantic
- **Error Handling**: Proper error handling without information leakage
- **CORS Configuration**: Configurable CORS settings
- **API Key Management**: Secure API key handling

## 📈 Performance Optimization

- **Multi-level Caching**: Memory, file, and Redis caching
- **Async Operations**: Full async/await support for I/O operations
- **Connection Pooling**: Efficient HTTP connection management
- **Batch Processing**: Batch operations for YouTube API calls

## 🛠️ Development

### Code Quality

The project follows strict coding standards:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **pytest**: Testing framework

### Pre-commit Hooks

Set up pre-commit hooks:

```bash
pre-commit install
```

### Development Guidelines

1. Follow the Cursor Rules defined in the project
2. Use dependency injection for all external dependencies
3. Implement proper async/await patterns
4. Add comprehensive error handling
5. Write tests for all new functionality
6. Use structured logging with context

## 🚀 Deployment

### Environment Variables

Ensure all required environment variables are set:

```env
# Production settings
DEBUG=false
LOG_LEVEL=INFO

# Database (if using)
DATABASE_URL=postgresql://user:pass@localhost/db

# Cache (if using Redis)
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secure-secret-key
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "app.api.v1.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📝 License

This project is licensed under the MIT License. See the LICENSE file for details.

## 🆘 Support

For support and questions:

1. Check the documentation
2. Review the API documentation at `/docs`
3. Check the health endpoint at `/health`
4. Review the logs for detailed error information

## 🔄 Changelog

See the CHANGELOG.md file for detailed version history and changes.

## 🏗️ Architecture

The application follows a clean architecture pattern:

- **API Layer**: FastAPI routes and endpoints
- **Service Layer**: Business logic and use cases
- **Client Layer**: External API integrations
- **Data Layer**: Storage and caching
- **Core Layer**: Configuration, logging, and utilities

This structure ensures maintainability, testability, and scalability. 