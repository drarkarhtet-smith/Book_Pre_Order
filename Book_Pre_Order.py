import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from datetime import datetime
import io

# Page Configuration
st.set_page_config(page_title="Book Pre-order", page_icon="📚")

# --- UI Header ---
# သင့် logo ကို folder ထဲမှာ ထည့်ထားပါ (logo.png)
try:
    st.image("logo.png", width=200)
except:
    pass

st.title("📚 The Secret Handbook for Business Consultants")
st.markdown("### **စာရေးသူ:** Dr. Yin Hlaing Min")
st.markdown("---")

# --- Google Services Setup ---
def get_sheets_client():
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file"])
    return gspread.authorize(creds)

def upload_to_drive(file_obj, filename):
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=["https://www.googleapis.com/auth/drive"])
    drive_service = build('drive', 'v3', credentials=creds)
    
    file_metadata = {'name': filename, 'parents': [st.secrets["FOLDER_ID"]]}
    media = MediaIoBaseUpload(file_obj, mimetype='image/jpeg')
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='webViewLink').execute()
    return file.get('webViewLink')

# --- Main Form ---
with st.form("preorder_form", clear_on_submit=True):
    name = st.text_input("အမည်")
    phone = st.text_input("ဖုန်းနံပါတ်")
    qty = st.number_input("မှာယူမည့်အရေအတွက်", min_value=1, step=1)
    
    delivery_type = st.radio("လက်ခံယူမည့်ပုံစံ", ["မိတ်ဆက်ပွဲတွင် ယူမည်", "Delivery ဖြင့်ပို့ရန်"])
    
    address = ""
    if delivery_type == "Delivery ဖြင့်ပို့ရန်":
        address = st.text_area("ပို့ပေးရမည့်လိပ်စာ")
    
    slip = st.file_uploader("ငွေလွှဲ Slip ပုံတင်ရန်", type=["jpg", "png", "jpeg"])
    
    submitted = st.form_submit_button("Order တင်မည်")

    if submitted:
        if not name or not phone or not slip:
            st.error("အချက်အလက်အားလုံး (Slip အပါအဝင်) ဖြည့်ပေးပါ။")
        elif delivery_type == "Delivery ဖြင့်ပို့ရန်" and not address:
            st.error("လိပ်စာဖြည့်ပေးပါရန်။")
        else:
            with st.spinner('Order တင်နေပါပြီ...'):
                try:
                    # Drive တင်ခြင်း
                    file_link = upload_to_drive(slip, f"{name}_{phone}_slip.jpg")
                    
                    # Sheet ထဲ သိမ်းခြင်း
                    client = get_sheets_client()
                    sheet = client.open("PreOrderDatabase").sheet1
                    row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), name, phone, qty, delivery_type, address, file_link]
                    sheet.append_row(row)
                    
                    st.success("သင်၏ အော်ဒါကို အောင်မြင်စွာ လက်ခံရရှိပါပြီ။ ကျေးဇူးတင်ပါသည်။")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error ဖြစ်သွားပါသည်: {e}")
