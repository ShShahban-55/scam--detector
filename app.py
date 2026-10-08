import os
from contextlib import nullcontext

import streamlit as st
from engine import run_chain

def secret(name, default=None):
    try:
        return st.secrets[name]
    except Exception:
        return os.getenv(name, default)

GROQ_KEY = secret("GROQ_API_KEY")
GROQ_MODEL = secret("GROQ_MODEL", "llama-3.3-70b-versatile")
MODE = "cloud" if GROQ_KEY else "local"      # بدون مفتاح = بيشتغل بالموديل المحلي (Kaggle)

# ---------------------- تحميل المكونات (مرة واحدة) ----------------------
@st.cache_resource
def load_cloud():
    from langchain_groq import ChatGroq
    from rag_light import get_light_retriever
    llm = ChatGroq(api_key=GROQ_KEY, model=GROQ_MODEL, temperature=0,
                   model_kwargs={"response_format": {"type": "json_object"}})
    return llm, get_light_retriever()

@st.cache_resource
def load_local():
    from llm import load_model, make_chat_llm
    from rag import get_retriever
    model, tok, has_adapter = load_model()
    return model, make_chat_llm(model, tok), get_retriever(), has_adapter

def analyze(message: str, use_ft: bool):
    if MODE == "cloud":
        llm, retriever = load_cloud()
        docs = retriever.invoke(message)
        res, warnings = run_chain(message, llm, docs, use_ft_prompt=False)
    else:
        model, llm, retriever, has_adapter = load_local()
        docs = retriever.invoke(message)
        ft = use_ft and has_adapter
        ctx = model.disable_adapter() if (has_adapter and not ft) else nullcontext()
        with ctx:
            res, warnings = run_chain(message, llm, docs, use_ft_prompt=ft)
    return res, warnings, docs

# ---------------------- الواجهة ----------------------
st.set_page_config(page_title="كاشف النصب", page_icon="🛡️")
st.markdown("""
<style>
.block-container, .stTextArea textarea {direction: rtl; text-align: right;}
.verdict {padding: 16px; border-radius: 12px; font-size: 24px; font-weight: bold; text-align: center; color: white;}
</style>""", unsafe_allow_html=True)

use_ft = False
if MODE == "local":
    use_ft = st.sidebar.toggle("🎯 استخدم الموديل المتدرب (Fine-tuned)", value=True)
else:
    st.sidebar.info("النسخة السحابية: RAG + Chain + Output Parser + فحص الروابط.\nالموديل المتدرب (QLoRA) بيشتغل في نسخة Kaggle.")

st.title("🛡️ كاشف النصب والرسائل المشبوهة")
st.caption("مساعد توعية، مش حكم نهائي. لو في شك كلم البنك أو الجهة على رقمها الرسمي.")

EXAMPLES = {
    "— اختار مثال —": "",
    "بنك": "عزيزي العميل، حسابك في البنك الأهلي هيتقفل خلال 24 ساعة. اضغط هنا للتحديث: bit.ly/3xYz",
    "جايزة": "مبروك! كسبت سيارة في سحب فودافون. ادفع 500 جنيه رسوم شحن على الرقم ده عشان تستلمها.",
    "سليمة": "ازيك؟ هعدي عليك بكرة الساعة 5 ناخد القهوة اللي اتفقنا عليها.",
}
choice = st.selectbox("جرّب مثال", list(EXAMPLES.keys()))
message = st.text_area("الصق الرسالة هنا", value=EXAMPLES[choice], height=160)

if st.button("🔍 افحص", type="primary", use_container_width=True):
    if not message.strip():
        st.warning("اكتب أو الصق رسالة الأول.")
    else:
        with st.spinner("بفحص الرسالة..."):
            try:
                res, warnings, docs = analyze(message, use_ft)
            except Exception as e:
                st.error(f"حصل خطأ (ممكن الموديل ماطلعش JSON صحيح، جرب تاني): {e}")
                st.stop()

        color = {"نصب": "#d9534f", "مشبوه": "#f0ad4e", "سليم": "#5cb85c"}[res.verdict]
        st.markdown(f'<div class="verdict" style="background:{color}">'
                    f'{res.verdict} — ثقة {res.confidence}%</div>', unsafe_allow_html=True)
        st.subheader("🧐 الأسباب")
        for r in res.reasons:
            st.markdown(f"- {r}")
        if warnings:
            st.subheader("🔗 فحص الروابط")
            for w in warnings:
                st.warning(w)
        st.subheader("✅ اعمل إيه دلوقتي")
        for i, a in enumerate(res.action, 1):
            st.markdown(f"{i}. {a}")
        if res.report_text.strip():
            st.subheader("📝 نص بلاغ جاهز")
            st.code(res.report_text, language=None)
        with st.expander("📚 الأنماط اللي اعتمد عليها (RAG)"):
            for d in docs:
                st.write(d.page_content)
