import os
from contextlib import nullcontext
from datetime import datetime, timedelta, timezone

import streamlit as st

st.set_page_config(page_title="كاشف النصب", page_icon="🛡️", layout="centered")

from engine import run_chain
from signals import detect, verdict_from_score, ACTIONS
from links import analyze_url
from url_check import extract_urls
import ui

def secret(name, default=None):
    try:
        return st.secrets[name]
    except Exception:
        return os.getenv(name, default)

GROQ_KEY = secret("GROQ_API_KEY")
GROQ_MODEL = secret("GROQ_MODEL", "llama-3.3-70b-versatile")
MODE = "cloud" if GROQ_KEY else "local"      # بدون مفتاح = بيشتغل بالموديل المحلي (Kaggle)

# ---------------------- تحميل المكونات (مرة واحدة) ----------------------
# بيجرّب الموديلات بالترتيب لحد ما واحد يشتغل مع حسابك
CANDIDATES = [GROQ_MODEL, "openai/gpt-oss-120b", "llama-3.1-8b-instant", "openai/gpt-oss-20b", "llama-3.3-70b-versatile"]

@st.cache_resource
def load_cloud():
    from langchain_groq import ChatGroq
    from rag_light import get_light_retriever
    models = list(dict.fromkeys(m for m in CANDIDATES if m))
    llms = [ChatGroq(api_key=GROQ_KEY, model=m, temperature=0,
                     model_kwargs={"response_format": {"type": "json_object"}}) for m in models]
    return llms[0].with_fallbacks(llms[1:]), get_light_retriever()

@st.cache_resource
def load_local():
    from llm import load_model, make_chat_llm
    from rag import get_retriever
    model, tok, has_adapter = load_model()
    return model, make_chat_llm(model, tok), get_retriever(), has_adapter

def run_llm(message: str, use_ft: bool):
    if MODE == "cloud":
        llm, retriever = load_cloud()
        docs = retriever.invoke(message)
        res, _ = run_chain(message, llm, docs, use_ft_prompt=False)
    else:
        model, llm, retriever, has_adapter = load_local()
        docs = retriever.invoke(message)
        ft = use_ft and has_adapter
        ctx = model.disable_adapter() if (has_adapter and not ft) else nullcontext()
        with ctx:
            res, _ = run_chain(message, llm, docs, use_ft_prompt=ft)
    return res, docs

# ---------------------- التحليل الكامل (قواعد + روابط + ذكاء اصطناعي) ----------------------
ORDER = {"سليم": 0, "مشبوه": 1, "نصب": 2}
BAND = {"سليم": (0, 34), "مشبوه": (35, 69), "نصب": (70, 100)}

def analyze_message(message: str, use_ft: bool, expand: bool) -> dict:
    sig = detect(message)
    urls = list(dict.fromkeys(extract_urls(message)))[:4]
    url_infos = [analyze_url(u, expand) for u in urls]
    url_risk = max((u["risk"] for u in url_infos), default=0)
    rule_score = min(100, sig["score"] + round(url_risk * 0.8))
    rule_verdict = verdict_from_score(rule_score)

    res, docs, llm_error = None, [], None
    try:
        res, docs = run_llm(message, use_ft)
    except Exception as e:
        llm_error = f"{type(e).__name__}: {str(e)[:140]}"

    if res is not None:                              # دمج الذكاء الاصطناعي مع القواعد (القواعد بترفع بس، مش بتنزّل)
        verdict = max(res.verdict, rule_verdict, key=lambda v: ORDER[v])
        llm_risk = max(res.confidence, 70) if res.verdict == "نصب" else 55 if res.verdict == "مشبوه" \
            else round((100 - res.confidence) * 0.4)
        score = round(0.55 * llm_risk + 0.45 * rule_score)
    else:
        verdict, score = rule_verdict, rule_score
    lo, hi = BAND[verdict]
    score = max(lo, min(hi, score))

    sig_labels = [m["label"] for m in sig["matched"]] + [f"رابط: {t}" for u in url_infos for t, w in u["findings"] if w >= 25][:2]
    reasons = (res.reasons if res else []) or sig_labels or ["مفيش علامات نصب واضحة في الرسالة"]
    actions = list(res.action) if res and res.action else []
    if not actions:
        if verdict != "سليم":
            if url_infos: actions.append(ACTIONS["click"])
            actions += [ACTIONS[m["key"]] for m in sig["matched"] if m["key"] in ACTIONS and m["key"] != "click"]
            actions += ["كلم الجهة على رقمها الرسمي، وبلّغ عن الرسالة وامسحها"]
        else:
            actions = ["مفيش إجراء خاص، تعامل معاها عادي", "خليك حذر دايماً من أي رابط أو طلب بيانات"]
    report = res.report_text if res else ""
    if not report.strip() and verdict != "سليم":
        report = "أبلغ عن رسالة احتيالية وصلتني على موبايلي، وبتحتوي على علامات نصب (طلب بيانات/فلوس أو رابط مشبوه). نص الرسالة:\n" + message[:300]
    return dict(verdict=verdict, score=score, res=res, docs=docs, sig=sig, urls=url_infos, reasons=reasons,
                actions=actions[:5], report=report, llm_error=llm_error,
                escalated=bool(res and ORDER[verdict] > ORDER[res.verdict]))

# ---------------------- حالة الجلسة ----------------------
st.session_state.setdefault("history", [])
st.session_state.setdefault("msg", "")
st.session_state.setdefault("auto_run", False)

EXAMPLES = [
    ("🏦 رسالة بنك", "عزيزي العميل، حسابك في البنك الأهلي هيتقفل خلال 24 ساعة. اضغط هنا للتحديث: bit.ly/3xYz"),
    ("🎁 جايزة", "مبروك! كسبت سيارة في سحب فودافون. ادفع 500 جنيه رسوم شحن على الرقم ده عشان تستلمها."),
    ("🔐 كود OTP", "معلش بعتلك كود بالغلط على موبايلك ممكن تبعتهولي؟"),
    ("🔗 رابط مشبوه", "تم رصد نشاط غريب على حسابك. ادخل على https://ahly-secure-login-verify.xyz/auth وأكد بياناتك"),
    ("💼 وظيفة وهمية", "فرصة شغل من البيت براتب 15000 جنيه من غير خبرة! حوّل 350 جنيه رسوم تسجيل وابدأ النهاردة."),
    ("📈 استثمار", "استثمر 1000 جنيه واكسب الضعف خلال أسبوع! ربح مضمون 100% من غير مخاطرة."),
    ("👨‍👩‍👦 قريب في ورطة", "ازيك يا بابا ده رقمي الجديد، موبايلي باظ. حوّلي 2000 جنيه ضروري على 01012345678"),
    ("✅ رسالة سليمة", "تم تأكيد حجزك في المطعم يوم الجمعة الساعة 8 مساءً. شكراً لاختيارك لنا."),
]

def load_example(text):
    st.session_state["msg"] = text
    st.session_state["auto_run"] = True

# ---------------------- عرض النتيجة ----------------------
def render_result(r: dict):
    color = ui.COLORS[r["verdict"]][0]
    summary = {"نصب": "الرسالة دي فيها علامات نصب واضحة. متتعاملش معاها.",
               "مشبوه": "فيه علامات تثير الشك. اتأكد من الجهة بنفسك قبل أي تصرف.",
               "سليم": "مفيش علامات نصب واضحة، بس خليك حذر دايماً."}[r["verdict"]]
    sources = ["قواعد الأمان", "فحص الروابط"] + (["ذكاء اصطناعي + RAG"] if r["res"] else ["قواعد فقط"])
    c1, c2 = st.columns([1, 1.25])
    c1.markdown(f'<div class="card">{ui.gauge(r["score"], color)}</div>', unsafe_allow_html=True)
    c2.markdown(ui.verdict_box(r["verdict"], summary, sources), unsafe_allow_html=True)

    if r["llm_error"]:
        st.warning("الذكاء الاصطناعي مش متاح دلوقتي، فالنتيجة من قواعد الأمان وفحص الروابط بس.")
    if r["escalated"]:
        st.info("قواعد الأمان رفعت التصنيف لأن فيه علامات قوية الذكاء الاصطناعي ماعتبرهاش.")

    if r["sig"]["matched"] or r["sig"]["positives"]:
        st.markdown(ui.card("🧩 العلامات اللي اتكشفت", ui.chips(r["sig"]["matched"]) + ui.chips(r["sig"]["positives"])),
                    unsafe_allow_html=True)
    st.markdown(ui.card("🧐 ليه الحكم ده؟", ui.ul(r["reasons"])), unsafe_allow_html=True)
    if r["urls"]:
        st.markdown("#### 🔗 فحص الروابط")
        for u in r["urls"]:
            st.markdown(ui.link_card(u), unsafe_allow_html=True)
    st.markdown(ui.card("✅ اعمل إيه دلوقتي", ui.steps(r["actions"])), unsafe_allow_html=True)
    if r["report"].strip():
        st.markdown("##### 📝 نص بلاغ جاهز (اضغط أيقونة النسخ)")
        st.code(r["report"], language=None)
    if r["docs"]:
        with st.expander("📚 الأنماط اللي اعتمد عليها الـ RAG"):
            for d in r["docs"]:
                st.write(d.page_content)
    st.caption("⚠️ مساعد توعية مش حكم نهائي. لو في شك، كلم البنك أو الجهة على رقمها الرسمي.")

def log(message, r):
    tz = timezone(timedelta(hours=3))
    st.session_state["history"].insert(0, {"الوقت": datetime.now(tz).strftime("%H:%M:%S"),
        "الرسالة": message[:60] + ("…" if len(message) > 60 else ""), "الحكم": r["verdict"], "الخطورة": r["score"]})

# ---------------------- الواجهة ----------------------
st.markdown(ui.CSS, unsafe_allow_html=True)
st.markdown(ui.hero(), unsafe_allow_html=True)

use_ft = False
with st.sidebar:
    st.markdown("### ⚙️ الإعدادات")
    expand = st.toggle("🌐 فك الروابط المختصرة (اتصال حقيقي)", value=True,
                       help="بيتتبع التحويلات عشان يعرف الرابط بيودّيك فين فعلاً، من غير ما يفتح الصفحة.")
    if MODE == "local":
        use_ft = st.toggle("🎯 الموديل المتدرب (Fine-tuned)", value=True)
    else:
        st.caption("النسخة السحابية: قواعد أمان + RAG + LangChain + Output Parser. الموديل المتدرب QLoRA بيشتغل في نسخة Kaggle.")
    h = st.session_state["history"]
    st.markdown("### 📊 إحصائيات الجلسة")
    a, b = st.columns(2)
    a.metric("تم فحصه", len(h))
    b.metric("نصب", sum(1 for x in h if x["الحكم"] == "نصب"))
    st.caption("الرسائل مش بتتخزن عندنا، والسجل بيتمسح لما تقفل الصفحة.")

tab1, tab2, tab3, tab4 = st.tabs(["🔍 فحص رسالة", "🔗 فحص رابط", "🕘 السجل", "ℹ️ عن المشروع"])

with tab1:
    st.markdown("**جرّب مثال بضغطة واحدة** أو الصق رسالة حقيقية وصلتك:")
    for row in (EXAMPLES[:4], EXAMPLES[4:]):
        cols = st.columns(4)
        for col, (label, text) in zip(cols, row):
            col.button(label, key=f"ex_{label}", on_click=load_example, args=(text,), width="stretch")
    st.text_area("الصق الرسالة هنا", key="msg", height=150,
                 placeholder="مثال: عزيزي العميل، حسابك هيتقفل... (SMS أو واتساب أو إيميل)")
    run = st.button("🔍 افحص الرسالة الآن", type="primary", width="stretch")
    auto = st.session_state.pop("auto_run", False)
    if run or auto:
        message = st.session_state["msg"]
        if not message.strip():
            st.warning("اكتب أو الصق رسالة الأول.")
        else:
            with st.spinner("بفحص الرسالة: قواعد الأمان، الروابط، والذكاء الاصطناعي..."):
                result = analyze_message(message, use_ft, expand)
            log(message, result)
            render_result(result)

with tab2:
    st.markdown("الصق أي رابط وصلك، وهنفحصه (ولو مختصر هنفكه ونعرف بيودّي فين).")
    link = st.text_input("الرابط", placeholder="bit.ly/xxxx أو https://...", key="link_in")
    if st.button("🔎 افحص الرابط", width="stretch"):
        if not link.strip():
            st.warning("الصق رابط الأول.")
        else:
            with st.spinner("بفحص الرابط..."):
                info = analyze_url(link, expand)
            ui_color = {"خطير": "نصب", "مشبوه": "مشبوه", "عادي": "سليم"}[info["level"]]
            st.markdown(f'<div class="card">{ui.gauge(info["risk"], ui.COLORS[ui_color][0])}</div>', unsafe_allow_html=True)
            st.markdown(ui.link_card(info), unsafe_allow_html=True)
            st.caption("غياب علامات الخطر مش معناه إن الرابط آمن 100%. لو في شك متفتحوش.")

with tab3:
    if not st.session_state["history"]:
        st.info("لسه ماعملتش أي فحص. جرّب مثال من تاب الفحص.")
    else:
        st.dataframe(st.session_state["history"], width="stretch", hide_index=True)
        if st.button("🗑️ مسح السجل"):
            st.session_state["history"] = []
            st.rerun()

with tab4:
    st.markdown(ui.card("إزاي بيشتغل؟", ui.pipeline()), unsafe_allow_html=True)
    st.markdown(ui.card("التقنيات المستخدمة", ui.chips([{"label": t} for t in
        ["RAG", "LangChain Chains", "Output Parsers (Pydantic)", "QLoRA Fine-tuning", "4-bit Quantization",
         "Streamlit", "ngrok", "Kaggle", "GitHub"]], "c-blue")), unsafe_allow_html=True)
    st.markdown(ui.card("حدود المشروع", ui.ul([
        "مساعد توعية، مش بديل عن البنك أو الجهات الرسمية.",
        "قواعد الأمان بترفع التصنيف بس، ومبتنزّلوش، عشان الحذر أهم من الراحة.",
        "فك الروابط بيتتبع التحويلات بس، ومبيفتحش الصفحة ولا بيحمّل محتواها.",
        "النسخة السحابية بترسل نص الرسالة لخدمة Groq للتحليل، والنسخة المحلية على Kaggle بتشتغل بموديلنا المتدرب.",
    ])), unsafe_allow_html=True)
