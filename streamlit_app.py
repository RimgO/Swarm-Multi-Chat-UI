import streamlit as st
import openai
import time
from dotenv import load_dotenv
import os

load_dotenv()

# OpenAI APIキーの設定
openai.api_key = st.secrets['OPEN_AI_API_KEY']

# Streamlitアプリケーションの設定
st.set_page_config(page_title="マルチユーザーチャットアプリ", page_icon="💬")
st.title("マルチユーザーチャットアプリ")

# セッション状態の初期化
if "messages" not in st.session_state:
    st.session_state.messages = []
if "users" not in st.session_state:
    st.session_state.users = ["ユーザー1"]
if "current_user_index" not in st.session_state:
    st.session_state.current_user_index = 0

# 新しいユーザーの追加
new_user = st.sidebar.text_input("新しいユーザー名を入力")
if st.sidebar.button("ユーザーを追加"):
    if new_user and new_user not in st.session_state.users:
        st.session_state.users.append(new_user)
        st.success(f"ユーザー '{new_user}' が追加されました。")
    elif new_user in st.session_state.users:
        st.warning("そのユーザー名は既に存在します。")
    else:
        st.warning("有効なユーザー名を入力してください。")

# ユーザー選択
selected_user = st.sidebar.selectbox("ユーザーを選択", st.session_state.users)
st.session_state.current_user_index = st.session_state.users.index(selected_user)

# チャット履歴の表示
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(f"{message['name']}: {message['content']}")

# ユーザー入力
user_input = st.chat_input(f"{selected_user}のメッセージを入力してください")

if user_input:
    # メッセージの追加
    st.session_state.messages.append({"role": "user", "name": selected_user, "content": user_input})
    
    # メッセージの表示
    with st.chat_message("user"):
        st.write(f"{selected_user}: {user_input}")
    
    # 次のユーザーに切り替え
    st.session_state.current_user_index = (st.session_state.current_user_index + 1) % len(st.session_state.users)

# OpenAI APIを使用した応答生成（オプション）
if st.button("AIアシスタントに質問する"):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_input}]
        )
        ai_response = response.choices[0].message.content
        
        # AIの応答をメッセージリストに追加
        st.session_state.messages.append({"role": "assistant", "name": "AIアシスタント", "content": ai_response})
        
        # AIの応答を表示
        with st.chat_message("assistant"):
            st.write(f"AIアシスタント: {ai_response}")
    except Exception as e:
        st.error(f"エラーが発生しました: {str(e)}")

# チャットのクリア
if st.button("チャットをクリア"):
    st.session_state.messages = []
    st.experimental_rerun()
