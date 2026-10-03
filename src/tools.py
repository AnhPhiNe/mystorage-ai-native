"""
Deterministic tools for MyStorage AI Agent to prevent hallucinations.
"""
from pathlib import Path
from typing import Optional
from langchain_core.tools import tool

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
LLMS_FILE = DATA_DIR / "llms.txt"


def _load_kb() -> str:
    if LLMS_FILE.exists():
        return LLMS_FILE.read_text(encoding="utf-8")
    return ""


@tool
def search_mystorage_kb(query: str) -> str:
    """
    Search the official MyStorage knowledge base (llms.txt) for accurate factual information
    about services, prices, locations, facilities, FAQ, operating hours, and policies.
    Use this tool whenever a customer asks about facts, services, or locations.
    """
    kb = _load_kb()
    if not kb:
        return "Knowledge base not found."

    sections = kb.split("\n## ")
    matches = []
    q_words = [w.lower() for w in query.split() if len(w) > 1]

    for section in sections:
        sec_lower = section.lower()
        score = sum(1 for w in q_words if w in sec_lower)
        if score > 0:
            matches.append((score, section))

    matches.sort(key=lambda x: x[0], reverse=True)
    if matches:
        top_sections = [m[1] for m in matches[:3]]
        return "\n\n---\n\n".join(top_sections)

    return kb[:2000]


@tool
def calculate_insurance(cbm: float, plan: str = "basic") -> str:
    """
    Calculate the exact insurance coverage limit and monthly cost for a given storage volume (in CBM/m³) and plan tier.
    Available plans: 'basic', 'silver', 'gold', 'platinum'.
    Always use this tool when the customer asks about insurance compensation, coverage limits, or protection tiers.
    """
    plan_clean = plan.strip().lower()

    if cbm <= 0:
        return "Lỗi: Thể tích kho (CBM / m³) phải lớn hơn 0."

    plans = {
        "basic": {
            "name": "Basic (Cơ bản)",
            "fee_vnd": 0,
            "formula": "500.000 VNĐ / m³, tối đa 10.000.000 VNĐ",
            "coverage_vnd": min(cbm * 500_000, 10_000_000)
        },
        "silver": {
            "name": "Silver (Bạc)",
            "fee_vnd": 50_000,
            "formula": "Cố định 25.000.000 VNĐ",
            "coverage_vnd": 25_000_000
        },
        "gold": {
            "name": "Gold (Vàng)",
            "fee_vnd": 100_000,
            "formula": "Cố định 50.000.000 VNĐ",
            "coverage_vnd": 50_000_000
        },
        "platinum": {
            "name": "Platinum (Bạch kim)",
            "fee_vnd": 200_000,
            "formula": "Cố định 100.000.000 VNĐ",
            "coverage_vnd": 100_000_000
        }
    }

    if plan_clean not in plans:
        available = ", ".join([f"'{k}'" for k in plans.keys()])
        return (
            f"Gói '{plan}' không hợp lệ. MyStorage có 4 gói bảo vệ:\n"
            f"- Basic: Miễn phí, bồi hoàn 500.000đ/m³, tối đa 10.000.000đ\n"
            f"- Silver: 50.000đ/tháng, bồi hoàn tối đa 25.000.000đ\n"
            f"- Gold: 100.000đ/tháng, bồi hoàn tối đa 50.000.000đ\n"
            f"- Platinum: 200.000đ/tháng, bồi hoàn tối đa 100.000.000đ\n"
            f"Vui lòng chọn một trong các gói: {available}."
        )

    info = plans[plan_clean]
    coverage = info["coverage_vnd"]
    fee = info["fee_vnd"]
    name = info["name"]

    res = (
        f"KẾT QUẢ TÍNH BẢO HIỂM MYSTORAGE:\n"
        f"- Thể tích kho: {cbm} m³ (CBM)\n"
        f"- Gói bảo vệ: {name}\n"
        f"- Phí hàng tháng: {fee:,.0f} VNĐ/tháng ({'Miễn phí' if fee == 0 else 'Trả phí'})\n"
        f"- Mức bồi thường tối đa: {coverage:,.0f} VNĐ\n"
        f"- Công thức áp dụng: {info['formula']}\n"
    )
    if plan_clean == "basic":
        res += (
            f"\n* Lưu ý quan trọng: Với gói Basic, bồi hoàn tính theo 500.000 VNĐ/m³ "
            f"({cbm} x 500.000 = {cbm * 500_000:,.0f} VNĐ, trần tối đa là 10.000.000 VNĐ)."
        )
    return res


@tool
def get_contact_info() -> str:
    """
    Get the official verified contact channels and hotline for MyStorage.
    Always call this tool when the customer asks for phone numbers, hotlines, emails, or emergency contacts.
    """
    return (
        "THÔNG TIN LIÊN HỆ CHÍNH THỨC CỦA MYSTORAGE:\n"
        "- Hotline duy nhất: 028 7770 0117 (+84 28 7770 0117) - Hỗ trợ cả Tiếng Việt và Tiếng Anh.\n"
        "- Email: hello@mystorage.vn\n"
        "- Thời gian hỗ trợ: Thứ Hai – Thứ Bảy: 9:00 – 18:00 (Chủ Nhật hỗ trợ từ xa).\n"
        "- Trụ sở chính: 375 Võ Nguyên Giáp, Phường An Khánh, TP. Thủ Đức, TP. Hồ Chí Minh.\n"
        "- Website / Đặt trực tuyến: https://booking.mystorage.vn/\n"
        "\n* QUY TẮC AN TOÀN QUAN TRỌNG: MyStorage KHÔNG có các số hotline máy lẻ theo ngôn ngữ "
        "(như 028 7771 0118, 0119, 0120) và KHÔNG có số di động khẩn cấp 0868 208 079. "
        "Mọi cuộc gọi hỗ trợ đều được tiếp nhận qua đầu số chính thức 028 7770 0117."
    )
