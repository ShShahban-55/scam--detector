import re
from typing import List
from urllib.parse import urlparse

SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "cutt.ly", "is.gd", "rb.gy", "goo.gl", "shorturl.at"}
BAD_TLDS = (".xyz", ".top", ".click", ".icu", ".tk", ".ml", ".gq", ".cf", ".buzz", ".live")
# كلمة في الدومين -> الدومين الرسمي (راجعهم قبل التسليم)
BRANDS = {
    "ahly": "nbe.com.eg", "nbe": "nbe.com.eg", "misr": "banquemisr.com",
    "cib": "cibeg.com", "vodafone": "vodafone.com.eg", "fawry": "fawry.com",
    "instapay": "instapay.eg", "aramex": "aramex.com", "dhl": "dhl.com",
}

def extract_urls(text: str) -> List[str]:
    return re.findall(r"(?:https?://|www\.)[^\s]+|\b[\w-]+\.(?:com|net|org|xyz|top|click|ly|co)(?:/[^\s]*)?", text)

def check_urls(text: str) -> List[str]:
    warnings = []
    for url in extract_urls(text):
        host = urlparse(url if url.startswith("http") else "http://" + url).netloc.lower().replace("www.", "")
        if host in SHORTENERS:
            warnings.append(f"الرابط {host} رابط مختصر بيخبي الوجهة الحقيقية.")
        if host.endswith(BAD_TLDS):
            warnings.append(f"الدومين {host} امتداده مشهور في روابط النصب.")
        for brand, official in BRANDS.items():
            if brand in host and not host.endswith(official):
                warnings.append(f"الدومين {host} فيه اسم '{brand}' بس مش الموقع الرسمي ({official}).")
        if host.count("-") >= 2:
            warnings.append(f"الدومين {host} فيه شرطات كتير، وده شائع في المواقع المزيفة.")
    return list(dict.fromkeys(warnings))
