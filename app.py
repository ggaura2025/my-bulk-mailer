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
from datetime import datetime, timedelta
from supabase import create_client, Client

# ==========================================
# 1. PREMIUM ENTERPRISE UI & CSS SYSTEM
# ==========================================
st.set_page_config(
    page_title="NexusMail Pro | Workspace", 
    page_icon="🚀", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 1400px !important;
    }
    
    .stApp {
        background-color: #F4F7F9;
        background-image: radial-gradient(at 0% 0%, hsla(253,16%,7%,0.02) 0, transparent 50%), 
                          radial-gradient(at 50% 0%, hsla(225,39%,30%,0.02) 0, transparent 50%);
    }
    
    /* Sleek Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0B1121 !important;
        border-right: 1px solid #1E293B;
    }
    [data-testid="stSidebar"] * {
        color: #E2E8F0 !important;
    }
    
    /* Premium Cards */
    .nexus-card {
        background-color: #FFFFFF;
        padding: 28px;
        border-radius: 16px;
        border: 1px solid rgba(226, 232, 240, 0.8);
        border-top: 4px solid #4F46E5;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .nexus-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 15px 35px -10px rgba(0, 0, 0, 0.08);
    }
    
    /* Gradient Primary Buttons */
    button[kind="primary"] {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%) !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        padding: 0.5rem 1rem !important;
        box-shadow: 0 4px 15px rgba(79, 70, 229, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(79, 70, 229, 0.45) !important;
    }
    
    /* Secondary Buttons */
    button[kind="secondary"] {
        border-radius: 10px !important;
        font-weight: 500 !important;
        border: 1px solid #E2E8F0 !important;
        transition: all 0.2s ease !important;
    }
    button[kind="secondary"]:hover {
        border-color: #4F46E5 !important;
        color: #4F46E5 !important;
    }

    /* Radio Button Pills */
    div[role="radiogroup"] > label {
        padding: 12px 18px !important;
        border-radius: 10px !important;
        margin-bottom: 6px !important;
        cursor: pointer !important;
        background-color: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
        transition: all 0.2s ease-in-out !important;
    }
    div[role="radiogroup"] > label > div:first-child { display: none !important; }
    div[role="radiogroup"] > label:hover { border-color: #CBD5E1 !important; }
    div[role="radiogroup"] > label:has(input:checked) {
        background-color: #EEF2FF !important;
        border-color: #6366F1 !important;
    }
    div[role="radiogroup"] > label:has(input:checked) p {
        font-weight: 600 !important;
        color: #4F46E5 !important;
    }
    
    /* Typography */
    h1, h2, h3, h4 {
        color: #0F172A !important;
        letter-spacing: -0.02em;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE CONNECTION (SUPABASE)
# ==========================================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("⚠️ Database connection missing. Check Streamlit Secrets.")
    st.stop()

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_connection()

# ==========================================
# 3. SESSION STATE INITIALIZATION
# ==========================================
ADMIN_EMAIL = "ggaura135@gmail.com"

if 'user' not in st.session_state: st.session_state.user = None
if 'nav_page' not in st.session_state: st.session_state.nav_page = "📊 Dashboard"
if 'engine_choice' not in st.session_state: st.session_state.engine_choice = "Google SMTP"
if 'smtp_email' not in st.session_state: st.session_state.smtp_email = ""
if 'smtp_password' not in st.session_state: st.session_state.smtp_password = ""
if 'resend_api_key' not in st.session_state: st.session_state.resend_api_key = ""
if 'resend_sender' not in st.session_state: st.session_state.resend_sender = "onboarding@resend.dev"
if 'total_sent' not in st.session_state: st.session_state.total_sent = 0
if 'saved_audience' not in st.session_state: st.session_state.saved_audience = []
if 'tier' not in st.session_state: st.session_state.tier = "Free"

# Billing Data
if 'payment_status' not in st.session_state: st.session_state.payment_status = "Unpaid"
if 'invoice_date' not in st.session_state: st.session_state.invoice_date = None
if 'plan_months' not in st.session_state: st.session_state.plan_months = 1
if 'checkout_active' not in st.session_state: st.session_state.checkout_active = False
if 'qr_generated' not in st.session_state: st.session_state.qr_generated = False

def navigate_to(page_name: str):
    st.session_state.nav_page = page_name
    st.session_state.checkout_active = False
    st.rerun()

def is_valid_email(email: str) -> bool:
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))

def fetch_user_data(email: str):
    """Fetches user data and automatically processes Subscription Expiry."""
    try:
        res = supabase.table("subscriptions").select("*").eq("email", email).execute()
        if res.data:
            u_data = res.data[0]
            
            # --- AUTO EXPIRATION LOGIC ---
            if u_data.get("tier") in ["Plus", "Pro"] and u_data.get("invoice_date"):
                try:
                    inv_date = datetime.strptime(u_data["invoice_date"], "%d %b %Y")
                    months_paid = u_data.get("plan_months", 1)
                    expiry_date = inv_date + timedelta(days=30 * months_paid)
                    
                    if datetime.now() > expiry_date:
                        # Auto-Downgrade in Database
                        supabase.table("subscriptions").update({
                            "tier": "Free", 
                            "payment_status": "Expired"
                        }).eq("email", email).execute()
                        u_data["tier"] = "Free"
                        u_data["payment_status"] = "Expired"
                except Exception:
                    pass # Fail silently if date parsing has an issue
                    
            return u_data
        else:
            new_user = {"email": email, "tier": "Free", "payment_status": "Unpaid", "invoice_date": None, "plan_months": 1}
            supabase.table("subscriptions").insert(new_user).execute()
            return new_user
    except Exception:
        return {"tier": "Free", "payment_status": "Unpaid", "invoice_date": None, "plan_months": 1}

# ==========================================
# 4. AUTHENTICATION PORTAL (CLIENT ONLY)
# ==========================================
if not st.session_state.user:
    st.markdown("<br><br><h1 style='text-align: center; color: #0F172A; font-weight: 700; font-size: 42px;'>NexusMail Pro 🚀</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B; font-size: 18px; margin-bottom: 40px;'>Enterprise Email Marketing & Outreach Engine</p>", unsafe_allow_html=True)
    
    _, col_auth, _ = st.columns([1, 1.2, 1])
    with col_auth:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #0F172A; margin-bottom: 25px;'>🔐 Secure Portal Access</h3>", unsafe_allow_html=True)
        
        login_username = st.text_input("Username", key="auth_login_username", placeholder="Enter your assigned username")
        login_pass = st.text_input("Password", type="password", key="auth_login_pass", placeholder="••••••••")
        
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
                    
                    # Fetch data & trigger auto-expiry check
                    u_data = fetch_user_data(res.user.email)
                    st.session_state.tier = u_data.get("tier", "Free")
                    st.session_state.payment_status = u_data.get("payment_status", "Unpaid")
                    st.session_state.invoice_date = u_data.get("invoice_date", None)
                    st.session_state.plan_months = u_data.get("plan_months", 1)
                    st.rerun()
                except Exception:
                    st.error("Invalid Username or Password.")
                    
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ==========================================
# 5. WORKSPACE PAGE VIEWS
# ==========================================
def render_dashboard():
    st.markdown("<h2 style='margin-bottom: 2px;'>Welcome back! 👋</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748B; margin-bottom: 24px; font-size: 16px;'>Here is an overview of your outreach engines and recent performance.</p>", unsafe_allow_html=True)
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(f"""
        <div class="nexus-card" style="border-top-color: #10B981;">
            <span style='color:#64748B; font-size:13px; font-weight:600; text-transform: uppercase;'>Total Emails Sent</span>
            <h2 style='margin:10px 0; color:#0F172A; font-size:38px;'>{st.session_state.total_sent}</h2>
            <span style='color:#10B981; font-size:13px; font-weight:600;'>↑ Live Counter</span>
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
        <div class="nexus-card" style="border-top-color: {color};">
            <span style='color:#64748B; font-size:13px; font-weight:600; text-transform: uppercase;'>Current Engine</span>
            <h2 style='margin:10px 0; color:#0F172A; font-size:26px;'>{st.session_state.engine_choice}</h2>
            <span style='color:{color}; font-size:13px; font-weight:600;'>• {txt}</span>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi3:
        st.markdown(f"""
        <div class="nexus-card" style="border-top-color: #F59E0B;">
            <span style='color:#64748B; font-size:13px; font-weight:600; text-transform: uppercase;'>Audience Loaded</span>
            <h2 style='margin:10px 0; color:#0F172A; font-size:38px;'>{len(st.session_state.saved_audience)}</h2>
            <span style='color:#F59E0B; font-size:13px; font-weight:600;'>Contacts Ready</span>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi4:
        tier_colors = {"Free": "#94A3B8", "Plus": "#06B6D4", "Pro": "#4F46E5"}
        t_color = tier_colors.get(st.session_state.tier, "#0F172A")
        
        st.markdown(f"""
        <div class="nexus-card" style="border-top-color: {t_color};">
            <span style='color:#64748B; font-size:13px; font-weight:600; text-transform: uppercase;'>Account Status</span>
            <h2 style='margin:10px 0; color:{t_color}; font-size:36px;'>{st.session_state.tier}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.tier != "Pro":
            if st.button("Upgrade Workspace →", type="primary", use_container_width=True):
                navigate_to("💎 Upgrade Plan")

    col_chart, col_recent = st.columns([1.8, 1.2])
    with col_chart:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.markdown("<h4 style='margin:0 0 15px 0;'>Delivery Volume Analytics</h4>", unsafe_allow_html=True)
        chart_data = pd.DataFrame(np.random.randint(250, 1400, size=(8, 3)), columns=['Sent', 'Delivered', 'Opened'])
        st.area_chart(chart_data, height=280, color=["#4F46E5", "#06B6D4", "#10B981"])
        st.markdown('</div>', unsafe_allow_html=True)

    with col_recent:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.markdown("<h4 style='margin-bottom:15px;'>Quick Actions</h4>", unsafe_allow_html=True)
        if st.button("🚀 Launch Campaign", type="primary", use_container_width=True): navigate_to("🚀 Campaigns")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⚙️ Configure Relay Engine", use_container_width=True): navigate_to("⚙️ Relay Settings")
        if st.button("👥 Manage Contact Lists", use_container_width=True): navigate_to("👥 Contact Lists")
        st.markdown('</div>', unsafe_allow_html=True)

def render_campaign_launcher():
    st.markdown("<h2>Email Campaign Engine</h2>", unsafe_allow_html=True)
    
    if st.session_state.tier == "Free":
        st.error("🔒 **Workspace Locked:** Mass email launching is restricted on the Free Tier.")
        st.info("Your subscription may have expired, or you have not upgraded yet. Please go to **💎 Upgrade Plan** to activate.")
        st.stop()

    engine = st.session_state.engine_choice
    if engine == "Google SMTP":
        if not st.session_state.smtp_email or not st.session_state.smtp_password:
            st.warning("⚠️ **SMTP Credentials Missing:** Configure your Gmail relay before dispatching.")
            if st.button("Configure Settings Now →"): navigate_to("⚙️ Relay Settings")
            return
    else:
        if not st.session_state.resend_api_key:
            st.warning("⚠️ **API Key Missing:** Configure your Resend HTTP API before dispatching.")
            if st.button("Configure Settings Now →"): navigate_to("⚙️ Relay Settings")
            return

    col_editor, col_target = st.columns([1.5, 1.0])
    
    with col_editor:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.markdown("<h4>1. Message Content</h4>", unsafe_allow_html=True)
        subject = st.text_input("Subject Line", placeholder="e.g., Exclusive Opportunity & Update")
        body = st.text_area("Email Body (Plain Text or HTML compatible)", height=320, placeholder="Write your email body here...")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_target:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.markdown("<h4>2. Target Audience</h4>", unsafe_allow_html=True)
        src_tab1, src_tab2 = st.tabs(["📁 File Import", "✏️ Direct Entry"])
        active_recipients = []
        
        with src_tab1:
            uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])
            if uploaded_file:
                try:
                    df = pd.read_csv(uploaded_file, header=None) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file, header=None)
                    active_recipients = [e.strip() for e in df.iloc[:, 0].dropna().astype(str) if is_valid_email(e.strip())]
                    st.success(f"✅ {len(active_recipients)} valid recipients found.")
                except Exception as e: st.error(f"Error parsing file: {e}")
            elif st.session_state.saved_audience:
                active_recipients = st.session_state.saved_audience
                st.info(f"Loaded {len(active_recipients)} contacts from Workspace Lists.")
                
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
        if st.button(f"🚀 Execute Dispatch via {engine}", type="primary", use_container_width=True):
            if not subject.strip() or not body.strip(): st.error("Please supply both a subject line and email body.")
            elif not active_recipients: st.error("No valid recipient email addresses detected.")
            else:
                with st.status(f"Establishing Secure {engine} Relay...", expanded=True) as status_box:
                    if engine == "Google SMTP":
                        try:
                            server = smtplib.SMTP("smtp.gmail.com", 587, timeout=20)
                            server.starttls()
                            server.login(st.session_state.smtp_email, st.session_state.smtp_password)
                            
                            p_bar = st.progress(0)
                            dispatched = 0
                            for idx, to_address in enumerate(active_recipients):
                                try:
                                    msg = MIMEMultipart()
                                    msg['From'], msg['To'], msg['Subject'] = st.session_state.smtp_email, to_address, subject
                                    msg.attach(MIMEText(body, 'plain'))
                                    server.send_message(msg)
                                    dispatched += 1
                                    st.session_state.total_sent += 1
                                except Exception as send_err: st.write(f"⚠️ Delivery failure for `{to_address}`: {send_err}")
                                p_bar.progress((idx + 1) / len(active_recipients))
                                time.sleep(0.5) 
                            server.quit()
                            status_box.update(label=f"SMTP Campaign Dispatched! Delivered {dispatched} emails.", state="complete", expanded=False)
                            st.balloons()
                        except Exception as fatal_err:
                            status_box.update(label="Campaign Terminated Abruptly", state="error", expanded=True)
                            st.error(f"Critical SMTP Error: {fatal_err}. If on Render Free Tier, this port is blocked. Switch to Resend API.")
                    elif engine == "Resend API":
                        try:
                            headers = {"Authorization": f"Bearer {st.session_state.resend_api_key}", "Content-Type": "application/json"}
                            p_bar = st.progress(0)
                            dispatched = 0
                            for idx, to_address in enumerate(active_recipients):
                                payload = {"from": st.session_state.resend_sender, "to": [to_address], "subject": subject, "text": body}
                                response = requests.post("https://api.resend.com/emails", json=payload, headers=headers)
                                if response.status_code == 200:
                                    dispatched += 1
                                    st.session_state.total_sent += 1
                                else: st.write(f"⚠️ Failed for `{to_address}`: {response.text}")
                                p_bar.progress((idx + 1) / len(active_recipients))
                                time.sleep(0.3) 
                            status_box.update(label=f"API Campaign Dispatched! Delivered {dispatched} emails.", state="complete", expanded=False)
                            st.balloons()
                        except Exception as fatal_err:
                            status_box.update(label="Campaign Terminated Abruptly", state="error", expanded=True)
                            st.error(f"Critical API Error: {fatal_err}")
    st.markdown('</div>', unsafe_allow_html=True)

def render_contact_lists():
    st.markdown("<h2>Audience & Contact Lists</h2>", unsafe_allow_html=True)
    col_left, col_right = st.columns([1.2, 1.8])
    with col_left:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.markdown("<h4>Upload or Paste Contacts</h4>", unsafe_allow_html=True)
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
            else: st.warning("No valid email addresses found.")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_right:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.markdown("<h4>Active Contact Segment</h4>", unsafe_allow_html=True)
        if st.session_state.saved_audience:
            st.dataframe(pd.DataFrame(st.session_state.saved_audience, columns=["Email Address"]), use_container_width=True, height=280)
            if st.button("Clear Saved List", use_container_width=True):
                st.session_state.saved_audience = []
                st.rerun()
        else: st.info("No contacts stored. Upload to begin.")
        st.markdown('</div>', unsafe_allow_html=True)

def render_relay_settings():
    st.markdown("<h2>Relay Configurations</h2>", unsafe_allow_html=True)
    
    col_form, col_instructions = st.columns([1.3, 1.2])
    with col_form:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.markdown("<h4>Select Delivery Engine</h4>", unsafe_allow_html=True)
        
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
                in_email = st.text_input("Verified Sender Email", value=st.session_state.resend_sender)
                in_password = st.text_input("Resend API Key", value=st.session_state.resend_api_key, type="password")
            
            if st.form_submit_button("Save Engine Configuration", type="primary", use_container_width=True):
                if engine == "Google SMTP":
                    if in_email and in_password:
                        st.session_state.smtp_email = in_email.strip()
                        st.session_state.smtp_password = in_password.strip().replace(" ", "")
                        st.success("✅ SMTP credentials saved.")
                    else: st.error("Both fields are required.")
                else:
                    if in_email and in_password:
                        st.session_state.resend_sender = in_email.strip()
                        st.session_state.resend_api_key = in_password.strip()
                        st.success("✅ API credentials saved.")
                    else: st.error("Both fields are required.")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_instructions:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.markdown("<h4>Engine Architecture</h4>", unsafe_allow_html=True)
        st.markdown("""
        **Google SMTP (Port 587)**
        * Best for premium hosting (Streamlit Cloud).
        * Relays directly through your authentic Google outbox.
        * Ensures maximum deliverability.
        
        <hr>
        
        **Resend HTTP API (Port 443)**
        * Best for firewalled servers (Render Free).
        * Uses highly secure REST endpoints.
        * Requires verified domain integration.
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 6. INVOICING & CHECKOUT SYSTEM
# ==========================================
def render_upgrade_page():
    st.markdown("<h2>Membership & Billing</h2>", unsafe_allow_html=True)
    
    # STATE 1: ALREADY PRO (Show Invoice)
    if st.session_state.tier in ["Plus", "Pro"] and st.session_state.payment_status == "Approved":
        st.success("✅ Your Workspace is actively upgraded. Unlimited features are unlocked.")
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.markdown("<h4>Current Billing Cycle</h4>", unsafe_allow_html=True)
        
        months = st.session_state.plan_months or 1
        base_price = 549.00 * months
        gst = base_price * 0.18
        total_price = base_price + gst
        
        invoice_date = st.session_state.invoice_date or time.strftime("%d %b %Y")
        disp_username = st.session_state.user.email.replace("@nexus.app", "")
        
        try:
            inv_dt = datetime.strptime(invoice_date, "%d %b %Y")
            exp_dt = inv_dt + timedelta(days=30 * months)
            expiry_str = exp_dt.strftime("%d %b %Y")
            st.info(f"🗓️ Your subscription is active until **{expiry_str}**.")
        except: pass
        
        invoice_html = f"""
        <html><body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; max-width: 800px; margin: auto; padding: 40px; border: 1px solid #ddd; border-radius: 12px;">
            <table width="100%"><tr>
                <td><h1 style="color: #4F46E5; margin:0;">NexusMail Pro</h1><p style="margin:0; color:#888;">TAX INVOICE</p></td>
                <td align="right"><b>Date:</b> {invoice_date}<br><b>Invoice #:</b> NM-{int(time.time())}</td>
            </tr></table><hr style="border:0; border-top: 1px solid #ddd; margin: 20px 0;">
            <p><b>Billed To (Username):</b><br>{disp_username}</p>
            <table width="100%" style="margin-top: 30px; border-collapse: collapse;">
                <tr style="background-color: #f8f8f8;"><th align="left" style="padding: 10px; border-bottom: 2px solid #ddd;">Description</th><th align="right" style="padding: 10px; border-bottom: 2px solid #ddd;">Amount</th></tr>
                <tr><td style="padding: 10px; border-bottom: 1px solid #eee;">Pro Tier Subscription ({months} Months)</td><td align="right" style="padding: 10px; border-bottom: 1px solid #eee;">₹{base_price:.2f}</td></tr>
                <tr><td style="padding: 10px; border-bottom: 1px solid #eee;">GST (18%)</td><td align="right" style="padding: 10px; border-bottom: 1px solid #eee;">₹{gst:.2f}</td></tr>
                <tr><th align="left" style="padding: 10px; font-size: 18px;">Total Paid</th><th align="right" style="padding: 10px; color: #10B981; font-size: 18px;">₹{total_price:.2f}</th></tr>
            </table><br><br>
            <p style="text-align: center; color: #888; font-size: 12px; margin-top: 40px;">Payment Processed Securely. Thank you for your business!</p>
        </body></html>
        """
        st.download_button(
            label="📄 Download Professional Tax Invoice", 
            data=invoice_html, 
            file_name=f"NexusMail_Invoice_{invoice_date.replace(' ', '_')}.html", 
            mime="text/html",
            type="primary"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # STATE 2: PENDING APPROVAL
    if st.session_state.payment_status == "Pending":
        st.markdown('<div class="nexus-card" style="text-align: center; padding: 40px;">', unsafe_allow_html=True)
        st.markdown("<h2 style='color:#F59E0B;'>Payment Under Review</h2>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 16px; color: #64748B;'>Your transaction is being verified by our team. Your workspace will unlock momentarily.</p>", unsafe_allow_html=True)
        if st.button("↻ Refresh Account Status", type="primary"):
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # STATE 3: CHECKOUT SCREEN
    if st.session_state.checkout_active:
        _, c_center, _ = st.columns([1, 1.5, 1])
        with c_center:
            st.markdown('<div class="nexus-card" style="text-align: center;">', unsafe_allow_html=True)
            st.markdown("<h3>Secure Checkout Portal</h3>", unsafe_allow_html=True)
            
            selected_months = st.selectbox("Select Subscription Duration", [1, 3, 6, 12], index=0, format_func=lambda x: f"{x} Month{'s' if x > 1 else ''} Plan")
            calc_base = 549.00 * selected_months
            calc_gst = calc_base * 0.18
            calc_total = calc_base + calc_gst
            
            st.markdown(f"""
            <div style="background-color: #F8FAFC; border-radius: 12px; padding: 20px; margin: 20px 0;">
                <table width="100%" style="text-align: left; font-size: 15px;">
                    <tr><td style="padding-bottom: 8px;">Pro Plan Base ({selected_months}M)</td><td align="right" style="padding-bottom: 8px;">₹{calc_base:.2f}</td></tr>
                    <tr><td style="padding-bottom: 12px; border-bottom: 1px solid #E2E8F0;">Tax (18% GST)</td><td align="right" style="padding-bottom: 12px; border-bottom: 1px solid #E2E8F0;">₹{calc_gst:.2f}</td></tr>
                    <tr><th style="padding-top: 12px;"><h3 style='margin:0;'>Total</h3></th><th align="right" style="padding-top: 12px;"><h3 style='margin:0; color:#4F46E5;'>₹{calc_total:.2f}</h3></th></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
            
            if not st.session_state.qr_generated:
                with st.spinner("Generating secure transaction..."):
                    time.sleep(1.5)
                st.session_state.qr_generated = True
                
            try:
                st.image("qr.png", caption=f"Scan & Pay Exact Amount: ₹{calc_total:.2f}", width=250)
            except:
                st.error("⚠️ [Admin Error: 'qr.png' missing from repository]")
                
            st.divider()
            if st.button("✅ Confirm Payment Sent", type="primary", use_container_width=True):
                supabase.table("subscriptions").update({
                    "payment_status": "Pending",
                    "plan_months": selected_months
                }).eq("email", st.session_state.user.email).execute()
                
                st.session_state.payment_status = "Pending"
                st.session_state.plan_months = selected_months
                st.session_state.checkout_active = False
                st.rerun()
                
            if st.button("Cancel Order"):
                st.session_state.checkout_active = False
                st.session_state.qr_generated = False
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        return

    # STATE 4: PRICING SCREEN
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("<div class='nexus-card'><h3>Free Tier</h3><h2>₹0</h2><hr><ul><li style='margin-bottom:8px'>Platform access</li><li style='color:#94A3B8'>Campaigns locked</li></ul></div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='nexus-card' style='border-top: 4px solid #06B6D4;'><h3>Plus Tier ⚡</h3><h2 style='color:#06B6D4;'>₹999/mo</h2><hr><ul><li style='margin-bottom:8px'><b>Unlock</b> Campaigns</li><li>Standard Support</li></ul></div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div class='nexus-card' style='border-top: 4px solid #4F46E5; background-color: #F8FAFC;'><h3>Pro Tier 🚀</h3><h2 style='color:#4F46E5;'>₹549 <span style='font-size:14px; color:#888;'>+ GST</span></h2><hr><ul><li style='margin-bottom:8px'><b>Unlimited</b> Volume</li><li>Auto-Invoicing</li></ul></div>", unsafe_allow_html=True)
        if st.button("💳 Proceed to Checkout", type="primary", use_container_width=True):
            st.session_state.checkout_active = True
            st.rerun()

# ==========================================
# 7. ADMIN CONTROL PANEL (HIDDEN)
# ==========================================
def render_admin_panel():
    st.markdown("<h2 style='color:#EF4444;'>🛡️ Command & Control Center</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1.5])
    with col1:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.markdown("<h4>Pending Approvals</h4>", unsafe_allow_html=True)
        try:
            res = supabase.table("subscriptions").select("*").eq("payment_status", "Pending").execute()
            pending = res.data
            if not pending: 
                st.info("Queue is empty. No pending payments.")
            for u in pending:
                requested_months = u.get('plan_months', 1)
                expected_total = (549.00 * requested_months) * 1.18
                display_uname = u['email'].replace("@nexus.app", "")
                
                st.markdown(f"<div style='padding: 15px; border: 1px solid #E2E8F0; border-radius: 8px; margin-bottom: 10px;'><b>User:</b> {display_uname}<br><span style='color:#64748B; font-size:13px;'>{requested_months} Months | Paid: ₹{expected_total:.2f}</span></div>", unsafe_allow_html=True)
                
                if st.button(f"✅ Approve & Issue Invoice", key=f"approve_{u['email']}", type="primary"):
                    today_str = time.strftime("%d %b %Y")
                    supabase.table("subscriptions").update({
                        "tier": "Pro", 
                        "payment_status": "Approved", 
                        "invoice_date": today_str
                    }).eq("email", u['email']).execute()
                    st.success(f"Approved {display_uname}!")
                    time.sleep(1)
                    st.rerun()
        except Exception as e: st.error(f"Database error: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.markdown("<h4>Provision New Customer</h4>", unsafe_allow_html=True)
        st.caption("Silently create a login for a new client.")
        with st.form("admin_create_user"):
            new_username = st.text_input("Customer Username", placeholder="e.g. johndoe")
            new_password = st.text_input("Secure Password", type="password")
            
            if st.form_submit_button("Create Account Profile", type="primary", use_container_width=True):
                if new_username and new_password:
                    target_email = f"{new_username.strip()}@nexus.app"
                    api_url = f"{SUPABASE_URL}/auth/v1/signup"
                    headers = {"apikey": SUPABASE_KEY, "Content-Type": "application/json"}
                    payload = {"email": target_email, "password": new_password}
                    
                    response = requests.post(api_url, headers=headers, json=payload)
                    if response.status_code == 200:
                        st.success(f"✅ Successfully created: {new_username}")
                    else: st.error(f"Creation failed: {response.text}")
                else: st.error("Credentials required.")
        st.markdown('</div>', unsafe_allow_html=True)
                    
    with col2:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.markdown("<h4>Global User Database</h4>", unsafe_allow_html=True)
        try:
            res = supabase.table("subscriptions").select("email, tier, payment_status, invoice_date, plan_months").execute()
            df = pd.DataFrame(res.data)
            
            if not df.empty:
                df['email'] = df['email'].str.replace("@nexus.app", "")
                df.rename(columns={'email': 'Username', 'tier': 'Plan', 'payment_status': 'Status', 'invoice_date': 'Billed On', 'plan_months': 'Duration'}, inplace=True)
            
            st.dataframe(df, use_container_width=True, height=650)
        except Exception as e: st.error("Could not fetch database.")
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 8. SIDEBAR & MASTER ROUTING
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='margin-top: 10px; margin-bottom: 20px; font-size: 24px; text-align: center;'>🚀 Nexus Hub</h2>", unsafe_allow_html=True)
    
    tier_colors = {"Free": "#64748B", "Plus": "#06B6D4", "Pro": "#10B981"}
    active_color = tier_colors.get(st.session_state.tier, "#64748B")
    display_name = st.session_state.user.email.replace("@nexus.app", "")
    
    st.markdown(f"""
    <div style='background: linear-gradient(145deg, #1E293B, #0F172A); padding:16px; border-radius:12px; margin-bottom: 25px; border:1px solid #334155; box-shadow: 0 4px 12px rgba(0,0,0,0.2);'>
        <div style='font-size:11px; color:#94A3B8; text-transform:uppercase; font-weight:700; letter-spacing: 0.05em;'>Active Session</div>
        <div style='font-weight:600; font-size:15px; color:#F8FAFC; margin: 4px 0 10px 0; word-break:break-all;'>{display_name}</div>
        <div><span style='background:{active_color}; color:white; font-size:11px; font-weight:700; padding:4px 10px; border-radius:12px; letter-spacing: 0.02em;'>{st.session_state.tier.upper()} PLAN</span></div>
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
    if st.button("🚪 Terminate Session", use_container_width=True):
        supabase.auth.sign_out()
        st.session_state.clear()
        st.rerun()

# Execute Active Route
if st.session_state.nav_page == "📊 Dashboard": render_dashboard()
elif st.session_state.nav_page == "🚀 Campaigns": render_campaign_launcher()
elif st.session_state.nav_page == "👥 Contact Lists": render_contact_lists()
elif st.session_state.nav_page == "⚙️️ Relay Settings": render_relay_settings()
elif st.session_state.nav_page == "💎 Upgrade Plan": render_upgrade_page()
elif st.session_state.nav_page == "🛡️ Admin Panel": render_admin_panel()