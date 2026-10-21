import asyncio
import logging
import sqlite3
import pandas as pd
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Telegram Bot Tokeningizni kiriting
API_TOKEN = "8786802772:AAHSvzLvgCQLXt7aCl2Wk1PZj0Rg0H8uA9Q"

logging.basicConfig(level=logging.INFO)

EXCEL_FILE = "kelishuv_baza_svod_avtomatik oxirgi.xlsx"

def setup_database():
    """Excel fayldan ma'lumotlarni o'qib, SQLite bazasiga avtomatik yuklaydi"""
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

            texnikum_nomi = str(row[1])
            fio = str(row[2])
            xolati = str(row[3]) if str(row[3]) != "" else "Doimiy"
            lavozim = str(row[4])
            viloyat = str(row[5])
            tuman = str(row[6])
            mfy = str(row[7])
            kocha = str(row[8])
            uy = str(row[9])
            tugilgan_yili = str(row[10])
            phone = str(row[11])
            tatil = str(row[12])

            cursor.execute("""
                INSERT INTO xodimlar VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (tr, texnikum_nomi, fio, xolati, lavozim, viloyat, tuman, mfy, kocha, uy, tugilgan_yili, phone, tatil))
            
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
        "Quyidagi bo'limlardan birini tanlang yoki **Texnikum nomi / Xodim F.I.Sh** bo'yicha qidiruv uchun matn yuboring:"
    )
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "svod_stat")
async def show_svod(callback: types.CallbackQuery):
    try:
        df_svod = pd.read_excel(EXCEL_FILE, sheet_name="Svod", header=None)
        df_svod = df_svod.fillna(0)
        
        # Excel Svod varog'idagi to'g'ri qator indekslari:
        # 0: Texnikumlar soni (67)
        # 2: Direktorlar jami, 3: Doimiy, 4: Vaqtincha, 5: Vakant
        # 7: O'rinbosarlar jami, 8: Doimiy, 9: Vaqtincha, 10: Vakant
        
        dir_jami = int(df_svod.iloc[2, 1])
        dir_doimiy = int(df_svod.iloc[3, 1])
        dir_vaqtincha = int(df_svod.iloc[4, 1])
        dir_vakant = int(df_svod.iloc[5, 1])

        orin_jami = int(df_svod.iloc[7, 1])
        orin_doimiy = int(df_svod.iloc[8, 1])
        orin_vaqtincha = int(df_svod.iloc[9, 1])
        orin_vakant = int(df_svod.iloc[10, 1])

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
        svod_text = f"Statistikani o'qishda xatolik yuz berdi: {e}"

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
    cursor.execute("""
        SELECT texnikum_nomi, fio, lavozim, phone, tuman, xolati 
        FROM xodimlar 
        WHERE fio LIKE ? OR texnikum_nomi LIKE ? OR tuman LIKE ?
        LIMIT 15
    """, (f'%{query}%', f'%{query}%', f'%{query}%'))
    
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

async def main():
    setup_database()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())