import streamlit as st
from agent import get_agent_executor
from evaluation import evaluate_response
from langchain_core.messages import HumanMessage, AIMessage
import uuid
import tiktoken


def count_tokens(text: str) -> int:
    """Count tokens in text"""
    try:
        encoding = tiktoken.encoding_for_model("gpt-4")
        return len(encoding.encode(str(text)))
    except:
        return len(str(text)) // 4  # Rough estimate


# Initialize session state FIRST - before any UI operations
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

st.title("Grünenthal AI Agent")
st.sidebar.title("Token Monitor")

# Clear conversation button
if st.sidebar.button("🗑️ Clear Conversation"):
    st.session_state.messages = []
    st.session_state.conversation_history = []
    st.session_state.thread_id = str(uuid.uuid4())
    st.rerun()

# Display conversation length
if st.session_state.conversation_history:
    st.sidebar.metric(
        "Conversation Length", f"{len(st.session_state.conversation_history)} messages"
    )

agent_executor = get_agent_executor()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask a question"):
    # Token monitoring
    prompt_tokens = count_tokens(prompt)
    st.sidebar.metric("Current Prompt Tokens", prompt_tokens)

    # Add user message to both display and conversation history
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.conversation_history.append(HumanMessage(content=prompt))

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        config = {"configurable": {"thread_id": st.session_state.thread_id}}

        # Send entire conversation history to the agent
        response = agent_executor.invoke(
            {"messages": st.session_state.conversation_history},
            config=config,
        )
        assistant_response = response["messages"][-1].content

        # Add assistant response to conversation history
        st.session_state.conversation_history.append(
            AIMessage(content=assistant_response)
        )

        # Token monitoring for response
        response_tokens = count_tokens(assistant_response)

        # Calculate total conversation tokens
        total_conversation_tokens = sum(
            count_tokens(msg.content) for msg in st.session_state.conversation_history
        )

        st.sidebar.metric("Response Tokens", response_tokens)
        st.sidebar.metric("Total Conversation Tokens", total_conversation_tokens)

        # Warning if tokens are high
        if total_conversation_tokens > 5000:
            st.sidebar.warning(
                f"⚠️ High conversation token usage: {total_conversation_tokens}"
            )
        elif total_conversation_tokens > 10000:
            st.sidebar.error(
                f"Very high conversation token usage: {total_conversation_tokens}"
            )

        st.markdown(assistant_response)

        eval_result = evaluate_response(prompt, assistant_response)
        with st.expander("Evaluation"):
            st.write(eval_result)

    # Add assistant response to display messages
    st.session_state.messages.append(
        {"role": "assistant", "content": assistant_response}
    )
