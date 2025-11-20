import streamlit as st
from typing import List, Dict, Any

# ============================================================
#  DUMMY STUBS – replace these with your real implementations
# ============================================================

def run_agent(
    user_input: str,
    region: str,
    location: str,
    mode: str,
    context: str,
) -> Dict[str, Any]:
    """Dummy agent. Replace with your real `run_agent`."""
    return {
        "phrase": f"(Demo) Response for '{user_input}' in {location}, {region}.",
        "gesture": "Smile and maintain relaxed eye contact.",
        "tone": "Friendly and calm",
        "custom": f"Avoid controversial topics when you first meet people in {location}.",
    }


def recall_similar(
    region: str,
    location: str,
    user_input: str,
    mode: str | None,
    context: str | None,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """Dummy recall. Replace with your real `recall_similar`."""
    return []


def store_interaction(
    region: str,
    location: str,
    phrase: str,
    tone: str,
    gesture: str,
    custom: str,
    mode: str,
    context: str,
    answer: str,
):
    """Dummy store. Replace with your real `store_interaction`."""
    pass


def delete_memories_for_region(
    region: str,
    location: str | None,
    mode: str | None,
    context: str | None,
) -> str:
    """Dummy delete. Replace with your real `delete_memories_for_region`."""
    return "Demo: would delete memories here."


def display_memory(m: Dict[str, Any]):
    """Dummy memory display. Replace with your real `display_memory`."""
    st.write("**Q:**", m.get("phrase", ""))
    st.write("**A:**", m.get("answer", ""))
    st.caption(
        f"Tone: {m.get('tone','N/A')} · Gesture: {m.get('gesture','N/A')} · Context: {m.get('context','')}"
    )


# ============================================================
#  DUMMY REGION DATA – later wire this to regions.json
# ============================================================

REGIONS = {
    "International": {
        "USA": ["New York", "San Francisco", "Chicago"],
        "Japan": ["Tokyo", "Osaka"],
        "Germany": ["Berlin", "Munich"],
    },
    "Indian States": {
        "Tamil Nadu": ["Chennai", "Coimbatore"],
        "Maharashtra": ["Mumbai", "Pune"],
        "Karnataka": ["Bengaluru", "Mysuru"],
    },
}

# ============================================================
#  PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="EchoAtlas",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
#  GLOBAL CSS – glassmorphism + layout refinements
# ============================================================

st.markdown(
    """
    <style>
    /* Global background */
    .stApp {
        background: radial-gradient(circle at top, #0f172a 0%, #020617 60%, #000000 100%);
        color: #e5e7eb;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    /* Hide some default chrome */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Center main content & limit width */
    .block-container {
        max-width: 1450px !important;
        margin-left: auto !important;
        margin-right: auto !important;
        padding-top: 1.1rem;
        padding-bottom: 1.3rem;
    }

    /* Slightly tighten vertical spacing */
    .element-container {
        margin-bottom: 0.4rem !important;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: rgba(15,23,42,0.97);
        border-right: 1px solid rgba(148,163,184,0.35);
    }
    .sidebar-title {
        font-size: 1.25rem;
        font-weight: 700;
        padding: 0.25rem 0 0.5rem 0;
    }

    /* Glass card */
    .ea-card {
        background: rgba(15,23,42,0.82);
        border-radius: 18px;
        padding: 18px 22px;
        border: 1px solid rgba(148,163,184,0.45);
        box-shadow: 0 18px 40px rgba(15,23,42,0.9);
        backdrop-filter: blur(14px);
    }
    .ea-card-header {
        font-size: 1.05rem;
        font-weight: 600;
        margin-bottom: 0.3rem;
    }
    .ea-subtitle {
        font-size: 0.9rem;
        color: #9ca3af;
    }

    /* Hero title styles */
    .ea-hero-title {
        font-size: 1.6rem;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .ea-hero-subtitle {
        font-size: 0.95rem;
        color: #cbd5f5;
    }

    /* Primary CTA-style button */
    .ea-primary-btn > button {
        background: linear-gradient(120deg,#2563eb,#1d4ed8);
        color: #f9fafb !important;
        border-radius: 999px !important;
        padding: 0.55rem 1.5rem !important;
        border: none !important;
        font-weight: 600 !important;
        box-shadow: 0 8px 20px rgba(37,99,235,0.55);
        transition: all 0.15s ease-in-out;
    }
    .ea-primary-btn > button:hover {
        background: linear-gradient(120deg,#1d4ed8,#1e40af);
        transform: translateY(-1px);
        box-shadow: 0 12px 26px rgba(37,99,235,0.8);
    }

    /* Tabs (if you add later) */
    button[role="tab"] {
        border-radius: 999px !important;
        padding: 0.25rem 1rem !important;
    }

    /* Expander cards (memories) */
    div.streamlit-expander {
        border-radius: 14px !important;
        border: 1px solid #1f2937 !important;
        margin-bottom: 0.4rem;
        background: rgba(15,23,42,0.9) !important;
    }
    div.streamlit-expanderHeader {
        font-weight: 500 !important;
        color: #e5e7eb !important;
    }
    .ea-mem-meta {
        font-size: 0.75rem;
        color: #9ca3af;
        margin-bottom: 0.35rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
#  SIDEBAR NAVIGATION
# ============================================================

with st.sidebar:
    st.markdown('<div class="sidebar-title">🌍 EchoAtlas</div>', unsafe_allow_html=True)
    st.caption("Cultural tone, gestures & customs — powered by AI.")

    page = st.radio(
        "Navigate",
        ["Ask EchoAtlas", "Conversation Memory", "Cultural Playbook", "Settings"],
        index=0,
    )

    st.markdown("---")
    st.caption("© EchoAtlas · Cultural AI Assistant")


# ============================================================
#  HELPER: region & location selectors (shared)
# ============================================================

def select_region_and_location() -> tuple[str, str, str]:
    """Render selectors in one row and return (group, region, city)."""

    group_col, region_col, city_col = st.columns([1.2, 1.2, 1.2])

    with group_col:
        group = st.selectbox("🌍 Region group", list(REGIONS.keys()), index=0)

    regions = list(REGIONS.get(group, {}).keys())
    with region_col:
        if regions:
            region = st.selectbox("🏳️ Region / Country / State", regions)
        else:
            region = st.text_input("🏳️ Region / Country / State")

    cities = REGIONS.get(group, {}).get(region, []) if region else []
    with city_col:
        if cities:
            city = st.selectbox("📍 City / Area", cities)
        else:
            city = st.text_input("📍 City / Area")

    return group, region or "", city or ""


# ============================================================
#  PAGE: ASK ECHOATLAS
# ============================================================

if page == "Ask EchoAtlas":
    # Hero card
    st.markdown(
        """
        <div class="ea-card" style="margin-bottom: 1.2rem; padding: 22px 30px;">
          <div class="ea-hero-title">✨ Speak with the world, confidently.</div>
          <div class="ea-hero-subtitle">
            Choose a region and city. EchoAtlas will help you communicate with the right tone,
            gestures, and cultural etiquette.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Region selector row
    group, selected_region, location = select_region_and_location()
    st.markdown("<br>", unsafe_allow_html=True)

    # Two-column layout: input (left), response (right)
    left_col, right_col = st.columns([1.05, 1.35])

    # ----- LEFT: input -----
    with left_col:
        st.markdown('<div class="ea-card">', unsafe_allow_html=True)
        st.markdown(
            '<div class="ea-card-header">🎤 Input & Question</div>'
            '<div class="ea-subtitle">Use text or mic to ask your phrase.</div>',
            unsafe_allow_html=True,
        )

        input_mode = st.radio("Input mode", ["Text", "Mic"], horizontal=True)

        user_input = ""
        submit_query = False

        if input_mode == "Text":
            user_input = st.text_area(
                "Type your phrase",
                placeholder="e.g., How do I politely ask for coffee here?",
                height=140,
                key="ea_text_input",
            )
            submit_query = st.button(
                "🚀 Ask EchoAtlas",
                key="ask_text",
                use_container_width=True,
            )
        else:
            st.info("🎙 Mic pipeline placeholder. Integrate your Vosk mic logic here.")
            user_input = st.text_area(
                "Transcript (editable)",
                placeholder="(Your microphone transcript will appear here...)",
                height=140,
                key="ea_mic_input",
            )
            submit_query = st.button(
                "🚀 Ask EchoAtlas",
                key="ask_mic",
                use_container_width=True,
            )

        st.markdown('</div>', unsafe_allow_html=True)

    # ----- RIGHT: response -----
    with right_col:
        st.markdown('<div class="ea-card">', unsafe_allow_html=True)
        st.markdown(
            '<div class="ea-card-header">🤖 EchoAtlas Response</div>',
            unsafe_allow_html=True,
        )

        # Initialize session state if needed
        if "last_main_text" not in st.session_state:
            st.session_state.last_main_text = ""
            st.session_state.last_source = ""
            st.session_state.last_user_input = ""
            st.session_state.last_tone = ""
            st.session_state.last_gesture = ""
            st.session_state.last_custom = ""

        if submit_query and user_input.strip() and selected_region and location:
            # Call your real agent here
            agent_result = run_agent(
                user_input=user_input.strip(),
                region=selected_region,
                location=location,
                mode=input_mode,
                context="casual",
            )

            main_text = agent_result.get("phrase", "").strip()
            tone = agent_result.get("tone", "").strip()
            gesture = agent_result.get("gesture", "").strip()
            custom = agent_result.get("custom", "").strip()

            # Store in memory (replace with your real store)
            store_interaction(
                region=selected_region,
                location=location,
                phrase=user_input.strip(),
                tone=tone,
                gesture=gesture,
                custom=custom,
                mode=input_mode,
                context="casual",
                answer=main_text,
            )

            st.session_state.last_main_text = main_text
            st.session_state.last_source = "Live Agent"
            st.session_state.last_user_input = user_input.strip()
            st.session_state.last_tone = tone
            st.session_state.last_gesture = gesture
            st.session_state.last_custom = custom

        # Read from session
        main_text = st.session_state.get("last_main_text", "")
        source_label = st.session_state.get("last_source", "")
        last_q = st.session_state.get("last_user_input", "")
        tone = st.session_state.get("last_tone", "")
        gesture = st.session_state.get("last_gesture", "")
        custom = st.session_state.get("last_custom", "")

        if last_q and main_text:
            st.markdown("##### 🗨️ You said")
            st.markdown(f"*{last_q}*")

            st.markdown("---")

            st.markdown("##### 🤖 EchoAtlas suggests")
            st.caption(
                f"{selected_region} · {location} · Mode: {input_mode} · {source_label}"
            )
            st.markdown(main_text)

            st.markdown("---")
            st.markdown("##### 🌐 Culture & Communication Tips")
            tips_col1, tips_col2 = st.columns(2)
            with tips_col1:
                st.write("**🙇 Gesture**")
                st.write(gesture or "–")
                st.write("**🎭 Tone**")
                st.write(tone or "–")
            with tips_col2:
                st.write("**📚 Cultural insight**")
                st.write(custom or "–")
        else:
            st.info("Ask a question on the left to see a region-aware response here.")

        st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
#  PAGE: CONVERSATION MEMORY
# ============================================================

elif page == "Conversation Memory":
    st.markdown(
        """
        <div class="ea-card" style="margin-bottom:1.0rem;">
          <div class="ea-card-header">🧠 Conversation Memory</div>
          <div class="ea-subtitle">
            Browse and manage stored interactions across regions and cities.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    group, selected_region, location = select_region_and_location()
    st.markdown("<br>", unsafe_allow_html=True)

    top_col1, top_col2 = st.columns([1.3, 0.7])
    with top_col1:
        st.write(f"**Scope:** {selected_region} → {location or 'All'}")
    with top_col2:
        if st.button("🧹 Clear memories for this city", key="clear_city"):
            msg = delete_memories_for_region(
                region=selected_region,
                location=location,
                mode=None,
                context=None,
            )
            st.success(msg)

    mems = recall_similar(
        region=selected_region,
        location=location,
        user_input="",
        mode=None,
        context=None,
        top_k=50,
    )

    if mems:
        st.write(f"Found **{len(mems)}** memories.")
        for idx, m in enumerate(mems, start=1):
            preview = m.get("phrase", "")
            if len(preview) > 80:
                preview = preview[:77] + "..."
            label = f"💬 Turn {idx}: {preview}"
            with st.expander(label):
                st.markdown(
                    f"<div class='ea-mem-meta'>"
                    f"Region: {m.get('region','')} · Location: {m.get('location','')} · "
                    f"Mode: {m.get('mode','')}</div>",
                    unsafe_allow_html=True,
                )
                display_memory(m)
    else:
        st.info("No memories found for this scope yet.")


# ============================================================
#  PAGE: CULTURAL PLAYBOOK
# ============================================================

elif page == "Cultural Playbook":
    st.markdown(
        """
        <div class="ea-card" style="margin-bottom:1.0rem;">
          <div class="ea-card-header">📒 Cultural Playbook</div>
          <div class="ea-subtitle">
            A place to surface reusable cultural profiles, etiquette snippets,
            and region-specific tips.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("🔧 TODO:")
    st.write("- Connect this to your `regions.json` and dynamic culture profiles.")
    st.write("- Show most-used regions as cards (NYC, Tokyo, Chennai, etc.).")
    st.write("- Each card can show greeting phrases, do/don't list, tone tips.")


# ============================================================
#  PAGE: SETTINGS
# ============================================================

else:
    st.markdown(
        """
        <div class="ea-card" style="margin-bottom:1.0rem;">
          <div class="ea-card-header">⚙️ Settings</div>
          <div class="ea-subtitle">
            Configure EchoAtlas behavior, appearance, and data management.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    theme_choice = st.selectbox(
        "Theme",
        ["Glassmorphism Dark (current)", "Light (future)", "High Contrast (future)"],
    )
    st.checkbox("Enable microphone by default", value=True)
    st.checkbox("Show developer debugging info", value=False)

    st.markdown("#### Memory Controls")
    if st.button("🧨 Factory reset all memories"):
        st.warning("Demo only: in your real app, this would wipe the memory store.")
