# imghdr shim: provide imghdr.what() using Pillow if the stdlib imghdr module is missing.
# This must be at the very top so any downstream imports using imghdr find it.
import sys
try:
    import imghdr  # try standard library first
except ModuleNotFoundError:
    try:
        from PIL import Image
    except Exception as e:
        raise RuntimeError("Pillow is required as a fallback for imghdr. Add 'Pillow' to requirements.txt.") from e
    import types
    import io as _io
    def _what(file, h=None):
        try:
            # determine bytes to inspect
            if h is not None:
                data = h
            else:
                # file can be a path or file-like object
                if isinstance(file, (str, bytes, bytearray)):
                    # treat as filename/path
                    with open(file, "rb") as f:
                        data = f.read(64)
                elif hasattr(file, "read"):
                    pos = None
                    try:
                        pos = file.tell()
                    except Exception:
                        pos = None
                    data = file.read(64)
                    if pos is not None:
                        try:
                            file.seek(pos)
                        except Exception:
                            pass
                else:
                    return None
            if not isinstance(data, (bytes, bytearray)):
                return None
            img = Image.open(_io.BytesIO(data))
            fmt = (img.format or "").lower()
            # return common imghdr type names
            mapping = {
                "jpeg": "jpeg",
                "png": "png",
                "gif": "gif",
                "bmp": "bmp",
                "webp": "webp",
                "tiff": "tiff",
            }
            return mapping.get(fmt)
        except Exception:
            return None
    mod = types.ModuleType("imghdr")
    mod.what = _what
    sys.modules["imghdr"] = mod
    imghdr = mod

import logging
import sqlite3
import time
import os
import re
import threading
import sys
import requests
import hashlib
import random
import zipfile
import io
import asyncio
from datetime import datetime, timedelta
from io import BytesIO
from bs4 import BeautifulSoup
from telegram import CopyTextButton
import json

# ---- PTB Imports ----
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.error import BadRequest

# ---- Main Configuration ----
BOT_NAME = "MaLiKoTpZoNe"
DB_FILE = "numbers.db"

# ---- Configure Logging ----
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

logging.getLogger("httpx").setLevel(logging.WARNING)

API_TOKEN = "8531523678:AAFXHiumK5Ho8dyuPneq7i_k_h8xFPl1jck"
ADMIN_IDS = [7500869913, 8365961338]

# --- Api 1
T1 = "YOUR_PANEL_API"
URL_API_1 = "http://139.99.63.204/crapi/dgroup/viewstats"
TYPE_API_1 = "DICT"

# --- Api 2
T2 = "YOUR_PANEL_API"
URL_API_2 = "http://139.99.63.204/crapi/dgroup/viewstats"
TYPE_API_2 = "DICT"

# not used
BASE_URL = "http://139.99.63.204"
LOGIN_PAGE_URL = BASE_URL + "/ints/login"
LOGIN_POST_URL = BASE_URL + "/ints/signin"
DATA_URL = BASE_URL + "/ints/client/res/data_smscdr.php"

# --- Multiple Accounts (HARUS AKUJ CLIENT)
ACCOUNTS = [
    {
        "username": "jadenafrix", 
        "password": "jadenafrix", 
        "base_url": "http://139.99.63.204"
    },
    {
        "username": "jadenafrix", 
        "password": "jadenafrix", 
        "base_url": "http://139.99.63.204"
    },
]

# --- Default Channel Configuration ---
DEFAULT_MAIN_CHANNEL = '@auroratechinc' # Use @
DEFAULT_BACKUP_CHANNEL = 'https://t.me/mrafrixtech'
DEFAULT_BACKUP_CHANNEL_LINK = 'https://t.me/auroratechinc'
DEFAULT_OTP_CHANNEL = 'https://t.me/afrixotpgc'

# --- Button Configuration ---
BOT_LINK = "@auroraotpbot"
BUTTON_TEXT1 = "Number Channel 🚀"
BUTTON_TEXT2 = "Panel Bot"

# --- Global variables ---
stop_event = threading.Event()
reported_sms_hashes_cache = set()
working_api_url = None
MAIN_LOOP = None 
GLOBAL_APP = None

USER_STATE = {}

# --- Reference Data 
COUNTRY_CODES = {
    '1': ('USA/Canada', '🇺🇸', 'US'), '7': ('Russia', '🇷🇺', 'RU'), '20': ('Egypt', '🇪🇬', 'EG'), '27': ('South Africa', '🇿🇦', 'ZA'),
    '30': ('Greece', '🇬🇷', 'GR'), '31': ('Netherlands', '🇳🇱', 'NL'), '32': ('Belgium', '🇧🇪', 'BE'), '33': ('France', '🇫🇷', 'FR'),
    '34': ('Spain', '🇪🇸', 'ES'), '36': ('Hungary', '🇭🇺', 'HU'), '39': ('Italy', '🇮����', 'IT'), '40': ('Romania', '🇷🇴', 'RO'),
    '41': ('Switzerland', '🇨🇭', 'CH'), '43': ('Austria', '🇦🇹', 'AT'), '44': ('United Kingdom', '🇬🇧', 'GB'), '45': ('Denmark', '🇩🇰', 'DK'),
    '46': ('Sweden', '🇸🇪', 'SE'), '47': ('Norway', '🇳🇴', 'NO'), '48': ('Poland', '🇵🇱', 'PL'), '49': ('Germany', '🇩🇪', 'DE'),
    '51': ('Peru', '🇵🇪', 'PE'), '52': ('Mexico', '🇲🇽', 'MX'), '53': ('Cuba', '🇨🇺', 'CU'), '54': ('Argentina', '🇦🇷', 'AR'),
    '55': ('Brazil', '🇧🇷', 'BR'), '56': ('Chile', '🇨🇱', 'CL'), '57': ('Colombia', '🇨🇴', 'CO'), '58': ('Venezuela', '🇻🇪', 'VE'),
    '60': ('Malaysia', '🇲🇾', 'MY'), '61': ('Australia', '🇦🇺', 'AU'), '62': ('Indonesia', '🇮🇩', 'ID'), '63': ('Philippines', '🇵🇭', 'PH'),
    '64': ('New Zealand', '🇳🇿', 'NZ'), '65': ('Singapore', '🇸🇬', 'SG'), '66': ('Thailand', '🇹🇭', 'TH'), '81': ('Japan', '🇯🇵', 'JP'),
    '82': ('South Korea', '🇰🇷', 'KR'), '84': ('Viet Nam', '🇻🇳', 'VN'), '86': ('China', '🇨🇳', 'CN'), '90': ('Turkey', '🇹🇷', 'TR'),
    '91': ('India', '🇮🇳', 'IN'), '92': ('Pakistan', '🇵🇰', 'PK'), '93': ('Afghanistan', '🇦🇫', 'AF'), '94': ('Sri Lanka', '🇱🇰', 'LK'),
    '95': ('Myanmar', '🇲🇲', 'MM'), '98': ('Iran', '🇮🇷', 'IR'), '211': ('South Sudan', '🇸🇸', 'SS'), '212': ('Morocco', '🇲🇦', 'MA'),
    '213': ('Algeria', '🇩🇿', 'DZ'), '216': ('Tunisia', '🇹🇳', 'TN'), '218': ('Libya', '🇱🇾', 'LY'), '220': ('Gambia', '🇬🇲', 'GM'),
    '221': ('Senegal', '🇸🇳', 'SN'), '222': ('Mauritania', '🇲🇷', 'MR'), '223': ('Mali', '🇲🇱', 'ML'), '224': ('Guinea', '🇬🇳', 'GN'),
    '225': ("Côte d'Ivoire", '🇨🇮', 'CI'), '226': ('Burkina Faso', '🇧🇫', 'BF'), '227': ('Niger', '🇳🇪', 'NE'), '228': ('Togo', '🇹🇬', 'TG'),
    '229': ('Benin', '🇧🇯', 'BJ'), '230': ('Mauritius', '🇲🇺', 'MU'), '231': ('Liberia', '🇱🇷', 'LR'), '232': ('Sierra Leone', '🇸🇱', 'SL'),
    '233': ('Ghana', '🇬🇭', 'GH'), '234': ('Nigeria', '🇳🇬', 'NG'), '235': ('Chad', '🇹🇩', 'TD'), '236': ('Central African Republic', '🇨🇫', 'CF'),
    '237': ('Cameroon', '🇨🇲', 'CM'), '238': ('Cape Verde', '🇨🇻', 'CV'), '239': ('Sao Tome and Principe', '🇸🇹', 'ST'),
    '240': ('Equatorial Guinea', '🇬🇶', 'GQ'), '241': ('Gabon', '🇬🇦', 'GA'), '242': ('Congo', '🇨🇬', 'CG'),
    '243': ('DR Congo', '🇨🇩', 'CD'), '244': ('Angola', '🇦🇴', 'AO'), '245': ('Guinea-Bissau', '🇬🇼', 'GW'), '248': ('Seychelles', '🇸🇨', 'SC'),
    '249': ('Sudan', '🇸🇩', 'SD'), '250': ('Rwanda', '🇷🇼', 'RW'), '251': ('Ethiopia', '🇪🇹', 'ET'), '252': ('Somalia', '🇸🇴', 'SO'),
    '253': ('Djibouti', '🇩🇯', 'DJ'), '254': ('Kenya', '🇰🇪', 'KE'), '255': ('Tanzania', '🇹🇿', 'TZ'), '256': ('Uganda', '🇺🇬', 'UG'),
    '257': ('Burundi', '🇧🇮', 'BI'), '258': ('Mozambique', '🇲🇿', 'MZ'), '260': ('Zambia', '🇿🇲', 'ZM'), '261': ('Madagascar', '🇲🇬', 'MG'),
    '263': ('Zimbabwe', '🇿🇼', 'ZW'), '264': ('Namibia', '🇳🇦', 'NA'), '265': ('Malawi', '🇲🇼', 'MW'), '266': ('Lesotho', '🇱🇸', 'LS'),
    '267': ('Botswana', '🇧🇼', 'BW'), '268': ('Eswatini', '🇸🇿', 'SZ'), '269': ('Comoros', '🇰🇲', 'KM'), '290': ('Saint Helena', '🇸🇭', 'SH'),
    '291': ('Eritrea', '🇪🇷', 'ER'), '297': ('Aruba', '🇦🇼', 'AW'), '298': ('Faroe Islands', '🇫🇴', 'FO'), '299': ('Greenland', '🇬🇱', 'GL'),
    '350': ('Gibraltar', '🇬🇮', 'GI'), '351': ('Portugal', '🇵🇹', 'PT'), '352': ('Luxembourg', '🇱🇺', 'LU'), '353': ('Ireland', '🇮🇪', 'IE'),
    '354': ('Iceland', '🇮🇸', 'IS'), '355': ('Albania', '🇦🇱', 'AL'), '356': ('Malta', '🇲🇹', 'MT'), '357': ('Cyprus', '🇨🇾', 'CY'),
    '358': ('Finland', '🇫🇮', 'FI'), '359': ('Bulgaria', '🇧🇬', 'BG'), '370': ('Lithuania', '🇱🇹', 'LT'), '371': ('Latvia', '🇱🇻', 'LV'),
    '372': ('Estonia', '🇪🇪', 'EE'), '373': ('Moldova', '🇲🇩', 'MD'), '374': ('Armenia', '🇦🇲', 'AM'), '375': ('Belarus', '🇧🇾', 'BY'),
    '376': ('Andorra', '🇦🇩', 'AD'), '377': ('Monaco', '🇲🇨', 'MC'), '378': ('San Marino', '🇸🇲', 'SM'), '380': ('Ukraine', '🇺🇦', 'UA'),
    '381': ('Serbia', '🇷🇸', 'RS'), '382': ('Montenegro', '🇲🇪', 'ME'), '385': ('Croatia', '🇭🇷', 'HR'), '386': ('Slovenia', '🇸🇮', 'SI'),
    '387': ('Bosnia and Herzegovina', '🇧🇦', 'BA'), '389': ('North Macedonia', '🇲🇰', 'MK'), '420': ('Czech Republic', '🇨🇿', 'CZ'),
    '421': ('Slovakia', '🇸🇰', 'SK'), '423': ('Liechtenstein', '🇱🇮', 'LI'), '501': ('Belize', '🇧🇿', 'BZ'), '502': ('Guatemala', '🇬🇹', 'GT'),
    '503': ('El Salvador', '🇸🇻', 'SV'), '504': ('Honduras', '🇭🇳', 'HN'), '505': ('Nicaragua', '🇳🇮', 'NI'), '506': ('Costa Rica', '🇨🇷', 'CR'),
    '507': ('Panama', '🇵🇦', 'PA'), '509': ('Haiti', '🇭🇹', 'HT'), '590': ('Guadeloupe', '🇬🇵', 'GP'), '591': ('Bolivia', '🇧🇴', 'BO'),
    '592': ('Guyana', '🇬🇾', 'GY'), '593': ('Ecuador', '🇪🇨', 'EC'), '595': ('Paraguay', '🇵🇾', 'PY'), '597': ('Suriname', '🇸🇷', 'SR'),
    '598': ('Uruguay', '🇺🇾', 'UY'), '673': ('Brunei', '🇧🇳', 'BN'), '675': ('Papua New Guinea', '🇵🇬', 'PG'), '676': ('Tonga', '🇹🇴', 'TO'),
    '677': ('Solomon Islands', '🇸🇧', 'SB'), '678': ('Vanuatu', '🇻🇺', 'VU'), '679': ('Fiji', '🇫🇯', 'FJ'), '685': ('Samoa', '🇼🇸', 'WS'),
    '689': ('French Polynesia', '🇵🇫', 'PF'), '852': ('Hong Kong', '🇭🇰', 'HK'), '853': ('Macau', '🇲🇴', 'MO'), '855': ('Cambodia', '🇰🇭', 'KH'),
    '856': ('Laos', '🇱🇦', 'LA'), '880': ('Bangladesh', '🇧🇩', 'BD'), '886': ('Taiwan', '🇹🇼', 'TW'), '960': ('Maldives', '🇲🇻', 'MV'),
    '961': ('Lebanon', '🇱🇧', 'LB'), '962': ('Jordan', '🇯🇴', 'JO'), '963': ('Syria', '🇸🇾', 'SY'), '964': ('Iraq', '🇮🇶', 'IQ'),
    '965': ('Kuwait', '🇰🇼', 'KW'), '966': ('Saudi Arabia', '🇸🇦', 'SA'), '967': ('Yemen', '🇾🇪', 'YE'), '968': ('Oman', '🇴🇲', 'OM'),
    '970': ('Palestine', '🇵🇸', 'PS'), '971': ('United Arab Emirates', '🇦🇪', 'AE'), '972': ('Israel', '🇮🇱', 'IL'),
    '973': ('Bahrain', '🇧🇭', 'BH'), '974': ('Qatar', '🇶🇦', 'QA'), '975': ('Bhutan', '🇧🇹', 'BT'), '976': ('Mongolia', '🇲🇳', 'MN'),
    '977': ('Nepal', '🇳🇵', 'NP'), '992': ('Tajikistan', '🇹🇯', 'TJ'), '993': ('Turkmenistan', '🇹🇲', 'TM'), '994': ('Azerbaijan', '🇦🇿', 'AZ'),
    '995': ('Georgia', '🇬🇪', 'GE'), '996': ('Kyrgyzstan', '🇰🇬', 'KG'), '998': ('Uzbekistan', '🇺🇿', 'UZ'), '383': ('Kosovo', '🇽🇰', 'XK'),
}

# Database Class
class Database:
    _instance = None
    _connection = None
    _lock = threading.RLock() 
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._connection = sqlite3.connect('numbers.db', check_same_thread=False, timeout=30)
            cls._connection.row_factory = sqlite3.Row
            cls.init_db()
            cls.migrate_db()
        return cls._instance

    @classmethod
    def migrate_db(cls):
        """Menjamin kolom balance dan total_earned ada"""
        with cls._lock:
            try:
                cls._connection.execute("ALTER TABLE users ADD COLUMN balance REAL DEFAULT 0.0")
            except sqlite3.OperationalError: pass 
            
            try:
                cls._connection.execute("ALTER TABLE users ADD COLUMN total_earned REAL DEFAULT 0.0")
            except sqlite3.OperationalError: pass
            
            cls._connection.commit()

    @classmethod
    def init_db(cls):
        with cls._lock:
            c = cls._connection.cursor()
            
            # Perbaikan: Tambahkan balance REAL DEFAULT 0.0 di skema tabel users
            c.execute('''CREATE TABLE IF NOT EXISTS users
                         (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, 
                         last_name TEXT, join_date TEXT, is_banned INTEGER DEFAULT 0,
                         balance REAL DEFAULT 0.0)''')
            
            c.execute('''CREATE TABLE IF NOT EXISTS numbers
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, country TEXT, number TEXT UNIQUE, 
                         is_used INTEGER DEFAULT 0, used_by INTEGER, use_date TEXT)''')
            
            c.execute('''CREATE TABLE IF NOT EXISTS countries
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, code TEXT)''')
            
            c.execute('''CREATE TABLE IF NOT EXISTS user_stats
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, date TEXT, 
                         numbers_today INTEGER DEFAULT 0)''')
            
            c.execute('''CREATE TABLE IF NOT EXISTS cooldowns
                         (user_id INTEGER PRIMARY KEY, timestamp INTEGER)''')
            
            c.execute('''CREATE TABLE IF NOT EXISTS notifications
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, country TEXT, notified INTEGER DEFAULT 0)''')
            
            c.execute('''CREATE TABLE IF NOT EXISTS sms_history
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, number TEXT, message TEXT, receive_date TEXT)''')
            
            c.execute('''CREATE TABLE IF NOT EXISTS public_sms_history
                         (hash TEXT PRIMARY KEY, date_added TEXT)''')

            c.execute('''CREATE TABLE IF NOT EXISTS bot_status
                         (id INTEGER PRIMARY KEY CHECK (id = 1), is_enabled INTEGER DEFAULT 1)''')
            
            c.execute("INSERT OR IGNORE INTO bot_status (id, is_enabled) VALUES (1, 1)")

            c.execute('''CREATE TABLE IF NOT EXISTS channel_settings
                         (id INTEGER PRIMARY KEY CHECK (id = 1),
                          main_channel TEXT,
                          backup_channel TEXT,
                          backup_channel_link TEXT,
                          otp_channel TEXT)''')

            c.execute("""INSERT OR IGNORE INTO channel_settings 
                         (id, main_channel, backup_channel, backup_channel_link, otp_channel)
                         VALUES (1, ?, ?, ?, ?)""",
                      (DEFAULT_MAIN_CHANNEL,
                       DEFAULT_BACKUP_CHANNEL,
                       DEFAULT_BACKUP_CHANNEL_LINK,
                       DEFAULT_OTP_CHANNEL))
            
            c.execute('''CREATE TABLE IF NOT EXISTS otp_stats (
                         id INTEGER PRIMARY KEY AUTOINCREMENT,
                         country TEXT,
                         service TEXT,
                         timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
            
            c.execute('''CREATE TABLE IF NOT EXISTS settings 
                         (id INTEGER PRIMARY KEY, otp_reward REAL, ref_reward REAL)''')
            
            c.execute('''INSERT OR IGNORE INTO settings (id, otp_reward, ref_reward) 
                         VALUES (1, 0.003, 0.0100)''')
            c.execute('''CREATE TABLE IF NOT EXISTS users
                         (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, 
                         last_name TEXT, join_date TEXT, is_banned INTEGER DEFAULT 0,
                         balance REAL DEFAULT 0.0, total_earned REAL DEFAULT 0.0)''')
            c.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in c.fetchall()]
            
            if 'balance' not in columns:
                c.execute("ALTER TABLE users ADD COLUMN balance REAL DEFAULT 0.0")
                logger.info("✅  The 'balance' column was successfully added automatically..")
                
            if 'total_earned' not in columns:
                c.execute("ALTER TABLE users ADD COLUMN total_earned REAL DEFAULT 0.0")
                logger.info("✅ The 'total_earned' column was successfully added automatically..")

            c.execute('''CREATE TABLE IF NOT EXISTS numbers
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, country TEXT, number TEXT UNIQUE, 
                         is_used INTEGER DEFAULT 0, used_by INTEGER, use_date TEXT)''')
            cls._connection.commit()

    @classmethod
    def migrate_db(cls):
        """Ensures balance column exists without deleting existing data."""
        with cls._lock:
            try:
                cls._connection.execute("ALTER TABLE users ADD COLUMN balance REAL DEFAULT 0.0")
                cls._connection.commit()
            except sqlite3.OperationalError:
                pass # Kolom sudah ada

    @classmethod
    def execute(cls, query, params=()):
        with cls._lock:
            try:
                c = cls._connection.cursor()
                c.execute(query, params)
                cls._connection.commit()
                return c
            except sqlite3.Error as e:
                logger.error(f"Database error: {e}")
                return cls._connection.cursor()

    @classmethod
    def commit(cls):
        """Fix: Added commit method so that 'db.commit()' outside the class does not error."""
        with cls._lock:
            cls._connection.commit()

db = Database()


def setup_statistics_db():
    db.execute('''CREATE TABLE IF NOT EXISTS otp_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country TEXT,
        service TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        
    )''')
    
# === Helper Functions ===
def get_country_from_number(number: str) -> str:
    for code in sorted(COUNTRY_CODES.keys(), key=lambda x: -len(x)):
        if number.startswith(code):
            return COUNTRY_CODES[code]
    return '🌍 Unknown'

def escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def save_already_sent(username, already_sent):
    with open(f"already_sent_{username}.json", "w") as f:
        json.dump(list(already_sent), f)

def load_already_sent(username):
    filename = f"already_sent_{username}.json"
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return set(json.load(f))
    return set()
async def login(session, username, password, base_url):
    try:
        login_page = f"{base_url.rstrip('/')}/ints/login"
        signin_url = f"{base_url.rstrip('/')}/ints/signin"
        
        resp = session.get(login_page)
        match = re.search(r'What is (\d+) \+ (\d+)', resp.text)
        if not match: return False
        
        captcha_answer = int(match.group(1)) + int(match.group(2))
        payload = {"username": username, "password": password, "capt": captcha_answer}
        
        resp = session.post(signin_url, data=payload, headers={"Referer": login_page})
        return "dashboard" in resp.text.lower() or "logout" in resp.text.lower()
    except Exception:
        return False

def build_api_url(endpoint_url):
    start_date = "2025-04-25"
    end_date = "2026-02-02"
    return (
        f"{endpoint_url}?fdate1={start_date}%2000:00:00&fdate2={end_date}%2023:59:59&"
        "frange=&fnum=&fcli=&fgdate=&fgmonth=&fgrange=&fgnumber=&fgcli=&fg=0&"
        "sEcho=1&iColumns=7&sColumns=%2C%2C%2C%2C%2C%2C&iDisplayStart=0&iDisplayLength=25&"
        "mDataProp_0=0&sSearch_0=&bRegex_0=false&bSearchable_0=true&bSortable_0=true&"
        "mDataProp_1=1&sSearch_1=&bRegex_1=false&bSearchable_1=true&bSortable_1=true&"
        "mDataProp_2=2&sSearch_2=&bRegex_2=false&bSearchable_2=true&bSortable_2=true&"
        "mDataProp_3=3&sSearch_3=&bRegex_3=false&bSearchable_3=true&bSortable_3=true&"
        "mDataProp_4=4&sSearch_4=&bRegex_4=false&bSearchable_4=true&bSortable_4=true&"
        "mDataProp_5=5&sSearch_5=&bRegex_5=false&bSearchable_5=true&bSortable_5=true&"
        "mDataProp_6=6&sSearch_6=&bRegex_6=false&bSearchable_6=true&bSortable_6=true&"
        "sSearch=&bRegex=false&iSortCol_0=0&sSortDir_0=desc&iSortingCols=1"
    )

def fetch_data(session, base_url):
    data_url = f"{base_url.rstrip('/')}/ints/client/res/data_smscdr.php"

    url = build_api_url(data_url) 
    
    headers = {"X-Requested-With": "XMLHttpRequest"}
    try:
        response = session.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 403 or "login" in response.text.lower():
            return "session_expired"
        return None
    except Exception:
        return None



def get_traffic_report(period='day'):
    if period == 'day':
        query_filter = "datetime('now', '-1 day')"
    elif period == 'week':
        query_filter = "datetime('now', '-7 days')"
    else:
        query_filter = "datetime('now', '-30 days')"

    rows = db.execute(f'''
        SELECT country, service, COUNT(*) as total 
        FROM otp_stats 
        WHERE timestamp >= {query_filter}
        GROUP BY country, service
        ORDER BY total DESC
    ''').fetchall()
    
    if not rows:
        return "No traffic recorded in this period."

    report = f"📊 *Traffic Report ({period.capitalize()})*\n"
    report += "----------------------------\n"
    for row in rows:
        report += f"📍 {row[0]} | {row[1].upper()}: `{row[2]}` OTP\n"
    
    return report
    
def record_traffic(number, sender, message):
    """Universal function to log traffic to database"""
    c_info = get_country_info(number)
    country_name = c_info[0]
    service_name = detect_service(sender, message)
    
    with db._lock:
        db.execute("INSERT INTO otp_stats (country, service) VALUES (?, ?)", 
                   (country_name, service_name))
        db.commit()

def get_channel_settings():
    c = db.execute("SELECT main_channel, backup_channel, backup_channel_link, otp_channel FROM channel_settings WHERE id = 1")
    row = c.fetchone()
    if row:
        return row['main_channel'], row['backup_channel'], row['backup_channel_link'], row['otp_channel']
    return DEFAULT_MAIN_CHANNEL, DEFAULT_BACKUP_CHANNEL, DEFAULT_BACKUP_CHANNEL_LINK, DEFAULT_OTP_CHANNEL

def update_channel_settings(main=None, backup=None, link=None, otp=None):
    current_main, current_backup, current_link, current_otp = get_channel_settings()
    main = main if main not in (None, '') else current_main
    backup = backup if backup not in (None, '') else current_backup
    link = link if link not in (None, '') else current_link
    otp = otp if otp not in (None, '') else current_otp

    db.execute("""UPDATE channel_settings 
                  SET main_channel=?, backup_channel=?, backup_channel_link=?, otp_channel=?
                  WHERE id=1""",
               (main, backup, link, otp))

def is_bot_enabled():
    c = db.execute("SELECT is_enabled FROM bot_status WHERE id = 1")
    result = c.fetchone()
    return result[0] == 1 if result else True

def set_bot_status(enabled):
    status = 1 if enabled else 0
    db.execute("UPDATE bot_status SET is_enabled = ? WHERE id = 1", (status,))
    return True

def get_country_info(phone_number):
    clean_num = phone_number.replace('+', '').strip()
    for i in range(4, 0, -1):
        prefix = clean_num[:i]
        if prefix in COUNTRY_CODES:
            return COUNTRY_CODES[prefix] 
    return ('Unknown', '❓', 'UN')

def get_short_service(sender_name):
    """Abbreviate the sender's name to 2-3 letters (eg: WhatsApp -> WS)"""
    if not sender_name: return "OT"
    name = sender_name.upper()
    if "WHATSAPP" in name: return "WS"
    if "FACEBOOK" in name: return "FB"
    if "GOOGLE" in name: return "GO"
    if "TELEGRAM" in name: return "TG"
    if "Instagram" in name: return "IG"
    if "TIKTOK" in name: return "TT"
    if "BITGET" in name: return "BG"
    if "APPLE" in name: return "AP"

    return name[:2]
def detect_service(sender_name, message_text):
    full_text = (str(sender_name) + " " + str(message_text)).lower()
    services = ['whatsapp', 'facebook', 'google', 'telegram', 'instagram', 'discord', 'twitter', 'snapchat', 'imo', 'tiktok']
    for service in services:
        if service in full_text: return service.capitalize()
    return sender_name if sender_name else "Unknown"

# --- BRIDGE FUNCTION
def send_async_message(chat_id, text, parse_mode=None, reply_markup=None, auto_delete=False):
    if GLOBAL_APP and MAIN_LOOP and not MAIN_LOOP.is_closed():
        async def sending():
            try:
                msg = await GLOBAL_APP.bot.send_message(
                    chat_id=chat_id, 
                    text=text, 
                    parse_mode=parse_mode, 
                    reply_markup=reply_markup
                )

                if auto_delete:
                    asyncio.create_task(silent_auto_delete(chat_id, msg.message_id, 120))
            except Exception as error:
                print(f"❌ Failed to send to {chat_id}: {error}")

        asyncio.run_coroutine_threadsafe(sending(), MAIN_LOOP)
    else:
        print("⏳ Waiting for bot to be ready before sending message...")

      
        

# --- PUBLIC BROADCAST NOTIFICATION ---
def format_public_message(recipient_number, sender_name, message, otp, sms_time, masked_num):
    main_ch, _, _, otp_ch = get_channel_settings()
    country_name, country_flag, country_iso = get_country_info(recipient_number)
    service_name = detect_service(sender_name, message)
    
    country_name, country_flag, country_iso = get_country_info(recipient_number)
    short_cli = get_short_service(sender_name)
    
    full_service = detect_service(sender_name, message)


    otp_digit_match = re.search(r'\d{5,8}', str(otp))
    clean_otp = otp_digit_match.group(0) if otp_digit_match else "N/A"
    
    if clean_otp == "N/A":
        only_digits = re.sub(r'\D', '', str(otp))
        clean_otp = only_digits if only_digits else "N/A"

    safe_service = str(service_name).replace('*', '').replace('_', '').replace('`', '')
    
    header_line = f"{country_flag} #{country_iso} #{short_cli} {masked_num}"
    
    message_text = (
        f"{header_line}\n rilzz chaniago team"

    )
    
    keyboard = [
        [

            InlineKeyboardButton(
                text=f"{clean_otp}", 
                copy_text=CopyTextButton(text=clean_otp)
            )
       ],
       [
            InlineKeyboardButton(
                text="Full Message",
                copy_text=CopyTextButton(text=message)
            )
        ],
        [
            InlineKeyboardButton(text="Channel 🚀", url=f"https://t.me/{main_ch.lstrip('@')}"),
            InlineKeyboardButton(text="Panel Bot", url=BOT_LINK)
        ]
    ]
    
    markup = InlineKeyboardMarkup(keyboard)
    
    return message_text, markup
# --- PRIVATE NOTIFICATION
def format_private_message(recipient_number, message, otp, current_balance, reward_amount):
    country_info = get_country_info(recipient_number)
    flag = country_info[1]
    otp_digit_match = re.search(r'\d{4,8}', str(otp))
    clean_otp = otp_digit_match.group(0) if otp_digit_match else None
    if not clean_otp:
         only_digits = re.sub(r'\D', '', str(otp))
         clean_otp = only_digits if only_digits else "No Code"

    html_text = (
         f"🌎 <b>Country :</b> {country_info[0]} {flag}\n"
         f"🔢 <b>Number :</b> <code>{recipient_number}</code>\n"
         f"🔑 <b>OTP :</b> <code>{clean_otp}</code>\n"
         f"━━━━━━━━━━━━━━━\n"
         f"💸 <b>Reward:</b> {reward_amount:.4f}\n"
         f"💵 <b>Balance:</b> {current_balance:.4f}\n\n"
         f"<b>Full Message:</b>\n"
         f"<blockquote>{message}</blockquote>\n"
         f"⏰ <i>{datetime.now().strftime('%H:%M:%S')}</i>"
    )
    return html_text

def extract_numbers_from_content(content, filename):
    cleaned_numbers = []
    try:
        if filename.endswith('.xlsx'):
            import openpyxl
            wb = openpyxl.load_workbook(BytesIO(content), data_only=True)
            sheet = wb.active
            for row in sheet.iter_rows(values_only=True):
                for cell in row:
                    if cell:
                        num = re.sub(r'\D', '', str(cell))
                        if 6 <= len(num) <= 30:
                            cleaned_numbers.append('+' + num)
        else:
            text_content = content.decode('utf-8', errors='ignore')
            matches = re.findall(r'\d{6,30}', text_content)
            for num in matches:
                cleaned_numbers.append('+' + num)
        return list(set(cleaned_numbers))
    except Exception as e:
        logger.error(f"Error extracting numbers: {e}")
        return []

def solve_math_captcha(text):
    try:
        match = re.search(r'(\d+)\s*([\+\*])\s*(\d+)', text)
        if match:
            num1 = int(match.group(1))
            operator = match.group(2)
            num2 = int(match.group(3))
            return str(num1 + num2 if operator == '+' else num1 * num2)
    except Exception:
        pass
    return "0"

# Sms Monitoring logic
def start_watching_sms_api(api_url, token, source_label, api_type):
    time.sleep(5)
    logger.info(f"🚀 [{source_label}] Monitoring started via API...")
    local_hash_cache = set()
    
    while not stop_event.is_set():
        try:

            response = requests.get(api_url, params={'token': token, 'records': 200}, timeout=30)
            
            if response.status_code != 200:
                time.sleep(10)
                continue
                
            try:
                data = response.json()
            except:
                time.sleep(10)
                continue

            sms_list = []
            if isinstance(data, dict):
                if data.get("status") == "success" and "data" in data:
                    sms_list = data["data"]
                elif "aaData" in data:
                    sms_list = data["aaData"]
            
            timestamp = datetime.now().strftime('%H:%M:%S')
            if sms_list:
                print(f"📡 [{timestamp}] [{source_label}] Connected | {len(sms_list)} records found.")
            else:
                print(f"😴 [{timestamp}] [{source_label}] Connected | No records (waiting for OTP...)")

            for item in reversed(sms_list):
                try:
                
                    if isinstance(item, dict):
                        dt = item.get("dt") or item.get("date")
                        rc = item.get("num") or item.get("number")
                        sn = item.get("cli") or item.get("sender")
                        msg = item.get("message") or item.get("msg")
                    elif isinstance(item, list) and len(item) >= 4:
                        sn = str(item[0])  
                        rc = str(item[1])
                        msg = str(item[2])
                        dt = str(item[3])
                    else:
                        continue

                    if not msg or not rc:
                        continue
                        
                    clean_rc = re.sub(r'\D', '', str(rc))
                    sms_hash = hashlib.md5(f"{dt}{clean_rc}{msg}".encode()).hexdigest()
                    
                    with db._lock:
                        check = db.execute("SELECT hash FROM public_sms_history WHERE hash = ?", (sms_hash,)).fetchone()
                        if check:
                            continue

                except Exception as e:
                    logger.error(f"Error parsing item: {e}")
                    continue

                if not msg or not rc: 
                    continue
                
                sms_hash = hashlib.md5(f"{dt}{rc}{msg}".encode()).hexdigest()

                with db._lock:
                    c_check = db.execute("SELECT hash FROM public_sms_history WHERE hash = ?", (sms_hash,))
                    already_reported = c_check.fetchone()

                if not already_reported and sms_hash not in local_hash_cache:
                    time.sleep(1)

                    country_info = get_country_info(rc)
                    country_name = country_info[0]
                    service_name = detect_service(sn, msg)
                    
                    db.execute("INSERT INTO otp_stats (country, service) VALUES (?, ?)", 
                               (country_name, service_name))

                    print(f"✅ [{source_label}] NEW OTP! Number: {rc} from {sn}")

                    clean_rc = re.sub(r'\D', '', str(rc))
                    c_user = db.execute("SELECT used_by FROM numbers WHERE number LIKE ? AND is_used = 1", (f"%{clean_rc}",))
                    user_res = c_user.fetchone()
                    clean_msg_for_otp = msg.replace('-', '')
                    otp_match = re.search(r'\d{5,8}', clean_msg_for_otp)
                    otp = otp_match.group(0) if otp_match else "N/A"

                    if user_res:
                        target_user_id = user_res['used_by']

                        with db._lock:
                            s_data = db.execute("SELECT otp_reward FROM settings WHERE id=1").fetchone()
                            reward_amt = s_data['otp_reward'] if s_data else 0.0050

                            db.execute("UPDATE users SET balance = balance + ?, total_earned = total_earned + ? WHERE user_id = ?", 
                                       (reward_amt, reward_amt, target_user_id))

                            u_data = db.execute("SELECT balance FROM users WHERE user_id = ?", (target_user_id,)).fetchone()
                            curr_bal = u_data['balance'] if u_data else reward_amt

                        formatted_private = format_private_message(rc, msg, otp, curr_bal, reward_amt)
                        send_async_message(target_user_id, formatted_private, parse_mode=ParseMode.HTML)

                    masked = f"+{clean_rc[:5]}RILZ{clean_rc[-4:]}" if len(clean_rc) > 9 else rc
                    text, markup = format_public_message(rc, sn, msg, otp, dt, masked)
                    
                    try:

                        _, _, _, otp_ch = get_channel_settings()
                        send_async_message(otp_ch, text, parse_mode=ParseMode.HTML, reply_markup=markup, auto_delete=True)

                        db.execute("INSERT OR IGNORE INTO public_sms_history (hash, date_added) VALUES (?, ?)", (sms_hash, dt))
                        local_hash_cache.add(sms_hash)
                        reported_sms_hashes_cache.add(sms_hash)
                    except Exception as e_send:
                        print(f"❌ [ERROR] Failed to send: {e_send}")

            time.sleep(5)
                
        except Exception as e:
            logger.error(f"⚠️ [{source_label}] Loop Error: {e}")
            time.sleep(10)

# PTB Handler
async def check_membership(user_id, context):
    """Checks if a user is a member of the required channels."""
    try:
        main_ch, backup_ch, _, _ = get_channel_settings()
        
        try:
            m1 = await context.bot.get_chat_member(main_ch, user_id)
            if m1.status not in ['member', 'administrator', 'creator']: 
                return False
        except BadRequest: 
            return False
        try:
            m2 = await context.bot.get_chat_member(backup_ch, user_id)
            if m2.status not in ['member', 'administrator', 'creator']: 
                return False
        except BadRequest: 
            pass 

        return True
    except Exception as e:
        logger.error(f"Membership check fail: {e}")
        return False

async def silent_auto_delete(chat_id, message_id, delay=120):
    """Wait for 'delay' seconds and delete the message without any bot notification."""
    await asyncio.sleep(delay)
    try:
        if GLOBAL_APP:
            await GLOBAL_APP.bot.delete_message(chat_id=chat_id, message_id=message_id)
            print(f"[*] [AUTO-DELETE] Message {message_id} removed from {chat_id}")
    except Exception as e:

        print(f"[!] [AUTO-DELETE] Failed to delete message {message_id}: {e}")
        
async def traffic_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id 
    if user_id not in ADMIN_IDS:
        is_member = await check_membership(user_id, context)
        if not is_member:
            await update.message.reply_text("❌ Join channel first to see traffic.")
            return
    is_member = await check_membership(update.effective_user.id, context)
    if not is_member:
        await update.message.reply_text("❌ Join channel first to see traffic.")
        return
        
    report = get_traffic_report(period='day')
    await update.message.reply_text(report, parse_mode=ParseMode.MARKDOWN)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id

    if user.id in USER_STATE: del USER_STATE[user.id]

    c = db.execute("SELECT is_banned FROM users WHERE user_id = ?", (user.id,))
    res = c.fetchone()
    if res and res[0] == 1:
        await context.bot.send_message(chat_id, "❌ You are banned.")
        return

    if not res:
        db.execute("INSERT INTO users (user_id, username, first_name, join_date) VALUES (?, ?, ?, ?)",
                   (user.id, user.username, user.first_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    is_member = await check_membership(user.id, context)
    main_ch, _, backup_link, _ = get_channel_settings()
    
    if not is_member and user.id not in ADMIN_IDS:
        keyboard = [
            [InlineKeyboardButton("📢 Main Channel", url=f"https://t.me/{main_ch.lstrip('@')}")],
            [InlineKeyboardButton("🔗 Backup Group", url=backup_link)],
            [InlineKeyboardButton("✅ Check Membership", callback_data="check_membership")]
        ]
        await context.bot.send_message(chat_id, 
            f"❌ You need to join our channels first!\n\nMain: {main_ch}\nBackup",
            reply_markup=InlineKeyboardMarkup(keyboard))
        return

    await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = []
    
    c = db.execute("SELECT DISTINCT country FROM numbers WHERE is_used = 0")
    countries = c.fetchall()
    
    # Grid 3 kolom
    row = []
    for country in countries:
        row.append(InlineKeyboardButton(f" {country[0]}", callback_data=f"country_{country[0]}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row: keyboard.append(row)

    if user_id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("🔧 Admin Panel", callback_data="admin_panel")])
    
    text = "🌍 *Global Virtual Number Hub*\nChoose a country:"
    markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)
    else:
        await update.callback_query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton("➕ Add Numbers", callback_data="admin_add_numbers"), InlineKeyboardButton("🗑️ Remove Numbers", callback_data="admin_remove_numbers")],
        [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats"), InlineKeyboardButton("👤 User Management", callback_data="admin_users")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"), InlineKeyboardButton("🔍 Find Number", callback_data="admin_find_number")],
        [InlineKeyboardButton("⚙️ Channel Settings", callback_data="admin_channel_settings"), InlineKeyboardButton("📦 Backup Code", callback_data="admin_backup")],
        [InlineKeyboardButton("🔄 Restart Bot", callback_data="admin_restart")]
    ]
    await query.message.edit_text("🔧 **Admin Control Panel**\n\nSelect a management option below:", 
                                  parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    
    await query.answer()

    if not is_bot_enabled() and user_id not in ADMIN_IDS:
        await query.answer("❌ Maintenance mode.", show_alert=True)
        return

    # --- Membership Check ---
    if data == "check_membership":
        is_member = await check_membership(user_id, context)
        if is_member:
            await show_main_menu(update, context)
        else:
            await query.answer("❌ Not joined yet!", show_alert=True)
        return

    # --- Country Selection & Change Number ---
    if data.startswith("country_") or data.startswith("change_"):
        country = data.split("_", 1)[1]
        
        # Check Cooldown (Simple)
        c = db.execute("SELECT timestamp FROM cooldowns WHERE user_id = ?", (user_id,))
        cd_res = c.fetchone()
        if cd_res:
            elapsed = int(time.time()) - cd_res[0]
            if elapsed < 5:
                await query.answer(f"⏳ Please wait {5-elapsed}s", show_alert=True)
                return

        # Check Available
        c = db.execute("SELECT number FROM numbers WHERE country = ? AND is_used = 0 LIMIT 1", (country,))
        res = c.fetchone()
        
        if not res:
            await query.answer("❌ No numbers available!", show_alert=True)
            return
        
        # Process Logic
        if data.startswith("change_"):
            old = db.execute("SELECT number FROM numbers WHERE country = ? AND used_by = ? ORDER BY use_date DESC LIMIT 1", (country, user_id)).fetchone()
            if old: db.execute("UPDATE numbers SET his_used = 2 WHERE number = ?", (old[0],))
        
        number = res[0]
        db.execute("UPDATE numbers SET is_used = 1, used_by = ?, use_date = ? WHERE number = ?",
                   (user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), number))
        
        # Update Stats & Cooldown
        today = datetime.now().strftime("%Y-%m-%d")
        exist = db.execute("SELECT id FROM user_stats WHERE user_id = ? AND date = ?", (user_id, today)).fetchone()
        if exist: db.execute("UPDATE user_stats SET numbers_today = numbers_today + 1 WHERE id = ?", (exist[0],))
        else: db.execute("INSERT INTO user_stats (user_id, date, numbers_today) VALUES (?, ?, 1)", (user_id, today))
        
        db.execute("REPLACE INTO cooldowns (user_id, timestamp) VALUES (?, ?)", (user_id, int(time.time())))

        _, _, _, otp_ch = get_channel_settings()
        
        keyboard = [
            [InlineKeyboardButton("🔄 Change Number", callback_data=f"change_{country}")],
            [InlineKeyboardButton("🔑 OTP GROUP", url=f"https://t.me/{otp_ch.lstrip('@')}")],
            [InlineKeyboardButton("⬅️ Back", callback_data="back_to_countries")]
        ]
        
        msg_text = f"✅ Your {country} Number:\n`{number}`\n`{number}`\n`{number}`\n\nTap to copy. Wait for SMS."
        await query.message.edit_text(msg_text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data == "back_to_countries":
        await show_main_menu(update, context)
        return
        # --- Logika Withdraw ---
    if data == "wd_start":
        res = db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)).fetchone()
        balance = res['balance'] if res else 0.0
        
        if balance < 10.0:
            await query.answer(f"❌ You must have $10! (Current: ${balance:.2f})", show_alert=True)
            return
            
        keyboard = [
            [InlineKeyboardButton("🟠 Binance (Pay ID)", callback_data="wd_method_binance")],
            [InlineKeyboardButton("🔵 TRX (TRC20)", callback_data="wd_method_trx")],
            [InlineKeyboardButton("⬅️ Back", callback_data="back_to_main")]
        ]
        await query.message.edit_text("✅ Balance sufficient. Choose payment method:", 
                                      reply_markup=InlineKeyboardMarkup(keyboard))
        return

   
        # --- Handler untuk Input Ala
        # Ambil data balance user l


    # --- ADMIN ACTIONS ---
    if user_id not in ADMIN_IDS: return

    if data == "admin_panel":
        await admin_panel(update, context)
        return

    if data == "admin_stats":
        today = datetime.now().strftime("%Y-%m-%d")
        

        total_today = db.execute("SELECT COUNT(*) FROM otp_stats WHERE timestamp >= datetime('now', 'start of day')").fetchone()[0]
        total_week = db.execute("SELECT COUNT(*) FROM otp_stats WHERE timestamp >= datetime('now', '-7 days')").fetchone()[0]
        total_month = db.execute("SELECT COUNT(*) FROM otp_stats WHERE timestamp >= datetime('now', '-30 days')").fetchone()[0]
        
        active_users = db.execute("SELECT COUNT(DISTINCT user_id) FROM user_stats WHERE date = ?", (today,)).fetchone()[0]
        c = db.execute("""
            SELECT country, service, COUNT(*) as qty 
            FROM otp_stats 
            WHERE timestamp >= datetime('now', 'start of day')
            GROUP BY country, service 
            ORDER BY qty DESC 
            LIMIT 5
        """)
        traffic_rows = c.fetchall()
        
        stats_msg = (
            f"📊 *Live Bot Statistics*\n"
            f"──────────────────\n"
            f"📈 *OTP Traffic:*\n"
            f" ├ Today: `{total_today}`\n"
            f" ├ Weekly: `{total_week}`\n"
            f" └ Monthly: `{total_month}`\n\n"
            f"👥 *User Activity:*\n"
            f" └ Active Today: `{active_users}` users\n\n"
            f"🌍 *Top Traffic Today:*\n"
        )
        
        if traffic_rows:
            for row in traffic_rows:
                stats_msg += f" • {row[0]} | {row[1].upper()}: `{row[2]}`\n"
        else:
            stats_msg += " • _No traffic recorded today_\n"
            
        stats_msg += "──────────────────"
        
        kb = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="admin_stats")],
            [InlineKeyboardButton("⬅️ Back to Menu", callback_data="admin_panel")]
        ]
        
        await query.message.edit_text(
            text=stats_msg, 
            parse_mode=ParseMode.MARKDOWN, 
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return
        

    if data == "admin_backup":
        await query.message.reply_text("⏳ Preparing Backup...")
        memory_file = io.BytesIO()
        
        # Daftar file yang WAJIB masuk
        target_files = ['bot.py', 'numbers.db', 'requirements.txt']
        # Daftar folder yang HARUS dibuang
        exclude_dirs = {'.git', '__pycache__', '.cache', '.local', 'venv'}

        try:
            with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk('.'):
                    # Filter folder: hapus folder terlarang dari daftar pencarian
                    dirs[:] = [d for d in dirs if d not in exclude_dirs]
                    
                    for file in files:
                        # Masukkan file jika ada di target_files atau berakhiran .py/.txt/.db
                        # Tapi tetap selektif agar tidak memasukkan sampah
                        if file in target_files or file.endswith(('.py', '.db', '.txt')):
                            file_path = os.path.join(root, file)
                            # Ambil path relatif agar struktur zip rapi
                            arcname = os.path.relpath(file_path, '.')
                            zf.write(file_path, arcname=arcname)
            
            memory_file.seek(0)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            await query.message.reply_document(
                document=memory_file, 
                filename=f"Edogawa_Backup_{timestamp}.zip",
                caption="✅ Backup Complete!\nThis your backup."
            )
        except Exception as e:
            await query.message.reply_text(f"❌ Gagal backup: {e}")
        return

    if data == "admin_restart":
        await query.message.edit_text("🔄 The bot is restarting... Wait a moment.")
        # Tutup koneksi DB sebelum restart biar gak corrupt
        try:
            db._connection.close()
        except:
            pass
        os.execv(sys.executable, [sys.executable] + sys.argv)
        

    if data == "admin_remove_numbers":
        kb = []
        c = db.execute("SELECT DISTINCT country FROM numbers")
        for cn in c.fetchall(): kb.append([InlineKeyboardButton(cn[0], callback_data=f"remove_{cn[0]}")])
        kb.append([InlineKeyboardButton("⬅️ Back", callback_data="admin_panel")])
        await query.message.edit_text("Select country to purge:", reply_markup=InlineKeyboardMarkup(kb))
        return
    
    if data.startswith("remove_"):
        cntry = data.split("_", 1)[1]
        db.execute("DELETE FROM numbers WHERE country = ?", (cntry,))
        await query.answer(f"Deleted numbers for {cntry}", show_alert=True)
        await admin_panel(update, context)
        return

    # --- STATE BASED INPUTS (Add Numbers, Broadcast, Settings) ---
    
    if data == "admin_add_numbers":
        USER_STATE[user_id] = "WAITING_COUNTRY_NAME"
        await query.message.reply_text("🌍 Enter country name (Ex: United Kingdom):")
        return

    if data == "admin_broadcast":
        USER_STATE[user_id] = "WAITING_BROADCAST_MSG"
        await query.message.reply_text("📢 Send broadcast message:")
        return

    if data == "admin_find_number":
        USER_STATE[user_id] = "WAITING_FIND_NUMBER"
        await query.message.reply_text("🔍 Send number (+123...):")
        return

    if data == "admin_channel_settings":
        kb = [[InlineKeyboardButton("Main", callback_data="set_main"), InlineKeyboardButton("OTP", callback_data="set_otp")]]
        main_ch, _, _, otp_ch = get_channel_settings()
        await query.message.edit_text(f"Settings:\nMain: {main_ch}\nOTP: {otp_ch}", reply_markup=InlineKeyboardMarkup(kb))
        return
    
    if data in ["set_main", "set_otp"]:
        USER_STATE[user_id] = data
        await query.message.reply_text(f"Send new ID/Link for {data}:")
        return

async def text_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # PENGAMAN 1: Pastikan update.message tidak None (penting!)
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    text = update.message.text
    state = USER_STATE.get(user_id)

    if not state: 
        return

    print(f"DEBUG: Input dari {user_id} dengan state {state}: {text}")

    # --- Admin Logic ---
    if user_id in ADMIN_IDS:
        if state == "WAITING_COUNTRY_NAME":
            USER_STATE[user_id] = f"WAITING_FILE_{text}" # Store country in state key
            await update.message.reply_text(f"📤 Country: {text}\nNow send the .txt/.csv/.xlsx file.")
            return
        
        if state == "WAITING_BROADCAST_MSG":
            c = db.execute("SELECT user_id FROM users WHERE is_banned = 0")
            users = c.fetchall()
            count = 0
            for u in users:
                try: 
                    await context.bot.send_message(u[0], text)
                    count += 1
                except: pass
                await asyncio.sleep(0.05)
            await update.message.reply_text(f"✅ Sent to {count} users.")
            del USER_STATE[user_id]
            return

        if state == "WAITING_FIND_NUMBER":
            num = text.strip().replace(' ', '')
            if not num.startswith('+'): num = '+' + num
            res = db.execute("SELECT * FROM numbers WHERE number = ?", (num,)).fetchone()
            msg = f"Info: {dict(res)}" if res else "Not found."
            await update.message.reply_text(msg)
            del USER_STATE[user_id]
            return

        if state in ["set_main", "set_otp"]:
            if state == "set_main": update_channel_settings(main=text)
            elif state == "set_otp": update_channel_settings(otp=text)
            await update.message.reply_text("✅ Updated!")
            del USER_STATE[user_id]
            return

async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = USER_STATE.get(user_id)

    if user_id in ADMIN_IDS and state and state.startswith("WAITING_FILE_"):
        country_name = state.replace("WAITING_FILE_", "")
        
        doc = update.message.document
        if not doc.file_name.endswith(('.txt', '.csv', '.xlsx')):
            await update.message.reply_text("❌ Invalid format. Use .txt, .csv, or .xlsx")
            return
            
        waiting = await update.message.reply_text("⏳ Processing...")
        
        try:
            new_file = await doc.get_file()
            file_content = await new_file.download_as_bytearray()
            
            nums = extract_numbers_from_content(file_content, doc.file_name)
            
            count, duplicates = 0, 0
            with db._lock: 
                c = db._connection.cursor()
                for n in nums:
                    try: 
                        c.execute("INSERT INTO numbers (country, number) VALUES (?, ?)", (country_name, n))
                        count += 1
                    except sqlite3.IntegrityError:
                        duplicates += 1
                db._connection.commit()
            
            await context.bot.edit_message_text(f"✅ Success!\n🌍 {country_name}\n📥 Added: {count}\n♻️ Duplicates: {duplicates}", 
                                                chat_id=update.effective_chat.id, message_id=waiting.message_id)
        except Exception as e:
            logger.error(f"File error: {e}")
            await update.message.reply_text("❌ Error processing file.")
        
        del USER_STATE[user_id]

async def command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmd = update.message.text.split()[0]
    user_id = update.effective_user.id

    if cmd == '/backup' and user_id in ADMIN_IDS:
        await admin_panel(update, context) # Shortcut to panel action
    
    if cmd == '/push' and user_id in ADMIN_IDS:
        set_bot_status(False)
        await update.message.reply_text("✅ Maintenance ON.")
        
    if cmd == '/on' and user_id in ADMIN_IDS:
        set_bot_status(True)
        await update.message.reply_text("✅ Bot Online.")
        
async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    res = db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)).fetchone()
    balance = res['balance'] if res else 0.0000
    
    keyboard = [[InlineKeyboardButton("💳 Withdraw", callback_data="wd_start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"💳 <b>Your Balance:</b> {balance:.4f} USDT\n"
        f"<i>Minimum withdraw: 10 USDT</i>", 
        parse_mode=ParseMode.HTML, 
        reply_markup=reply_markup
    )

async def reff_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bot_username = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={user_id}"
    await update.message.reply_text(f"🔗 <b>Your Referral Link:</b>\n<code>{link}</code>", parse_mode=ParseMode.HTML)
    
async def sent_messages(session, username, already_sent, base_url):
    data = fetch_data(session, base_url)

    if data == "session_expired":
        return "relogin"
        
    elif data and 'aaData' in data:
        for row in data['aaData']:
            dt, rc, sn, msg = str(row[0]), str(row[2]), str(row[3]), str(row[4])
            
            match = re.search(r'\d{3}-\d{3}|\d{4,8}', msg)
            otp = match.group() if match else None

            if otp:
                sms_hash = hashlib.md5(f"{dt}{rc}{msg}".encode()).hexdigest()
                
                # Cek DB & Cache
                with db._lock:
                    check = db.execute("SELECT hash FROM public_sms_history WHERE hash=?", (sms_hash,)).fetchone()
                    if check or sms_hash in already_sent: continue
                    record_traffic(rc, sn, msg) 
                # Ambil settings
                _, _, _, otp_ch = get_channel_settings()
                
                # Format Public
                clean_rc = re.sub(r'\D', '', rc)
                masked = f"+{clean_rc[:5]}RILZ{clean_rc[-4:]}"
                text, markup = format_public_message(rc, sn, msg, otp, dt, masked)

                # --- FIX: Pakai Bridge Function agar tidak crash Loop ---
                send_async_message(otp_ch, text, parse_mode=ParseMode.HTML, reply_markup=markup, auto_delete=True)
                
                # Simpan History
                already_sent.add(sms_hash)
                with db._lock:
                    db.execute("INSERT OR IGNORE INTO public_sms_history (hash, date_added) VALUES (?, ?)", (sms_hash, dt))
                    db.commit()
                
                save_already_sent(username, already_sent)
                logging.info(f"[{username}] [+] OTP Terkirim ke Channel: {otp}")
    return None

async def worker(account):
    username = account['username']
    password = account['password']
    base_url = account['base_url']
    
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest"})
    already_sent = load_already_sent(username)

    while True:
        try:
            # Login ke URL spesifik akun
            if await login(session, username, password, base_url):
                logging.info(f"✅ [{username}] Login Sukses di {base_url}")
                while True:
                    result = await sent_messages(session, username, already_sent, base_url)
                    if result == "relogin": break
                    await asyncio.sleep(15)
            else:
                logging.error(f"❌ [{username}] Login Gagal di {base_url}. Retry 30s...")
                await asyncio.sleep(30)
        except Exception as e:
            logging.error(f"⚠️ Error Worker {username}: {e}")
            await asyncio.sleep(10)


async def main():
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    tasks = [worker(account) for account in ACCOUNTS]
    await asyncio.gather(*tasks)
        

async def post_init(application):
       global MAIN_LOOP
       MAIN_LOOP = asyncio.get_running_loop()
       logger.info("✅ Event Loop successfully captured via post_init!")

if __name__ == "__main__":
    from telegram.request import HTTPXRequest
    
    t_request = HTTPXRequest(connect_timeout=60, read_timeout=60)
    db.init_db()
    application = ApplicationBuilder().token(API_TOKEN).post_init(post_init).build()
    GLOBAL_APP = application

    # 2. Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("traffic", traffic_user_command))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("reff", reff_command))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_input_handler))
    application.add_handler(MessageHandler(filters.Document.ALL, document_handler))

    # 3. Threads
    logger.info("🔥 Starting Background Threads...")
    
    threading.Thread(target=start_watching_sms_api, args=(URL_API_1, T1, "API_1", TYPE_API_1), daemon=True).start()
    threading.Thread(target=start_watching_sms_api, args=(URL_API_2, T2, "API_2", TYPE_API_2), daemon=True).start()

    for acc in ACCOUNTS:
        def start_worker(a):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(worker(a))

        t = threading.Thread(target=start_worker, args=(acc,), daemon=True)
        t.start()
        logger.info(f"✅ Monitoring started for account: {acc['username']}")
        print("🚀 rilzz chaniago Bot is now Online...")
    application.run_polling(drop_pending_updates=True)
