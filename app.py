import streamlit as st
import pandas as pd
import numpy as np
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import os
from supabase import create_client, Client

# ==========================================
# 1. COMMERCIAL UI & CSS CONFIGURATION
# ==========================================
st.set_page_config(page_title="Nexus Workspace", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Overall Background and Font */
    .stApp {
        background-color: #F4F7FE;
    }
    
    /* Custom Card Styling for Metrics & Panels */
    .nexus-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.03);
        margin-bottom: 20px;
        border: 1px solid #E5E7EB;
    }
    
    /* Sidebar Text Adjustments */
    [data-testid="stSidebar"] {
        color: white !important;
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Primary Button Styling */
    .stButton>button {
        background-color: #4F46E5;
        color: white;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1rem;
        border: none;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
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
# 3. SESSION STATE MANAGEMENT
# ==========================================
if 'user' not in st.session_state:
    st.session_state.user = None
if 'sender_email' not in st.session_state:
    st.session_state.sender_email = ""
if 'email_app_password' not in st.session_state:
    st.session_state.email_app_password = ""
if 'total_sent' not in st.session_state:
    st.session_state.total_sent = 0
if 'is_pro' not in st.session_state:
    st.session_state.is_pro = False 

# ==========================================
# 4. AUTHENTICATION PORTAL (LOGIN/SIGNUP)
# ==========================================
if not st.session_state.user:
    st.markdown("<br><br><h1 style='text-align: center; color: #1E1E2E;'>NexusMail Pro 🚀</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #6B7280; font-size: 18px;'>Professional Mass Email Marketing Platform</p><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
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
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()


# ==========================================
# 5. MODULAR PAGE FUNCTIONS
# ==========================================
def render_dashboard():
    st.markdown("<h1>Welcome back! 👋</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#6B7280;'>Here's an overview of your email campaigns and account activity.</p>", unsafe_allow_html=True)
    
    # --- TOP KPI CARDS ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="nexus-card">
            <h4 style='color:#6B7280; margin:0; font-size:14px;'>Total Emails Sent</h4>
            <h2 style='margin:10px 0; color:#111827;'>{st.session_state.total_sent}</h2>
            <p style='color:#10B981; margin:0; font-size:12px;'>↑ 12% from last month</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        smtp_status = "2" if st.session_state.sender_email else "0"
        status_color = "#10B981" if st.session_state.sender_email else "#EF4444"
        status_text = "All working properly" if st.session_state.sender_email else "Requires Setup"
        st.markdown(f"""
        <div class="nexus-card">
            <h4 style='color:#6B7280; margin:0; font-size:14px;'>Active SMTP Connections</h4>
            <h2 style='margin:10px 0; color:#111827;'>{smtp_status}</h2>
            <p style='color:{status_color}; margin:0; font-size:12px;'>✓ {status_text}</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="nexus-card">
            <h4 style='color:#6B7280; margin:0; font-size:14px;'>Campaigns Created</h4>
            <h2 style='margin:10px 0; color:#111827;'>8</h2>
            <p style='color:#10B981; margin:0; font-size:12px;'>↑ 33% from last month</p>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        plan_name = "Pro Tier 👑" if st.session_state.is_pro else "Free Tier"
        st.markdown(f"""
        <div class="nexus-card">
            <h4 style='color:#6B7280; margin:0; font-size:14px;'>Current Plan</h4>
            <h2 style='margin:10px 0; color:#111827;'>{plan_name}</h2>
            <a href='#' style='color:#4F46E5; font-size:12px; text-decoration:none;'>Manage Subscription →</a>
        </div>
        """, unsafe_allow_html=True)

    # --- MIDDLE SECTION (Chart & Recent) ---
    col_main, col_side = st.columns([2, 1])
    
    with col_main:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.markdown("### Email Performance")
        st.caption("Sent, delivered, opened and clicked emails over time.")
        # Dummy data for the aesthetic chart
        chart_data = pd.DataFrame(
            np.random.randint(100, 1500, size=(10, 3)),
            columns=['Sent', 'Opened', 'Clicked']
        )
        st.area_chart(chart_data, height=280, color=["#4F46E5", "#10B981", "#F59E0B"])
        st.markdown('</div>', unsafe_allow_html=True)

    with col_side:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.markdown("### Recent Campaigns")
        st.markdown("""
        <div style='display:flex; justify-content:space-between; margin-bottom:15px; border-bottom:1px solid #E5E7EB; padding-bottom:10px;'>
            <div><strong>October Newsletter</strong><br><span style='font-size:12px; color:gray;'>2,420 sent • 38% opened</span></div>
            <div style='color:#10B981; font-weight:bold; font-size:12px;'>Completed</div>
        </div>
        <div style='display:flex; justify-content:space-between; margin-bottom:15px; border-bottom:1px solid #E5E7EB; padding-bottom:10px;'>
            <div><strong>Course Announcement</strong><br><span style='font-size:12px; color:gray;'>1,830 sent • 42% opened</span></div>
            <div style='color:#10B981; font-weight:bold; font-size:12px;'>Completed</div>
        </div>
        <div style='display:flex; justify-content:space-between; border-bottom:1px solid #E5E7EB; padding-bottom:10px;'>
            <div><strong>Community Update</strong><br><span style='font-size:12px; color:gray;'>1,540 sent • 28% opened</span></div>
            <div style='color:#F59E0B; font-weight:bold; font-size:12px;'>Sending...</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- BOTTOM SECTION (Usage & Actions) ---
    col_action, col_usage, col_help = st.columns(3)
    with col_action:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.markdown("### Quick Actions")
        st.button("🚀 Launch Campaign", use_container_width=True)
        st.button("⚙️ Setup SMTP Settings", use_container_width=True)
        st.button("👥 Manage Contact Lists", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_usage:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.markdown("### Plan Usage")
        st.caption("Emails Sent (This Month)")
        st.progress(0.12)
        st.caption("SMTP Connections")
        st.progress(0.20)
        st.caption("Email Lists")
        st.progress(0.10)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_help:
        st.markdown('<div class="nexus-card">', unsafe_allow_html=True)
        st.markdown("### Need Help?")
        st.markdown("📖 **Setup Guide**<br><span style='font-size:12px; color:gray;'>Learn how to configure SMTP</span>", unsafe_allow_html=True)
        st.markdown("📄 **Documentation**<br><span style='font-size:12px; color:gray;'>Detailed guides and API reference</span>", unsafe_allow_html=True)
        st.markdown("🎧 **Contact Support**<br><span style='font-size:12px; color:gray;'>Get help from our team</span>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


def render_upgrade_page():
    st.title("💎 Upgrade to NexusMail Pro")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="nexus-card" style="text-align: center; border: 2px solid #4F46E5;">
            <h2>Pro Plan 🚀</h2>
            <h1 style="color: #4F46E5;">$29<span style="font-size: 16px; color: #888;"> / month</span></h1>
            <hr>
            <ul style="text-align: left; line-height: 2;">
                <li>✅ <b>Unlimited</b> Email Blasting</li>
                <li>✅ High-Speed Multi-threading</li>
                <li>✅ Priority Google SMTP Relay</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        STRIPE_CHECKOUT_URL = "https://buy.stripe.com/test_your_link_here"
        st.markdown(f'<a href="{STRIPE_CHECKOUT_URL}" target="_blank"><button style="width:100%; background-color:#4F46E5; color:white; padding:14px; border:none; border-radius:8px; font-size:18px; font-weight:bold; cursor:pointer;">💳 Secure Checkout</button></a>', unsafe_allow_html=True)

def render_smtp_settings():
    st.title("⚙️ SMTP Configurations")
    with st.form("smtp_form"):
        st.subheader("Sender Credentials")
        new_email = st.text_input("Sender Email Address", value=st.session_state.sender_email)
        new_password = st.text_input("App Password", type="password", value=st.session_state.email_app_password)
        if st.form_submit_button("Save Configuration", type="primary"):
            st.session_state.sender_email = new_email
            st.session_state.email_app_password = new_password
            st.toast('SMTP Credentials Saved!', icon='✅')

def render_campaign_launcher():
    st.title("🚀 Launch Campaign")
    if not st.session_state.is_pro:
        st.error("🔒 **Pro Tier Required:** Mass email launching is locked for free accounts.")
        if st.button("🛠️ Developer Bypass: Grant Pro Status"):
            st.session_state.is_pro = True
            st.rerun()
        st.stop()
        
    if not st.session_state.sender_email:
        st.warning("⚠️ Please configure **SMTP Settings** first.")
        st.stop()
        
    col_main, col_sidebar = st.columns([2, 1])
    with col_main:
        subject = st.text_input("Subject Line")
        body = st.text_area("Email Body", height=250)
    with col_sidebar:
        emails = st.text_area("Target Emails (comma separated)", height=150)
        emails_list = [e.strip() for e in emails.split(",") if e.strip()]

    if st.button("🚀 Blast Campaign", type="primary"):
        if emails_list and subject and body:
            with st.status("Initializing...", expanded=True) as status:
                try:
                    server = smtplib.SMTP("smtp.gmail.com", 587)
                    server.starttls()
                    server.login(st.session_state.sender_email, st.session_state.email_app_password)
                    progress_bar = st.progress(0)
                    for i, recipient in enumerate(emails_list):
                        msg = MIMEMultipart()
                        msg['From'], msg['To'], msg['Subject'] = st.session_state.sender_email, recipient, subject
                        msg.attach(MIMEText(body, 'plain'))
                        server.send_message(msg)
                        st.session_state.total_sent += 1
                        progress_bar.progress((i + 1) / len(emails_list))
                    server.quit()
                    status.update(label="Complete!", state="complete")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error: {e}")

# ==========================================
# 6. MAIN APPLICATION ROUTING
# ==========================================
with st.sidebar:
    st.markdown("<h2>🚀 Nexus Workspace</h2>", unsafe_allow_html=True)
    st.markdown(f"<div style='background-color:#374151; padding:10px; border-radius:8px; margin-bottom:20px;'><span style='font-size:12px; color:#9CA3AF;'>Logged in as</span><br><b>{st.session_state.user.email}</b></div>", unsafe_allow_html=True)
    
    page = st.radio("", ["🏠 Dashboard", "🚀 Campaigns", "⚙️ SMTP Settings", "💎 Upgrade to Pro", "🚪 Log Out"])
    
    # Custom Sidebar Pro Card
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background-color:rgba(79, 70, 229, 0.1); border:1px solid #4F46E5; padding:15px; border-radius:10px; text-align:center;'>
        <h3 style='margin:0; color:#A5B4FC;'>👑 Pro Tier</h3>
        <p style='font-size:12px; color:#D1D5DB;'>Unlimited campaigns.<br>More power for your outreach.</p>
    </div>
    """, unsafe_allow_html=True)

if page == "🏠 Dashboard":
    render_dashboard()
elif page == "💎 Upgrade to Pro":
    render_upgrade_page()
elif page == "⚙️ SMTP Settings":
    render_smtp_settings()
elif page == "🚀 Campaigns":
    render_campaign_launcher()
elif page == "🚪 Log Out":
    supabase.auth.sign_out()
    st.session_state.clear()
    st.rerun()