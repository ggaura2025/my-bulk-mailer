import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import os
from supabase import create_client, Client

# ==========================================
# 1. COMMERCIAL UI & CSS CONFIGURATION
# ==========================================
st.set_page_config(page_title="NexusMail Pro | Bulk Sender", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
    /* Hide default Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Premium Button Styling */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Custom Card Styling for Upgrade Page */
    .pricing-card {
        background-color: #1E1E2E;
        padding: 30px;
        border-radius: 12px;
        border: 1px solid #333;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
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
    # MVP: Default to False so you can test the lock screen. 
    # (Later, this will read from your Supabase user profile)
    st.session_state.is_pro = False 

# ==========================================
# 4. AUTHENTICATION PORTAL (LOGIN/SIGNUP)
# ==========================================
if not st.session_state.user:
    st.markdown("<h1 style='text-align: center; margin-top: 50px;'>NexusMail Pro 🚀</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888; font-size: 18px;'>Professional Mass Email Marketing Platform</p>", unsafe_allow_html=True)
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


# ==========================================
# 5. MODULAR PAGE FUNCTIONS
# ==========================================
def render_dashboard():
    st.title("📊 Campaign Overview")
    st.markdown("Welcome to your command center.")
    st.write("")
    
    col1, col2, col3 = st.columns(3)
    col1.metric(label="Total Emails Sent", value=f"{st.session_state.total_sent}", delta="This Session")
    col2.metric(label="SMTP Connection", value="Active" if st.session_state.sender_email else "Offline", delta_color="off")
    col3.metric(label="Current Plan", value="Pro Tier" if st.session_state.is_pro else "Free Tier")
    
    st.divider()
    if not st.session_state.sender_email:
        st.warning("⚠️ **Action Required:** Connect your Google SMTP account in **⚙️ SMTP Settings** to start sending.")
    else:
        st.success(f"✅ **System Ready:** Connected securely to `{st.session_state.sender_email}`")

def render_upgrade_page():
    st.title("💎 Upgrade to NexusMail Pro")
    st.markdown("Unlock unlimited bulk email blasts, advanced analytics, and priority SMTP relays.")
    st.write("")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="pricing-card">
            <h2 style="margin-bottom: 0px;">Pro Plan 🚀</h2>
            <h1 style="color: #FF4B4B; margin-top: 10px;">$29<span style="font-size: 16px; color: #888;"> / month</span></h1>
            <hr style="border-color: #333;">
            <ul style="text-align: left; list-style-type: '✅  '; line-height: 2;">
                <li><b>Unlimited</b> Email Blasting</li>
                <li>High-Speed Multi-threading</li>
                <li>Priority Google SMTP Relay</li>
                <li>Commercial Use License</li>
            </ul>
        </div>
        <br>
        """, unsafe_allow_html=True)
        
        # INSERT YOUR STRIPE PAYMENT LINK HERE
        STRIPE_CHECKOUT_URL = "https://buy.stripe.com/test_your_link_here"
        
        st.markdown(f"""
            <a href="{STRIPE_CHECKOUT_URL}" target="_blank" style="text-decoration: none;">
                <button style="width:100%; background-color:#FF4B4B; color:white; padding:14px; border:none; border-radius:8px; font-size:18px; font-weight:bold; cursor:pointer;">
                    💳 Secure Checkout with Stripe
                </button>
            </a>
        """, unsafe_allow_html=True)
        st.caption("Payments are securely processed by Stripe. You can cancel at any time.")

def render_smtp_settings():
    st.title("⚙️ SMTP Configurations")
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

def render_campaign_launcher():
    st.title("🚀 Email Campaign Builder")
    
    # --- SUBSCRIPTION GATING ---
    if not st.session_state.is_pro:
        st.error("🔒 **Pro Tier Required:** Mass email campaign launching is currently locked for free accounts.")
        st.info("Please go to **💎 Upgrade to Pro** in the sidebar to activate your subscription and unlock this feature.")
        
        # DEV BYPASS (Remove this button before launching to real customers)
        if st.button("🛠️ Developer Bypass: Grant Pro Status"):
            st.session_state.is_pro = True
            st.rerun()
        st.stop()
        
    if not st.session_state.sender_email or not st.session_state.email_app_password:
        st.warning("⚠️ Connection Error: Please configure your **SMTP Settings** before launching a campaign.")
        st.stop()
        
    col_main, col_sidebar = st.columns([2, 1])
    
    with col_main:
        st.subheader("1. Message Details")
        subject = st.text_input("Subject Line", placeholder="e.g., Exclusive Early Access Offer!")
        body = st.text_area("Email Body (Plain Text)", height=250, placeholder="Type your message here...")
    
    with col_sidebar:
        st.subheader("2. Target Audience")
        tabs = st.tabs(["📁 Upload List", "✏️ Manual"])
        emails = []
        
        with tabs[0]:
            uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])
            if uploaded_file:
                try:
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file, header=None)
                    else:
                        df = pd.read_excel(uploaded_file, header=None)
                    emails = df.iloc[:, 0].dropna().astype(str).tolist()
                    st.success(f"✅ {len(emails)} recipients loaded.")
                except Exception as e:
                    st.error(f"File error: {e}")
                    
        with tabs[1]:
            manual_emails = st.text_area("Enter emails (comma separated)", height=150)
            if manual_emails:
                emails = [e.strip() for e in manual_emails.split(",") if e.strip()]
                st.success(f"✅ {len(emails)} recipients loaded.")

    st.divider()
    
    col_space1, col_action, col_space2 = st.columns([1, 2, 1])
    with col_action:
        if st.button("🚀 Blast Campaign", type="primary", use_container_width=True):
            if not subject or not body:
                st.toast("Missing subject or body!", icon="❌")
            elif not emails:
                st.toast("No recipients found!", icon="❌")
            else:
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
                        st.balloons()
                        
                    except Exception as e:
                        status.update(label="Campaign Failed", state="error", expanded=True)
                        st.error(f"Critical SMTP Error: {e}. Check your App Password.")

# ==========================================
# 6. MAIN APPLICATION ROUTING
# ==========================================
with st.sidebar:
    st.markdown("### 🏢 Nexus Workspace")
    st.caption(f"Logged in as: **{st.session_state.user.email}**")
    
    if st.session_state.is_pro:
        st.success("💎 Pro Member")
    else:
        st.warning("🆓 Free Member")
        
    st.divider()
    page = st.radio("Navigation", ["📊 Dashboard", "💎 Upgrade to Pro", "⚙️ SMTP Settings", "🚀 Launch Campaign"])
    st.divider()
    
    if st.button("🚪 Log Out", use_container_width=True):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.session_state.sender_email = ""
        st.session_state.email_app_password = ""
        st.session_state.is_pro = False
        st.rerun()

# Execute the selected page
if page == "📊 Dashboard":
    render_dashboard()
elif page == "💎 Upgrade to Pro":
    render_upgrade_page()
elif page == "⚙️ SMTP Settings":
    render_smtp_settings()
elif page == "🚀 Launch Campaign":
    render_campaign_launcher()