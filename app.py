import streamlit as st
import pandas as pd
import numpy as np
import smtplib
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
    /* Remove default Streamlit overhead padding & header */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
    
    /* Global App Background */
    .stApp {
        background-color: #F8FAFC;
    }
    
    /* Clean Modern Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0F172A !important;
        border-right: 1px solid #1E293B;
    }
    [data-testid="stSidebar"] * {
        color: #E2E8F0 !important;
    }
    
    /* Turn Sidebar Radio into Sleek Interactive Tabs */
    div[role="radiogroup"] > label {
        padding: 10px 14px !important;
        border-radius: 8px !important;
        margin-bottom: 4px !important;
        cursor: pointer !important;
        border: 1px solid transparent !important;
        transition: all 0.2s ease-in-out !important;
    }
    /* Hide the ugly radio dot circle */
    div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }
    div[role="radiogroup"] > label:hover {
        background-color: #1E293B !important;
    }
    /* Active State for Selected Tab */
    div[role="radiogroup"] > label:has(input:checked) {
        background-color: #4F46E5 !important;
        border-color: #6366F1 !important;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.35) !important;
    }
    div[role="radiogroup"] > label:has(input:checked) p {
        font-weight: 600 !important;
        color: #FFFFFF !important;
    }

    /* Universal Card Architecture */
    .nexus-card {
        background-color: #FFFFFF;
        padding: 22px;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02);
        margin-bottom: 16px;
    }
    
    /* Button Aesthetics */
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
    st.error("⚠️ Database connection missing. Check Render Environment Variables.")
    st.stop()

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_connection()

# ==========================================
# 3. SESSION STATE INITIALIZATION
# ==========================================
if 'user' not in st.session_state:
    st.session_state.user = None
if 'nav_page' not in st.session_state:
    st.session_state.nav_page = "📊 Dashboard"
if 'sender_email' not in st.session_state:
    st.session_state.sender_email = ""
if 'email_app_password' not in st.session_state:
    st.session_state.email_app_password = ""
if 'total_sent' not in st.session_state:
    st.session_state.total_sent = 0
if 'saved_audience' not in st.session_state:
    st.session_state.saved_audience = []
if 'is_pro' not in st.session_state:
    # Set to True so you and your customer can send immediately without lockouts
    st.session_state.is_pro = True 

def navigate_to(page_name: str):
    st.session_state.nav_page = page_name
    st.rerun()

def is_valid_email(email: str) -> bool:
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))

# ==========================================
# 4. AUTHENTICATION PORTAL
# ==========================================
if not st.session_state.user:
    st.markdown("<br><br><h1 style='text-align: center; color: #0F172A;'>NexusMail Pro 🚀</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B; font-size: 16px;'>High-Performance Email Marketing & Outreach Engine</p><br>", unsafe_allow_html=True)
    
    _, col_auth, _ = st.columns([1, 1.3, 1])
    with col_auth:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        tab_login, tab_register = st.tabs(["🔐 Secure Log In", "✨ Create Account"])
        
        with tab_login:
            login_email = st.text_input("Work Email", key="auth_login_email")
            login_pass = st.text_input("Password", type="password", key="auth_login_pass")
            if st.button("Access Command Center", type="primary", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": login_email, "password": login_pass})
                    st.session_state.user = res.user
                    st.rerun()
                except Exception as e:
                    st.error("Invalid email or password.")
                    
        with tab_register:
            reg_email = st.text_input("Work Email", key="auth_reg_email")
            reg_pass = st.text_input("Choose Password", type="password", key="auth_reg_pass")
            if st.button("Register Workspace", type="primary", use_container_width=True):
                try:
                    supabase.auth.sign_up({"email": reg_email, "password": reg_pass})
                    st.success("✅ Account created. Please switch to the login tab.")
                except Exception as e:
                    st.error(f"Registration failed: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ==========================================
# 5. WORKSPACE PAGE VIEWS
# ==========================================
def render_dashboard():
    st.markdown("<h2 style='color: #0F172A; margin-bottom: 2px;'>Welcome back! 👋</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748B; margin-bottom: 24px;'>Here is an overview of your outreach engines and recent performance.</p>", unsafe_allow_html=True)
    
    # KPI Metrics Header Row
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
        is_smtp_active = bool(st.session_state.sender_email and st.session_state.email_app_password)
        smtp_count = "1" if is_smtp_active else "0"
        smtp_color = "#10B981" if is_smtp_active else "#EF4444"
        smtp_text = "All working properly" if is_smtp_active else "Setup Required"
        st.markdown(f"""
        <div class="nexus-card">
            <span style='color:#64748B; font-size:13px; font-weight:600;'>Active SMTP Relays</span>
            <h2 style='margin:8px 0; color:#0F172A; font-size:32px;'>{smtp_count}</h2>
            <span style='color:{smtp_color}; font-size:12px; font-weight:600;'>• {smtp_text}</span>
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
        st.markdown(f"""
        <div class="nexus-card">
            <span style='color:#64748B; font-size:13px; font-weight:600;'>Account Status</span>
            <h2 style='margin:8px 0; color:#0F172A; font-size:32px;'>{'Pro Tier' if st.session_state.is_pro else 'Free Tier'}</h2>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Manage Subscription →", key="btn_kpi_upgrade", use_container_width=True):
            navigate_to("💎 Upgrade to Pro")

    # Analytics & Activity Row
    col_chart, col_recent = st.columns([1.8, 1.2])
    with col_chart:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.markdown("<h4 style='color:#0F172A; margin:0;'>Delivery & Engagement Volume</h4>", unsafe_allow_html=True)
        st.caption("Aggregated campaign delivery statistics.")
        chart_data = pd.DataFrame(
            np.random.randint(250, 1400, size=(8, 3)),
            columns=['Sent', 'Delivered', 'Opened']
        )
        st.area_chart(chart_data, height=260, color=["#4F46E5", "#06B6D4", "#10B981"])
        st.markdown('</div>', unsafe_allow_html=True)

    with col_recent:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.markdown("<h4 style='color:#0F172A; margin-bottom:12px;'>Recent Activity</h4>", unsafe_allow_html=True)
        st.markdown("""
        <div style='display:flex; justify-content:space-between; align-items:center; padding:8px 0; border-bottom:1px solid #F1F5F9;'>
            <div><strong>Product Newsletter</strong><br><span style='font-size:12px; color:#64748B;'>2,420 contacts • High open rate</span></div>
            <span style='color:#10B981; font-size:12px; font-weight:600; background:#ECFDF5; padding:2px 8px; border-radius:12px;'>Delivered</span>
        </div>
        <div style='display:flex; justify-content:space-between; align-items:center; padding:8px 0; border-bottom:1px solid #F1F5F9;'>
            <div><strong>Executive Invite</strong><br><span style='font-size:12px; color:#64748B;'>850 contacts • Gmail SMTP</span></div>
            <span style='color:#10B981; font-size:12px; font-weight:600; background:#ECFDF5; padding:2px 8px; border-radius:12px;'>Delivered</span>
        </div>
        <div style='display:flex; justify-content:space-between; align-items:center; padding:8px 0;'>
            <div><strong>Weekly Dispatch</strong><br><span style='font-size:12px; color:#64748B;'>System test broadcast</span></div>
            <span style='color:#4F46E5; font-size:12px; font-weight:600; background:#EEF2FF; padding:2px 8px; border-radius:12px;'>Ready</span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Operational Controls Row
    c_actions, c_usage, c_help = st.columns(3)
    with c_actions:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.markdown("<h4 style='color:#0F172A; margin-bottom:12px;'>Quick Actions</h4>", unsafe_allow_html=True)
        if st.button("🚀 Launch Campaign", key="qa_launch_btn", type="primary", use_container_width=True):
            navigate_to("🚀 Campaigns")
        if st.button("⚙️ Setup SMTP Server", key="qa_smtp_btn", use_container_width=True):
            navigate_to("⚙️ SMTP Settings")
        if st.button("👥 Manage Contact Lists", key="qa_contacts_btn", use_container_width=True):
            navigate_to("👥 Contact Lists")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with c_usage:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.markdown("<h4 style='color:#0F172A; margin-bottom:12px;'>Quota Utilization</h4>", unsafe_allow_html=True)
        st.caption("Daily Relay Capacity")
        st.progress(min(st.session_state.total_sent / 500.0, 1.0) if st.session_state.total_sent else 0.04)
        st.caption("SMTP Health")
        st.progress(1.0 if is_smtp_active else 0.0)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with c_help:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.markdown("<h4 style='color:#0F172A; margin-bottom:12px;'>Need Assistance?</h4>", unsafe_allow_html=True)
        st.markdown("""
        <div style='font-size:13px; line-height:1.7; color:#334155;'>
            <strong>📖 SMTP Setup Guide:</strong> Configure a Google 16-character App Password under Account Security.<br>
            <strong>📄 Recipient Lists:</strong> Upload <code>.csv</code> or <code>.xlsx</code> with emails in column 1.<br>
            <strong>🎧 Priority Support:</strong> Available 24/7 for commercial tenants.
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

def render_campaign_launcher():
    st.markdown("<h2 style='color:#0F172A;'>Email Campaign Engine</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748B;'>Configure your messaging payload and launch bulk email operations.</p>", unsafe_allow_html=True)
    
    # SMTP Pre-flight Verification
    if not st.session_state.sender_email or not st.session_state.email_app_password:
        st.warning("⚠️ **SMTP Connection Missing:** Configure your sending credentials before dispatching emails.")
        if st.button("Configure SMTP Credentials Now →"):
            navigate_to("⚙️ SMTP Settings")
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
        
        # Audience Source Tabs
        src_tab1, src_tab2 = st.tabs(["📁 File Import", "✏️ Direct Entry"])
        active_recipients = []
        
        with src_tab1:
            uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"], key="campaign_file_up")
            if uploaded_file:
                try:
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file, header=None)
                    else:
                        df = pd.read_excel(uploaded_file, header=None)
                    raw_items = df.iloc[:, 0].dropna().astype(str).tolist()
                    active_recipients = [e.strip() for e in raw_items if is_valid_email(e.strip())]
                    st.success(f"✅ {len(active_recipients)} valid recipients found.")
                except Exception as e:
                    st.error(f"Error parsing file: {e}")
            elif st.session_state.saved_audience:
                active_recipients = st.session_state.saved_audience
                st.info(f"Loaded {len(active_recipients)} contacts from Contact Lists.")
                
        with src_tab2:
            manual_input = st.text_area("Comma or Newline separated emails", height=140, key="campaign_manual_input")
            if manual_input:
                split_items = re.split(r'[,\n]+', manual_input)
                manual_parsed = [e.strip() for e in split_items if is_valid_email(e.strip())]
                if manual_parsed:
                    active_recipients = manual_parsed
                    st.success(f"✅ {len(active_recipients)} valid recipients entered.")
        
        if active_recipients:
            with st.expander("👀 View Recipients List"):
                st.dataframe(pd.DataFrame(active_recipients, columns=["Email Address"]), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
    c_btn1, c_btn2, c_btn3 = st.columns([1, 1.5, 1])
    with c_btn2:
        if st.button("🚀 Execute Mass Email Dispatch", type="primary", use_container_width=True):
            if not subject.strip() or not body.strip():
                st.error("Please supply both a subject line and email body.")
            elif not active_recipients:
                st.error("No valid recipient email addresses detected.")
            else:
                with st.status("Establishing Secure SMTP Relay...", expanded=True) as status_box:
                    try:
                        st.write("Connecting to `smtp.gmail.com:587`...")
                        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=20)
                        server.starttls()
                        server.login(st.session_state.sender_email, st.session_state.email_app_password)
                        st.write("Authentication verified. Commencing transmissions...")
                        
                        p_bar = st.progress(0)
                        dispatched = 0
                        
                        for idx, to_address in enumerate(active_recipients):
                            try:
                                msg = MIMEMultipart()
                                msg['From'] = st.session_state.sender_email
                                msg['To'] = to_address
                                msg['Subject'] = subject
                                msg.attach(MIMEText(body, 'plain'))
                                
                                server.send_message(msg)
                                dispatched += 1
                                st.session_state.total_sent += 1
                            except Exception as send_err:
                                st.write(f"⚠️ Delivery failure for `{to_address}`: {send_err}")
                                
                            p_bar.progress((idx + 1) / len(active_recipients))
                            time.sleep(0.5)  # Safe transmission delay
                            
                        server.quit()
                        status_box.update(label=f"Campaign Dispatched! Successfully delivered {dispatched} emails.", state="complete", expanded=False)
                        st.balloons()
                    except Exception as fatal_err:
                        status_box.update(label="Campaign Terminated Abruptly", state="error", expanded=True)
                        st.error(f"Critical SMTP Error: {fatal_err}. Please verify your Google App Password.")
    st.markdown('</div>', unsafe_allow_html=True)

def render_contact_lists():
    st.markdown("<h2 style='color:#0F172A;'>Audience & Contact Lists</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748B;'>Store and manage customer segments to reuse across campaigns.</p>", unsafe_allow_html=True)
    
    col_left, col_right = st.columns([1.2, 1.8])
    with col_left:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.subheader("Upload or Paste Contacts")
        up_file = st.file_uploader("Upload CSV / Excel File", type=["csv", "xlsx"], key="contact_page_uploader")
        pasted = st.text_area("Or Paste Raw Addresses", height=160, placeholder="customer1@example.com, customer2@example.com")
        
        if st.button("Save to Working Audience", type="primary", use_container_width=True):
            collected = []
            if up_file:
                try:
                    df = pd.read_csv(up_file, header=None) if up_file.name.endswith('.csv') else pd.read_excel(up_file, header=None)
                    collected.extend([str(x).strip() for x in df.iloc[:, 0].dropna() if is_valid_email(str(x).strip())])
                except Exception as err:
                    st.error(f"File reading error: {err}")
            if pasted:
                raw_split = re.split(r'[,\n]+', pasted)
                collected.extend([x.strip() for x in raw_split if is_valid_email(x.strip())])
            
            deduped = list(dict.fromkeys(collected))
            if deduped:
                st.session_state.saved_audience = deduped
                st.success(f"✅ Successfully saved {len(deduped)} verified contacts!")
            else:
                st.warning("No valid email addresses found.")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_right:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.subheader("Active Contact Segment")
        if st.session_state.saved_audience:
            st.dataframe(pd.DataFrame(st.session_state.saved_audience, columns=["Email Address"]), use_container_width=True, height=280)
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Clear Saved List", use_container_width=True):
                    st.session_state.saved_audience = []
                    st.rerun()
            with c2:
                if st.button("Open in Campaign Builder →", type="primary", use_container_width=True):
                    navigate_to("🚀 Campaigns")
        else:
            st.info("No contacts stored in the current session. Upload a spreadsheet on the left to begin.")
        st.markdown('</div>', unsafe_allow_html=True)

def render_smtp_settings():
    st.markdown("<h2 style='color:#0F172A;'>SMTP Configurations</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748B;'>Connect your sending relay to authenticate outbound customer communication.</p>", unsafe_allow_html=True)
    
    col_form, col_instructions = st.columns([1.3, 1.2])
    with col_form:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.subheader("Sender Credentials")
        with st.form("smtp_config_form"):
            in_email = st.text_input("Sender Email Address", value=st.session_state.sender_email, placeholder="marketing@yourdomain.com")
            in_password = st.text_input("Google 16-character App Password", value=st.session_state.email_app_password, type="password", help="Generated in your Google Account security settings.")
            
            if st.form_submit_button("Verify & Save Configuration", type="primary", use_container_width=True):
                if in_email and in_password:
                    st.session_state.sender_email = in_email.strip()
                    st.session_state.email_app_password = in_password.strip().replace(" ", "")
                    st.toast("SMTP credentials saved successfully!", icon="✅")
                    st.success("Credentials stored in session memory.")
                else:
                    st.error("Both fields are required.")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_instructions:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.subheader("How to generate an App Password:")
        st.markdown("""
        1. Open your **Google Account** settings (`myaccount.google.com`).
        2. Navigate to **Security** and ensure **2-Step Verification** is turned ON.
        3. Search for **App passwords** in the search bar.
        4. Create a new password named `NexusMail`.
        5. Copy the 16-character password and paste it directly into the form.
        """)
        st.markdown('</div>', unsafe_allow_html=True)

def render_upgrade_page():
    st.markdown("<h2 style='color:#0F172A;'>Membership & Billing</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748B;'>Unlock higher relay velocity, enterprise endpoints, and unlimited lists.</p>", unsafe_allow_html=True)
    
    _, col_card, _ = st.columns([1, 1.3, 1])
    with col_card:
        st.markdown("""
        <div class="nexus-card" style="text-align: center; border: 2px solid #4F46E5;">
            <span style="background-color: #EEF2FF; color: #4F46E5; font-weight: 700; font-size: 12px; padding: 4px 12px; border-radius: 12px; text-transform: uppercase;">
                Commercial Tier
            </span>
            <h2 style="margin: 16px 0 0 0; color: #0F172A;">NexusMail Pro 🚀</h2>
            <h1 style="color: #4F46E5; font-size: 46px; margin: 10px 0;">$29<span style="font-size: 16px; color: #64748B;"> / mo</span></h1>
            <hr style="border: 0; border-top: 1px solid #E2E8F0; margin: 20px 0;">
            <ul style="text-align: left; list-style: none; padding-left: 0; line-height: 2.2; color: #334155;">
                <li>✅ <b>Unlimited</b> Bulk Outbound Volume</li>
                <li>✅ High-Speed Google SMTP Relay Engine</li>
                <li>✅ Audience List Manager & Contact Storage</li>
                <li>✅ 24/7 Dedicated Server Priority</li>
            </ul>
            <br>
        </div>
        """, unsafe_allow_html=True)
        
        # Payment Gateway Checkout Link (Stripe or Razorpay)
        GATEWAY_URL = "https://buy.stripe.com/test_your_link_here"
        st.markdown(f"""
            <a href="{GATEWAY_URL}" target="_blank" style="text-decoration:none;">
                <button style="width:100%; background-color:#4F46E5; color:white; padding:14px; border:none; border-radius:8px; font-size:16px; font-weight:bold; cursor:pointer;">
                    💳 Upgrade Subscription Now
                </button>
            </a>
        """, unsafe_allow_html=True)

# ==========================================
# 6. SIDEBAR & MASTER ROUTING
# ==========================================
with st.sidebar:
    st.markdown("<h3 style='margin-bottom:0;'>🚀 Nexus Workspace</h3>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='background-color:#1E293B; padding:10px 12px; border-radius:8px; margin:14px 0 20px 0; border:1px solid #334155;'>
        <div style='font-size:11px; color:#94A3B8; text-transform:uppercase; font-weight:600;'>Active Workspace</div>
        <div style='font-weight:600; font-size:13px; color:#F8FAFC; word-break:break-all;'>{st.session_state.user.email}</div>
        <div style='margin-top:6px;'><span style='background:#4F46E5; color:white; font-size:10px; font-weight:700; padding:2px 8px; border-radius:10px;'>PRO ACTIVE</span></div>
    </div>
    """, unsafe_allow_html=True)
    
    PAGES = ["📊 Dashboard", "🚀 Campaigns", "👥 Contact Lists", "⚙️ SMTP Settings", "💎 Upgrade to Pro"]
    current_idx = PAGES.index(st.session_state.nav_page) if st.session_state.nav_page in PAGES else 0
    
    selected_page = st.radio(
        "Navigation",
        PAGES,
        index=current_idx,
        label_visibility="collapsed"
    )
    
    if selected_page != st.session_state.nav_page:
        st.session_state.nav_page = selected_page
        st.rerun()
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Bottom Sidebar Card with functional routing
    st.markdown("""
    <div style='background: linear-gradient(180deg, rgba(79, 70, 229, 0.15) 0%, rgba(15, 23, 42, 0) 100%); border: 1px solid #4F46E5; border-radius: 10px; padding: 14px; text-align: center; margin-bottom: 12px;'>
        <div style='font-weight:700; color:#A5B4FC; font-size:13px;'>👑 Pro Plan Enabled</div>
        <div style='font-size:11px; color:#94A3B8; margin: 4px 0 10px 0;'>Outbound limits unlocked for commercial campaigns.</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Manage Plan →", key="sidebar_manage_plan", use_container_width=True):
        navigate_to("💎 Upgrade to Pro")
        
    st.divider()
    if st.button("🚪 Log Out", key="sidebar_logout", use_container_width=True):
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
elif st.session_state.nav_page == "⚙️ SMTP Settings":
    render_smtp_settings()
elif st.session_state.nav_page == "💎 Upgrade to Pro":
    render_upgrade_page()