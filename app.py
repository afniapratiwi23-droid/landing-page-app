import streamlit as st
import google.generativeai as genai
import streamlit.components.v1 as components

# --- CONFIGURATION & SETUP ---
st.set_page_config(
    page_title="Landing Page Generator AI",
    page_icon="🚀",
    layout="wide"
)

import json

import requests
from bs4 import BeautifulSoup

# --- HELPER FUNCTIONS ---
def scrape_content(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
            
        # Get text
        text = soup.get_text(separator=' ')
        
        # Break into lines and remove leading/trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text[:5000] # Limit characters
    except Exception as e:
        return f"Gagal scraping: {e}"

import os

# --- SIDEBAR ---
with st.sidebar:
    st.header("Konfigurasi")
    
    # Try to load existing key
    current_keys_str = ""
    if "GOOGLE_API_KEY" in st.secrets:
        if st.secrets["GOOGLE_API_KEY"] != "PASTE_YOUR_API_KEY_HERE":
            current_keys_str = st.secrets["GOOGLE_API_KEY"]
            
    # Split existing keys for pre-filling
    current_keys_list = [k.strip() for k in current_keys_str.split('\n') if k.strip()]

    st.info("Masukkan hingga 10 API Key. Sistem akan otomatis ganti ke key berikutnya jika limit habis.")
    
    new_api_keys = []
    with st.expander("🔑 Kelola API Keys (Max 10)", expanded=True):
        for i in range(10):
            # Get existing value if available
            val = current_keys_list[i] if i < len(current_keys_list) else ""
            key_input = st.text_input(
                f"API Key #{i+1}", 
                value=val,
                type="password",
                placeholder=f"Paste API Key ke-{i+1} di sini...",
                key=f"api_key_input_{i}"
            )
            if key_input.strip():
                new_api_keys.append(key_input.strip())
    
    if st.button("💾 Simpan API Keys (Sesi Ini)"):
        if new_api_keys:
            st.session_state.saved_api_keys = new_api_keys
            st.success(f"✅ Tersimpan {len(new_api_keys)} API Keys untuk sesi ini!")
            st.info("💡 Keys akan aktif selama browser tidak di-refresh. Untuk save permanen, edit file `.streamlit/secrets.toml` secara manual.")
        else:
            st.warning("Minimal isi 1 API Key dong bos!")
            
    st.divider()

st.sidebar.header("Pilih Jenis Produk")
product_type = st.sidebar.radio(
    "Kategori:",
    ("Ebook / Produk Digital", "Produk Fisik / Barang")
)

# --- API KEY SETUP ---
# Use the keys collected from the inputs (if any) or load from secrets or session state
if 'saved_api_keys' not in st.session_state:
    st.session_state.saved_api_keys = []

# Priority: new_api_keys from current input > session state > secrets file
if new_api_keys:
    api_keys = new_api_keys
    st.session_state.saved_api_keys = new_api_keys  # Save to session for persistence during session
elif st.session_state.saved_api_keys:
    api_keys = st.session_state.saved_api_keys
elif "GOOGLE_API_KEY" in st.secrets:
    raw_keys = st.secrets["GOOGLE_API_KEY"]
    api_keys = [k.strip() for k in raw_keys.split('\n') if k.strip()]
    st.session_state.saved_api_keys = api_keys
else:
    api_keys = []

# --- HELPER: ROTATION GENERATOR ---
def generate_content_with_rotation(prompt, keys):
    last_error = None
    for i, key in enumerate(keys):
        try:
            genai.configure(api_key=key)
            # Try Flash model first (2.0), fallback to latest alias
            try:
                model = genai.GenerativeModel('gemini-2.0-flash')
                response = model.generate_content(prompt)
                return response
            except Exception:
                model = genai.GenerativeModel('gemini-flash-latest')
                response = model.generate_content(prompt)
                return response
        except Exception as e:
            last_error = e
            print(f"Key {i+1} failed: {e}")
            continue # Try next key
    
    # If all failed
    raise last_error

if api_keys:
    # Configure with first key just for init (though rotation handles it)
    genai.configure(api_key=api_keys[0])

# --- MAIN CONTENT ---
st.title("🚀 Landing Page Generator AI")
st.markdown("Buat landing page profesional dalam hitungan detik menggunakan Google Gemini.")

# --- SESSION STATE INIT ---
if "target_audience" not in st.session_state: st.session_state.target_audience = ""
if "cta_text" not in st.session_state: st.session_state.cta_text = ""
if "product_desc" not in st.session_state: st.session_state.product_desc = ""

# --- INPUT SECTION ---
product_name = st.text_input("Nama Produk (Wajib)", placeholder="Contoh: Ebook Jago Python / Sepatu Anti Air")

if st.button("✨ Isi Otomatis (Magic Fill)"):
    if not product_name:
        st.error("Isi Nama Produk dulu dong!")
    elif not api_keys:
        st.error("API Key belum ada! Cek sidebar.")
    else:
        with st.spinner("Sedang menerawang ide marketing..."):
            try:
                prompt = f"""
                Berikan ide marketing untuk produk: "{product_name}".
                Outputkan HANYA JSON dengan format:
                {{
                    "target_audience": "Target audience spesifik",
                    "cta_text": "Kata-kata tombol CTA yang menarik (pendek)",
                    "product_desc": "Deskripsi produk yang persuasif (2-3 kalimat)"
                }}
                """
                
                response = generate_content_with_rotation(prompt, api_keys)
                
                text = response.text.replace("```json", "").replace("```", "")
                data = json.loads(text)
                
                # Handle case where AI returns a list instead of dict
                if isinstance(data, list):
                    data = data[0]
                
                st.session_state.target_audience = data.get("target_audience", "")
                st.session_state.cta_text = data.get("cta_text", "")
                st.session_state.product_desc = data.get("product_desc", "")
                st.success("Berhasil diisi! Silakan review di bawah.")
                st.rerun()
            except Exception as e:
                st.error(f"Gagal generate: {e}")

with st.form("input_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        target_audience = st.text_input("Target Audience", key="target_audience", placeholder="Kosongkan jika ingin AI yang menentukan")
    
    with col2:
        cta_text = st.text_input("Teks Tombol / CTA", key="cta_text", placeholder="Kosongkan jika ingin AI yang menentukan")
        
    # Tone of Voice Selector
    tone = st.selectbox(
        "Gaya Bahasa Copywriting",
        ("Profesional & Berwibawa", "Santai & Akrab (Bahasa Gaul)", "Persuasif & Hard Selling", "Emosional & Menyentuh Hati", "Lucu & Humoris", "Curhat & Personal (Deep Talk)"),
        index=5
    )
    
    # --- COMPETITOR URL HISTORY ---
    history_file = "competitor_history.json"
    try:
        with open(history_file, "r") as f:
            url_history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        url_history = []

    # Dropdown for history
    history_options = ["➕ Input URL Baru"] + url_history
    selected_history = st.selectbox("Pilih Link Kompetitor (Riwayat)", history_options)
    
    if selected_history == "➕ Input URL Baru":
        competitor_url = st.text_input("Link Kompetitor Baru (Opsional)", placeholder="Masukkan URL landing page kompetitor...")
    else:
        competitor_url = st.text_input("Link Kompetitor (Opsional - Fitur ATM)", placeholder="Masukkan URL landing page kompetitor untuk ditiru polanya...")
        
    # Conversion Boosters Toggle
    use_boosters = st.checkbox("🔥 Aktifkan Fitur 'Booster Penjualan' (Sticky CTA, Timer, FAQ, Garansi)", value=True)
    
    product_desc = st.text_area("Deskripsi & Manfaat Utama", key="product_desc", height=150, placeholder="Kosongkan jika ingin AI yang mengarang deskripsi berdasarkan Nama Produk...")
    
    # Copy Helper
    with st.expander("📋 Copy Teks (Target, CTA, Deskripsi)"):
        st.caption("Klik ikon 'Copy' di pojok kanan atas setiap blok untuk menyalin.")
        st.text("Target Audience:")
        st.code(st.session_state.target_audience, language=None)
        st.text("CTA:")
        st.code(st.session_state.cta_text, language=None)
        st.text("Deskripsi:")
        st.code(st.session_state.product_desc, language=None)
    
    submitted = st.form_submit_button("✨ Generate Landing Page")

# --- AI LOGIC ---
if submitted:
    if not product_name:
        st.error("Mohon isi Nama Produk!")
    else:
        # Save URL to history if new
        if competitor_url and competitor_url not in url_history:
            url_history.append(competitor_url)
            with open(history_file, "w") as f:
                json.dump(url_history, f)
        if not api_keys:
            st.error("⚠️ API Key belum dimasukkan! Silakan masukkan di Sidebar sebelah kiri atau setting di secrets.toml")
            st.stop()
            
        # Loading State
        with st.spinner("Sedang meracik copywriting & kodingan... (Mungkin butuh 10-20 detik)"):
            try:
                # --- PROMPT ENGINEERING ---
                # Handle optional fields
                desc_prompt = product_desc if product_desc else "TIDAK ADA. Karanglah deskripsi yang sangat menarik, persuasif, dan menjual berdasarkan Nama Produk. Buat seolah-olah ini produk best-seller."
                target_prompt = target_audience if target_audience else "TIDAK ADA. Analisa dan tentukan target audience yang paling relevan dan potensial untuk produk ini."
                cta_prompt = cta_text if cta_text else "TIDAK ADA. Buat CTA yang mendesak dan mengundang klik (misal: Beli Sekarang, Ambil Diskon 50%, dll)."
                
                competitor_data = ""
                if competitor_url:
                    scraped_text = scrape_content(competitor_url)
                    competitor_data = f"""
                    DATA KOMPETITOR (ATM - AMATI TIRU MODIFIKASI):
                    Berikut adalah konten dari landing page kompetitor:
                    ---
                    {scraped_text}
                    ---
                    TUGAS ATM:
                    1. Analisa struktur dan copywriting kompetitor di atas.
                    2. AMBIL poin-poin winning campaign mereka (hook, benefit, offer).
                    3. JANGAN MENJIPLAK PLEK-PLEKAN.
                    4. MODIFIKASI agar versi kita LEBIH MENJUAL, LEBIH PREMIUM, dan LEBIH PERSUASIF.
                    5. Kalahkan kualitas copywriting mereka!
                    """

                booster_instruction = ""
                if use_boosters:
                    booster_instruction = """
                    FITUR BOOSTER PENJUALAN (WAJIB ADA):
                    1. **STICKY CTA (Mobile Only)**: Buat tombol CTA yang melayang di bawah layar (fixed bottom) khusus tampilan mobile. Gunakan class `fixed bottom-0 left-0 w-full p-4 bg-white shadow-lg md:hidden z-50`.
                    2. **URGENCY TIMER**: Tambahkan Countdown Timer sederhana (misal: "Promo berakhir dalam 15:00 menit") di dekat tombol CTA utama. Gunakan JavaScript vanilla sederhana untuk menjalankannya.
                    3. **FAQ SECTION**: Buat section FAQ (Tanya Jawab) yang menjawab 3-5 keraguan utama pembeli (Objection Handling). Gunakan tag <details> dan <summary> untuk accordion.
                    4. **TRUST BADGES**: Tambahkan elemen visual "Garansi 30 Hari Uang Kembali", "Pembayaran Aman", dll di bawah tombol CTA.
                    """

                base_prompt = f"""
                Bertindaklah sebagai Expert Web Developer & UI/UX Designer kelas dunia yang biasa menangani klien "High-Ticket".
                Tugasmu adalah membuat SATU FILE HTML LENGKAP (Single File) untuk Landing Page produk dengan standar desain PREMIUM.
                
                DATA PRODUK:
                - Nama: {product_name}
                - Deskripsi: {desc_prompt}
                - Target: {target_prompt}
                - CTA: {cta_prompt}
                - GAYA BAHASA: {tone} (Wajib ikuti tone ini di seluruh teks!)
                
                {competitor_data}
                
                INSTRUKSI DESAIN (PENTING):
                1. **VIBE**: PROFESIONAL, MENARIK, dan "SOFT". Jangan terlalu polos (boring), tapi jangan norak. Harus terlihat "Eye-Catching" tapi tetap elegan.
                2. **COLOR PALETTE**: Gunakan warna-warna **SOFT PASTEL & GRADIENT**.
                   - Background utama jangan hanya putih polos. Gunakan `bg-slate-50`, `bg-blue-50`, atau gradient halus `bg-gradient-to-br from-indigo-50 to-white`.
                   - Gunakan warna Primary yang lembut tapi tegas (misal: Soft Blue, Sage Green, atau Coral).
                3. **LAYOUT & SECTIONS**:
                   - **Alternating Backgrounds**: Pastikan setiap section punya warna background yang selang-seling (Misal: Hero (Gradient) -> Features (White) -> Testimoni (Soft Grey) -> CTA (Accent Color)).
                   - Gunakan **Card Design** (Kotak putih dengan shadow halus) untuk menonjolkan konten di atas background berwarna.
                4. **TYPOGRAPHY**: Gunakan font modern (Google Fonts). Judul gunakan warna gelap (bukan hitam pekat), Body text gunakan abu-abu tua.
                5. **UI TRENDS**:
                   - **Glassmorphism**: Gunakan efek kaca (`bg-white/80 backdrop-blur-md`) untuk header atau kartu floating.
                   - **Soft Shadows**: Gunakan `shadow-lg` atau `shadow-xl` yang warnanya pudar (colored shadows) agar terlihat modern.
                   - **Rounded Corners**: Gunakan `rounded-2xl` atau `rounded-3xl` untuk kesan friendly & modern.
                6. **TRUST ELEMENTS**: Tambahkan section "Featured In" atau "Trusted By" dengan logo placeholder.
                
                {booster_instruction}
                
                TEKNIS:
                - Gunakan Tailwind CSS via CDN (wajib).
                - Pastikan Mobile Responsive 100%.
                - Jangan gunakan CSS eksternal atau JS eksternal selain Tailwind CDN.
                - Pastikan tag <html>, <head>, dan <body> lengkap.
                """

                if product_type == "Ebook / Produk Digital":
                    scenario_prompt = """
                    SKENARIO: EBOOK / DIGITAL PRODUCT (Storytelling Mode)
                    Struktur Halaman:
                    1. **Headline Provokatif**: Fokus pada pain point/frustasi {target_audience}. Gunakan font besar & bold.
                    2. **Story Section**: 2-3 paragraf pendek. Ceritakan masalah yang relate dengan user. Gunakan bahasa santai ("Lu/Gue" atau "Anda" yang akrab).
                    3. **Solution**: Perkenalkan {product_name} sebagai solusi akhir.
                    4. **What You Get**: List bullet points materi/isi produk.
                    5. **Bonus Section**: Tambahkan 2-3 bonus fiktif yang relevan (misal: Cheatsheet, Video Tutorial) untuk menaikkan value.
                    6. **Pricing & Guarantee**: Tampilkan harga coret (diskon) dan Garansi Uang Kembali 30 Hari.
                    7. **Sticky CTA**: Tombol beli yang sangat menonjol warnanya.
                    """
                else: # Produk Fisik
                    scenario_prompt = """
                    SKENARIO: PRODUK FISIK (Visual & Urgency Mode)
                    Struktur Halaman:
                    1. **Hero Section**: Background bersih, Placeholder gambar produk besar di tengah/kanan. Headline kuat & singkat.
                    2. **Agitation**: Sub-headline yang menekan masalah (misal: "Sering merasa minder karena...?").
                    3. **Product Solution**: Penjelasan singkat cara pakai & solusi praktis.
                    4. **Benefit Grid**: Layout Grid 2x2 atau 4 kolom. Ikon (bisa pakai emoji atau SVG inline) + Poin keunggulan.
                    5. **Social Proof**: Placeholder untuk 3 testimoni user (Foto bulat + Nama + Teks pendek).
                    6. **Scarcity Offer**: "Promo Terbatas", "Beli 2 Gratis 1", atau Countdown Timer (tampilan visual saja). Harga coret besar.
                    7. **Simple Form**: Form statis (hanya tampilan) untuk Nama & WhatsApp sebelum tombol CTA.
                    """

                json_instruction = """
                INSTRUKSI OUTPUT (WAJIB JSON):
                Jangan hanya berikan HTML. Outputkan data dalam format JSON valid sebagai berikut:
                {
                    "copywriting": {
                        "headline": "Headline yang nendang...",
                        "subheadline": "Subheadline yang menjelaskan benefit...",
                        "body_copy": "Paragraf pembuka/storytelling...",
                        "benefits": ["Benefit 1", "Benefit 2", "Benefit 3", ...],
                        "cta": "Teks tombol CTA",
                        "guarantee": "Teks garansi..."
                    },
                    "html_code": "<!DOCTYPE html>..."
                }
                Pastikan "html_code" berisi kode HTML lengkap (Single File) dengan CSS Tailwind yang sudah di-embed.
                """

                final_prompt = base_prompt + "\n" + scenario_prompt + "\n" + json_instruction

                # Generate with Rotation
                response = generate_content_with_rotation(final_prompt, api_keys)
                
                # Parse JSON Response
                text_response = response.text.replace("```json", "").replace("```", "")
                try:
                    data = json.loads(text_response)
                    # Handle if AI returns list
                    if isinstance(data, list): data = data[0]
                    
                    generated_html = data.get("html_code", "")
                    copy_sections = data.get("copywriting", {})
                except json.JSONDecodeError:
                    # Fallback if JSON fails (rare but possible)
                    generated_html = text_response
                    copy_sections = {}
                    st.error("Gagal memisahkan copywriting, tapi HTML mungkin masih aman.")

                # Success message
                st.success("Landing Page Berhasil Dibuat! 🎉")
                
                # Create tabs for preview and code
                tab1, tab2 = st.tabs(["📱 Live Preview", "💻 Source Code"])
                
                # Display HTML
                with tab1:
                    st.caption("Preview (Tampilan mungkin sedikit berbeda tergantung browser)")
                    components.html(generated_html, height=800, scrolling=True)
                
                with tab2:
                    st.code(generated_html, language="html")

                # Download Button
                st.download_button(
                    label="⬇️ Download HTML File",
                    data=generated_html,
                    file_name="landing_page.html",
                    mime="text/html"
                )
                
                # Copywriting Sections
                if copy_sections:
                    st.divider()
                    st.subheader("📝 Draft Copywriting (Siap Copy)")
                    st.info("Jika Anda hanya butuh teksnya saja untuk dipasang di platform lain (WordPress, Elementor, dll).")
                    
                    with st.expander("Lihat Draft Copywriting", expanded=True):
                        st.text("Headline:")
                        st.code(copy_sections.get("headline", ""), language=None)
                        
                        st.text("Subheadline:")
                        st.code(copy_sections.get("subheadline", ""), language=None)
                        
                        st.text("Body Copy / Story:")
                        st.code(copy_sections.get("body_copy", ""), language=None)
                        
                        st.text("Poin-Poin Benefit:")
                        benefits_text = "\n".join([f"- {b}" for b in copy_sections.get("benefits", [])])
                        st.code(benefits_text, language=None)
                        
                        st.text("Call to Action (CTA):")
                        st.code(copy_sections.get("cta", ""), language=None)
                        
                        st.text("Garansi:")
                        st.code(copy_sections.get("guarantee", ""), language=None)

            except Exception as e:
                st.error(f"Gagal generate: {e}")
                st.error("Coba lagi, mungkin AI sedang sibuk atau kuota habis.")

# Fix applied - Force Reload
