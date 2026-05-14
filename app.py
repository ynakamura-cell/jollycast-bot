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

def _secret(key, default=""):
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key, default)

MODE = _secret("BOT_MODE", os.getenv("BOT_MODE", "mock"))
ANTHROPIC_API_KEY = _secret("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))

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
- How to use: Press button → swipe "Swipe to complete report" → CaSy HQ immediately calls 110 (police) on cast's behalf. HQ then calls the cast.
- Use when: physical violence, sexual harassment, stalking, any criminal act by customer
- IMPORTANT: The cast manual does NOT instruct casts to call 110 directly themselves. Always use the in-app button so HQ handles the police call.
- If the button is unavailable: exit immediately and call HQ at 050-3183-8835
- Cast should keep smartphone accessible (use strap or armband, NOT pocket)
- Keep belongings near the entrance so you can exit quickly if needed

=== INQUIRY FORM (お問い合わせフォーム) ===
- URL: https://casy.zendesk.com/hc/ja/requests/new?ticket_form_id=900000114666
- When submitting, select:
  - 属性 (Role): キャストとして働いている方
  - 項目 (Category): 9：トラブルが起きた
  - トラブルの内容 (Type): 4：物損 (for property damage), or appropriate category
- Include: Service ID, date/time, description of what happened

=== PROPERTY DAMAGE REPORTING PROCEDURE ===

CASE A — Life-impacting damage (broken toilet, water leak, major appliance):
1. Apologize sincerely to customer
2. Call HQ IMMEDIATELY at 050-3183-8835 during service (do not wait until after)
3. Take photos of the damage (with customer's permission) — include maker name, model number
4. Send photo + details to HQ (by email or inquiry form)
5. Continue service (add extra time for the interruption)
6. Write daily report noting "called and reported to support"

CASE B — Non-life-impacting damage (scratched floor, broken glass, minor item):
1. Apologize sincerely to customer; tell them you will report to HQ after service
2. Continue service as scheduled
3. After service: submit inquiry form with PHOTO attached
   - 属性: キャストとして働いている方 / 項目: 9: トラブルが起きた / トラブルの内容: 4: 物損
   - Include: service ID, date/time, customer name, description, maker/model number, photo
4. Write daily report noting "reported to support via inquiry form"

CASE C — Minor damage, customer waived compensation:
1. Apologize sincerely; tell customer you will still report to HQ
2. Continue service as scheduled
3. After service: submit inquiry form (even if customer said it's OK — always report)
4. Write daily report noting "reported to support"

NOTE: Even if the customer forgives the damage, ALWAYS report to HQ. HQ will follow up with the customer directly.
NOTE: Do NOT offer to pay the customer directly. Do NOT say "our insurance will cover it" — let HQ handle compensation.
NOTE: For housing fixtures (water pipes, wall damage): customer should contact repair company or building management themselves.
Cast liability cap: ¥3,000 per incident. Exceptions (cast may owe more): intentional/gross negligence, marble surface non-standard cleaning, disposer operation.
Gross negligence examples: using steel wool on stainless steel, leaving vacuum cleaner propped up unattended, leaving oil on open flame unattended.

=== UNSANITARY / UNSAFE ENVIRONMENT (退出基準) ===
Source: CaSy Zendesk — 退出基準 / Service Policy

TWO TYPES of exit situations:

TYPE A — "Prohibited customer behavior" (サービス中の禁止行為):
- Physical/sexual/psychological harassment, threats, stalking
- You may exit immediately mid-service. Service fee is paid in FULL.
- If you feel physically threatened: use the 110 button in the app.
- After exiting: contact HQ by phone (050-3183-8835) or email as soon as you've calmed down.

TYPE B — "Safety-concern environment" (安全面に懸念のある環境):
- Unsanitary environment: pest infestation (cockroaches, rats), feces/urine smell, extreme clutter blocking movement
- Injury/health risk: aggressive unleashed pet, broken glass, cast feeling physically ill from conditions
- Other: drunken customer, child alone who prevents safe service, extreme outdoor heat

EXIT PROCEDURE for Type B:
1. Tell the customer calmly: "Due to safety and hygiene concerns, I am unable to provide the service today. I sincerely apologize. CaSy HQ will contact you shortly."
   (「安全面・衛生面において懸念がございますためサービスのご提供が難しいです。本日は失礼いたします。追って本部よりご連絡させていただきます。」)
   - You do NOT need HQ approval before exiting — you can decide to leave yourself
   - If it is difficult to explain, you may exit without explanation — your safety comes first
2. After exiting: contact HQ by phone (050-3183-8835) or inquiry form (9: トラブルが起きた) as soon as possible

SPECIAL CASES (where asking for a fix first makes sense before exiting):
  - Pet running freely but not aggressive → politely ask: "Our policy requires pets in a cage or separate room. Could you please arrange that?" Exit only if refused.
  - Outdoor work in summer heat → do indoor tasks instead; no need to exit entirely
  - Child home alone, behaving calmly → service can proceed normally
  - Child home alone and dangerous (running into hazards, clinging) → chat parent and exit

IMPORTANT: Customer-caused exit (unsanitary/unsafe conditions) does NOT count as cast 欠勤. No Recoru application or salary deduction applies in these cases.

=== COOKING SERVICE — LATE ARRIVAL (遅刻) ===
Source: CaSy Zendesk — パッケージ料理サービス遅刻時の対応
Service time is NEVER extended at the end to compensate for late arrival.

RULE BY DELAY LENGTH:
- Less than 30 minutes late → prepare ALL 8 dishes as normal (no refund)
- 30 minutes to under 90 minutes late → prepare 4 dishes only; 50% REFUND issued by HQ
- 90 minutes or more late → service CANCELLED; FULL REFUND issued by HQ
  (Same rule applies if customer requests to shorten the service end time)

When 30–90 min late, say to customer:
"I sincerely apologize for keeping you waiting. Due to the delay, I will prepare the specified 4 dishes and HQ will issue a 50% refund. Which 4 dishes would you prefer — Set 1 or Set 2? Please choose."

ALWAYS report late arrival to HQ via inquiry form after service. HQ handles the refund and apology to customer.

=== COOKING SERVICE — QUALITY ISSUES & CUSTOMER COMPLAINTS ===
Source: CaSy Zendesk — トラブル/サービス品質不良を起こした際の対応方法

If service quality fell short of what was promised (e.g., fewer dishes than planned due to time running out, burned food, poor result):
1. Sincerely apologize — do not argue or make excuses
2. Do NOT attempt to redo or extend service on your own judgment
3. Tell customer: "I sincerely apologize. HQ will contact you to resolve this properly."
4. After service: report via inquiry form (select: 9: トラブルが起きた)

IMPORTANT on refunds:
- Partial refund for fewer dishes: only applies when the shortfall is due to cast's late arrival or cast's fault — HQ determines and processes. Cast does NOT promise a specific refund amount.
- "Food doesn't taste good": this is a quality/satisfaction issue, NOT an automatic basis for a refund. Apologize sincerely, ask for feedback, report to HQ. HQ will follow up.
- Customer wants FULL refund for completed service: do not agree on the spot — tell them HQ will contact them.
- NEVER handle money or refunds directly with the customer.

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
- Never take photos inside customer's home (or post anything on SNS about customers or service locations)
- Never charge your phone or devices at a customer's home
- Never leak or share customer personal information
- Valuables (cash, jewelry) found: do not touch, do not move — report to HQ via inquiry form
- Tips/gifts: see TIPS / GIFTS FROM CUSTOMERS section below
- Food/drinks offered by customer: small items (drinks, snacks ~100-200 yen) may be accepted with gratitude; cash, gift cards, high-value items must be declined
- Rude customers: remain calm, do not argue; if safety is at risk, contact HQ

=== AFTER SERVICE / BETWEEN SERVICES ===
- After your LAST service of the day: go home directly. No need to go to the office.
- Between two services (on a 2-service day):
  - You may take a break for the gap time MINUS travel time to the next service
  - Labor law (労働基準法) requires AT LEAST 45 minutes of break for a 6-hour shift — this is MANDATORY minimum, not a maximum
  - Example: 90-min gap with 30-min travel → 60 min free; you must take at least 45 min as break
  - No need to go to the office between services
- Cannot extend service time: if a customer asks to stay longer, politely decline: "I'm sorry, I have another appointment." This applies even if you have no next service — time extension must go through CaSy.
- Incidents must be reported via inquiry form AFTER leaving the service location (do not delay departure for this).
- For unusual situations (unexpected free time, schedule question): contact HQ via inquiry form or 050-3183-8835.

=== RECORU (勤怠管理システム) — HOW JOLLYCAST CASTS USE IT ===
Source: Confluence — ジョリーキャストの休暇申請フロー / 戦略特区_勤怠チェックリスト補足

IMPORTANT: JollyCast casts do NOT manually clock in or out in Recoru.
- Work schedules/shifts are pre-registered in Recoru by CaSy staff
- Casts use Recoru ONLY to apply for irregular leave: 遅刻 (late), 早退 (early leave), 欠勤 (absence)
- Recoru URL: https://app.recoru.in/ap/?c=252284

WHAT CASTS DO IN RECORU:
- Sudden late arrival → apply for 遅刻 in Recoru
- Leaving early → apply for 早退 in Recoru
- Absent all day → apply for 欠勤 in Recoru
- A CaSy attendance manager then approves the application in Recoru

WHAT CASTS DO NOT DO IN RECORU:
- Do NOT clock in/out daily (not required)
- Do NOT enter check-in or check-out times
- Do NOT register planned vacations (that's via Google Form only — CaSy staff handles Recoru for planned leave)

For questions about work hours, overtime, or attendance corrections → contact HQ via inquiry form or 050-3183-8835.

=== SUDDEN SICK DAY / UNEXPECTED ABSENCE (体調不良・突発欠勤) ===
Source: Confluence — ジョリーキャストの休暇申請フロー (updated 2026/04/30)
If a cast cannot attend a service due to sudden illness or emergency on the day:
1. Message the customer via in-app chat IMMEDIATELY — apologize and inform them you cannot come. Inform them they can cancel or have a different cast assigned (rescheduling to another date is NOT possible for JollyCast).
2. Submit the inquiry form RIGHT AFTER contacting the customer:
   - 属性 (Role): キャストとして働いている方
   - 項目 (Category): 2: サービスのキャンセルをしたい
   - If the service start time has already passed: select 5: 開始時刻を過ぎたサービスのキャンセルをしたい
3. Apply for leave in Recoru immediately after submitting the inquiry form.
   - Select the appropriate type: 遅刻 (late), 早退 (early leave), or 欠勤 (absence)
   - Do NOT fill in the Google Form for sudden absences — Recoru only.
4. A CaSy attendance manager will approve the leave in Recoru.
NOTE on salary: 欠勤 (cast-caused absence) = salary deducted per 就業規則第27条. Paid leave (有給) is available after 6 months of employment and can cover absences without deduction.
NOTE on customer-caused cancellation: If a service is cancelled due to CUSTOMER reasons (customer absent, cast forced to exit due to unsanitary conditions, etc.) → this does NOT count as cast 欠勤 and no salary deduction applies.
NOTE on medical certificate: If absent 7+ consecutive days due to illness/injury, submit a 診断書 (medical certificate) to HQ via inquiry form. This is an administrative requirement, not a penalty waiver (the penalty waiver rule is for freelance casts only, not JollyCast employees).
NOTE on child's illness: If your child is suddenly sick, you may be eligible for 子の看護休暇 (nursing leave for sick child, available under the employment rules — ask HQ for details).

=== PLANNED VACATION / SCHEDULED ABSENCE (計画的な休暇) ===
Source: Confluence — ジョリーキャストの休暇申請フロー
For pre-planned days off (confirmed the month before):
1. Message the relevant customers via in-app chat by the 15th of the PREVIOUS month — inform them of the absence and ask if they want to cancel or have a different cast assigned (rescheduling NOT possible).
2. Wait for the Google Form to be distributed by CaSy (distributed by the 10th each month).
3. Submit the Google Form with your planned absence dates between the 10th and 15th of the month.
   - Do NOT use Recoru for planned vacations — CaSy staff handles Recoru registration on your behalf.
Note: Pre-planned vacations = Google Form only (cast side). Sudden absences = Recoru only (cast side).

=== TIPS / GIFTS FROM CUSTOMERS ===
Source: CaSy Zendesk "お客様からチップやお品物をいただいた"
- Cash: NEVER accepted (strictly prohibited)
- Gift cards /商品券 / vouchers: NEVER accepted
- High-value items (branded goods, electronics, etc.): NEVER accepted
- Small consumables on the spot (drinks, snacks — roughly 100-200 yen): MAY be accepted with gratitude
- If unsure: decline politely — "Thank you, but company rules do not allow me to accept this. I appreciate your kindness."
- If offered something you're unsure about: consult HQ at 050-3183-8835

=== APP OPERATIONS (チェックイン・チェックアウト・日報) ===
- For detailed app operation steps (check-in, check-out, daily report, schedule viewing), refer to the training video: https://casy.zendesk.com/hc/ja/articles/31405614157209
- If the app is not working or you cannot check in: call HQ immediately at 050-3183-8835
- If you forgot to check out: contact HQ via support phone or inquiry form to correct it
- If the app crashes and you lose your service record: contact HQ at 050-3183-8835

=== CANCELLATION POLICY (キャンセルポリシー) ===
Source: CaSy Zendesk — お客様からキャンセルをしたいと言われた / キャンセル数の制限について

CUSTOMER-INITIATED CANCELLATION:
- Before 2 days 18:00: Free cancellation. Ask customer to cancel in the app themselves.
- After 2 days 18:00: Full paid cancellation (100% fee). Inform customer and ask them to cancel in the app.
- IMPORTANT: Even if customer told you verbally or via chat they want to cancel, if they have NOT processed it in the app → you MUST still visit as scheduled. If you skip the visit on your own judgment → it is treated as FREE cancellation (you receive no pay).
- At-the-door cancellation (customer cancels when you arrive): Inform them the full cancellation fee applies, then leave. Report via inquiry form (select: 5: 開始時刻を過ぎたサービスのキャンセルをしたい).

CAST-INITIATED CANCELLATION — JollyCast rules (employed cast):
- "直前キャンセル" = cancellation the day before or day of service
- JollyCast casts are EMPLOYEES — disciplinary action follows 就業規則 (employment rules), not monetary penalty deductions
- 3+ 直前キャンセル in 90 days → disciplinary review per 就業規則 (warning → further action)
- NOTE: The ¥1,000-per-cancellation penalty and "診断書 waives penalty" rules apply to FREELANCE (業務委託) casts only — NOT JollyCast employees
- Customer-caused cancellation (customer absent, customer cancelled via app in time, unsanitary exit) = does NOT count toward cast's cancellation record

=== SCHEDULE CHANGES (日程変更) ===
Source: CaSy Zendesk — お客様から日程変更をお願いされたが応じられない

CUSTOMER REQUESTS RESCHEDULE:
- Before 2 days 18:00: Cast cannot accommodate → offer customer 2 options:
  ① Find a different/substitute cast (only possible if no key deposit arrangement)
  ② Cancel the service (free cancellation)
- After 2 days 18:00: Cancellation policy applies. Customer should either proceed as scheduled or cancel (full cancellation fee).
- Cast MAY choose to accommodate the change as a goodwill gesture (optional, cast's decision only).
  WARNING: If cast accepts the change and customer then cancels before 2-day deadline → treated as FREE cancellation (cast receives NO pay).

JOLLYCAST-SPECIFIC NOTE: JollyCast casts CANNOT offer to reschedule to another date — other services are already booked for alternative time slots. Rescheduling is not possible. The service will be cancelled.

CAST requests schedule change: Process through the CaSy app. Contact CaSy support: 050-3183-8835 or inquiry form.

=== MUNICIPAL VOUCHERS (自治体案件・利用券) ===
Source: CaSy Zendesk — 自治体案件とは / 墨田区 / 葛飾区 / 台東区 / 豊島区

WHAT IT IS: Government-subsidized cleaning/cooking services for families with pregnant women or children under 3. The customer holds 利用券 (vouchers) from their local ward to cover part of the service cost.

Covered wards (as of 2026/04/01): 墨田区・葛飾区・台東区・豊島区・国分寺市・中野区・港区・渋谷区・文京区・武蔵野市
- Services: cleaning, cooking, shopping proxy (no house cleaning / organization services)
- Customer must be HOME during service (no key deposit)
- Jobs appear in the app with "自治体案件" label

STANDARD VOUCHER PROCESS (most wards: 墨田区・葛飾区):
1. BEFORE service: Bring the "利用券送付用封筒" (voucher mailing envelope) — sent to you by CaSy when you apply for a municipal job.
2. DURING service: Receive the 利用券 from the customer — one voucher per hour of service.
3. AFTER service: Fill in the back of each voucher (date, time slot, service type, customer name, your name). Put them in the envelope, write your cast name on the back, and mail it. No stamp or address needed. Mail by end of service day or next day at the latest.
Note: Month-end deadline — CaSy must submit to the ward by the 10th of the following month.

WARD-SPECIFIC DIFFERENCES:
- 葛飾区: Some vouchers require the child's name written by the customer — check and ask customer to fill in if missing.
- 台東区 (since 2026/1/5): Two methods are used simultaneously — paper vouchers OR QR code.
  - QR method: Cast shows QR code on their app's check-in screen → customer scans it with their smartphone.
  - If customer cannot scan QR: guide them to tap "こちら" (red text) on their scan screen and manually enter the code 91374493.
  - If customer has no smartphone or cannot enter code at all: proceed with service normally, then report to HQ immediately after — CaSy will notify the ward.
  - If cast's app QR code is not showing: try refreshing the check-in screen. If still missing, report to HQ (050-3183-8835).
- 豊島区: Uses 実施報告票 (service report form) + customer signature instead of individual vouchers. Bring the form and sample (＜記入例＞) to the service; have customer fill in and sign before you leave.

PROBLEM SITUATIONS:
- Voucher expired → Return to customer. Customer pays full regular price. Report via inquiry form (25: 自治体案件について).
- Customer lost their voucher → Customer pays full regular price. Tell them and report via inquiry form.
- Cast forgot to collect voucher → Report via inquiry form immediately. 3 such incidents → first warning, then suspended from municipal jobs.
- Cast lost received voucher → Report via inquiry form immediately (same penalty as above).
- No mailing envelope yet (arrived late) → Mail when envelope arrives. If not received 1 week after service, contact via inquiry form.
- Vouchers not enough to cover full service time → Send only what you received; note the shortfall. HQ will contact customer.
- Service not labeled "自治体案件" but customer hands you voucher → Check expiry. If valid AND municipal coupon is registered in the app → process normally. If not registered → return to customer, charge regular price.

=== CONTACT CHANNELS (連絡手段) ===
Source: HR Policy Manual (人事制度説明スライド) — JollyCast employees use 4 channels:

1. CaSy Cast App (キャストアプリ) — for service-related questions, incidents, customer communication
   - Inquiry form: for cancellations, property damage, trouble reports
   - In-app chat: to contact customers (preferred over emergency phone)
   - Emergency phone: only when lost, customer is absent, or urgent
   - 110 button: for physical threats / criminal acts

2. GTN App — for daily life support in Japan (housing, banking, daily questions)
   - NOT for CaSy work questions

3. Recoru (勤怠管理) — for attendance records ONLY
   - Log check-in/out, apply for 遅刻・早退・欠勤 (sudden absences only; NOT planned vacations)
   - Access: PC or app → Recoru login

4. Slack — for company-wide announcements and internal communication
   - Training-period Q&A was on Google Chat — after training, use Slack instead

NOTE: Google Chat is for the training period only. After training, switch to Slack for company communication.

=== SALARY & BENEFITS (給与・福利厚生) ===
Source: HR Policy Manual (人事制度説明スライド) — for JollyCast employees only

SALARY:
- Monthly gross: ¥211,380 (基本給 ¥198,450 + 地域手当 ¥12,930)
- Paid by bank transfer on the 10th of the following month
- Salary is deducted for absent days (欠勤控除)
- Overtime pay applies for work beyond scheduled hours

PAID LEAVE (有給休暇):
- Eligible after 6 months of continuous employment
- 10 days granted after 6 months; increases each year
- Cannot use paid leave during the first 6 months

BONUSES / INCENTIVES:
- High Drive Bonus: ¥500/3 months for perfect attendance (no absences or late arrivals)
- Jolly DAY: ¥1,200/month gift card (Jollibee chicken — given monthly to all cast)
- Japanese PASS: Pass JLPT N3 → ¥20,000; N2 → ¥20,000; N1 → ¥20,000 (one-time per level)

APRON CHALLENGE (rank system):
- Blue Apron (entry) → Gray Apron → Black Apron
- Promotion based on evaluation stars earned

CONTRACT:
- Initial contract: 3 years
- Maximum total: 5 years (employment ends after 5 years maximum)
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


# ── パスワード認証 ────────────────────────────────────────────

def check_password() -> bool:
    APP_PASSWORD = _secret("APP_PASSWORD", "")
    if not APP_PASSWORD:
        return True  # パスワード未設定なら認証スキップ
    if st.session_state.get("authenticated"):
        return True

    st.set_page_config(page_title="JollyCast Support Bot", page_icon="🧹", layout="centered")
    st.title("🧹 JollyCast Support Bot")
    st.markdown("Please enter the password to access the support bot.")
    pw = st.text_input("Password", type="password", key="pw_input")
    if st.button("Login"):
        if pw == APP_PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password. Please try again.")
    st.stop()

check_password()

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
