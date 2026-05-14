from fastapi import FastAPI, UploadFile, File, Request, HTTPException, Depends
from fastapi.responses import FileResponse, RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import shortuuid
import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
from config import UPLOAD_DIR, DB_PATH, MAX_FILE_SIZE

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs('instances', exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}")
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

class FileEntry(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True)
    short_code = Column(String, unique=True, index=True)
    original_name = Column(String)
    file_path = Column(String)
    size = Column(Integer)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Angst Share")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload(file: UploadFile = File(...), db = Depends(get_db)):
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(400, "File te groot")
    
    short_code = shortuuid.uuid()[:8]
    file_path = f"{UPLOAD_DIR}/{short_code}_{file.filename}"
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    entry = FileEntry(
        short_code=short_code,
        original_name=file.filename,
        file_path=file_path,
        size=len(content)
    )
    db.add(entry)
    db.commit()
    
    return {"url": f"/f/{short_code}", "delete_url": f"/delete/{short_code}"}

@app.get("/f/{short_code}")
async def serve_file(short_code: str, db = Depends(get_db)):
    entry = db.query(FileEntry).filter_by(short_code=short_code).first()
    if not entry:
        raise HTTPException(404, "File niet gevonden")
    return FileResponse(entry.file_path, filename=entry.original_name)

@app.get("/files", response_class=HTMLResponse)
async def list_files(request: Request, db = Depends(get_db)):
    files = db.query(FileEntry).order_by(FileEntry.uploaded_at.desc()).all()
    return templates.TemplateResponse("files.html", {"request": request, "files": files})

@app.get("/delete/{short_code}")
async def delete_file(short_code: str, db = Depends(get_db)):
    entry = db.query(FileEntry).filter_by(short_code=short_code).first()
    if entry:
        if os.path.exists(entry.file_path):
            os.remove(entry.file_path)
        db.delete(entry)
        db.commit()
    return RedirectResponse("/files")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)