"""
JollyCast Support Bot
MODE: "mock"  -> runs without API key
MODE: "claude" -> requires ANTHROPIC_API_KEY in .env
"""
import os, textwrap
from dotenv import load_dotenv
load_dotenv()
import streamlit as st
from zendesk_loader import build_knowledge_base, search_articles

MODE = os.getenv("BOT_MODE", "mock")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

TROUBLE_FLOW = """
| Type | Condition | Cast Action 1 | Cast Action 2 |
|---|---|---|---|
| Property damage (life impact) | - | Call HQ during service | Report via inquiry form after |
| Property damage (no life impact) | - | Apologize, continue service | Report via inquiry form after |
| Customer absent | Contact within 30 min | Call customer (emergency phone) | Wait; if 30+ min no reply → leave, report |
| Customer absent | No contact in 30 min | Call customer, send chat | Report via inquiry form |
| Cancellation (user) | Before 2 days 18:00 | Guide customer to cancel themselves | Visit if not cancelled |
| Cancellation (user) | After 2 days 18:00 | Inform of paid cancellation | Visit if not cancelled |
| Lost / late | Running late | Call customer (emergency phone) | Ask people nearby |
| Incident (danger) | Physical risk | Swipe 110 button in app → HQ calls police | Exit immediately |
| Incident (no danger) | Direct contract solicitation | Continue service | Report via inquiry form |
"""

KNOWLEDGE = """
=== ABOUT JOLLYCAST ===
JollyCast (ジョリーキャスト) cast members are EMPLOYEES of CaSy (株式会社CaSy), not freelance contractors.
CaSy operates the cleaning/cooking service platform. JollyCast is CaSy's employed cast program.
CaSy Support number: 050-3183-8835 (available 9:00-18:00, weekdays and weekends/holidays)
This support number is correct and appropriate for JollyCast casts to use.

=== EMERGENCY PHONE (緊急電話) ===
- Used ONLY in emergencies: when lost, customer is absent, or urgent situations
- For normal communication, always use in-app chat
- Available time window: 2 hours BEFORE service start to 3 hours AFTER service end
- The customer CANNOT see the cast's personal phone number (it is hidden/masked)
- Customer callbacks come from a 050 number
- How to call: App MENU → Schedule → Upcoming → tap the service time (blue) → Customer Info → Phone → "Show phone number" → "Make call"
- If the feature doesn't work (non-registered device or feature phone): contact HQ directly at 050-3183-8835

=== 110 EMERGENCY BUTTON (110番通報ボタン) ===
- Located at the TOP of the cast app home screen
- Visible from 10 minutes BEFORE service start to 30 minutes AFTER service end
- How to use: Press button → swipe "Swipe to complete report" → CaSy HQ immediately calls 110 (police) on cast's behalf
- After police are notified, HQ will also call the cast
- Use when: physical violence, sexual harassment, stalking, any criminal act
- Cast should keep smartphone accessible (use strap or armband, NOT pocket) to avoid accidental press
- Keep belongings near the entrance so you can exit quickly if needed

=== INQUIRY FORM (お問い合わせフォーム) ===
- URL: https://casy.zendesk.com/hc/ja/requests/new?ticket_form_id=900000114666
- When submitting, select:
  - 属性 (Role): キャストとして働いている方
  - 項目 (Category): 9：トラブルが起きた
  - トラブルの内容 (Type): 4：物損 (for property damage), or appropriate category
- Include: Service ID, date/time, description of what happened

=== PROPERTY DAMAGE REPORTING PROCEDURE ===
1. Tell customer you will report to HQ after service (apologize sincerely)
2. Continue service as scheduled
3. Submit inquiry form after service (select: トラブル → 物損)
4. Also note it in your daily report, including "already reported to support"
- If damage is life-impacting (e.g. broke toilet, caused water leak, broke major appliance): call HQ IMMEDIATELY at 050-3183-8835 during service

=== DISCIPLINARY RULES (JollyCast-specific) ===
NOTE: JollyCast casts are employees. Disciplinary actions follow 就業規則 (employment rules/懲戒), NOT the freelance cast contract termination process.
- Property damage (furniture/appliances): 3+ incidents in 6 months → disciplinary review
- Key loss: Serious incident (Level 2) → disciplinary action per 就業規則
- Cancellations (3+ in 90 days): disciplinary action per 就業規則
- Direct contract solicitation: first warning, then disciplinary action if repeated
- Direct personal contact exchange: first warning, then disciplinary action
- Visiting customer home outside service hours: prohibited (住居侵入 risk)

=== RULES FOR CAST BEHAVIOR ===
- Never visit customer's home outside scheduled service time (prohibited — legal risk)
- Never exchange personal contact information with customers
- Never accept direct hiring offers from customers (refer them to CaSy)
- Never bring friends or helpers to a service
- Never take photos inside customer's home
- Valuables (cash, jewelry) found: do not touch, do not move — report to HQ via inquiry form
- Tips/gifts: see TIPS / GIFTS FROM CUSTOMERS section below
- Food/drinks offered by customer: small items (drinks, snacks ~100-200 yen) may be accepted with gratitude; cash, gift cards, high-value items must be declined
- Rude customers: remain calm, do not argue; if safety is at risk, contact HQ

=== AFTER SERVICE / BETWEEN SERVICES ===
- Go directly to next service — no need to report to office between services
- Lunch break: 45 minutes allowed between services (cannot exceed 45 min)
- If no service (gap between services or end of day with time remaining): go to the Meguro office to study Japanese using Duolingo. This is a JollyCast-specific rule — Japanese study during work hours is considered part of your job.
- If last service is done and work hours are over: you may go home directly.
- Incidents must be reported via inquiry form AFTER leaving (do not delay departure for this)

=== TIPS / GIFTS FROM CUSTOMERS ===
- Cash: NEVER accepted (strictly prohibited)
- Gift cards, vouchers, high-value items (branded goods, electronics, etc.): NEVER accepted
- Small consumables (drinks, snacks — roughly 100-200 yen equivalent): acceptable, with gratitude
- If unsure: do not accept. Politely say: "Thank you, but company rules do not allow me to accept this."
- Always report to HQ if offered something significant

=== APP OPERATIONS (チェックイン・チェックアウト・日報) ===
- For detailed app operation steps (check-in, check-out, daily report, schedule viewing), refer to the training video: https://casy.zendesk.com/hc/ja/articles/31405614157209
- If the app is not working or you cannot check in: call HQ immediately at 050-3183-8835
- If you forgot to check out: contact HQ via support phone or inquiry form to correct it
- If the app crashes and you lose your service record: contact HQ at 050-3183-8835

=== SCHEDULE CHANGES ===
- Cast cannot arrange schedule changes directly — all changes must go through CaSy app/support
- Contact CaSy support: 050-3183-8835 or inquiry form
- Customer requesting different cast: handled by CaSy support, not the cast
"""

# ── 回答生成関数（UI より先に定義） ───────────────────────────

def generate_mock_response(question: str, relevant_articles: list) -> str:
    q = question.lower()

    if any(w in q for w in ["absent", "not home", "no one", "no answer", "not there", "not reply", "no reply", "not responding",
                             "不在", "来ない", "戻ってこない", "いない", "応答ない", "返事ない", "待った", "待ってい", "出てこない", "開けない"]):
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

    elif any(w in q for w in ["cancel", "cancellation", "キャンセル", "取り消し"]):
        return textwrap.dedent("""\
            **Cancellation procedure:**

            **If the customer wants to cancel:**

            - *More than 2 days before service (before 18:00):*
              Ask the customer to cancel through the app themselves. If they have not cancelled, still visit.

            - *Less than 2 days before service (after 18:00, 2 days prior):*
              This is a **paid cancellation**. Inform the customer that a cancellation fee applies.
              If they have not cancelled in the app, still visit.

            **If you need to cancel (cast-initiated):**
            1. Send a chat message to the customer immediately
            2. Process the cancellation in the app yourself

            **Warning:** 3+ cancellations within 90 days = disciplinary action

            📞 Questions? Call CaSy Support: **050-3183-8835**

            *Source: Trouble Flow Guide — キャンセル*
        """)

    elif any(w in q for w in ["lost", "address", "wrong address", "can't find", "cannot find", "where", "room", "floor", "building",
                              "道に迷", "住所", "見つからない", "場所", "何階", "号室", "部屋番号"]):
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

    elif any(w in q for w in ["key", "locked", "no key", "don't have key", "dont have key", "鍵", "カギ", "入れない", "開かない"]):
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

    elif any(w in q for w in ["damage", "broke", "broken", "accident", "property", "物損", "壊", "割れ", "傷", "破損"]):
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

    elif any(w in q for w in ["qr", "voucher", "scan", "code", "バウチャー", "スキャン", "紙"]):
        return textwrap.dedent("""\
            **QR code / Voucher:**

            - The customer scans the QR code **once** to confirm service completion
            - Once scanned, you do **not** need to collect a paper voucher
            - If you forgot to collect the voucher, report via the **inquiry form** immediately

            *Source: Training Booklet Day 18 — Completing Service*
        """)

    elif any(w in q for w in ["schedule", "change", "time", "reschedule", "change time", "日程", "時間変更", "スケジュール", "変更"]):
        return textwrap.dedent("""\
            **Schedule change request from customer:**

            1. The change needs to be processed through the CaSy app
            2. Contact CaSy support to help process: **050-3183-8835**
            3. Customer approval is also required for the change to be confirmed

            *Source: Zendesk — 定期サービスの日程変更*
        """)

    elif any(w in q for w in ["visit", "go to house", "go to their house", "go into their house", "go to their home", "stop by", "outside service", "in person", "hand me",
                              "訪問", "家に行", "渡す", "受け取り", "サービス外"]):
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

KNOWLEDGE BASE:
{KNOWLEDGE}

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
