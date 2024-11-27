from fastapi import FastAPI, Form, Request, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
import os
from dotenv import load_dotenv
from groq import Groq
import pdfplumber
from docx import Document
from utils import generate_mcqs, save_mcqs_to_doc, read_pdf, read_docx, read_txt

# Create FastAPI app
app = FastAPI()

# Set up templates for HTML
templates = Jinja2Templates(directory="templates")

SAVE_DIR = "generated_docs"
os.makedirs(SAVE_DIR, exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "mcqs": None})


@app.post("/", response_class=HTMLResponse)
async def generate_mcqs_page(
    request: Request,
    text: str = Form(...),
    num_questions: int = Form(...),
    difficulty_level: str = Form("medium"),
    include_topics: str = Form(""),
    exclude_topics: str = Form(""),
    question_format: str = Form("mcq"),
):
    # Generate MCQs with customization options
    mcqs = generate_mcqs(
        text,
        num_questions,
        difficulty_level,
        include_topics,
        exclude_topics,
        question_format,
    )

    return templates.TemplateResponse("index.html", {"request": request, "mcqs": mcqs})


@app.post("/upload", response_class=HTMLResponse)
async def upload_pdf(
    request: Request,
    file: UploadFile = File(...),
    num_questions: int = Form(...),
    difficulty_level: str = Form("medium"),
    include_topics: str = Form(""),
    exclude_topics: str = Form(""),
    question_format: str = Form("mcq"),
):
    # Check file size
    file_size = len(
        await file.read()
    )  # Read the entire file into memory to check its size
    if file_size > MAX_FILE_SIZE:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "mcqs": None,
                "error": f"Error: File size exceeds the {MAX_FILE_SIZE / (1024 * 1024)} MB limit.",
            },
        )

    # Reset the file pointer after reading for size check (important!)
    file.file.seek(0)

    # Read and parse the uploaded PDF (or DOCX/TXT)
    try:
        if file.filename.endswith(".pdf"):
            with pdfplumber.open(file.file) as pdf:
                text = "\n".join(
                    page.extract_text() for page in pdf.pages if page.extract_text()
                )
        elif file.filename.endswith(".docx"):
            doc = Document(file.file)
            text = "\n".join([para.text for para in doc.paragraphs])
        elif file.filename.endswith(".txt"):
            text = await file.read()
            text = text.decode("utf-8")  # Decode bytes to string for TXT files
        else:
            raise ValueError("Unsupported file format")

    except Exception as e:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "mcqs": None,
                "error": f"Error reading file: {str(e)}",
            },
        )

    # Generate MCQs with customization based on form data
    mcqs = generate_mcqs(
        text,
        num_questions,
        difficulty_level,
        include_topics,
        exclude_topics,
        question_format,
    )

    return templates.TemplateResponse("index.html", {"request": request, "mcqs": mcqs})


@app.post("/save")
async def save_mcqs(mcqs: str = Form(...), file_name: str = Form("mcqs.docx")):
    """Saves MCQs to a .doc file and returns the file for download."""
    try:
        file_path = save_mcqs_to_doc(mcqs, file_name)
        return FileResponse(
            file_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=file_name,
        )
    except Exception as e:
        return {"error": f"Failed to save MCQs: {str(e)}"}
