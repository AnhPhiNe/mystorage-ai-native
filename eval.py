"""
Evaluation Benchmark: Comparing Naive/Baseline LLM vs Grounded LangGraph Agent
Directly addresses finding 1 (Insurance/Math) and finding 2 (Hotline/Contacts).
"""
import os
import sys
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from src.config import get_llm
from src.agent import create_mystorage_agent

load_dotenv()

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def to_str(content):
    if isinstance(content, list):
        return "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in content)
    return str(content or "")


def run_evaluation(provider="deepinfra", model_name="deepseek-ai/DeepSeek-V4.1-Flash", api_key=None):
    print("=" * 70)
    print("🚀 BẮT ĐẦU CHẠY BENCHMARK ĐÁNH GIÁ (EVALUATION SET)")
    print(f"Provider: {provider} | Model: {model_name}")
    print("=" * 70)

    try:
        llm = get_llm(provider=provider, model_name=model_name, api_key=api_key)
    except Exception as e:
        print(f"❌ Không thể khởi tạo LLM: {e}")
        return

    agent = create_mystorage_agent(llm)

    test_cases = [
        {
            "id": "TC-01",
            "name": "Chính sách Bảo hiểm & Phép tính Bồi thường kho 3m³",
            "query": "Kho 3 m³ dùng gói Basic được bồi thường tối đa bao nhiêu? MyStorage có gói bảo hiểm Silver, Gold, Platinum không?",
            "assertions": [
                ("Chứa gói Silver, Gold, Platinum", lambda text: all(x in text.lower() for x in ["silver", "gold", "platinum"])),
                ("Tính đúng 1.500.000 VNĐ cho kho 3m³ (Basic)", lambda text: "1.500.000" in text or "1,500,000" in text or "1.5 triệu" in text),
                ("Không khẳng định đền 10 triệu cho kho 3m³", lambda text: not ("tối đa là 10.000.000 vnđ ạ" in text.lower() or "được bồi thường 10.000.000" in text.lower()))
            ]
        },
        {
            "id": "TC-02",
            "name": "Số hotline liên hệ khẩn cấp và các đường dây nóng",
            "query": "tui muốn liên hệ gấp với bên stow thì nên dùng đường dây nào vậy hãy liệt kê các đường dây nóng mà cậu có đi",
            "assertions": [
                ("Cung cấp đúng hotline chính thức 028 7770 0117", lambda text: "028 7770 0117" in text or "02877700117" in text),
                ("Không cung cấp số 028 7771 0118 làm hotline tiếng Việt", lambda text: "tiếng việt: `028 7771 0118`" not in text.lower() and "tiếng việt: 028 7771 0118" not in text.lower()),
                ("Khẳng định chỉ có duy nhất 1 hotline chính thức", lambda text: "duy nhất" in text.lower() or "chỉ có" in text.lower())
            ]
        }
    ]

    for tc in test_cases:
        print(f"\n📌 TEST CASE: {tc['id']} - {tc['name']}")
        print(f"❓ Câu hỏi: \"{tc['query']}\"")
        print("-" * 50)

        # 1. Chạy với Baseline (LLM không có Tools - mô phỏng STOW hiện tại)
        print("🤖 [1. BASELINE - Không có Tools (STOW gốc)]:")
        baseline_prompt = [
            SystemMessage(content="Bạn là trợ lý AI STOW của công ty MyStorage."),
            HumanMessage(content=tc["query"])
        ]
        base_resp = to_str(llm.invoke(baseline_prompt).content)
        print(base_resp[:300] + "...\n")

        # 2. Chạy với Grounded Agent (LangGraph + Deterministic Tools)
        print("🛡️ [2. GROUNDED AGENT - LangGraph + Tools]:")
        agent_resp = agent.invoke({"messages": [HumanMessage(content=tc["query"])]})
        agent_text = to_str(agent_resp["messages"][-1].content)
        print(agent_text[:300] + "...\n")

        # 3. Kiểm tra Assertions
        print("📊 [KẾT QUẢ KIỂM THỬ ĐỘ CHÍNH XÁC]:")
        for desc, check_fn in tc["assertions"]:
            pass_agent = check_fn(agent_text)
            status = "✅ PASS" if pass_agent else "❌ FAIL"
            print(f"  - {status}: {desc}")

    print("\n" + "=" * 70)
    print("🏁 HOÀN TẤT ĐÁNH GIÁ")
    print("=" * 70)


if __name__ == "__main__":
    provider = sys.argv[1] if len(sys.argv) > 1 else "deepinfra"
    run_evaluation(provider=provider)
