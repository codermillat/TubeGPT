"""
Main API router for YouTube SEO Assistant.

Cursor Rules:
- Use dependency injection for all external dependencies
- Implement proper async/await patterns
- Add comprehensive error handling with structured logging
- Follow FastAPI best practices
"""

import asyncio
import time
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.exceptions import (
    TubeGPTException,
    get_http_status_code,
    YouTubeAPIException,
    AIServiceException,
    StorageException
)
from app.core.logging import request_logger, app_logger
from app.core.dependencies import (
    get_ai_service,
    get_youtube_client,
    get_memory_service,
    get_request_id,
    get_client_ip,
    get_user_agent,
    get_performance_context,
    validate_video_id,
    validate_channel_id,
    health_check_youtube,
    health_check_gemini
)
from app.services.ai_service import AIService
from app.services.memory_service import MemoryService
from app.clients.youtube_client import YouTubeClient

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered YouTube SEO optimization assistant",
    debug=settings.DEBUG
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class QuestionRequest(BaseModel):
    """Request model for asking questions."""
    question: str = Field(..., min_length=1, max_length=1000, description="User question")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional context data")

class StrategyResponse(BaseModel):
    """Response model for strategy operations."""
    id: str = Field(..., description="Strategy ID")
    filename: str = Field(..., description="Strategy filename")
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")

class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Overall health status")
    services: Dict[str, Any] = Field(..., description="Individual service health")
    timestamp: float = Field(..., description="Health check timestamp")

# Exception handlers
@app.exception_handler(TubeGPTException)
async def tube_gpt_exception_handler(request: Request, exc: TubeGPTException):
    """Handle custom TubeGPT exceptions with correlation tracking."""
    status_code = get_http_status_code(exc)
    correlation_id = request.headers.get("X-Request-ID", f"app-{int(time.time() * 1000)}")
    
    # Structured logging for application exceptions
    app_logger.warning(
        "Application exception occurred",
        extra={
            "exception_type": type(exc).__name__,
            "error_code": exc.error_code,
            "correlation_id": correlation_id,
            "context": exc.context,
            "request_path": request.url.path,
            "status_code": status_code
        }
    )
    
    request_logger.log_response(
        status_code=status_code,
        duration_ms=0,  # TODO: Add proper timing
        correlation_id=correlation_id,
        error=str(exc)
    )
    
    # Add correlation ID to response
    response_data = exc.to_dict()
    response_data["correlation_id"] = correlation_id
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    request_logger.log_response(
        status_code=exc.status_code,
        duration_ms=0,  # TODO: Add proper timing
        correlation_id=request.headers.get("X-Request-ID"),
        error=str(exc.detail)
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTPException", "message": str(exc.detail)}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with structured logging."""
    correlation_id = request.headers.get("X-Request-ID", f"err-{int(time.time() * 1000)}")
    
    # Structured error logging with context
    app_logger.error(
        "Unhandled exception occurred",
        extra={
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "correlation_id": correlation_id,
            "request_method": request.method,
            "request_path": request.url.path,
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("User-Agent", "unknown")
        },
        exc_info=True
    )
    
    request_logger.log_response(
        status_code=500,
        duration_ms=0,  # TODO: Add proper timing
        correlation_id=correlation_id,
        error=str(exc)
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError", 
            "message": "Internal server error",
            "correlation_id": correlation_id
        }
    )

# Middleware
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log all requests and responses."""
    start_time = time.time()
    
    # Generate correlation ID
    correlation_id = request.headers.get("X-Request-ID", f"req-{int(time.time() * 1000)}")
    
    # Log request
    request_logger.log_request(
        method=request.method,
        path=request.url.path,
        correlation_id=correlation_id,
        client_ip=request.client.host,
        user_agent=request.headers.get("User-Agent", "Unknown")
    )
    
    # Process request
    response = await call_next(request)
    
    # Log response
    duration_ms = (time.time() - start_time) * 1000
    request_logger.log_response(
        status_code=response.status_code,
        duration_ms=duration_ms,
        correlation_id=correlation_id
    )
    
    # Add correlation ID to response headers
    response.headers["X-Request-ID"] = correlation_id
    
    return response

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check(
    youtube_healthy: bool = Depends(health_check_youtube),
    gemini_healthy: bool = Depends(health_check_gemini)
):
    """
    Health check endpoint.
    
    Returns:
        Health status of all services
    """
    services = {
        "youtube_api": youtube_healthy,
        "gemini_ai": gemini_healthy,
        "memory_service": True,  # TODO: Add memory service health check
        "cache_service": True    # TODO: Add cache service health check
    }
    
    overall_healthy = all(services.values())
    
    return HealthResponse(
        status="healthy" if overall_healthy else "degraded",
        services=services,
        timestamp=time.time()
    )

# Chat endpoint
@app.post("/ask")
async def ask_question(
    request: QuestionRequest,
    ai_service: AIService = Depends(get_ai_service),
    memory_service: MemoryService = Depends(get_memory_service),
    request_id: str = Depends(get_request_id),
    client_ip: str = Depends(get_client_ip)
):
    """
    Process user question with AI.
    
    Args:
        request: Question request
        ai_service: AI service instance
        memory_service: Memory service instance
        request_id: Request correlation ID
        client_ip: Client IP address
    
    Returns:
        AI response
    """
    async with get_performance_context("ask_question") as perf:
        try:
            # Process question with AI
            ai_response = await ai_service.process_question(
                question=request.question,
                context_data=request.context
            )
            
            # Save to memory
            strategy_data = {
                "question": request.question,
                "response": ai_response["response"],
                "context": request.context,
                "request_id": request_id,
                "client_ip": client_ip,
                "timestamp": ai_response["timestamp"]
            }
            
            filename = await memory_service.save_strategy(strategy_data)
            
            return {
                "response": ai_response["response"],
                "success": True,
                "strategy_id": filename,
                "timestamp": ai_response["timestamp"],
                "request_id": request_id
            }
            
        except Exception as e:
            app_logger.error(f"Error in ask_question: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process question: {str(e)}"
            )

# Strategy management endpoints
@app.get("/strategies")
async def list_strategies(
    limit: Optional[int] = 10,
    offset: int = 0,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """
    List all stored strategies.
    
    Args:
        limit: Maximum number of strategies to return
        offset: Offset for pagination
        memory_service: Memory service instance
    
    Returns:
        List of strategies
    """
    try:
        strategies = await memory_service.list_strategies(limit=limit, offset=offset)
        return {
            "strategies": strategies,
            "count": len(strategies),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        app_logger.error(f"Error listing strategies: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list strategies: {str(e)}"
        )

@app.get("/strategies/{strategy_id}")
async def get_strategy(
    strategy_id: str,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """
    Get specific strategy by ID.
    
    Args:
        strategy_id: Strategy ID
        memory_service: Memory service instance
    
    Returns:
        Strategy data
    """
    try:
        # Add .json extension if not present
        filename = strategy_id if strategy_id.endswith('.json') else f"{strategy_id}.json"
        
        strategy = await memory_service.load_strategy(filename)
        return strategy
        
    except StorageException as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail="Strategy not found")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        app_logger.error(f"Error getting strategy: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get strategy: {str(e)}"
        )

@app.delete("/strategies/{strategy_id}")
async def delete_strategy(
    strategy_id: str,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """
    Delete strategy by ID.
    
    Args:
        strategy_id: Strategy ID
        memory_service: Memory service instance
    
    Returns:
        Deletion result
    """
    try:
        # Add .json extension if not present
        filename = strategy_id if strategy_id.endswith('.json') else f"{strategy_id}.json"
        
        success = await memory_service.delete_strategy(filename)
        
        if not success:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        return {"success": True, "message": "Strategy deleted successfully"}
        
    except Exception as e:
        app_logger.error(f"Error deleting strategy: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete strategy: {str(e)}"
        )

@app.get("/strategies/search")
async def search_strategies(
    q: str,
    limit: int = 10,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """
    Search strategies by content.
    
    Args:
        q: Search query
        limit: Maximum number of results
        memory_service: Memory service instance
    
    Returns:
        Search results
    """
    try:
        results = await memory_service.search_strategies(q, max_results=limit)
        return {
            "query": q,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        app_logger.error(f"Error searching strategies: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search strategies: {str(e)}"
        )

# YouTube API endpoints
@app.get("/youtube/overview")
async def get_youtube_overview(
    youtube_client: YouTubeClient = Depends(get_youtube_client),
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Get YouTube channel overview with AI insights.
    
    Args:
        youtube_client: YouTube client instance
        ai_service: AI service instance
    
    Returns:
        Channel overview with AI insights
    """
    async with get_performance_context("youtube_overview") as perf:
        try:
            # Get channel stats
            channel_stats = await youtube_client.get_channel_stats()
            
            # Get latest videos
            latest_videos = await youtube_client.get_latest_videos(max_results=5)
            
            # Generate AI insights
            channel_data = {
                "stats": channel_stats,
                "latest_videos": latest_videos
            }
            
            suggestions = await ai_service.generate_content_suggestions(
                channel_data, count=3
            )
            
            return {
                "channel_stats": channel_stats,
                "latest_videos": latest_videos,
                "ai_suggestions": suggestions,
                "timestamp": time.time()
            }
            
        except YouTubeAPIException as e:
            raise HTTPException(status_code=503, detail=str(e))
        except Exception as e:
            app_logger.error(f"Error getting YouTube overview: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get YouTube overview: {str(e)}"
            )

@app.get("/youtube/video/{video_id}/analyze")
async def analyze_video(
    video_id: str = Depends(validate_video_id),
    youtube_client: YouTubeClient = Depends(get_youtube_client),
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Analyze specific video with AI insights.
    
    Args:
        video_id: YouTube video ID
        youtube_client: YouTube client instance
        ai_service: AI service instance
    
    Returns:
        Video analysis with AI insights
    """
    async with get_performance_context("analyze_video") as perf:
        try:
            # Get video data
            video_data = await youtube_client.get_video_by_id(video_id)
            
            # Get video comments
            comments = await youtube_client.get_video_comments(video_id, max_results=10)
            
            # Analyze with AI
            analysis = await ai_service.analyze_video(video_data, analysis_type="seo")
            
            return {
                "video_data": video_data,
                "comments": comments,
                "ai_analysis": analysis,
                "timestamp": time.time()
            }
            
        except YouTubeAPIException as e:
            raise HTTPException(status_code=503, detail=str(e))
        except Exception as e:
            app_logger.error(f"Error analyzing video: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to analyze video: {str(e)}"
            )

@app.get("/youtube/search")
async def search_youtube_videos(
    q: str,
    max_results: int = 10,
    order: str = "relevance",
    youtube_client: YouTubeClient = Depends(get_youtube_client)
):
    """
    Search YouTube videos.
    
    Args:
        q: Search query
        max_results: Maximum number of results
        order: Sort order
        youtube_client: YouTube client instance
    
    Returns:
        Search results
    """
    try:
        results = await youtube_client.search_videos(
            query=q,
            max_results=max_results,
            order=order
        )
        
        return {
            "query": q,
            "results": results,
            "count": len(results),
            "order": order
        }
        
    except YouTubeAPIException as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        app_logger.error(f"Error searching YouTube videos: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search YouTube videos: {str(e)}"
        )

# Timeline endpoint
@app.get("/timeline")
async def get_timeline(
    days: int = 7,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """
    Get timeline of activities.
    
    Args:
        days: Number of days to look back
        memory_service: Memory service instance
    
    Returns:
        Timeline data
    """
    try:
        # Get recent strategies
        strategies = await memory_service.list_strategies(limit=50)
        
        # Filter by date range
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        
        filtered_strategies = []
        for strategy in strategies:
            if strategy.get("created_at"):
                created_at = datetime.fromisoformat(strategy["created_at"])
                if created_at > cutoff_date:
                    filtered_strategies.append(strategy)
        
        return {
            "timeline": filtered_strategies,
            "days": days,
            "total_items": len(filtered_strategies)
        }
        
    except Exception as e:
        app_logger.error(f"Error getting timeline: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get timeline: {str(e)}"
        )

# Storage stats endpoint
@app.get("/stats")
async def get_storage_stats(
    memory_service: MemoryService = Depends(get_memory_service)
):
    """
    Get storage statistics.
    
    Args:
        memory_service: Memory service instance
    
    Returns:
        Storage statistics
    """
    try:
        stats = await memory_service.get_storage_stats()
        return stats
    except Exception as e:
        app_logger.error(f"Error getting storage stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get storage stats: {str(e)}"
        )

# Playground endpoint for local browser demo
@app.post("/playground/analyze")
async def playground_analyze(
    request: Request,
    ai_service: AIService = Depends(get_ai_service),
    request_id: str = Depends(get_request_id)
) -> Dict[str, Any]:
    """
    Playground endpoint for running full AI strategy analysis.
    
    Upload CSV, set parameters, and get complete analysis results.
    Designed for local browser interface testing.
    """
    
    bound_logger = request_logger.bind(
        request_id=request_id,
        endpoint="/playground/analyze"
    )
    
    try:
        # Get form data
        form = await request.form()
        
        # Validate required fields
        if "csv_file" not in form:
            raise HTTPException(status_code=400, detail="CSV file is required")
        
        csv_file = form["csv_file"]
        goal = form.get("goal", "Generate optimized YouTube content strategy")
        audience = form.get("audience", None)
        tone = form.get("tone", "engaging")
        
        bound_logger.info("Processing playground analysis request")
        
        # Save uploaded file temporarily
        from tempfile import NamedTemporaryFile
        import os
        
        with NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
            content = await csv_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Import and run the strategy runner
            from app.services.ai_strategy_runner import AIStrategyRunner
            
            runner = AIStrategyRunner(
                correlation_id=request_id,
                verbose=True
            )
            
            # Run analysis
            result = await runner.run_full_analysis(
                csv_file=temp_file_path,
                goal=goal,
                audience=audience,
                tone=tone
            )
            
            bound_logger.info("Playground analysis completed successfully")
            
            return {
                "success": True,
                "data": result,
                "playground": True,
                "download_enabled": True
            }
            
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass
                
    except HTTPException:
        raise
    except Exception as e:
        bound_logger.error(f"Playground analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@app.get("/playground")
async def playground_interface():
    """
    Simple HTML interface for local browser testing.
    
    Provides a basic form to upload CSV and run analysis.
    """
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🎯 TubeGPT Playground</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .header { text-align: center; margin-bottom: 30px; }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, textarea, select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
            button { background: #007bff; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #0056b3; }
            .results { margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 4px; }
            .loading { display: none; text-align: center; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎯 TubeGPT Playground</h1>
            <p>Local-First AI YouTube SEO Assistant</p>
            <p><small>✅ No Login • ✅ No Cloud • ✅ No Tracking</small></p>
        </div>
        
        <form id="analysisForm" enctype="multipart/form-data">
            <div class="form-group">
                <label for="csv_file">YouTube CSV Data File:</label>
                <input type="file" id="csv_file" name="csv_file" accept=".csv" required>
                <small>Upload your YouTube analytics CSV file</small>
            </div>
            
            <div class="form-group">
                <label for="goal">Analysis Goal:</label>
                <textarea id="goal" name="goal" rows="3" placeholder="E.g., Find gaps and generate 5 high-CTR titles for a female GenZ audience in Bangladesh">Generate optimized YouTube content strategy</textarea>
            </div>
            
            <div class="form-group">
                <label for="audience">Target Audience:</label>
                <input type="text" id="audience" name="audience" placeholder="E.g., female GenZ in Bangladesh, tech enthusiasts">
            </div>
            
            <div class="form-group">
                <label for="tone">Content Tone:</label>
                <select id="tone" name="tone">
                    <option value="engaging">Engaging</option>
                    <option value="curiosity">Curiosity</option>
                    <option value="authority">Authority</option>
                    <option value="persuasive">Persuasive</option>
                    <option value="fear">Fear/Urgency</option>
                </select>
            </div>
            
            <button type="submit">🚀 Run Analysis</button>
        </form>
        
        <div class="loading" id="loading">
            <p>🔄 Running AI analysis... This may take a few moments.</p>
        </div>
        
        <div class="results" id="results" style="display: none;">
            <h3>📊 Analysis Results</h3>
            <div id="resultsContent"></div>
            <button onclick="downloadResults()" id="downloadBtn" style="margin-top: 10px;">💾 Download JSON</button>
        </div>
        
        <script>
            let analysisResults = null;
            
            document.getElementById('analysisForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const loading = document.getElementById('loading');
                const results = document.getElementById('results');
                const formData = new FormData(this);
                
                loading.style.display = 'block';
                results.style.display = 'none';
                
                try {
                    const response = await fetch('/playground/analyze', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        analysisResults = data.data;
                        displayResults(data.data);
                        results.style.display = 'block';
                    } else {
                        alert('Analysis failed: ' + (data.detail || 'Unknown error'));
                    }
                } catch (error) {
                    alert('Request failed: ' + error.message);
                } finally {
                    loading.style.display = 'none';
                }
            });
            
            function displayResults(data) {
                const content = document.getElementById('resultsContent');
                const analysis = data.analysis_result;
                
                let html = '<h4>🎯 Strategy Summary</h4>';
                html += '<p>' + (analysis.insights || 'Analysis completed successfully') + '</p>';
                
                if (analysis.optimized_content) {
                    const content = analysis.optimized_content;
                    
                    if (content.titles && content.titles.length > 0) {
                        html += '<h4>📝 Optimized Titles</h4><ul>';
                        content.titles.forEach(title => {
                            html += '<li>' + title + '</li>';
                        });
                        html += '</ul>';
                    }
                    
                    if (content.tags && content.tags.length > 0) {
                        html += '<h4>🏷️ SEO Tags</h4>';
                        html += '<p>' + content.tags.join(', ') + '</p>';
                    }
                }
                
                if (analysis.keywords && analysis.keywords.keywords) {
                    html += '<h4>🔍 Keywords Found</h4>';
                    html += '<p>' + analysis.keywords.keywords.slice(0, 10).join(', ') + '</p>';
                }
                
                content.innerHTML = html;
            }
            
            function downloadResults() {
                if (analysisResults) {
                    const blob = new Blob([JSON.stringify(analysisResults, null, 2)], {
                        type: 'application/json'
                    });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'tubegpt-analysis-' + new Date().toISOString().split('T')[0] + '.json';
                    a.click();
                    URL.revokeObjectURL(url);
                }
            }
        </script>
    </body>
    </html>
    """
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "endpoints": {
            "health": "/health",
            "ask": "/ask",
            "strategies": "/strategies",
            "youtube": "/youtube/overview",
            "timeline": "/timeline",
            "stats": "/stats",
            "playground": "/playground"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    ) 