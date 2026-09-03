import os
import glob
import time
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from scraper import convert_url_to_pdf, OUTPUT_DIR

app = FastAPI(
    title="Universal Article PDF Generator",
    description="Automated Article Scraper & PDF Generator API",
    version="1.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConvertRequest(BaseModel):
    url: str
    template_id: Optional[str] = "economic"
    custom_filename: Optional[str] = None
    raw_html: Optional[str] = None
    cookie_header: Optional[str] = None

@app.post("/api/convert")
def convert_article(req: ConvertRequest):
    if not req.url or not req.url.startswith(('http://', 'https://')):
        raise HTTPException(status_code=400, detail="Please provide a valid HTTP or HTTPS article URL.")
    
    try:
        result = convert_url_to_pdf(
            url=req.url,
            template_id=req.template_id or "economic",
            custom_filename=req.custom_filename,
            raw_html=req.raw_html,
            cookie_header=req.cookie_header
        )
        result['download_url'] = f"/api/download/{result['filename']}"
        return JSONResponse(content={"status": "success", "data": result})
    except Exception as e:
        print(f"Conversion Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to scrape & convert article: {str(e)}")

@app.get("/api/history")
def get_history():
    pdf_files = glob.glob(os.path.join(OUTPUT_DIR, "*.pdf"))
    history = []
    
    for filepath in sorted(pdf_files, key=os.path.getmtime, reverse=True):
        filename = os.path.basename(filepath)
        history.append({
            'filename': filename,
            'filepath': filepath,
            'filesize': os.path.getsize(filepath),
            'mtime': os.path.getmtime(filepath),
            'formatted_date': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(filepath))),
            'download_url': f"/api/download/{filename}"
        })
        
    return JSONResponse(content={"status": "success", "history": history})

@app.get("/api/download/{filename}")
def download_pdf(filename: str):
    filepath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Requested PDF file not found.")
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type='application/pdf'
    )

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
os.makedirs(STATIC_DIR, exist_ok=True)

# Direct Root Manifest & Service Worker Routes for PWABuilder / Android WebAPK
@app.get("/manifest.json")
def get_manifest():
    manifest_path = os.path.join(STATIC_DIR, "manifest.json")
    return FileResponse(manifest_path, media_type="application/manifest+json")

@app.get("/sw.js")
def get_sw():
    sw_path = os.path.join(STATIC_DIR, "sw.js")
    return FileResponse(sw_path, media_type="application/javascript")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def read_root():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"message": "Universal Article PDF Generator Server is Running."})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
