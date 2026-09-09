import io
import re
import fitz
import pytesseract
from PIL import Image


def normalize_pdf_orientation(pdf_bytes: bytes) -> bytes:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(dpi=150)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        try:
            osd_result = pytesseract.image_to_osd(img)
            print(f"Страница {page_num}:", osd_result.replace('\n', ' | '))  # Временный принт для отладки

            rotation_match = re.search(r'Rotate: (\d+)', osd_result)
            confidence_match = re.search(r'Orientation confidence: ([\d\.]+)', osd_result)

            if rotation_match and confidence_match:
                angle = int(rotation_match.group(1))
                confidence = float(confidence_match.group(1))

                if confidence > 2.0 and angle != 0:
                    current_rotation = page.rotation
                    new_rotation = (current_rotation - angle) % 360
                    page.set_rotation(new_rotation)

        except pytesseract.TesseractError:
            continue

    out_pdf = io.BytesIO()

    doc.save(out_pdf)
    doc.close()

    return out_pdf.getvalue()