import streamlit as st
from gtts import gTTS
import speech_recognition as sr
from streamlit_mic_recorder import mic_recorder
import io

# ページの設定
st.set_page_config(page_title="英会話アプリ", layout="centered")

st.title("🇬🇧 English Speaking & Listening")
st.markdown("PCのマイクを使って、英語の発音練習をしましょう！")

# --- 1. お題の設定 ---
st.subheader("1. 練習する文章 (Target)")
default_text = "Hello, how are you doing today?"
target_text = st.text_input("ここにお題を入力できます", default_text)

# --- 2. リスニング機能 (AIが読む) ---
st.subheader("2. お手本を聞く (Listening)")

if st.button("🔊 音声を再生"):
    if target_text:
        try:
            # Googleの音声合成を使用
            tts = gTTS(text=target_text, lang='en')
            audio_bytes = io.BytesIO()
            tts.write_to_fp(audio_bytes)
            st.audio(audio_bytes, format='audio/mp3')
        except Exception as e:
            st.error(f"エラーが発生しました: {e}\nインターネット接続を確認してください。")

# --- 3. スピーキング機能 (あなたが読む) ---
st.subheader("3. 発音する (Speaking)")
st.write("下のボタンを押して録音してください。")

# マイクボタンの設置
audio = mic_recorder(
    start_prompt="🎤 録音開始 (Click to Record)",
    stop_prompt="⏹️ 録音終了 (Stop)",
    key='recorder',
    just_once=False,
    use_container_width=False,
     format='wav' 
)

# 録音データがある場合に処理を実行
if audio:
    st.info("音声を解析中...")
    
    # 録音データを取得
    audio_bio = io.BytesIO(audio['bytes'])
    audio_bio.name = 'audio.wav'
    
    r = sr.Recognizer()
    
    try:
        # 音声データを読み込む
        with sr.AudioFile(audio_bio) as source:
            audio_data = r.record(source)
            
        # Google音声認識でテキスト化 (要ネット接続)
        user_text = r.recognize_google(audio_data, language='en-US')
        
        # 結果表示
        st.write("---")
        st.write(f"🗣️ **あなたが言った言葉:** {user_text}")
        
        # 正誤判定ロジック（記号と大文字小文字を無視）
        def clean(text):
            return text.lower().replace('.', '').replace(',', '').replace('?', '').replace('!', '').strip()

        if clean(user_text) == clean(target_text):
            st.success("🎉 Perfect! 発音バッチリです！")
            st.balloons()
        else:
            st.error("惜しい！もう一度トライしましょう。")
            st.write(f"正解: {target_text}")
            
    except sr.UnknownValueError:
        st.warning("音声が聞き取れませんでした。マイクに近づいてもう一度話してください。")
    except sr.RequestError:
        st.error("音声認識サービスに接続できませんでした。インターネットを確認してください。")
    except Exception as e:
        st.error(f"エラー: {e}")