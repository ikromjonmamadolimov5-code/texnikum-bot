import asyncio
import logging
import os
import sqlite3
import pandas as pd
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# Telegram Bot Tokeningizni kiriting
API_TOKEN = "8786802772:AAHSvzLvgCQLXt7aCl2Wk1PZj0Rg0H8uA9Q"

logging.basicConfig(level=logging.INFO)
EXCEL_FILE = "kelishuv_baza_svod_avtomatik oxirgi.xlsx"

def setup_database():
    conn = sqlite3.connect("texnikumlar_baza.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS xodimlar (
            tr INTEGER,
            texnikum_nomi TEXT,
            fio TEXT,
            xolati TEXT,
            lavozim TEXT,
            viloyat TEXT,
            tuman TEXT,
            mfy TEXT,
            kocha TEXT,
            uy TEXT,
            tugilgan_yili TEXT,
            phone TEXT,
            tatil TEXT
        )
    """)
    cursor.execute("DELETE FROM xodimlar")
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name="Лист1", skiprows=3, header=None)
        df = df.fillna("")
        for index, row in df.iterrows():
            if str(row[0]).strip() == "":
                continue
            try:
                tr = int(row[0])
            except:
                continue
            cursor.execute("INSERT INTO xodimlar VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                           (tr, str(row[1]), str(row[2]), str(row[3]) if str(row[3]) != "" else "Doimiy", 
                            str(row[4]), str(row[5]), str(row[6]), str(row[7]), str(row[8]), str(row[9]), 
                            str(row[10]), str(row[11]), str(row[12])))
        conn.commit()
        print("✅ Ma'lumotlar bazaga muvaffaqiyatli yuklandi!")
    except Exception as e:
        print(f"⚠️ Bazaga yuklashda xatolik: {e}")
    finally:
        conn.close()

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Umumiy Svod (Statistika)", callback_data="svod_stat")],
        [InlineKeyboardButton(text="👨‍💼 Direktorlar", callback_data="filter_Direktor")],
        [InlineKeyboardButton(text="👥 O'quv ishlari o'rinbosarlari", callback_data="filter_o'quv")],
        [InlineKeyboardButton(text="⚡ Yoshlar bilan ishlash o'rinbosarlari", callback_data="filter_yoshlar")],
        [InlineKeyboardButton(text="🛠 Ishlab chiqarish o'rinbosarlari", callback_data="filter_ishlab")],
        [InlineKeyboardButton(text="🔍 Vakant o'rinlar", callback_data="filter_vakant")]
    ])
    text = (
        "👋 **Farg'ona viloyati kasbiy ta'lim boshqarmasi**\n"
        "Texnikum rahbar kadrlar ma'lumot bazasiga xush kelibsiz!\n\n"
        "Quyidagi bo'limlardan birini tanlang yoki qidiruv uchun matn yuboring:"
    )
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "svod_stat")
async def show_svod(callback: types.CallbackQuery):
    try:
        df_svod = pd.read_excel(EXCEL_FILE, sheet_name="Svod", header=None).fillna(0)
        dir_jami, dir_doimiy, dir_vaqtincha, dir_vakant = int(df_svod.iloc[2, 1]), int(df_svod.iloc[3, 1]), int(df_svod.iloc[4, 1]), int(df_svod.iloc[5, 1])
        orin_jami, orin_doimiy, orin_vaqtincha, orin_vakant = int(df_svod.iloc[7, 1]), int(df_svod.iloc[8, 1]), int(df_svod.iloc[9, 1]), int(df_svod.iloc[10, 1])
        svod_text = (
            "📊 **UMUMIY SVOD MA'LUMOTLARI (RASMIY BAZA)**\n\n"
            f"🏫 **Texnikumlar soni:** 67 ta\n\n"
            f"👔 **Direktorlar jami:** {dir_jami} ta\n"
            f"  ├ Doimiy: {dir_doimiy} ta\n"
            f"  ├ Vaqtincha: {dir_vaqtincha} ta\n"
            f"  └ Vakant: {dir_vakant} ta\n\n"
            f"👥 **O'rinbosarlar jami:** {orin_jami} ta\n"
            f"  ├ Doimiy: {orin_doimiy} ta\n"
            f"  ├ Vaqtincha: {orin_vaqtincha} ta\n"
            f"  └ Vakant: {orin_vakant} ta"
        )
    except Exception as e:
        svod_text = f"Xatolik: {e}"
    await callback.message.answer(svod_text, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("filter_"))
async def process_filter(callback: types.CallbackQuery):
    f_type = callback.data.split("_")[1]
    conn = sqlite3.connect("texnikumlar_baza.db")
    cursor = conn.cursor()
    if f_type == "Direktor":
        cursor.execute("SELECT texnikum_nomi, fio, lavozim, phone, xolati FROM xodimlar WHERE lavozim = 'Direktor'")
    elif f_type == "o'quv":
        cursor.execute("SELECT texnikum_nomi, fio, lavozim, phone, xolati FROM xodimlar WHERE lavozim LIKE '%o‘quv%' OR lavozim LIKE '%oquv%'")
    elif f_type == "yoshlar":
        cursor.execute("SELECT texnikum_nomi, fio, lavozim, phone, xolati FROM xodimlar WHERE lavozim LIKE '%yoshlar%'")
    elif f_type == "ishlab":
        cursor.execute("SELECT texnikum_nomi, fio, lavozim, phone, xolati FROM xodimlar WHERE lavozim LIKE '%ishlab chiqarish%'")
    elif f_type == "vakant":
        cursor.execute("SELECT texnikum_nomi, fio, lavozim, phone, xolati FROM xodimlar WHERE xolati = 'vk' OR xolati = 'v' OR fio LIKE '%vakant%'")
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        await callback.message.answer("Ma'lumot topilmadi.")
        return
    res = f"📋 **Natijalar (Jami: {len(rows)} ta):**\n\n"
    for r in rows:
        phone_str = r[3] if r[3] and r[3] != 'nan' and r[3] != '' else "Kiritilmagan"
        status_str = f" [{r[4]}]" if r[4] and r[4] != 'nan' and r[4] != '' else ""
        res += f"🏫 **{r[0]}**\n👤 **{r[1]}**{status_str}\n📌 {r[2]}\n📞 Tel: {phone_str}\n---------------\n"
        if len(res) > 3500:
            await callback.message.answer(res, parse_mode="Markdown")
            res = ""
    if res:
        await callback.message.answer(res, parse_mode="Markdown")
    await callback.answer()

@dp.message()
async def search_handler(message: types.Message):
    query = message.text.strip()
    if len(query) < 2:
        await message.answer("Qidirish uchun kamida 2 ta harf kiriting.")
        return
    conn = sqlite3.connect("texnikumlar_baza.db")
    cursor = conn.cursor()
    cursor.execute("SELECT texnikum_nomi, fio, lavozim, phone, tuman, xolati FROM xodimlar WHERE fio LIKE ? OR texnikum_nomi LIKE ? OR tuman LIKE ? LIMIT 15", (f'%{query}%', f'%{query}%', f'%{query}%'))
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        await message.answer("🔍 Qidiruv bo'yicha hech qanday ma'lumot topilmadi.")
        return
    res = f"🔎 **\"{query}\" bo'yicha qidiruv natijalari:**\n\n"
    for r in rows:
        phone_str = r[3] if r[3] and r[3] != 'nan' and r[3] != '' else "Kiritilmagan"
        res += f"🏫 **{r[0]}** ({r[4]})\n👤 **{r[1]}**\n📌 {r[2]}\n📞 Tel: {phone_str}\n---------------\n"
    await message.answer(res, parse_mode="Markdown")

# --- WEB DASHBOARD SERVER (TELEFON ILOVA UCHUN) ---
async def web_dashboard(request):
    conn = sqlite3.connect("texnikumlar_baza.db")
    cursor = conn.cursor()
    cursor.execute("SELECT texnikum_nomi, fio, lavozim, phone, tuman, xolati FROM xodimlar")
    rows = cursor.fetchall()
    
    total_kadrlar = len(rows)
    doimiy = sum(1 for r in rows if not r[5] or 'doimiy' in str(r[5]).lower())
    vakant = sum(1 for r in rows if 'vk' in str(r[5]).lower() or 'v' in str(r[5]).lower() or 'vakant' in str(r[1]).lower())
    
    conn.close()

    cards_html = ""
    for r in rows:
        tuman = r[4] if r[4] else ""
        texnikum = r[0] if r[0] else ""
        fio = r[1] if r[1] else ""
        xolati = r[5] if r[5] else "Doimiy"
        lavozim = r[2] if r[2] else ""
        phone = r[3] if r[3] and r[3] != 'nan' and r[3] != '' else 'Kiritilmagan'
        
        cards_html += f"""
        <div class="bg-slate-800 p-4 rounded-2xl shadow-sm border border-slate-700 mb-3 hover:border-slate-600 transition">
            <div class="flex justify-between items-center mb-1">
                <span class="text-[11px] font-bold uppercase tracking-wider text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded-md">{tuman}</span>
                <span class="text-[11px] font-medium text-slate-400 bg-slate-700 px-2 py-0.5 rounded-md">{xolati}</span>
            </div>
            <div class="font-bold text-white text-sm mb-1">{texnikum}</div>
            <div class="text-slate-200 text-sm font-semibold flex items-center gap-1.5 mt-1">
                <span>👤</span> {fio}
            </div>
            <div class="text-slate-400 text-xs mt-1">📌 {lavozim}</div>
            <div class="mt-3 pt-2 border-t border-slate-700/50 flex justify-between items-center text-xs">
                <span class="text-slate-400">Telefon:</span>
                <a href="tel:{phone}" class="text-blue-400 font-bold bg-blue-500/10 px-2.5 py-1 rounded-lg">📞 {phone}</a>
            </div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Farg'ona Texnikum HR - Nazorat Paneli</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="mobile-web-app-capable" content="yes">
    <link rel="icon" href="https://img.icons8.com/color/96/administrator-male.png">
</head>
<body class="bg-slate-900 text-slate-100 p-3 max-w-md mx-auto font-sans">
    
    <!-- HEADER -->
    <div class="flex justify-between items-center bg-slate-800 p-4 rounded-2xl shadow-lg mb-4 border border-slate-700">
        <div class="flex items-center gap-3">
            <div class="bg-blue-600 p-2.5 rounded-xl shadow-md text-white font-bold">👨‍💼</div>
            <div>
                <div class="text-[10px] tracking-wider uppercase text-blue-400 font-bold">Boshqarma Boshlig'i</div>
                <div class="text-base font-bold text-white">Farg'ona Viloyati</div>
            </div>
        </div>
        <div class="flex gap-2">
            <div class="bg-slate-700 p-2 rounded-xl text-slate-300">🌙</div>
            <div class="bg-slate-700 p-2 rounded-xl text-slate-300">🔔</div>
        </div>
    </div>

    <!-- HERO CARD -->
    <div class="bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700 p-5 rounded-2xl shadow-xl mb-4 relative overflow-hidden">
        <div class="flex justify-between items-center mb-2">
            <span class="text-xs font-semibold text-blue-400 tracking-wide uppercase">📊 Nazorat Paneli</span>
            <span class="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-[10px] font-bold px-2.5 py-1 rounded-full flex items-center gap-1.5">
                <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> Jonli holat
            </span>
        </div>
        <h2 class="text-lg font-bold text-white mb-1">Kasbiy Ta'lim Rahbariyat Tizimi</h2>
        <p class="text-xs text-slate-400 leading-relaxed">Farg'ona viloyatidagi <strong class="text-white">67 ta texnikum</strong> va <strong class="text-white">{total_kadrlar} nafar rahbar</strong> kadrlar bo'yicha tezkor svod va analitika.</p>
    </div>

    <!-- STATS GRID -->
    <div class="grid grid-cols-2 gap-3 mb-4">
        <div class="bg-slate-800 border border-slate-700/60 p-4 rounded-2xl shadow-sm">
            <div class="text-xs text-slate-400 mb-1">Jami Texnikumlar</div>
            <div class="text-2xl font-black text-white">67</div>
            <div class="text-[10px] text-emerald-400 font-semibold mt-1">100% qamrov</div>
        </div>
        <div class="bg-slate-800 border border-slate-700/60 p-4 rounded-2xl shadow-sm">
            <div class="text-xs text-slate-400 mb-1">Jami Rahbar Kadrlar</div>
            <div class="text-2xl font-black text-white">{total_kadrlar}</div>
            <div class="text-[10px] text-blue-400 font-semibold mt-1">4 shtat / texnikum</div>
        </div>
        <div class="bg-slate-800 border border-slate-700/60 p-4 rounded-2xl shadow-sm">
            <div class="text-xs text-slate-400 mb-1">Doimiy Tayinlangan</div>
            <div class="text-2xl font-black text-emerald-400">{doimiy}</div>
            <div class="text-[10px] text-slate-400 font-semibold mt-1">Asosiy tarkib</div>
        </div>
        <div class="bg-slate-800 border border-slate-700/60 p-4 rounded-2xl shadow-sm border-l-4 border-l-rose-500">
            <div class="text-xs text-slate-400 mb-1">Vakant O'rinlar</div>
            <div class="text-2xl font-black text-rose-400">{vakant}</div>
            <div class="text-[10px] text-rose-400/80 font-semibold mt-1">Bo'sh o'rinlar</div>
        </div>
    </div>

    <!-- SEARCH INPUT -->
    <div class="mb-4">
        <input type="text" id="search" placeholder="🔍 Texnikum yoki F.I.Sh bo'yicha qidirish..." class="w-full p-3.5 rounded-xl bg-slate-800 border border-slate-700 text-sm text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 shadow-inner">
    </div>

    <!-- LIST OF CARDS -->
    <div id="list">
        {cards_html}
    </div>

    <script>
        document.getElementById('search').addEventListener('input', function(e) {{
            let val = e.target.value.toLowerCase();
            let cards = document.querySelectorAll('#list > div');
            cards.forEach(card => {{
                let text = card.innerText.toLowerCase();
                card.style.display = text.includes(val) ? 'block' : 'none';
            }});
        }});
    </script>
</body>
</html>"""
    return web.Response(text=html, content_type='text/html')

async def start_web():
    app = web.Application()
    app.router.add_get('/', web_dashboard)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🌐 Veb Dashboard {port}-portda ishga tushdi!")

async def main():
    setup_database()
    web_task = asyncio.create_task(start_web())
    polling_task = asyncio.create_task(dp.start_polling(bot))
    await asyncio.gather(web_task, polling_task)

if __name__ == "__main__":
    asyncio.run(main())
