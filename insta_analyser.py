import streamlit as st
from bs4 import BeautifulSoup
import re
from collections import Counter
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# -----------------------------------------------------------------------------
# 1. Page Configuration & Custom CSS (Mobile-First + Premium UI)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Instagram Chat Analyser",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for a premium, modern, and mobile-friendly look
st.markdown("""
<style>
    /* Global Font & Colors */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Background & Main Container */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #e2e8f0;
    }
    
    /* Headings */
    h1, h2, h3 {
        color: #f8fafc !important;
        font-weight: 700 !important;
    }
    h1 {
        text-align: center;
        margin-bottom: 30px !important;
        background: -webkit-linear-gradient(45deg, #60a5fa, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Block Containers (Glassmorphism) */
    .stMarkdown, .stPlotlyChart {
         /* Ensure charts don't get cut off on mobile */
    }
    
    /* File Uploader */
    .stFileUploader > div > div {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px dashed #64748b;
        border-radius: 12px;
    }
    .stFileUploader > div > div:hover {
        border-color: #60a5fa;
    }
    
    /* Expanders (Instructions) */
    .streamlit-expanderHeader {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border-radius: 8px !important;
        color: #e2e8f0 !important;
    }
    
    /* Mobile Updates: Center align text on small screens if needed, ensure padding */
    @media only screen and (max-width: 600px) {
        h1 { font-size: 2rem !important; }
        .stPlotlyChart { height: 400px !important; }
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. Parsing Logic
# -----------------------------------------------------------------------------

def get_messages_dictionary(uploaded_files):
    """
    Parses a list of uploaded Streamlit file objects (HTML).
    Returns a list of message dictionaries.
    """
    if not uploaded_files:
        return []

    messages = []
    
    for uploaded_file in uploaded_files:
        # Streamlit uploaded files are bytes-like; read and decode
        try:
            string_data = uploaded_file.getvalue().decode("utf-8")
            soup = BeautifulSoup(string_data, 'html.parser')
            
            # Select message blocks
            message_blocks = soup.select('div.pam.uiBoxWhite.noborder')
            
            for msg in message_blocks:
                text = msg.get_text(" ", strip=True)

                # Skip reacted messages or those with links/reels
                if ("Reacted" in text and "to your message" in text) or msg.find('a'):
                    continue

                # Extract safely
                name_tag = msg.find('h2')
                message_tag = msg.find('div', class_='_3-95 _a6-p')
                time_tag = msg.find('div', class_='_3-94 _a6-o')

                if not (name_tag and message_tag and time_tag):
                    continue  # skip incomplete blocks

                messages.append({
                    'name': name_tag.get_text(strip=True),
                    'message': message_tag.get_text(strip=True),
                    'time': time_tag.get_text(strip=True)
                })
        except Exception as e:
            st.warning(f"Could not parse file {uploaded_file.name}: {e}")
            continue

    return messages

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\u2600-\u26FF"
    "\u2700-\u27BF"
    "]+", flags=re.UNICODE
)

def extract_emojis(text):
    if not isinstance(text, str):
        return []
    return EMOJI_PATTERN.findall(text)

def hour_label_12h(h):
    """Return 12-hour label for integer hour 0..23, e.g. 0 -> '12 AM', 13 -> '1 PM'."""
    suffix = "AM" if h < 12 else "PM"
    hour12 = h % 12
    if hour12 == 0:
        hour12 = 12
    return f"{hour12} {suffix}"

# -----------------------------------------------------------------------------
# 3. Dashboard Logic
# -----------------------------------------------------------------------------

def build_dashboard(messages, title="Messages Analysis Dashboard", template="plotly_dark", top_senders_n=10):
    """
    messages: list of dicts with keys 'name', 'message', 'time'
    returns: Plotly Figure
    """
    # --- Normalize into DataFrame
    rows = []
    for m in messages:
        name = m.get('name') or 'Unknown'
        msg = m.get('message') or ''
        time_str = m.get('time') or ''
        dt = None
        # Try various formats
        for fmt in ("%b %d, %Y %I:%M %p", "%Y-%m-%d %H:%M:%S", "%d %b %Y %H:%M", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(time_str, fmt)
                break
            except Exception:
                continue
        if dt is None:
            dt = pd.to_datetime(time_str, errors='coerce')
            
        if pd.notnull(dt):
            rows.append({
                'name': name,
                'message': msg,
                'time': pd.to_datetime(dt),
                'length': len(msg)
            })

    if not rows:
        st.error("No valid messages found. Please check your HTML files.")
        return None

    df = pd.DataFrame(rows).sort_values('time')

    # --- Derived columns
    df['date'] = df['time'].dt.date
    df['month'] = df['time'].dt.strftime('%Y-%m')
    df['month_dt'] = pd.to_datetime(df['month'] + '-01')
    df['day'] = df['time'].dt.day
    df['hour'] = df['time'].dt.hour
    df['weekday'] = df['time'].dt.day_name().str.slice(0,3)

    # Extract emojis
    df['emojis'] = df['message'].apply(extract_emojis)
    emoji_counts = Counter([e for sub in df['emojis'] for e in sub])
    top_emojis = pd.DataFrame(emoji_counts.most_common(), columns=['emoji', 'count'])

    # Top senders
    sender_counts = df['name'].value_counts().reset_index()
    sender_counts.columns = ['name', 'count']

    # --- Weekly trend per top senders
    df_idx = df.set_index('time')
    weekly_all = df_idx.groupby('name').resample('W-MON').size().reset_index(name='count')
    top_senders = sender_counts['name'].head(5).tolist() # Expanded to 5 for better insight
    weekly_top = weekly_all[weekly_all['name'].isin(top_senders)].copy()
    weekly_pivot = weekly_top.pivot(index='time', columns='name', values='count').fillna(0)

    # --- Monthly heatmap
    monthly_pivot = df.groupby(['day', 'month']).size().unstack(fill_value=0)
    all_days = pd.Index(range(1,32), name='day')
    monthly_pivot = monthly_pivot.reindex(all_days, fill_value=0)
    month_cols = sorted(monthly_pivot.columns, key=lambda x: pd.to_datetime(x + '-01'))
    monthly_pivot = monthly_pivot[month_cols]

    # --- Messages by hour
    hour_counts = df['hour'].value_counts().reindex(range(24), fill_value=0).reset_index()
    hour_counts.columns = ['hour', 'count']
    hour_counts['hour_label'] = hour_counts['hour'].apply(hour_label_12h)
    hour_counts['hour_label'] = pd.Categorical(hour_counts['hour_label'],
                                              categories=[hour_label_12h(h) for h in range(24)],
                                              ordered=True)
    peak_hour = hour_counts.loc[hour_counts['count'].idxmax()]

    # --- Avg message length
    avg_len = df.groupby('name')['length'].mean().reset_index().sort_values('length', ascending=False)
    top_len = avg_len.head(top_senders_n)

    # --- Build subplot layout
    # On mobile, plotly subplots can be small, but making the figure tall helps
    fig = make_subplots(
        rows=3, cols=3,
        column_widths=[0.33, 0.33, 0.34],
        row_heights=[0.33, 0.33, 0.34],
        vertical_spacing=0.1,
        horizontal_spacing=0.05,
        specs=[
            [{"type":"xy"}, {"type":"xy"}, {"type":"xy"}],
            [{"type":"xy"}, {"type":"xy"}, {"type":"xy"}],
            [{"type":"xy"}, {"type":"xy"}, {"type":"xy"}],
        ],
        subplot_titles=(
            "Top Senders", "Top Emojis", "Activity by Hour",
            "Weekly Messaging Trend", "Daily Activity Heatmap", "Monthly Growth",
            "Avg Message Length", "Top Emojis (Compact)", ""
        )
    )

    # 1. Top senders
    top_n = sender_counts.head(top_senders_n)
    bar1 = px.bar(top_n[::-1], x='count', y='name', orientation='h', text='count', template=template)
    bar1.update_traces(marker_color='#60a5fa', hovertemplate='%{y}: %{x} msgs', showlegend=False)
    for trace in bar1.data:
        fig.add_trace(trace, row=1, col=1)

    # 2. Top emojis
    if not top_emojis.empty:
        top_e = top_emojis.head(15)
        bar2 = px.bar(top_e[::-1], x='count', y='emoji', orientation='h', text='count', template=template)
        bar2.update_traces(marker_color='#fbbf24', hovertemplate='%{y}: %{x}', showlegend=False)
        for trace in bar2.data:
            fig.add_trace(trace, row=1, col=2)
    else:
        fig.add_trace(go.Scatter(x=[0], y=[0], mode='markers', marker_opacity=0), row=1, col=2)

    # 3. By Hour
    bar_hour = px.bar(hour_counts, x='hour_label', y='count', template=template)
    bar_hour.update_traces(marker_color='#34d399', hovertemplate='%{x}: %{y} msgs', showlegend=False)
    for trace in bar_hour.data:
        fig.add_trace(trace, row=1, col=3)
    fig.add_annotation(
        x=peak_hour['hour_label'], y=peak_hour['count'],
        text=f"Peak: {peak_hour['hour_label']}",
        showarrow=True, arrowhead=2, ax=0, ay=-40,
        row=1, col=3
    )

    # 4. Weekly Trend (Lines)
    color_seq = px.colors.qualitative.Pastel
    if not weekly_pivot.empty:
        senders = list(weekly_pivot.columns)
        for i, sender in enumerate(senders):
            color = color_seq[i % len(color_seq)]
            fig.add_trace(
                go.Scatter(
                    x=weekly_pivot.index, y=weekly_pivot[sender],
                    mode='lines+markers', name=sender,
                    line=dict(width=2),
                    marker=dict(size=5),
                    hovertemplate=f"{sender}: %{{y}}",
                    showlegend=True
                ),
                row=2, col=1
            )
    else:
        fig.add_trace(go.Scatter(x=[0], y=[0], mode='markers', marker_opacity=0), row=2, col=1)

    # 5. Heatmap
    z = monthly_pivot.values
    x = monthly_pivot.columns.tolist()
    y = monthly_pivot.index.tolist()
    hm = go.Heatmap(
        z=z, x=x, y=y,
        colorscale='Viridis',
        colorbar=dict(title='Msgs'),
        hovertemplate='%{x} Day %{y}: %{z}',
        showscale=True
    )
    fig.add_trace(hm, row=2, col=2)

    # 6. Monthly Growth
    monthly_counts = df.groupby('month_dt').size().reset_index(name='count').sort_values('month_dt')
    bar_month = px.bar(monthly_counts, x='month_dt', y='count', template=template)
    bar_month.update_traces(marker_color='#a78bfa', hovertemplate='%{x}: %{y}', showlegend=False)
    for trace in bar_month.data:
        fig.add_trace(trace, row=2, col=3)

    # 7. Avg Length
    top_len_plot = top_len.head(top_senders_n)
    bar_len = px.bar(top_len_plot[::-1], x='length', y='name', orientation='h', template=template)
    bar_len.update_traces(marker_color='#2dd4bf', hovertemplate='%{y}: %{x} chars', showlegend=False)
    for trace in bar_len.data:
        fig.add_trace(trace, row=3, col=1)

    # 8. Compact Emojis (Smaller)
    if not top_emojis.empty:
        top_e2 = top_emojis.head(10)
        bar_e_small = px.bar(top_e2[::-1], x='count', y='emoji', orientation='h', template=template)
        bar_e_small.update_traces(marker_color='#fbbf24', showlegend=False)
        for trace in bar_e_small.data:
            fig.add_trace(trace, row=3, col=2)
    else:
        fig.add_trace(go.Scatter(x=[0], y=[0], mode='markers', marker_opacity=0), row=3, col=2)

    fig.update_layout(
        height=1400, # Taller for mobile scrolling
        title_text=title,
        template=template,
        showlegend=True,
        margin=dict(t=80, l=40, r=20, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig

# -----------------------------------------------------------------------------
# 4. Main App UI
# -----------------------------------------------------------------------------

st.title("Instagram Chat Analyser 🚀")
st.write("Visualize your Instagram chat history in seconds! Privacy-friendly: everything runs locally in your browser/server.")

# Instructions Expander
with st.expander("📥 How to get your Instagram chat files? (Click to Expand)", expanded=False):
    st.markdown("""
    ### 1. Request Your Data
    1. Go to **Instagram Settings** -> **Your Information and Permissions**.
    2. Select **Download Your Information**.
    3. Choose **Download or transfer information** -> Select focus on **Messages**.
    4. **Format**: Choose **HTML** (Crucial!) and Download to device.
    5. Wait for the email from Instagram (can take minutes to hours).

    ### 2. Extract & Locate
    1. Download the `.zip` file from the email.
    2. Extract it. Navigate to `your_instagram_activity/messages/inbox/`.
    3. You will see folders for each chat. Inside are files like `message_1.html`.
    
    ### 3. Upload Below
    - Select one or multiple `message_X.html` files from the same chat folder to analyze the full usage.
    """)

# File Uploader
uploaded_files = st.file_uploader(
    "📂 Drop your `message_1.html` files here to analyze:", 
    type=['html'], 
    accept_multiple_files=True
)

if uploaded_files:
    with st.spinner("Parsing messages..."):
        messages = get_messages_dictionary(uploaded_files)
        
    if messages:
        st.success(f"Successfully loaded {len(messages)} messages! Generating dashboard...")
        
        # Build Dashboard
        try:
            fig = build_dashboard(messages, title="Conversations Overview")
            if fig:
                # Use container width ensuring mobile responsiveness
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating dashboard: {e}")
            st.write("Please ensure the HTML files are from Instagram 'Messages' download format.")
    else:
        st.warning("No messages could be extracted. Are you sure these are Instagram chat HTML files?")
else:
    # Empty State / Landing
    st.info("👆 Upload your files above to see the magic happen!")
