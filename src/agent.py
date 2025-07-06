from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from tools import query_neo4j_database, get_adverse_events, read_financial_report
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Annotated, List
import operator


def get_agent_executor():
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0)
    tools = [query_neo4j_database, get_adverse_events, read_financial_report]

    agent = create_agent(llm, tools)
    graph = StateGraph(AgentState)
    graph.add_node("agent", lambda state: agent_node(state, agent, "agent"))
    graph.add_node("tools", lambda state: tool_node(state, tools))
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue)
    graph.add_edge("tools", "agent")

    memory = MemorySaver()
    agent_executor = graph.compile(checkpointer=memory)
    return agent_executor


class AgentState(TypedDict):
    messages: Annotated[list, operator.add]


def create_agent(llm, tools):
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful assistant. You have access to a set of tools. Use them to answer the user's questions accurately.",
            ),
            ("placeholder", "{messages}"),
        ]
    )
    return prompt | llm.bind_tools(tools)


def agent_node(state, agent, name):
    result = agent.invoke(state)
    return {"messages": [result]}


def tool_node(state, tools):
    tool_calls = state["messages"][-1].tool_calls
    messages = []
    for tool_call in tool_calls:
        tool_name = tool_call["name"]
        tool = {t.name: t for t in tools}[tool_name]
        tool_output = tool.invoke(tool_call["args"])
        messages.append(
            ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"])
        )
    return {"messages": messages}


def should_continue(state):
    if (
        isinstance(state["messages"][-1], AIMessage)
        and state["messages"][-1].tool_calls
    ):
        return "tools"
    else:
        return END
