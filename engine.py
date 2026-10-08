"""قلب النظام: الـ Prompt + الـ Chain + الـ Output Parser (مشترك بين النسخة السحابية والمحلية)"""
from typing import List, Literal
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from url_check import check_urls
from prompts import SHORT_SYSTEM, build_user

class ScamResult(BaseModel):
    verdict: Literal["نصب", "مشبوه", "سليم"] = Field(description="الحكم النهائي")
    confidence: int = Field(description="نسبة الثقة من 0 إلى 100")
    reasons: List[str] = Field(description="أسباب الحكم، كل سبب جملة قصيرة")
    action: List[str] = Field(description="خطوات يعملها المستخدم دلوقتي")
    report_text: str = Field(description="نص بلاغ جاهز، أو فاضي لو الرسالة سليمة")

parser = PydanticOutputParser(pydantic_object=ScamResult)

PROMPT_BASE = ChatPromptTemplate.from_messages([
    ("system",
     "أنت مساعد توعية لكشف الاحتيال بالعربي المصري. حلل الرسالة بناءً على الأنماط المرجعية وتحذيرات الروابط.\n"
     "قواعد: لو مش متأكد قول 'مشبوه' ومش 'سليم'. لا تخترع معلومات. اكتب بلغة بسيطة.\n"
     "الأنماط المرجعية:\n{context}\n\nتحذيرات الروابط (من فحص آلي):\n{url_warnings}\n\n{format_instructions}"),
    ("human", "الرسالة:\n{message}"),
]).partial(format_instructions=parser.get_format_instructions())

PROMPT_FT = ChatPromptTemplate.from_messages([("system", SHORT_SYSTEM), ("human", "{user}")])

def run_chain(message: str, llm, docs, use_ft_prompt: bool = False):
    """بيرجّع (النتيجة، تحذيرات الروابط)"""
    context = "\n---\n".join(d.page_content for d in docs)
    warnings = check_urls(message)
    warn_txt = "\n".join(warnings) if warnings else "لا يوجد"
    if use_ft_prompt:
        chain = PROMPT_FT | llm | parser
        payload = {"user": build_user(message, context, warn_txt)}
    else:
        chain = PROMPT_BASE | llm | parser
        payload = {"context": context, "url_warnings": warn_txt, "message": message}
    return chain.invoke(payload), warnings
