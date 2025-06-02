from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Optional
import os
import io
from dotenv import load_dotenv
from pathlib import Path
import PyPDF2

# Load environment variables from the correct location
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    expose_headers=["Content-Disposition"],
    max_age=600,
)

# --- Add Manim Engine API Integration ---
try:
    from .manim_engine.api_integration import router as manim_router
    
    try:
        from .manim_engine.api_integration import load_tasks_from_file
        load_tasks_from_file()
        print("Successfully loaded Manim task store.")
    except Exception as task_store_error:
        print(f"Warning: Failed to initialize Manim task store: {task_store_error}")

    app.include_router(manim_router)
    print("Successfully included Manim router.")

    MANIM_VIDEOS_SERVE_DIR = Path(__file__).parent / "manim_engine" / "output"
    os.makedirs(MANIM_VIDEOS_SERVE_DIR, exist_ok=True)
    app.mount("/animations/video", StaticFiles(directory=MANIM_VIDEOS_SERVE_DIR), name="manim_videos")
    print(f"Static files for Manim videos mounted from {MANIM_VIDEOS_SERVE_DIR} at /animations/video.")

except ImportError as e:
    print(f"Warning: Manim engine not available: {e}")

# Try to include classroom engine
try:
    from .classroom_engine.router import router as classroom_router
    app.include_router(classroom_router, prefix="/classroom")
    print("Successfully included Classroom router.")
except ImportError as e:
    print(f"Warning: Failed to import classroom router: {e}. Classroom API endpoints will not be available.")
except Exception as e:
    print(f"Warning: Error setting up classroom engine: {e}. Classroom API endpoints may not work correctly.")

# Try to include diagnostic engine
try:
    from .diagnostic_engine.api_integration import router as diagnostic_router
    app.include_router(diagnostic_router)
    print("Successfully included Diagnostic router.")
except ImportError as e:
    print(f"Warning: Failed to import diagnostic router: {e}. Diagnostic API endpoints will not be available.")
except Exception as e:
    print(f"Warning: Error setting up diagnostic engine: {e}. Diagnostic API endpoints may not work correctly.")

@app.post("/upload-content", response_model=str)
async def upload_content(file: Optional[UploadFile] = File(None), text_content: Optional[str] = Form(None)):
    """
    Upload text content either as a file or as raw text.
    Returns the extracted text content.
    """
    if file:
        content = await file.read()
        
        if file.filename.endswith(".txt"):
            return content.decode("utf-8")
        
        elif file.filename.endswith(".pdf"):
            try:
                pdf_file = io.BytesIO(content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text = ""
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n\n"
                
                if not text.strip():
                    raise HTTPException(status_code=400, detail="Could not extract text from the PDF. The file may be scanned or encrypted.")
                
                return text
            except Exception as e:
                print(f"Error extracting text from PDF: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Error processing PDF file: {str(e)}")
        else:
            raise HTTPException(status_code=400, detail="Only .txt and .pdf files are supported at this time")
    elif text_content:
        return text_content
    else:
        raise HTTPException(status_code=400, detail="Either file or text_content must be provided")

@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 