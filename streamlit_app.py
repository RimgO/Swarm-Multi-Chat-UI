import streamlit as st
import openai
import time

# OpenAI APIキーの設定
openai.api_key = "YOUR_API_KEY_HERE"

# Streamlitアプリケーションの設定
st.set_page_config(page_title="2人用チャットアプリ", page_icon="💬")
st.title("2人用チャットアプリ")

# セッション状態の初期化
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_user" not in st.session_state:
    st.session_state.current_user = "ユーザー1"

# チャット履歴の表示
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(f"{message['name']}: {message['content']}")

# ユーザー入力
user_input = st.chat_input(f"{st.session_state.current_user}のメッセージを入力してください")

if user_input:
    # メッセージの追加
    st.session_state.messages.append({"role": "user", "name": st.session_state.current_user, "content": user_input})
    
    # メッセージの表示
    with st.chat_message("user"):
        st.write(f"{st.session_state.current_user}: {user_input}")
    
    # ユーザーの切り替え
    st.session_state.current_user = "ユーザー2" if st.session_state.current_user == "ユーザー1" else "ユーザー1"

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
