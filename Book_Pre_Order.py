import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from datetime import datetime

# Page Configuration
st.set_page_config(page_title="Book Order", page_icon="📚")

BOOK_OPTIONS = {
    "Option 1 - Hard Copy Only (60,000 MMK)": 60000,
    "Option 2 - Hard Copy + Soft Copy + Training (100,000 MMK)": 100000,
}


# --- UI Header ---
try:
    st.image("book.png", use_container_width=True)
except Exception:
    st.warning("Book cover image not found. Please add `book.png` in this folder.")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700&family=Noto+Sans+Myanmar:wght@500;700&display=swap');

    .book-header {
        text-align: center;
        margin-top: 0.5rem;
        margin-bottom: 1.2rem;
        padding: 0.3rem 0.5rem 0.8rem 0.5rem;
        border-bottom: 2px solid #5aa8c6;
    }
    .book-title-mm {
        font-family: 'Noto Sans Myanmar', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        color: #148fbe;
        margin-bottom: 0.35rem;
    }
    .book-title-en {
        font-family: 'Cinzel', serif;
        font-size: 2.2rem;
        font-weight: 700;
        letter-spacing: 0.03em;
        color: #0d6f98;
        margin-bottom: 0.45rem;
        text-transform: uppercase;
    }
    .book-author {
        font-family: 'Noto Sans Myanmar', sans-serif;
        font-size: 1.25rem;
        color: #2f3a40;
        font-weight: 600;
    }
    </style>

    <div class="book-header">
        <div class="book-title-mm">စီးပွါးရေးအတိုင်ပင်ခံ လျှို့ဝှက်လက်စွဲ</div>
        <div class="book-title-en">The Secret Handbook for Business Consultants</div>
        <div class="book-author">စာရေးသူ: Dr. Yin Hlaing Min</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# --- Google Services Setup ---
def get_sheets_client():
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file",
        ],
    )
    return gspread.authorize(creds)


def upload_to_drive(file_obj, filename):
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/drive"],
    )
    drive_service = build("drive", "v3", credentials=creds)

    file_metadata = {"name": filename, "parents": [st.secrets["FOLDER_ID"]]}
    media = MediaIoBaseUpload(
        file_obj,
        mimetype=getattr(file_obj, "type", None) or "application/octet-stream",
    )
    file = (
        drive_service.files()
        .create(body=file_metadata, media_body=media, fields="webViewLink")
        .execute()
    )
    return file.get("webViewLink")


# --- Main Form ---
with st.form("preorder_form", clear_on_submit=True):
    name = st.text_input("အမည်")
    phone = st.text_input("ဖုန်းနံပါတ်")
    email = st.text_input("အီးမေးလ်")
    qty = st.number_input("မှာယူမည့်အရေအတွက်", min_value=1, step=1)

    book_option = st.radio("ဝယ်ယူမည့် Package", list(BOOK_OPTIONS.keys()))
    unit_price = BOOK_OPTIONS[book_option]
    total_price = unit_price * int(qty)
    st.info(f"ကျသင့်ငွေစုစုပေါင်း: {total_price:,} MMK")

    delivery_type = st.radio(
        "လက်ခံယူမည့်ပုံစံ", ["မိတ်ဆက်ပွဲတွင် ယူမည်", "Delivery ဖြင့်ပို့ရန်"]
    )

    st.markdown("### ငွေပေးချေရန် အချက်အလက်")
    st.info("K Pay Number: 09420064987 (Yin Hlaing Min)")

    address = ""
    if delivery_type == "Delivery ဖြင့်ပို့ရန်":
        address = st.text_area("ပို့ပေးရမည့်လိပ်စာ")

    slip = st.file_uploader("ငွေလွှဲ Slip ပုံတင်ရန်", type=["jpg", "png", "jpeg"])
    submitted = st.form_submit_button("Order တင်မည်")

    if submitted:
        if not name or not phone or not email or not slip:
            st.error("အချက်အလက်အားလုံး (Slip အပါအဝင်) ဖြည့်ပေးပါ။")
        elif delivery_type == "Delivery ဖြင့်ပို့ရန်" and not address:
            st.error("လိပ်စာဖြည့်ပေးပါရန်။")
        else:
            with st.spinner("Order တင်နေပါပြီ..."):
                try:
                    file_ext = (slip.name.rsplit(".", 1)[-1].lower() if "." in slip.name else "jpg")
                    filename = (
                        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        f"_{name}_{phone}_slip.{file_ext}"
                    )
                    file_link = upload_to_drive(slip, filename)

                    client = get_sheets_client()
                    sheet = client.open("PreOrderDatabase").sheet1
                    row = [
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        name,
                        phone,
                        email,
                        qty,
                        book_option,
                        unit_price,
                        total_price,
                        delivery_type,
                        address,
                        file_link,
                    ]
                    sheet.append_row(row)

                    st.success("သင်၏ အော်ဒါကို အောင်မြင်စွာ လက်ခံရရှိပါပြီ။ ကျေးဇူးတင်ပါသည်။")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error ဖြစ်သွားပါသည်: {e}")
