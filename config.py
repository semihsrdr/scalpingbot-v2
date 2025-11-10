import os
from dotenv import load_dotenv

# .env dosyasındaki değişkenleri yükle
load_dotenv()

# Groq Ayarları
# Ortamdaki GROQ_API_KEY, GROQ_API_KEY1, GROQ_API_KEY2 vb. tüm anahtarları bulup bir listeye atar.
GROQ_API_KEYS = [
    key for key_name, key in os.environ.items() 
    if key_name.startswith("GROQ_API_KEY") and key
]
if not GROQ_API_KEYS:
    raise ValueError("UYARI: .env dosyasında 'GROQ_API_KEY' ile başlayan hiçbir API anahtarı bulunamadı!")
print(f"Found {len(GROQ_API_KEYS)} Groq API keys.")

LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME")

# Binance Ayarları
BINANCE_API_KEY = os.getenv("BINANCE_TESTNET_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_TESTNET_API_SECRET")
# TRADING_SYMBOL'ı TRADING_SYMBOLS olarak değiştirip listeye çeviriyoruz.
# .env dosyasından "BTC/USDT,ETH/USDT" gibi virgülle ayrılmış bir string olarak okunabilir.
symbols_from_env = os.getenv("TRADING_SYMBOLS", "BTC/USDT,ETH/USDT,DOGE/USDT,SOL/USDT,XRP/USDT")
TRADING_SYMBOLS = [symbol.strip() for symbol in symbols_from_env.split(',')]


if not BINANCE_API_KEY:
    print("UYARI: API anahtarları .env dosyasında eksik!")

# Simülasyon Ayarları
SIMULATION_MODE = os.getenv("SIMULATION_MODE", "True").lower() in ('true', '1', 't')
SIMULATION_STARTING_BALANCE = float(os.getenv("SIMULATION_STARTING_BALANCE", 1000.0))

# Trade Strateji Ayarları
TAKE_PROFIT_PCT = float(os.getenv("TAKE_PROFIT_PCT", 25.0)) # Yüzde olarak
STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", 15.0))   # Yüzde olarak