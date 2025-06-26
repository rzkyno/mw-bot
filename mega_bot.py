import os
import json
import requests
from bs4 import BeautifulSoup
from collections import deque, Counter
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler

TOKEN = os.getenv("BOT_TOKEN")
RIWAYAT_FILE = "riwayat.json"
MAX_LEN = 500
riwayat = deque(maxlen=MAX_LEN)

def load_riwayat():
    try:
        with open(RIWAYAT_FILE, "r") as f:
            data = json.load(f)
            riwayat.extendleft(reversed(data[-MAX_LEN:]))
            print(f"✔️ Loaded {len(riwayat)} data dari file")
    except FileNotFoundError:
        print("⚠️ File riwayat.json belum ada, mulai baru.")
    except Exception as e:
        print("❌ Gagal load:", e)

def save_riwayat():
    try:
        with open(RIWAYAT_FILE, "w") as f:
            json.dump(list(riwayat), f)
            print(f"💾 Riwayat disimpan: {len(riwayat)} angka")
    except Exception as e:
        print("❌ Gagal simpan:", e)

def ambil_putaran_terakhir():
    url = "https://gamblingcounting.com/id/mega-wheel"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    tabel = soup.select_one("table tbody tr td:nth-of-type(2)")
    angka = int(tabel.text.strip())
    return angka

def update_data():
    try:
        angka = ambil_putaran_terakhir()
        if not riwayat or angka != riwayat[0]:
            riwayat.appendleft(angka)
            save_riwayat()
            print("🔄 Update angka terbaru:", angka)
    except Exception as e:
        print("❌ Gagal ambil data:", e)

def prediksi_angka(data):
    semua = [1, 2, 5, 8, 10, 15, 20, 30, 40]
    freq = Counter(data)
    total = len(data)
    peluang = {a: 1 - freq.get(a, 0) / total for a in semua}
    return sorted(peluang.items(), key=lambda x: x[1], reverse=True)[:3]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎡 Bot Prediksi Mega Wheel Siap!\nGunakan /prediksi untuk melihat angka potensial.")

async def prediksi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(riwayat) < 10:
        await update.message.reply_text("Data belum cukup. Mohon tunggu beberapa saat...")
        return
    top = prediksi_angka(list(riwayat))
    pesan = "🎯 Prediksi Angka Berikutnya:\n"
    for angka, skor in top:
        pesan += f"- {angka}: {round(skor * 100, 1)}%\n"
    await update.message.reply_text(pesan)

load_riwayat()

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("prediksi", prediksi))

scheduler = BackgroundScheduler()
scheduler.add_job(update_data, "interval", seconds=15)
scheduler.start()

print("🤖 Bot berjalan...")
app.run_polling()
