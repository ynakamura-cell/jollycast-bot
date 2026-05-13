"""
JollyCast Support Bot
MODE: "mock"  -> runs without API key
MODE: "claude" -> requires ANTHROPIC_API_KEY in .env
"""
import os, textwrap
import streamlit as st
from zendesk_loader import build_knowledge_base, search_articles

MODE = os.getenv("BOT_MODE", "mock")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

TROUBLE_FLOW = """
| Type | Condition | Cast Action 1 | Cast Action 2 |
|---|---|---|---|
| Property damage (life impact) | - | Call HQ during service | Report via inquiry form |
| Property damage (no life impact) | - | Apologize, continue service | Report via inquiry form after |
| Customer absent | Contact within 30 min | Call customer (emergency phone) | Wait; if 30+ min no reply → leave, report |
| Customer absent | No contact in 30 min | Call customer, send chat | Report via inquiry form |
| Cancellation (user) | Before 2 days 18:00 | Guide customer to cancel themselves | Visit if not cancelled |
| Cancellation (user) | After 2 days 18:00 | Inform of paid cancellation | Visit if not cancelled |
| Lost / late | Running late | Call customer (emergency phone) | Ask people nearby |
| Incident (danger) | Physical risk | Call 110 from app | Exit immediately |
| Incident (no danger) | Direct contract solicitation | Continue service | Report via inquiry form |
"""

# ── 回答生成関数（UI より先に定義） ───────────────────────────

def generate_mock_response(question: str, relevant_articles: list) -> str:
    q = question.lower()

    if any(w in q for w in ["absent", "not home", "no one", "no answer", "not there", "not reply", "no reply", "not responding"]):
        return textwrap.dedent("""\
            **Customer is not home — here's what to do:**

            1. Ring the doorbell and wait
            2. Call the customer using the **emergency phone** in the CaSy app
            3. If no answer, send a chat message to the customer
            4. **Wait up to 30 minutes** from the scheduled start time
            5. If still no response after 30 minutes, send this via chat:
               > *"I have been waiting outside but could not reach you. I will need to leave now. This will be treated as a paid cancellation."*
            6. Report the incident via the **inquiry form** after leaving

            📞 If you need help: **050-3183-8835**

            *Source: CaSy Zendesk — お客様がご不在の時 / Trouble Flow Guide*
        """)

    elif any(w in q for w in ["cancel", "cancellation"]):
        return textwrap.dedent("""\
            **Cancellation procedure:**

            **If the customer wants to cancel:**
            - Ask the customer to cancel through the app themselves
            - If they have not cancelled, you should still visit

            **If you need to cancel (cast-initiated):**
            1. Send a chat message to the customer immediately
            2. Process the cancellation in the app yourself

            **Warning:** 3+ cancellations within 90 days = disciplinary action

            📞 Questions? Call CaSy Support: **050-3183-8835**

            *Source: Trouble Flow Guide — キャンセル*
        """)

    elif any(w in q for w in ["lost", "address", "wrong address", "can't find", "cannot find", "where", "room", "floor", "building"]):
        return textwrap.dedent("""\
            **Cannot find the address / getting lost:**

            1. **Try to figure it out yourself** — check Google Maps carefully
            2. **Ask someone nearby** using this Japanese phrase:
               > *Sumimasen, tasukete kudasai. Michi ni mayoimashita. [ADDRESS] ni ikitai desu.*
            3. **Call the customer** using the emergency phone in the app
            4. Contact your trainer if still stuck

            **Room number tip:** In Japan:
            - "202" = 2nd floor, room 02
            - "302" = 3rd floor, room 02

            📞 CaSy Support: **050-3183-8835**

            *Source: Training Booklet Day 1 / Zendesk — 道に迷った時*
        """)

    elif any(w in q for w in ["key", "locked", "no key", "don't have key", "dont have key"]):
        return textwrap.dedent("""\
            **No key / locked out:**

            If you do not have a key deposit arrangement:
            - The customer needs to be home to let you in
            - Send a chat message: *"I'm here but don't have a key. Could you please open the door?"*
            - If no response, use the emergency phone in the CaSy app

            If you were supposed to have a key but don't:
            - Contact CaSy Support immediately: **050-3183-8835**

            *Source: CaSy Zendesk — サービスの仕組み*
        """)

    elif any(w in q for w in ["damage", "broke", "broken", "accident", "property"]):
        return textwrap.dedent("""\
            **Property damage — what to do:**

            **If it affects daily life (e.g., broke a major appliance, TV):**
            1. Call HQ immediately during service: **050-3183-8835**
            2. Apologize to the customer sincerely
            3. Report via inquiry form after service ends

            **If it does not affect daily life (minor damage):**
            1. Apologize to the customer and continue service
            2. Report via inquiry form after service ends
            3. Also include it in your daily report

            **Warning:** 3+ property damage incidents in 6 months = disciplinary action

            *Source: Trouble Flow Guide — 物損*
        """)

    elif any(w in q for w in ["next service", "go home", "report", "office", "straight", "leave now", "leaving"]):
        return textwrap.dedent("""\
            **After finishing / between services:**

            - Go **directly to your next service** — no need to report to the office
            - If there was an incident, report via the **inquiry form** after service
            - If you have no afternoon service: study Japanese at the **Meguro office**
            - You can take a **45-minute lunch break** between services

            📞 CaSy Support: **050-3183-8835**

            *Source: JollyCast operating rules / Trouble Flow Guide*
        """)

    elif any(w in q for w in ["qr", "voucher", "scan", "code"]):
        return textwrap.dedent("""\
            **QR code / Voucher:**

            - The customer scans the QR code **once** to confirm service completion
            - Once scanned, you do **not** need to collect a paper voucher
            - If you forgot to collect the voucher, report via the **inquiry form** immediately

            *Source: Training Booklet Day 18 — Completing Service*
        """)

    elif any(w in q for w in ["schedule", "change", "time", "reschedule", "change time"]):
        return textwrap.dedent("""\
            **Schedule change request from customer:**

            1. The change needs to be processed through the CaSy app
            2. Contact CaSy support to help process: **050-3183-8835**
            3. Customer approval is also required for the change to be confirmed

            *Source: Zendesk — 定期サービスの日程変更*
        """)

    elif any(w in q for w in ["visit", "go to house", "go to their house", "outside service"]):
        return textwrap.dedent("""\
            **Visiting outside of service hours:**

            Visiting a customer's home outside of your scheduled service time is **strictly prohibited**.

            - Do not visit the customer's home outside of your booking time
            - If the customer needs something (e.g., pass a document), ask them to mail it
            - For any questions, contact CaSy Support: **050-3183-8835**

            *Source: JollyCast Policy / 中村さんの案内 (5/13)*
        """)

    else:
        if relevant_articles:
            titles = "\n".join(f"- {a['title']}" for a in relevant_articles)
            return textwrap.dedent(f"""\
                Here is some relevant information I found:

                {titles}

                For your specific situation, please check the CaSy manual or contact support directly.

                📞 CaSy Support: **050-3183-8835**

                *(DEMO mode — the live Claude AI version would give a more precise answer for this question)*
            """)
        else:
            return textwrap.dedent("""\
                I could not find specific information about that in the manual.

                Please contact CaSy Support directly:
                📞 **050-3183-8835**

                *(DEMO mode — the live Claude AI version searches more deeply and handles any question)*
            """)


def generate_claude_response(question: str, context: str) -> str:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        prompt = f"""You are a support assistant for JollyCast (ジョリーキャスト), helping Filipino cast members in Japan.
Always respond in English. Be concise and action-oriented — cast members are often mid-service.
Number steps clearly. Always end with CaSy support number if urgent: 050-3183-8835.

TROUBLE FLOW:
{TROUBLE_FLOW}

MANUAL EXCERPTS:
{context}

QUESTION: {question}"""
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        return f"Error connecting to Claude API: {e}\n\nPlease check your API key.\n\n📞 CaSy Support: **050-3183-8835**"


# ── ページ設定 ────────────────────────────────────────────────

st.set_page_config(page_title="JollyCast Support Bot", page_icon="🧹", layout="centered")

st.markdown("""
<style>
.badge { display:inline-block; padding:3px 12px; border-radius:12px; font-size:12px; font-weight:bold; margin-bottom:8px; }
.mock  { background:#FFF3CD; color:#856404; }
.live  { background:#D1E7DD; color:#0A3622; }
</style>
""", unsafe_allow_html=True)

st.title("🧹 JollyCast Support Bot")
st.caption("Ask anything about your service — available 24/7")

if MODE == "mock":
    st.markdown('<span class="badge mock">⚠️ DEMO MODE — responses are simulated</span>', unsafe_allow_html=True)
else:
    st.markdown('<span class="badge live">✅ LIVE — powered by Claude AI</span>', unsafe_allow_html=True)

st.divider()

# ── ナレッジベース読み込み ────────────────────────────────────

@st.cache_resource(show_spinner="Loading manual data from Zendesk...")
def load_kb():
    return build_knowledge_base()

articles = load_kb()

with st.sidebar:
    st.markdown(f"📚 **Knowledge base**: {len(articles)} articles loaded from Zendesk")
    st.markdown("**Sources:**\n- CaSy Zendesk manual\n- Trouble flow guide\n- Training booklet (Day 1-24)")
    st.divider()
    st.markdown("🆘 **Emergency**: CaSy Support")
    st.markdown("📞 `050-3183-8835`")
    if len(articles) > 0:
        with st.expander("Loaded articles"):
            for a in articles:
                st.markdown(f"- {a['title'][:50]}")

# ── チャット履歴 ──────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! I'm your JollyCast support assistant. Ask me anything about your service — what to do if a customer is absent, how to handle property damage, schedule changes, and more. I'm here 24/7! 😊"}
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── 入力 ─────────────────────────────────────────────────────

if prompt := st.chat_input("Type your question here (English OK)..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    relevant = search_articles(prompt, articles, top_k=3)
    context_text = "\n\n---\n\n".join(
        f"[{a['title']}]\n{a['content'][:600]}" for a in relevant
    )
    sources = [{"title": a["title"], "url": a["url"]} for a in relevant]

    with st.chat_message("assistant"):
        if MODE == "mock":
            response = generate_mock_response(prompt, relevant)
        else:
            response = generate_claude_response(prompt, context_text)

        st.markdown(response)

        if sources:
            with st.expander("📖 Sources from Zendesk", expanded=False):
                for s in sources:
                    st.markdown(f"- [{s['title']}]({s['url']})")

    st.session_state.messages.append({"role": "assistant", "content": response})
