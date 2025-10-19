import os
import re
import tempfile
import streamlit as st
from PIL import Image
from pdf2image import convert_from_path, pdfinfo_from_path
import pytesseract

# ----------------------------------------------------------------------
# تنظیمات اولیه
# ----------------------------------------------------------------------
ZWNJ = '\u200c'

# ----------------------------------------------------------------------
# تابع نرمال‌سازی متن فارسی
# ----------------------------------------------------------------------
def normalize_text(text: str) -> str:
    if not text:
        return ""
    
    arabic_to_persian = {
        'ك': 'ک', 'ي': 'ی', 'ئ': 'ی', 'أ': 'ا', 'ة': 'ه',
        'ؤ': 'و', 'إ': 'ا', 'ٰ': '', 'ٔ': '', 'ّ': ''
    }
    for ar, pr in arabic_to_persian.items():
        text = text.replace(ar, pr)

    corrections = {
        'پسرده': 'پرده', 'اینن': 'این', 'خلسوت': 'خلوت',
        'نضورد': 'نخورد', 'سبصد': 'سیصد', 'صایون': 'صابون',
        'وشد': 'شد', 'میکنند': 'می‌کنند', 'میشود': 'می‌شود',
        'میکرد': 'می‌کرد', 'میکنم': 'می‌کنم', 'میکنی': 'می‌کنی',
        'میکسرد': 'می‌کرد', 'میکسند': 'می‌کنند', 'اِقتصاد': 'اقتصاد',
        'اِجتماع': 'اجتماع', 'اِنسان': 'انسان', 'اِمکان': 'امکان'
    }
    for wrong, correct in corrections.items():
        text = text.replace(wrong, correct)

    text = re.sub(r'\b[0-9a-zA-Z\-]+\b', '', text)
    text = re.sub(r'[^\w\s\u200c\u200d\u200e\u200f\u0600-\u06FF]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'(می|نمی)\s+(باشد|کند|شود|روم|کنم|کنی|کنید|کنیم|رسد|گردد|دهد)',
                  lambda m: m.group(1) + ZWNJ + m.group(2), text)
    text = re.sub(r'(ها)\s+', r'\1' + ZWNJ + ' ', text)
    text = re.sub(r'\s+([؟؟،،.:!;])', r'\1', text)
    text = re.sub(r'([؟؟.!?])\s*', r'\1\n', text)
    return text

# ----------------------------------------------------------------------
# OCR از تصویر
# ----------------------------------------------------------------------
def ocr_from_image(image: Image.Image) -> str:
    image = image.convert('L')
    config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
    raw = pytesseract.image_to_string(image, lang='fas+eng', config=config)
    return normalize_text(raw)

# ----------------------------------------------------------------------
# OCR از PDF با بازه صفحات
# ----------------------------------------------------------------------
def ocr_from_pdf(pdf_path: str, start_page: int, end_page: int) -> str:
    try:
        info = pdfinfo_from_path(pdf_path)
        total_pages = int(info["Pages"])
        end_page = min(end_page, total_pages)
        start_page = max(1, start_page)

        if start_page > total_pages:
            return "❌ شماره صفحه شروع از تعداد کل صفحات بیشتر است."

        images = convert_from_path(
            pdf_path, dpi=300, first_page=start_page, last_page=end_page
        )

        all_text = f"📊 استخراج صفحات {start_page} تا {end_page} از {total_pages} صفحه:\n\n"
        for i, img in enumerate(images):
            page_num = start_page + i
            text = ocr_from_image(img)
            all_text += f"--- صفحه {page_num} ---\n{text}\n\n"

        return all_text.strip()

    except Exception as e:
        return f"❌ خطا در پردازش PDF: {str(e)}"

# ----------------------------------------------------------------------
# رابط کاربری Streamlit با استایل کتابی فارسی
# ----------------------------------------------------------------------
def main():
    st.set_page_config(page_title="OCR فارسی - استخراج متن", layout="wide")
    st.markdown(
        """
        <style>
        body {
            direction: rtl;
            text-align: right;
            font-family: "Vazir", "Tahoma", sans-serif;
        }
        textarea {
            direction: rtl !important;
            text-align: justify !important;
            font-family: "Vazir", "Tahoma", sans-serif !important;
            line-height: 1.8 !important;
            white-space: pre-wrap !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("🎯 سیستم OCR فارسی پیشرفته")
    st.markdown("استخراج متن از **PDF** یا **تصویر** با حفظ خطوط و پاراگراف‌های اصلی کتاب")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ تنظیمات استخراج")
        uploaded_file = st.file_uploader("📁 فایل خود را آپلود کنید (PDF، JPG، PNG)", 
                                         type=["pdf", "jpg", "jpeg", "png"])

        start_page = 1
        end_page = 1

        if uploaded_file is not None:
            file_ext = uploaded_file.name.lower().split('.')[-1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name

            if file_ext == "pdf":
                try:
                    info = pdfinfo_from_path(tmp_path)
                    total_pages = int(info["Pages"])
                    st.success(f"📄 فایل PDF با **{total_pages} صفحه** شناسایی شد.")
                    extract_all = st.checkbox("✅ استخراج همه صفحات", value=True)
                    if not extract_all:
                        start_page = st.number_input("صفحه شروع", 1, total_pages, 1)
                        end_page = st.number_input("صفحه پایان", 1, total_pages, total_pages)
                    else:
                        start_page, end_page = 1, total_pages
                except Exception as e:
                    st.error(f"❌ خطا در خواندن PDF: {e}")
            else:
                st.info("📷 فایل تصویری — تمام محتوا پردازش خواهد شد.")
        else:
            tmp_path = None

    # Main
    if uploaded_file is not None:
        file_ext = uploaded_file.name.lower().split('.')[-1]

        if file_ext == "pdf":
            if st.button("🚀 استخراج متن از PDF", use_container_width=True):
                with st.spinner("در حال پردازش..."):
                    result = ocr_from_pdf(tmp_path, start_page, end_page)
                    st.markdown("### 📝 متن استخراج‌شده (فرمت کتابی)")
                    st.text_area("📘 خروجی OCR", result, height=600)
                    st.download_button("📥 دانلود متن", result, file_name="extracted_text.txt")

        else:
            st.image(uploaded_file, caption="تصویر آپلود شده", use_column_width=True)
            if st.button("🚀 استخراج متن از تصویر", use_container_width=True):
                with st.spinner("در حال پردازش..."):
                    image = Image.open(tmp_path)
                    result = ocr_from_image(image)
                    st.markdown("### 📝 متن استخراج‌شده (فرمت کتابی)")
                    st.text_area("📘 خروجی OCR", result, height=600)
                    st.download_button("📥 دانلود متن", result, file_name="extracted_text.txt")

        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    else:
        st.info("📁 لطفاً یک فایل آپلود کنید.")

if __name__ == "__main__":
    main()
