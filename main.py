from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import Response
from processor import normalize_pdf_orientation

app = FastAPI(title="PDF Orientation Normalizer")

@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/api/v1/orient")
async def orient_pdf(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=415, detail="Поддерживаются только PDF файлы.")

    try:
        pdf_bytes = await file.read()

        if not pdf_bytes.startswith(b"%PDF-"):
            raise HTTPException(status_code=400, detail="Файл не является валидным PDF (отсутствует сигнатура).")

        normalized_pdf_bytes = normalize_pdf_orientation(pdf_bytes)

        return Response(
            content=normalized_pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=normalized.pdf"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка обработки: {str(e)}")