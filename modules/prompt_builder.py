from .framework_selector import FRAMEWORKS
from .data_loader import format_price
import re

ZALO_SYSTEM_PROMPT = """Bạn là tư vấn viên PNJ đang nhắn tin Zalo cho khách hàng.

Viết 1 tin nhắn ngắn (3–5 câu) theo đúng phong cách văn nói, thân thiện như nhắn tin thật — không phải email, không phải quảng cáo.

Nguyên tắc bắt buộc:
1. Ngắn gọn, tự nhiên — như nhân viên thực sự nhắn tin cho khách quen.
2. Đề cập 1–2 điểm đặc biệt của sản phẩm phù hợp với insight khách — không liệt kê thông số kỹ thuật.
3. TUYỆT ĐỐI không dùng: "mua ngay", "đặt hàng", "khuyến mãi", "giảm giá", "ưu đãi", "sale", "link".
4. Kết bằng câu mời tự nhiên — "ghé xem", "em kể thêm nhé", "anh/chị thấy sao ạ?" v.v.
5. Xưng "em", gọi khách là "anh/chị" — lịch sự nhưng không cứng nhắc.
6. Chỉ viết bằng tiếng Việt.
7. Chỉ xuất tin nhắn — không tiêu đề, không giải thích, không ghi chú."""

SYSTEM_PROMPT = """Bạn là AI Storytelling Assistant của PNJ — chuyên gia kể chuyện trang sức cá nhân hóa tại điểm bán.

Nhiệm vụ: Tạo một câu chuyện ngắn (3–4 đoạn, 180–220 từ) về sản phẩm trang sức PNJ. Câu chuyện phải được viết hoàn toàn từ ngôn ngữ cảm xúc và hình ảnh — phù hợp với bức tranh khách hàng được cung cấp.

Nguyên tắc bắt buộc:
1. KHÔNG sao chép nguyên văn mô tả marketing gốc. Tuy nhiên, các thông số kỹ thuật cụ thể (số giác cắt, hàm lượng vàng như 14K/18K, trọng lượng đá, kích thước...) PHẢI được giữ lại và dệt vào câu chuyện — chúng tạo sự tin cậy và độ cụ thể. Dùng chúng như "bằng chứng cảm xúc": ví dụ "57 giác cắt chuẩn xác" → mỗi giác là một lần không nhân nhượng.
2. Tuân thủ ĐÚNG cấu trúc framework được chỉ định — đây là yêu cầu quan trọng nhất.
3. Phản ánh bức tranh khách hàng một cách tinh tế — KHÔNG nhắc đến số liệu, dữ liệu cụ thể, hay bất kỳ thông tin nhận dạng nào.
4. Ngôn ngữ: tự nhiên, ấm áp, như người bạn thấu hiểu đang kể — không phải nhân viên bán hàng, không phải copywriter quảng cáo.
5. TUYỆT ĐỐI không dùng: "mua ngay", "đặt hàng", "khuyến mãi", "giảm giá", "ưu đãi", "sale".
6. Câu kết tinh tế — gợi mở cảm xúc, không thúc ép hành động mua.
7. Chỉ viết bằng tiếng Việt.
8. Chỉ xuất câu chuyện — không tiêu đề, không giải thích, không ghi chú ngoài lề."""


CUSTOM_STORY_SYSTEM_PROMPT = """Bạn là AI Creative Storytelling Agent chuyên tạo nội dung marketing trang sức cá nhân hóa.

Nhiệm vụ: Dựa trên mô tả gốc sản phẩm và persona khách hàng, chọn framework storytelling phù hợp, rồi tạo bộ nội dung có thể dùng cho sales, chat tư vấn, lookbook, email và video quảng cáo.

Framework cốt lõi:
1. Hero's Journey: Khách hàng là nhân vật chính, có nhu cầu/khao khát, gặp thiếu hụt, sản phẩm xuất hiện như trợ thủ và giúp tạo chuyển hóa như tự tin, yêu thương, thành công. Phù hợp nội dung truyền cảm hứng, milestone cuộc đời.
2. Golden Circle: Đi từ Why đến How đến What. Tập trung vào ý nghĩa sâu xa, craftsmanship, chất liệu, thiết kế và lý do mua hàng.
3. Emotional Branding: Khơi gợi tình yêu, tự hào, gắn kết, kỷ niệm, phần thưởng bản thân. Tập trung vào cảm giác khi sở hữu hoặc trao tặng sản phẩm.

Rule chọn framework:
- Ưu tiên Hero's Journey khi dịp mua là milestone như sinh nhật, cưới, thăng chức, kỷ niệm; tuổi 25-45; nghề nghiệp có yếu tố nỗ lực/thành tựu; phong cách hiện đại, cá tính, self-expression. Có thể kết hợp Emotional Branding.
- Ưu tiên Golden Circle khi ngân sách cao, sản phẩm cao cấp, khách quan tâm giá trị/đẳng cấp/craftsmanship; nghề nghiệp quản lý/business/người có gu; phong cách tinh tế, sang trọng, tối giản. Có thể kết hợp Emotional Branding.
- Ưu tiên Emotional Branding khi dịp mua là quà tặng tình yêu/gia đình/bạn bè; phong cách nữ tính, lãng mạn, nhẹ nhàng, ấm áp; ngân sách trung bình. Có thể kết hợp Golden Circle.
- Chỉ áp dụng những trường có trong data được cung cấp. Khi có giới tính, tuổi, nghề nghiệp thì dùng để cá nhân hóa bối cảnh, cách xưng hô, insight nghề nghiệp và reasoning. Nếu thiếu trường nào thì không tự suy đoán trường đó.

Ràng buộc bắt buộc:
1. Nội dung phải ngắn gọn, tự nhiên, conversational nhưng vẫn premium và tinh tế.
2. Phù hợp cả văn viết như lookbook/product page và văn nói như chat tư vấn online.
3. Luôn gắn sản phẩm với bối cảnh sử dụng cụ thể, cảm xúc cụ thể và ý nghĩa cá nhân.
4. Không sao chép mô tả gốc một cách máy móc, không dài dòng, không sáo rỗng, không quá quảng cáo.
5. Mỗi mục storytelling nên 5-8 câu, riêng lời chào/lời kết có thể ngắn hơn để tự nhiên.
6. Có thúc đẩy hành động nhẹ nhàng, không dùng giọng ép mua.
7. Chỉ viết bằng tiếng Việt.
8. Không bịa dữ liệu khách hàng không có trong input. Không dùng giới tính để tạo định kiến; chỉ dùng như tín hiệu xưng hô, ngữ cảnh và độ phù hợp tinh tế.

Output đúng format:
### Phần 1: Storytelling
### 1. Tạo kịch bản tư vấn cho sales
### 2. Viết nội dung storytelling cho chat tư vấn
### 3. Tạo nội dung cho lookbook trang sức
### 4. Viết nội dung ngắn gọn cho email marketing
### 5. Soạn email chăm sóc khách hàng sau mua
### 6. Soạn lời chào mở đầu cho chat tư vấn
### 7. Soạn lời kết thúc chat tư vấn nhẹ nhàng
### 8. Viết nội dung kịch bản video quảng cáo
### Phần 2: Framework Used
### Phần 3: Reasoning

Trong Phần 3, giải thích 2-4 dòng, liên hệ trực tiếp với độ tuổi, nghề nghiệp, dịp mua, phong cách và ngân sách."""


def build_features_text(features: dict) -> str:
    if not features or not isinstance(features, dict):
        return ""
    parts = [f"{k}: {v}" for k, v in features.items() if v not in (None, "", "None")]
    return " | ".join(parts)


def _contains_any(value: str, keywords: list[str]) -> bool:
    text = str(value or "").lower()
    return any(keyword in text for keyword in keywords)


def _has_value(value) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    return text not in ("", "—", "nan", "NaN", "None")


def _optional_line(label: str, value) -> str:
    if not _has_value(value):
        return ""
    return f"  • {label}: {value}\n"


def _parse_age(age_value) -> int | None:
    try:
        digits = "".join(ch for ch in str(age_value) if ch.isdigit())
        return int(digits) if digits else None
    except (ValueError, TypeError):
        return None


def _budget_level(budget_value) -> str:
    text = str(budget_value or "").lower().replace(".", "").replace(",", "")
    numbers = [int(num) for num in re.findall(r"\d+", text)]
    amount = max(numbers) if numbers else 0
    if "triệu" in text or "trieu" in text or "m" in text:
        amount *= 1_000_000

    if _contains_any(text, ["cao", "high", "premium", "luxury", "sang", "vip"]):
        return "cao"
    if _contains_any(text, ["trung bình", "medium", "vừa", "mid"]):
        return "trung bình"
    if ("<" in text or "dưới" in text or "duoi" in text) and amount <= 5_000_000:
        return "thấp"
    if amount >= 30_000_000:
        return "cao"
    if amount >= 5_000_000:
        return "trung bình"
    return "chưa rõ"


def select_custom_story_framework(inputs: dict) -> tuple[str, list[str]]:
    """Select framework for the custom storytelling form based on explicit persona inputs."""
    age = _parse_age(inputs.get("age"))
    occupation = inputs.get("occupation", "")
    gender = inputs.get("gender", "")
    style = inputs.get("style", "")
    occasion = " ".join(
        str(inputs.get(key, ""))
        for key in ("purchase_occasion", "persona", "cluster", "persona_ml", "cluster_ml")
    )
    budget = inputs.get("budget", "")
    price = inputs.get("price", 0)
    budget_level = _budget_level(budget)
    if budget_level == "chưa rõ":
        budget_level = _budget_level(price)

    scores = {
        "Hero's Journey": 0,
        "Golden Circle": 0,
        "Emotional Branding": 0,
    }
    reasons = {
        "Hero's Journey": [],
        "Golden Circle": [],
        "Emotional Branding": [],
    }

    if _contains_any(occasion, ["milestone", "sinh nhật", "cưới", "thăng chức", "kỷ niệm", "tốt nghiệp", "tự thưởng"]):
        scores["Hero's Journey"] += 2
        reasons["Hero's Journey"].append("dịp mua là một cột mốc cá nhân")
    if age is not None and 25 <= age <= 45:
        scores["Hero's Journey"] += 1
        reasons["Hero's Journey"].append("độ tuổi nằm trong giai đoạn phát triển bản thân")
    if _contains_any(occupation, ["corporate", "doanh nhân", "entrepreneur", "professional", "chuyên viên", "văn phòng", "bác sĩ", "luật", "kỹ sư", "nhân viên", "chuyên gia"]):
        scores["Hero's Journey"] += 1
        reasons["Hero's Journey"].append("nghề nghiệp gắn với nỗ lực và thành tựu")
    if _contains_any(style, ["hiện đại", "cá tính", "self", "expression", "trẻ trung"]):
        scores["Hero's Journey"] += 1
        reasons["Hero's Journey"].append("phong cách thiên về thể hiện bản thân")

    if budget_level == "cao":
        scores["Golden Circle"] += 2
        reasons["Golden Circle"].append("ngân sách cao cần nhấn mạnh giá trị và đẳng cấp")
    if _contains_any(occupation, ["quản lý", "manager", "business", "doanh nhân", "giám đốc", "founder", "người có gu", "trưởng phòng", "leader", "chủ doanh nghiệp"]):
        scores["Golden Circle"] += 1
        reasons["Golden Circle"].append("nghề nghiệp/gu thẩm mỹ phù hợp cách kể về giá trị")
    if _contains_any(style, ["tinh tế", "sang trọng", "tối giản", "minimal", "luxury", "classic"]):
        scores["Golden Circle"] += 1
        reasons["Golden Circle"].append("phong cách ưu tiên sự tinh tế và craftsmanship")

    if _contains_any(occasion, ["quà", "tặng", "tình yêu", "gia đình", "mẹ", "vợ", "người yêu", "bạn bè", "valentine"]):
        scores["Emotional Branding"] += 2
        reasons["Emotional Branding"].append("dịp mua thiên về quà tặng và kết nối cảm xúc")
    if _contains_any(style, ["nữ tính", "lãng mạn", "nhẹ nhàng", "ấm áp", "thanh lịch"]):
        scores["Emotional Branding"] += 1
        reasons["Emotional Branding"].append("phong cách giàu cảm xúc, mềm mại")
    if age is not None and 18 <= age <= 60 and _contains_any(occasion, ["quà", "tặng", "sinh nhật", "kỷ niệm"]):
        scores["Emotional Branding"] += 1
        reasons["Emotional Branding"].append("độ tuổi và dịp mua phù hợp hướng kể cảm xúc")
    if budget_level == "trung bình":
        scores["Emotional Branding"] += 1
        reasons["Emotional Branding"].append("ngân sách trung bình phù hợp hướng kể gần gũi, cảm xúc")
    top_framework = max(scores, key=scores.get)
    if scores[top_framework] == 0:
        return "Emotional Branding", ["input chưa đủ tín hiệu mạnh, ưu tiên hướng cảm xúc an toàn cho tư vấn trang sức"]

    if scores["Hero's Journey"] > 0 and scores["Emotional Branding"] > 0 and scores["Hero's Journey"] >= scores["Golden Circle"]:
        return "Hero's Journey + Emotional Branding", reasons["Hero's Journey"] + reasons["Emotional Branding"]
    if scores["Golden Circle"] > 0 and scores["Emotional Branding"] > 0:
        return "Golden Circle + Emotional Branding", reasons["Golden Circle"] + reasons["Emotional Branding"]

    return top_framework, reasons[top_framework]


def infer_purchase_occasion(customer: dict) -> str:
    """Infer purchase occasion from customer fields that actually exist in the Excel data."""
    hints = []
    persona = str(customer.get("persona", ""))
    cluster = str(customer.get("cluster", ""))
    persona_ml = str(customer.get("persona_ml", ""))
    cluster_ml = str(customer.get("cluster_ml", ""))
    source_text = " ".join([persona, cluster, persona_ml, cluster_ml]).lower()

    if "cầu hôn" in source_text or "engagement" in source_text:
        hints.append("cầu hôn/cam kết")
    if "kỷ niệm" in source_text or "anniversary" in source_text:
        hints.append("kỷ niệm")
    if "tự thưởng" in source_text or "self" in source_text or "reward" in source_text:
        hints.append("tự thưởng")
    if "quà" in source_text or "gift" in source_text:
        hints.append("quà tặng")

    try:
        if float(customer.get("camp_birthday", 0)) > 0:
            hints.append("sinh nhật")
    except (ValueError, TypeError):
        pass

    try:
        if float(customer.get("camp_anniversary", 0)) > 0:
            hints.append("kỷ niệm")
    except (ValueError, TypeError):
        pass

    try:
        if float(customer.get("camp_selfreward", 0)) > 0:
            hints.append("tự thưởng")
    except (ValueError, TypeError):
        pass

    try:
        if float(customer.get("camp_engagement", 0)) > 0:
            hints.append("cầu hôn/cam kết")
    except (ValueError, TypeError):
        pass

    try:
        birthday_days = float(customer.get("sig_birthday_in_days", 999))
        if birthday_days < 60:
            hints.append(f"sinh nhật gần ({int(birthday_days)} ngày)")
    except (ValueError, TypeError):
        pass

    deduped = []
    for hint in hints:
        if hint not in deduped:
            deduped.append(hint)
    return ", ".join(deduped)


def build_custom_story_inputs(customer: dict, product: dict) -> dict:
    """Build the data-backed input object for the custom multi-format storytelling prompt."""
    detail_desc = product.get("detail_description", "").strip()
    if not detail_desc:
        detail_desc = product.get("description", "").strip()

    return {
        "product_description": detail_desc,
        "product_original_description": product.get("description", "").strip(),
        "product_name": product.get("name", ""),
        "sku": product.get("sku", ""),
        "price": product.get("price", 0),
        "main_stone": product.get("main_stone", ""),
        "features_text": build_features_text(product.get("features", {})),
        "categories": ", ".join(product.get("categories", [])),
        "product_gender": product.get("gender", ""),
        "gender": customer.get("gioi_tinh", ""),
        "age": customer.get("tuoi", ""),
        "occupation": customer.get("nghe_nghiep", ""),
        "persona": customer.get("persona", ""),
        "cluster": customer.get("cluster", ""),
        "persona_ml": customer.get("persona_ml", ""),
        "cluster_ml": customer.get("cluster_ml", ""),
        "style": customer.get("style", ""),
        "budget": customer.get("budget", ""),
        "preferred_type": customer.get("preferred_type", ""),
        "material": customer.get("material", ""),
        "segment": customer.get("segment_rfm_tier", ""),
        "frequency": customer.get("frequency", ""),
        "monetary": customer.get("monetary", ""),
        "avg_unit_price": customer.get("avg_unit_price", ""),
        "purchase_occasion": infer_purchase_occasion(customer),
        "signals": build_context_hints(customer),
    }


def build_context_hints(customer: dict) -> list[str]:
    """
    Translate raw behavioral signals into natural-language observations.
    These are phrased as things 'the advisor observed' — no raw numbers,
    no customer IDs, nothing that would make the customer feel surveilled.
    """
    hints = []

    try:
        if int(customer.get("sig_search_propose", 0)) == 1:
            hints.append("Đang tìm kiếm điều gì đó có ý nghĩa sâu sắc cho một dịp đặc biệt")
    except (ValueError, TypeError):
        pass

    try:
        if float(customer.get("sig_view_engagement_ring", 0)) > 1:
            hints.append("Thể hiện sự quan tâm đặc biệt đến nhẫn — biểu tượng của cam kết bền lâu")
    except (ValueError, TypeError):
        pass

    try:
        if float(customer.get("sig_view_diamond", 0)) > 1:
            hints.append("Đặc biệt chú ý đến vẻ đẹp và giá trị của kim cương")
    except (ValueError, TypeError):
        pass

    try:
        val = float(customer.get("sig_birthday_in_days", 999))
        if val < 60:
            hints.append("Đang trong giai đoạn gần một dịp kỷ niệm hoặc ngày đặc biệt quan trọng")
    except (ValueError, TypeError):
        pass

    try:
        if float(customer.get("camp_selfreward", 0)) > 0:
            hints.append("Có xu hướng tự thưởng cho bản thân vào những dịp đáng nhớ")
    except (ValueError, TypeError):
        pass

    try:
        if float(customer.get("camp_anniversary", 0)) > 1:
            hints.append("Thường tìm kiếm trang sức để ghi dấu những cột mốc quan trọng trong cuộc sống")
    except (ValueError, TypeError):
        pass

    try:
        if float(customer.get("monetary", 0)) > 50_000_000:
            hints.append("Đặt giá trị và chất lượng lên trên cùng — sẵn sàng đầu tư cho điều thực sự xứng đáng")
    except (ValueError, TypeError):
        pass

    try:
        if float(customer.get("frequency", 0)) >= 3:
            hints.append("Đã có kinh nghiệm lựa chọn trang sức, biết rõ mình muốn gì")
    except (ValueError, TypeError):
        pass

    return hints


def build_user_prompt(customer: dict, product: dict, framework_key: str) -> str:
    fw = FRAMEWORKS[framework_key]

    # Product data
    features_text = build_features_text(product.get("features", {}))
    price_formatted = format_price(product.get("price", 0))

    # Use detail_description as primary; fall back to description
    detail_desc = product.get("detail_description", "").strip()
    if not detail_desc:
        detail_desc = product.get("description", "").strip()

    # Customer context — abstract observations, no IDs or raw numbers
    hints = build_context_hints(customer)
    if hints:
        hints_block = "\n" + "\n".join(f"  • {h}" for h in hints)
    else:
        hints_block = "\n  • Chưa có quan sát đặc biệt ngoài thông tin cơ bản trên"

    prompt = f"""FRAMEWORK ÁP DỤNG: {fw['icon']} {fw['name']} — {fw['short_desc']}

━━━ CẤU TRÚC BẮT BUỘC ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{fw['structure']}

━━━ BỨC TRANH VỀ KHÁCH HÀNG ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
(Những gì tư vấn viên quan sát được — phản ánh tinh tế vào câu chuyện, KHÔNG nhắc trực tiếp)

  • Phong cách thẩm mỹ: {customer.get('style', '—')}
  • Loại trang sức quan tâm: {customer.get('preferred_type', '—')}
  • Chất liệu yêu thích: {customer.get('material', '—')}
  • Nhóm khách hàng: {customer.get('segment_rfm_tier', '—')}

Quan sát thêm từ hành vi:{hints_block}

━━━ THÔNG TIN SẢN PHẨM (NGUYÊN LIỆU THÔ — KHÔNG SAO CHÉP) ━━━
  • Tên: {product.get('name', '')}
  • Giá bán: {price_formatted} VND
  • Chất liệu chính: {product.get('main_stone', '')}
  • Thông số kỹ thuật (PHẢI giữ lại ít nhất 1–2 chi tiết này trong story, dệt vào ngôn ngữ cảm xúc): {features_text if features_text else 'Không có thông số'}

Mô tả thương hiệu gốc (VIẾT LẠI hoàn toàn — đây chỉ là tham khảo, không phải để sao chép):
"{product.get('description', '')}"

Chi tiết thiết kế & chất liệu (nguyên liệu cảm xúc chính — khai thác để tạo hình ảnh):
"{detail_desc}"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Viết câu chuyện 3–4 đoạn (180–220 từ) theo đúng cấu trúc {fw['name']} ở trên.
  • Phản ánh bức tranh khách hàng tinh tế — không nhắc số liệu hành vi, không lộ thông tin cá nhân.
  • BẮT BUỘC giữ lại ít nhất 1–2 thông số kỹ thuật cụ thể (số giác cắt, hàm lượng vàng, trọng lượng đá...) và chuyển hóa chúng thành hình ảnh cảm xúc trong câu chuyện."""

    return prompt


def build_custom_story_prompt(inputs: dict) -> str:
    framework_used, reasons = select_custom_story_framework(inputs)
    reason_text = "; ".join(reasons) if reasons else "framework phù hợp nhất với dữ liệu persona đã nhập"
    price_formatted = format_price(inputs.get("price", 0))
    signals = inputs.get("signals", [])
    signals_text = "\n".join(f"  • {signal}" for signal in signals) if signals else "  • Không có tín hiệu bổ sung nổi bật"

    product_lines = ""
    product_lines += _optional_line("Tên sản phẩm", inputs.get("product_name"))
    product_lines += _optional_line("SKU", inputs.get("sku"))
    product_lines += _optional_line("Giá bán", f"{price_formatted} VND" if _has_value(inputs.get("price")) else "")
    product_lines += _optional_line("Nhóm sản phẩm", inputs.get("categories"))
    product_lines += _optional_line("Giới tính sản phẩm", inputs.get("product_gender"))
    product_lines += _optional_line("Đá/chất liệu chính", inputs.get("main_stone"))
    product_lines += _optional_line("Thông số kỹ thuật", inputs.get("features_text"))

    customer_lines = ""
    customer_lines += _optional_line("Giới tính khách hàng", inputs.get("gender"))
    customer_lines += _optional_line("Tuổi", inputs.get("age"))
    customer_lines += _optional_line("Nghề nghiệp", inputs.get("occupation"))
    customer_lines += _optional_line("Persona", inputs.get("persona"))
    customer_lines += _optional_line("Cluster", inputs.get("cluster"))
    customer_lines += _optional_line("Persona ML", inputs.get("persona_ml"))
    customer_lines += _optional_line("Cluster ML", inputs.get("cluster_ml"))
    customer_lines += _optional_line("Phong cách", inputs.get("style"))
    customer_lines += _optional_line("Dịp mua suy ra từ data", inputs.get("purchase_occasion"))
    customer_lines += _optional_line("Ngân sách", inputs.get("budget"))
    customer_lines += _optional_line("Loại trang sức quan tâm", inputs.get("preferred_type"))
    customer_lines += _optional_line("Chất liệu yêu thích", inputs.get("material"))
    customer_lines += _optional_line("Phân khúc RFM", inputs.get("segment"))
    customer_lines += _optional_line("Số lần mua", inputs.get("frequency"))
    customer_lines += _optional_line("Tổng chi tiêu", inputs.get("monetary"))
    customer_lines += _optional_line("Giá trị đơn trung bình", inputs.get("avg_unit_price"))
    product_block = product_lines if product_lines else "  • Không có metadata sản phẩm bổ sung\n"
    customer_block = customer_lines if customer_lines else "  • Không có dữ liệu khách hàng bổ sung\n"

    prompt = f"""Hãy tạo storytelling cá nhân hóa cho một khách hàng cụ thể theo đúng yêu cầu bên dưới.

━━━ INPUT SẢN PHẨM ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{product_block}

Nội dung mô tả gốc/chi tiết sản phẩm từ data:
\"\"\"{inputs.get('product_description', '').strip()}\"\"\"

Mô tả marketing gốc nếu có:
\"\"\"{inputs.get('product_original_description', '').strip()}\"\"\"

━━━ INPUT KHÁCH HÀNG ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{customer_block}

Quan sát/tín hiệu hành vi từ data:
{signals_text}

━━━ FRAMEWORK ĐƯỢC CHỌN THEO RULE ━━━━━━━━━━━━━━━━━━━━━━━
Framework đề xuất: {framework_used}
Lý do tín hiệu: {reason_text}

━━━ YÊU CẦU SÁNG TẠO ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Dựa vào mô tả gốc sản phẩm, nhưng viết lại hoàn toàn bằng ngôn ngữ tự nhiên.
2. Cá nhân hóa theo các trường THỰC SỰ có trong data ở trên, đặc biệt là giới tính, tuổi, nghề nghiệp, phong cách, dịp mua, ngân sách, persona và tín hiệu hành vi nếu có.
3. Nội dung phải có cảm giác được viết riêng cho người này, không chung chung.
4. Mỗi mục nên ngắn gọn, rõ ràng, dễ đọc, dễ nói; phù hợp CRM dynamic script và AI assistant cho sales.
5. Gắn sản phẩm với bối cảnh sử dụng cụ thể, cảm xúc cụ thể và ý nghĩa cá nhân.
6. Giữ tone premium nhưng gần gũi, tinh tế, không phô trương, có chiều sâu cảm xúc nhưng không sến.
7. Tránh giọng quảng cáo quá đà, tránh sáo rỗng, tránh lặp mô tả gốc máy móc.
8. Nếu một trường trong framework rule không tồn tại trong data, bỏ qua trường đó trong nội dung và reasoning.
9. Dùng giới tính khách hàng để tinh chỉnh cách xưng hô/ngữ cảnh một cách tự nhiên; không tạo định kiến hoặc giả định quá mức.

Hãy xuất đúng format:

### Phần 1: Storytelling
### 1. Tạo kịch bản tư vấn cho sales
[5-8 câu]

### 2. Viết nội dung storytelling cho chat tư vấn
[5-8 câu, văn nói tự nhiên]

### 3. Tạo nội dung cho lookbook trang sức
[5-8 câu, văn viết tinh tế]

### 4. Viết nội dung ngắn gọn cho email marketing
[5-8 câu, có subject ngắn nếu phù hợp]

### 5. Soạn email chăm sóc khách hàng sau mua
[5-8 câu, nhẹ nhàng, chăm sóc sau mua]

### 6. Soạn lời chào mở đầu cho chat tư vấn
[2-4 câu, tự nhiên]

### 7. Soạn lời kết thúc chat tư vấn nhẹ nhàng
[2-4 câu, không ép mua]

### 8. Viết nội dung kịch bản video quảng cáo
[5-8 câu, có cảnh/bối cảnh và voice-over ngắn]

### Phần 2: Framework Used
Ghi rõ framework đã dùng: {framework_used}

### Phần 3: Reasoning
Giải thích ngắn gọn 2-4 dòng. Bắt buộc liên hệ trực tiếp với tuổi, nghề nghiệp, dịp mua, phong cách và ngân sách nếu các trường đó có trong data; có thể bổ sung persona, cluster, giới tính, chất liệu yêu thích, preferred type, RFM hoặc tín hiệu hành vi để làm reasoning hữu ích hơn."""

    return prompt


def build_zalo_prompt(customer: dict, product: dict, framework_key: str, story_text: str) -> str:
    """Build a short conversational Zalo message prompt, informed by the already-generated story."""
    fw = FRAMEWORKS[framework_key]
    price_formatted = format_price(product.get("price", 0))
    hints = build_context_hints(customer)
    hints_block = "; ".join(hints) if hints else "Không có quan sát đặc biệt"

    # Pick 1 key emotional angle from the framework to anchor the message
    angle_map = {
        "Hero's Journey": "tự thưởng, ghi nhận bản thân sau hành trình nỗ lực",
        "Golden Circle": "khoảnh khắc đặc biệt, ý nghĩa của tình cảm và cam kết",
        "Emotional Branding": "món quà ý nghĩa dành tặng người thân yêu",
    }
    angle = angle_map.get(framework_key, "khoảnh khắc đặc biệt")

    prompt = f"""Dựa trên câu chuyện dưới đây (đã được viết theo framework {fw['name']}), hãy rút gọn thành 1 tin nhắn Zalo ngắn (3–5 câu) mà nhân viên có thể gửi cho khách.

THÔNG TIN KHÁCH HÀNG:
  • Persona: {customer.get('persona', '—')}
  • Phong cách: {customer.get('style', '—')}
  • Góc cảm xúc phù hợp: {angle}
  • Quan sát thêm: {hints_block}

SẢN PHẨM:
  • Tên: {product.get('name', '')}
  • Giá: {price_formatted} ₫
  • Chất liệu: {product.get('main_stone', '')}

CÂU CHUYỆN GỐC (tham khảo — KHÔNG sao chép, chỉ lấy tinh thần):
\"\"\"{story_text[:500]}\"\"\"

Hãy viết 1 tin nhắn Zalo ngắn gọn, văn nói tự nhiên, thân thiện."""

    return prompt
