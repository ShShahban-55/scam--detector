"""بيولّد داتا ست تدريب (train.jsonl) وتقييم (test.jsonl) من قوالب رسائل نصب بالعامية المصرية.
الأفضل بعد كده تزوّد عليها رسائل حقيقية (من غير بيانات شخصية) في SEED_REAL تحت."""
import json, os, random, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from prompts import SHORT_SYSTEM, build_user
from url_check import check_urls

random.seed(42)
CHUNKS = open(os.path.join(ROOT, "data", "scam_patterns.txt"), encoding="utf-8").read().split("\n\n")
def chunk_of(key): return next(c for c in CHUNKS if key in c)

BANKS = ["البنك الأهلي", "بنك مصر", "CIB", "البنك التجاري الدولي", "بنك القاهرة"]
BRANDS_AR = ["فودافون", "اتصالات", "أورنج", "فوري", "أمازون", "نون"]
PRIZES = ["سيارة", "موبايل آيفون", "مبلغ 50000 جنيه", "رحلة عمرة", "لابتوب"]
AMOUNTS = ["200", "350", "500", "1000", "2500", "5000"]
HOURS = ["12", "24", "48"]
BAD_LINKS_PREFIX = ["ahly", "misr", "cib", "vodafone", "fawry"]

def rnd(n=6): return "".join(random.choice("abcdefghjkmnpqrstuvwxyz23456789") for _ in range(n))
def make_link():
    k = random.randint(0, 3)
    if k == 0: return f"bit.ly/{rnd()}"
    if k == 1: return f"cutt.ly/{rnd(5)}"
    if k == 2: return f"https://{random.choice(BAD_LINKS_PREFIX)}-{random.choice(['login','secure','update'])}-{random.choice(['verify','portal'])}.xyz"
    return f"http://{random.choice(BAD_LINKS_PREFIX)}-eg.top/{rnd(4)}"
def make_phone(): return "01" + random.choice("0125") + "".join(random.choice("0123456789") for _ in range(8))

TYPES = {
 "bank": dict(key="انتحال صفة البنك", verdict="نصب", conf=(90, 98),
  templates=[
   "عزيزي العميل، حسابك في {bank} هيتقفل خلال {hours} ساعة. اضغط هنا للتحديث: {link}",
   "تم إيقاف كارتك في {bank} لأسباب أمنية. حدّث بياناتك فورا من {link}",
   "{bank}: تم رصد عملية مشبوهة على حسابك. ابعتلنا الرقم السري وكود OTP لإلغائها.",
   "تنبيه هام من {bank}: لازم تأكد بيانات الكارت خلال {hours} ساعة وإلا هيتم تجميد الحساب. {link}",
   "حسابك البنكي اتعلق. للفتح ادخل على {link} وادخل رقم الكارت وCVV."],
  reasons=["تهديد بقفل الحساب أو الكارت", "استعجال بمهلة قصيرة", "طلب بيانات سرية (رقم سري أو OTP أو CVV)",
           "البنوك مبتطلبش بيانات الكارت برسالة", "الرابط مش الموقع الرسمي للبنك"],
  action=["متضغطش على الرابط", "امسح الرسالة", "كلم البنك على الرقم الرسمي ورا الكارت", "لو دخلت بياناتك غيّر الرقم السري وجمّد الكارت فورا"],
  report="أبلغ عن رسالة احتيالية منتحلة صفة {bank} وصلتني على موبايلي، بتطلب بيانات الكارت وبتحتوي على رابط مشبوه. مرفق نص الرسالة."),
 "prize": dict(key="جايزة وهمية", verdict="نصب", conf=(88, 97),
  templates=[
   "مبروك! كسبت {prize} في سحب {brand}. ادفع {amount} جنيه رسوم شحن عشان تستلمها: {link}",
   "تهانينا! تم اختيار رقمك للفوز بـ{prize}. ابعتلنا بياناتك وكارت شحن بـ{amount} جنيه.",
   "{brand}: أنت الفائز بـ{prize}! سجّل بياناتك خلال {hours} ساعة من {link}"],
  reasons=["جايزة من غير ما تشارك في أي سحب", "طلب فلوس أو رسوم قبل الاستلام", "استعجال بمهلة محددة", "رابط مجهول أو غير رسمي"],
  action=["تجاهل الرسالة ومتحولش فلوس", "متبعتش أي بيانات شخصية", "بلّغ الشركة الحقيقية من قنواتها الرسمية"],
  report="أبلغ عن رسالة نصب بجايزة وهمية منسوبة لـ{brand} بتطلب رسوم لاستلام الجايزة."),
 "otp": dict(key="طلب كود OTP", verdict="نصب", conf=(90, 97),
  templates=[
   "معلش بعتلك كود بالغلط على موبايلك ممكن تبعتهولي؟",
   "أنا من خدمة عملاء {brand}، ابعتلي الكود اللي وصلك عشان نفعّل حسابك.",
   "كود التحقق بتاعك وصلك؟ ابعتهولي بسرعة عشان نلغي عملية سحب على حسابك.",
   "أهلا، أنا بكلمك من {bank}، قولي الكود اللي هيوصلك دلوقتي."],
  reasons=["طلب كود تحقق OTP", "كود OTP سري ومش بيتشارك مع أي حد", "ادعاء صفة خدمة العملاء بدون إثبات"],
  action=["متبعتش الكود لأي حد", "اقفل المحادثة أو المكالمة", "لو شاركته غيّر كلمة السر فورا وكلم الجهة على رقمها الرسمي"],
  report="أبلغ عن محاولة احتيال لسرقة كود التحقق OTP عن طريق انتحال صفة خدمة العملاء."),
 "job": dict(key="عرض شغل وهمي", verdict="نصب", conf=(85, 95),
  templates=[
   "فرصة شغل من البيت براتب 15000 جنيه من غير خبرة! حوّل {amount} جنيه رسوم تسجيل وابدأ النهاردة. {link}",
   "مطلوب موظفين فورا للعمل أونلاين، الراتب يومي. ادفع {amount} جنيه ثمن الأدوات وهنبعتلك الشغل.",
   "وظيفة مضمونة في شركة كبيرة من غير مقابلة، التسجيل بـ{amount} جنيه بس: {link}"],
  reasons=["راتب مبالغ فيه من غير خبرة", "طلب رسوم من المتقدم للوظيفة", "مفيش مقابلة أو بيانات واضحة للشركة"],
  action=["متدفعش أي رسوم", "ابحث عن الشركة في موقعها الرسمي", "متبعتش صورة بطاقتك لجهة مجهولة"],
  report="أبلغ عن عرض وظيفة وهمي بيطلب رسوم تسجيل مقابل فرصة عمل."),
 "invest": dict(key="استثمار وربح مضمون", verdict="نصب", conf=(85, 95),
  templates=[
   "استثمر {amount} جنيه واكسب الضعف خلال أسبوع! ربح مضمون 100% من غير مخاطرة. {link}",
   "عملات رقمية بربح يومي مضمون، ادخل المجموعة وابدأ بـ{amount} جنيه بس.",
   "فرصة العمر: ضاعف فلوسك في {hours} ساعة مع خبراء التداول. التواصل واتساب {phone}"],
  reasons=["وعد بربح مضمون من غير مخاطرة", "ضغط للدفع بسرعة", "شكل مشهور من الاستثمار الوهمي (هرمي)"],
  action=["متحولش أي فلوس", "اتأكد إن الجهة مرخصة من الهيئة العامة للرقابة المالية", "بلّغ المنصة اللي وصلتك منها الرسالة"],
  report="أبلغ عن عرض استثمار وهمي بيوعد بأرباح مضمونة ويطلب تحويل أموال."),
 "relative": dict(key="قريب أو صديق في ورطة", verdict="نصب", conf=(80, 92),
  templates=[
   "ازيك يا بابا ده رقمي الجديد، موبايلي باظ. حوّلي {amount} جنيه ضروري على {phone}",
   "أنا صاحبك، اتحجزت في مشكلة وعايز {amount} جنيه حالا، متقولش لحد.",
   "مرحبا يا ماما ده رقم جديد، محتاج فلوس بسرعة وهرجعهم لك. حوّلي على {phone}"],
  reasons=["رقم جديد بيدّعي إنه قريب أو صديق", "طلب تحويل فلوس عاجل", "مبرر ضعيف وطلب إخفاء الموضوع"],
  action=["اتصل بالشخص على رقمه القديم قبل أي تحويل", "متحولش فلوس لرقم مجهول", "اسأل سؤال شخصي ميعرفش إجابته غير الشخص الحقيقي"],
  report="أبلغ عن محاولة نصب بانتحال شخصية أحد المقربين وطلب تحويل أموال عاجل."),
 "bill": dict(key="فاتورة أو شحنة أو غرامة مرور وهمية", verdict="نصب", conf=(85, 95),
  templates=[
   "عليك غرامة مرور {amount} جنيه، ادفع قبل {hours} ساعة لتجنب الزيادة: {link}",
   "شحنتك من {brand} معلقة. ادفع {amount} جنيه رسوم توصيل من {link}",
   "فاتورة {brand} متأخرة، هيتم فصل الخدمة لو مدفعتش خلال {hours} ساعة: {link}"],
  reasons=["تهديد بغرامة أو فصل الخدمة", "طلب دفع من رابط في رسالة", "الجهات الرسمية بتدفع من تطبيقاتها ومواقعها المعروفة"],
  action=["متضغطش على الرابط", "ادخل على التطبيق أو الموقع الرسمي بنفسك وراجع الفاتورة", "بلّغ الجهة اللي اتنسبت لها الرسالة"],
  report="أبلغ عن رسالة وهمية منسوبة لـ{brand} بتطلب دفع مبلغ من رابط مشبوه."),
}

SUSPICIOUS = dict(key="علامات عامة للنصب", verdict="مشبوه", conf=(50, 70),
  templates=[
   "عرض خاص! خصم 70% على كل الموبايلات النهاردة بس، اطلب من {shop}",
   "عندك رسالة جديدة، اتفرج عليها هنا {shop}",
   "رقم جديد: أهلا، ممكن تكلمني ضروري في موضوع هام؟",
   "حد سجّل باسمك في خدمة جديدة، لو مش انت ادخل على {shop} للإلغاء"],
  reasons=["فيه علامات تثير الشك (استعجال أو رابط غير معروف)", "مفيش معلومات كافية تأكد الجهة المرسلة", "الأفضل التحقق قبل أي تصرف"],
  action=["متضغطش على أي رابط قبل ما تتأكد", "اتواصل مع الجهة من قناتها الرسمية", "متبعتش أي بيانات شخصية"],
  report="")

SAFE = [
 "ازيك؟ هعدي عليك بكرة الساعة 5 ناخد القهوة اللي اتفقنا عليها.",
 "تم تأكيد حجزك في المطعم يوم الجمعة الساعة 8 مساءً. شكراً لاختيارك لنا.",
 "الاجتماع اتأجل لبكرة الساعة 11، هبعتلك اللينك على الإيميل.",
 "كل سنة وانت طيب! ربنا يتمم عليك بالخير.",
 "ماما بتسأل هتيجي الغدا النهاردة ولا لأ؟",
 "اشتراكك الشهري اتجدد بنجاح. تقدر تراجع التفاصيل من التطبيق الرسمي.",
 "نتيجة التحليل جاهزة، تقدر تستلمها من المعمل من الساعة 9 لـ5.",
 "ماتنساش تجيب الكتب معاك بكرة الكلية.",
 "شكرا على المساعدة امبارح، فرقت معايا كتير.",
 "الدكتور بيقول الامتحان يوم الأحد في المدرج الكبير.",
 "هرجع من الشغل متأخر شوية، اتغدوا من غيري.",
 "تم استلام طلبك رقم 4521 وهيوصلك خلال يومين، تقدر تتابعه من تطبيق المتجر.",
]
SHOPS = ["deals-eg.shop", "bit.ly/" , "offers-today.online", "cutt.ly/"]

def fmt(t):
    return t.format(bank=random.choice(BANKS), brand=random.choice(BRANDS_AR), prize=random.choice(PRIZES),
                    amount=random.choice(AMOUNTS), hours=random.choice(HOURS), link=make_link(),
                    phone=make_phone(), shop=random.choice(SHOPS) + (rnd(5) if SHOPS else ""))

def build(message, spec, ctx_key):
    others = [c for c in CHUNKS if ctx_key not in c]
    ctx = [chunk_of(ctx_key), random.choice(others)]
    random.shuffle(ctx)
    warnings = check_urls(message)
    reasons = random.sample(spec["reasons"], k=min(3, len(spec["reasons"])))
    if warnings and spec["verdict"] != "سليم":
        reasons = reasons[:2] + [warnings[0]]
    out = {"verdict": spec["verdict"], "confidence": random.randint(*spec["conf"]),
           "reasons": reasons, "action": spec["action"],
           "report_text": spec["report"].format(bank=random.choice(BANKS), brand=random.choice(BRANDS_AR)) if spec["report"] else ""}
    user = build_user(message, "\n---\n".join(ctx), "\n".join(warnings) if warnings else "لا يوجد")
    return {"messages": [{"role": "system", "content": SHORT_SYSTEM},
                         {"role": "user", "content": user},
                         {"role": "assistant", "content": json.dumps(out, ensure_ascii=False)}]}

rows, seen = [], set()
def add(msg, spec, key):
    if msg in seen: return
    seen.add(msg); rows.append(build(msg, spec, key))

for spec in TYPES.values():
    for _ in range(60):
        add(fmt(random.choice(spec["templates"])), spec, spec["key"])
for _ in range(50):
    add(fmt(random.choice(SUSPICIOUS["templates"])), SUSPICIOUS, SUSPICIOUS["key"])
SAFE_SPEC = dict(verdict="سليم", conf=(85, 95), report="",
                 reasons=["مفيش طلب فلوس أو بيانات سرية", "مفيش استعجال أو تهديد", "مفيش رابط مشبوه", "الرسالة عادية ومفيهاش علامات نصب"],
                 action=["مفيش إجراء خاص، تعامل معاها عادي", "خليك حذر دايما من أي رابط أو طلب بيانات"])
for m in SAFE:
    add(m, SAFE_SPEC, SUSPICIOUS["key"])

# ---- ضيف هنا رسائل حقيقية (من غير بيانات شخصية) بنفس الشكل ----
SEED_REAL = []  # مثال: ("نص الرسالة", "bank")
for msg, t in SEED_REAL:
    add(msg, TYPES[t], TYPES[t]["key"])

random.shuffle(rows)
cut = int(len(rows) * 0.85)
os.chdir(os.path.dirname(os.path.abspath(__file__)))
for name, part in (("train.jsonl", rows[:cut]), ("test.jsonl", rows[cut:])):
    with open(name, "w", encoding="utf-8") as f:
        for r in part: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(name, len(part))
