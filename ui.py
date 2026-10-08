 """مكونات الواجهة: CSS + قطع HTML (كلها بتعمل escape للنصوص عشان الأمان)"""
from html import escape as esc

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
html, body, .stApp, .stApp * {font-family: 'Cairo', sans-serif;}
[data-testid="stIconMaterial"], .material-symbols-rounded {font-family: "Material Symbols Rounded" !important;}
.stApp {background: radial-gradient(900px 500px at 90% -5%, rgba(99,102,241,.35), transparent 60%),
        radial-gradient(800px 500px at 0% 0%, rgba(20,184,166,.30), transparent 60%), #0a0f1f; color: #e8ecf8;}
.stApp p, .stApp li, .stApp label, .stApp span, .stApp h1, .stApp h2, .stApp h3, .stApp div[data-testid="stMarkdownContainer"] {color: #e8ecf8;}
[data-testid="stHeader"] {background: transparent;}
#MainMenu, footer {visibility: hidden;}
.block-container {max-width: 980px; padding-top: 1.2rem; direction: rtl; text-align: right;}
[data-testid="stSidebar"] {background: #0d1430; direction: rtl;}
.hero {padding: 26px 28px; border-radius: 22px; margin-bottom: 18px; position: relative; overflow: hidden;
       background: linear-gradient(135deg, rgba(34,211,238,.16), rgba(99,102,241,.22)); border: 1px solid rgba(255,255,255,.14);}
.hero h1 {margin: 0; font-size: 34px; font-weight: 800; background: linear-gradient(90deg,#67e8f9,#a5b4fc);
          -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
.hero p {margin: 6px 0 12px; color: #b9c2e0 !important; font-size: 16px;}
.shield {font-size: 46px; float: left; margin-right: 12px; filter: drop-shadow(0 4px 14px rgba(34,211,238,.5));}
.card {background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.11); border-radius: 18px;
       padding: 16px 20px; margin-bottom: 14px; backdrop-filter: blur(8px);}
.card h4 {margin: 0 0 10px; font-size: 17px; color: #fff;}
.chip {display: inline-block; padding: 4px 12px; border-radius: 999px; font-size: 13px; margin: 3px 0 3px 6px; border: 1px solid;}
.c-red {color: #fecaca; background: rgba(239,68,68,.16); border-color: rgba(239,68,68,.5);}
.c-amber {color: #fde68a; background: rgba(245,158,11,.16); border-color: rgba(245,158,11,.5);}
.c-green {color: #bbf7d0; background: rgba(34,197,94,.16); border-color: rgba(34,197,94,.5);}
.c-blue {color: #bfdbfe; background: rgba(59,130,246,.16); border-color: rgba(59,130,246,.5);}
.muted {color: #9aa6c9 !important; font-size: 13px;}
.verdict-box {border-radius: 20px; padding: 18px 22px; border: 1px solid; height: 100%;}
.v-red {background: linear-gradient(135deg, rgba(239,68,68,.25), rgba(127,29,29,.25)); border-color: rgba(239,68,68,.6);}
.v-amber {background: linear-gradient(135deg, rgba(245,158,11,.25), rgba(120,53,15,.25)); border-color: rgba(245,158,11,.6);}
.v-green {background: linear-gradient(135deg, rgba(34,197,94,.22), rgba(20,83,45,.25)); border-color: rgba(34,197,94,.6);}
.v-title {font-size: 34px; font-weight: 800; margin: 0; color: #fff !important;}
.step {display: flex; gap: 12px; align-items: flex-start; padding: 8px 0; border-bottom: 1px dashed rgba(255,255,255,.1);}
.step:last-child {border-bottom: none;}
.step .n {min-width: 28px; height: 28px; border-radius: 50%; background: linear-gradient(135deg,#22d3ee,#6366f1);
          color: #fff; font-weight: 800; display: flex; align-items: center; justify-content: center; font-size: 14px;}
.flow {display: flex; flex-wrap: wrap; gap: 10px; margin: 8px 0;}
.flow .f {flex: 1 1 150px; background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.12); border-radius: 14px; padding: 12px; text-align: center;}
.flow .f b {display: block; color: #67e8f9; margin-bottom: 4px;}
.arc {animation: grow 1.1s ease-out;}
@keyframes grow {from {stroke-dasharray: 0 251.3;}}
ul.clean {margin: 0; padding-right: 20px;}
/* عناصر Streamlit */
.stButton > button {border-radius: 12px; border: 1px solid rgba(255,255,255,.18); background: rgba(255,255,255,.07);
                    color: #e8ecf8; font-weight: 600; transition: all .15s;}
.stButton > button:hover {border-color: #22d3ee; background: rgba(34,211,238,.14); color: #fff; transform: translateY(-1px);}
.stButton > button[kind="primary"], [data-testid="stBaseButton-primary"] {background: linear-gradient(90deg,#06b6d4,#6366f1) !important;
        border: none !important; color: #fff !important; font-size: 17px; padding: .6rem 1rem; box-shadow: 0 8px 24px rgba(99,102,241,.35);}
.stTextArea textarea, .stTextInput input {background: rgba(255,255,255,.06) !important; color: #fff !important;
        border-radius: 14px !important; border: 1px solid rgba(255,255,255,.18) !important; direction: rtl; text-align: right; font-size: 16px;}
.stTabs [data-baseweb="tab-list"] {gap: 6px;}
.stTabs [data-baseweb="tab"] {border-radius: 12px 12px 0 0; padding: 8px 16px; color: #b9c2e0;}
.stTabs [aria-selected="true"] {background: rgba(255,255,255,.08); color: #fff;}
[data-testid="stMetricValue"] {color: #67e8f9;}
[data-testid="stExpander"] {background: rgba(255,255,255,.04); border-radius: 14px; border: 1px solid rgba(255,255,255,.1);}
</style>
"""

COLORS = {"نصب": ("#ef4444", "v-red", "c-red", "🚨"), "مشبوه": ("#f59e0b", "v-amber", "c-amber", "⚠️"),
          "سليم": ("#22c55e", "v-green", "c-green", "✅")}

def hero() -> str:
    return ('<div class="hero"><span class="shield">🛡️</span><h1>كاشف النصب والرسائل المشبوهة</h1>'
            '<p>الصق أي رسالة SMS أو واتساب أو إيميل أو رابط، وهتعرف في ثواني: نصب ولا لأ، وليه، وتعمل إيه.</p>'
            '<span class="chip c-blue">RAG</span><span class="chip c-blue">LangChain</span>'
            '<span class="chip c-blue">Output Parser</span><span class="chip c-blue">QLoRA</span>'
            '<span class="chip c-blue">فحص روابط حقيقي</span></div>')

def gauge(score: int, color: str) -> str:
    d = 251.3 * score / 100
    return ('<svg viewBox="0 0 200 125" width="100%" style="max-width:290px;display:block;margin:auto">'
            '<path d="M20 100 A80 80 0 0 1 180 100" fill="none" stroke="rgba(255,255,255,.12)" stroke-width="16" stroke-linecap="round"/>'
            f'<path class="arc" d="M20 100 A80 80 0 0 1 180 100" fill="none" stroke="{color}" stroke-width="16" '
            f'stroke-linecap="round" stroke-dasharray="{d:.1f} 251.3"/>'
            f'<text x="100" y="94" text-anchor="middle" font-size="40" font-weight="800" fill="{color}">{score}</text>'
            '<text x="100" y="116" text-anchor="middle" font-size="12" fill="#9aa6c9">درجة الخطورة من 100</text></svg>')

def verdict_box(verdict: str, summary: str, sources: list) -> str:
    color, vcls, ccls, icon = COLORS[verdict]
    chips = "".join(f'<span class="chip c-blue">{esc(s)}</span>' for s in sources)
    return (f'<div class="verdict-box {vcls}"><p class="v-title">{icon} {esc(verdict)}</p>'
            f'<p style="margin:8px 0 12px;font-size:16px">{esc(summary)}</p>{chips}</div>')

def chips(items, kind=None) -> str:
    out = ""
    for it in items:
        w = it.get("weight", 0)
        cls = kind or ("c-green" if w < 0 else "c-red" if w >= 30 else "c-amber" if w >= 20 else "c-blue")
        out += f'<span class="chip {cls}">{esc(it["label"])}</span>'
    return out

def card(title: str, body: str) -> str:
    return f'<div class="card"><h4>{esc(title)}</h4>{body}</div>'

def steps(items) -> str:
    return "".join(f'<div class="step"><div class="n">{i}</div><div>{esc(a)}</div></div>' for i, a in enumerate(items, 1))

def ul(items) -> str:
    return '<ul class="clean">' + "".join(f"<li>{esc(i)}</li>" for i in items) + "</ul>"

def link_card(a: dict) -> str:
    cls = {"خطير": "c-red", "مشبوه": "c-amber", "عادي": "c-green"}[a["level"]]
    rows = "".join(f'<li>{esc(t)}</li>' for t, _ in a["findings"]) or \
        '<li>مفيش علامات خطر ظاهرة (ده مش معناه إنه آمن 100%)</li>'
    chain = ""
    if len(a["chain"]) > 1:
        hops = " ← ".join(f'<span dir="ltr">{esc(h[:60])}</span>' for h in a["chain"])
        chain = f'<div class="muted" style="margin-top:6px">مسار التحويل: {hops}</div>'
    note = f'<div class="muted">ملاحظة: {esc(a["note"])}</div>' if a.get("note") else ""
    return (f'<div class="card"><div><span class="chip {cls}">{esc(a["level"])} · {a["risk"]}/100</span> '
            f'<span dir="ltr" style="font-weight:600">{esc(a["url"][:80])}</span></div>'
            f'<ul class="clean" style="margin-top:8px">{rows}</ul>{chain}{note}</div>')

def pipeline() -> str:
    items = [("1. الرسالة", "بتلصقها أو تختار مثال"), ("2. قواعد الأمان", "علامات النصب + فحص الروابط"),
             ("3. RAG", "أقرب أنماط نصب معروفة"), ("4. LLM + Chain", "تحليل وتفسير"),
             ("5. Output Parser", "JSON ثابت: حكم + أسباب + إجراء")]
    return '<div class="flow">' + "".join(f'<div class="f"><b>{a}</b><span class="muted">{b}</span></div>' for a, b in items) + "</div>"
