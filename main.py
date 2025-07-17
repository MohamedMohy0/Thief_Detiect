from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import gspread
import json
import re
from oauth2client.service_account import ServiceAccountCredentials
import os

app = FastAPI()

# لتفعيل الاتصال من React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def connect_to_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_json = os.getenv("GOOGLE_CREDS")  # Load from env var
    if creds_json is None:
        raise Exception("Missing GOOGLE_CREDS environment variable.")

    creds_dict = json.loads(creds_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key("1B5GhDPdkWhdyo39RLStR0o10VDQ77Wlw01DigisNRN0").sheet1
    return sheet

def clean_number(number: str) -> str:
    return re.sub(r"\D", "", number)

@app.get("/check_number")
def check_number(phone: str = Query(..., description="Phone number to check")):
    try:
        sheet = connect_to_sheet()
        raw_numbers = sheet.col_values(1)[1:]  # تجاهل أول صف
        cleaned_input = clean_number(phone)
        cleaned_sheet = [clean_number(n) for n in raw_numbers]

        if phone in raw_numbers:
            idx = raw_numbers.index(phone) + 2
        elif cleaned_input in raw_numbers:
            idx = raw_numbers.index(cleaned_input) + 2
        elif cleaned_input in cleaned_sheet:
            idx = cleaned_sheet.index(cleaned_input) + 2
        else:
            return {
                "found": False,
                "raw_input": phone,
                "message": f"الرقم {phone} غير موجود في البيانات ممكن يكون نصاب بس لسه متسجلش في الداتا معنى كدا اننا معندناش بيانات ليه، ممكن يبقى نصاب ولسة متسجلش، وممكن يكون امان فخد احتياطاتك  \n No risk No rizk"
            }

        row = sheet.row_values(idx)
        return {
            "found": True,
            "raw_input": phone,
            "matched_clean": cleaned_input,
            "row": row
        }

    except Exception as e:
        print(f"❌ Server Error: {e}")
        return {
            "found": False,
            "message": "❌ حدث خطأ في الخادم.",
            "details": str(e)
        }
