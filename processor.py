import io
import re
import os
import fitz
import pytesseract
from PIL import Image

# Для запуска нужен установленный Tesseract. По умолчанию он включен в большинство дистрибутивов Linux.
# Чтобы запустить на Windows, нужно установить Tesseract. Поэтому использую проверку, чтобы можно было этот код без изменений запустить на сервере
if os.name == 'nt':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def count_cyrillic(text: str) -> int:
    return len(re.findall(r'[а-яА-ЯёЁ]', text))


def normalize_pdf_orientation(file_bytes: bytes) -> bytes:
    doc = fitz.open(stream=file_bytes, filetype="pdf")

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)

        pix = page.get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(pix.tobytes("png"))).convert('L')

        osd_success = False

        try:
            osd_data = pytesseract.image_to_osd(img, output_type=pytesseract.Output.DICT)
            rotation = osd_data['rotate']
            confidence = osd_data['orientation_conf']

            print(f"Страница {page_num} -> OSD просит повернуть на: {rotation} (Уверенность: {confidence})", flush=True)

            if confidence > 15.0:
                if rotation != 0:
                    page.set_rotation((page.rotation + rotation) % 360)
                osd_success = True
                print(f"Страница {page_num} -> Успешно применено по OSD.", flush=True)
            else:
                print(f"Страница {page_num} -> Низкая уверенность OSD. Переход к запасному методу.", flush=True)

        except pytesseract.TesseractError as e:
            print(f"Страница {page_num} -> Ошибка OSD: {e}. Переход к запасному методу.", flush=True)

        if not osd_success:
            best_angle = 0
            max_letters = 0

            print(f"Страница {page_num} -> Запуск поиска текста по углам...", flush=True)

            for test_angle in [0, 90, 180, 270]:
                rotated_img = img.rotate(-test_angle, expand=True)
                text = pytesseract.image_to_string(rotated_img, lang='rus', config='--psm 6')
                letters_count = count_cyrillic(text)

                print(f"--- Угол {test_angle}: найдено {letters_count} рус. букв", flush=True)

                if letters_count > max_letters:
                    max_letters = letters_count
                    best_angle = test_angle

            if max_letters > 20:
                print(f"Страница {page_num} -> Fallback выбрал угол {best_angle} (Макс. букв: {max_letters})",
                      flush=True)
                if best_angle != 0:
                    new_rotation = (page.rotation + best_angle) % 360
                    page.set_rotation(new_rotation)
            else:
                print(f"Страница {page_num} -> Fallback не нашел достаточно текста, страница пропущена.", flush=True)

        print("-" * 40, flush=True)

    out_pdf = io.BytesIO()
    doc.save(out_pdf)
    doc.close()

    return out_pdf.getvalue()