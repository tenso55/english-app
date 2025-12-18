import streamlit as st
from gtts import gTTS
from streamlit_mic_recorder import mic_recorder, speech_to_text
import speech_recognition as sr
import io
import pandas as pd
from openai import OpenAI
import base64

# --- ページ設定 ---
st.set_page_config(page_title="Ultimate English App", layout="wide", page_icon="🇬🇧")

# --- サイドバー設定 (APIキー入力など) ---
with st.sidebar:
    st.title("⚙️ 設定")
    openai_api_key = st.text_input("OpenAI API Keyを入力", type="password")
    st.markdown("[APIキーの取得はこちら](https://platform.openai.com/api-keys)")
    
    st.divider()
    st.write("📚 単語帳データ")
    # 単語帳の初期化
    if 'vocab_list' not in st.session_state:
        st.session_state.vocab_list = []
    
    # 単語帳表示
    if st.session_state.vocab_list:
        df = pd.DataFrame(st.session_state.vocab_list)
        st.dataframe(df, hide_index=True)
        if st.button("単語帳をリセット"):
            st.session_state.vocab_list = []
            st.rerun()
    else:
        st.write("まだ登録がありません")

# --- OpenAIクライアント初期化 ---
client = None
if openai_api_key:
    client = OpenAI(api_key=openai_api_key)

# --- 共通関数: 音声再生 ---
def play_tts(text):
    try:
        tts = gTTS(text=text, lang='en')
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        st.audio(audio_bytes, format='audio/mp3')
    except Exception as e:
        st.error(f"音声再生エラー: {e}")

# --- アプリ本体 ---
st.title("🇬🇧 Ultimate English Practice")

# タブで機能を切り替え
tab1, tab2 = st.tabs(["🗣️ 英会話＆アドバイス", "📸 カメラで英単語"])

# ==========================================
# タブ1: 英会話 & AIアドバイス & 無限お題
# ==========================================
with tab1:
    st.header("Speaking Practice with AI")

    # --- 1. お題生成機能 ---
    col1, col2 = st.columns([3, 1])
    with col1:
        # 手動入力も可能
        target_text = st.text_input("練習する文章 (またはAIにお任せ👇)", key="target_input")
    with col2:
        # AIにお題を出させる
        if st.button("🎲 お題を生成"):
            if not client:
                st.error("左のサイドバーにAPIキーを入れてください")
            else:
                with st.spinner("AIが考え中..."):
                    try:
                        prompt = "英語学習者のために、日常会話で使える実用的な短い英文を1つだけ作成してください。日本語訳は不要です。引用符も不要です。"
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[{"role": "user", "content": prompt}]
                        )
                        generated_text = response.choices[0].message.content
                        # 入力欄を更新するためのトリック
                        st.session_state.target_temp = generated_text
                        st.rerun() 
                    except Exception as e:
                        st.error(str(e))

    # 生成されたお題があればセットする
    if 'target_temp' in st.session_state:
        target_text = st.session_state.target_temp
        st.info(f"お題: {target_text}")
        del st.session_state.target_temp # 一回使ったら消す

    # --- 2. リスニング ---
    if target_text and st.button("🔊 お手本を聞く"):
        play_tts(target_text)

    st.divider()

    # --- 3. スピーキング & 判定 ---
    st.write("👇 マイクボタンを押して発音してください")
    
    # マイク入力 (Google Speech-to-Text利用)
    user_text = speech_to_text(
        language='en',
        start_prompt="🎤 録音開始",
        stop_prompt="⏹️ 録音終了",
        just_once=False,
        key='STT_tab1'
    )

    if user_text:
        st.subheader("結果発表")
        st.write(f"🗣️ **あなたの発音:** {user_text}")

        # シンプルな正誤判定
        clean_user = user_text.lower().replace('.', '').replace(',', '').strip()
        clean_target = target_text.lower().replace('.', '').replace(',', '').strip()

        if clean_user == clean_target:
            st.success("🎉 Perfect! 完璧です！")
            st.balloons()
        else:
            st.warning("惜しい！少し違います。")
            
            # --- AIアドバイス機能 ---
            if client:
                with st.expander("🤖 AI先生のアドバイスを見る（クリック）", expanded=True):
                    with st.spinner("AIが分析中..."):
                        prompt = f"""
                        ターゲット文: "{target_text}"
                        ユーザーの発音: "{user_text}"
                        
                        ユーザーの発音のどこが間違っていたか、またはどう発音すればネイティブに近づくか、
                        日本語で優しく、かつ具体的にアドバイスしてください。
                        """
                        res = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[{"role": "user", "content": prompt}]
                        )
                        st.write(res.choices[0].message.content)

            # --- 単語帳登録ボタン ---
            if st.button("📖 この文を単語帳に保存"):
                st.session_state.vocab_list.append({
                    "Target": target_text,
                    "Your Speech": user_text
                })
                st.success("保存しました！サイドバーを確認してください。")

# ==========================================
# タブ2: 画像認識 (カメラで英語)
# ==========================================
with tab2:
    st.header("📸 Photo to English")
    st.write("身の回りのものをカメラで撮ると、AIが英語で答えてくれます！")

    # カメラ入力
    img_file = st.camera_input("写真を撮る")

    if img_file and client:
        # 画像をBase64に変換
        bytes_data = img_file.getvalue()
        base64_image = base64.b64encode(bytes_data).decode('utf-8')

        with st.spinner("AIが画像を見ています..."):
            try:
                # GPT-4o (Vision) に画像を送る
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "この画像に写っている主要なものを、英語単語一つで答えてください（冠詞は不要）。例: Apple"},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                            ],
                        }
                    ],
                    max_tokens=20
                )
                
                english_word = response.choices[0].message.content
                
                st.markdown(f"# 🍎 {english_word}")
                
                # 発音を聞く
                if st.button("🔊 発音を聞く", key="vision_tts"):
                    play_tts(english_word)

                # 単語帳へ保存
                if st.button("📖 単語帳へ保存", key="vision_save"):
                    st.session_state.vocab_list.append({"Word": english_word, "Type": "Image"})
                    st.success("保存しました！")
                    
            except Exception as e:
                st.error(f"エラー: {e}")
    elif img_file and not client:
        st.error("APIキーが必要です。サイドバーに入力してください。")