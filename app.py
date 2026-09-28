import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time

# --- 1. PROFESSIONAL UI SETTINGS ---
# This hides the default Streamlit menu and footer
st.set_page_config(page_title="Professional Bulk Mailer", layout="wide")
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- 2. MASTER SECURITY PASSWORD ---
APP_PASSWORD = "mysecretpassword123"

if st.text_input("Enter Access Password:", type="password") != APP_PASSWORD:
    st.warning("Please enter the correct password to access the tool.")
    st.stop()

# --- 3. SESSION STATE (MEMORY) ---
# This ensures the app remembers your email credentials when you switch pages
if 'sender_email' not in st.session_state:
    st.session_state.sender_email = ""
if 'email_app_password' not in st.session_state:
    st.session_state.email_app_password = ""

# --- 4. SIDEBAR NAVIGATION ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["⚙️ Account Settings", "📧 Send Emails"])

# ==========================================
# PAGE 1: ACCOUNT SETTINGS
# ==========================================
if page == "⚙️ Account Settings":
    st.title("Account Settings")
    st.write("Save your Gmail and App Password here. To switch accounts, simply overwrite them and click save.")
    
    new_email = st.text_input("Your Email Address", value=st.session_state.sender_email)
    new_password = st.text_input("Email App Password", type="password", value=st.session_state.email_app_password)
    
    if st.button("Save Credentials"):
        st.session_state.sender_email = new_email
        st.session_state.email_app_password = new_password
        st.success("✅ Credentials saved securely for this session!")

# ==========================================
# PAGE 2: SEND EMAILS
# ==========================================
elif page == "📧 Send Emails":
    st.title("Send Bulk Emails")
    
    # Check if user logged in on the other page
    if not st.session_state.sender_email or not st.session_state.email_app_password:
        st.warning("⚠️ Please go to **⚙️ Account Settings** first and save your email credentials.")
        st.stop()
        
    st.info(f"Currently sending from: **{st.session_state.sender_email}**")
    
    st.header("1. Email Content")
    subject = st.text_input("Email Subject")
    body = st.text_area("Email Body", height=200, help="Write your email content here.")
    
    st.header("2. Recipients")
    recipient_method = st.radio("How do you want to add recipients?", ["Manual Entry (For Testing)", "Upload Excel/CSV"])
    
    emails = []
    
    # MANUAL ENTRY OPTION
    if recipient_method == "Manual Entry (For Testing)":
        manual_emails = st.text_area("Enter email addresses (separated by commas)")
        if manual_emails:
            # Clean up the text and split by comma
            emails = [e.strip() for e in manual_emails.split(",") if e.strip()]
            
    # FILE UPLOAD OPTION
    else:
        uploaded_file = st.file_uploader("Upload File (.xlsx or .csv)", type=["csv", "xlsx"])
        if uploaded_file:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                emails = df.iloc[:, 0].dropna().tolist()
                st.success(f"Found {len(emails)} email(s) in the file.")
            except Exception as e:
                st.error(f"Error reading file: {e}")

    # SENDING LOGIC
    if st.button("Start Sending"):
        if not subject or not body:
            st.error("Please enter a subject and body.")
        elif not emails:
            st.error("Please add at least one recipient.")
        else:
            st.info("Connecting to server...")
            try:
                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.starttls()
                server.login(st.session_state.sender_email, st.session_state.email_app_password)
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                success_count = 0
                for i, recipient in enumerate(emails):
                    try:
                        msg = MIMEMultipart()
                        msg['From'] = st.session_state.sender_email
                        msg['To'] = str(recipient).strip()
                        msg['Subject'] = subject
                        msg.attach(MIMEText(body, 'plain'))
                        
                        server.send_message(msg)
                        success_count += 1
                    except Exception as e:
                        st.error(f"Failed to send to {recipient}: {e}")
                    
                    progress_bar.progress((i + 1) / len(emails))
                    status_text.text(f"Sent {i+1} of {len(emails)}...")
                    time.sleep(1)
                    
                server.quit()
                st.success(f"✅ Successfully sent {success_count} emails!")
                
            except Exception as e:
                st.error(f"Failed to connect or authenticate: {e}. Check your App Password.")