import streamlit as st
import pandas as pd
import numpy as np
import smtplib
import requests
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import os
from supabase import create_client, Client

# ==========================================
# 1. COMMERCIAL UI & CSS SYSTEM
# ==========================================
st.set_page_config(
    page_title="NexusMail Pro | Workspace", 
    page_icon="🚀", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
    .stApp {
        background-color: #F8FAFC;
    }
    [data-testid="stSidebar"] {
        background-color: #0F172A !important;
        border-right: 1px solid #1E293B;
    }
    [data-testid="stSidebar"] * {
        color: #E2E8F0 !important;
    }
    div[role="radiogroup"] > label {
        padding: 10px 14px !important;
        border-radius: 8px !important;
        margin-bottom: 4px !important;
        cursor: pointer !important;
        border: 1px solid transparent !important;
        transition: all 0.2s ease-in-out !important;
    }
    div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }
    div[role="radiogroup"] > label:hover {
        background-color: #1E293B !important;
    }
    div[role="radiogroup"] > label:has(input:checked) {
        background-color: #4F46E5 !important;
        border-color: #6366F1 !important;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.35) !important;
    }
    div[role="radiogroup"] > label:has(input:checked) p {
        font-weight: 600 !important;
        color: #FFFFFF !important;
    }
    .nexus-card {
        background-color: #FFFFFF;
        padding: 22px;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02);
        margin-bottom: 16px;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.15s ease-in-out;
        border: 1px solid transparent;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE CONNECTION (SUPABASE)
# ==========================================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("⚠️ Database connection missing. Check Streamlit Secrets or Environment Variables.")
    st.stop()

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_connection()

# ==========================================
# 3. SESSION STATE & ADMIN INITIALIZATION
# ==========================================
ADMIN_EMAIL = "ggaura135@gmail.com"

if 'user' not in st.session_state:
    st.session_state.user = None
if 'nav_page' not in st.session_state:
    st.session_state.nav_page = "📊 Dashboard"
if 'engine_choice' not in st.session_state:
    st.session_state.engine_choice = "Google SMTP"
if 'smtp_email' not in st.session_state:
    st.session_state.smtp_email = ""
if 'smtp_password' not in st.session_state:
    st.session_state.smtp_password = ""
if 'resend_api_key' not in st.session_state:
    st.session_state.resend_api_key = ""
if 'resend_sender' not in st.session_state:
    st.session_state.resend_sender = "onboarding@resend.dev"
if 'total_sent' not in st.session_state:
    st.session_state.total_sent = 0
if 'saved_audience' not in st.session_state:
    st.session_state.saved_audience = []
if 'tier' not in st.session_state:
    st.session_state.tier = "Free"

# Billing Data
if 'payment_status' not in st.session_state:
    st.session_state.payment_status = "Unpaid"
if 'invoice_date' not in st.session_state:
    st.session_state.invoice_date = None
if 'plan_months' not in st.session_state:
    st.session_state.plan_months = 1
if 'checkout_active' not in st.session_state:
    st.session_state.checkout_active = False
if 'qr_generated' not in st.session_state:
    st.session_state.qr_generated = False

def navigate_to(page_name: str):
    st.session_state.nav_page = page_name
    st.session_state.checkout_active = False
    st.rerun()

def is_valid_email(email: str) -> bool:
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))

def fetch_user_data(email: str):
    try:
        res = supabase.table("subscriptions").select("*").eq("email", email).execute()
        if res.data:
            return res.data[0]
        else:
            new_user = {
                "email": email, 
                "tier": "Free", 
                "payment_status": "Unpaid", 
                "invoice_date": None,
                "plan_months": 1
            }
            supabase.table("subscriptions").insert(new_user).execute()
            return new_user
    except Exception as e:
        return {
            "tier": "Free", 
            "payment_status": "Unpaid", 
            "invoice_date": None,
            "plan_months": 1
        }

# ==========================================
# 4. AUTHENTICATION PORTAL (CLIENT ONLY)
# ==========================================
if not st.session_state.user:
    st.markdown("<br><br><h1 style='text-align: center; color: #0F172A;'>NexusMail Pro 🚀</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B; font-size: 16px;'>Enterprise Email Marketing & Outreach Engine</p><br>", unsafe_allow_html=True)
    
    _, col_auth, _ = st.columns([1, 1.2, 1])
    with col_auth:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #0F172A; margin-bottom: 20px;'>🔐 Secure Log In</h3>", unsafe_allow_html=True)
        
        login_username = st.text_input("Username", key="auth_login_username")
        login_pass = st.text_input("Password", type="password", key="auth_login_pass")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Access Command Center", type="primary", use_container_width=True):
            if not login_username or not login_pass:
                st.error("Please enter both Username and Password.")
            else:
                try:
                    # Append proxy domain if not an email (Allows Admin to still use their real email)
                    raw_user = login_username.strip()
                    auth_email = raw_user if "@" in raw_user else f"{raw_user}@nexus.app"
                    
                    res = supabase.auth.sign_in_with_password({"email": auth_email, "password": login_pass})
                    st.session_state.user = res.user
                    
                    # Fetch comprehensive user data including billing
                    u_data = fetch_user_data(res.user.email)
                    st.session_state.tier = u_data.get("tier", "Free")
                    st.session_state.payment_status = u_data.get("payment_status", "Unpaid")
                    st.session_state.invoice_date = u_data.get("invoice_date", None)
                    st.session_state.plan_months = u_data.get("plan_months", 1)
                    st.rerun()
                except Exception as e:
                    st.error("Invalid Username or Password.")
                    
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ==========================================
# 5. WORKSPACE PAGE VIEWS
# ==========================================
def render_dashboard():
    st.markdown("<h2 style='color: #0F172A; margin-bottom: 2px;'>Welcome back! 👋</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748B; margin-bottom: 24px;'>Here is an overview of your outreach engines and recent performance.</p>", unsafe_allow_html=True)
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(f"""
        <div class="nexus-card">
            <span style='color:#64748B; font-size:13px; font-weight:600;'>Total Emails Sent</span>
            <h2 style='margin:8px 0; color:#0F172A; font-size:32px;'>{st.session_state.total_sent}</h2>
            <span style='color:#10B981; font-size:12px; font-weight:600;'>↑ Live Counter</span>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi2:
        if st.session_state.engine_choice == "Google SMTP":
            is_active = bool(st.session_state.smtp_email and st.session_state.smtp_password)
            txt = "SMTP Connected" if is_active else "SMTP Offline"
        else:
            is_active = bool(st.session_state.resend_api_key)
            txt = "API Connected" if is_active else "API Offline"
            
        color = "#10B981" if is_active else "#EF4444"
        
        st.markdown(f"""
        <div class="nexus-card">
            <span style='color:#64748B; font-size:13px; font-weight:600;'>Current Engine</span>
            <h2 style='margin:8px 0; color:#0F172A; font-size:24px;'>{st.session_state.engine_choice}</h2>
            <span style='color:{color}; font-size:12px; font-weight:600;'>• {txt}</span>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi3:
        st.markdown(f"""
        <div class="nexus-card">
            <span style='color:#64748B; font-size:13px; font-weight:600;'>Audience Loaded</span>
            <h2 style='margin:8px 0; color:#0F172A; font-size:32px;'>{len(st.session_state.saved_audience)}</h2>
            <span style='color:#4F46E5; font-size:12px; font-weight:600;'>Contacts Ready</span>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi4:
        tier_colors = {"Free": "#64748B", "Plus": "#06B6D4", "Pro": "#4F46E5"}
        t_color = tier_colors.get(st.session_state.tier, "#0F172A")
        
        st.markdown(f"""
        <div class="nexus-card">
            <span style='color:#64748B; font-size:13px; font-weight:600;'>Account Status</span>
            <h2 style='margin:8px 0; color:{t_color}; font-size:32px;'>{st.session_state.tier} Tier</h2>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.tier != "Pro":
            if st.button("Manage Subscription →", key="btn_kpi_upgrade", use_container_width=True):
                navigate_to("💎 Upgrade Plan")

    col_chart, col_recent = st.columns([1.8, 1.2])
    with col_chart:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.markdown("<h4 style='color:#0F172A; margin:0;'>Delivery Volume</h4>", unsafe_allow_html=True)
        chart_data = pd.DataFrame(np.random.randint(250, 1400, size=(8, 3)), columns=['Sent', 'Delivered', 'Opened'])
        st.area_chart(chart_data, height=260, color=["#4F46E5", "#06B6D4", "#10B981"])
        st.markdown('</div>', unsafe_allow_html=True)

    with col_recent:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.markdown("<h4 style='color:#0F172A; margin-bottom:12px;'>Quick Actions</h4>", unsafe_allow_html=True)
        if st.button("🚀 Launch Campaign", type="primary", use_container_width=True):
            navigate_to("🚀 Campaigns")
        if st.button("⚙️ Configure Relay Engine", use_container_width=True):
            navigate_to("⚙️ Relay Settings")
        if st.button("👥 Manage Contact Lists", use_container_width=True):
            navigate_to("👥 Contact Lists")
        st.markdown('</div>', unsafe_allow_html=True)

def render_campaign_launcher():
    st.markdown("<h2 style='color:#0F172A;'>Email Campaign Engine</h2>", unsafe_allow_html=True)
    
    if st.session_state.tier == "Free":
        st.error("🔒 **Upgrade Required:** Mass email launching is restricted on the Free Tier.")
        st.info("Please go to **💎 Upgrade Plan** in the sidebar to activate your Plus or Pro subscription.")
        st.stop()

    engine = st.session_state.engine_choice
    if engine == "Google SMTP":
        if not st.session_state.smtp_email or not st.session_state.smtp_password:
            st.warning("⚠️ **SMTP Credentials Missing:** Configure your Gmail relay before dispatching.")
            if st.button("Configure Settings Now →"):
                navigate_to("⚙️ Relay Settings")
            return
    else:
        if not st.session_state.resend_api_key:
            st.warning("⚠️ **API Key Missing:** Configure your Resend HTTP API before dispatching.")
            if st.button("Configure Settings Now →"):
                navigate_to("⚙️️ Relay Settings")
            return

    col_editor, col_target = st.columns([1.5, 1.0])
    
    with col_editor:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.subheader("1. Message Content")
        subject = st.text_input("Subject Line", placeholder="e.g., Exclusive Opportunity & Update", key="campaign_subject")
        body = st.text_area("Email Body (Plain Text or HTML compatible)", height=320, placeholder="Write your email body here...", key="campaign_body")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_target:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.subheader("2. Target Audience")
        src_tab1, src_tab2 = st.tabs(["📁 File Import", "✏️ Direct Entry"])
        active_recipients = []
        
        with src_tab1:
            uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])
            if uploaded_file:
                try:
                    df = pd.read_csv(uploaded_file, header=None) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file, header=None)
                    active_recipients = [e.strip() for e in df.iloc[:, 0].dropna().astype(str) if is_valid_email(e.strip())]
                    st.success(f"✅ {len(active_recipients)} valid recipients found.")
                except Exception as e:
                    st.error(f"Error parsing file: {e}")
            elif st.session_state.saved_audience:
                active_recipients = st.session_state.saved_audience
                st.info(f"Loaded {len(active_recipients)} contacts from Contact Lists.")
                
        with src_tab2:
            manual_input = st.text_area("Comma or Newline separated emails", height=140)
            if manual_input:
                manual_parsed = [e.strip() for e in re.split(r'[,\n]+', manual_input) if is_valid_email(e.strip())]
                if manual_parsed:
                    active_recipients = manual_parsed
                    st.success(f"✅ {len(active_recipients)} valid recipients entered.")
        
        if active_recipients:
            with st.expander("👀 View Recipients List"):
                st.dataframe(pd.DataFrame(active_recipients, columns=["Email Address"]), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
    _, c_btn2, _ = st.columns([1, 1.5, 1])
    
    with c_btn2:
        btn_label = f"🚀 Execute Dispatch via {engine}"
        if st.button(btn_label, type="primary", use_container_width=True):
            if not subject.strip() or not body.strip():
                st.error("Please supply both a subject line and email body.")
            elif not active_recipients:
                st.error("No valid recipient email addresses detected.")
            else:
                with st.status(f"Establishing {engine} Relay...", expanded=True) as status_box:
                    if engine == "Google SMTP":
                        try:
                            st.write("Connecting to `smtp.gmail.com:587`...")
                            server = smtplib.SMTP("smtp.gmail.com", 587, timeout=20)
                            server.starttls()
                            server.login(st.session_state.smtp_email, st.session_state.smtp_password)
                            st.write("✅ Authentication verified. Commencing transmissions...")
                            
                            p_bar = st.progress(0)
                            dispatched = 0
                            
                            for idx, to_address in enumerate(active_recipients):
                                try:
                                    msg = MIMEMultipart()
                                    msg['From'] = st.session_state.smtp_email
                                    msg['To'] = to_address
                                    msg['Subject'] = subject
                                    msg.attach(MIMEText(body, 'plain'))
                                    
                                    server.send_message(msg)
                                    dispatched += 1
                                    st.session_state.total_sent += 1
                                except Exception as send_err:
                                    st.write(f"⚠️ Delivery failure for `{to_address}`: {send_err}")
                                    
                                p_bar.progress((idx + 1) / len(active_recipients))
                                time.sleep(0.5) 
                                
                            server.quit()
                            status_box.update(label=f"SMTP Campaign Dispatched! Delivered {dispatched} emails.", state="complete", expanded=False)
                            st.balloons()
                        except Exception as fatal_err:
                            status_box.update(label="Campaign Terminated Abruptly", state="error", expanded=True)
                            st.error(f"Critical SMTP Error: {fatal_err}. If on Render Free Tier, this port is blocked. Switch to Resend API in Relay Settings.")
                    elif engine == "Resend API":
                        try:
                            st.write("Connecting securely via HTTPS (Port 443)...")
                            headers = {
                                "Authorization": f"Bearer {st.session_state.resend_api_key}",
                                "Content-Type": "application/json"
                            }
                            st.write("✅ API configuration loaded. Commencing transmissions...")
                            
                            p_bar = st.progress(0)
                            dispatched = 0
                            
                            for idx, to_address in enumerate(active_recipients):
                                payload = {
                                    "from": st.session_state.resend_sender,
                                    "to": [to_address],
                                    "subject": subject,
                                    "text": body
                                }
                                
                                response = requests.post("https://api.resend.com/emails", json=payload, headers=headers)
                                
                                if response.status_code == 200:
                                    dispatched += 1
                                    st.session_state.total_sent += 1
                                else:
                                    st.write(f"⚠️ Failed for `{to_address}`: {response.text}")
                                    
                                p_bar.progress((idx + 1) / len(active_recipients))
                                time.sleep(0.3) 
                                
                            status_box.update(label=f"API Campaign Dispatched! Delivered {dispatched} emails.", state="complete", expanded=False)
                            st.balloons()
                        except Exception as fatal_err:
                            status_box.update(label="Campaign Terminated Abruptly", state="error", expanded=True)
                            st.error(f"Critical API Error: {fatal_err}")
    st.markdown('</div>', unsafe_allow_html=True)

def render_contact_lists():
    st.markdown("<h2 style='color:#0F172A;'>Audience & Contact Lists</h2>", unsafe_allow_html=True)
    col_left, col_right = st.columns([1.2, 1.8])
    with col_left:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.subheader("Upload or Paste Contacts")
        up_file = st.file_uploader("Upload CSV / Excel File", type=["csv", "xlsx"])
        pasted = st.text_area("Or Paste Raw Addresses", height=160)
        
        if st.button("Save to Working Audience", type="primary", use_container_width=True):
            collected = []
            if up_file:
                df = pd.read_csv(up_file, header=None) if up_file.name.endswith('.csv') else pd.read_excel(up_file, header=None)
                collected.extend([str(x).strip() for x in df.iloc[:, 0].dropna() if is_valid_email(str(x).strip())])
            if pasted:
                collected.extend([x.strip() for x in re.split(r'[,\n]+', pasted) if is_valid_email(x.strip())])
            
            deduped = list(dict.fromkeys(collected))
            if deduped:
                st.session_state.saved_audience = deduped
                st.success(f"✅ Saved {len(deduped)} verified contacts!")
            else:
                st.warning("No valid email addresses found.")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_right:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.subheader("Active Contact Segment")
        if st.session_state.saved_audience:
            st.dataframe(pd.DataFrame(st.session_state.saved_audience, columns=["Email Address"]), use_container_width=True, height=280)
            if st.button("Clear Saved List", use_container_width=True):
                st.session_state.saved_audience = []
                st.rerun()
        else:
            st.info("No contacts stored. Upload to begin.")
        st.markdown('</div>', unsafe_allow_html=True)

def render_relay_settings():
    st.markdown("<h2 style='color:#0F172A;'>Relay Configurations</h2>", unsafe_allow_html=True)
    
    col_form, col_instructions = st.columns([1.3, 1.2])
    with col_form:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.subheader("Select Delivery Engine")
        
        engine = st.radio(
            "Choose your outbound mail processor:",
            ["Google SMTP", "Resend API"],
            index=0 if st.session_state.engine_choice == "Google SMTP" else 1
        )
        st.session_state.engine_choice = engine
        st.divider()
        
        with st.form("relay_config_form"):
            if engine == "Google SMTP":
                st.markdown("**Google Workspace / Gmail Credentials**")
                in_email = st.text_input("Sender Email Address", value=st.session_state.smtp_email, placeholder="marketing@gmail.com")
                in_password = st.text_input("Google 16-character App Password", value=st.session_state.smtp_password, type="password")
            else:
                st.markdown("**Resend HTTP API Credentials**")
                in_email = st.text_input("Verified Sender Email", value=st.session_state.resend_sender, help="Use onboarding@resend.dev for free testing.")
                in_password = st.text_input("Resend API Key", value=st.session_state.resend_api_key, type="password", placeholder="re_123456...")
            
            if st.form_submit_button("Save Configuration", type="primary", use_container_width=True):
                if engine == "Google SMTP":
                    if in_email and in_password:
                        st.session_state.smtp_email = in_email.strip()
                        st.session_state.smtp_password = in_password.strip().replace(" ", "")
                        st.success("✅ SMTP credentials saved successfully.")
                    else:
                        st.error("Both fields are required.")
                else:
                    if in_email and in_password:
                        st.session_state.resend_sender = in_email.strip()
                        st.session_state.resend_api_key = in_password.strip()
                        st.success("✅ API credentials saved successfully.")
                    else:
                        st.error("Both fields are required.")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_instructions:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.subheader("Engine Differences Explained")
        st.markdown("""
        **Google SMTP (Port 587)**
        * Best for local development and premium hosting.
        * Uses your actual Gmail outbox.
        * *Note:* Blocked by default on Render's Free Tier.
        
        **Resend API (Port 443)**
        * Best for cloud deployment (works perfectly on Render Free).
        * Uses highly secure HTTP infrastructure.
        * Requires a free API key from Resend.com.
        """)
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 6. INVOICING & CHECKOUT SYSTEM
# ==========================================
def render_upgrade_page():
    st.markdown("<h2 style='color:#0F172A;'>Membership & Billing</h2>", unsafe_allow_html=True)
    
    # STATE 1: ALREADY PRO (Show Invoice)
    if st.session_state.tier == "Pro" and st.session_state.payment_status == "Approved":
        st.success("✅ Your Workspace is on the Pro Tier. Unlimited sending is unlocked.")
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.subheader("Billing History")
        
        months = st.session_state.plan_months
        if not months: months = 1
        base_price = 549.00 * months
        gst = base_price * 0.18
        total_price = base_price + gst
        
        invoice_date = st.session_state.invoice_date or time.strftime("%d %b %Y")
        disp_username = st.session_state.user.email.replace("@nexus.app", "")
        
        invoice_html = f"""
        <html><body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; max-width: 800px; margin: auto; padding: 40px; border: 1px solid #ddd;">
            <table width="100%"><tr>
                <td><h1 style="color: #4F46E5; margin:0;">NexusMail Pro</h1><p style="margin:0; color:#888;">TAX INVOICE</p></td>
                <td align="right"><b>Date:</b> {invoice_date}<br><b>Invoice #:</b> NM-{int(time.time())}</td>
            </tr></table><hr style="border:0; border-top: 1px solid #ddd; margin: 20px 0;">
            <p><b>Billed To (Username):</b><br>{disp_username}</p>
            <table width="100%" style="margin-top: 30px; border-collapse: collapse;">
                <tr style="background-color: #f8f8f8;"><th align="left" style="padding: 10px; border-bottom: 2px solid #ddd;">Description</th><th align="right" style="padding: 10px; border-bottom: 2px solid #ddd;">Amount</th></tr>
                <tr><td style="padding: 10px; border-bottom: 1px solid #eee;">Pro Tier Subscription ({months} Months)</td><td align="right" style="padding: 10px; border-bottom: 1px solid #eee;">₹{base_price:.2f}</td></tr>
                <tr><td style="padding: 10px; border-bottom: 1px solid #eee;">GST (18%)</td><td align="right" style="padding: 10px; border-bottom: 1px solid #eee;">₹{gst:.2f}</td></tr>
                <tr><th align="left" style="padding: 10px;">Total Paid</th><th align="right" style="padding: 10px; color: #10B981;">₹{total_price:.2f}</th></tr>
            </table><br><br>
            <p style="text-align: center; color: #888; font-size: 12px;">Payment Processed via UPI. Thank you for your business!</p>
        </body></html>
        """
        st.download_button(
            label="📄 Download Professional Invoice", 
            data=invoice_html, 
            file_name=f"NexusMail_Invoice_{invoice_date.replace(' ', '_')}.html", 
            mime="text/html",
            type="primary"
        )
        st.caption("Tip: Open the downloaded file in your browser, press Ctrl+P (or Cmd+P), and select 'Save as PDF'.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # STATE 2: PENDING APPROVAL
    if st.session_state.payment_status == "Pending":
        st.info("⏳ Your payment is currently under review by our Admin team. Your account will be upgraded and your invoice generated shortly.")
        if st.button("Refresh Status"):
            st.rerun()
        return

    # STATE 3: CHECKOUT SCREEN
    if st.session_state.checkout_active:
        _, c_center, _ = st.columns([1, 1.5, 1])
        with c_center:
            st.markdown('<div class="nexus-card" style="text-align: center;">', unsafe_allow_html=True)
            st.subheader("Secure UPI Checkout")
            
            selected_months = st.selectbox("Select Subscription Duration", [1, 3, 6, 12], index=0, format_func=lambda x: f"{x} Month{'s' if x > 1 else ''}")
            calc_base = 549.00 * selected_months
            calc_gst = calc_base * 0.18
            calc_total = calc_base + calc_gst
            
            st.markdown(f"""
            <table width="100%" style="text-align: left; margin-bottom: 20px; margin-top: 20px;">
                <tr><td>Pro Plan ({selected_months} Months)</td><td align="right">₹{calc_base:.2f}</td></tr>
                <tr><td>GST (18%)</td><td align="right">₹{calc_gst:.2f}</td></tr>
                <tr><th><h3 style='margin:0;'>Total Payable</h3></th><th align="right"><h3 style='margin:0; color:#4F46E5;'>₹{calc_total:.2f}</h3></th></tr>
            </table>
            """, unsafe_allow_html=True)
            
            if not st.session_state.qr_generated:
                with st.spinner("Preparing secure checkout..."):
                    time.sleep(2)
                st.session_state.qr_generated = True
                
            try:
                st.image("qr.png", caption=f"Scan to Pay Exact Amount: ₹{calc_total:.2f}", width=250)
            except:
                st.error("⚠️ [Admin Note: Ensure 'qr.png' is uploaded to the root folder]")
                
            st.divider()
            if st.button("✅ I have completed the payment", type="primary", use_container_width=True):
                supabase.table("subscriptions").update({
                    "payment_status": "Pending",
                    "plan_months": selected_months
                }).eq("email", st.session_state.user.email).execute()
                
                st.session_state.payment_status = "Pending"
                st.session_state.plan_months = selected_months
                st.session_state.checkout_active = False
                st.rerun()
                
            if st.button("Cancel & Go Back"):
                st.session_state.checkout_active = False
                st.session_state.qr_generated = False
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        return

    # STATE 4: PRICING SCREEN
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("<div class='nexus-card'><h3>Free Tier</h3><h2>₹0</h2><hr><ul><li>Platform access</li><li>Campaigns locked</li></ul></div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='nexus-card' style='border: 2px solid #06B6D4;'><h3>Plus Tier ⚡</h3><h2 style='color:#06B6D4;'>₹999/mo</h2><hr><ul><li><b>Unlock</b> Campaigns</li><li>Standard Support</li></ul></div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div class='nexus-card' style='border: 2px solid #4F46E5;'><h3>Pro Tier 🚀</h3><h2 style='color:#4F46E5;'>₹549 <span style='font-size:14px; color:#888;'>+ GST</span></h2><hr><ul><li><b>Unlimited</b> Volume</li><li>Invoicing Enabled</li></ul></div>", unsafe_allow_html=True)
        if st.button("💳 Proceed to Checkout", type="primary", use_container_width=True):
            st.session_state.checkout_active = True
            st.rerun()

# ==========================================
# 7. ADMIN CONTROL PANEL (HIDDEN)
# ==========================================
def render_admin_panel():
    st.markdown("<h2 style='color:#EF4444;'>🛡️ Admin Control Panel</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1.5])
    with col1:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.subheader("Action Required: Pending Payments")
        try:
            res = supabase.table("subscriptions").select("*").eq("payment_status", "Pending").execute()
            pending = res.data
            if not pending: 
                st.info("No pending payments.")
            for u in pending:
                requested_months = u.get('plan_months', 1)
                expected_total = (549.00 * requested_months) * 1.18
                display_uname = u['email'].replace("@nexus.app", "")
                
                st.write(f"🧾 **{display_uname}**")
                st.caption(f"Requested: {requested_months} Months | Expected Payment: ₹{expected_total:.2f}")
                
                if st.button(f"✅ Approve & Generate Invoice", key=f"approve_{u['email']}"):
                    today_str = time.strftime("%d %b %Y")
                    supabase.table("subscriptions").update({
                        "tier": "Pro", 
                        "payment_status": "Approved", 
                        "invoice_date": today_str
                    }).eq("email", u['email']).execute()
                    st.success(f"Approved {display_uname}!")
                    time.sleep(1)
                    st.rerun()
        except Exception as e:
            st.error(f"Database error: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # NEW: PROVISION CUSTOMER ACCOUNT
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.subheader("Provision Customer Account")
        st.caption("Create an account for a new customer without logging yourself out.")
        with st.form("admin_create_user"):
            new_username = st.text_input("New Customer Username", placeholder="e.g. johndoe")
            new_password = st.text_input("New Password", type="password")
            
            if st.form_submit_button("Create Account & Provision", type="primary", use_container_width=True):
                if new_username and new_password:
                    target_email = f"{new_username.strip()}@nexus.app"
                    
                    # Direct REST API call to bypass Streamlit session mutation
                    api_url = f"{SUPABASE_URL}/auth/v1/signup"
                    headers = {"apikey": SUPABASE_KEY, "Content-Type": "application/json"}
                    payload = {"email": target_email, "password": new_password}
                    
                    response = requests.post(api_url, headers=headers, json=payload)
                    
                    if response.status_code == 200:
                        st.success(f"✅ Created Account: {new_username}")
                    else:
                        st.error(f"Creation failed: {response.text}")
                else:
                    st.error("Username and Password required.")
        st.markdown('</div>', unsafe_allow_html=True)
                    
    with col2:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.subheader("Subscription Database")
        try:
            res = supabase.table("subscriptions").select("email, tier, payment_status, invoice_date, plan_months").execute()
            df = pd.DataFrame(res.data)
            
            # Clean up emails for display
            if not df.empty:
                df['email'] = df['email'].str.replace("@nexus.app", "")
                df.rename(columns={'email': 'username'}, inplace=True)
            
            st.dataframe(df, use_container_width=True, height=650)
        except Exception as e:
            st.error("Could not fetch users.")
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 8. SIDEBAR & MASTER ROUTING
# ==========================================
with st.sidebar:
    st.markdown("<h3 style='margin-bottom:0;'>🚀 Nexus Workspace</h3>", unsafe_allow_html=True)
    
    tier_colors = {"Free": "#94A3B8", "Plus": "#06B6D4", "Pro": "#4F46E5"}
    active_color = tier_colors.get(st.session_state.tier, "#94A3B8")
    display_name = st.session_state.user.email.replace("@nexus.app", "")
    
    st.markdown(f"""
    <div style='background-color:#1E293B; padding:10px 12px; border-radius:8px; margin:14px 0 20px 0; border:1px solid #334155;'>
        <div style='font-size:11px; color:#94A3B8; text-transform:uppercase; font-weight:600;'>Active Workspace</div>
        <div style='font-weight:600; font-size:13px; color:#F8FAFC; word-break:break-all;'>{display_name}</div>
        <div style='margin-top:6px;'><span style='background:{active_color}; color:white; font-size:10px; font-weight:700; padding:2px 8px; border-radius:10px;'>{st.session_state.tier.upper()} PLAN</span></div>
    </div>
    """, unsafe_allow_html=True)
    
    PAGES = ["📊 Dashboard", "🚀 Campaigns", "👥 Contact Lists", "⚙️ Relay Settings", "💎 Upgrade Plan"]
    
    if st.session_state.user.email == ADMIN_EMAIL:
        PAGES.append("🛡️ Admin Panel")
        
    current_idx = PAGES.index(st.session_state.nav_page) if st.session_state.nav_page in PAGES else 0
    
    selected_page = st.radio("Navigation", PAGES, index=current_idx, label_visibility="collapsed")
    
    if selected_page != st.session_state.nav_page:
        navigate_to(selected_page)
        
    st.divider()
    if st.button("🚪 Log Out", use_container_width=True):
        supabase.auth.sign_out()
        st.session_state.clear()
        st.rerun()

# Execute Active Route
if st.session_state.nav_page == "📊 Dashboard":
    render_dashboard()
elif st.session_state.nav_page == "🚀 Campaigns":
    render_campaign_launcher()
elif st.session_state.nav_page == "👥 Contact Lists":
    render_contact_lists()
elif st.session_state.nav_page == "⚙️ Relay Settings":
    render_relay_settings()
elif st.session_state.nav_page == "💎 Upgrade Plan":
    render_upgrade_page()
elif st.session_state.nav_page == "🛡️ Admin Panel":
    render_admin_panel()