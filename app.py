
import streamlit as st
import pandas as pd
import requests
import math

# ==========================================
# SMARTAVIATORAI V4.2
# SUPABASE AUTH + PRIVATE USER DATA
# ==========================================

st.set_page_config(
    page_title="SmartAviatorAI V4.2",
    page_icon="✈️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==========================================
# SUPABASE CONFIGURATION
# ==========================================

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"].rstrip("/")
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    st.error("Supabase settings hazijapatikana kwenye Streamlit Secrets.")
    st.stop()


def auth_request(endpoint, payload):
    response = requests.post(
        f"{SUPABASE_URL}/auth/v1/{endpoint}",
        headers={
            "apikey": SUPABASE_KEY,
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=30
    )

    if not response.ok:
        try:
            message = response.json().get("msg") or response.json().get("message")
        except Exception:
            message = response.text
        raise RuntimeError(message or "Authentication failed.")

    return response.json()


def login(email, password):
    return auth_request(
        "token?grant_type=password",
        {"email": email, "password": password}
    )


def refresh_session():
    refresh_token = st.session_state.get("refresh_token")

    if not refresh_token:
        return False

    try:
        data = auth_request(
            "token?grant_type=refresh_token",
            {"refresh_token": refresh_token}
        )

        st.session_state.access_token = data["access_token"]
        st.session_state.refresh_token = data["refresh_token"]
        st.session_state.user_id = data["user"]["id"]
        st.session_state.user_email = data["user"]["email"]
        return True

    except Exception:
        return False


# ==========================================
# LOGIN SYSTEM
# ==========================================

if "access_token" not in st.session_state:
    st.session_state.access_token = None

if not st.session_state.access_token:

    st.markdown(
        "<h1 style='text-align:center'>✈️ SmartAviatorAI</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align:center'>🔐 Secure Private Access</p>",
        unsafe_allow_html=True
    )

    with st.form("supabase_login"):
        email = st.text_input("Email address", placeholder="you@example.com")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button(
            "🔓 LOGIN",
            use_container_width=True
        )

    if submitted:
        if not email.strip() or not password:
            st.error("Ingiza email na password.")
        else:
            try:
                data = login(email.strip(), password)

                st.session_state.access_token = data["access_token"]
                st.session_state.refresh_token = data["refresh_token"]
                st.session_state.user_id = data["user"]["id"]
                st.session_state.user_email = data["user"]["email"]

                st.rerun()

            except Exception as e:
                st.error(f"Login imeshindikana: {e}")

    st.stop()


# ==========================================
# AUTHENTICATED DATABASE REQUESTS
# ==========================================

def db_request(method, endpoint, params=None, payload=None):

    def send_request():
        return requests.request(
            method,
            f"{SUPABASE_URL}/rest/v1/{endpoint}",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {st.session_state.access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Prefer": "return=representation"
            },
            params=params,
            json=payload,
            timeout=30
        )

    response = send_request()

    if response.status_code == 401:
        if refresh_session():
            response = send_request()
        else:
            st.session_state.access_token = None
            st.session_state.refresh_token = None
            st.rerun()

    if not response.ok:
        try:
            message = response.json().get("message", response.text)
        except Exception:
            message = response.text

        raise RuntimeError(
            f"Database error ({response.status_code}): {message}"
        )

    if response.status_code == 204 or not response.text.strip():
        return []

    return response.json()


# ==========================================
# DATABASE FUNCTIONS
# ==========================================

def save_rounds(values):

    user_id = st.session_state.user_id

    records = [
        {
            "multiplier": float(value),
            "user_id": user_id
        }
        for value in values
    ]

    saved = 0

    for i in range(0, len(records), 500):
        batch = records[i:i + 500]

        result = db_request(
            "POST",
            "rounds",
            payload=batch
        )

        saved += len(result)

    return saved


def load_data():

    all_records = []
    offset = 0
    page_size = 1000

    while offset < 10000:

        records = db_request(
            "GET",
            "rounds",
            params={
                "select": "id,multiplier,created_at,user_id",
                "user_id": f"eq.{st.session_state.user_id}",
                "order": "id.desc",
                "limit": page_size,
                "offset": offset
            }
        )

        if not records:
            break

        all_records.extend(records)

        if len(records) < page_size:
            break

        offset += page_size

    df = pd.DataFrame(all_records)

    if not df.empty:
        df["id"] = pd.to_numeric(df["id"], errors="coerce")
        df["multiplier"] = pd.to_numeric(
            df["multiplier"], errors="coerce"
        )
        df["created_at"] = pd.to_datetime(
            df["created_at"], utc=True, errors="coerce"
        )

        df = df.dropna(subset=["id", "multiplier"])
        df = df.sort_values("id", ascending=False).reset_index(drop=True)

    return df


def validate_values(values):

    if not values:
        raise ValueError("Ingiza angalau multiplier moja.")

    clean = []

    for value in values:
        number = float(value)

        if not math.isfinite(number) or number < 1:
            raise ValueError(
                "Multiplier lazima iwe namba halali ya 1.00 au zaidi."
            )

        clean.append(number)

    return clean


# ==========================================
# DESIGN
# ==========================================

st.markdown("""
<style>
.block-container {
    max-width: 850px;
    padding-top: 1.5rem;
    padding-bottom: 3rem;
    padding-left: 1rem;
    padding-right: 1rem;
}
.main-title {
    text-align: center;
    font-size: 30px;
    font-weight: 800;
}
.subtitle {
    text-align: center;
    color: #888;
    margin-bottom: 25px;
}
div.stButton > button {
    width: 100%;
    border-radius: 12px;
    min-height: 48px;
    font-weight: 700;
}
div[data-testid="stMetric"] {
    background: rgba(128,128,128,0.08);
    padding: 12px;
    border-radius: 12px;
}
@media(max-width:600px) {
    .main-title { font-size: 25px; }
    .block-container {
        padding-left: .7rem;
        padding-right: .7rem;
    }
}
</style>
""", unsafe_allow_html=True)


# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:
    st.title("✈️ SmartAviatorAI")
    st.caption(f"Logged in: {st.session_state.user_email}")

    if st.button("🔒 LOGOUT", use_container_width=True):
        st.session_state.access_token = None
        st.session_state.refresh_token = None
        st.session_state.user_id = None
        st.session_state.user_email = None
        st.rerun()


# ==========================================
# HEADER
# ==========================================

st.markdown(
    '<div class="main-title">✈️ SmartAviatorAI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Professional Aviator Analytics | V4.2</div>',
    unsafe_allow_html=True
)

st.warning(
    "Aviator ni mchezo wa bahati nasibu. "
    "Takwimu na historia haziwezi kuhakikisha multiplier ya round inayofuata."
)


# ==========================================
# LOAD USER DATA
# ==========================================

try:
    df = load_data()
except Exception as e:
    st.error(f"Imeshindikana kusoma database: {e}")
    st.stop()

values = (
    df["multiplier"].astype(float)
    if not df.empty
    else pd.Series(dtype=float)
)


# ==========================================
# NAVIGATION
# ==========================================

menu = st.selectbox(
    "SYSTEM MENU",
    [
        "📊 Dashboard",
        "📈 Trend Analysis",
        "🧠 Advanced Analysis",
        "🎯 Prediction Analytics",
        "📋 Round History",
        "⚙️ Settings"
    ]
)


# ==========================================
# INPUT RESULTS
# ==========================================

st.header("📥 Ingiza Matokeo")

manual = st.text_area(
    "Weka multipliers ukitenganisha kwa koma",
    placeholder="1.20, 2.50, 1.05, 4.80"
)

uploaded = st.file_uploader(
    "Au upload CSV",
    type=["csv"],
    key="round_csv"
)

if st.button("💾 SAVE RESULTS", type="primary"):

    try:
        values_to_save = []

        if manual.strip():
            values_to_save.extend([
                float(x.strip())
                for x in manual.split(",")
                if x.strip()
            ])

        if uploaded is not None:
            csv_df = pd.read_csv(uploaded)

            if "multiplier" not in csv_df.columns:
                raise ValueError(
                    "CSV lazima iwe na column inayoitwa multiplier."
                )

            csv_values = pd.to_numeric(
                csv_df["multiplier"],
                errors="coerce"
            )

            if csv_values.isna().any():
                raise ValueError("CSV ina multiplier zisizo sahihi.")

            values_to_save.extend(csv_values.tolist())

        values_to_save = validate_values(values_to_save)

        saved_count = save_rounds(values_to_save)

        st.success(f"✅ Rounds {saved_count} zimehifadhiwa!")
        st.rerun()

    except Exception as e:
        st.error(f"Hitilafu: {e}")


# ==========================================
# DASHBOARD
# ==========================================

if menu == "📊 Dashboard":

    st.header("📊 Main Dashboard")

    if df.empty:
        st.info("Bado hakuna matokeo. Ingiza multipliers kwanza.")

    else:
        st.metric("TOTAL ROUNDS", len(df))

        c1, c2 = st.columns(2)
        c1.metric("AVERAGE", f"{values.mean():.2f}x")
        c2.metric("MEDIAN", f"{values.median():.2f}x")

        c3, c4 = st.columns(2)
        c3.metric("HIGHEST", f"{values.max():.2f}x")
        c4.metric("LOWEST", f"{values.min():.2f}x")

        st.subheader("📈 Historical Trend")

        chart_df = df.sort_values("id").reset_index(drop=True)
        chart_df["Round"] = range(1, len(chart_df) + 1)

        st.line_chart(
            chart_df.set_index("Round")["multiplier"]
        )

        st.subheader("📉 Distribution")

        for level in [1.5, 2, 3, 5, 10]:
            count = int((values >= level).sum())
            percentage = count / len(values) * 100

            st.write(
                f"Rounds ≥ {level}x: {count} ({percentage:.1f}%)"
            )


# ==========================================
# TREND ANALYSIS
# ==========================================

elif menu == "📈 Trend Analysis":

    st.header("📈 Trend Analysis")

    if df.empty:
        st.info("Ingiza multipliers kwanza.")

    else:
        recent = values.head(50)

        st.metric(
            "Recent Average",
            f"{recent.mean():.2f}x"
        )

        st.line_chart(recent.iloc[::-1].reset_index(drop=True))

        st.subheader("Multiplier Categories")

        categories = {
            "Low (1x - 1.99x)": (
                (recent >= 1) & (recent < 2)
            ),
            "Medium (2x - 4.99x)": (
                (recent >= 2) & (recent < 5)
            ),
            "High (5x - 9.99x)": (
                (recent >= 5) & (recent < 10)
            ),
            "Very High (10x+)": recent >= 10
        }

        for name, mask in categories.items():
            count = int(mask.sum())
            st.write(
                f"{name}: {count} rounds "
                f"({count / len(recent) * 100:.1f}%)"
            )


# ==========================================
# ADVANCED ANALYSIS
# ==========================================

elif menu == "🧠 Advanced Analysis":

    st.header("🧠 Advanced Statistical Analysis")

    if df.empty:
        st.info("Ingiza multipliers kwanza.")

    else:
        period = st.selectbox(
            "Analysis Period",
            [20, 50, 100, 500]
        )

        recent = values.head(period)

        a, b, c = st.columns(3)
        a.metric("Average", f"{recent.mean():.2f}x")
        b.metric("Median", f"{recent.median():.2f}x")
        c.metric("Highest", f"{recent.max():.2f}x")

        st.subheader("📊 Recent Trend")
        st.line_chart(recent.iloc[::-1].reset_index(drop=True))

        streak = 0
        for value in recent:
            if value < 2:
                streak += 1
            else:
                break

        st.metric("Consecutive rounds below 2x", streak)

        if len(recent) > 1:
            st.metric(
                "Standard Deviation",
                f"{recent.std():.2f}"
            )

        distribution = []

        for level in [1.5, 2, 3, 5, 10]:
            count = int((recent >= level).sum())

            distribution.append({
                "Multiplier": f"{level}x",
                "Rounds": count,
                "Percentage": round(
                    count / len(recent) * 100, 2
                )
            })

        st.dataframe(
            pd.DataFrame(distribution),
            use_container_width=True,
            hide_index=True
        )


# ==========================================
# PREDICTION ANALYTICS
# ==========================================

elif menu == "🎯 Prediction Analytics":

    st.header("🎯 Prediction Analytics")

    if len(values) < 10:
        st.info(
            "Ingiza angalau rounds 10 ili kupata uchambuzi "
            "wa takwimu za kihistoria."
        )

    else:
        period = st.selectbox(
            "Historical sample",
            [20, 50, 100, 500],
            key="prediction_period"
        )

        recent = values.head(period)

        st.subheader("Historical probability estimates")

        for level in [1.5, 2, 3, 5, 10]:
            count = int((recent >= level).sum())
            rate = count / len(recent) * 100

            st.write(
                f"Matokeo yaliyofikia {level}x: "
                f"{rate:.1f}% ({count}/{len(recent)})"
            )
            st.progress(rate / 100)

        st.subheader("Recent sample statistics")

        st.metric(
            "Sample average",
            f"{recent.mean():.2f}x"
        )

        st.metric(
            "Sample median",
            f"{recent.median():.2f}x"
        )

        st.metric(
            "Sample size",
            len(recent)
        )

        st.warning(
            "Hizi ni asilimia za historia iliyochaguliwa, "
            "si uwezekano wa uhakika wa round inayofuata. "
            "Kila round inaweza kuwa huru na matokeo ya awali."
        )


# ==========================================
# ROUND HISTORY
# ==========================================

elif menu == "📋 Round History":

    st.header("📋 Round History")

    if df.empty:
        st.info("Hakuna historia bado.")

    else:
        limit = st.selectbox(
            "History Size",
            [20, 50, 100, 500]
        )

        st.dataframe(
            df.drop(columns=["user_id"], errors="ignore").head(limit),
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "⬇️ DOWNLOAD CSV",
            df.drop(
                columns=["user_id"], errors="ignore"
            ).to_csv(index=False).encode("utf-8"),
            file_name="smartaviator_history.csv",
            mime="text/csv",
            use_container_width=True
        )


# ==========================================
# SETTINGS
# ==========================================

elif menu == "⚙️ Settings":

    st.header("⚙️ Settings")

    st.metric("TOTAL SAVED ROUNDS", len(df))

    st.success("Database: Supabase PostgreSQL")
    st.success("Authentication: Supabase Auth")
    st.success("Data access: User-specific RLS")

    st.write("System Version: SmartAviatorAI V4.2")
    st.write("Storage: Supabase Cloud Database")
    st.write("Login email:", st.session_state.user_email)

    st.divider()

    st.subheader("📥 Database Backup")

    if not df.empty:
        st.download_button(
            "⬇️ DOWNLOAD BACKUP CSV",
            df.drop(
                columns=["user_id"], errors="ignore"
            ).to_csv(index=False).encode("utf-8"),
            file_name="smartaviator_backup.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("Hakuna data ya kufanya backup.")


# ==========================================
# FOOTER
# ==========================================

st.divider()

st.caption(
    "✈️ SmartAviatorAI V4.2 | "
    "Private Historical Statistics & Analytics"
)