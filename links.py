"""فحص الروابط: فحص ثابت للدومين + فك الروابط المختصرة بالاتصال الفعلي (مع حماية من الشبكات الداخلية)"""
import ipaddress, re, socket
from urllib.parse import urljoin, urlparse
import requests
from url_check import SHORTENERS, BAD_TLDS, BRANDS

def normalize(url: str) -> str:
    url = url.strip().strip(".,;:!?()[]{}\"'«»")
    return url if re.match(r"^https?://", url, re.I) else "http://" + url

def _host(url: str) -> str:
    return (urlparse(url).hostname or "").lower().replace("www.", "")

def static_checks(url: str):
    p, host, out = urlparse(url), _host(url), []
    if not host:
        return [("الرابط شكله مش سليم", 20)]
    if p.scheme == "http":
        out.append(("الرابط مش مشفّر (HTTP بدل HTTPS)", 10))
    if re.fullmatch(r"[\d.]+", host):
        out.append(("الرابط عبارة عن رقم IP مش اسم موقع", 30))
    if host in SHORTENERS:
        out.append((f"رابط مختصر ({host}) بيخبي الوجهة الحقيقية", 25))
    if host.endswith(BAD_TLDS):
        out.append((f"امتداد الدومين ({host.rsplit('.', 1)[-1]}) مشهور في روابط النصب", 20))
    for brand, official in BRANDS.items():
        if brand in host and not (host == official or host.endswith("." + official)):
            out.append((f"الدومين فيه اسم '{brand}' بس مش الموقع الرسمي ({official})", 40))
            break
    if host.count("-") >= 2:
        out.append(("الدومين فيه شرطات كتير، وده شائع في المواقع المزيفة", 10))
    if host.count(".") >= 4:
        out.append(("الدومين فيه نطاقات فرعية كتير", 10))
    if "@" in url.split("//", 1)[-1].split("/", 1)[0]:
        out.append(("الرابط فيه علامة @ لتضليل الوجهة", 25))
    if "xn--" in host:
        out.append(("الدومين بحروف مموّهة (Punycode)", 30))
    if len(url) > 90:
        out.append(("الرابط طويل بشكل غير طبيعي", 5))
    return out

def _is_public(host: str) -> bool:
    try:
        for info in socket.getaddrinfo(host, None):
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                return False
        return True
    except Exception:
        return False

def expand(url: str, max_hops: int = 5):
    """بيتتبع التحويلات واحدة واحدة (من غير ما يفتح الصفحة). بيرجّع (المسار، خطأ)"""
    chain, cur = [url], url
    try:
        for _ in range(max_hops):
            if not _is_public(_host(cur)):
                return chain, "الدومين مش قابل للوصول أو شبكة داخلية"
            r = requests.get(cur, allow_redirects=False, stream=True, timeout=6,
                             headers={"User-Agent": "Mozilla/5.0 (ScamChecker)"})
            loc, code = r.headers.get("Location"), r.status_code
            r.close()
            if code in (301, 302, 303, 307, 308) and loc:
                cur = urljoin(cur, loc)
                chain.append(cur)
            else:
                return chain, None
        return chain, "تحويلات كتير ورا بعض (مشبوه)"
    except Exception as e:
        return chain, f"تعذّر الاتصال ({type(e).__name__})"

def analyze_url(raw: str, do_expand: bool = False) -> dict:
    url = normalize(raw)
    findings = list(static_checks(url))
    info = {"url": url, "host": _host(url), "chain": [url], "final": url, "note": None}
    if do_expand:
        chain, err = expand(url)
        info["chain"], info["note"] = chain, err
        if len(chain) > 1:
            info["final"] = chain[-1]
            findings.append((f"الرابط بيحوّلك فعلياً إلى: {_host(chain[-1])}", 0))
            seen = {t for t, _ in findings}
            for t, w in static_checks(chain[-1]):
                if t not in seen:
                    findings.append(("الوجهة النهائية: " + t, w))
        if err and "كتير" in err:
            findings.append((err, 15))
    risk = min(100, sum(w for _, w in findings))
    info.update(findings=findings, risk=risk,
                level="خطير" if risk >= 45 else "مشبوه" if risk >= 20 else "عادي")
    return info
