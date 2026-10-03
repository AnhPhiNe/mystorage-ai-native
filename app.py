"""
Streamlit Web App: MyStorage AI Assistant (AI-Native Grounded Agent)
Prototype solving Hallucinations for MyStorage AI Sales Agent (STOW).
"""
import streamlit as st
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from src.config import get_llm
from src.agent import create_mystorage_agent

load_dotenv()

st.set_page_config(
    page_title="MyStorage AI Agent (STOW 2.0)",
    page_icon="📦",
    layout="wide"
)

st.title("📦 MyStorage AI Assistant (STOW 2.0)")
st.caption("AI-Native Prototype giải quyết triệt để vấn đề Ảo giác (Hallucination) cho STOW Assistant")

# Sidebar Configuration
with st.sidebar:
    st.header("⚡ LLM Engine & Architecture")
    
    provider = "DeepInfra"
    model_name = "deepseek-ai/DeepSeek-V4.1-Flash"
    
    # Check secrets or environment
    env_key = ""
    if hasattr(st, "secrets") and "DEEPINFRA_API_KEY" in st.secrets:
        env_key = st.secrets["DEEPINFRA_API_KEY"]
    if not env_key:
        env_key = os.getenv("DEEPINFRA_API_KEY", "")

    st.markdown(
        """
        * **Provider:** DeepInfra
        * **Model:** `DeepSeek-V4.1-Flash`
        * **Pattern:** LangGraph ReAct + Tools
        * **Knowledge Base:** Grounded `/llms.txt`
        """
    )

    if env_key:
        st.success("🟢 **Sẵn sàng thử nghiệm** (API Key đã được cấu hình)")
        api_key = env_key
    else:
        api_key = st.text_input("DeepInfra API Key", type="password", placeholder="Nhập API key tại đây...")

    st.markdown("---")
    st.subheader("🎯 1-Click Demo Finding Test Cases")
    st.caption("Các test case bắt lỗi ảo giác của STOW gốc theo bài Audit:")

    quick_prompt = None
    if st.button("🧪 Case 1: Kho 3m³ bảo hiểm Basic đền bao nhiêu? Có Silver/Gold không?", use_container_width=True):
        quick_prompt = "Kho 3 m³ dùng gói Basic được bồi thường tối đa bao nhiêu? MyStorage có gói bảo hiểm Silver, Gold, Platinum không?"

    if st.button("🧪 Case 2: Hỏi hotline gấp & các đường dây nóng?", use_container_width=True):
        quick_prompt = "tui muốn liên hệ gấp với bên stow thì nên dùng đường dây nào vậy hãy liệt kê các đường dây nóng mà cậu có đi"

    if st.button("🧪 Case 3: Hỏi địa điểm kho & dịch vụ Full-Service", use_container_width=True):
        quick_prompt = "MyStorage có những địa điểm kho nào tại TP.HCM và dịch vụ Full-Service là gì?"

    st.markdown("---")
    if st.button("🧹 Xóa lịch sử trò chuyện", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Xin chào anh/chị! Em là STOW 2.0 - Trợ lý AI của MyStorage. Em có thể hỗ trợ anh/chị chọn kích thước kho, tra cứu bảng giá, chính sách bảo vệ hoặc đặt lịch lưu trữ đồ đạc ạ!", "traces": []}
    ]

# Display conversation
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("traces"):
            with st.expander("🛠️ Tool Traces & Grounded Data (Đã gọi Tool gì?)"):
                for t in msg["traces"]:
                    st.code(f"Tool: {t['tool']}\nInput: {t['args']}\nOutput:\n{t['output']}", language="yaml")

# Handle input
user_input = st.chat_input("Hỏi về kho, kích thước, hotline, hoặc gói bảo hiểm...")
if quick_prompt:
    user_input = quick_prompt

if user_input:
    if not api_key:
        st.error(f"Vui lòng nhập {provider} API Key trong thanh bên trái để trò chuyện.")
    else:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input, "traces": []})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Đang tra cứu dữ liệu thực tế và tính toán..."):
                try:
                    llm = get_llm(provider=provider, model_name=model_name, api_key=api_key)
                    agent = create_mystorage_agent(llm)

                    # Build conversation messages for agent
                    input_msgs = []
                    for m in st.session_state.messages:
                        if m["role"] == "user":
                            input_msgs.append(HumanMessage(content=m["content"]))
                        elif m["role"] == "assistant":
                            input_msgs.append(AIMessage(content=m["content"]))

                    # Execute agent
                    result = agent.invoke({"messages": input_msgs})
                    
                    # Extract tool calls traces and final answer
                    traces = []
                    final_answer = ""
                    for msg in result["messages"]:
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            for tc in msg.tool_calls:
                                traces.append({
                                    "tool": tc["name"],
                                    "args": tc.get("args", {}),
                                    "output": ""
                                })
                        elif isinstance(msg, ToolMessage):
                            if traces:
                                traces[-1]["output"] = str(msg.content)
                        elif isinstance(msg, AIMessage) and msg.content:
                            c = msg.content
                            if isinstance(c, list):
                                final_answer = "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in c)
                            else:
                                final_answer = str(c)

                    if not final_answer and result["messages"]:
                        c = result["messages"][-1].content
                        if isinstance(c, list):
                            final_answer = "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in c)
                        else:
                            final_answer = str(c)

                    st.markdown(final_answer)
                    if traces:
                        with st.expander("🛠️ Tool Traces & Grounded Data (Đã gọi Tool gì?)"):
                            for t in traces:
                                st.code(f"Tool: {t['tool']}\nInput: {t['args']}\nOutput:\n{t['output']}", language="yaml")

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": final_answer,
                        "traces": traces
                    })

                except Exception as e:
                    st.error(f"Đã xảy ra lỗi khi thực thi Agent: {e}")
