from .framework_selector import FRAMEWORKS
from .data_loader import format_price

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


def build_features_text(features: dict) -> str:
    if not features or not isinstance(features, dict):
        return ""
    parts = [f"{k}: {v}" for k, v in features.items() if v not in (None, "", "None")]
    return " | ".join(parts)


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
