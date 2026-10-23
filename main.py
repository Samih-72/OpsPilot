
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import ToolMessage,HumanMessage,AIMessage,SystemMessage
from tools import get_order,get_return_policy,get_money_collected,get_monthly_collection_comparison,get_customer,get_payment_health_summary,get_total_orders
from research_tools import web_search
import streamlit as st
import os

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=os.getenv("GROQ_API_KEY")
)

llm_with_tools = llm.bind_tools([get_order,get_return_policy,get_money_collected,get_monthly_collection_comparison,get_customer,web_search,get_payment_health_summary,get_total_orders])

system_message = SystemMessage(
    content="""
    You are a customer support assistant for an e-commerce store.

    Follow these rules:
    1. Use available tools when you need order or policy information.
    2.Use the web_search tool when the user asks for public web research, market trends, competitor information, or industry strategies. Base web research answers on the tool results, and never invent sources or findings.
    3. Only provide information supported by the conversation or tool results.
    4. Never claim you have performed an action unless a tool confirms it.
    5. You can only perform actions or provide services that are directly supported by your available tools.
    6. Never claim that you can track shipments, set reminders, issue refunds, process exchanges, send notifications, or perform any other action unless a tool explicitly provides that capability.
    7. If you do not have enough information, explain what is missing.
    8. Be polite, clear, and concise.
    9. Never assume an order has or has not been delivered
    unless the tool result explicitly confirms it.

    10. Do not determine refund or return eligibility
     from order status alone. Explain the return policy
     and direct the customer to the store for confirmation.

    11. Never invent order details, delivery dates,
    refund eligibility, or completed actions.
    12.When using web_search:
        1. Base research claims on the returned search results.
        2. Include the source title and URL for important claims.
        3. Distinguish verified findings from suggestions or hypotheses.
        4. Never invent studies, statistics, citations, or source URLs.
        5. Organize the answer with clear headings and actionable recommendations.
        6. If the search results are insufficient, explicitly explain the limitations.
    """
)
chat_history =[system_message]






def handle_customer_query(user_query):
    activity = []
    chat_history.append(HumanMessage(content=user_query))

    for _ in range(5):
        response = llm_with_tools.invoke(chat_history[-6:])
        chat_history.append(response)

        # If the AI has finished, return its answer immediately.
        if not response.tool_calls:
            answer = response.content

            if not answer or not answer.strip():
                answer = (
                    "I can't issue a refund directly because "
                    "refund processing is not available in my tools. "
                    "I can check your order information and explain "
                    "the store's return policy."
                )

            return {
                "answer": answer,
                "activity": activity,
            }

        # Execute the tools requested by the AI.
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]

            if tool_name == "get_order":
                activity.append("Checking order information...")
                result = get_order.invoke(tool_call["args"])

            elif tool_name == "get_return_policy":
                activity.append("Retrieving return policy...")
                result = get_return_policy.invoke(tool_call["args"])
            elif tool_name=="get_money_collected":
                activity.append("Checking payment collections...")
                result=get_money_collected.invoke(tool_call["args"])
            elif tool_name =="get_monthly_collection_comparison":
                activity.append("Checking payment collections...")
                result=get_monthly_collection_comparison.invoke(tool_call["args"])
            elif tool_name == "get_customer":
                activity.append("Looking up customer information...")
                result = get_customer.invoke(tool_call["args"])
            elif tool_name == "web_search":
                activity.append("Researching the web...")
                result = web_search.invoke(tool_call["args"])
            elif tool_call["name"] == "get_payment_health_summary":
                result = get_payment_health_summary.invoke(
                tool_call["args"])
            
            
            elif tool_name == "get_total_orders":
                activity.append("Counting total orders in the uploaded dataset...")

                uploaded_data = st.session_state.get("uploaded_data", {})
                orders_df = uploaded_data.get("orders.csv")

                if orders_df is not None:
                    result = get_total_orders.func(orders_df=orders_df)
                else:
                    result = get_total_orders.invoke(tool_call["args"])



            else:
                result = "This action is not supported."
                activity.append(
                    f"Unsupported tool requested: {tool_name}"
                )

            tool_message = ToolMessage(
                content=str(result),
                tool_call_id=tool_call["id"],
            )
            chat_history.append(tool_message)

    # Stop safely if the agent reaches the five-round limit.
    return {
        "answer": (
            "I couldn't complete your request after several attempts. "
            "Please try asking in a different way."
        ),
        "activity": activity,
    }



if __name__ == "__main__":
    while True:
        user_query = input("Customer: ")

        if user_query.lower() == "exit":
            break

        handle_customer_query(user_query)
