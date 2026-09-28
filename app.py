import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import os
from supabase import create_client, Client

# --- 1. COMMERCIAL UI CONFIGURATION ---
st.set_page_config(page_title="NexusMail Pro | Bulk Sender", page_icon="🚀", layout="wide")

# Premium Custom CSS for a sleek look
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stButton>button {
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. DATABASE CONNECTION (SUPABASE) ---
SUPABASE_URL = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("⚠️ Database connection missing. Check Render Environment Variables.")
    st.stop()

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_connection()

# --- 3. SESSION STATE MANAGEMENT ---
if 'user' not in st.session_state:
    st.session_state.user = None
if 'sender_email' not in st.session_state:
    st.session_state.sender_email = ""
if 'email_app_password' not in st.session_state:
    st.session_state.email_app_password = ""
if 'total_sent' not in st.session_state:
    st.session_state.total_sent = 0

# --- 4. AUTHENTICATION PORTAL (LOGIN/SIGNUP) ---
if not st.session_state.user:
    st.markdown("<h1 style='text-align: center; margin-top: 50px;'>NexusMail Pro 🚀</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Professional Mass Email Marketing Platform</p>", unsafe_allow_html=True)
    st.write("")
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        tab1, tab2 = st.tabs(["🔐 Secure Log In", "✨ Create Free Account"])
        
        with tab1:
            login_email = st.text_input("Email Address", key="log_email")
            login_password = st.text_input("Password", type="password", key="log_pass")
            if st.button("Access Dashboard", type="primary", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": login_email, "password": login_password})
                    st.session_state.user = res.user
                    st.rerun()
                except Exception as e:
                    st.error("Invalid email or password.")
                    
        with tab2:
            st.info("Start your free trial today. No credit card required.")
            reg_email = st.text_input("Email Address", key="reg_email")
            reg_password = st.text_input("Password", type="password", key="reg_pass")
            if st.button("Register Account", type="primary", use_container_width=True):
                try:
                    res = supabase.auth.sign_up({"email": reg_email, "password": reg_password})
                    st.success("✅ Registration successful! You can now log in.")
                except Exception as e:
                    st.error(f"Registration failed: {e}")
    st.stop()

# --- 5. LOGGED-IN SAAS DASHBOARD ---
# Workspace Sidebar Navigation
with st.sidebar:
    st.markdown("### 🏢 Nexus Workspace")
    st.caption(f"User: {st.session_state.user.email}")
    st.divider()
    page = st.radio("Navigation", ["📊 Dashboard", "🚀 Launch Campaign", "⚙️ SMTP Settings"])
    st.divider()
    if st.button("🚪 Log Out", use_container_width=True):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.session_state.sender_email = ""
        st.session_state.email_app_password = ""
        st.rerun()

# ==========================================
# PAGE 1: DASHBOARD
# ==========================================
if page == "📊 Dashboard":
    st.title("Campaign Overview")
    st.markdown("Welcome to your command center.")
    st.write("")
    
    # Pro Metrics Design
    col1, col2, col3 = st.columns(3)
    col1.metric(label="Total Emails Sent (Session)", value=f"{st.session_state.total_sent}")
    col2.metric(label="Active SMTP Connections", value="1" if st.session_state.sender_email else "0")
    col3.metric(label="Current Plan", value="Pro Tier")
    
    st.divider()
    if not st.session_state.sender_email:
        st.warning("⚠️ **Action Required:** You haven't connected an SMTP sending account yet. Go to **⚙️ SMTP Settings** to configure it.")
    else:
        st.success(f"✅ **System Ready.** Connected to SMTP via: `{st.session_state.sender_email}`")

# ==========================================
# PAGE 2: SMTP SETTINGS
# ==========================================
elif page == "⚙️ SMTP Settings":
    st.title("SMTP Configurations")
    st.write("Securely connect your Google Workspace or Gmail account to send campaigns.")
    
    with st.form("smtp_form"):
        st.subheader("Sender Credentials")
        new_email = st.text_input("Sender Email Address", value=st.session_state.sender_email, placeholder="e.g., marketing@yourdomain.com")
        new_password = st.text_input("App Password", type="password", value=st.session_state.email_app_password, help="Must be a 16-character Google App Password.")
        
        submit = st.form_submit_button("Save & Verify Configuration", type="primary")
        if submit:
            if new_email and new_password:
                st.session_state.sender_email = new_email
                st.session_state.email_app_password = new_password
                st.toast('SMTP Credentials Saved!', icon='✅')
            else:
                st.error("Please fill in both fields.")

# ==========================================
# PAGE 3: CAMPAIGN LAUNCHER
# ==========================================
elif page == "🚀 Launch Campaign":
    st.title("Email Campaign Builder")
    
    if not st.session_state.sender_email or not st.session_state.email_app_password:
        st.error("⚠️ Connection Error: Please configure your **SMTP Settings** before launching a campaign.")
        st.stop()
        
    st.subheader("1. Message Details")
    subject = st.text_input("Subject Line", placeholder="e.g., Exclusive Early Access Offer!")
    body = st.text_area("Email Body (Plain Text)", height=200, placeholder="Type your message here...")
    
    st.subheader("2. Target Audience")
    tabs = st.tabs(["📁 Upload Audience List", "✏️ Manual Entry"])
    
    emails = []
    
    with tabs[0]:
        uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"])
        if uploaded_file:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file, header=None)
                else:
                    df = pd.read_excel(uploaded_file, header=None)
                
                emails = df.iloc[:, 0].dropna().astype(str).tolist()
                st.success(f"✅ Audience loaded: {len(emails)} recipients ready.")
                
                with st.expander("👀 Preview Target Audience"):
                    # Uses a professional dataframe instead of simple text list
                    st.dataframe(pd.DataFrame(emails, columns=["Email Address"]), use_container_width=True)
            except Exception as e:
                st.error(f"Failed to process file: {e}")
                
    with tabs[1]:
        manual_emails = st.text_area("Enter emails (comma separated)", placeholder="john@example.com, jane@example.com")
        if manual_emails:
            emails = [e.strip() for e in manual_emails.split(",") if e.strip()]
            st.info(f"Manual mode: {len(emails)} recipients ready.")

    st.divider()
    
    # Action Bar using columns to control button width
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Blast Campaign", type="primary", use_container_width=True):
            if not subject or not body:
                st.toast("Missing subject or body!", icon="❌")
            elif not emails:
                st.toast("No recipients found!", icon="❌")
            else:
                # Modern animated status box
                with st.status("Initializing Mail Servers...", expanded=True) as status:
                    try:
                        st.write("Connecting to Google SMTP relay...")
                        server = smtplib.SMTP("smtp.gmail.com", 587)
                        server.starttls()
                        server.login(st.session_state.sender_email, st.session_state.email_app_password)
                        
                        st.write("✅ Authenticated successfully.")
                        st.write(f"Preparing to blast {len(emails)} emails...")
                        
                        progress_bar = st.progress(0)
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
                                st.session_state.total_sent += 1
                            except Exception as e:
                                st.write(f"❌ Failed to send to {recipient}: {e}")
                            
                            progress_bar.progress((i + 1) / len(emails))
                            time.sleep(1)
                            
                        server.quit()
                        status.update(label=f"Campaign Complete! Sent {success_count} emails.", state="complete", expanded=False)
                        st.balloons() # Triggers celebration animation on success
                        
                    except Exception as e:
                        status.update(label="Campaign Failed", state="error", expanded=True)
                        st.error(f"Critical SMTP Error: {e}. Check your App Password.")