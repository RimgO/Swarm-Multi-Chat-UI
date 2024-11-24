from swarm import Swarm, Agent
from swarm.repl import run_demo_loop
from tavily import TavilyClient
from loguru import logger

from dotenv import load_dotenv
import os
load_dotenv()

import time
import streamlit as st
from openai import OpenAI

AGENTS = {
    "聴き上手なカウンセラー": {
        "description": "共感的な聴き手として、あなたの話に寄り添います",
        "model": "phi3:mini",
        "color": "#2E7D32",
        "max_tokens": 100,
        "system_prompt": "あなたは共感的なカウンセラーです。回答は必ず100文字以内で簡潔に返してください。"
    },
    "的確なアドバイザー": {
        "description": "問題解決のための具体的なアドバイスを提供します",
        "model": "phi3:mini",
        "color": "#1976D2",
        "max_tokens": 100,
        "system_prompt": "あなたは的確なアドバイザーです。回答は必ず100文字以内で簡潔に返してください。"
    },
    "心理分析の専門家": {
        "description": "心理学的な視点から状況を分析します",
        "model": "phi3:mini",
        "color": "#7B1FA2",
        "max_tokens": 100,
        "system_prompt": "あなたは心理分析の専門家です。回答は必ず100文字以内で簡潔に返してください。"
    }
}

st.set_page_config(page_title="Ollama-Chatbot", page_icon="🤖", layout="wide")

client = OpenAI(
    base_url='http://localhost:11434/v1/',
    api_key='dummy'
)

chat_model = "phi3:mini"

if "authenticated_users" not in st.session_state:
    st.session_state.authenticated_users = []
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "messages" not in st.session_state:
    st.session_state.messages = {}

st.sidebar.title("ユーザー認証")
username = st.sidebar.text_input("ユーザー名")
password = st.sidebar.text_input("パスワード", type="password")
if st.sidebar.button("ログイン"):
    if username and password:
        if username not in st.session_state.authenticated_users:
            st.session_state.authenticated_users.append(username)
            st.session_state.messages[username] = {}
        st.session_state.current_user = username
        st.sidebar.success(f"{username}としてログインしました。")
        st.rerun()
    else:
        st.sidebar.error("ユーザー名とパスワードを入力してください。")

st.sidebar.title("ログイン中のユーザー")
for user in st.session_state.authenticated_users:
    if st.sidebar.button(user, key=f"user_{user}"):
        st.session_state.current_user = user
        st.rerun()

st.sidebar.title("アクティブエージェント")

def share_context_between_agents(current_user, new_agent):
    """エージェント間でコンテキストを共有する関数"""
    active_agents = [agent for agent in AGENTS.keys()
                    if agent in st.session_state.messages.get(current_user, {})]

    if len(active_agents) > 1:
        # 重複を避けるために一時的にすべてのメッセージを集める
        all_messages = {}
        for agent in active_agents:
            if agent != new_agent:  # 新しく選択したエージェント以外から収集
                messages = st.session_state.messages[current_user][agent]
                for msg in messages:
                    msg_key = f"{msg['role']}:{msg['content']}"
                    all_messages[msg_key] = msg

        # 時系列順を維持するためにリストに変換
        unique_messages = list(all_messages.values())

        # 最新の3つのメッセージのみを取得
        latest_context = unique_messages[-3:] if len(unique_messages) > 3 else unique_messages

        # 新しく選択したエージェントにコンテキストを追加
        if latest_context:
            st.session_state.messages[current_user][new_agent] = latest_context.copy()
            return True
    return False

# エージェント選択ボタン処理
for agent_name, agent_info in AGENTS.items():
    is_active = (st.session_state.current_user and
                st.session_state.current_user in st.session_state.messages and
                agent_name in st.session_state.messages[st.session_state.current_user])

    col1, col2 = st.sidebar.columns([3, 1])
    with col1:
        background_color = agent_info['color'] if is_active else '#2F3336'  # ダークグレー
        st.markdown(
            f"<div style='padding:10px;border-radius:5px;background-color:{background_color}'>"
            f"<strong style='color:white'>{agent_name}</strong><br/>"
            f"<small style='color:#E0E0E0'>{agent_info['description']}</small>"
            "</div>",
            unsafe_allow_html=True
        )
    with col2:
        if st.button("選択", key=f"select_{agent_name}"):
            if st.session_state.current_user:
                if st.session_state.current_user in st.session_state.messages:
                    if agent_name not in st.session_state.messages[st.session_state.current_user]:
                        st.session_state.messages[st.session_state.current_user][agent_name] = []
                        # 新しいエージェントが選択された時にコンテキストを共有
                        if share_context_between_agents(st.session_state.current_user, agent_name):
                            st.toast(f"他のエージェントとコンテキストを共有しました", icon="✨")
                else:
                    st.session_state.messages[st.session_state.current_user] = {agent_name: []}
            st.rerun()


if st.session_state.current_user:
    st.sidebar.title("コンテキスト管理")

    # ユーザー間コンテキストマージのUI
    st.sidebar.subheader("ユーザー間コンテキスト共有")

    # 自分以外のユーザーのチェックボックス
    selected_users = []
    for user in st.session_state.authenticated_users:
        if user != st.session_state.current_user:
            if st.sidebar.checkbox(f"{user}のコンテキスト", key=f"merge_{user}"):
                selected_users.append(user)

    def summarize_context(messages):
        """コンテキストを要約する関数"""
        if not messages:
            return []

        # 最新の3つのメッセージを抽出
        recent_messages = messages[-3:]
        return recent_messages

    if st.sidebar.button("選択したユーザーとコンテキストを共有", disabled=len(selected_users) == 0):
        if selected_users:
            # 現在のユーザーのコンテキストを取得
            current_user_context = {}
            for agent in st.session_state.messages.get(st.session_state.current_user, {}):
                current_user_context[agent] = summarize_context(
                    st.session_state.messages[st.session_state.current_user][agent]
                )

            # 選択されたユーザーのコンテキストを取得して統合
            for selected_user in selected_users:
                if selected_user in st.session_state.messages:
                    for agent in st.session_state.messages[selected_user]:
                        # エージェントが現在のユーザーにない場合は初期化
                        if agent not in st.session_state.messages[st.session_state.current_user]:
                            st.session_state.messages[st.session_state.current_user][agent] = []

                        # 選択されたユーザーのコンテキストを要約
                        selected_user_context = summarize_context(
                            st.session_state.messages[selected_user][agent]
                        )

                        # 重複を避けながらマージ
                        existing_messages = set(
                            f"{msg['role']}:{msg['content']}"
                            for msg in st.session_state.messages[st.session_state.current_user][agent]
                        )

                        for msg in selected_user_context:
                            msg_key = f"{msg['role']}:{msg['content']}"
                            if msg_key not in existing_messages:
                                st.session_state.messages[st.session_state.current_user][agent].append(msg)
                                existing_messages.add(msg_key)

            st.sidebar.success(f"選択したユーザー ({', '.join(selected_users)}) とコンテキストを共有しました")
            st.rerun()

if st.session_state.current_user:
    st.title(f"こんにちは、{st.session_state.current_user}さん")

    active_agents = [agent for agent in AGENTS.keys()
                    if agent in st.session_state.messages.get(st.session_state.current_user, {})]

    if active_agents:
        cols = st.columns(len(active_agents))
        for idx, (agent_name, col) in enumerate(zip(active_agents, cols)):
            with col:
                st.subheader(f"{agent_name} 🤖")

                for message in st.session_state.messages[st.session_state.current_user][agent_name]:
                    with st.chat_message(message["role"]):
                        st.write(f"{message['content']}")

                user_input = st.chat_input(f"メッセージを入力 ({agent_name})", key=f"input_{agent_name}")
                if user_input:
                    st.session_state.messages[st.session_state.current_user][agent_name].append(
                        {"role": "user", "content": user_input}
                    )

                    with st.chat_message("assistant"):
                        messages = [
                            {"role": "system", "content": AGENTS[agent_name]["system_prompt"]},
                            *[{"role": m["role"], "content": m["content"]}
                            for m in st.session_state.messages[st.session_state.current_user][agent_name]]
                        ]

                        stream = client.chat.completions.create(
                            model=AGENTS[agent_name]["model"],
                            messages=messages,
                            max_tokens=AGENTS[agent_name]["max_tokens"],
                            stream=True,
                        )
                        response = st.write_stream(stream)

                    st.session_state.messages[st.session_state.current_user][agent_name].append(
                        {"role": "assistant", "content": response}
                    )
                    st.rerun()

                if st.button("チャットをクリア", key=f"clear_{agent_name}"):
                    st.session_state.messages[st.session_state.current_user][agent_name] = []
                    st.rerun()
    else:
        st.info("左側のメニューからエージェントを選択してください")

else:
    st.title("Ollama チャットボット🤖")
    st.write("左側のメニューからログインしてください。")

