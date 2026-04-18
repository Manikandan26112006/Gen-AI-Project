import streamlit as st
import os
import base64
import pandas as pd
from sqlalchemy import text
from backend.data_loader import engine

def _get_avatar_b64():
    """Load the AI avatar image as a base64 string."""
    # Try avatar_ai.png in dashboard dir first, then assets/ai_avatar.png
    base_dir = os.path.dirname(__file__)
    for path in [os.path.join(base_dir, "avatar_ai.png"), os.path.join(base_dir, "assets", "ai_avatar.png")]:
        if os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    return None

def init_db():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS certificates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                faculty_id INTEGER,
                faculty_name TEXT,
                category TEXT,
                content TEXT,
                file_path TEXT,
                ai_analysis TEXT,
                status TEXT DEFAULT 'Pending',
                admin_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()

# Ensure DB table exists
init_db()

def handle_chat(user_query, role, faculty_id=None, faculty_name="Guest", mode="text"):
    from groq import Groq
    # Try multiple ways to get the key + fallback to the user's provided key
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key: return "Groq API Key missing."
    client = Groq(api_key=api_key)
    # Provide data context if possible
    context = ""
    try:
        from backend.data_loader import load_faculty_data
        if role == "Faculty" and faculty_id:
            df = load_faculty_data(faculty_id)
            if not df.empty:
                context = f"Here is {faculty_name}'s data:\n{df.to_string(index=False)}"
    except: pass
    
    if mode == "voice":
        prompt = f"""
        You are Gemini Voice AI. User is {role} ({faculty_name}).
        {context}
        Answer directly and conversationally like a helpful AI voice assistant handling voice input. DO NOT use markdown. Keep it suitable for text-to-speech reading.
        """
    else:
        prompt = f"""
        You are an AI assistant. User is {role} ({faculty_name}).
        {context}
        Produce only the text in a sweet and very short manner. Answer their query directly.
        """
    try:
        chat = client.chat.completions.create(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_query}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.7
        )
        return chat.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

def render_floating_agent(role="Guest", faculty_id=None, faculty_name="Guest"):
    # Inject TTS engine if speech is queued
    if "latest_ai_speech" in st.session_state:
        spoken_text = st.session_state.pop("latest_ai_speech")
        import streamlit.components.v1 as components
        safe_text = spoken_text.replace("`", "").replace("'", "\\'").replace('"', '\\"').replace("\n", " ").replace("\r", "")
        components.html(f"""
        <script>
            setTimeout(() => {{
                try {{
                    const synth = window.parent.speechSynthesis || window.speechSynthesis;
                    if(synth) {{
                        const msg = new SpeechSynthesisUtterance("{safe_text}");
                        msg.lang = 'en-US';
                        synth.speak(msg);
                    }}
                }} catch(e) {{}}
            }}, 200);
        </script>
        """, width=0, height=0)

    if "agent_open" not in st.session_state: 
        st.session_state.agent_open = False

    def toggle_agent():
        st.session_state.agent_open = not st.session_state.agent_open

    avatar_b64 = _get_avatar_b64()
    avatar_src = f"data:image/png;base64,{avatar_b64}" if avatar_b64 else ""

    st.markdown(f"""
    <style>
    @keyframes floatBob {{
        0%   {{ transform: translateY(0px) drop-shadow(0 8px 16px rgba(225,120,50,0.4)); }}
        50%  {{ transform: translateY(-8px) drop-shadow(0 16px 24px rgba(225,120,50,0.2)); }}
        100% {{ transform: translateY(0px) drop-shadow(0 8px 16px rgba(225,120,50,0.4)); }}
    }}

    /* Floating avatar trigger container */
    div[data-testid="stVerticalBlock"]:has(> div.element-container span.floating-btn-anchor) {{
       position: fixed !important; bottom: 25px !important; right: 25px !important;
       z-index: 99999 !important; width: auto !important; height: auto !important;
    }}
    /* Hide the default streamlit button, we overlay our own avatar click area */
    div[data-testid="stVerticalBlock"]:has(> div.element-container span.floating-btn-anchor) button {{
       opacity: 0 !important; position: absolute !important;
       width: 70px !important; height: 70px !important;
       bottom: 0 !important; right: 0 !important;
       cursor: pointer !important; z-index: 2 !important;
       border: none !important; background: transparent !important;
       box-shadow: none !important;
    }}

    /* Floating panel container */
    div[data-testid="stVerticalBlock"]:has(> div.element-container span.floating-agent-anchor) {{
       position: fixed !important; bottom: 105px !important; right: 25px !important;
       width: 400px !important; height: 540px !important; 
       background: #0f172a !important;
       backdrop-filter: blur(25px) !important;
       border-radius: 20px !important; z-index: 100000 !important;
       box-shadow: 0 20px 60px rgba(0,0,0,0.9) !important; 
       border: 2px solid rgba(225,120,50,0.6) !important;
       padding: 0px !important; overflow: hidden !important;
       border-bottom-right-radius: 4px !important;
    }}
    .panel-header {{
       background: linear-gradient(135deg,#b91c1c,#7c2d12); color: white; padding: 12px 20px; 
       font-weight: 800; font-size: 18px;
       border-bottom: 1px solid rgba(255,255,255,0.1);
    }}
    div[data-testid="stVerticalBlock"]:has(> div.element-container span.floating-agent-anchor) input {{
       background: #1f2937 !important; border: 2px solid #e11d48 !important;
       color: #ffffff !important; border-radius: 10px !important;
       min-height: 45px !important; padding: 5px 15px !important;
    }}
    div[data-testid="stChatMessage"] {{
       background: #1e293b !important; border-radius: 12px; 
       border: 1px solid rgba(255,255,255,0.08) !important; margin-bottom: 0.8rem;
    }}
    div[data-testid="stChatMessage"] div[data-testid="stMarkdownContainer"],
    div[data-testid="stChatMessage"] div[data-testid="stMarkdownContainer"] *,
    div[data-testid="stChatMessage"] p, 
    div[data-testid="stChatMessage"] span {{
       color: #ffffff !important;
       -webkit-text-fill-color: #ffffff !important;
       font-weight: 500 !important;
       font-size: 0.95rem !important;
    }}
    div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatar"] img[alt="🤖"]) {{
       background: #311b22 !important; border: 1px solid #7f1d1d !important;
    }}
    div[data-testid="stAudioInput"] {{ margin-bottom: -15px; }}

    /* The visible floating avatar image */
    .ai-float-avatar-wrap {{
        position: fixed;
        bottom: 25px;
        right: 25px;
        z-index: 99998;
        pointer-events: none;   /* clicks go through to the invisible button above */
        display: flex;
        justify-content: center;
        align-items: center;
    }}
    .ai-float-avatar-img {{
        width: 70px;
        height: 70px;
        object-fit: cover;
        border-radius: 50%;
        animation: floatBob 3s ease-in-out infinite;
        border: 2px solid rgba(255,160,80,0.6);
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    }}
    </style>

    <!-- Visible floating avatar (purely decorative / not clickable) -->
    <div class="ai-float-avatar-wrap">
        <img class="ai-float-avatar-img" src="{avatar_src}" alt="AI" />
    </div>
    """, unsafe_allow_html=True)
    
    # Always render the invisible toggle button over the avatar
    with st.container():
        st.markdown('<span class="floating-btn-anchor"></span>', unsafe_allow_html=True)
        st.button("Toggle AI Assistant", key="toggle_ai_fab", on_click=toggle_agent)
        
    if st.session_state.agent_open:
        with st.container():
            st.markdown('<span class="floating-agent-anchor"></span>', unsafe_allow_html=True)
            head_col1, head_col2 = st.columns([5, 1])
            with head_col1:
                st.markdown("<div style='padding:5px 0 0 10px; color:#e11d48; font-weight:800; font-size:18px;'>🤖 AI Assistant</div>", unsafe_allow_html=True)
            with head_col2:
                st.button("✖", key="close_fab_v9", on_click=toggle_agent)
            
            chat_container = st.container(height=340)
            if "antigravity_chat_history" not in st.session_state:
                st.session_state["antigravity_chat_history"] = []
            
            with chat_container:
                for m in st.session_state["antigravity_chat_history"]:
                    with st.chat_message(m["role"]):
                        st.write(m["content"])
            
            # --- INPUT AREA ---
            # Text only (no voice in floating widget per user request)
            st.markdown("<div style='font-size:0.85rem; font-weight:bold; color:#ffffff; padding:0 15px;'>💬 Send Message</div>", unsafe_allow_html=True)
            
            c_txt, c_btn = st.columns([4, 1])
            with c_txt:
                query = st.text_input("Type message...", key="txt_v11", label_visibility="collapsed", placeholder="Type message...")
            with c_btn:
                sent = st.button("🚀", key="btn_sent_v11", use_container_width=True)
            
            final_query = query if sent and query else None
            
            if final_query:
                st.session_state["antigravity_chat_history"].append({"role": "user", "content": final_query})
                with st.spinner("AI is thinking..."):
                    res = handle_chat(final_query, role, faculty_id, faculty_name, mode="text")
                    st.session_state["antigravity_chat_history"].append({"role": "assistant", "content": res})
                    # Removed latest_ai_speech assignment here so TEXT MEANS TEXT.
                st.rerun()

def render_sidebar_voice_button():
    st.sidebar.markdown("<hr style='border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
    st.sidebar.markdown("<h3 style='text-align: center; color: #e2e8f0; font-size: 1.1rem;'>🎙️ Interactive Voice AI</h3>", unsafe_allow_html=True)
    if st.sidebar.button("Enter Voice Mode 🔮", use_container_width=True):
        st.session_state.voice_mode_active = True
        st.rerun()

def render_voice_mode_page(role, faculty_id, faculty_name):
    import streamlit.components.v1 as components
    
    # Hide Streamlit chrome for a clean full-page experience, NO SCROLL
    st.markdown("""
    <style>
    header {visibility: hidden;}
    html, body, .main, [data-testid="stAppViewContainer"], [data-testid="stVerticalBlock"] {
        overflow: hidden !important; max-height: 100vh !important;
    }
    .block-container {padding-top: 2rem !important; max-width: 100% !important; overflow: hidden !important;}
    
    /* Make the voice orb iframe cover the ENTIRE screen */
    iframe {
        position: fixed !important;
        top: 0 !important; left: 0 !important;
        width: 100vw !important; height: 100vh !important;
        min-height: 100vh !important;
        z-index: 99999 !important;
        border: none !important;
        pointer-events: auto !important;
        background: transparent !important;
    }
    /* Hide the tiny TTS iframe */
    iframe[height="0"] {
        width: 0 !important; height: 0 !important; 
        min-height: 0 !important;
        position: absolute !important; 
        pointer-events: none !important;
        z-index: -1 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Use HTML5 TTS globally on Voice page — speak back AI response
    if "latest_ai_speech" in st.session_state:
        spoken_text = st.session_state.pop("latest_ai_speech")
        safe_text = spoken_text.replace("`", "").replace("'", "\\'").replace('"', '\\"').replace("\n", " ").replace("\r", "")
        components.html(f"""
        <script>
            setTimeout(() => {{
                try {{
                    const synth = window.parent.speechSynthesis || window.speechSynthesis;
                    if(synth) {{
                        const msg = new SpeechSynthesisUtterance("{safe_text}");
                        msg.lang = 'en-US';
                        synth.speak(msg);
                    }}
                }} catch(e) {{}}
            }}, 100);
        </script>
        """, width=0, height=0)

    # ── The Custom Voice Orb Component ──
    # This orb is purely visual. When clicked, it triggers the HIDDEN st.audio_input below.
    # It also monitors the hidden button state to pulse red when recording.
    # Included: Controls for Exit and Stop Voice within the same layer.
    components.html("""
    <style>
    * { margin:0; padding:0; box-sizing:border-box; }
    html, body { width:100%; height:100%; overflow:hidden !important; background:transparent; }
    
    @keyframes pulse { 0%,100%{box-shadow: 0 0 40px rgba(239,68,68,0.8);} 50%{box-shadow: 0 0 80px rgba(239,68,68,1);} }
    
    /* ── Controls Area (Top Left) ── */
    #controls {
        position: fixed; top: 20px; left: 20px;
        display: flex; flex-direction: column; gap: 10px;
        z-index: 100001; width: 220px;
    }
    .btn {
        padding: 12px; border: none; border-radius: 10px;
        font-weight: bold; font-family: 'Segoe UI', sans-serif;
        cursor: pointer; text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        transition: all 0.2s;
        text-decoration: none; display: block; width: 100%;
    }
    .btn-exit { background: #1f2937; color: white; border: 1px solid rgba(255,255,255,0.1); }
    .btn-exit:hover { background: #374151; }
    .btn-stop { background: #e11d48; color: white; }
    .btn-stop:hover { background: #be123c; }

    #voiceOrb {
        position: absolute; 
        width: 200px; height: 200px; border-radius: 50%;
        background: radial-gradient(circle at 35% 35%, #0ea5e9, #6366f1, #a855f7);
        border: 5px solid rgba(255,255,255,0.6);
        display: flex; justify-content: center; align-items: center;
        cursor: pointer; user-select: none;
        transition: border-color 0.3s, transform 0.2s;
        box-shadow: 0 10px 50px rgba(99,102,241,0.7), inset 0 0 30px rgba(56,189,248,0.3);
    }
    #voiceOrb:active { transform: scale(0.95); }
    #voiceOrb:hover { filter: brightness(1.15); }
    #voiceOrb.recording {
        border-color: #ef4444 !important;
        animation: pulse 1.2s infinite !important;
    }
    #voiceOrb .icon { font-size: 70px; color: white; pointer-events: none; }
    #status {
        position: fixed; bottom: 25px; left: 50%; transform: translateX(-50%);
        color: #94a3b8; font-family: 'Segoe UI', sans-serif; font-size: 1.05rem;
        text-align: center; z-index: 9999; pointer-events: none;
    }
    </style>

    <div id="controls">
        <button class="btn btn-exit" onclick="exitVoice()">⬅️ Exit to Dashboard</button>
        <button class="btn btn-stop" onclick="stopAI()">⏹️ Stop AI Voice</button>
    </div>

    <div id="voiceOrb" onclick="triggerHiddenMic()">
        <span class="icon" id="orbIcon">🎙️</span>
    </div>
    <div id="status">Click the orb to speak</div>

    <script>
    const orb = document.getElementById('voiceOrb');
    const orbIcon = document.getElementById('orbIcon');
    const statusText = document.getElementById('status');
    const orbSize = 200;
    const pad = 10;
    
    function getW() { try { return window.parent.innerWidth; } catch(e) { return window.innerWidth; } }
    function getH() { try { return window.parent.innerHeight; } catch(e) { return window.innerHeight; } }
    
    let x = (getW() - orbSize) / 2;
    let y = pad;
    let dx = 1.5;
    let dy = 1.5;

    function animate() {
        x += dx; y += dy;
        const maxX = getW() - orbSize - pad;
        const maxY = getH() - orbSize - pad;
        if (x <= pad) { x = pad; dx = Math.abs(dx); }
        if (x >= maxX) { x = maxX; dx = -Math.abs(dx); }
        if (y <= pad) { y = pad; dy = Math.abs(dy); }
        if (y >= maxY) { y = maxY; dy = -Math.abs(dy); }
        orb.style.left = x + 'px';
        orb.style.top  = y + 'px';
        requestAnimationFrame(animate);
    }
    requestAnimationFrame(animate);

    function triggerHiddenMic() {
        try {
            const hiddenButton = window.parent.document.querySelector('div[data-testid="stAudioInput"] button');
            if (hiddenButton) hiddenButton.click();
        } catch(e) {}
    }

    function exitVoice() {
        try {
            // Find the streamlit button for exit and click it
            const buttons = window.parent.document.querySelectorAll('button');
            for (let b of buttons) {
                if (b.innerText === 'HIDDEN_EXIT') {
                    b.click();
                    break;
                }
            }
        } catch(e) {
            window.parent.location.reload(); // fallback
        }
    }

    function stopAI() {
        const synth = window.parent.speechSynthesis || window.speechSynthesis;
        if(synth) synth.cancel();
    }

    // Sync orb state with Streamlit's internal mic state
    setInterval(() => {
        try {
            const hiddenContainer = window.parent.document.querySelector('div[data-testid="stAudioInput"]');
            if (!hiddenContainer) return;
            const isRec = hiddenContainer.innerHTML.includes('stop') || 
                          hiddenContainer.querySelector('button[aria-label*="Stop"]') !== null ||
                          hiddenContainer.querySelector('svg[aria-label*="stop"]') !== null;
            if (isRec) {
                orb.classList.add('recording');
                orbIcon.textContent = '⏹️';
                statusText.textContent = "Listening... Click to stop";
            } else {
                orb.classList.remove('recording');
                orbIcon.textContent = '🎙️';
                statusText.textContent = "Click orb to speak";
            }
        } catch(e) {}
    }, 200);

    // Listen for messages if needed
    window.addEventListener('message', function(e) {
        if(e.data.type === 'stop_voice') stopAI();
    });
    </script>
    """, height=2000)

    # ── Hidden Exit Trigger ──
    if st.button("HIDDEN_EXIT", key="hidden_exit_voice"):
        st.session_state.voice_mode_active = False
        st.rerun()

    # ── Hidden Streamlit Audio Input ──
    # We make it totally invisible and non-obstructive
    st.markdown("""<style>
    /* Hide the technical trigger button */
    button:contains('HIDDEN_EXIT'), .stButton > button:has(div:contains('HIDDEN_EXIT')) {
        display: none !important;
    }
    div[data-testid="stAudioInput"] { 
        position: fixed !important; bottom: 0 !important; right: 0 !important;
        width: 0px !important; height: 0px !important;
        opacity: 0 !important; pointer-events: none !important;
        overflow: hidden !important;
    }
    </style>""", unsafe_allow_html=True)
    
    if "audio_attempt" not in st.session_state:
        st.session_state["audio_attempt"] = 1

    audio_key = f"huge_orb_audio_{st.session_state['audio_attempt']}"
    audio = st.audio_input("🎙️", label_visibility="collapsed", key=audio_key)

    if audio:
        audio_bytes = audio.getvalue()
        
        # --- Actual Speech-to-Text Transcription via Groq Whisper ---
        transcribed_text = ""
        try:
            from groq import Groq
            api_key = os.getenv("GROQ_API_KEY")
            client = Groq(api_key=api_key)
            with st.spinner("AI is understanding your voice..."):
                transcription = client.audio.transcriptions.create(
                    file=("audio.wav", audio_bytes),
                    model="whisper-large-v3-turbo"
                )
                transcribed_text = getattr(transcription, 'text', str(transcription))
        except Exception as e:
            transcribed_text = f"Error: I could not transcribe audio. {e}"

        if not transcribed_text.strip() or "Error" in transcribed_text:
            final_query = "The user spoke, but it couldn't be transcribed clearly."
        else:
            final_query = transcribed_text

        res = handle_chat(final_query, role, faculty_id, faculty_name, mode="voice")
        st.session_state["latest_ai_speech"] = res
        
        # Increment to forcefully discard the current audio_input cache, providing a fresh recorder immediately!
        st.session_state["audio_attempt"] += 1
        st.rerun()




# --- CERTIFICATE / EVIDENCE SYSTEM ---

def analyze_certificate(category, text_content):
    prompt = f"Analyze this '{category}' claim: '{text_content}'. Is it likely real/authentic or fake/suspicious? Determine its intent. Be brief (2-3 sentences max)."
    try:
        from groq import Groq
        api_key = os.getenv("GROQ_API_KEY")
        client = Groq(api_key=api_key)
        chat = client.chat.completions.create(
            messages=[{"role":"user", "content":prompt}], model="llama-3.1-8b-instant"
        )
        ans = chat.choices[0].message.content
        status = "Needs Review" if any(word in ans.lower() for word in ["fake", "suspicious", "doubt", "unlikely"]) else "Likely Real"
        return (status, ans)
    except Exception as e:
        return ("Unknown", "Failed to analyze with AI due to API limits or network issues.")

def upload_certificate_section(fid, fname):
    st.markdown('<div class="section-title">📄 Submit Evidence (NPTEL, Publications, etc)</div>', unsafe_allow_html=True)
    with st.form("cert_upload_form"):
        cat = st.selectbox("Category", ["NPTEL", "Publications", "Workshops", "Consultancy", "Other"])
        txt = st.text_area("Heading or Details of Evidence", placeholder="E.g., NPTEL 12-week course on AI...")
        file = st.file_uploader("Or Upload Image/PDF", type=["png", "jpg", "pdf"])
        if st.form_submit_button("Submit & Analyze via AI"):
            if not txt and not file:
                st.error("Please provide text or a file.")
            else:
                st.info("AI is analyzing your submission...")
                status, analysis = analyze_certificate(cat, txt or "Attached file.")
                
                filepath = ""
                if file:
                    filepath = f"data/uploads/{fid}_{file.name}"
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    with open(filepath, "wb") as f:
                        f.write(file.read())
                
                with engine.connect() as conn:
                    conn.execute(text("""
                        INSERT INTO certificates (faculty_id, faculty_name, category, content, file_path, ai_analysis, status)
                        VALUES (:fid, :fname, :cat, :txt, :path, :ai, 'Pending')
                    """), {"fid":fid, "fname":fname, "cat":cat, "txt":txt, "path":filepath, "ai":analysis})
                    conn.commit()
                st.success("✅ Submitted to Admin for Review!")
                with st.expander("AI Preliminary Analysis"):
                    st.write(analysis)

def render_feedback_status(fid):
    st.markdown("#### 🔄 My Submissions Status")
    df = pd.read_sql(text("SELECT category, content, status, admin_reason, created_at FROM certificates WHERE faculty_id=:fid ORDER BY created_at DESC"), engine, params={"fid":fid})
    if df.empty:
        st.write("No submissions yet.")
    else:
        # Dark-themed status table for maximum visibility
        html = f"""
        <div style="background: #111827; padding: 15px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);">
            <style>
                .status-tbl {{ width: 100%; border-collapse: collapse; color: white !important; font-family: sans-serif; }}
                .status-tbl th {{ background: #1f2937; padding: 10px; text-align: left; border-bottom: 2px solid #e11d48; color: #ffffff !important; }}
                .status-tbl td {{ padding: 10px; border-bottom: 1px solid #374151; color: #d1d5db !important; }}
            </style>
            <table class="status-tbl">
                <thead>
                    <tr><th>Category</th><th>Content</th><th>Status</th><th>Reason</th><th>Date</th></tr>
                </thead>
                <tbody>
                    {''.join([f"<tr><td>{r['category']}</td><td>{r['content']}</td><td>{r['status']}</td><td>{r['admin_reason'] or '-'}</td><td>{r['created_at']}</td></tr>" for idx, r in df.iterrows()])}
                </tbody>
            </table>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)

def admin_review_section():
    st.markdown("### 📋 Certificate Review Console")
    df = pd.read_sql("SELECT * FROM certificates WHERE status='Pending'", engine)
    
    if df.empty:
        st.success("No pending items to review.")
        return
        
    for idx, row in df.iterrows():
        with st.expander(f"{row['faculty_name']} - {row['category']} (ID: {row['id']})", expanded=True):
            st.write(f"**Content Details:** {row['content']}")
            if row['file_path']: st.write(f"📁 Attached: {row['file_path']}")
            st.markdown("🤖 **AI Analysis:**")
            st.info(row['ai_analysis'])
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Approve", key=f"app_{row['id']}"):
                    with engine.connect() as conn:
                        conn.execute(text("UPDATE certificates SET status='Approved', admin_reason='Verified by Admin' WHERE id=:id"), {"id":row['id']})
                        conn.commit()
                    st.success("Approved!")
                    st.rerun()
            with c2:
                with st.form(f"deny_form_{row['id']}"):
                    reason = st.text_input("Reason for Denial")
                    if st.form_submit_button("❌ Deny"):
                        with engine.connect() as conn:
                            conn.execute(text("UPDATE certificates SET status='Denied', admin_reason=:rsn WHERE id=:id"), {"id":row['id'], "rsn":reason})
                            conn.commit()
                        st.warning("Denied.")
                        st.rerun()
