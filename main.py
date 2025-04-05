from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
import pandas as pd
import spacy
import langdetect
import speech_recognition as sr

# Load spaCy NLP model
nlp = spacy.load("en_core_web_sm")

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Load Excel Data
billing_df = pd.read_excel(r"C:\Users\rahul.k\Downloads\master table data.xlsx")
complaints_df = pd.read_excel(r"C:\Users\rahul.k\Downloads\comlpaiyts.xlsx")


def detect_language(text: str) -> str:
    """Detects language (English, Hindi, or Hinglish)."""
    try:
        lang = langdetect.detect(text)
        return "hi" if lang == "hi" else "en"
    except:
        return "en"


def create_html_table(data_dict, title, lang):
    """Creates an HTML table for structured output."""
    table = f"""
    <table border="1" style="border-collapse: collapse; width: 100%;">
        <tr style="background-color: #007bff; color: white; text-align: left;">
            <th colspan="2">{title}</th>
        </tr>
    """
    for key, value in data_dict.items():
        table += f"<tr><td><strong>{key}</strong></td><td>{value}</td></tr>"
    table += "</table>"

    return table


def process_query(query: str) -> str:
    """Processes user query and returns response."""
    lang = detect_language(query)
    doc = nlp(query.lower())

    # 🔹 Bill Inquiry
    if any(token.text in ["bill", "amount", "payment", "account", "status"] for token in doc):
        for acc in billing_df["ACCOUNT_NO"].astype(str):
            if acc in query:
                data = billing_df[billing_df["ACCOUNT_NO"].astype(str) == acc]
                if not data.empty:
                    details = {
                        "नाम" if lang == "hi" else "Name": data.iloc[0]["NAME"],
                        "उपभोक्ता लोड" if lang == "hi" else "Consumer Load": f"{data.iloc[0]['CONSUMER_LOAD']} kW",
                        "मीटर नंबर" if lang == "hi" else "Meter Number": data.iloc[0]["METER_NUMBER"],
                        "बिलिंग स्थिति" if lang == "hi" else "Billing Status": data.iloc[0]["BILLING_STATUS"],
                        "अंतिम बिल महीना" if lang == "hi" else "Last Bill Month-Year": data.iloc[0]["LAST_BILLMONTH_YEAR"],
                        "बिल राशि" if lang == "hi" else "Bill Amount": f"₹{data.iloc[0]['BILL_AMOUNT']}",
                        "भुगतान राशि" if lang == "hi" else "Amount Paid": f"₹{data.iloc[0]['AMOUNT_PAID']}",
                        "कार्यालय" if lang == "hi" else "Office": data.iloc[0]["OFFICE_NAME"],
                    }
                    return create_html_table(details, f"{'खाते ' + acc + ' की जानकारी' if lang == 'hi' else 'Account ' + acc + ' Details'}", lang)

        return "❌ कृपया मान्य खाता संख्या दें।" if lang == "hi" else "❌ Please provide a valid account number."

    # 🔹 Power Cut Inquiry
    elif "bijli" in query and "kab" in query:
        return "⚡ पटना में बिजली 2 घंटे में आएगी। 📞 हेल्पलाइन: 1912" if lang == "hi" else "⚡ Power will be restored in 2 hours in Patna. 📞 Helpline: 1912"

    # 🔹 Complaint Status
    elif "complaint" in query or "issue" in query:
        for acc in complaints_df["ACCOUNT_NO"].astype(str):
            if acc in query:
                data = complaints_df[complaints_df["ACCOUNT_NO"].astype(str) == acc]
                if not data.empty:
                    details = {
                        "शिकायत प्रकार" if lang == "hi" else "Complaint Type": data.iloc[0]["REQUEST_TYPE"],
                        "स्थिति" if lang == "hi" else "Status": data.iloc[0]["APP_STATUS"],
                    }
                    return create_html_table(details, "📢 **शिकायत स्थिति**" if lang == "hi" else "📢 **Complaint Status**", lang)

        return "कोई शिकायत नहीं मिली।" if lang == "hi" else "No complaints found for this account."

    # 🔹 New Connection Inquiry
    elif "naya connection" in query or "new connection" in query:
        details = {
            "चरण 1️⃣" if lang == "hi" else "Step 1️⃣": "SBPDCL वेबसाइट पर जाएं: [SBPDCL Website](https://www.sbpdcl.co.in)" if lang == "hi" else "Visit: [SBPDCL Website](https://www.sbpdcl.co.in)",
            "चरण 2️⃣" if lang == "hi" else "Step 2️⃣": "ऑनलाइन आवेदन करें" if lang == "hi" else "Apply Online",
            "चरण 3️⃣" if lang == "hi" else "Step 3️⃣": "सुरक्षा जमा राशि का भुगतान करें" if lang == "hi" else "Pay Security Deposit",
            "चरण 4️⃣" if lang == "hi" else "Step 4️⃣": "7 दिनों में मीटर इंस्टॉल होगा" if lang == "hi" else "Meter Installation in 7 Days",
            "हेल्पलाइन 📞" if lang == "hi" else "Helpline 📞": "1912",
        }
        return create_html_table(details, "✅ **नया कनेक्शन प्रक्रिया**" if lang == "hi" else "✅ **New Connection Process**", lang)


    # 🔹 Load Extension
    elif "load" in query and "badhana" or "enhancement" in query:  
        return ("🔹 **लोड बढ़ाने की प्रक्रिया:**\n"
                "1️⃣ [SBPDCL Website](https://www.sbpdcl.co.in) पर आवेदन करें\n"
                "2️⃣ एड्रेस और आईडी प्रूफ अपलोड करें\n"
                "3️⃣ लोड बढ़ाने की फीस जमा करें\n"
                "📞 हेल्पलाइन: 1912" if lang == "hi"
                else "🔹 **Load Enhancement Process:**\n"
                     "1️⃣ Apply Online at [SBPDCL Website](https://www.sbpdcl.co.in)\n"
                     "2️⃣ Upload Address & ID Proof\n"
                     "3️⃣ Pay Load Enhancement Fee\n"
                     "📞 Helpline: 1912")

    # 🔹 Smart Meter Benefits
    elif "smart meter" in query:
        return ("🔹 **स्मार्ट मीटर के फायदे:**\n"
                "✅ ऑनलाइन रिचार्ज\n"
                "✅ सटीक बिलिंग\n"
                "✅ तुरंत कटौती/रीकनेक्शन\n"
                "✅ मासिक उपयोग अलर्ट" if lang == "hi"
                else "🔹 **Smart Meter Benefits:**\n"
                     "✅ Online Recharge\n"
                     "✅ Accurate Billing\n"
                     "✅ Instant Power Cut/Reconnection\n"
                     "✅ Monthly Usage Alerts")

    # 🔹 Default Response
    else:
        if lang == "hi":
            if query.lower() in ["hi", "hello"]:
                return "नमस्ते! कैसे मदद कर सकता हूँ?"
            elif query.lower() == "kaise ho":
                return "मैं ठीक हूँ, बताओ क्या कर रहा हूँ?"
            elif query.lower() == "mujhe help chahiye":
                return "हाँ, बताओ क्या मदद चाहिए?"
            else:
                return "❌ मुझे समझ में नहीं आया! कृपया स्पष्ट करें।"
        else:
            if query.lower() in ["hi", "hello"]:
                return "Hello! How can I assist you?"
            elif query.lower() == "how are you":
                return "I'm doing well, tell me what you're up to?"
            elif query.lower() == "i need help":
                return "Yes, tell me what help you need?"
            else:
                return "❌ I didn't understand! Please clarify."


@app.post("/chat/") 
async def chat(message: str = Form(...)):
    reply = process_query(message)
    return {"reply": reply}


@app.post("/speech-to-text/") 
async def speech_to_text(audio: UploadFile = File(...)):
    """Converts audio to text using SpeechRecognition."""
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio.file) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data, language="hi-IN")
            return {"text": text}
        except sr.UnknownValueError:
            return {"error": "Speech not recognized"}
        except sr.RequestError:
            return {"error": "API request failed"}


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
