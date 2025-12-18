import streamlit as st
from gtts import gTTS
from streamlit_mic_recorder import mic_recorder, speech_to_text
import io
import pandas as pd
import google.generativeai as genai
from PIL import Image

# --- ページ設定 ---
st.set_page_config(page_title="AI English App (Gemini)", layout="wide", page_icon="🇬🇧")

# --- サイドバー設定 ---
with st.sidebar:
    st.title("⚙️ 設定")
    
    # 👇 ここが魔法のコードです
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("APIキー読み込み済み (クラウド) ✅")
    else:
        api_key = st.text_input("Google API Keyを入力", type="password")
        st.markdown("[キーの取得はこちら(無料)](https://aistudio.google.com/app/apikey)")
    
    st.divider()
    # ...以下、単語帳のコードなどはそのまま...
    st.write("📚 単語帳")
    if 'vocab_list' not in st.session_state:
        st.session_state.vocab_list = []
    
    if st.session_state.vocab_list:
        df = pd.DataFrame(st.session_state.vocab_list)
        st.dataframe(df, hide_index=True)
        if st.button("リセット"):
            st.session_state.vocab_list = []
            st.rerun()

# --- Google Gemini初期化 ---
if api_key:
    genai.configure(api_key=api_key)

# --- 音声再生関数 ---
def play_tts(text):
    try:
        tts = gTTS(text=text, lang='en')
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        st.audio(audio_bytes, format='audio/mp3')
    except:
        st.error("音声再生エラー")

# --- アプリ本体 ---
st.title("🇬🇧 AI English App (Powered by Google)")

tab1, tab2 = st.tabs(["🗣️ 英会話＆アドバイス", "📸 カメラで英単語"])

# ==========================================
# タブ1: 英会話
# ==========================================
with tab1:
    st.header("Speaking Practice")

    col1, col2 = st.columns([3, 1])
    with col1:
        target_text = st.text_input("練習する文章 (またはAI生成👇)", key="target_input")
    with col2:
        if st.button("🎲 お題を生成"):
            if not api_key:
                st.error("サイドバーにAPIキーを入れてね")
            else:
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response = model.generate_content("英語学習用に、日常会話の短い英文を1つ作って。日本語訳不要。引用符不要。")
                    st.session_state.target_temp = response.text.strip()
                    st.rerun()
                except Exception as e:
                    st.error(f"エラー: {e}")

    if 'target_temp' in st.session_state:
        target_text = st.session_state.target_temp
        st.info(f"お題: {target_text}")
        del st.session_state.target_temp

    if target_text and st.button("🔊 お手本を聞く"):
        play_tts(target_text)

    st.divider()
    st.write("👇 マイクボタンを押して発音してください")
    
    user_text = speech_to_text(
        language='en', start_prompt="🎤 録音開始", stop_prompt="⏹️ 録音終了", key='STT_tab1'
    )

    if user_text:
        st.write(f"🗣️ **あなた:** {user_text}")
        
        clean_user = user_text.lower().replace('.', '').strip()
        clean_target = target_text.lower().replace('.', '').strip()

        if clean_user == clean_target:
            st.success("🎉 Perfect!")
            st.balloons()
        else:
            st.warning("惜しい！")
            
            # --- AIアドバイス (Gemini) ---
            if api_key:
                with st.expander("🤖 アドバイスを見る"):
                    with st.spinner("分析中..."):
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        prompt = f"文: '{target_text}'\n私の発音認識結果: '{user_text}'\nどこが違ったか日本語で優しく教えて。"
                        response = model.generate_content(prompt)
                        st.write(response.text)

            if st.button("📖 単語帳に保存"):
                st.session_state.vocab_list.append({"Target": target_text, "You": user_text})
                st.success("保存しました")

# ==========================================
# タブ2: 画像認識 (Gemini Vision)
# ==========================================
with tab2:
    st.header("📸 Photo to English")
    img_file = st.camera_input("写真を撮る")

    if img_file and api_key:
        # 画像を読み込む
        image = Image.open(img_file)

        with st.spinner("AIが見ています..."):
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                # 画像とテキストを同時に渡す
                response = model.generate_content(["この画像に写っている主要な物を英単語1つで答えて(冠詞不要)", image])
                english_word = response.text.strip()
                
                st.markdown(f"# 🍎 {english_word}")
                
                if st.button("🔊 発音を聞く", key="vision_tts"):
                    play_tts(english_word)

                if st.button("📖 保存", key="vision_save"):
                    st.session_state.vocab_list.append({"Word": english_word, "Type": "Image"})
                    st.success("保存しました")
                    
            except Exception as e:
                st.error(f"エラー: {e}")
    elif img_file and not api_key:
        st.error("APIキーが必要です")