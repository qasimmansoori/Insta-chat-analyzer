import streamlit as st
from bs4 import BeautifulSoup
import re
from collections import Counter
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Instagram Chat Analyser",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #e2e8f0;
    }
    
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
    
    .stFileUploader > div > div {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px dashed #64748b;
        border-radius: 12px;
    }
    .stFileUploader > div > div:hover {
        border-color: #60a5fa;
    }
    
    .streamlit-expanderHeader {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border-radius: 8px !important;
        color: #e2e8f0 !important;
    }
    
    @media only screen and (max-width: 600px) {
        h1 { font-size: 2rem !important; }
    }
</style>
""", unsafe_allow_html=True)

def get_messages_dictionary(uploaded_files, include_reels=False):
    if not uploaded_files:
        return []

    messages = []
    
    # List of known reaction patterns to exclude
    REACTION_PATTERNS = [
        "Reacted", "Liked a message", "Loved a message", 
        "Emphasized a message", "Laughed at a message", 
        "Questioned a message", "Disliked a message"
    ]
    
    for uploaded_file in uploaded_files:
        try:
            string_data = uploaded_file.getvalue().decode("utf-8")
            soup = BeautifulSoup(string_data, 'html.parser')
            
            message_blocks = soup.select('div.pam.uiBoxWhite.noborder')
            
            for msg in message_blocks:
                name_tag = msg.find('h2')
                message_tag = msg.find('div', class_='_3-95 _a6-p')
                time_tag = msg.find('div', class_='_3-94 _a6-o')

                if not (name_tag and message_tag and time_tag):
                    continue
                
                # Extract text content
                text_content = message_tag.get_text(" ", strip=True)
                
                # STRICT REACTION FILTERING
                # Check if the message is just a reaction notification
                is_reaction = any(pattern in text_content for pattern in REACTION_PATTERNS)
                if is_reaction:
                    continue

                # REELS / ATTACHMENTS HANDLING
                has_link = message_tag.find('a') is not None
                is_attachment_text = "sent an attachment" in text_content or "shared a reel" in text_content
                
                if (has_link or is_attachment_text):
                    if not include_reels:
                        continue
                    # If including reels, try to get the link text or formatting
                    if has_link:
                         link_tag = message_tag.find('a')
                         # Use the link content or generic text
                         msg_text = f"Attachment: {link_tag.get_text()}" 
                    else:
                         msg_text = text_content
                else:
                    msg_text = text_content

                messages.append({
                    'name': name_tag.get_text(strip=True),
                    'message': msg_text,
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
    suffix = "AM" if h < 12 else "PM"
    hour12 = h % 12
    if hour12 == 0:
        hour12 = 12
    return f"{hour12} {suffix}"

st.title("Instagram Chat Analyser 🚀")
st.write("Visualize your Instagram chat history in seconds!")

with st.expander("📥 How to get your Instagram chat files? (Click to Expand)", expanded=False):
    st.markdown("""
    1. Go to **Instagram Settings** → **Account Center** → **Your Information and Permissions**.
    2. Select **Export Your Information**.
    3. Choose **Create Export** → Select Account → **Export to device**.
    4. **Format**: Choose **HTML** (Crucial!) and Download to device.
    5. Wait for the email.
    6. After receiving the email, go back to settings export page and download your information.
    7. Download the zip file, extract it, and find `your_instagram_activity/messages/inbox/[chat_you_want_to_analyze]`. Inside there will be HTML files that you need to upload here.
    """)

uploaded_files = st.file_uploader(
    "📂 Drop your `message_1.html` files here to analyze:", 
    type=['html'], 
    accept_multiple_files=True
)

include_reels = st.toggle("Include Reels, Posts & Attachments 📸", value=False)

if uploaded_files:
    with st.spinner("Parsing messages..."):
        messages = get_messages_dictionary(uploaded_files, include_reels)
        
    if messages:
        st.success(f"Successfully loaded {len(messages)} messages!")
        
        rows = []
        for m in messages:
            name = m.get('name') or 'Unknown'
            msg = m.get('message') or ''
            time_str = m.get('time') or ''
            dt = None
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
            st.error("No valid messages found.")
        else:
            df = pd.DataFrame(rows).sort_values('time')

            df['date'] = df['time'].dt.date
            df['month'] = df['time'].dt.strftime('%Y-%m')
            df['month_dt'] = pd.to_datetime(df['month'] + '-01')
            df['day'] = df['time'].dt.day
            df['hour'] = df['time'].dt.hour
            df['weekday'] = df['time'].dt.day_name().str.slice(0,3)

            df['emojis'] = df['message'].apply(extract_emojis)
            emoji_counts = Counter([e for sub in df['emojis'] for e in sub])
            top_emojis = pd.DataFrame(emoji_counts.most_common(), columns=['emoji', 'count'])

            sender_counts = df['name'].value_counts().reset_index()
            sender_counts.columns = ['name', 'count']

            template = "plotly_dark"

            col1, col2, col3 = st.columns(3)

            with col1:
                st.subheader("Top Senders")
                top_n = sender_counts.head(10)
                fig_senders = px.bar(top_n[::-1], x='count', y='name', orientation='h', text='count', template=template)
                fig_senders.update_traces(marker_color='#60a5fa', hovertemplate='%{y}: %{x} msgs')
                st.plotly_chart(fig_senders, use_container_width=True)

            with col2:
                st.subheader("Top Emojis")
                if not top_emojis.empty:
                    top_e = top_emojis.head(15)
                    fig_emojis = px.bar(top_e[::-1], x='count', y='emoji', orientation='h', text='count', template=template)
                    fig_emojis.update_traces(marker_color='#fbbf24', hovertemplate='%{y}: %{x}')
                    st.plotly_chart(fig_emojis, use_container_width=True)
                else:
                    st.write("No emojis found.")

            with col3:
                st.subheader("Activity by Hour")
                hour_counts = df['hour'].value_counts().reindex(range(24), fill_value=0).sort_index().reset_index()
                hour_counts.columns = ['hour', 'count']
                hour_counts['hour_label'] = hour_counts['hour'].apply(hour_label_12h)
                
                fig_hour = px.bar(hour_counts, x='hour_label', y='count', template=template)
                fig_hour.update_traces(marker_color='#34d399', hovertemplate='%{x}: %{y} msgs')
                fig_hour.update_xaxes(categoryorder='array', categoryarray=[hour_label_12h(h) for h in range(24)])
                st.plotly_chart(fig_hour, use_container_width=True)

            col4, col5 = st.columns(2)

            with col4:
                st.subheader("Weekly Activity")
                df_idx = df.set_index('time')
                weekly_total = df_idx.resample('W-MON').size().reset_index(name='count')
                weekly_total.columns = ['week', 'count']
                
                if not weekly_total.empty:
                    fig_weekly = px.bar(weekly_total, x='week', y='count', template=template)
                    fig_weekly.update_traces(marker_color='#60a5fa', hovertemplate='%{y} messages')
                    fig_weekly.update_layout(xaxis_title="Week", yaxis_title="Messages")
                    st.plotly_chart(fig_weekly, use_container_width=True)
                else:
                    st.write("Not enough data for trend.")

            with col5:
                st.subheader("Monthly Growth")
                monthly_counts = df.groupby('month_dt').size().reset_index(name='count').sort_values('month_dt')
                fig_month = px.bar(monthly_counts, x='month_dt', y='count', template=template)
                fig_month.update_traces(marker_color='#a78bfa')
                st.plotly_chart(fig_month, use_container_width=True)
            
            st.subheader("Activity Heatmap (Weekly)")
            
          
            df_heat = df.copy()
            
     
            weekly_data = df_heat.set_index('time').resample('W-MON').size().reset_index(name='count')
            
           
            weekly_data['month_date'] = weekly_data['time'].dt.to_period('M').apply(lambda r: r.start_time)
            
  
            weekly_data['week_rank'] = weekly_data.groupby('month_date').cumcount() + 1
            
        
            weekly_data.loc[weekly_data['week_rank'] > 4, 'week_rank'] = 4
            
    
            weekly_data = weekly_data.groupby(['month_date', 'week_rank'])['count'].sum().reset_index()
            
            
            last_year = weekly_data['month_date'].max() - pd.DateOffset(months=11)
            weekly_data = weekly_data[weekly_data['month_date'] >= last_year]
            
           
            heatmap_pivot = weekly_data.pivot(index='week_rank', columns='month_date', values='count').fillna(0)
            
           
            heatmap_pivot = heatmap_pivot.reindex(range(1, 5), fill_value=0)
            
           
            x_labels = [d.strftime('%b') for d in heatmap_pivot.columns]
            y_labels = ['Week 1', 'Week 2', 'Week 3', 'Week 4']
            
         
            max_val = heatmap_pivot.values.max()
            z_max = max(max_val, 10)
            
            fig_heat = go.Figure(data=go.Heatmap(
                z=heatmap_pivot.values,
                x=x_labels,
                y=y_labels,
                colorscale=[[0, '#161b22'], [0.2, '#0e4429'], [0.4, '#006d32'], [0.6, '#26a641'], [0.8, '#39d353'], [1, '#39d353']],
                showscale=False,
                zmin=0,
                zmax=z_max,
                hovertemplate='Month: %{x}<br>%{y}: %{z} messages<extra></extra>',
                xgap=3,
                ygap=3
            ))
            fig_heat.update_layout(
                template=template,
                height=220, 
                xaxis=dict(side='top', showgrid=False, tickangle=0),
                yaxis=dict(showgrid=False, autorange='reversed', tickfont=dict(size=10)),
                margin=dict(l=50, r=20, t=50, b=20)
            )
            st.plotly_chart(fig_heat, use_container_width=True)

    else:
        st.warning("No messages found.")
else:
    st.info("👆 Upload files to start.")
