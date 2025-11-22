import streamlit as st
import google.generativeai as genai
import streamlit.components.v1 as components
import json
import requests
from bs4 import BeautifulSoup

# --- CONFIGURATION & SETUP ---
st.set_page_config(
    page_title="Landing Page Generator AI",
    page_icon="🚀",
    layout="wide"
)

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

# --- SIDEBAR ---
with st.sidebar:
    st.header("Konfigurasi")
    
    # Try to load existing key
    current_key = ""
    if "GOOGLE_API_KEY" in st.secrets:
        current_key = st.secrets["GOOGLE_API_KEY"]

    api_key_input = st.text_input(
        "Google API Key", 
        type="password",
        value=current_key,
        placeholder="Paste API Key di sini...",
        help="Dapatkan API Key di https://aistudio.google.com/"
    )
    
    if st.button("💾 Simpan API Key"):
        if api_key_input:
            st.success("API Key siap digunakan!")
            st.rerun()
        else:
            st.warning("Isi API Key dulu bos!")
            
    st.divider()

    st.header("Pilih Jenis Produk")
    product_type = st.radio(
        "Kategori:",
        ("Ebook / Produk Digital", "Produk Fisik / Barang")
    )

# --- API KEY SETUP ---
final_api_key = api_key_input
if not final_api_key and "GOOGLE_API_KEY" in st.secrets:
    final_api_key = st.secrets["GOOGLE_API_KEY"]

if final_api_key:
    genai.configure(api_key=final_api_key)

# --- MAIN CONTENT ---
st.title("🚀 Landing Page Generator AI")
st.markdown("Buat landing page profesional dalam hitungan detik menggunakan Google Gemini.")

# --- SESSION STATE INIT ---
if "target_audience" not in st.session_state: st.session_state.target_audience = ""
if "cta_text" not in st.session_state: st.session_state.cta_text = ""
if "product_desc" not in st.session_state: st.session_state.product_desc = ""

# --- INPUT SECTION ---
with st.form("input_form"):
    product_name = st.text_input("Nama Produk (Wajib)", placeholder="Contoh: Ebook Jago Python / Sepatu Anti Air")
    
    col1, col2 = st.columns(2)
    with col1:
        target_audience = st.text_input("Target Audience", key="target_audience", placeholder="Kosongkan jika ingin AI yang menentukan")
    with col2:
        cta_text = st.text_input("Teks Tombol / CTA", key="cta_text", placeholder="Kosongkan jika ingin AI yang menentukan")
        
    tone = st.selectbox(
        "Gaya Bahasa Copywriting",
        ("Profesional & Berwibawa", "Santai & Akrab (Bahasa Gaul)", "Persuasif & Hard Selling", "Emosional & Menyentuh Hati", "Lucu & Humoris"),
        index=2
    )
    
    # Competitor URL
    competitor_url = st.text_input("Link Kompetitor (Opsional - Fitur ATM)", placeholder="Masukkan URL landing page kompetitor untuk ditiru polanya...")
    
    use_boosters = st.checkbox("🔥 Aktifkan Fitur 'Booster Penjualan' (Sticky CTA, Timer, FAQ, Garansi)", value=True)
    
    product_desc = st.text_area("Deskripsi & Manfaat Utama", key="product_desc", height=100, placeholder="Jelaskan sedikit tentang produk Anda...")
    
    submitted = st.form_submit_button("✨ Generate Landing Page")

# --- AI LOGIC ---
if submitted:
    if not product_name:
        st.error("Mohon isi Nama Produk!")
    elif not final_api_key:
        st.error("⚠️ API Key belum dimasukkan! Silakan masukkan di Sidebar sebelah kiri atau setting di secrets.toml")
    else:
        # Loading State
        with st.spinner("Sedang meracik copywriting & kodingan... (Mungkin butuh 10-20 detik)"):
            try:
                # Model Selection
                try:
                    model = genai.GenerativeModel('gemini-2.0-flash')
                    model.generate_content("test")
                except:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Prompt Construction
                desc_prompt = product_desc if product_desc else "TIDAK ADA. Karanglah deskripsi yang sangat menarik."
                target_prompt = target_audience if target_audience else "TIDAK ADA. Tentukan target audience yang paling relevan."
                cta_prompt = cta_text if cta_text else "TIDAK ADA. Buat CTA yang mendesak."
                
                competitor_data = ""
                if competitor_url:
                    scraped_text = scrape_content(competitor_url)
                    competitor_data = f"DATA KOMPETITOR (ATM): {scraped_text[:2000]}"

                booster_instruction = ""
                if use_boosters:
                    booster_instruction = "FITUR BOOSTER: Tambahkan Sticky CTA (Mobile), Countdown Timer, FAQ Section, dan Trust Badges."

                # Specific Scenarios
                if product_type == "Ebook / Produk Digital":
                    scenario_prompt = "FOKUS: EBOOK. Struktur Storytelling: Headline Provokatif -> Cerita Masalah -> Solusi Ebook -> Benefit List -> Bonus -> Harga Coret -> Garansi."
                else:
                    scenario_prompt = "FOKUS: PRODUK FISIK. Struktur Visual: Hero Image Besar -> Masalah -> Solusi Produk -> Benefit Grid -> Testimoni Image -> Scarcity Offer -> Form Order."

                # FINAL PROMPT
                final_prompt = f"""
                Bertindaklah sebagai Expert Web Developer. Buat SATU FILE HTML LENGKAP untuk Landing Page: "{product_name}".
                
                DATA:
                - Deskripsi: {desc_prompt}
                - Target: {target_prompt}
                - CTA: {cta_prompt}
                - Tone: {tone}
                - {competitor_data}
                - {booster_instruction}
                - {scenario_prompt}

                INSTRUKSI TEKNIS:
                1. Gunakan Tailwind CSS via CDN.
                2. Desain harus PREMIUM, MODERN, dan RESPONSIF (Mobile Friendly).
                3. Gunakan warna Soft/Gradient yang profesional.

                OUTPUT WAJIB JSON FORMAT:
                Outputkan HANYA JSON valid dengan struktur:
                {{
                    "copywriting": {{
                        "headline": "...",
                        "subheadline": "...",
                        "body_copy": "...",
                        "benefits": ["...", "..."],
                        "cta": "...",
                        "guarantee": "..."
                    }},
                    "html_code": "<!DOCTYPE html>..."
                }}
                Pastikan "html_code" berisi seluruh kode HTML single file yang siap pakai.
                """

                response = model.generate_content(final_prompt)
                text_response = response.text.replace("```json", "").replace("```", "").strip()
                
                # Parse JSON
                try:
                    data = json.loads(text_response)
                    if isinstance(data, list): data = data[0]
                    
                    generated_html = data.get("html_code", "")
                    copy_sections = data.get("copywriting", {})
                except:
                    # Fallback if JSON fails
                    generated_html = text_response
                    copy_sections = {}

                # Display Result
                st.success("Landing Page Berhasil Dibuat! 🎉")
                
                tab1, tab2 = st.tabs(["📱 Live Preview", "💻 Source Code"])
                
                with tab1:
                    components.html(generated_html, height=800, scrolling=True)
                
                with tab2:
                    st.code(generated_html, language="html")

                st.download_button(
                    label="⬇️ Download HTML File",
                    data=generated_html,
                    file_name="landing_page.html",
                    mime="text/html"
                )
                
                if copy_sections:
                    with st.expander("📝 Lihat Copywriting (Teks Saja)"):
                        st.json(copy_sections)

            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}")
