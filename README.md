# 📊 Instagram Chat Analyzer

> **Visualize your Instagram conversations with beautiful, interactive charts.**

A privacy-focused tool that transforms your Instagram chat history into insightful visualizations. Built with [Streamlit](https://streamlit.io/) and [Plotly](https://plotly.com/).

## ✨ Key Features

- **🔒 Privacy First**: All processing happens locally in your browser. No data is stored or sent to any server.
- **📈 Interactive Visualizations**:
  - **Activity Heatmap**: track daily text habits.
  - **Hourly Activity**: See when you and your friends are most active during the day.
  - **Weekly Trends**: Track volume changes week-over-week.
  - **Top Emojis**: Discover your most used reactions and emojis.
  - **Top Senders**: Ranking of who talks the most in group chats.
- **📱 Mobile & Dark Mode**: Fully responsive design that looks stunning on all devices.

## 🛠️ Installation & Usage

1. **Clone the repository**

   ```bash
   git clone https://github.com/qasimmansoori/Insta-chat-analyzer.git
   cd Insta-chat-analyzer
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run insta_analyser.py
   ```

## 📥 How to Export Instagram Data

To analyze your chats, you need to export your data from Instagram:

1. Go to **Instagram Settings** → **Account Center** → **Your Information and Permissions**.
2. Select **Export Your Information**.
3. Choose **Create Export** → Select Account → **Export to device**.
4. **Format**: Choose **HTML** (Crucial!) and Download to device.
5. Wait for the email.
6. After receiving the email, go back to settings export page and download your information.
7. Download the zip file, extract it, and find `your_instagram_activity/messages/inbox/[chat_you_want_to_analyze]`. Inside there will be HTML files that you need to upload here.

## 🤝 Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.

---

_Created by [Qasim Mansoori](https://github.com/qasimmansoori) | [Instagram @qasim_244](https://www.instagram.com/qasim_244/)_
