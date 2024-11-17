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

# ページ設定
st.set_page_config(
    page_title="Ollama-Chatbot",
    page_icon="🤖",
    layout="wide",
)

# タイトルの表示
st.title("マルチユーザー Ollama チャットボット🤖")
st.caption("会話をリセットしたいときはページを再読み込みしてね。")

# OpenAIクライアントの設定
client = OpenAI(
    base_url='http://localhost:11434/v1/',  # 実際のIPアドレスを入力する
    api_key='dummy'  # ダミーでOK
)

# LLMモデルの指定
chat_model = "phi3:mini"

# セッション状態の初期化
if "users" not in st.session_state:
    st.session_state.users = ["ユーザー1"]
if "messages" not in st.session_state:
    st.session_state.messages = {user: [
        {"role": "assistant", "content": f"こんにちは。私は{st.session_state.users}さん専用の対話AIです。 **何でも聞いてください。** "}
    ] for user in st.session_state.users}

# 新しいユーザーの追加
new_user = st.sidebar.text_input("新しいユーザー名を入力")
if st.sidebar.button("ユーザーを追加"):
    if new_user and new_user not in st.session_state.users:
        st.session_state.users.append(new_user)
        st.session_state.messages[new_user] = [
            {"role": "assistant", "content": f"こんにちは。私は{new_user}さん専用の対話AIです。 **何でも聞いてください。** "}
        ]
        st.success(f"ユーザー '{new_user}' が追加されました。")
    elif new_user in st.session_state.users:
        st.warning("そのユーザー名は既に存在します。")
    else:
        st.warning("有効なユーザー名を入力してください。")

# タブの作成
tabs = st.tabs(st.session_state.users)

# 各ユーザーのチャットウィンドウを作成
for i, user in enumerate(st.session_state.users):
    with tabs[i]:
        st.header(f"{user}のチャット")
        
        # チャット履歴の表示
        for message in st.session_state.messages[user]:
            if message["role"] == "system":
                st.chat_message(message["role"], avatar='💻').write(message['content'])
            elif message["role"] == "assistant":
                st.chat_message(message["role"], avatar='🤖').write(message["content"])
            elif message["role"] == "user":
                st.chat_message(message["role"], avatar='👦').write(message["content"])
        
        # ユーザー入力
        prompt = st.chat_input(f"{user}のメッセージを入力してください")
        
        if prompt:
            # ユーザーのメッセージを追加
            st.session_state.messages[user].append({"role": "user", "content": prompt})
            
            # ユーザーのメッセージを表示
            with st.chat_message("user", avatar='👦'):
                st.markdown(prompt)
            
            # チャットボットの返答を取得＆表示
            with st.chat_message("assistant", avatar='🤖'):
                stream = client.chat.completions.create(
                    model=chat_model,
                    messages=st.session_state.messages[user],
                    stream=True,
                )
                response = st.write_stream(stream)
            
            # メッセージに返答を追加
            st.session_state.messages[user].append({"role": "assistant", "content": response})

# チャットのクリア
if st.sidebar.button("全てのチャットをクリア"):
    for user in st.session_state.users:
        st.session_state.messages[user] = [
            {"role": "assistant", "content": f"こんにちは。私は{user}さん専用のAIです。 **何でも聞いてください。** "}
        ]
    st.rerun()