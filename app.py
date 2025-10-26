import streamlit as st
import time
import json
from datetime import datetime
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="Intense Debator", page_icon="💬")

st.markdown("""
<style>
    .stApp { background-color: #121212; color: #FFFFFF; }
    .css-1d391kg { background-color: #1E1E2E !important; color: white; }
    .stButton>button {
        background-color: #4A90E2; color: white; border-radius: 6px; font-weight: bold;
    }
    .stProgress > div > div > div { background-color: #4A90E2; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1E1E2E; color: white; border: 1px solid #333;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #4A90E2; border-bottom: 3px solid #FF6B6B;
    }
    h1, h2, h3 { color: #FFFFFF; }
</style>
""", unsafe_allow_html=True)

# ✅ SESSION STATE INIT — ALL KEYS
if 'prompt' not in st.session_state:
    st.session_state.prompt = ""
if 'answer' not in st.session_state:
    st.session_state.answer = ""
if 'timer_active' not in st.session_state:
    st.session_state.timer_active = False
if 'timer_start' not in st.session_state:
    st.session_state.timer_start = None
if 'feedback_data' not in st.session_state:
    st.session_state.feedback_data = None
if 'time_limit' not in st.session_state:
    st.session_state.time_limit = 60
if 'current_q_index' not in st.session_state:
    st.session_state.current_q_index = 0
if 'cross_transcript' not in st.session_state:
    st.session_state.cross_transcript = []

def reset_all():
    st.session_state.prompt = ""
    st.session_state.answer = ""
    st.session_state.timer_active = False
    st.session_state.timer_start = None
    st.session_state.feedback_data = None
    st.session_state.current_q_index = 0
    st.session_state.cross_transcript = []

def get_feedback(text, topic, difficulty):
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """
You are a debate coach. Return ONLY valid JSON with:
{
  "scores": {"structure": int, "clarity": int, "evidence": int, "rhetoric": int},
  "summary": "short evaluation",
  "improvements": ["tip1", "tip2", "tip3"],
  "suggested_practice": ["ex1", "ex2", "ex3"]
}
Be specific and constructive. No extra text.
                """.strip()},
                {"role": "user", "content": f"Topic: {topic}\nDifficulty: {difficulty}/5\nResponse:\n```\n{text}\n```"}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        st.error("⚠️ AI feedback failed. Using sample data.")
        return {
            "scores": {"structure": 70, "clarity": 75, "evidence": 60, "rhetoric": 65},
            "summary": "Solid start! Add more evidence and tighten your structure.",
            "improvements": [
                "Back claims with real-world examples or data",
                "Use clear transitions between points",
                "Vary sentence length for impact"
            ],
            "suggested_practice": [
                "Practice 2-minute impromptu speeches daily",
                "Watch and analyze Oxford-style debates",
                "Record yourself and review pacing/clarity"
            ]
        }

# ===== SIDEBAR =====
with st.sidebar:
    st.image("https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/apple/325/speech-balloon_1f4ac.png", width=40)
    st.title("💬 Intense Debator")
    st.markdown("### 📘 How to Use\n1. Pick a topic\n2. Set time & difficulty\n3. Go to **Prompts** → *New Prompt*\n4. Type while timer runs\n5. Submit → see **Feedback**")
    st.divider()
    
    topic = st.selectbox("Topic Category", [
        "Science", "History", "Current Trends", "Global Issues",
        "Ethics", "Technology", "Economics", "Environment"
    ])
    difficulty = st.slider("Difficulty", 1, 5, 3)
    time_limit = st.selectbox("Time (seconds)", [60, 90, 120])
    auto_start = st.checkbox("Auto-start timer", value=True)
    st.session_state.time_limit = time_limit

    st.divider()
    if st.button("🔄 Reset All", type="primary"):
        reset_all()
        st.rerun()

# ===== MAIN APP =====
st.title("💬 Intense Debator")
tabs = st.tabs(["Prompts", "Crossing", "Feedback"])

# --- PROMPTS TAB ---
with tabs[0]:
    st.subheader("🎯 Generate a Prompt")
    
    if st.button("New Prompt"):
        prompts = {
            "Science": "Should gene editing in humans be universally banned?",
            "History": "Was the Industrial Revolution more harmful than beneficial?",
            "Current Trends": "Is remote work damaging urban economies long-term?",
            "Global Issues": "Should wealthy nations fund climate adaptation in poorer countries?",
            "Ethics": "Is it ever justifiable to use AI for lethal autonomous weapons?",
            "Technology": "Do social media algorithms harm democracy more than they help?",
            "Economics": "Should governments cap personal wealth to reduce inequality?",
            "Environment": "Is nuclear energy the best replacement for fossil fuels?"
        }
        st.session_state.prompt = prompts.get(topic, f"Debate a key issue in {topic}.")
        st.session_state.answer = ""
        if auto_start:
            st.session_state.timer_active = True
            st.session_state.timer_start = time.time()
        else:
            st.session_state.timer_active = False
    
    if st.session_state.prompt:
        st.write(f"**{st.session_state.prompt}**")
        
        st.session_state.answer = st.text_area(
            "Your Response:",
            value=st.session_state.answer,
            height=180,
            disabled=not st.session_state.timer_active
        )
        
        if st.session_state.timer_active:
            elapsed = time.time() - st.session_state.timer_start
            remaining = max(0, st.session_state.time_limit - elapsed)
            st.progress(remaining / st.session_state.time_limit)
            st.write(f"⏰ {int(remaining)}s left")
            if remaining <= 0:
                st.session_state.timer_active = False
                st.warning("Time’s up! Submit your answer.")
            else:
                time.sleep(1)
                st.rerun()
        else:
            if st.session_state.timer_start is not None:
                used = min(st.session_state.time_limit, int(time.time() - st.session_state.timer_start))
                st.progress(used / st.session_state.time_limit)
                st.write(f"⏸️ Paused ({used}s used)")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if not st.session_state.timer_active and st.session_state.prompt and not auto_start:
                if st.button("▶️ Start Timer"):
                    st.session_state.timer_start = time.time()
                    st.session_state.timer_active = True
                    st.rerun()
        with col2:
            if st.session_state.timer_active:
                if st.button("⏸️ Pause"):
                    st.session_state.timer_active = False
                    st.rerun()
        with col3:
            if st.button("⏹️ Stop & Reset"):
                reset_all()
                st.rerun()
        
        # ✅ SAFE check for None or empty string
        if st.button("✅ Submit Response", disabled=not (st.session_state.answer and st.session_state.answer.strip())):
            with st.spinner("Analyzing your argument..."):
                st.session_state.feedback_data = get_feedback(st.session_state.answer, topic, difficulty)
            st.success("Submitted! Check the Feedback tab.")
    else:
        st.info("Click 'New Prompt' to begin.")

# --- CROSSING TAB ---
with tabs[1]:
    st.subheader("🔄 Cross-Examination")
    
    questions = {
        "Science": ["What empirical evidence supports your claim?", "How would you respond to critics who say this technology is too risky?", "Can you explain the ethical implications of your position?", "What are the long-term societal impacts of your proposal?", "Who benefits most from your solution, and who might be harmed?"],
        "History": ["Which historical precedent supports your argument?", "How does your view differ from mainstream historiography?", "What primary sources back your interpretation?", "How would your policy have changed the outcome of [event]?", "What unintended consequences might arise from applying this lesson today?"],
        "Current Trends": ["What recent data supports your stance?", "How does your argument address the counter-trend of [opposing force]?", "Who are the key stakeholders affected by this trend?", "What regulatory or market forces could disrupt your prediction?", "How scalable is your proposed solution in the next 5 years?"],
        "Global Issues": ["Which international treaties or organizations are relevant here?", "How would your solution be enforced across borders?", "What role should non-state actors play?", "How do you balance sovereignty with global responsibility?", "What metrics would measure success of your proposal?"],
        "Ethics": ["Which ethical framework guides your view?", "How do you weigh individual rights against collective good?", "What moral dilemma does your position create?", "Can you justify your stance in a worst-case scenario?", "How does your argument hold under scrutiny from opposing ethical views?"],
        "Technology": ["What technical limitations affect your proposal?", "How does your solution handle privacy or security concerns?", "What is the innovation-to-risk ratio of your approach?", "How would you regulate this technology without stifling progress?", "What user behavior patterns must change for your solution to succeed?"],
        "Economics": ["What fiscal or monetary policies support your claim?", "How would your proposal affect GDP, inflation, or unemployment?", "Who bears the cost of implementation?", "What market distortions might arise?", "How does your solution compare to existing economic models?"],
        "Environment": ["Which ecosystems or species are most impacted by your proposal?", "How do you quantify environmental risk vs. economic benefit?", "What scientific models support your intervention?", "How would climate change alter the effectiveness of your plan?", "What funding mechanisms ensure long-term sustainability?"]
    }
    
    if st.button("Start Cross-Ex"):
        st.session_state.cross_transcript = []
        st.session_state.current_q_index = 0
        st.session_state.timer_start = time.time()
        st.session_state.timer_active = True
    
    if st.session_state.cross_transcript or st.session_state.current_q_index < 5:
        if st.session_state.current_q_index < 5:
            current_q = questions[topic][st.session_state.current_q_index]
            st.subheader(f"Question {st.session_state.current_q_index + 1}/5")
            st.write(f"**{current_q}**")
            
            user_answer = st.text_area(
                "Your Answer:",
                height=150,
                key=f"cross_ex_{st.session_state.current_q_index}",
                disabled=not st.session_state.timer_active
            )
            
            if st.session_state.timer_active:
                elapsed = time.time() - st.session_state.timer_start
                remaining = max(0, st.session_state.time_limit - elapsed)
                st.progress(remaining / st.session_state.time_limit)
                st.write(f"⏰ {int(remaining)}s left")
                if remaining <= 0:
                    st.session_state.timer_active = False
                    st.warning("Time's up! Submit your answer.")
                else:
                    time.sleep(1)
                    st.rerun()
            
            if st.button("Submit Answer", key="cross_ex_submit"):
                if user_answer.strip():
                    st.session_state.cross_transcript.append({"question": current_q, "answer": user_answer})
                    st.session_state.current_q_index += 1
                    st.session_state.timer_start = time.time()
                    st.session_state.timer_active = True
                    st.rerun()
                else:
                    st.error("Please provide an answer.")
        else:
            st.success("Cross-examination complete!")
            st.subheader("Transcript")
            for i, qa in enumerate(st.session_state.cross_transcript):
                st.write(f"**Q{i+1}:** {qa['question']}")
                st.write(f"**A:** {qa['answer']}")
                st.divider()
            
            full_transcript = "\n\n".join([f"Q: {qa['question']}\nA: {qa['answer']}" for qa in st.session_state.cross_transcript])
            if st.button("Get Feedback"):
                with st.spinner("🧠 Analyzing your cross-ex..."):
                    st.session_state.feedback_data = get_feedback(full_transcript, topic, difficulty)
                st.success("Feedback generated! View in Feedback tab.")
    else:
        st.info("Click 'Start Cross-Ex' to begin.")

# --- FEEDBACK TAB ---
with tabs[2]:
    st.subheader("📊 Your Feedback")
    # ✅ CORRECTED: use feedback_data, NOT feedback_
    if st.session_state.feedback_data is not None:
        data = st.session_state.feedback_data
        cols = st.columns(4)
        for i, (name, score) in enumerate(data["scores"].items()):
            with cols[i]:
                st.metric(name.title(), f"{score}/100")
                st.progress(score / 100)
        st.write(f"**Summary:** {data['summary']}")
        st.markdown("### 🔧 Improvements")
        for tip in data["improvements"]:
            st.write(f"- {tip}")
        st.markdown("### 📚 Practice Suggestions")
        for ex in data["suggested_practice"]:
            st.write(f"- {ex}")
        report = {
            "timestamp": datetime.now().isoformat(),
            "topic": topic,
            "difficulty": difficulty,
            "time_limit_sec": time_limit,
            **data
        }
        st.download_button(
            "📥 Download Report (JSON)",
            data=json.dumps(report, indent=2),
            file_name="intense_debator_feedback.json",
            mime="application/json"
        )
    else:
        st.info("Complete a prompt or cross-ex to see feedback here.")