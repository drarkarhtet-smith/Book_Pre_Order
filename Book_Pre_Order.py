import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import smtplib
from email.message import EmailMessage

# Page Configuration
st.set_page_config(page_title="Book Order", page_icon="📚")

BOOK_OPTIONS = {
    "Option 1 - Hard Copy Only (60,000 MMK)": 60000,
    "Option 2 - Hard Copy + Soft Copy + Training (100,000 MMK)": 100000,
}
ADMIN_EMAIL = "dr.arkarhtet@gmail.com"


# --- UI Header ---
try:
    # New Streamlit prefers width="stretch"; fallback keeps compatibility.
    try:
        st.image("book.png", width="stretch")
    except TypeError:
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
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    return gspread.authorize(creds)


def send_slip_email(
    file_obj,
    attachment_name,
    name,
    phone,
    email,
    qty,
    book_option,
    unit_price,
    total_price,
    delivery_type,
    address,
):
    required_secret_keys = ["smtp_host", "smtp_user", "smtp_password"]
    missing_keys = [key for key in required_secret_keys if key not in st.secrets]
    if missing_keys:
        raise RuntimeError(
            "Missing Streamlit secrets for email: " + ", ".join(missing_keys)
        )

    smtp_host = st.secrets["smtp_host"]
    smtp_port = int(st.secrets.get("smtp_port", 465))
    smtp_user = st.secrets["smtp_user"]
    smtp_password = st.secrets["smtp_password"]
    smtp_sender = st.secrets.get("smtp_sender", smtp_user)

    message = EmailMessage()
    message["Subject"] = f"Book Pre-Order Slip: {name} ({phone})"
    message["From"] = smtp_sender
    message["To"] = ADMIN_EMAIL
    message["Reply-To"] = email
    message.set_content(
        "\n".join(
            [
                "New book pre-order submitted.",
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"Customer Name: {name}",
                f"Phone: {phone}",
                f"Customer Email: {email}",
                f"Quantity: {qty}",
                f"Package: {book_option}",
                f"Unit Price: {unit_price:,} MMK",
                f"Total Price: {total_price:,} MMK",
                f"Delivery Type: {delivery_type}",
                f"Address: {address if address else '-'}",
                "",
                "Payment slip is attached.",
            ]
        )
    )

    mime_type = getattr(file_obj, "type", "") or "application/octet-stream"
    if "/" in mime_type:
        maintype, subtype = mime_type.split("/", 1)
    else:
        maintype, subtype = "application", "octet-stream"

    message.add_attachment(
        file_obj.getvalue(),
        maintype=maintype,
        subtype=subtype,
        filename=attachment_name,
    )

    with smtplib.SMTP_SSL(smtp_host, smtp_port) as smtp:
        smtp.login(smtp_user, smtp_password)
        smtp.send_message(message)


# --- Main Form ---
with st.form("preorder_form", clear_on_submit=False):
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

    slip = st.file_uploader(
        "ငွေလွှဲ Slip ပုံတင်ရန်",
        type=["jpg", "png", "jpeg"],
        key="payment_slip",
    )
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
                    send_slip_email(
                        file_obj=slip,
                        attachment_name=filename,
                        name=name,
                        phone=phone,
                        email=email,
                        qty=qty,
                        book_option=book_option,
                        unit_price=unit_price,
                        total_price=total_price,
                        delivery_type=delivery_type,
                        address=address,
                    )

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
                        f"Sent to {ADMIN_EMAIL} ({filename})",
                        "Pending Verification",
                    ]
                    sheet.append_row(row)

                    st.success(
                        "Order ကို လက်ခံရရှိပါပြီ။ Payment slip ကို စစ်ဆေးပြီးနောက် အတည်ပြုချက် ပြန်လည်ပေးပို့ပါမည်။"
                    )
                    st.balloons()
                except Exception as e:
                    st.error(f"Error ဖြစ်သွားပါသည်: {e}")
