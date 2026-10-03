"""
ReAct Agent for MyStorage AI Assistant (Supports LangGraph with automatic fallback)
"""
from typing import List, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from src.tools import search_mystorage_kb, calculate_insurance, get_contact_info

SYSTEM_PROMPT = """Bạn là STOW - Trợ lý AI chính thức của MyStorage (công ty cho thuê kho tự quản và lưu trữ trọn gói hàng đầu tại Việt Nam).
Mục tiêu của bạn là tư vấn chính xác, trung thực, tận tâm cho khách hàng, giúp khách hàng chọn kích thước kho, hiểu rõ bảng giá và các chính sách bảo vệ.

CÁC NGUYÊN TẮC VÀ RÀNG BUỘC CỐT LÕI (BẮT BUỘC TUÂN THỦ 100%):

1. VỀ THÔNG TIN LIÊN HỆ & HOTLINE:
- BẮT BUỘC gọi tool `get_contact_info` khi khách hỏi về số điện thoại, hotline, cách liên hệ khẩn cấp.
- CHỈ cung cấp DUY NHẤT một số hotline chính thức: 028 7770 0117 (+84 28 7770 0117) và email: hello@mystorage.vn.
- TUYỆT ĐỐI KHÔNG tự bịa hoặc suy diễn các số hotline máy lẻ theo ngôn ngữ (như 028 7771 0118, 0119, 0120) hoặc số di động khẩn cấp (0868 208 079). Nếu khách cần hỗ trợ tiếng Hàn, tiếng Nhật hay khẩn cấp, hướng dẫn họ gọi vào số 028 7770 0117 để nhân viên điều phối.

2. VỀ CHÍNH SÁCH BẢO VỆ & BẢO HIỂM:
- MyStorage có 4 gói bảo vệ rõ ràng: Basic (Miễn phí), Silver (50.000đ/tháng), Gold (100.000đ/tháng), và Platinum (200.000đ/tháng).
- TUYỆT ĐỐI KHÔNG phủ nhận sự tồn tại của các gói Silver, Gold, Platinum.
- BẮT BUỘC gọi tool `calculate_insurance(cbm, plan)` khi khách hàng hỏi về số tiền bồi thường cụ thể cho thể tích kho nào đó.
- TUYỆT ĐỐI KHÔNG tự nhân nhẩm hoặc tự đoán mức bồi thường. Nhắc nhở khách rằng với gói Basic, mức bồi hoàn tính theo 500.000đ/m³ (tối đa 10.000.000đ), do đó kho nhỏ (ví dụ 3m³) mức đền tối đa chỉ là 1.500.000đ, không thể nhận 10.000.000đ.

3. VỀ CÁC THÔNG TIN DỊCH VỤ KHÁC:
- Gọi tool `search_mystorage_kb(query)` để tra cứu thông tin chính xác từ tài liệu chính thức (llms.txt) trước khi trả lời về giá thuê, địa chỉ kho, giờ mở cửa.
- Trả lời bằng giọng điệu lịch sự, chuyên nghiệp, tiếng Việt tự nhiên và thân thiện.
"""

TOOLS = [search_mystorage_kb, calculate_insurance, get_contact_info]
TOOL_MAP = {t.name: t for t in TOOLS}


class FallbackReActAgent:
    """
    Lightweight, highly reliable ReAct agent runner matching LangGraph's interface.
    """
    def __init__(self, model, tools, system_prompt: str, max_iterations: int = 5):
        self.model = model.bind_tools(tools)
        self.tools = tools
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations

    def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        messages = list(state.get("messages", []))
        if not messages or not isinstance(messages[0], SystemMessage):
            messages.insert(0, SystemMessage(content=self.system_prompt))

        for _ in range(self.max_iterations):
            response = self.model.invoke(messages)
            messages.append(response)

            if not getattr(response, "tool_calls", None):
                break

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call.get("args", {})
                call_id = tool_call.get("id", "call_1")

                tool_fn = TOOL_MAP.get(tool_name)
                if tool_fn:
                    try:
                        observation = tool_fn.invoke(tool_args)
                    except Exception as err:
                        observation = f"Lỗi khi thực thi tool {tool_name}: {err}"
                else:
                    observation = f"Tool '{tool_name}' không tồn tại."

                messages.append(ToolMessage(content=str(observation), tool_call_id=call_id))

        return {"messages": messages}


def create_mystorage_agent(llm):
    """
    Creates a compiled LangGraph ReAct agent if available and compatible,
    supporting both 'prompt' (LangGraph >=0.2) and 'state_modifier' (LangGraph 0.1),
    with robust FallbackReActAgent ensuring 100% uptime.
    """
    try:
        import inspect
        from langgraph.prebuilt import create_react_agent
        
        params = inspect.signature(create_react_agent).parameters
        if "prompt" in params:
            return create_react_agent(model=llm, tools=TOOLS, prompt=SYSTEM_PROMPT)
        elif "state_modifier" in params:
            return create_react_agent(model=llm, tools=TOOLS, state_modifier=SYSTEM_PROMPT)
        elif "messages_modifier" in params:
            return create_react_agent(model=llm, tools=TOOLS, messages_modifier=SYSTEM_PROMPT)
        else:
            return create_react_agent(model=llm, tools=TOOLS)
    except Exception:
        return FallbackReActAgent(
            model=llm,
            tools=TOOLS,
            system_prompt=SYSTEM_PROMPT
        )
