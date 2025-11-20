import os
import json
import queue
import time
import random
from pathlib import Path

import sounddevice as sd
from vosk import Model, KaldiRecognizer

import streamlit as st
from openai import OpenAI   # 👈 add this

client = OpenAI()           # 👈 and this


import sounddevice as sd
from vosk import Model, KaldiRecognizer

import streamlit as st
import openai

from agents.memory_agent import (
    setup_memory_schema,
    store_interaction,
    recall_similar,
    display_memory,
    delete_memories_for_region,
    list_all_regions,
)
from langchain_runner import run_agent

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

# -----------------------
# OpenAI setup (for dynamic culture profile)
# -----------------------
openai.api_key = os.getenv("OPENAI_API_KEY", "")


def pick_variant(field, context=None, default=None):
    """
    Handles both single values and lists of variants.
    - If field is a list, pick one (optionally filter by context).
    - If field is a dict with 'text' + 'context', pick matching context.
    - If field is a string, just return it.
    """
    if isinstance(field, list):
        # If list contains dicts with context tags
        if context:
            candidates = [
                f
                for f in field
                if isinstance(f, dict) and f.get("context") == context
            ]
            if candidates:
                return random.choice(candidates).get("text")
        # Otherwise just pick randomly
        choice = random.choice(field)
        return choice["text"] if isinstance(choice, dict) else choice
    return field or default


# Simple in-memory cache for dynamic culture profiles
if "dynamic_culture_cache" not in st.session_state:
    st.session_state.dynamic_culture_cache = {}


def generate_dynamic_culture_profile(region: str, location: str) -> dict:
    """
    Use LLM to dynamically generate a culture profile for (region, location).

    Returns a dict with keys: phrase, gesture, tone, custom.
    """
    cache_key = f"{region.strip()}|{location.strip()}"
    cache = st.session_state.dynamic_culture_cache

    # 1) Check cache first
    if cache_key in cache:
        return cache[cache_key]

    try:
        prompt = f"""
You are a cultural communication expert.

For the following place:
- Country or State/Region: {region}
- City/Area: {location}

Generate a short, practical profile for how a visitor should speak and behave.
Return ONLY valid JSON with these keys:
- "phrase": a short example phrase for politely asking for something (in English or local language).
- "gesture": a one-sentence description of an appropriate gesture/body language.
- "tone": 2–5 words describing the recommended tone of voice.
- "custom": 1–2 sentences of a key cultural tip for everyday interactions.

Example output:
{{
  "phrase": "Can I get a coffee, please?",
  "gesture": "Smile and make brief eye contact.",
  "tone": "Friendly and polite",
  "custom": "Start with a short greeting before making your request."
}}
        """.strip()

        # ✅ modern OpenAI client (SDK >= 1.0)
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # adjust if you use a different model
            messages=[
                {"role": "system", "content": "You return only concise JSON objects."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
        )

        content = response.choices[0].message.content.strip()

        # Sometimes models wrap JSON in ```json ... ``` fences – strip them
        if content.startswith("```"):
            content = content.strip("`")
            # drop leading "json\n" if present
            if content.lower().startswith("json"):
                content = content.split("\n", 1)[1]

        profile = json.loads(content)

        result = {
            "phrase": profile.get("phrase", "").strip(),
            "gesture": profile.get("gesture", "").strip(),
            "tone": profile.get("tone", "").strip(),
            "custom": profile.get("custom", "").strip(),
        }

    except Exception as e:
        # Fallback minimal profile if LLM fails
        result = {
            "phrase": f"Hello, could you please help me here in {location}?",
            "gesture": "Smile gently and be respectful.",
            "tone": "Polite and friendly",
            "custom": f"Be respectful and watch how locals behave in {location}.",
        }
        st.warning(f"LLM culture profile generation failed: {e}")

    # 3) Cache and return
    cache[cache_key] = result
    return result


# -----------------------
# UI Setup
# -----------------------
st.set_page_config(page_title="EchoAtlas", page_icon="🌍", layout="centered")

# Global styling
st.markdown(
    """
    <style>
    /* Primary buttons */
    div.stButton > button:first-child {
        background-color: #1E90FF;
        color: white;
        border-radius: 6px;
        border: none;
        padding: 0.6em 1.2em;
        font-weight: 600;
        box-shadow: 2px 4px 6px rgba(0,0,0,0.3);
        transition: background-color 0.2s ease, box-shadow 0.2s ease, transform 0.05s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #0d6efd;
        box-shadow: 3px 6px 10px rgba(0,0,0,0.4);
    }
    div.stButton > button:first-child:active {
        transform: translateY(1px);
        box-shadow: 1px 2px 4px rgba(0,0,0,0.25);
    }

    /* Transcript panel */
    .ea-transcript-box {
        background: #020617;
        border-radius: 10px;
        padding: 12px 14px;
        border: 1px solid #1e293b;
        font-size: 0.95rem;
        min-height: 56px;
        color: #e5e7eb;
        box-shadow: 0 4px 12px rgba(15,23,42,0.6);
    }
    .ea-transcript-empty {
        color: #64748b;
        font-style: italic;
    }

    /* Status pill */
    .ea-status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    .ea-status-running {
        background: #064e3b;
        color: #bbf7d0;
        border: 1px solid #22c55e;
    }
    .ea-status-stopped {
        background: #450a0a;
        color: #fecaca;
        border: 1px solid #ef4444;
    }
    .ea-dot {
        width: 8px;
        height: 8px;
        border-radius: 999px;
    }
    .ea-dot-running { background: #22c55e; }
    .ea-dot-stopped { background: #ef4444; }

    /* Simple "waveform" animation when listening */
    @keyframes eaPulse {
        0%   { transform: scaleY(0.6); }
        50%  { transform: scaleY(1.2); }
        100% { transform: scaleY(0.6); }
    }
    .ea-wave span {
        display: inline-block;
        width: 4px;
        margin: 0 1px;
        border-radius: 999px;
        background: #22c55e;
        animation: eaPulse 1s ease-in-out infinite;
    }
    .ea-wave span:nth-child(2) { animation-delay: 0.1s; }
    .ea-wave span:nth-child(3) { animation-delay: 0.2s; }
    .ea-wave span:nth-child(4) { animation-delay: 0.3s; }
    .ea-wave span:nth-child(5) { animation-delay: 0.4s; }

    /* EchoAtlas response panel */
    .ea-response-panel {
        background: #020617;
        border-radius: 14px;
        padding: 20px 22px 24px;
        border: 1px solid #1e293b;
        box-shadow: 0 8px 24px rgba(15,23,42,0.8);
        margin-top: 0.8rem;
    }
    .ea-response-panel h3 {
        margin-top: 1rem;
        margin-bottom: 0.4rem;
        font-size: 1.05rem;
        color: #93c5fd; /* soft blue for section titles */
    }
    .ea-response-meta {
        font-size: 0.8rem;
        color: #9ca3af;
        margin-bottom: 0.5rem;
    }
    .ea-response-main {
        font-size: 1rem;
        line-height: 1.5;
        color: #e5e7eb;
        margin-bottom: 0.75rem;
    }
    .ea-response-panel hr {
        border: none;
        border-top: 1px solid #1f2937;
        margin: 0.5rem 0 0.8rem 0;
    }

    .ea-tip-label {
        display: inline-block;
        font-weight: 600;
        color: #facc15; /* yellow accent for tip labels */
        margin-right: 4px;
    }
    .ea-tip-text {
        color: #d1d5db;
        font-size: 0.95rem;
        margin-bottom: 0.6rem;
        line-height: 1.4;
        padding-left: 10px;
        border-left: 2px solid #334155;
    }

    /* Two-column layout for tips (responsive) */
    .ea-tip-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-top: 0.6rem;
    }
    .ea-tip-col {
        flex: 1 1 220px;   /* two columns on wide screens, one on narrow */
        min-width: 0;
    }
    .ea-tip-full {
        flex-basis: 100%;
    }

    /* -- Modern primary button -- */
    .ea-primary-btn > button {
        background: linear-gradient(90deg,#2563eb,#1d4ed8);
        color: white !important;
        border-radius: 999px !important;
        padding: 0.5rem 1.4rem !important;
        border: none !important;
        font-weight: 600 !important;
        box-shadow: 0 6px 16px rgba(37,99,235,0.45);
        transition: all 0.15s ease-in-out;
    }
    .ea-primary-btn > button:hover {
        background: linear-gradient(90deg,#1d4ed8,#1e40af);
        transform: translateY(-1px);
        box-shadow: 0 8px 20px rgba(37,99,235,0.6);
    }

    /* Hero header card */
    .ea-hero {
        background: radial-gradient(circle at top left,#1d4ed8 0%,#020617 50%);
        border-radius: 18px;
        padding: 14px 18px;
        border: 1px solid #1e293b;
        box-shadow: 0 12px 30px rgba(15,23,42,0.8);
        margin-bottom: 0.75rem;
    }
    .ea-hero-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #e5e7eb;
        margin-bottom: 4px;
    }
    .ea-hero-sub {
        font-size: 0.85rem;
        color: #cbd5f5;
    }

    /* Memory cards (Streamlit expanders) */
    div.streamlit-expander {
        border-radius: 14px !important;
        border: 1px solid #1f2937 !important;
        margin-bottom: 0.4rem;
        background: #020617 !important;
        animation: eaMemFade 0.22s ease-out;
    }
    div.streamlit-expanderHeader {
        font-weight: 500 !important;
        color: #e5e7eb !important;
    }
    div.streamlit-expanderHeader:hover {
        background: radial-gradient(circle at top left,#1d4ed8 0%,#020617 60%) !important;
        border-color: #38bdf8 !important;
    }
    .ea-mem-meta {
        font-size: 0.75rem;
        color: #9ca3af;
        margin-bottom: 0.35rem;
    }
    @keyframes eaMemFade {
        from { opacity: 0; transform: translateY(4px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

BANNER_PATH = "banner.png"
if Path(BANNER_PATH).exists():
    st.image(BANNER_PATH, use_container_width=True)

st.title("🌍 EchoAtlas")
st.caption("Real-time cultural translator with live microphone transcription")

setup_memory_schema()

# -----------------------
# Mode toggle + reset
# -----------------------
mode = st.radio("Choose mode", ["🌐 International", "🇮🇳 Indian States"])

# Track last mode in session state
if "last_mode" not in st.session_state:
    st.session_state.last_mode = mode

if st.session_state.last_mode != mode:
    # Mode switched: reset relevant state
    st.session_state.typed_phrase = ""
    st.session_state.transcript = ""
    st.session_state.recording = False
    if "selected_region" in st.session_state:
        del st.session_state["selected_region"]

    st.markdown(
        """
        <style>
        .fade-in {
            animation: fadeIn 1.5s ease-in-out;
        }
        @keyframes fadeIn {
            from {opacity: 0;}
            to {opacity: 1;}
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"<div class='fade-in'><p style='color:#b58900; font-weight:bold;'>🔄 Mode switched to "
        f"<b>{mode}</b>. Input and region selection have been reset.</p></div>",
        unsafe_allow_html=True,
    )

    st.session_state.last_mode = mode

# -----------------------
# Load region options (2-level: region → locations)
# -----------------------
with open("regions.json", "r", encoding="utf-8") as f:
    region_options = json.load(f)

regions_for_mode = (
    region_options["International"]
    if mode == "🌐 International"
    else region_options["Indian States"]
)

# 1) First dropdown: country or Indian state
display_options = [
    f"{info.get('emoji', '')} {region}" for region, info in regions_for_mode.items()
]
selected_display = st.selectbox("🌍 Choose a country / state", display_options)

selected_region = selected_display.split(" ", 1)[1]
region_data = regions_for_mode[selected_region]

# 2) Second dropdown: city / sub-region within that country/state
locations_dict = region_data.get("locations", {})
if not locations_dict:
    st.error(f"No locations configured for {selected_region} in regions.json")
    st.stop()

location_names = list(locations_dict.keys())
location_choices = location_names + ["🆕 Other (not listed)"]

selected_location_name = st.selectbox(
    f"📍 Choose a city / region in {selected_region}",
    location_choices,
    key="location_choice",
)

if selected_location_name == "🆕 Other (not listed)":
    location = st.text_input(
        f"Enter a custom city / region in {selected_region}",
        key="custom_location",
    ).strip()

    if not location:
        st.warning("Please type a city or region name to continue.")
        st.stop()

    st.info(
        f"✨ Generating a dynamic culture profile for **{location}** in **{selected_region}**..."
    )

    dynamic_profile = generate_dynamic_culture_profile(selected_region, location)

    location_profile = {
        "phrase": dynamic_profile.get("phrase", ""),
        "gesture": dynamic_profile.get("gesture", ""),
        "tone": dynamic_profile.get("tone", ""),
        "custom": dynamic_profile.get("custom", ""),
    }
else:
    location = selected_location_name
    location_profile = locations_dict[location]

st.markdown(
    f"📍 Location: **{location}** {region_data.get('emoji', '')}"
)

# -----------------------
# Dynamic variant selection (defaults) - city-specific
# -----------------------
phrase = pick_variant(location_profile.get("phrases", location_profile.get("phrase")))
gesture = pick_variant(location_profile.get("gestures", location_profile.get("gesture")))
tone = pick_variant(location_profile.get("tones", location_profile.get("tone")))
custom = pick_variant(location_profile.get("customs", location_profile.get("custom")))

# Display default region tips
st.success(f"✅ Default Phrase Suggestion: {phrase}")
st.info(f"{region_data.get('emoji','')} Gesture Tip: {gesture}")
st.warning(f"📚 Cultural Insight: {custom}")
st.info(f"🎭 Tone Tip: {tone}")

# -----------------------
# Mic setup (Vosk)
# -----------------------
MODEL_PATH = "models/vosk-model-small-en-us-0.15"
model = Model(MODEL_PATH)
rec = KaldiRecognizer(model, 16000)
q = queue.Queue()


def audio_callback(indata, frames, time_, status):
    if status:
        print(status)
    q.put(bytes(indata))


if "transcript" not in st.session_state:
    st.session_state.transcript = ""
if "recording" not in st.session_state:
    st.session_state.recording = False
if "run_from_mic" not in st.session_state:
    st.session_state.run_from_mic = False

# -----------------------
# Input section
# -----------------------
st.subheader("🎤 Speak or Type Your Phrase")
input_mode = st.radio("Select input mode", ["Mic", "Text"])

# Initialize submit_query so it's always defined
submit_query = False
user_input = ""

if input_mode == "Mic":
    # ----- MIC MODE -----
    st.markdown("### 🎧 Live Microphone Capture")

    mic_col1, mic_col2, mic_col3 = st.columns(3)

    with mic_col1:
        if st.button("🎙 Start listening", key="mic_start"):
            st.session_state.recording = True
            st.session_state.transcript = ""
            st.session_state.run_from_mic = False

    with mic_col2:
        if st.button("⏹ Stop listening", key="mic_stop"):
            st.session_state.recording = False
            if st.session_state.transcript.strip():
                st.session_state.run_from_mic = True
                st.rerun()

    with mic_col3:
        if st.button("🧹 Clear transcript", key="mic_clear"):
            st.session_state.transcript = ""
            st.rerun()

    # Status pill
    if st.session_state.recording:
        st.markdown(
            "<div class='ea-status-pill ea-status-running'>"
            "<span class='ea-dot ea-dot-running'></span>"
            "Listening..."
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div class='ea-status-pill ea-status-stopped'>"
            "<span class='ea-dot ea-dot-stopped'></span>"
            "Mic stopped"
            "</div>",
            unsafe_allow_html=True,
        )

    placeholder = st.empty()

    # Capture audio when recording
    if st.session_state.recording:
        with sd.RawInputStream(
            samplerate=16000,
            blocksize=8000,
            dtype="int16",
            channels=1,
            callback=audio_callback,
        ):
            st.info("🎙️ Speak now... press **Stop listening** when you're done.")
            while st.session_state.recording:
                if not q.empty():
                    data = q.get()
                    if rec.AcceptWaveform(data):
                        result = json.loads(rec.Result())
                        text = result.get("text", "")
                        if text:
                            st.session_state.transcript += " " + text
                    else:
                        partial = json.loads(rec.PartialResult())
                        if partial.get("partial"):
                            placeholder.write(
                                "🗣️ Transcript: "
                                + st.session_state.transcript
                                + " "
                                + partial["partial"]
                            )
                            continue
                placeholder.write("🗣️ Transcript: " + st.session_state.transcript)
                time.sleep(0.1)
    else:
        # 🔑 When not recording, remove the streaming placeholder box
        placeholder.empty()

    # ✅ Captured Transcript ONLY in Mic mode
    st.markdown("#### 📝 Captured Transcript")
    transcript = st.session_state.get("transcript", "").strip()

    if transcript:
        st.markdown(
            "<div class='ea-transcript-box'>"
            f"{transcript}"
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div class='ea-transcript-box ea-transcript-empty'>"
            "No transcript yet. Press <b>Start listening</b> and speak."
            "</div>",
            unsafe_allow_html=True,
        )

    # Little wave animation while listening
    if st.session_state.recording:
        st.markdown(
            "<div style='margin-top:6px;'>"
            "<span class='ea-wave'>"
            "<span></span><span></span><span></span><span></span><span></span>"
            "</span> <span style='margin-left:6px; color:#e5e7eb;'>Listening...</span>"
            "</div>",
            unsafe_allow_html=True,
        )

    # After Stop, auto-send transcript as query
    if st.session_state.run_from_mic and transcript:
        user_input = transcript
        submit_query = True
        st.session_state.run_from_mic = False

else:
    # ----- TEXT MODE -----
    typed_input = st.text_area(
        "Type your phrase here",
        placeholder="e.g., Can I get a bowl of ramen?",
        key="typed_phrase",
    )
    user_input = typed_input.strip()
    submit_query = st.button("🚀 Ask EchoAtlas")



# =====================================================
# MODERN CENTER LAYOUT: hero + tabs + cards
# =====================================================

# --- Hero header (region/location strip) ---
st.markdown(
    f"""
    <div class="ea-hero">
      <div class="ea-hero-title">
        🌍 EchoAtlas · <span style="opacity:0.9;">{selected_region}</span>
      </div>
      <div class="ea-hero-sub">
        📍 <b>{location}</b> · Mode: <b>{input_mode}</b><br/>
        Ask anything and we’ll respond with region-aware language, gestures, tone, and culture tips.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =====================================================
# 1) Handle submission + store "last_results" in session
# =====================================================
if "last_results" not in st.session_state:
    st.session_state.last_results = []

if submit_query and user_input:
    agent_result = run_agent(
        user_input=user_input,
        region=selected_region,
        location=location,
        mode=input_mode,
        context="casual",
    )

    llm_phrase = agent_result.get("phrase", "")

    # Store this Q&A into memory
    store_interaction(
        region=selected_region,
        location=location,
        phrase=user_input,
        tone=tone,
        gesture=gesture,
        custom=custom,
        mode=input_mode,
        context="casual",
        answer=llm_phrase,
    )

    # Get similar memories JUST for this question
    results = recall_similar(
        region=selected_region,
        location=location,
        user_input=user_input,
        mode=input_mode,
        context="casual",
    )

    # Cache in session to show under "Related Memories" tab
    st.session_state.last_results = results

    # Decide what to show as the main answer text
    if llm_phrase:
        main_text = llm_phrase
        source_label = "Live Agent"
    elif results:
        mem0 = results[0]
        main_text = mem0.get("answer") or mem0.get("phrase", "")
        source_label = "From Conversation Memory"
    else:
        main_text = phrase  # default from regions.json / dynamic profile
        source_label = "Default Region Suggestion"

    st.session_state.last_main_text = main_text
    st.session_state.last_source_label = source_label
    st.session_state.last_user_input = user_input
else:
    # No new submission this run: use last stored values
    main_text = st.session_state.get("last_main_text", "")
    source_label = st.session_state.get("last_source_label", "")
    user_input = st.session_state.get("last_user_input", "")


# =====================================================
# 2) Tabs: Ask/Response · Related Memories · All Memories
# =====================================================
tab_ask, tab_related, tab_all = st.tabs(
    ["💬 Ask & Response", "🧠 Related Memories", "📚 All Memories for this City"]
)

# ----------------------
# TAB 1: Ask & Response
# ----------------------
with tab_ask:
    if user_input and main_text:
        st.markdown('<div class="ea-response-panel">', unsafe_allow_html=True)

        st.markdown("### 🗨️ You said")
        st.markdown(f"*{user_input}*")

        st.markdown("---")

        st.markdown("### 🤖 EchoAtlas Suggests")
        meta_html = (
            f'<span class="ea-response-meta">'
            f"🌍 <b>{selected_region}</b> · 📍 {location} · 🎛️ {input_mode} · {source_label}"
            f"</span>"
        )
        st.markdown(meta_html, unsafe_allow_html=True)

        st.markdown(f"<div class='ea-response-main'>{main_text}</div>", unsafe_allow_html=True)

        st.markdown("### 🌐 Culture & Communication Tips", unsafe_allow_html=True)

        tip_html = f"""
        <div class="ea-tip-grid">
          <div class="ea-tip-col">
            <p class="ea-tip-text">
              <span class="ea-tip-label">🙇 Gesture Tip for {selected_region}:</span>
              {gesture}
            </p>
          </div>
          <div class="ea-tip-col">
            <p class="ea-tip-text">
              <span class="ea-tip-label">🎭 Tone Coaching:</span>
              {tone}
            </p>
          </div>
          <div class="ea-tip-full">
            <p class="ea-tip-text">
              <span class="ea-tip-label">📚 Cultural Insight in {location}:</span>
              {custom}
            </p>
          </div>
        </div>
        """
        st.markdown(tip_html, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
    else:
        # Empty state
        st.info(
            "Type or speak a phrase on the left, then click **Ask EchoAtlas** "
            "to see a region-aware answer here."
        )

# ----------------------
# TAB 2: Related Memories
# ----------------------
with tab_related:
    st.markdown("### 🧠 Related Memories")

    # Last question the user asked (if any)
    last_q = st.session_state.get("last_user_input", "").strip()

    # Check if we have ANY memories for this city at all
    city_mems = recall_similar(
        region=selected_region,
        location=location,
        user_input="",      # empty → fetch all for scope
        mode=None,
        context=None,
        top_k=10,
    )

    if not last_q:
        # No question asked yet this session for this city
        if city_mems:
            # There is history, but nothing "related" yet
            st.markdown(
                """
                <div class="ea-banner">
                    <div class="ea-banner-title">🧭 No Recent Question</div>
                    <div class="ea-banner-desc">
                        This city already has conversation history, but you haven’t asked a question in this session.<br>
                        Ask EchoAtlas a new question to see related memories, or browse the full history in the <b>All Memories</b> tab.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            # No history at all
            st.markdown(
                """
                <div class="ea-banner">
                    <div class="ea-banner-title">🕊 No Conversation History Yet</div>
                    <div class="ea-banner-desc">
                        This city doesn’t have any stored memories yet.<br>
                        Ask EchoAtlas a question to start building a cultural understanding trail here.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        # We have a last question – show memories related to that question
        rel = recall_similar(
            region=selected_region,
            location=location,
            user_input=last_q,
            mode=input_mode,
            context="casual",
            top_k=5,
        )

        if not rel:
            st.markdown(
                """
                <div class="ea-banner">
                    <div class="ea-banner-title">📭 No Related Memories Found</div>
                    <div class="ea-banner-desc">
                        We couldn’t find any stored conversations similar to your last question for this city.<br>
                        Keep asking, and EchoAtlas will start building a richer memory trail to draw from.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"📊 Showing up to <b>{len(rel)}</b> memories similar to your latest question.",
                unsafe_allow_html=True,
            )

            for idx, r in enumerate(rel, start=1):
                preview = r.get("phrase", "")
                if len(preview) > 80:
                    preview = preview[:77] + "..."

                ts = r.get("timestamp", "")
                ts_label = ts[:19].replace("T", " ") if ts else "no timestamp"

                label = f"💬 Memory {idx}: {preview}"
                with st.expander(label):
                    st.markdown(
                        f"<div class='ea-mem-meta'>🕒 {ts_label}</div>",
                        unsafe_allow_html=True,
                    )
                    display_memory(r)


            # else:
                    # st.info("No related memories yet. Ask something to start building a trail!")

# ----------------------
# TAB 3: All Memories for this City
# ----------------------
with tab_all:
    all_mems = recall_similar(
        region=selected_region,
        location=location,
        user_input="",      # empty → get all for this scope
        mode=None,          # any mode
        context=None,       # any context
        top_k=50,
    )

    if all_mems:
        st.markdown(
            f"### 📚 Full Conversation History for {selected_region} → {location}"
        )
        st.caption(
            "Sorted by most recent first. These include both Mic and Text interactions."
        )

        for idx, r in enumerate(all_mems, start=1):
            preview = r.get("phrase", "")
            if len(preview) > 80:
                preview = preview[:77] + "..."

            ts = r.get("timestamp", "")
            ts_label = ts[:19].replace("T", " ") if ts else "no timestamp"

            label = f"💬 Turn {idx}: {preview}"
            with st.expander(label):
                st.markdown(
                    f"<div class='ea-mem-meta'>🕒 {ts_label}</div>",
                    unsafe_allow_html=True,
                )
                display_memory(r)

        if st.button("🧹 Clear ALL memories for this city"):
            msg = delete_memories_for_region(
                region=selected_region,
                location=location,
                mode=None,
                context=None,
            )
            st.success(msg)

            # also clear cached “last” values so Related tab empties
            st.session_state.last_results = []
            st.session_state.last_main_text = ""
            st.session_state.last_source_label = ""
            st.session_state.last_user_input = ""

            st.rerun()
    else:
        st.markdown("### 📚 All Memories for this City")
        st.markdown(
            """
            <div class="ea-banner">
                <div class="ea-banner-title">🕊 No Conversation History Yet</div>
                <div class="ea-banner-desc">
                    This city doesn’t have any stored conversations.<br>
                    Ask EchoAtlas a question to start building a memory trail for this region.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# -----------------------
# Global Memory Controls
# -----------------------
st.subheader("🧹 Global Memory Controls")

col1, col2 = st.columns(2)

# Soft reset: clear all entries in collection
with col1:
    if st.button("🧽 Clear ALL Memories (soft)"):

        client = chromadb.PersistentClient(path="memory_store")
        collection = client.get_or_create_collection(
            name="echoatlas_memory",
            embedding_function=OpenAIEmbeddingFunction(
                model_name="text-embedding-3-small"
            ),
        )

        all_ids = collection.get().get("ids", [])
        if all_ids and isinstance(all_ids[0], list):
            flat = []
            for sub in all_ids:
                flat.extend(sub)
            all_ids = flat

        if all_ids:
            collection.delete(ids=all_ids)
            st.success(
                f"🧽 Cleared ALL memories in collection ({len(all_ids)} entries)."
            )
        else:
            st.info("ℹ️ No memories found in the collection to clear.")

# Hard reset: schedule factory reset on next restart
with col2:
    if "show_factory_reset_confirm" not in st.session_state:
        st.session_state.show_factory_reset_confirm = False

    if st.button("🧨 Factory Reset Memory Store (hard)"):
        st.session_state.show_factory_reset_confirm = True

    if st.session_state.show_factory_reset_confirm:
        st.warning(
            "⚠️ You are about to schedule a **Factory Reset**.\n\n"
            "This will delete **ALL saved memories** for every region, location, mode, and context.\n"
            "The deletion will occur on the next app restart."
        )

        choice = st.radio(
            "Are you sure?",
            ["No", "Yes"],
            index=0,
            key="factory_reset_choice",
            horizontal=True,
        )

        colA, colB = st.columns(2)

        with colA:
            if st.button("✅ Confirm Reset"):
                if choice == "Yes":
                    flag_path = "reset_memory_store.flag"
                    try:
                        with open(flag_path, "w", encoding="utf-8") as f:
                            f.write("reset")
                        st.success(
                            "🧨 Factory reset scheduled.\n\n"
                            "Please **stop & restart** the Streamlit app.\n"
                            "On next startup, the `memory_store` folder will be deleted "
                            "and a fresh memory database will be created."
                        )
                    except Exception as e:
                        st.error(f"❌ Could not create reset flag: {e}")
                else:
                    st.info("Factory reset cancelled (you selected 'No').")

                st.session_state.show_factory_reset_confirm = False

        with colB:
            if st.button("❌ Cancel"):
                st.session_state.show_factory_reset_confirm = False
                st.info("Factory reset cancelled.")
