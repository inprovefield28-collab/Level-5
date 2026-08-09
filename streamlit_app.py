import streamlit as st
import pandas as pd
import os
import re
import random

# ==========================================
# 老師修改區
# ==========================================
APP_TITLE = "線上聽力測驗 Level 2"
INTRO_BOX_TEXT = """• 小學六年級單字、句型
• 自然發音 Level 5：特殊規則Phonics


COLOR_MAIN = "#8B5CF6"   # 主色
COLOR_LIGHT = "#F5F3FF"  # 說明框背景
COLOR_BG = "#F8F9FD"     # 網頁底色
# ==========================================

st.set_page_config(page_title=APP_TITLE, layout="centered")

# --- 1. 樣式注入 ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {COLOR_BG}; }}
    header {{ visibility: hidden; }}
    .block-container {{ padding-top: 1rem !important; }}
    [data-testid="stForm"] {{
        background-color: white !important;
        padding: 30px 40px !important;
        border-radius: 20px !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05) !important;
        border: none !important;
        border-top: 10px solid {COLOR_MAIN} !important;
        max-width: 600px;
        margin: 0px auto;
    }}
    .app-title {{
        color: {COLOR_MAIN};
        font-weight: 800;
        font-size: 32px;
        margin-top: -10px;
        margin-bottom: 10px;
        text-align: center;
    }}
    .intro-box {{
        background-color: {COLOR_LIGHT};
        padding: 12px 25px !important;
        border-radius: 12px;
        color: {COLOR_MAIN};
        font-size: 15px;
        line-height: 1.4;
        margin-bottom: 20px;
        white-space: pre-wrap;
        text-align: left;
    }}
    .quiz-btn button {{
        width: 100% !important;
        background-color: white !important;
        color: #333 !important;
        border: 2px solid #F3F4F6 !important;
        text-align: left !important;
        border-radius: 12px !important;
        padding: 15px !important;
        margin-bottom: 10px !important;
        font-size: 26px !important;
    }}
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心功能：讀取並整合所有題庫 (包含 Dialogue) ---
@st.cache_data
def load_all_questions():
    df_list = []
    # 支援匹配：Main1-50.csv, Phonics51-100.csv, Dialogue1-50.csv 等
    file_pattern = re.compile(r"([a-zA-Z]+)(\d+(?:-\d+)?)\.csv$")
    
    # 獲取當前目錄下所有檔案
    all_files = [f for f in os.listdir('.') if os.path.isfile(f)]
    
    for file_name in all_files:
        match = file_pattern.match(file_name)
        if match:
            cat, rng = match.group(1), match.group(2)
            try:
                # 優先嘗試 utf-8，不行則用 big5
                temp_df = pd.read_csv(file_name, encoding='utf-8-sig')
            except:
                temp_df = pd.read_csv(file_name, encoding='big5')
            
            # 統一欄位名稱為小寫並去除空格
            temp_df.columns = [c.strip().lower() for c in temp_df.columns]
            # 標註來源分類與範圍 (例如 Dialogue1-50)
            temp_df['cat_folder'] = f"{cat}{rng}" 
            df_list.append(temp_df)
    
    if not df_list:
        return []
    
    # 合併所有讀取到的 CSV
    full_df = pd.concat(df_list, ignore_index=True)
    all_questions = []
    
    for q in full_df.to_dict('records'):
        # 處理 ID 補零，確保 1 變成 001
        raw_id = str(q.get('id', '0')).split('.')[0]
        clean_id = raw_id.zfill(3)
        
        # 建立選項清單並打亂
        opts = [str(q.get('a','')), str(q.get('b','')), str(q.get('c',''))]
        correct_text = opts[0] # 假設 A 永遠是正確答案
        random.shuffle(opts)
        
        # 音檔路徑：Dialogue1-50 / q_001.mp3
        folder = q['cat_folder']
        audio_path = os.path.join(folder, f"q_{clean_id}.mp3")
        
        all_questions.append({
            'id': clean_id,
            'q_text': q.get('question', ''),
            'opts': opts,
            'ans_idx': opts.index(correct_text),
            'path': audio_path,
            'source': folder
        })
    return all_questions

# --- 3. 狀態管理與介面 ---
if 'step' not in st.session_state:
    st.session_state.step = 'start'

# A. 啟動頁面
if st.session_state.step == 'start':
    with st.form("start_form"):
        st.markdown(f'<div class="app-title">{APP_TITLE}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="intro-box">{INTRO_BOX_TEXT}</div>', unsafe_allow_html=True)
        user_name = st.text_input("姓名", label_visibility="collapsed", placeholder="請輸入姓名")
        submit = st.form_submit_button("進入挑戰")
        
        if submit:
            if not user_name.strip():
                st.error("請輸入姓名後再開始唷！")
            else:
                st.session_state.user_name = user_name
                st.session_state.all_pool = load_all_questions()
                
                if not st.session_state.all_pool:
                    st.error("找不到 CSV 題庫，請確認檔案命名是否正確。")
                else:
                    # 從總題庫中隨機抽取 10 題
                    num_to_pick = min(len(st.session_state.all_pool), 10)
                    st.session_state.quiz_data = random.sample(st.session_state.all_pool, num_to_pick)
                    
                    st.session_state.current_idx = 0
                    st.session_state.results = []
                    st.session_state.step = 'quiz'
                    st.rerun()

# B. 測驗執行頁
elif st.session_state.step == 'quiz':
    q = st.session_state.quiz_data[st.session_state.current_idx]
    st.markdown(f"### 第 {st.session_state.current_idx + 1} / 10 題")
    
    # 音檔播放
    if os.path.exists(q['path']):
        st.audio(q['path'])
    else:
        st.warning(f"找不到音檔：{q['path']}")
    
    st.markdown('<div class="quiz-btn">', unsafe_allow_html=True)
    labels = ['A', 'B', 'C']
    for i, opt_text in enumerate(q['opts']):
        if st.button(f"{labels[i]}. {opt_text}", key=f"btn_{st.session_state.current_idx}_{i}"):
            # 記錄結果
            st.session_state.results.append({
                "question": q['q_text'],
                "user_choice": opt_text,
                "correct_answer": q['opts'][q['ans_idx']],
                "is_correct": (i == q['ans_idx']),
                "source": q['source']
            })
            # 進入下一題
            st.session_state.current_idx += 1
            if st.session_state.current_idx >= len(st.session_state.quiz_data):
                st.session_state.step = 'result'
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# C. 結果顯示頁
elif st.session_state.step == 'result':
    st.markdown(f"""
    <div style="background-color: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); border-top: 10px solid {COLOR_MAIN}; max-width: 600px; margin: 20px auto;">
        <h2 style='text-align:center;'>🏆 挑戰完成！</h2>
    """, unsafe_allow_html=True)
    
    score_count = sum(1 for item in st.session_state.results if item['is_correct'])
    total_count = len(st.session_state.results)
    final_score = score_count * 10
    
    st.markdown(f"<h3 style='text-align:center; color:{COLOR_MAIN};'>{st.session_state.user_name} 的得分：{final_score} 分</h3>", unsafe_allow_html=True)

    # --- 建立複製用的文字報告 ---
    wrong_txt = ""
    for i, item in enumerate(st.session_state.results):
        if not item['is_correct']:
            source_info = item.get('source', '未知範圍')
            wrong_txt += f"Q{i+1} ({source_info}): {item['question']}\\n   ❌ 您選: {item['user_choice']}\\n   ✅ 正確: {item['correct_answer']}\\n\\n"
    
    if not wrong_txt:
        wrong_txt = "🎉 太棒了！全對！"

    report_text = f"【{APP_TITLE}】\\n姓名：{st.session_state.user_name}\\n成績：{final_score} 分\\n\\n--- 錯題記錄 ---\\n{wrong_txt}"

    # --- JavaScript 一鍵複製按鈕 ---
    html_copy_button = f"""
        <button id="copyBtn" style="background-color:{COLOR_MAIN}; color:white; border:none; padding:15px; font-size:20px; font-weight:bold; border-radius:15px; width:100%; cursor:pointer; margin-top: 20px; transition: background 0.3s;">
            按我複製成績給老師
        </button>
        <script>
            document.getElementById('copyBtn').onclick = function() {{
                const text = "{report_text}";
                const cleanText = text.replace(/\\\\n/g, '\\n');
                
                if (navigator.clipboard && navigator.clipboard.writeText) {{
                    navigator.clipboard.writeText(cleanText).then(function() {{
                        document.getElementById('copyBtn').innerText = '✅ 複製成功！';
                        document.getElementById('copyBtn').style.backgroundColor = '#10B981';
                        setTimeout(function() {{ 
                            document.getElementById('copyBtn').innerText = '按我複製成績給老師'; 
                            document.getElementById('copyBtn').style.backgroundColor = '{COLOR_MAIN}';
                        }}, 2000);
                    }}).catch(function(err) {{
                        fallbackCopyTextToClipboard(cleanText);
                    }});
                }} else {{
                    fallbackCopyTextToClipboard(cleanText);
                }}
            }};

            function fallbackCopyTextToClipboard(text) {{
                var textArea = document.createElement("textarea");
                textArea.value = text;
                textArea.style.position = "fixed";
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                try {{
                    document.execCommand('copy');
                    document.getElementById('copyBtn').innerText = '✅ 複製成功 (備案)！';
                    setTimeout(function() {{ document.getElementById('copyBtn').innerText = '按我複製成績給老師'; }}, 2000);
                }} catch (err) {{
                    document.getElementById('copyBtn').innerText = '❌ 複製失敗，請手動截圖';
                    console.error('Fallback: Oops, unable to copy', err);
                }}
                document.body.removeChild(textArea);
            }}
        </script>
    """
    
    st.components.v1.html(html_copy_button, height=100)
    st.write("---")
    
    # 錯題預覽區
    has_wrong = False
    for i, item in enumerate(st.session_state.results):
        if not item['is_correct']:
            has_wrong = True
            st.error(f"**Q{i+1} [{item.get('source', '')}]: {item['question']}**\n\n❌ 您選: {item['user_choice']}  \n✅ 正確: {item['correct_answer']}")
            
    if not has_wrong:
        st.balloons()
        st.success("太厲害了！全部答對！")

    if st.button("再玩一次 (重新隨機抽題)", key="restart_btn"):
        st.session_state.step = 'start'
        st.rerun()
        
    st.markdown('</div>', unsafe_allow_html=True)
