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
| Lost / late | Minor delay | #1 Figure out yourself → #2 Ask people nearby → #3 Chat customer w/ screenshot | #4 Call customer → #5 Contact HQ/trainer |
| Severe late / cancel | Start time passed or major delay expected | Contact customer immediately + Call HQ 050-3183-8835 | Submit inquiry form + Recoru 遅刻. NO substitute cast. |
| Incident (danger) | Physical risk | Swipe 110 button in app → HQ calls police | Exit immediately |
| Incident (no danger) | Direct contract solicitation | Continue service | Report via inquiry form |
| Double booking | Other cast is Japanese | Defer to Japanese cast; do not enter | Report via inquiry form after |
| Double booking | Other cast is JollyCast | Ask customer: proceed with 2 casts or 1? If 1: later hire date cast stays | Report via inquiry form; HQ checks booking history |
"""

KNOWLEDGE = """
=== GTN (GLOBAL TRUST NETWORKS) ===
GTN supports JollyCast cast members with non-work daily life matters in Japan.
For questions about banking, money transfers, SIM cards, housing, resident registration,
or other personal life admin — direct the cast to GTN, not HQ.
Cast members can contact GTN via chat or phone through the GTN app (separate from the CaSy/JollyCast app).
Example response: "For this kind of question, please contact GTN through the GTN app (chat or phone)."
Do NOT try to answer banking procedures, housing contracts, or admin paperwork yourself.
GTN is the correct resource for these topics — HQ is for CaSy service issues only.
⚠️ GTN does NOT handle navigation or getting-lost issues during service. For those, use the 5-step GETTING LOST procedure.

=== ABOUT JOLLYCAST ===
JollyCast (ジョリーキャスト) cast members are EMPLOYEES of CaSy (株式会社CaSy), not freelance contractors.
CaSy operates the cleaning/cooking service platform. JollyCast is CaSy's employed cast program.
CaSy Support number: 050-3183-8835 (available 9:00-18:00, weekdays and weekends/holidays)
This support number is correct and appropriate for JollyCast casts to use.

HQ CONTACT — 2 PATTERNS (CRITICAL RULE):
1. CALL 050-3183-8835 — EMERGENCY ONLY (4 situations):
   a) Safety or hygiene danger during service (injury risk, fire, gas leak, etc.)
   b) Property damage that seriously affects the customer's daily life (e.g., broken essential appliance)
   c) Serious on-site trouble with the customer during service
   d) Any situation NOT in the manual that involves risk to service provision OR potential criminal risk
      (e.g., unauthorized entry, legal ambiguity, situations where proceeding could expose cast to legal liability)
      → When in doubt about legality or safety: CALL HQ immediately. Do not proceed on your own judgment.
2. INQUIRY FORM — ALL OTHER SITUATIONS:
   App issues, QR/voucher problems, schedule questions, reporting after the fact, forgetting a procedure, etc.
   Do NOT call HQ for non-emergency issues — it overloads the phone line.
   To submit: Cast App → Inquiry Form (問い合わせフォーム)

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
Source: Training Booklet Day22 + Property Damage Sheet (PDS)

⚠️ DO NOT DECIDE URGENCY YOURSELF — CONFIRM WITH THE CUSTOMER:
Show the damaged item to the customer and ask whether it disrupts their daily life.
Use the PDS (Property Damage Sheet / 指差しシート) to communicate.
- Urgent = damage that disrupts daily life (broken toilet, water leak, essential appliance, etc.)
- Non-urgent = does not disrupt daily life (scratched floor, broken glass, minor item, etc.)

9 STEPS — NON-URGENT:
1. Inform the customer immediately with a sincere apology
2. Show the customer the damaged property
3. Ask the customer for permission to take a photo ("写真を撮らせてください" — PDS)
4. Take a photo (include maker name and model number)
5. Ask the customer if they want compensation — use PDS: A「弁償してください」/ B「弁償はいりません」
6. Clean up the damage
7. Continue service until the scheduled end time
8. Apologize again before leaving
9. After service: report via inquiry form + upload photo + write daily report
   - 属性: キャストとして働いている方 / 項目: 9: トラブルが起きた / トラブルの内容: 4: 物損
   - Include: service ID, date/time, customer name, description, maker/model number, photo

9 STEPS — URGENT:
1. Inform the customer immediately with a sincere apology
2. Show the customer the damaged property
3. Ask the customer for permission to take a photo ("写真を撮らせてください" — PDS)
4. Take a photo (include maker name and model number)
5. Call HQ at 📞 050-3183-8835 immediately and explain the situation
6. Clean up the damage
7. Continue service until the scheduled end time
8. Apologize again before leaving
9. After service: report via inquiry form + upload photo + write daily report

NOTE: Even if the customer waives compensation (「弁償はいりません」), ALWAYS report to HQ via inquiry form.
NOTE: Do NOT offer to pay the customer directly. Do NOT say "our insurance will cover it" — let HQ handle.
NOTE: For housing fixtures (water pipes, wall damage): customer contacts repair company or building management themselves.
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
SEVERE conditions — EXIT IMMEDIATELY without asking customer to fix it first:
  - Pest infestation: cockroaches, rats (any visible infestation)
  - Feces/urine smell or extreme unsanitary conditions
  - Extreme clutter blocking safe movement
  - Cast feeling physically ill due to the environment
  - Broken glass or physical hazards on the floor
  - Drunken customer (posing a risk)
  - Aggressive unleashed pet

MINOR conditions — you MAY ask for a fix before deciding to exit (see SPECIAL CASES below):
  - Non-aggressive pet running freely
  - Outdoor summer heat (can switch to indoor tasks)
  - Child alone who is calm and not dangerous

CRITICAL RULE: For SEVERE Type B conditions, do NOT ask the customer to clean up or fix the issue before you exit. Exit directly.
Do NOT add a "Step 1: ask customer to improve the situation" for pest infestations, feces smell, broken glass, physical illness, or other severe hazards. These are immediate exit situations.

EXIT PROCEDURE for Type B:
1. Tell the customer calmly: "Due to safety and hygiene concerns, I am unable to provide the service today. I sincerely apologize. CaSy HQ will contact you shortly."
   (「安全面・衛生面において懸念がございますためサービスのご提供が難しいです。本日は失礼いたします。追って本部よりご連絡させていただきます。」)
   - You do NOT need HQ approval before exiting — you can decide to leave yourself
   - If it is difficult to explain, you may exit without explanation — your safety comes first
2. After exiting: submit the inquiry form (9: トラブルが起きた) as soon as possible. Phone HQ at 050-3183-8835 if urgent.

SPECIAL CASES (where asking for a fix first makes sense before exiting):
  - Pet running freely but not aggressive → politely ask: "Our policy requires pets in a cage or separate room. Could you please arrange that?" Exit only if refused.
  - Outdoor work in summer heat → do indoor tasks instead; no need to exit entirely
  - Child home alone, behaving calmly → service can proceed normally
  - Child home alone and dangerous (running into hazards, clinging) → chat parent and exit

IMPORTANT: Customer-caused exit (unsanitary/unsafe conditions) does NOT count as cast 欠勤. No Recoru application or salary deduction applies in these cases.

=== COOKING SERVICE — PACKAGE PLAN OVERVIEW & RULES ===
Source: CaSy Zendesk — 【重要】お料理サービスに3つのパッケージプランをつくりました

JollyCast provides ONLY the package-plan cooking service (not the free-plan / フリープラン).

WHAT THE PACKAGE PLAN IS:
- Fixed menu of 8 dishes: 主菜3品 (main dishes) + 副菜4品 (side dishes) + 汁もの1品 (soup) = 8 total
- 3 plan options: Package A, B, or C (each has its own set of 8 dishes)
- Ingredients and seasonings are prepared by the customer, NOT the cast
- Serves 4 people (4名分)
- Recipes are fixed by CaSy instructors — casts prepare in advance; no menu discussion with customer needed

REQUIREMENTS:
- Customer must have AT LEAST 2 gas/IH burners (コンロ2口以上). If only 1 burner: service cannot be provided.
- Customer must be HOME during service (no key deposit option for package plan).

OPTIONS NOT AVAILABLE WITH PACKAGE PLAN:
- 買物代行 (shopping proxy) — NOT available
- 鍵預かりオプション (key deposit) — NOT available

⛔ STRICT RULES — NEVER deviate from the recipe:
Menu changes and flavor adjustments are PROHIBITED. This is treated as a "serious incident."
- Disciplinary: 3 violations in 3 months → 厳重注意 + suspended from package plan
- 4th violation or more → banned from ALL cooking services (including package plan)

HANDLING COMMON SITUATIONS:

Q: Customer asks to change flavor ("make it less salty", "make it sweeter")
→ Politely decline: "I'm sorry, the seasoning is fixed for this package to ensure consistent quality. I'm unable to adjust the flavor."

Q: Customer asks to change a specific dish or substitute an ingredient
→ Decline: "This package provides a set of 8 dishes with a fixed menu. I'm unable to make changes to the ingredients or dishes."

Q: A required ingredient is missing when you arrive
→ Do NOT substitute. Skip that dish.
Say: "I'm sorry, the required ingredient is missing, so I will not be able to prepare this dish today."

Q: Basic seasonings (e.g., soy sauce, sugar) are insufficient
→ Complete all cooking steps up to the point of seasoning. Ask customer to finish the seasoning.
Say: "I'm sorry, the seasoning is insufficient. I will prepare everything up to this point, and could you please add the final seasoning yourself?"

Q: You finish all 8 dishes before the scheduled end time
→ Exit immediately after completing the dishes. Do NOT offer additional cooking or cleaning.
Say: "I have completed all 8 dishes as promised. Thank you — I will be leaving now."

Q: Customer asks you to do extra cooking or cleaning since "you have time left"
→ Politely decline: "I'm sorry, this package plan is specifically for preparing the 8 set dishes. I'm not able to provide additional cooking or cleaning under this plan."

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

=== KEY BOX (キーボックス) ACCESS ===
Some customers use a physical key box (combination lock box) outside their home instead of the official 鍵預かりオプション.
- Before service: the customer should have provided the combination/code in advance via in-app chat.
- If you cannot open the box or don't have the code: contact the customer via emergency phone or in-app chat immediately.
- After service: return the key to the box and make sure it is locked.
- If any issue (lost key, broken box, etc.): report via inquiry form after service.
- Note: CaSy does not officially recommend key handover outside of 鍵預かりオプション — if the customer insists on non-standard methods, inform HQ via inquiry form.

=== CUSTOMER ABSENT (お客様不在) ===
⛔ Do NOT enter the building by following someone else in (tailgating) — this is considered TRESPASSING.

PROCEDURE (do these steps IN ORDER during the 30-minute wait):
1. Ring the doorbell / knock when you arrive
2. Send a chat message via the in-app chat
3. Call the customer using the emergency phone (App MENU → Schedule → tap service time → Customer Info → Phone → "Show phone number" → "Make call")
4. Wait up to 30 minutes total from the scheduled start time
5. If still no response after 30 minutes AND you have tried both chat AND phone call → leave

NOTE: If a cast asks "I have been waiting 30 minutes with no response — what do I do?",
assume steps 1–3 may not have been completed yet. Remind them to try BOTH phone call AND
in-app chat before leaving, even if the 30-minute mark has been reached.
  - 属性: キャストとして働いている方 / 項目: 9: トラブルが起きた
- This is a customer-caused cancellation — does NOT count as 欠勤, no salary deduction applies
- Do NOT call HQ (050-3183-8835) — customer absent is NOT an emergency, use inquiry form

WAITING LOCATION:
- Wait somewhere close enough to reach the customer's home quickly.
- If weather conditions (heavy rain, extreme heat, etc.) make waiting outside dangerous to your health,
  you MAY move to a nearby covered area (e.g., a convenience store, shade) to wait.

IF THERE IS NO SAFE PLACE TO WAIT DUE TO WEATHER:
- Do NOT push through and wait in dangerous conditions. Your safety comes first.
- Contact the customer via in-app chat AND emergency phone, explaining you cannot wait due to weather.
- You may leave and cancel today's service.
- This is treated as a FREE cancellation (キャストの待機不可によるキャンセル — no cancellation fee for the customer).
- After leaving: report to HQ via inquiry form (属性: キャストとして働いている方 / 項目: 9: トラブルが起きた / 1: お客様が不在).

=== ENTRY VIA NEIGHBOR OR THIRD PARTY (隣人・第三者による入室) ===
This is an extremely unusual situation. Entering a customer's home via a neighbor or third party
WITHOUT the customer's explicit permission risks 住居侵入罪 (unlawful entry — a criminal offence).

⛔ DEFAULT: Do NOT enter.
- A neighbor saying "it's fine" is NOT sufficient. Only the customer can authorize entry.

✅ EXCEPTION — You MAY enter ONLY IF:
- You have explicit WRITTEN confirmation from the customer via in-app chat (text message) authorizing you to enter.
- In that case, proceed with normal service.
- HOWEVER — before entering, clearly inform the customer in writing:
  "As this is not the 鍵預かりオプション arrangement, I am unable to take responsibility for locking
   your door when I leave."
  (Manual states cast cannot be held responsible for locking/security risks in this situation.)

❓ IF UNCERTAIN OR UNABLE TO REACH CUSTOMER:
→ Call HQ immediately at 📞 050-3183-8835. Do not enter on your own judgment.

=== OUT-OF-SCOPE CUSTOMER REQUESTS ===
If a customer asks you to do something outside your service scope (e.g., teach cleaning techniques, give personal advice, stay longer without an extension booking, etc.):
- Politely decline and continue your normal scheduled service
- No need to contact HQ — this is not an emergency situation
- Example: "I'm here to clean for you today, so let me focus on providing the best service!"
- If the customer becomes persistent or aggressive: note it in your daily report and submit an inquiry form after service

=== AFTER SERVICE / BETWEEN SERVICES ===

AFTER YOUR LAST SERVICE OF THE DAY:
- Go home directly. NEVER go to any CaSy office unless HQ specifically instructs you to.
- There is NO requirement to report to an office or perform any task after your last service.
- There is NO language study (Duolingo or otherwise) required during or after work hours.

IF YOU HAVE NO AFTERNOON SERVICES (or schedule is cancelled):
- Basically go to the CaSy office. Do NOT go home unless HQ specifically tells you to.
- If unsure what to do: contact HQ via inquiry form or 050-3183-8835.

IF A SERVICE ENDS EARLIER THAN SCHEDULED:
- You may leave once the service is complete. Do not wait at the customer's home until the original end time.
- Do not wait at any office for the remaining time.

BETWEEN TWO SERVICES (gap time):
- You may use the gap time freely (rest, eat, use a café, etc.) MINUS travel time to the next service.
- Labor law (労働基準法) requires AT LEAST 45 minutes of break for a 6-hour shift — this is a MANDATORY MINIMUM, not a maximum. You may take a longer break if the gap allows.
- Example: 90-min gap, 30-min travel → 60 min free time; you must take at least 45 min as break.
- NEVER go to a CaSy office between services unless HQ specifically instructs you to.
- NO language study or specific activity is required during break time.

OTHER RULES:
- Cannot extend service time: JollyCast company rules do not allow on-site time extensions. If a customer asks to stay longer, politely decline: "I'm sorry, company rules do not allow me to extend the service on-site. If you'd like more time, please book additional time through the CaSy app." Do NOT use excuses like "I have another appointment" — state the company rule directly.
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

=== DAILY REPORT CORRECTION (日報修正) ===
- Cast CAN edit a submitted daily report directly in the cast app.
- How: open the report → tap "内容を編集する" (Edit content) button.
- Deadline: within 24 hours of submission.
- If outside the 24-hour window: contact HQ via inquiry form.

=== SEVERE LATENESS / CANCELLATION DUE TO BEING VERY LATE (大幅遅刻・遅刻によるキャンセル) ===

If the service start time has already passed OR significant lateness is expected:

1. Contact the customer IMMEDIATELY via in-app chat — apologize sincerely and inform them of the situation.
2. Call HQ at 📞 050-3183-8835 IMMEDIATELY after contacting the customer.
   (This is an urgent situation requiring HQ coordination — do not use inquiry form alone.)
3. Submit the inquiry form after calling HQ:
   - 属性: キャストとして働いている方
   - 項目: 5: 開始時刻を過ぎたサービスのキャンセルをしたい (if start time has passed)
   - Or: 2: サービスのキャンセルをしたい (if not yet past start time)
4. Apply for 遅刻 in Recoru.

⛔ Do NOT suggest "finding a substitute cast" — this is not possible for JollyCast employed casts.
   (Unlike freelance CaSy casts, JollyCast casts are on company-managed shifts. No substitution available.)

NOTE: Cast-caused cancellation = 欠勤, salary deduction applies per 就業規則第27条.

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
- Before 2 days 18:00 (前々日18:00まで): FREE cancellation. Ask customer to cancel in the app themselves.
- At or after 2 days 18:00 (前々日18:00以降): FULL paid cancellation (100% fee charged to customer). Inform customer and ask them to cancel in the app.

TIMING RULE — HOW TO COUNT "2 days before":
  "2 days before" = 前々日 = the day-before-yesterday relative to the service date.
  Example: Service is on Wednesday.
    → Monday 17:59 = BEFORE the deadline → FREE cancellation
    → Monday 18:00 = AT the deadline → PAID (full amount)
    → Monday 18:05 = AFTER the deadline → PAID (full amount)
  Another example: If customer contacts you 2 days before at 17:50 → that is BEFORE 18:00 → FREE cancellation.

- IMPORTANT: Even if customer told you verbally or via chat they want to cancel, if they have NOT processed it in the app → you MUST still visit as scheduled. If you skip the visit on your own judgment → it is treated as FREE cancellation (you receive no pay).
- At-the-door cancellation (customer cancels when you arrive): Inform them the full cancellation fee applies, then leave. Report via inquiry form (select: 5: 開始時刻を過ぎたサービスのキャンセルをしたい).

CAST-INITIATED CANCELLATION — JollyCast rules (employed cast):
- "直前キャンセル" = cancellation the day before or day of service
- JollyCast casts are EMPLOYEES — disciplinary action follows 就業規則 (employment rules), not monetary penalty deductions
- 3+ 直前キャンセル in 90 days → disciplinary review per 就業規則 (warning → further action)
- NOTE: The ¥1,000-per-cancellation penalty and "診断書 waives penalty" rules apply to FREELANCE (業務委託) casts only — NOT JollyCast employees
- Customer-caused cancellation (customer absent, customer cancelled via app in time, unsanitary exit) = does NOT count toward cast's cancellation record

=== DOUBLE BOOKING (ダブルブッキング) ===
Source: CaSy Zendesk manual + Trouble Flow (JollyCast-specific note added)

Situation: You arrive at the customer's home and another cast is already there.
This happens when a customer made two separate bookings (different service IDs) at the same time.

BILLING RULE (most important):
- If HQ confirms the customer made 2 bookings by their own operation → 2-cast fee applies NO MATTER WHAT.
- This means even if only 1 cast ends up doing the work, the customer is still charged for 2 casts.
- HQ handles all billing — do not discuss fees directly with the customer beyond informing them that 2 bookings were made.

CASE A — The other cast is Japanese (non-JollyCast cast):
★ JollyCast-specific rule: defer to the Japanese cast.
- Let the Japanese cast take the lead on customer interaction.
- Inform the customer: "Two casts have arrived. Since both bookings were made by you, a 2-cast fee will apply regardless of how many casts work today."
- Do not argue with the other cast or the customer.
- After the situation resolves: report to HQ via inquiry form.

CASE B — The other cast is also a JollyCast cast:
(Follow standard CaSy Zendesk procedure)
1. Inform the customer that 2 casts have arrived and that a 2-cast fee applies:
   "Two casts have arrived. Since 2 bookings were made, a 2-cast fee will apply regardless of how many casts work. Would you like both of us to work, or just one?"
2. If customer wants 2 casts: both perform the service together.
3. If customer wants only 1 cast:
   - Regular (定期) booking vs Spot (スポット): the regular (定期) cast stays.
   - Both regular (定期): the cast with the later hire date stays; the earlier hire leaves.
   - Both spot: the cast with the later hire date stays.
   - Remind the customer again: the 2-cast fee still applies even with only 1 cast working.
4. After service: report to HQ via inquiry form. HQ checks booking history and handles billing.

IMPORTANT: In ALL cases, clearly inform the customer upfront that a 2-cast fee will apply if they made 2 bookings. This prevents disputes later. Do not promise a refund or fee reduction — that is HQ's decision.

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

PERMANENT DAY/TIME CHANGE FOR RECURRING SERVICE (定期サービスの曜日・時間の永続変更):
JollyCast casts are employed staff — the company manages their daily shift schedule.
Therefore, it is NOT possible to move a recurring service to a different day or time slot.
(This differs from freelance CaSy casts who can adjust their own schedules.)

If a customer wants to permanently change the day/time of their recurring service:
→ They must cancel the entire recurring service (定期全体キャンセル) and re-book a new request for their preferred day/time.

CUSTOMER REQUESTS A DIFFERENT CAST MEMBER (担当キャストの変更):
It is not possible to simply swap cast members within an existing recurring service.
If a customer wants a different cast member:
→ They must cancel the entire recurring service (定期全体キャンセル) and re-book a new request (a different cast will be assigned).

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
3. AFTER service:
   - THE CAST fills in the back of each voucher: write the date, time slot (e.g., 10:00-11:00 / 11:00-12:00 / 12:00-13:00), service type, customer name, and your own (cast) name.
   - NOTE: It is the CAST who writes on the back of the voucher, not the customer.
   - Put them in the mailing envelope, write your cast name on the back of the envelope, and drop it in a mailbox. No stamp or address needed.
   - Mail by end of service day or next day at the latest.
Note: Month-end deadline — CaSy must submit to the ward by the 10th of the following month.

WARD-SPECIFIC DIFFERENCES:
- 葛飾区: Some vouchers require the child's name — ask customer to fill in the child's name if missing. (Only the child's name is filled by the customer; everything else is filled by the cast.)
- 台東区 (since 2026/1/5): QR code method is available IN ADDITION TO paper vouchers. QR questions (Q59-Q64 type) refer to this 台東区 context.
  - QR method: Cast shows QR code on their app's check-in screen → customer scans it with their smartphone.
  - If customer cannot scan QR: guide them to tap "こちら" (red text) on their scan screen and manually enter the code 91374493.
  - If customer has no smartphone or cannot enter the manual code at all: proceed with service normally, then report via inquiry form (25: 自治体案件について) after service — CaSy will notify the ward.
  - If cast forgot to scan QR at check-in: QR scan is still possible until checkout is complete — use Cast App "QRコード提示" to have the customer scan. Only if already checked out and exited: report via inquiry form (25: 自治体案件について) after service.
  - If cast's app QR code is not showing: try refreshing the check-in screen. If still missing, proceed with service normally and report via inquiry form (25: 自治体案件について) after service.
  - If QR scan fails (error shown): try the manual code entry first; if that also fails, report via inquiry form (25: 自治体案件について).
  - If cast accidentally scanned QR themselves instead of customer: report via inquiry form (25: 自治体案件について).
  - If customer accidentally scanned twice: report via inquiry form (25: 自治体案件について).
- 豊島区: Uses 実施報告票 (service report form) + customer signature instead of individual vouchers. Bring the form and sample (＜記入例＞) to the service; have customer fill in and sign before you leave.
- 武蔵野市: NO paper vouchers — do NOT accept or process any physical vouchers from 武蔵野市 customers. Service itself is completely normal (nothing special before or during service).
  AFTER service: At the start of the following month, CaSy will forward an email from 武蔵野市 containing a 実施報告書 (service report). Respond promptly by signing electronically via クラウドサイン (cloud signature). Failing to sign means the municipal subsidy will not be applied and the customer will be charged full price.
  If a customer hands you a physical voucher in 武蔵野市: politely explain the system is electronic only, return the voucher, and continue service normally.
- 中野区・港区・渋谷区・文京区・国分寺市: Follow the same standard voucher process as 墨田区/葛飾区 unless otherwise specified.

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
   - Inquiry form: DEFAULT for all non-emergency reports (QR/voucher issues, app problems, schedule questions, post-incident reports, etc.)
   - In-app chat: to contact customers (preferred over emergency phone)
   - Emergency phone (050-3183-8835): ONLY for 3 emergencies — safety/hygiene danger, serious property damage affecting daily life, serious on-site trouble with customer
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

=== CLEANING SERVICE — CUSTOMER DISSATISFACTION (仕上がり不満) ===
Source: CaSy Zendesk — 仕上がりにご満足いただけなかった時

If a customer is not satisfied with your cleaning result:
1. Apologize sincerely and wholeheartedly — do not argue or make excuses.
2. Ask for honest feedback: "What went well? What could I do better next time?"
   - At end-of-service walkthrough: ask directly what they felt was good/not good.
   - Let them know they can also note it in the app evaluation form under "気になった点・改善要望等"
     (their written comments are NOT shown directly to you — they are reviewed by an instructor who may follow up with you separately)
3. If the customer is very angry or you cannot handle the situation: contact HQ 📞 050-3183-8835

NOTE: A dissatisfied customer does NOT automatically entitle them to a refund. If they ask for a refund, tell them HQ will contact them — do not promise any refund yourself.

=== MOVING SUPPORT (引越しサポート / 荷造り・荷ほどきサポート) ===
Source: CaSy Zendesk — お引越し時の「荷造り、荷ほどきサポート」について

If a customer asks you to help with packing (荷造り) or unpacking (荷ほどき) for a move:
- This is ACCEPTED by CaSy. You may help with simple items like clothes, dishes, books, small items.
- CaSy does NOT provide specialist training for this — do your best within your capability.
- Always discuss scope with the customer at the start of service.

IMPORTANT RESTRICTIONS — the following are PROHIBITED and you must NOT do them:
- Heavy lifting: sofas, appliances, or anything you cannot carry alone
- High-location work: standing on a table or anything higher than knee height
- Handling high-value/fragile specialized items (expensive furniture, delicate antiques)
NOTE: CaSy is NOT responsible for breakages during packing. Customers are informed of this in advance.

Also confirm with customer:
- All packing materials (cardboard boxes, tape, bubble wrap, newspaper) must be prepared by the customer.
- Trash removal is not included.
- If volume is large and cannot be completed in one session, recommend the customer book multiple sessions.

PACKING TIPS (荷造り):
- Start from rooms farthest from the entrance.
- Label boxes with contents and "すぐに使う物" (immediately needed) on the outside.
- Books: pack in small boxes (20–30 paperbacks or 15–20 magazines per box — heavier than they look).
- Dishes: wrap each piece individually in newspaper; never stack unwrapped dishes.
- Clothes: pack in large boxes; pack off-season items first.

UNPACKING TIPS (荷ほどき):
- Unpack immediately needed items first: futon, curtains, toiletries, toilet paper, clothes.
- Open one box at a time; flatten empty boxes immediately.

=== GETTING LOST / CANNOT FIND ADDRESS (道に迷った時) ===
Source: Training Booklet Day4 — Navigate with Google Map & Ask for Help

⚠️ THIS APPLIES TO ALL NAVIGATION ISSUES DURING SERVICE — including "Google Maps is wrong/taking me the wrong way."
Do NOT direct to GTN for service navigation problems. GTN is for daily life matters only.

JollyCast casts are not fluent in Japanese and are unfamiliar with local geography.
Contacting the customer first would cause them inconvenience and is unlikely to help.
Follow the 5 STEPS BELOW IN ORDER:

STEP 1 — Figure it out yourself
- Re-check Google Maps carefully: correct start point, destination, and travel method
- If the Google Maps arrow moves in the opposite direction → you are going the wrong way; turn around
- For large stations (Shinjuku, Shibuya): allow at least 40 minutes extra; exit the station building for better GPS signal

STEP 2 — Ask people nearby (DO THIS BEFORE contacting the customer)
Use these Japanese phrases:
- "Sumimasen. Michi ni mayoimashita. [ADDRESS] ni ikitai desu. Oshiete kudasai."
  すみません。みちにまよいました。〇〇に行きたいです。おしえてください。
  "Excuse me. I'm lost. I want to go to [ADDRESS]. Please tell me how."
- If they don't speak English: show them the address on your phone screen
- "Nihongo ga wakaranai node, chatto de oshiete kudasai."
  日本語がわからないので、チャットでおしえてください。
  "I don't understand Japanese, so please tell me via chat."

STEP 3 — Send a chat message to the customer (with screenshot of your current location)
- Take a screenshot of your Google Maps location
- Send via in-app chat: "I'm sorry, I seem to be lost. I am at [screenshot location]. I am on my way."
- Do NOT call yet — chat first to minimize inconvenience

STEP 4 — Call the customer using the emergency phone in the app
- Only if chat does not resolve it
- App MENU → Schedule → tap service time → Customer Info → Phone → "Show phone number" → "Make call"

STEP 5 — Contact CaSy trainer / HQ
- If still stuck after steps 1–4: contact HQ via inquiry form or trainer directly

VARIATION — CANNOT FIND THE ROOM INSIDE THE BUILDING (部屋番号がわからない・ドアに番号がない):
Source: Training Booklet Day9 — Arrive at the Correct Building
Follow the same 4-step order — ask people in the building BEFORE contacting the customer:

STEP 1 — Confirm by yourself
- Re-check the app booking: apartment name, floor, room number
- Check the intercom panel or mailboxes near the entrance — room numbers / names are usually listed
- Confirm you are in the correct building (large complexes may have multiple buildings: 1号棟, 2号棟, etc.)

STEP 2 — Ask the building receptionist or people nearby
  "Sumimasen, tasukete kudasai. [ROOM#]-kai ni ikitai desu. Dono erebeetaa wo tsukaeba ii desu ka?"
  すみません、たすけてください。＃かいに行きたいです。どのエレベーターを、つかえばいいですか？
  "Excuse me, please help me. I want to go to floor #. Which elevator should I use?"

STEP 3 — Send a chat message to the customer
  Ask via in-app chat: "I have arrived at the building. Could you tell me which floor and room number?"
  (Chat before calling — less disruptive to the customer)

STEP 4 — Call the customer using the emergency phone in the app
- Only if chat does not resolve it

=== SERVICE ADDRESS MISMATCH (住所が違う時) ===
Source: CaSy Zendesk — サービスを実施する住所が違う時

If a customer asks you to perform the service at a DIFFERENT address than what is shown in your app:
- You CANNOT do so. Politely explain that you can only work at the registered service address.
- Even if it is in the same building (different room) or very nearby — you cannot move to a different location.
- Reason: insurance/liability coverage, 110 emergency button accuracy, and legal risk (住居侵入).

Also: if a customer's address is missing the apartment name or room number:
- Ask the customer to update their address in the app BEFORE 前々日18:00 (2 days before, 6 PM).

TIMING AND ACTION:
- Before 前々日18:00: Cancel the current service and ask the customer to re-book with the correct address.
- After 前々日18:00: A paid cancellation applies. Inform the customer. Cast WILL be paid.

=== NOT APPLICABLE TO JOLLYCAST (フリープラン・業務委託向け機能) ===
JollyCast cast members are EMPLOYEES (雇用). The following features/services exist in CaSy but do NOT apply to JollyCast:
- 報酬前払いサービス (advance salary payment) — for freelance cast only
- 買物代行 (shopping proxy option) — for free-plan cooking service only; JollyCast provides package-plan cooking only
- 特別報酬制度 (special incentive bonus system) — for freelance cast only
- 確定申告・インボイス (tax filing, invoice system) — for freelance (業務委託) cast only; JollyCast are employees and CaSy handles withholding
- キャストセッション / CACACAコミュニティ — freelance cast community platform, not used by JollyCast

If a cast member asks about any of the above:
Respond: "This feature is for freelance CaSy casts and does not apply to JollyCast employees. For questions about your employment terms or benefits, please contact HQ via inquiry form or 📞 050-3183-8835."
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

            - After your **last service**: go home directly. No need to go to any office.
            - Between services: free time (rest, eat, etc.) minus travel time to next service.
            - Labor law requires **at least 45 minutes break** for a 6-hour shift.
            - If unsure what to do: contact HQ at **050-3183-8835**

            📞 CaSy Support: **050-3183-8835**

            *Source: JollyCast operating rules*
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


def generate_claude_response(question: str):
    """Streams response text chunks. Uses KNOWLEDGE BASE + TROUBLE FLOW only (no Zendesk)."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        system_text = f"""You are a support assistant for JollyCast (ジョリーキャスト) cast members working in Japan.

RESPONSE RULES:

【TYPE A — Work procedure questions】
Anything related to CaSy/JollyCast operations: cancellations, vouchers, app usage, incidents, schedules, Recoru, payments, customer trouble, etc.
1. Answer ONLY from the KNOWLEDGE BASE and TROUBLE FLOW provided below.
2. Do NOT use general knowledge or invent procedures not written in these materials.
3. If not covered in the materials: respond with "This situation is not covered in my manual. Please report via the inquiry form or contact CaSy HQ: 📞 050-3183-8835"

【TYPE B — Japan daily life / common sense questions】
Navigation, train directions, room/floor numbering, Japanese customs, addresses, general etiquette — things a foreign worker in Japan might not know.
4. You MAY use your general knowledge to answer helpfully and concisely.
5. End your answer with: *(General knowledge — not CaSy policy)*

【ALL questions】
6. Always respond in English. Be concise — cast members are often mid-service.
7. Number steps clearly. For urgent work situations (safety, serious damage, on-site emergency), include 📞 050-3183-8835.
8. When materials conflict, prioritize: KNOWLEDGE BASE > TROUBLE FLOW.

=== KNOWLEDGE BASE (JollyCast-specific curated rules) ===
{KNOWLEDGE}

=== TROUBLE FLOW ===
{TROUBLE_FLOW}"""

        with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=800,
            system=[{
                "type": "text",
                "text": system_text,
                "cache_control": {"type": "ephemeral"}
            }],
            messages=[{"role": "user", "content": question}]
        ) as stream:
            for text in stream.text_stream:
                yield text

    except Exception as e:
        yield f"Error connecting to Claude API: {e}\n\nPlease contact CaSy Support: 📞 **050-3183-8835**"


def send_slack_log(question: str, response: str):
    """質問とBot回答をSlack Incoming Webhookに投稿する。SLACK_WEBHOOK_URL未設定時はスキップ。"""
    import urllib.request as _req
    import json as _json
    import datetime

    webhook_url = _secret("SLACK_WEBHOOK_URL", "")
    if not webhook_url:
        return

    now = datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=9))
    ).strftime("%Y-%m-%d %H:%M JST")

    # Slackの文字数制限（3000文字）に合わせてトリミング
    q_text = question[:800]
    r_text = response[:2000]

    payload = {
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "📝 JollyCast Bot — Question Log", "emoji": True}
            },
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": f"🕐 {now}"}]
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Question:*\n{q_text}"}
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Bot Answer:*\n{r_text}"}
            },
            {"type": "divider"}
        ]
    }
    try:
        data = _json.dumps(payload).encode("utf-8")
        req = _req.Request(
            webhook_url, data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        _req.urlopen(req, timeout=5)
    except Exception:
        pass  # ログ失敗はサイレントに無視（本体機能に影響させない）


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
    st.markdown("📚 **Knowledge base**: JollyCast KNOWLEDGE + Trouble Flow")
    st.markdown("**Sources:**\n- JollyCast curated KNOWLEDGE BASE\n- Trouble flow guide")
    st.divider()
    st.markdown("🆘 **Emergency**: CaSy Support")
    st.markdown("📞 `050-3183-8835`")

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

    with st.chat_message("assistant"):
        if MODE == "mock":
            relevant = search_articles(prompt, articles, top_k=3)
            response = generate_mock_response(prompt, relevant)
            st.markdown(response)
        else:
            # Streaming: show text as it generates
            placeholder = st.empty()
            chunks = []
            for chunk in generate_claude_response(prompt):
                chunks.append(chunk)
                placeholder.markdown("".join(chunks) + "▌")
            response = "".join(chunks)
            placeholder.markdown(response)

            with st.expander("📖 Source", expanded=False):
                st.markdown("Based on JollyCast KNOWLEDGE BASE + Trouble Flow")

            # Slackにログ送信（失敗しても無視）
            send_slack_log(prompt, response)

    st.session_state.messages.append({"role": "assistant", "content": response})
