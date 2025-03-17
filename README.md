## 🚀 Chat Application Features

### 🛠️ Functionalities & Solutions Implemented

### 📌 **Group Management**
- Admins can create groups, share invite links, and remove participants.

### 🗑️ **Message Deletion**
- Users can delete messages within **1 minute**, replaced by *"This message was deleted."* in both personal and group chats.

### 📩 **Read & Delivery Tracking**
- Real-time insights on message delivery and read status with timestamps.

### 💬 **Personal Chat from Group**
- Click on a group member's name to start a direct personal chat.

### 🟢 **Online/Offline Status**
- Real-time visibility of user status during personal chats.

### ↩️ **Reply System**
- Users can reply to messages in both personal and group chats.

### 🔔 **Unread Messages Indicator**
- Displays the count of unread messages in group & personal chats.

### 📝 **Last Message Preview**
- Chat home page shows the last message preview for each chat.

### 📢 **Notification System**
- Alerts users about new messages while scrolling in a group chat.

### 🔄 **Efficient Navigation**
- Clicking the unread message alert scrolls to the first unread message.

### ⚡ **Optimized WebSockets**
- High-performance real-time updates ensure a seamless chat experience.

### 🗄️ **Redis-based Presence Tracking**
- Redis CLI tracks online users and opened chat pages, preventing redundant notifications.

---

### 🛠️ **Tech Stack Used**
- **WebSockets** for real-time messaging
- **Redis** for presence tracking
- **Django** for backend
- **Django Templates, HTML, JavaScript, jQuery** for frontend
- **PostgreSQL** for database

### 📌 **Installation & Setup**
```sh
# Clone the repository
git clone https://github.com/your-repo/chat-app.git
cd chat-app

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Start the server
python manage.py runserver
```

### 📜 **License**
This project is licensed under the MIT License.
