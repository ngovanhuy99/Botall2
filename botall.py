import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os
import random
import string
import threading
import requests
import time
from datetime import datetime, timedelta
from flask import Flask
import logging
import urllib.parse
import sys

# ==================== CẤU HÌNH ====================
BOT_TOKEN = "8357910547:AAGdWiYr03KVEu860_lNw3PxNgsG039C5NQ"
CHANNEL = "https://t.me/+pxXrNnB-ciZmZWE1"
CHANNEL_LINK = "https://t.me/+MsSL6BSqpyRkZDJl"

ADMINS = [7071414779, 7071414779]  # Thay bằng ID của bạn
ADMIN_CONTACTS = ["@NguyenTung2029", "@NguyenTung2029"]

# Thông tin ngân hàng cho VietQR
BANK_ID = "708588"          # Mã MB Bank
BANK_NAME = "MBank"
BANK_ACCOUNT = "KO CS"
ACCOUNT_NAME = "NGUYEN THANH TUN"

FLASK_PORT = 8080

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ==================== CẤU HÌNH API GAME ====================
GAME_API = {
    "SUNWIN": "https://apisunbantung-production.up.railway.app",
    "LC79 HŨ": "https://lc79-betvip-api-production.up.railway.app/api/lc79_tx?key=apihdx",
    "LC79 MD5": "https://lc79-betvip-api-production.up.railway.app/api/lc79_md5?key=apihdx",
    "BETVIP HŨ": "https://lc79-betvip-api-production.up.railway.app/api/betvip_tx?key=apihdx",
    "BETVIP MD5": "https://lc79-betvip-api-production.up.railway.app/api/betvip_md5?key=apihdx",
    "XOCDIA88 HŨ": "https://lc79-betvip-api-production.up.railway.app/api/xocdia88_tx?key=apihdx",
    "XOCDIA88 MD5": "https://lc79-betvip-api-production.up.railway.app/api/xocdia88_md5?key=apihdx",
    "XÈNG LIVE HŨ": "https://lc79-betvip-api-production.up.railway.app/api/xenglive_tx?key=apihdx",
    "XÈNG LIVE MD5": "https://lc79-betvip-api-production.up.railway.app/api/xenglive_md5?key=apihdx",
    "789CLUB HŨ": "https://lc79-betvip-api-production.up.railway.app/api/789club_tx?key=apihdx",
    "789CLUB MD5": "https://lc79-betvip-api-production.up.railway.app/api/789club_md5?key=apihdx",
    "B52CLUB HŨ": "https://lc79-betvip-api-production.up.railway.app/api/b52club_tx?key=apihdx",
    "B52CLUB MD5": "https://lc79-betvip-api-production.up.railway.app/api/b52club_md5?key=apihdx",
    "HITCLUB HŨ": "https://lc79-betvip-api-production.up.railway.app/api/hitclub_tx?key=apihdx",
    "HITCLUB MD5": "https://lc79-betvip-api-production.up.railway.app/api/hitclub_md5?key=apihdx",
    "BACARAT": None
}

# ==================== KHỞI TẠO ====================
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
app = Flask(__name__)

pending_bill = {}
pending_support = {}
active_predictions = {}

# ==================== HÀM TIỆN ÍCH JSON ====================
def load_json(filename, default=None):
    if default is None:
        default = {}
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return default
    return default

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

USERS_FILE = 'users.json'
KEYS_FILE = 'keys.json'
DEPOSITS_FILE = 'deposits.json'
TRANSACTIONS_FILE = 'transactions.json'

users = load_json(USERS_FILE, {})
keys_data = load_json(KEYS_FILE, {})
deposits = load_json(DEPOSITS_FILE, [])
transactions = load_json(TRANSACTIONS_FILE, [])

def save_all():
    save_json(USERS_FILE, users)
    save_json(KEYS_FILE, keys_data)
    save_json(DEPOSITS_FILE, deposits)
    save_json(TRANSACTIONS_FILE, transactions)

# ==================== HÀM NGHIỆP VỤ ====================
def generate_key():
    prefix = "HDXTOOLAI"
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
    numeric_part = ''.join(random.choices(string.digits, k=4))
    return f"{prefix}-{random_part}-{numeric_part}"

def create_vietqr_link(amount, content):
    template = "compact"
    encoded_info = urllib.parse.quote(content)
    encoded_name = urllib.parse.quote(ACCOUNT_NAME)
    url = f"https://img.vietqr.io/image/{BANK_ID}-{BANK_ACCOUNT}-{template}.png?amount={amount}&addInfo={encoded_info}&accountName={encoded_name}"
    return url

def is_joined(user_id):
    if user_id in ADMINS:
        return True
    try:
        member = bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Check join error: {e}")
        return False

def get_user(user_id):
    uid = str(user_id)
    if uid not in users:
        users[uid] = {
            "balance": 0,
            "active_key": None,
            "joined_at": datetime.now().isoformat()
        }
        save_all()
    return users[uid]

def update_user_balance(user_id, amount):
    user = get_user(user_id)
    user["balance"] += amount
    save_all()
    return user["balance"]

def log_transaction(user_id, type_, amount, description, ref_id=None):
    trans = {
        "user_id": user_id,
        "type": type_,
        "amount": amount,
        "description": description,
        "ref_id": ref_id,
        "timestamp": datetime.now().isoformat()
    }
    transactions.append(trans)
    save_all()

def create_key_for_user(user_id, package, price, tool_type="general"):
    key = generate_key()
    if package == "12 Giờ":
        expiry = datetime.now() + timedelta(hours=12)
    elif package == "1 Ngày":
        expiry = datetime.now() + timedelta(days=1)
    elif package == "3 Ngày":
        expiry = datetime.now() + timedelta(days=3)
    elif package == "7 Ngày":
        expiry = datetime.now() + timedelta(days=7)
    elif package == "1 Tháng":
        expiry = datetime.now() + timedelta(days=30)
    elif package == "1 Năm":
        expiry = datetime.now() + timedelta(days=365)
    else:
        expiry = datetime.max

    keys_data[key] = {
        "key": key,
        "user_id": user_id,
        "created_at": datetime.now().isoformat(),
        "expiry": expiry.isoformat() if expiry != datetime.max else "forever",
        "package": package,
        "tool_type": tool_type,
        "status": "active"
    }
    user = get_user(user_id)
    user["active_key"] = key
    save_all()
    return key

def is_valid_key(key, user_id):
    if key not in keys_data:
        return False
    info = keys_data[key]
    if info["status"] != "active":
        return False
    if info["user_id"] != user_id:
        return False
    if info["expiry"] != "forever":
        expiry = datetime.fromisoformat(info["expiry"])
        if datetime.now() > expiry:
            info["status"] = "expired"
            save_all()
            return False
    return True

def get_key_expiry_text(key):
    info = keys_data.get(key)
    if not info:
        return "Không có key"
    if info["expiry"] == "forever":
        return "Vĩnh viễn"
    expiry = datetime.fromisoformat(info["expiry"])
    remaining = expiry - datetime.now()
    days = remaining.days
    hours = remaining.seconds // 3600
    minutes = (remaining.seconds % 3600) // 60
    if days > 0:
        return f"{days} ngày {hours} giờ"
    elif hours > 0:
        return f"{hours} giờ {minutes} phút"
    else:
        return f"{minutes} phút"

# ==================== HÀM DỰ ĐOÁN ====================
def get_bacarat_prediction():
    outcomes = ["Banker", "Player", "Tie"]
    prev_phien = random.randint(100000, 999999)
    prev_result = random.choice(outcomes)
    prev_xuc_xac = [random.randint(1, 6) for _ in range(3)]
    prev_tong = sum(prev_xuc_xac)
    current_phien = prev_phien + 1
    prob = random.random()
    if prob < 0.45:
        prediction = "Banker"
    elif prob < 0.9:
        prediction = "Player"
    else:
        prediction = "Tie"
    confidence = random.randint(70, 99)
    return {
        "phien_truoc": prev_phien,
        "ket_qua_truoc": prev_result,
        "xuc_xac_truoc": prev_xuc_xac,
        "tong_truoc": prev_tong,
        "phien_hien_tai": current_phien,
        "du_doan": prediction,
        "do_tin_cay": f"{confidence}%",
        "id": f"BAC{random.randint(1000, 9999)}",
        "ai_model": "BACARAT AI v1.0",
        "self_learning": "Active"
    }

def get_prediction(game):
    if game == "BACARAT":
        return get_bacarat_prediction()
    url = GAME_API.get(game)
    if not url:
        return None
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "phien_truoc": data.get("phien"),
                "ket_qua_truoc": data.get("ket_qua"),
                "xuc_xac_truoc": data.get("xuc_xac"),
                "tong_truoc": data.get("tong"),
                "phien_hien_tai": data.get("phien_hien_tai"),
                "du_doan": data.get("du_doan"),
                "do_tin_cay": data.get("do_tin_cay"),
                "id": data.get("id"),
                "ai_model": data.get("ai_model"),
                "self_learning": data.get("self_learning")
            }
        else:
            return None
    except Exception as e:
        logger.error(f"API request failed for {game}: {e}")
        return None

def format_prediction_message(game, data):
    if not data:
        return f"<b>{game}</b>\n❌ Không thể lấy dữ liệu dự đoán. Vui lòng thử lại sau."
    
    if game == "BACARAT":
        xuc_xac_str = ', '.join(map(str, data['xuc_xac_truoc'])) if data.get('xuc_xac_truoc') else 'N/A'
        return f"""
━━━━━━━━━━━━━━━━━━━
🎲 <b>DỰ ĐOÁN {game}</b>
━━━━━━━━━━━━━━━━━━━

📊 <b>Phiên trước:</b> #{data['phien_truoc']}
🎲 <b>Xúc xắc:</b> {xuc_xac_str}
💰 <b>Tổng:</b> {data['tong_truoc']}
🏆 <b>Kết quả:</b> {data['ket_qua_truoc']}

━━━━━━━━━━━━━━━━━━━
🔮 <b>Phiên hiện tại:</b> #{data['phien_hien_tai']}
🎯 <b>Dự đoán:</b> {data['du_doan']}
📈 <b>Độ tin cậy:</b> {data['do_tin_cay']}

🤖 <b>AI Model:</b> {data['ai_model']}
🔄 <b>Tự học:</b> {data['self_learning']}
👤 <b>ID:</b> {data['id']}
━━━━━━━━━━━━━━━━━━━
⏳ <i>Cập nhật mỗi 3 giây...</i>
"""
    else:
        xuc_xac_str = ', '.join(map(str, data['xuc_xac_truoc'])) if data.get('xuc_xac_truoc') else 'N/A'
        return f"""
━━━━━━━━━━━━━━━━━━━
🎲 <b>DỰ ĐOÁN {game}</b>
━━━━━━━━━━━━━━━━━━━

📊 <b>Phiên trước:</b> #{data['phien_truoc']}
🎲 <b>Xúc xắc:</b> {xuc_xac_str}
💰 <b>Tổng:</b> {data['tong_truoc']}
🏆 <b>Kết quả:</b> {data['ket_qua_truoc']}

━━━━━━━━━━━━━━━━━━━
🔮 <b>Phiên hiện tại:</b> #{data['phien_hien_tai']}
🎯 <b>Dự đoán:</b> {data['du_doan']}
📈 <b>Độ tin cậy:</b> {data['do_tin_cay']}

🤖 <b>AI Model:</b> {data['ai_model']}
🔄 <b>Tự học:</b> {data['self_learning']}
👤 <b>ID:</b> {data['id']}
━━━━━━━━━━━━━━━━━━━
⏳ <i>Cập nhật mỗi 3 giây...</i>
"""

def prediction_loop(user_id, game, chat_id, message_id):
    stop_event = active_predictions[user_id]["stop_event"]
    while not stop_event.is_set():
        data = get_prediction(game)
        if data:
            text = format_prediction_message(game, data)
            try:
                bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=stop_prediction_markup())
            except Exception as e:
                logger.error(f"Edit message error: {e}")
        time.sleep(3)

# ==================== MENU CHÍNH ====================
def main_menu_inline():
    markup = InlineKeyboardMarkup(row_width=2)
    btn1 = InlineKeyboardButton("💰 NẠP TIỀN", callback_data="menu_deposit")
    btn2 = InlineKeyboardButton("🔑 MUA KEY", callback_data="menu_buy_key")
    btn3 = InlineKeyboardButton("🔐 NHẬP KEY", callback_data="menu_enter_key")
    btn4 = InlineKeyboardButton("🧠 SỬ DỤNG TOOL", callback_data="menu_use_tool")
    btn5 = InlineKeyboardButton("💎 BẢNG GIÁ KEY", callback_data="menu_price")
    btn6 = InlineKeyboardButton("📋 THÔNG TIN TK", callback_data="menu_info")
    btn7 = InlineKeyboardButton("📞 LIÊN HỆ ADMIN", callback_data="menu_contact")
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    markup.add(btn5, btn6)
    markup.add(btn7)
    return markup

def game_selection_markup():
    markup = InlineKeyboardMarkup(row_width=3)
    games = [
        "SUNWIN", "LC79 HŨ", "LC79 MD5", "BETVIP HŨ", "BETVIP MD5",
        "XOCDIA88 HŨ", "XOCDIA88 MD5", "XÈNG LIVE HŨ", "XÈNG LIVE MD5",
        "789CLUB HŨ", "789CLUB MD5", "B52CLUB HŨ", "B52CLUB MD5",
        "HITCLUB HŨ", "HITCLUB MD5", "BACARAT"
    ]
    buttons = [InlineKeyboardButton(game, callback_data=f"game_{game}") for game in games]
    markup.add(*buttons)
    return markup

def deposit_confirmation_markup(deposit_id):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ DUYỆT", callback_data=f"approve_deposit_{deposit_id}"))
    markup.add(InlineKeyboardButton("❌ TỪ CHỐI", callback_data=f"reject_deposit_{deposit_id}"))
    return markup

def package_selection_markup():
    markup = InlineKeyboardMarkup(row_width=2)
    packages = [
        ("12 Giờ", 20000, "general"), ("1 Ngày", 35000, "general"), ("3 Ngày", 70000, "general"),
        ("7 Ngày", 150000, "general"), ("1 Tháng", 300000, "general"), ("1 Năm", 400000, "general"),
        ("Vĩnh Viễn", 800000, "general"), ("CASIO VIP", 500000, "casio")
    ]
    for name, price, tool_type in packages:
        markup.add(InlineKeyboardButton(f"{name} - {price:,} VND", callback_data=f"buy_{name}_{price}_{tool_type}"))
    return markup

def stop_prediction_markup():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("⏹️ DỪNG DỰ ĐOÁN", callback_data="stop_prediction"))
    return markup

def join_button():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📌 THAM GIA CHANNEL NGAY", url=CHANNEL_LINK))
    markup.add(InlineKeyboardButton("✅ ĐÃ THAM GIA (XÁC NHẬN)", callback_data="check_join"))
    return markup

JOIN_CAPTION = f"""
━━━━━━━━━━━━━━━━━━━
🚀 <b>YÊU CẦU THAM GIA KÊNH</b>
━━━━━━━━━━━━━━━━━━━

✨ <i>Chào mừng bạn đến với hệ thống BOT VIP!</i>
👉 Vui lòng tham gia kênh chính thức để tiếp tục.

📌 <b>Link tham gia:</b>
➤ {CHANNEL_LINK}

━━━━━━━━━━━━━━━━━━━
⚠️ <b>HƯỚNG DẪN KÍCH HOẠT:</b>
1️⃣ Nhấn vào link để tham gia kênh.
2️⃣ Quay lại đây và nhấn <b>✅ XÁC NHẬN</b>.

💎 <i>Hệ thống sẽ tự động kiểm tra và mở khóa!</i>
━━━━━━━━━━━━━━━━━━━
"""

THANK_CAPTION = """
━━━━━━━━━━━━━━━━━━━
🎉 <b>XÁC NHẬN THÀNH CÔNG</b>
━━━━━━━━━━━━━━━━━━━

💖 Cảm ơn bạn đã đồng hành cùng cộng đồng!

🚀 <b>BOT ĐÃ MỞ KHÓA TOÀN BỘ CHỨC NĂNG</b>

📌 Vui lòng chọn tiện ích trên menu bên dưới để bắt đầu trải nghiệm.

🔥 <i>Chúc bạn có trải nghiệm tuyệt vời!</i>
━━━━━━━━━━━━━━━━━━━
"""

# ==================== XỬ LÝ /START & JOIN ====================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if is_joined(user_id):
        try:
            with open("thankyou.png", "rb") as photo:
                bot.send_photo(message.chat.id, photo, caption=THANK_CAPTION, reply_markup=main_menu_inline())
        except FileNotFoundError:
            bot.send_message(message.chat.id, THANK_CAPTION, reply_markup=main_menu_inline())
    else:
        try:
            with open("checkjoin.png", "rb") as photo:
                bot.send_photo(message.chat.id, photo, caption=JOIN_CAPTION, reply_markup=join_button())
        except FileNotFoundError:
            bot.send_message(message.chat.id, JOIN_CAPTION, reply_markup=join_button())

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def callback_check(call):
    user_id = call.from_user.id
    if is_joined(user_id):
        try:
            bot.answer_callback_query(call.id, "✅ Xác nhận thành công! Chào mừng bạn.")
        except Exception as e:
            logger.error(f"Answer callback query failed: {e}")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        try:
            with open("thankyou.png", "rb") as photo:
                bot.send_photo(call.message.chat.id, photo, caption=THANK_CAPTION, reply_markup=main_menu_inline())
        except FileNotFoundError:
            bot.send_message(call.message.chat.id, THANK_CAPTION, reply_markup=main_menu_inline())
    else:
        try:
            bot.answer_callback_query(call.id, "❌ Bạn chưa tham gia kênh! Vui lòng tham gia rồi ấn lại.", show_alert=True)
        except Exception as e:
            logger.error(f"Answer callback query failed: {e}")

# ==================== XỬ LÝ MENU CHÍNH ====================
@bot.callback_query_handler(func=lambda call: call.data.startswith("menu_"))
def handle_main_menu(call):
    user_id = call.from_user.id
    action = call.data.split("_")[1]
    
    if not is_joined(user_id):
        try:
            bot.answer_callback_query(call.id, "❌ Bạn cần tham gia kênh để sử dụng bot.")
        except Exception as e:
            logger.error(f"Answer callback query failed: {e}")
        return

    if action == "deposit":
        msg = bot.send_message(call.message.chat.id, "💰 <b>Vui lòng nhập số tiền cần nạp (VNĐ):</b>\n<i>(Ví dụ: 50000)</i>", parse_mode="HTML")
        bot.register_next_step_handler(msg, process_deposit_amount, user_id)
        try:
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.error(f"Answer callback query failed: {e}")
        
    elif action == "enter":
        msg = bot.send_message(call.message.chat.id, "🔑 <b>Vui lòng nhập key của bạn (dạng HDXTOOLAI-XXX-XXXX):</b>", parse_mode="HTML")
        bot.register_next_step_handler(msg, process_key_input, user_id)
        try:
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.error(f"Answer callback query failed: {e}")

    elif action == "buy":
        bot.send_message(call.message.chat.id, "💎 <b>Chọn gói key bạn muốn mua:</b>", parse_mode="HTML", reply_markup=package_selection_markup())
        try:
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.error(f"Answer callback query failed: {e}")
        
    elif action == "use":
        user = get_user(user_id)
        if user["active_key"] and is_valid_key(user["active_key"], user_id):
            key_info = keys_data.get(user["active_key"])
            if key_info and key_info.get("tool_type") == "casio":
                bot.send_message(call.message.chat.id, """
━━━━━━━━━━━━━━━━━━━
🔧 <b>TOOL CASIO VIP</b>
━━━━━━━━━━━━━━━━━━━

🎯 <b>Chức năng CASIO chuyên nghiệp:</b>
➤ Giải toán nâng cao
➤ Vẽ đồ thị hàm số
➤ Tính ma trận, số phức
➤ Xác suất thống kê

🚀 <i>Đang phát triển - sắp ra mắt!</i>
━━━━━━━━━━━━━━━━━━━
""", parse_mode="HTML")
            else:
                bot.send_message(call.message.chat.id, "🎮 <b>Vui lòng chọn game bạn muốn sử dụng:</b>", parse_mode="HTML", reply_markup=game_selection_markup())
        else:
            bot.send_message(call.message.chat.id, "❌ Bạn chưa có key hợp lệ. Vui lòng mua key hoặc nhập key để kích hoạt.")
        try:
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.error(f"Answer callback query failed: {e}")
        
    elif action == "price":
        bot.send_message(call.message.chat.id, """
━━━━━━━━━━━━━━━━━━━
💎 <b>BẢNG GIÁ DỊCH VỤ VIP</b>
━━━━━━━━━━━━━━━━━━━

⏱ <b>12 Giờ</b>   ┊ <code>20,000 VND</code>
⏱ <b>1 Ngày</b>    ┊ <code>35,000 VND</code>
⏱ <b>3 Ngày</b>    ┊ <code>70,000 VND</code>
⏱ <b>7 Ngày</b>    ┊ <code>150,000 VND</code>
⏱ <b>1 Tháng</b>   ┊ <code>300,000 VND</code>
⏱ <b>1 Năm</b>     ┊ <code>400,000 VND</code>
♾ <b>Vĩnh Viễn</b> ┊ <code>800,000 VND</code>
🔧 <b>CASIO VIP</b> ┊ <code>500,000 VND</code>

━━━━━━━━━━━━━━━━━━━
🔥 <i>Đầu tư 1 lần - Trải nghiệm mãi mãi!</i>
━━━━━━━━━━━━━━━━━━━
""", parse_mode="HTML")
        try:
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.error(f"Answer callback query failed: {e}")
        
    elif action == "contact":
        contacts = ', '.join(ADMIN_CONTACTS)
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📨 GỬI TIN NHẮN HỖ TRỢ", callback_data="send_support"))
        bot.send_message(call.message.chat.id, f"""
━━━━━━━━━━━━━━━━━━━
📞 <b>THÔNG TIN HỖ TRỢ</b>
━━━━━━━━━━━━━━━━━━━

👤 <b>Quản trị viên:</b> {contacts}

💬 <b>Danh mục hỗ trợ:</b>
➤ Xử lý giao dịch nạp tiền.
➤ Cấp phát và gia hạn Key.
➤ Báo lỗi & Góp ý hệ thống.

🔥 <i>Đội ngũ Admin luôn sẵn sàng hỗ trợ bạn!</i>
━━━━━━━━━━━━━━━━━━━
Nhấn nút bên dưới để gửi tin nhắn trực tiếp đến Admin:
""", parse_mode="HTML", reply_markup=markup)
        try:
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.error(f"Answer callback query failed: {e}")
        
    elif action == "info":
        user = get_user(user_id)
        active_key = user["active_key"]
        if active_key and is_valid_key(active_key, user_id):
            key_info = keys_data[active_key]
            expiry_text = get_key_expiry_text(active_key)
            tool_type = "CASIO" if key_info.get("tool_type") == "casio" else "General Game Tool"
            info_text = f"""
━━━━━━━━━━━━━━━━━━━
📋 <b>THÔNG TIN TÀI KHOẢN</b>
━━━━━━━━━━━━━━━━━━━

🆔 <b>User ID:</b> <code>{user_id}</code>
💰 <b>Số dư:</b> {user['balance']:,} VND

🔑 <b>Key đang dùng:</b> <code>{active_key}</code>
📦 <b>Gói:</b> {key_info['package']}
🛠 <b>Tool:</b> {tool_type}
⏳ <b>Hạn sử dụng:</b> {expiry_text}

━━━━━━━━━━━━━━━━━━━
💡 <i>Nếu key sắp hết, vui lòng mua key mới để tiếp tục trải nghiệm!</i>
━━━━━━━━━━━━━━━━━━━
"""
        else:
            info_text = f"""
━━━━━━━━━━━━━━━━━━━
📋 <b>THÔNG TIN TÀI KHOẢN</b>
━━━━━━━━━━━━━━━━━━━

🆔 <b>User ID:</b> <code>{user_id}</code>
💰 <b>Số dư:</b> {user['balance']:,} VND

🔑 <b>Key đang dùng:</b> Chưa có key hoặc key đã hết hạn

💡 <i>Vui lòng mua key để kích hoạt tính năng VIP!</i>
━━━━━━━━━━━━━━━━━━━
"""
        bot.send_message(call.message.chat.id, info_text, parse_mode="HTML")
        try:
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.error(f"Answer callback query failed: {e}")

# ==================== XỬ LÝ GỬI TIN NHẮN HỖ TRỢ ====================
@bot.callback_query_handler(func=lambda call: call.data == "send_support")
def callback_send_support(call):
    user_id = call.from_user.id
    pending_support[user_id] = "waiting"
    try:
        bot.answer_callback_query(call.id)
    except Exception as e:
        logger.error(f"Answer callback query failed: {e}")
    msg = bot.send_message(call.message.chat.id, "📨 Vui lòng nhập nội dung hỗ trợ của bạn (tối đa 500 ký tự).\nBot sẽ chuyển tiếp đến admin.")
    bot.register_next_step_handler(msg, process_support_message, user_id)

def process_support_message(message, user_id):
    if user_id not in pending_support:
        return
    
    if not message.text:
        bot.send_message(message.chat.id, "❌ Vui lòng chỉ nhập văn bản, không gửi ảnh hoặc sticker.")
        del pending_support[user_id]
        return
        
    content = message.text.strip()
    if not content:
        bot.send_message(message.chat.id, "❌ Nội dung không được để trống.")
        del pending_support[user_id]
        return
        
    for admin_id in ADMINS:
        try:
            bot.send_message(admin_id, f"""
📨 <b>YÊU CẦU HỖ TRỢ TỪ USER</b>
━━━━━━━━━━━━━━━━━━━
👤 User ID: <code>{user_id}</code>
💬 Nội dung:
{content}
━━━━━━━━━━━━━━━━━━━
""", parse_mode="HTML")
        except Exception as e:
            logger.error(f"Gửi hỗ trợ đến admin {admin_id} thất bại: {e}")
            
    bot.send_message(message.chat.id, "✅ Đã gửi yêu cầu hỗ trợ đến admin. Vui lòng chờ phản hồi.")
    del pending_support[user_id]

# ==================== XỬ LÝ NẠP TIỀN ====================
def process_deposit_amount(message, user_id):
    if not message.text:
        bot.send_message(message.chat.id, "❌ Định dạng không hợp lệ, vui lòng chỉ nhập số.")
        return
        
    try:
        amount = int(message.text.strip())
        if amount <= 0:
            raise ValueError
    except:
        bot.send_message(message.chat.id, "❌ Số tiền không hợp lệ. Vui lòng nhập số nguyên dương.")
        return

    content = f"NAP {user_id}"
    qr_link = create_vietqr_link(amount, content)

    deposit_id = len(deposits) + 1
    deposit = {
        "id": deposit_id,
        "user_id": user_id,
        "amount": amount,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    deposits.append(deposit)
    save_all()

    caption = f"""
━━━━━━━━━━━━━━━━━━━
💰 <b>THÔNG TIN NẠP TIỀN</b>
━━━━━━━━━━━━━━━━━━━

🏦 Ngân hàng: <b>{BANK_NAME}</b>
💳 Số tài khoản: <code>{BANK_ACCOUNT}</code>
👤 Chủ tài khoản: <b>{ACCOUNT_NAME}</b>
💰 Số tiền: <b>{amount:,} VND</b>
📝 Nội dung CK: <code>{content}</code>

🔥 <i>Vui lòng quét mã QR hoặc chuyển khoản với nội dung chính xác!</i>
━━━━━━━━━━━━━━━━━━━
"""
    bot.send_photo(message.chat.id, qr_link, caption=caption, parse_mode="HTML")

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ Tôi đã chuyển khoản", callback_data=f"deposited_{deposit_id}"))
    bot.send_message(message.chat.id, "Sau khi chuyển khoản, hãy nhấn nút bên dưới để gửi yêu cầu xác nhận:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("deposited_"))
def callback_deposited(call):
    deposit_id = int(call.data.split("_")[1])
    deposit = next((d for d in deposits if d["id"] == deposit_id), None)
    if not deposit or deposit["status"] != "pending":
        try:
            bot.answer_callback_query(call.id, "Yêu cầu không hợp lệ hoặc đã được xử lý.")
        except Exception as e:
            logger.error(f"Answer callback query failed: {e}")
        return

    user_id = call.from_user.id
    pending_bill[user_id] = deposit_id
    try:
        bot.answer_callback_query(call.id, "📸 Vui lòng gửi ảnh bill chuyển khoản.")
    except Exception as e:
        logger.error(f"Answer callback query failed: {e}")
    bot.send_message(call.message.chat.id, """
━━━━━━━━━━━━━━━━━━━
📸 <b>YÊU CẦU GỬI ẢNH BILL</b>
━━━━━━━━━━━━━━━━━━━

Vui lòng gửi ảnh chụp màn hình giao dịch chuyển khoản thành công.

📌 <b>Yêu cầu ảnh:</b>
➤ Hiển thị rõ số tiền
➤ Hiển thị nội dung chuyển khoản
➤ Hiển thị thời gian giao dịch

⏳ Sau khi gửi ảnh, admin sẽ xử lý yêu cầu nạp tiền của bạn.
━━━━━━━━━━━━━━━━━━━
""", parse_mode="HTML")
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except:
        pass

@bot.message_handler(content_types=['photo'])
def handle_bill_photo(message):
    user_id = message.from_user.id
    if user_id not in pending_bill:
        return

    deposit_id = pending_bill.pop(user_id)
    deposit = next((d for d in deposits if d["id"] == deposit_id), None)
    if not deposit or deposit["status"] != "pending":
        bot.send_message(message.chat.id, "❌ Yêu cầu nạp không hợp lệ hoặc đã được xử lý.")
        return

    photo = message.photo[-1]
    file_id = photo.file_id
    deposit["bill_photo"] = file_id
    save_all()

    for admin_id in ADMINS:
        try:
            bot.send_photo(admin_id, file_id, caption=f"""
🔔 <b>YÊU CẦU NẠP TIỀN MỚI (kèm bill)</b>
━━━━━━━━━━━━━━━━━━━
👤 User: <code>{user_id}</code>
💰 Số tiền: {deposit['amount']:,} VND
🆔 Mã yêu cầu: #{deposit_id}
📸 Bill đã được đính kèm.
""", parse_mode="HTML", reply_markup=deposit_confirmation_markup(deposit_id))
        except Exception as e:
            logger.error(f"Gửi bill đến admin {admin_id} thất bại: {e}")

    bot.send_message(message.chat.id, f"✅ <b>Đã nhận ảnh bill!</b>\n💰 Số tiền: {deposit['amount']:,} VND\n📸 Bill của bạn đã được gửi đến admin để xử lý.", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_deposit_") or call.data.startswith("reject_deposit_"))
def callback_admin_deposit(call):
    admin_id = call.from_user.id
    if admin_id not in ADMINS:
        try:
            bot.answer_callback_query(call.id, "❌ Bạn không có quyền thực hiện thao tác này.")
        except Exception as e:
            logger.error(f"Answer callback query failed: {e}")
        return

    parts = call.data.split("_")
    action = parts[0]
    deposit_id = int(parts[2])

    deposit = next((d for d in deposits if d["id"] == deposit_id), None)
    if not deposit or deposit["status"] != "pending":
        try:
            bot.answer_callback_query(call.id, "Yêu cầu đã được xử lý hoặc không tồn tại.")
        except Exception as e:
            logger.error(f"Answer callback query failed: {e}")
        return

    user_id = deposit["user_id"]
    if action == "approve":
        new_balance = update_user_balance(user_id, deposit["amount"])
        deposit["status"] = "approved"
        log_transaction(user_id, "deposit", deposit["amount"], f"Nạp tiền qua admin duyệt", deposit_id)
        save_all()
        bot.send_message(user_id, f"""
━━━━━━━━━━━━━━━━━━━
✅ <b>YÊU CẦU NẠP TIỀN ĐÃ ĐƯỢC DUYỆT</b>
━━━━━━━━━━━━━━━━━━━

💰 Số tiền: <b>{deposit['amount']:,} VND</b>
💎 Số dư hiện tại: <b>{new_balance:,} VND</b>

🔥 <i>Bạn có thể mua key ngay bây giờ!</i>
━━━━━━━━━━━━━━━━━━━
""", parse_mode="HTML")
        try:
            bot.answer_callback_query(call.id, "Đã duyệt và cộng tiền.")
        except Exception as e:
            logger.error(f"Answer callback query failed: {e}")
    else:
        deposit["status"] = "rejected"
        save_all()
        contacts = ', '.join(ADMIN_CONTACTS)
        bot.send_message(user_id, f"""
━━━━━━━━━━━━━━━━━━━
❌ <b>YÊU CẦU NẠP TIỀN BỊ TỪ CHỐI</b>
━━━━━━━━━━━━━━━━━━━

💰 Số tiền: <b>{deposit['amount']:,} VND</b>
📞 Lý do: <i>Vui lòng liên hệ admin để biết chi tiết</i>

👤 Admin: {contacts}
━━━━━━━━━━━━━━━━━━━
""", parse_mode="HTML")
        try:
            bot.answer_callback_query(call.id, "Đã từ chối yêu cầu.")
        except Exception as e:
            logger.error(f"Answer callback query failed: {e}")

    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except:
        pass

# ==================== XỬ LÝ MUA KEY & NHẬP KEY ====================
@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def callback_buy_key(call):
    user_id = call.from_user.id
    _, package_name, price_str, tool_type = call.data.split("_")
    price = int(price_str)
    user = get_user(user_id)
    if user["balance"] < price:
        try:
            bot.answer_callback_query(call.id, f"❌ Số dư không đủ. Cần nạp thêm {price - user['balance']:,} VND.", show_alert=True)
        except Exception as e:
            logger.error(f"Answer callback query failed: {e}")
        return

    user["balance"] -= price
    key = create_key_for_user(user_id, package_name, price, tool_type)
    log_transaction(user_id, "purchase", -price, f"Mua key {package_name} - {key}", key)
    save_all()

    bot.send_message(call.message.chat.id, f"""
━━━━━━━━━━━━━━━━━━━
🎉 <b>CHÚC MỪNG BẠN ĐÃ MUA KEY THÀNH CÔNG!</b>
━━━━━━━━━━━━━━━━━━━

🔑 <b>Key của bạn:</b> <code>{key}</code>
⏱ <b>Gói:</b> {package_name}
🛠 <b>Tool:</b> {'CASIO VIP' if tool_type == 'casio' else 'General Game Tool'}
💰 <b>Đã trừ:</b> {price:,} VND
💎 <b>Số dư còn lại:</b> {user['balance']:,} VND

🔥 <i>Key đã tự động được liên kết. Chọn SỬ DỤNG TOOL để bắt đầu!</i>
━━━━━━━━━━━━━━━━━━━
""", parse_mode="HTML")
    try:
        bot.answer_callback_query(call.id, "Mua key thành công! Key đã được gửi.")
    except Exception as e:
        logger.error(f"Answer callback query failed: {e}")

def process_key_input(message, user_id):
    if not message.text:
        bot.send_message(message.chat.id, "❌ Vui lòng nhập văn bản chứa Key.")
        return
        
    key = message.text.strip()
    if key not in keys_data:
        bot.send_message(message.chat.id, "❌ Key không tồn tại. Vui lòng kiểm tra lại.")
        return
    info = keys_data[key]
    if info["status"] != "active":
        bot.send_message(message.chat.id, "❌ Key đã hết hạn hoặc bị vô hiệu hóa.")
        return
    if info["user_id"] != user_id:
        if info["user_id"] == 0:
            info["user_id"] = user_id
            save_all()
        else:
            bot.send_message(message.chat.id, "❌ Key này đã được kích hoạt bởi người dùng khác.")
            return
            
    user = get_user(user_id)
    user["active_key"] = key
    save_all()
    bot.send_message(message.chat.id, f"""
✅ <b>Kích hoạt key thành công!</b>
🔑 Key: <code>{key}</code>
🎉 Chào mừng bạn đến với hệ thống VIP.
""", parse_mode="HTML")
    bot.send_message(message.chat.id, "Hãy chọn chức năng bên dưới:", reply_markup=main_menu_inline())

# ==================== XỬ LÝ GAME (DỰ ĐOÁN) ====================
@bot.callback_query_handler(func=lambda call: call.data.startswith("game_"))
def callback_game(call):
    user_id = call.from_user.id
    game = call.data.split("_")[1]

    user = get_user(user_id)
    if not user["active_key"] or not is_valid_key(user["active_key"], user_id):
        try:
            bot.answer_callback_query(call.id, "❌ Bạn chưa có key hợp lệ để sử dụng tool.")
        except Exception as e:
            logger.error(f"Answer callback query failed: {e}")
        return

    if user_id in active_predictions:
        active_predictions[user_id]["stop_event"].set()
        active_predictions[user_id]["thread"].join(timeout=1)
        del active_predictions[user_id]

    data = get_prediction(game)
    if not data:
        bot.send_message(call.message.chat.id, f"❌ Không thể lấy dữ liệu dự đoán cho {game}. Vui lòng thử lại sau.")
        return

    text = format_prediction_message(game, data)
    msg = bot.send_message(call.message.chat.id, text, parse_mode="HTML", reply_markup=stop_prediction_markup())

    stop_event = threading.Event()
    prediction_thread = threading.Thread(
        target=prediction_loop,
        args=(user_id, game, msg.chat.id, msg.message_id),
        daemon=True
    )
    active_predictions[user_id] = {
        "thread": prediction_thread,
        "stop_event": stop_event,
        "message_id": msg.message_id,
        "chat_id": msg.chat.id,
        "game": game
    }
    prediction_thread.start()

    try:
        bot.answer_callback_query(call.id, f"Đã bắt đầu dự đoán cho {game}")
    except Exception as e:
        logger.error(f"Answer callback query failed: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "stop_prediction")
def callback_stop_prediction(call):
    user_id = call.from_user.id
    if user_id in active_predictions:
        active_predictions[user_id]["stop_event"].set()
        active_predictions[user_id]["thread"].join(timeout=1)
        del active_predictions[user_id]
        try:
            bot.answer_callback_query(call.id, "Đã dừng dự đoán.")
        except Exception as e:
            logger.error(f"Answer callback query failed: {e}")
        try:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        except:
            pass
        bot.send_message(call.message.chat.id, "⏹️ Đã dừng cập nhật dự đoán.")
    else:
        try:
            bot.answer_callback_query(call.id, "Không có dự đoán nào đang chạy.")
        except Exception as e:
            logger.error(f"Answer callback query failed: {e}")

# ==================== ADMIN COMMANDS ====================
@bot.message_handler(commands=['addmoney'])
def admin_add_money(message):
    if message.from_user.id not in ADMINS:
        bot.reply_to(message, "❌ Bạn không có quyền Admin.")
        return
    parts = message.text.split()
    if len(parts) != 3:
        bot.reply_to(message, "⚠️ Cú pháp: /addmoney <user_id> <số_tiền>")
        return
    try:
        user_id = int(parts[1])
        amount = int(parts[2])
    except:
        bot.reply_to(message, "❌ Sai định dạng. User ID và số tiền phải là số.")
        return
    new_balance = update_user_balance(user_id, amount)
    log_transaction(user_id, "admin_add", amount, f"Admin cộng tiền: {amount}", None)
    bot.reply_to(message, f"✅ Đã cộng {amount:,} VND cho user {user_id}. Số dư hiện tại: {new_balance:,} VND.")
    try:
        bot.send_message(user_id, f"💰 Admin đã cộng {amount:,} VND vào tài khoản của bạn. Số dư: {new_balance:,} VND.")
    except:
        pass

@bot.message_handler(commands=['keys'])
def admin_keys(message):
    if message.from_user.id not in ADMINS:
        bot.reply_to(message, "❌ Bạn không có quyền Admin.")
        return
    if not keys_data:
        bot.reply_to(message, "Chưa có key nào.")
        return
    text = "📋 Danh sách key:\n"
    for key, info in keys_data.items():
        text += f"🔑 {key} - User: {info['user_id']} - Gói: {info['package']} - Hết hạn: {info['expiry']}\n"
    bot.reply_to(message, text[:4000])

@bot.message_handler(commands=['revenue'])
def admin_revenue(message):
    if message.from_user.id not in ADMINS:
        bot.reply_to(message, "❌ Bạn không có quyền Admin.")
        return
    total_deposit = sum(t["amount"] for t in transactions if t["type"] == "deposit")
    total_purchase = sum(-t["amount"] for t in transactions if t["type"] == "purchase")
    bot.reply_to(message, f"""
📊 <b>THỐNG KÊ DOANH THU</b>
━━━━━━━━━━━━━━━━━━━
💰 Tổng nạp: {total_deposit:,} VND
💸 Tổng mua key: {total_purchase:,} VND
📈 Lợi nhuận (tạm tính): {total_deposit - total_purchase:,} VND
""", parse_mode="HTML")

@bot.message_handler(commands=['users'])
def admin_users(message):
    if message.from_user.id not in ADMINS:
        bot.reply_to(message, "❌ Bạn không có quyền Admin.")
        return
    if not users:
        bot.reply_to(message, "Chưa có user nào.")
        return
    text = "👥 Danh sách user:\n"
    for uid, info in users.items():
        text += f"ID: {uid} | Số dư: {info['balance']:,} | Key: {info['active_key'] or 'Chưa có'}\n"
    bot.reply_to(message, text[:4000])

@bot.message_handler(commands=['broadcast'])
def admin_broadcast(message):
    if message.from_user.id not in ADMINS:
        bot.reply_to(message, "❌ Bạn không có quyền Admin.")
        return
    msg = message.text.split(' ', 1)
    if len(msg) < 2:
        bot.reply_to(message, "⚠️ Cú pháp: /broadcast <nội dung>")
        return
    content = msg[1]
    count = 0
    for uid in users:
        try:
            bot.send_message(int(uid), content)
            count += 1
        except:
            pass
    bot.reply_to(message, f"✅ Đã gửi broadcast tới {count} user.")

@bot.message_handler(commands=['helpadmin'])
def admin_help(message):
    if message.from_user.id not in ADMINS:
        bot.reply_to(message, f"❌ Bạn không có quyền sử dụng lệnh này.\n(ID của bạn là: {message.from_user.id}. Hãy thêm ID này vào danh sách ADMINS trong code để mở khóa quyền Admin)")
        return
    bot.reply_to(message, """
📌 <b>LỆNH ADMIN</b>
/addmoney &lt;user_id&gt; &lt;số_tiền&gt; : Cộng tiền trực tiếp
/keys : Xem danh sách key
/revenue : Xem tổng doanh thu
/users : Xem danh sách user
/broadcast &lt;nội dung&gt; : Gửi tin nhắn tới tất cả user
/helpadmin : Hiển thị trợ giúp
""", parse_mode="HTML")

# ==================== FLASK KEEP-ALIVE ====================
@app.route('/')
def index():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=FLASK_PORT, threaded=True)

# ==================== KHỞI CHẠY VỚI RESTART ====================
def run_bot_with_restart():
    while True:
        try:
            logger.info("Bot đang chạy polling...")
            # Tăng timeout để tránh lỗi timeout, sử dụng skip_pending để bỏ qua các update cũ
            bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True)
        except Exception as e:
            logger.error(f"Bot polling crashed: {e}. Restarting in 10 seconds...")
            time.sleep(10)

if __name__ == "__main__":
    # Chạy Flask trong một thread riêng
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info(f"Flask server đang chạy trên cổng {FLASK_PORT}...")
    
    # Chạy bot với cơ chế restart tự động
    run_bot_with_restart()