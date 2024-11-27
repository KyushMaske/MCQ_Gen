*MCQ Generator Web Application*

A web application built with FastAPI to generate multiple-choice questions (MCQs) based on provided text or uploaded documents (PDF, DOCX, or TXT). Users can customize the number of questions, difficulty level, topics to include or exclude, and more. The generated MCQs can be saved as a .docx file for easy download.

Create a .env file to store your GROQ API Key.

uvicorn main:app --reload
