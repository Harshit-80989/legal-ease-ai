import streamlit as st
# --- THEME TOGGLE & CSS: ---
import streamlit as st

if "theme" not in st.session_state:
    st.session_state["theme"] = "light"
theme = st.session_state["theme"]
toggle = st.toggle("🌗 Dark Mode", value=(theme == "dark"))
st.session_state["theme"] = "dark" if toggle else "light"

# Inject CSS immediately after theme is set
if theme == "dark":
    st.markdown(
        """
        <style>
        body, .stApp { background: #18191a !important; color: #f5f6fa !important; }
        .card { background: #242526 !important; color: #f5f6fa !important; border: 1px solid #333 !important; }
        h1, h2, h3, h4, h5, h6, b, strong, label, .stTextInput label, .stTextArea label, .stFileUploader label, .st-expanderHeader, .stButton>button, .stDownloadButton>button { color: #f5f6fa !important; }
        .stMarkdown table { color: #f5f6fa !important; }
        .stMarkdown a { color: #8ab4f8 !important; }
        .stMarkdown code { background: #333 !important; color: #fff !important; }
        .stAlert-success { background: #223322 !important; color: #b6fcb6 !important; }
        .stAlert-warning { background: #332a00 !important; color: #ffe066 !important; }
        .stTextInput, .stTextArea, .stFileUploader, .stButton>button, .stDownloadButton>button { background: #222 !important; color: #f5f6fa !important; }
        </style>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        """
        <style>
        .card { background: #f8f9fa !important; color: #222 !important; }
        </style>
        """,
        unsafe_allow_html=True
    )
# --- IMPORTS ---

import cohere
import re
from fpdf import FPDF
import time

# --- HEADER ---
st.markdown(
    """
    <style>
    .big-title {font-size:2.6rem; font-weight:700; margin-bottom:0;}
    .subtitle {font-size:1.2rem; color:#666; margin-top:0;}
    .step {background:#e3eafc; border-radius:8px; padding:0.7em 1em; margin-bottom:1em;}
    .footer {color:#888; font-size:0.9em; text-align:center; margin-top:2em;}
    .stTabs [data-baseweb="tab-list"] {justify-content: center;}
    .card {border-radius: 12px; box-shadow: 0 2px 8px #0001; padding: 1.2em 1.5em; margin-bottom: 1.5em;}
    @media (max-width: 600px) {
        .big-title {font-size:1.5rem;}
        .subtitle {font-size:1rem;}
        .card {padding: 0.7em 0.5em;}
    }
    </style>
    <div style='text-align:center'>
        <span class='big-title'>🧑‍⚖️ LegalEase</span>
        <div class='subtitle'>AI-Powered Legal Document Analyzer</div>
        <div style='margin-top:0.5em; color:#444;'>Summarize, extract key clauses, search, and decode legal jargon in seconds.</div>
    </div>
    """,
    unsafe_allow_html=True
)

# --- PROGRESS STEPS ---
st.markdown(
    """
    <div class='step'>
        <b>Step 1:</b> <span style='color:#1a73e8'>Paste</span> or <span style='color:#1a73e8'>upload</span> your legal document.<br>
        <b>Step 2:</b> Click <b>Analyze Document</b>.<br>
        <b>Step 3:</b> Review the <span style='color:#34a853'>Summary</span>, <span style='color:#fbbc05'>Key Clauses</span>, <span style='color:#ea4335'>Jargon Buster</span>, or <span style='color:#1a73e8'>search</span> for any clause.
    </div>
    """,
    unsafe_allow_html=True
)

# --- API KEY MANAGEMENT ---
try:
    COHERE_API_KEY = st.secrets["COHERE_API_KEY"]
except Exception:
    st.error("❌ Cohere API key not found. Please set it in Streamlit secrets as 'COHERE_API_KEY'.")
    st.info("For local development, create a .streamlit/secrets.toml file and add your key.")
    st.stop()

co = cohere.Client(COHERE_API_KEY)

def analyze_document(text):
    prompt = """
You are a legal expert AI assistant. Your task is to analyze the following legal document and present a clear, easy-to-understand breakdown for a non-expert.

Perform these three tasks:

1. **Summary:** Write a concise, bullet-point summary of the document's main purpose and key outcomes in plain, simple English.

2. **Key Clauses:** Identify and extract the most important clauses, focusing specifically on:
   - Liability
   - Termination
   - Confidentiality
   - Payment Terms
   - Governing Law
For each clause, provide a direct quote or a clear summary. If a specific clause is not found in the document, explicitly state "Not found".

3. **Jargon Buster:** Identify complex legal terms or jargon from the document. For each term, provide a simple, one-sentence explanation.

Please format your entire response exactly as follows, using '---' as a separator:

---
**Summary:**
[Your bullet-point summary here]

---
**Key Clauses:**
**Liability:** [Text or "Not found"]
**Termination:** [Text or "Not found"]
**Confidentiality:** [Text or "Not found"]
**Payment Terms:** [Text or "Not found"]
**Governing Law:** [Text or "Not found"]

---
**Jargon Buster:**
**Term1:** [Explanation]
**Term2:** [Explanation]
...
"""
    try:
        response = co.chat(
            message=prompt + "\n\n**DOCUMENT FOR ANALYSIS:**\n" + text,
            model="command-r-plus-08-2024"
        )
        return response.text.strip()
    except Exception as e:
        st.error(f"An error occurred during the Cohere API call: {e}")
        return None

def parse_response(llm_response):
    if not llm_response:
        return {}, {}, []

    sections = {}
    parts = re.split(r'\s*---\s*', llm_response)
    for part in parts:
        if not part.strip():
            continue
        if re.search(r'\*\*Summary:\*\*', part, re.IGNORECASE):
            sections['summary'] = re.sub(r'\*\*Summary:\*\*', '', part, flags=re.IGNORECASE).strip()
        elif re.search(r'\*\*Key Clauses:\*\*', part, re.IGNORECASE):
            sections['key_clauses'] = re.sub(r'\*\*Key Clauses:\*\*', '', part, flags=re.IGNORECASE).strip()
        elif re.search(r'\*\*Jargon Buster:\*\*', part, re.IGNORECASE):
            sections['jargon'] = re.sub(r'\*\*Jargon Buster:\*\*', '', part, flags=re.IGNORECASE).strip()

    summary = sections.get('summary', "_No summary found._")
    
    key_clauses = {}
    if 'key_clauses' in sections:
        clause_text = sections['key_clauses']
        clause_pattern = re.compile(r'\*\*(.*?):\*\*\s*(.*)', re.DOTALL)
        clauses_found = dict(re.findall(clause_pattern, clause_text))
        for k, v in clauses_found.items():
            key_clauses[k.strip()] = v.strip()

    jargon = []
    if 'jargon' in sections:
        jargon_text = sections['jargon']
        jargon_pattern = re.compile(r'\*\*(.*?):\*\*\s*(.*)')
        jargon_pairs = re.findall(jargon_pattern, jargon_text)
        for term, expl in jargon_pairs:
            jargon.append((term.strip(), expl.strip()))

    return summary, key_clauses, jargon

# --- INPUT AREA ---
st.markdown("#### 📄 Input Your Legal Document")
col1, col2 = st.columns([2, 1])

# Use session_state for doc_text so it persists and updates everywhere
if "doc_text" not in st.session_state:
    st.session_state["doc_text"] = ""
    
with col1:
    st.session_state["doc_text"] = st.text_area(
        "Paste your legal document here:",
        value=st.session_state["doc_text"],
        height=220,
        placeholder="Paste the full text of your legal contract, agreement, or policy here..."
    )

with col2:
    uploaded_file = st.file_uploader("Or upload a .txt or .pdf file", type=["txt", "pdf"])
    if uploaded_file:
        if uploaded_file.type == "text/plain":
            st.session_state["doc_text"] = uploaded_file.read().decode("utf-8")
        elif uploaded_file.type == "application/pdf":
            try:
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                st.session_state["doc_text"] = "\n".join(page.extract_text() for page in pdf_reader.pages if page.extract_text())
            except Exception:
                st.warning("Could not read PDF. Please upload a valid text-based PDF.")

# --- SAMPLE DOC ---
with st.expander("🔎 Need a sample? Click to autofill a sample legal agreement."):
    if st.button("Use Sample Document"):
        st.session_state["doc_text"] = """SERVICE AGREEMENT

This Service Agreement is made between Alpha Corp ("Provider") and Beta LLC ("Client").

1. Confidentiality: Both parties agree to keep all information confidential.
2. Payment Terms: Client will pay Provider $5,000 within 30 days of invoice.
3. Liability: Provider is not liable for indirect damages.
4. Termination: Either party may terminate this agreement with 30 days' notice.
5. Governing Law: This agreement is governed by the laws of India.

Signed,
Alpha Corp & Beta LLC
"""
doc_text = st.session_state["doc_text"]
# --- ADVANCED SETTINGS ---
with st.expander("⚙️ Advanced Settings", expanded=False):
    st.markdown(
        "- **Privacy:** Your document is sent securely to Cohere for analysis and is not stored.\n"
        "- **Supported files:** Text-based PDF or TXT files only.\n"
        "- **Best results:** Use clear, well-formatted legal documents."
    )

# --- CLAUSE SEARCH ---
with st.expander("🔍 Search for a Specific Clause or Keyword"):
    search_term = st.text_input("Enter a clause or keyword (e.g., 'arbitration', 'force majeure')", "")
    search_result = ""
    if search_term and 'doc_text' in locals() and doc_text:
        pattern = re.compile(rf".*{re.escape(search_term)}.*", re.IGNORECASE)
        matches = pattern.findall(doc_text)
        if matches:
            st.success(f"Found {len(matches)} occurrence(s):")
            for m in matches:
                st.markdown(f"<div class='card' style='background:#fffbe6'>{m}</div>", unsafe_allow_html=True)
        else:
            st.warning("No matching clause found in the document.")

# --- ANALYZE BUTTON WITH ANIMATED PROGRESS BAR ---
analyze_btn = st.button("🔍 Analyze Document", help="Click to analyze your document with AI")

if analyze_btn and doc_text.strip():
    progress = st.progress(0, text="Starting analysis...")
    for percent in range(1, 80, 10):
        time.sleep(0.04)
        progress.progress(percent, text=f"Analyzing... ({percent}%)")
    with st.spinner("AI is analyzing your document. This may take a moment..."):
        llm_response = analyze_document(doc_text)
        progress.progress(100, text="Analysis complete!")
        if llm_response:
            summary, key_clauses, jargon = parse_response(llm_response)
            # Store results in session_state
            st.session_state['summary'] = summary
            st.session_state['key_clauses'] = key_clauses
            st.session_state['jargon'] = jargon

# --- SHOW RESULTS IF PRESENT IN SESSION_STATE ---
if 'summary' in st.session_state and 'key_clauses' in st.session_state and 'jargon' in st.session_state:
    summary = st.session_state['summary']
    key_clauses = st.session_state['key_clauses']
    jargon = st.session_state['jargon']

    tabs = st.tabs([
        "✅ Summary",
        "🔑 Key Clauses",
        "💡 Jargon Buster"
    ])

    with tabs[0]:
        st.markdown("<div class='card'><h3>📋 Document Summary</h3>" + summary + "</div>", unsafe_allow_html=True)

    with tabs[1]:
        st.markdown("<div class='card'><h3>📑 Key Clauses</h3>", unsafe_allow_html=True)
        clause_order = ["Liability", "Termination", "Confidentiality", "Payment Terms", "Governing Law"]
        for clause_name in clause_order:
            text = key_clauses.get(clause_name, "_Not explicitly found in the document._")
            st.markdown(f"<b>{clause_name}:</b> <br><div style='margin-bottom:1em'>{text}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[2]:
        st.markdown("<div class='card'><h3>📚 Jargon Buster</h3>", unsafe_allow_html=True)
        if jargon:
            md_table = "| Term | Explanation |\n|---|---|\n"
            for term, expl in jargon:
                md_table += f"| **{term}** | {expl} |\n"
            st.markdown(md_table)
        else:
            st.markdown("_No complex legal jargon was identified._")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- EXPORT AS PDF ---
    def safe_multicell(pdf, w, h, text):
    # Remove problematic characters and split long words
     text = re.sub(r'[\r\n\t]', ' ', text)
     max_word_len = 40
     words = text.split()
     safe_words = []
     for word in words:
        # Split very long words
        if len(word) > max_word_len:
            word = ' '.join([word[i:i+max_word_len] for i in range(0, len(word), max_word_len)])
        safe_words.append(word)
     safe_text = ' '.join(safe_words)
     # Use a fixed width (190) for A4 minus margins
     pdf.multi_cell(190, h, safe_text)

    def export_pdf(summary, key_clauses, jargon):
     pdf = FPDF()
     pdf.add_page()
     pdf.set_font("Arial", "B", 16)
     pdf.cell(0, 10, "LegalEase AI Legal Document Analysis", ln=1, align="C")
     pdf.set_font("Arial", "", 12)
     pdf.ln(5)
     safe_multicell(pdf, 190, 10, "Summary:\n" + summary)
     pdf.ln(3)
     pdf.set_font("Arial", "B", 13)
     pdf.cell(0, 10, "Key Clauses:", ln=1)
     pdf.set_font("Arial", "", 12)
     for k, v in key_clauses.items():
        safe_multicell(pdf, 190, 8, f"{k}: {v}")
     pdf.ln(3)
     pdf.set_font("Arial", "B", 13)
     pdf.cell(0, 10, "Jargon Buster:", ln=1)
     pdf.set_font("Arial", "", 12)
     for t, e in jargon:
        safe_multicell(pdf, 190, 8, f"{t}: {e}")
     return pdf.output(dest="S")  # <-- No .encode("latin1")


    st.markdown("---")
    result_text = f"Summary:\n{summary}\n\nKey Clauses:\n" + \
        "\n".join([f"{k}: {v}" for k, v in key_clauses.items()]) + \
        "\n\nJargon Buster:\n" + "\n".join([f"{t}: {e}" for t, e in jargon])
    st.download_button("⬇️ Download Analysis (TXT)", result_text, file_name="legal_analysis.txt")
    pdf_bytes = export_pdf(summary, key_clauses, jargon)
    st.download_button("⬇️ Export as PDF", bytes(pdf_bytes), file_name="legal_analysis.pdf", mime="application/pdf")
else:
    st.info("Paste, upload, or use a sample legal document above, then click 'Analyze Document'.")

# --- FOOTER ---
st.markdown(
    """
    <div class='footer'>
        Made with ❤️ using <a href='https://cohere.com/' target='_blank'>Cohere</a> & <a href='https://streamlit.io/' target='_blank'>Streamlit</a>.<br>
        <a href='https://github.com/' target='_blank'>Need help?</a>
    </div>
    """,
    unsafe_allow_html=True
)
