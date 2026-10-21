import asyncio
import logging
import os
import sqlite3
import json
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

# --- WEB DASHBOARD SERVER ---
async def web_dashboard(request):
    conn = sqlite3.connect("texnikumlar_baza.db")
    cursor = conn.cursor()
    cursor.execute("SELECT tr, texnikum_nomi, fio, xolati, lavozim, viloyat, tuman, phone FROM xodimlar")
    rows = cursor.fetchall()
    conn.close()

    js_leaders = []
    for r in rows:
        js_leaders.append({
            "id": r[0],
            "texnikum_nomi": str(r[1]),
            "fio": str(r[2]),
            "xolati": str(r[3]) if r[3] else "Doimiy",
            "lavozim": str(r[4]),
            "tuman": str(r[6]),
            "phone": str(r[7]) if r[7] and r[7] != 'nan' else ""
        })

    leaders_json = json.dumps(js_leaders, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="uz" class="h-full light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Boshqarma Boshlig'i Dashboard - Farg'ona Kasbiy Ta'lim</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            darkMode: 'class',
            theme: {{
                extend: {{
                    colors: {{
                        brand: {{ 50: '#f0f7ff', 100: '#e0effe', 500: '#0284c7', 600: '#0369a1', 700: '#075985', 800: '#0c4a6e', 900: '#0c3a57' }},
                        m3: {{ surfaceLight: '#F8F9FE', surfaceDark: '#111318', cardLight: '#FFFFFF', cardDark: '#1D2026', accent: '#1063FD' }}
                    }}
                }}
            }}
        }}
    </script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body {{ user-select: none; -webkit-user-select: none; touch-action: manipulation; font-family: 'Inter', sans-serif; }}
        .scroll-hide::-webkit-scrollbar {{ display: none; }}
        .scroll-hide {{ -ms-overflow-style: none; scrollbar-width: none; }}
    </style>
</head>
<body class="bg-gray-100 dark:bg-gray-950 text-gray-900 dark:text-gray-100 min-h-screen flex justify-center items-center p-0 sm:p-4">

    <div class="w-full max-w-md sm:max-w-lg md:max-w-xl h-screen sm:h-[915px] sm:rounded-[40px] bg-m3-surfaceLight dark:bg-m3-surfaceDark shadow-2xl overflow-hidden flex flex-col relative border-0 sm:border-8 sm:border-gray-800 dark:sm:border-gray-700">
        
        <!-- Status Bar -->
        <div class="w-full bg-slate-900 text-white px-6 pt-2 pb-1.5 flex justify-between items-center text-xs font-semibold tracking-wider z-50 shrink-0">
            <span id="current-time">09:41</span>
            <div class="flex items-center space-x-2">
                <i class="fa-solid fa-wifi text-[11px]"></i>
                <i class="fa-solid fa-signal text-[11px]"></i>
                <div class="flex items-center space-x-0.5">
                    <span class="text-[10px]">98%</span>
                    <i class="fa-solid fa-battery-full text-xs text-emerald-400"></i>
                </div>
            </div>
        </div>

        <!-- App Bar -->
        <header class="bg-slate-900 text-white px-5 py-3.5 flex justify-between items-center shrink-0 shadow-md z-40 border-b border-slate-800">
            <div class="flex items-center space-x-3">
                <div class="relative">
                    <div class="w-11 h-11 rounded-2xl bg-gradient-to-tr from-brand-600 to-blue-400 flex items-center justify-center font-bold text-white shadow-lg text-lg border-2 border-white/20">
                        <i class="fa-solid fa-user-tie"></i>
                    </div>
                    <span class="absolute bottom-0 right-0 w-3 h-3 bg-emerald-500 rounded-full border-2 border-slate-900"></span>
                </div>
                <div>
                    <span class="text-[10px] uppercase tracking-wider font-extrabold bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded-full border border-blue-400/30">Boshqarma Boshlig'i</span>
                    <h1 class="text-base font-bold tracking-tight text-white mt-0.5">Farg'ona Viloyati</h1>
                </div>
            </div>
            
            <div class="flex items-center space-x-1">
                <button onclick="toggleDarkMode()" class="w-9 h-9 rounded-xl bg-slate-800 hover:bg-slate-700 flex items-center justify-center text-gray-300 transition-colors">
                    <i id="theme-icon" class="fa-solid fa-moon text-sm"></i>
                </button>
            </div>
        </header>

        <!-- Main Content Area -->
        <div id="main-content" class="flex-1 overflow-y-auto scroll-hide p-4 space-y-4 pb-20">

            <!-- TAB 1: DASHBOARD -->
            <div id="view-dashboard" class="space-y-4">
                <div class="bg-gradient-to-r from-slate-900 via-brand-900 to-slate-900 text-white rounded-2xl p-4 shadow-lg border border-blue-500/20">
                    <div class="flex justify-between items-center mb-1">
                        <span class="text-xs text-blue-300 font-semibold uppercase tracking-wider"><i class="fa-solid fa-chart-line mr-1"></i> Nazorat Paneli</span>
                        <span class="text-[11px] bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded-full border border-emerald-400/30 font-medium">Jonli holat</span>
                    </div>
                    <h2 class="text-lg font-bold">Kasbiy Ta'lim Rahbariyat Tizimi</h2>
                    <p class="text-xs text-slate-300 mt-1">Farg'ona viloyatidagi <b class="text-white">67 ta texnikum</b> va <b class="text-white">268 nafar rahbar</b> kadrlar bazasi.</p>
                </div>

                <div class="grid grid-cols-2 gap-3">
                    <div onclick="switchTab('kadrlar');" class="bg-white dark:bg-m3-cardDark p-3.5 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-800 cursor-pointer">
                        <div class="text-2xl font-extrabold text-gray-900 dark:text-white">67</div>
                        <div class="text-xs text-gray-500 dark:text-gray-400 font-medium mt-0.5">Jami Texnikumlar</div>
                    </div>
                    <div onclick="switchTab('kadrlar');" class="bg-white dark:bg-m3-cardDark p-3.5 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-800 cursor-pointer">
                        <div class="text-2xl font-extrabold text-gray-900 dark:text-white" id="stat-total-kadrs">268</div>
                        <div class="text-xs text-gray-500 dark:text-gray-400 font-medium mt-0.5">Jami Rahbarlar</div>
                    </div>
                </div>

                <div class="bg-white dark:bg-m3-cardDark rounded-2xl p-4 shadow-sm border border-gray-100 dark:border-gray-800 space-y-3">
                    <h3 class="text-sm font-bold text-gray-900 dark:text-white">Lavozimlar Kesimida Holat</h3>
                    <div class="relative h-52">
                        <canvas id="roleStatusChart"></canvas>
                    </div>
                </div>
            </div>

            <!-- TAB 2: KADRLAR DIRECTORY -->
            <div id="view-kadrlar" class="hidden space-y-3">
                <div class="bg-white dark:bg-m3-cardDark rounded-2xl p-3.5 shadow-sm border border-gray-100 dark:border-gray-800 space-y-3 sticky top-0 z-30">
                    <div class="relative">
                        <i class="fa-solid fa-magnifying-glass absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 text-xs"></i>
                        <input type="text" id="kadrlar-search" oninput="applyFilters()" placeholder="F.I.Sh, Texnikum yoki Tuman bo'yicha..." 
                            class="w-full pl-9 pr-4 py-2.5 bg-gray-100 dark:bg-gray-800 rounded-xl text-xs border-0 text-gray-900 dark:text-gray-100 outline-none">
                    </div>
                    <div class="grid grid-cols-2 gap-2">
                        <select id="filter-status" onchange="applyFilters()" class="py-2 px-2.5 bg-gray-100 dark:bg-gray-800 rounded-xl text-xs text-gray-800 dark:text-gray-200 outline-none">
                            <option value="all">Barcha Holatlar</option>
                            <option value="Doimiy">Doimiy</option>
                            <option value="v.v.b">Vaqtincha</option>
                            <option value="vk">Vakant</option>
                        </select>
                        <select id="filter-role" onchange="applyFilters()" class="py-2 px-2.5 bg-gray-100 dark:bg-gray-800 rounded-xl text-xs text-gray-800 dark:text-gray-200 outline-none">
                            <option value="all">Barcha Lavozimlar</option>
                            <option value="Direktor">Direktorlar</option>
                            <option value="o'quv">O'quv o'rinbosarlari</option>
                            <option value="yoshlar">Yoshlar o'rinbosarlari</option>
                            <option value="ishlab chiqarish">Ishlab chiqarish</option>
                        </select>
                    </div>
                </div>
                <div class="text-xs text-gray-500 px-1" id="results-count">Natijalar yuklanmoqda...</div>
                <div id="leaders-container" class="space-y-3"></div>
            </div>

            <!-- TAB 3: ANALYTICS -->
            <div id="view-analitika" class="hidden space-y-4">
                <div class="bg-white dark:bg-m3-cardDark rounded-2xl p-4 shadow-sm border border-gray-100 dark:border-gray-800 space-y-3">
                    <h3 class="text-sm font-bold text-gray-900 dark:text-white">Shtat Birliklari Nisbati</h3>
                    <div class="relative h-56 flex justify-center">
                        <canvas id="statusDoughnutChart"></canvas>
                    </div>
                </div>
            </div>

            <!-- TAB 4: REPORTS -->
            <div id="view-hisobot" class="hidden space-y-4">
                <div class="bg-white dark:bg-m3-cardDark rounded-2xl p-4 shadow-sm border border-gray-100 dark:border-gray-800 space-y-3">
                    <h3 class="text-sm font-bold text-gray-900 dark:text-white">Rasmiy Hisobotlar</h3>
                    <p class="text-xs text-gray-500">Baza ma'lumotlari to'liq sinxronlangan.</p>
                </div>
            </div>

        </div>

        <!-- Bottom Navigation -->
        <nav class="bg-white dark:bg-slate-900 border-t border-gray-200 dark:border-slate-800 px-3 py-2 flex justify-around items-center shrink-0 z-50">
            <button onclick="switchTab('dashboard')" id="nav-dashboard" class="nav-btn flex flex-col items-center space-y-1 text-brand-600 dark:text-brand-400 font-bold">
                <i class="fa-solid fa-chart-line text-lg"></i>
                <span class="text-[10px]">Bosh sahifa</span>
            </button>
            <button onclick="switchTab('kadrlar')" id="nav-kadrlar" class="nav-btn flex flex-col items-center space-y-1 text-gray-400 font-medium">
                <i class="fa-solid fa-id-card-clip text-lg"></i>
                <span class="text-[10px]">Kadrlar</span>
            </button>
            <button onclick="switchTab('analitika')" id="nav-analitika" class="nav-btn flex flex-col items-center space-y-1 text-gray-400 font-medium">
                <i class="fa-solid fa-chart-pie text-lg"></i>
                <span class="text-[10px]">Analitika</span>
            </button>
            <button onclick="switchTab('hisobot')" id="nav-hisobot" class="nav-btn flex flex-col items-center space-y-1 text-gray-400 font-medium">
                <i class="fa-solid fa-folder-open text-lg"></i>
                <span class="text-[10px]">Hisobotlar</span>
            </button>
        </nav>
    </div>

    <!-- Frontend Script Logic -->
    <script>
        const LEADERS_DATA = {leaders_json};
        let currentFilteredData = [...LEADERS_DATA];

        document.addEventListener("DOMContentLoaded", () => {{
            document.getElementById('stat-total-kadrs').innerText = LEADERS_DATA.length;
            renderLeadersList(LEADERS_DATA);
            initCharts();
        }});

        function switchTab(tabName) {{
            ['dashboard', 'kadrlar', 'analitika', 'hisobot'].forEach(tab => {{
                document.getElementById(`view-${tab}`).classList.toggle('hidden', tab !== tabName);
                document.getElementById(`nav-${tab}`).className = tab === tabName ? 
                    "nav-btn flex flex-col items-center space-y-1 text-brand-600 dark:text-brand-400 font-bold" : 
                    "nav-btn flex flex-col items-center space-y-1 text-gray-400 font-medium";
            }});
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }}

        function toggleDarkMode() {{
            const html = document.documentElement;
            const isDark = html.classList.toggle('dark');
            document.getElementById('theme-icon').className = isDark ? 'fa-solid fa-sun text-sm text-amber-400' : 'fa-solid fa-moon text-sm';
        }}

        function renderLeadersList(data) {{
            const container = document.getElementById('leaders-container');
            document.getElementById('results-count').innerText = `Topilgan kadrlar: ${{data.length}} nafar`;

            if (data.length === 0) {{
                container.innerHTML = `<div class="text-center py-10 text-gray-500 text-xs">Ma'lumot topilmadi</div>`;
                return;
            }}

            container.innerHTML = data.map(item => `
                <div class="bg-white dark:bg-m3-cardDark rounded-2xl p-4 shadow-sm border border-gray-100 dark:border-gray-800 space-y-2">
                    <div class="flex justify-between items-start">
                        <div>
                            <span class="text-[10px] font-bold text-brand-600 dark:text-brand-400 uppercase">${{item.tuman}} tumani</span>
                            <h4 class="text-sm font-bold text-gray-900 dark:text-white mt-0.5">${{item.fio}}</h4>
                            <div class="text-xs text-gray-500">${{item.lavozim}}</div>
                        </div>
                        <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-600">${{item.xolati}}</span>
                    </div>
                    <div class="text-xs text-gray-600 dark:text-gray-300 font-medium">🏫 ${{item.texnikum_nomi}}</div>
                    ${{item.phone ? `<a href="tel:${{item.phone}}" class="block text-xs text-blue-500 font-semibold mt-1">📞 ${{item.phone}}</a>` : ''}}
                </div>
            `).join('');
        }}

        function applyFilters() {{
            const q = document.getElementById('kadrlar-search').value.toLowerCase();
            const status = document.getElementById('filter-status').value;
            const role = document.getElementById('filter-role').value;

            currentFilteredData = LEADERS_DATA.filter(i => {{
                const matchQ = i.fio.toLowerCase().includes(q) || i.texnikum_nomi.toLowerCase().includes(q) || i.tuman.toLowerCase().includes(q);
                const matchS = status === 'all' || i.xolati.toLowerCase().includes(status.toLowerCase());
                const matchR = role === 'all' || i.lavozim.toLowerCase().includes(role.toLowerCase());
                return matchQ && matchS && matchR;
            }});
            renderLeadersList(currentFilteredData);
        }}

        function initCharts() {{
            new Chart(document.getElementById('roleStatusChart').getContext('2d'), {{
                type: 'bar',
                data: {{
                    labels: ['Direktor', 'O\'quv', 'Yoshlar', 'Ishlab chiqarish'],
                    datasets: [{{ label: 'Soni', data: [67, 67, 67, 67], backgroundColor: '#0284c7' }}]
                }},
                options: {{ responsive: true, maintainAspectRatio: false }}
            }});

            new Chart(document.getElementById('statusDoughnutChart').getContext('2d'), {{
                type: 'doughnut',
                data: {{
                    labels: ['Doimiy', 'Vaqtincha', 'Vakant'],
                    datasets: [{{ data: [218, 28, 22], backgroundColor: ['#10B981', '#F59E0B', '#EF4444'] }}]
                }},
                options: {{ responsive: true, maintainAspectRatio: false }}
            }});
        }}
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
