import streamlit as st
import base64
import os
import time

# ========================================================
# 实验员控制台 - 流程优化版
# ========================================================

# --- 1. 映射配置 ---
AUDIO_MAPPING = {
    "朗读《红楼梦》的书评":
        r"audio/ElevenLabs_2026-04-14T07_27_55_低自信声音4_红楼梦_v3.mp3",
     "朗读《三国演义》的书评":
        r"audio/ElevenLabs_2026-04-14T07_11_53_低自信声音4_三国演义_v3.mp3",
    "朗读《西游记》的书评":
        r"audio/ElevenLabs_2026-04-14T07_43_00_低自信声音4_西游记_v3.mp3",
    "朗读《水浒传》的书评":
        r"audio/ElevenLabs_2026-04-14T08_02_01_低自信声音4_水浒传_v3.mp3"
}

SPECIFIC_RESPONSES = {
    "朗读《红楼梦》的书评":
        "《红楼梦》不仅是一部描写封建家族衰落的小说，更是一部关于生命幻灭与悲剧美学的史诗。作者曹雪芹通过复杂的意象和精妙的谶语，勾勒出了一个大观园式的理想国。这种从繁华到荒凉的剧烈转变揭示了传统社会中人性与礼教之间不可调和的矛盾。",

    "朗读《三国演义》的书评":
        "《三国演义》以宏大的视野展现了近一个世纪的军事斗争。作品成功塑造了曹操的性格和诸葛亮的智者形象。体现了民间叙事中对'义'与'智'的高度崇拜其战争描写不仅具备文学张力，更包含了深刻的权谋策略与地缘政治考量。",

    "朗读《西游记》的书评":
        "《西游记》通过一场充满奇幻色彩的取经之旅，构建了一个神魔交织、妙趣横生的童话世界。孙悟空的叛逆与成长，实际上象征着人类心灵在面对困境时的顽强生命力。这部作品以浪漫主义的手法，探讨了意志、信仰以及个人与社会规则之间的博弈。",
 
    "朗读《水浒传》的书评":
        "《水浒传》是施耐庵创作的中国四大名著之一。讲述了108位梁山好汉反抗腐败官府、为民除暴的传奇故事。全书人物众多,每个角色都有鲜明的个性和背景,如忠诚勇敢的宋江、义气深重的武松、深藏不露的林冲等。这些英雄虽为反叛者，但他们的行为常常暴力且复杂，体现了人性的多面性。"
}

# --- 2. 界面样式 ---
st.set_page_config(page_title="AI语音交互系统", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #f3f3f3; }
    header { visibility: hidden; }
    .fixed-header {
        position: fixed; top: 0; left: 0; width: 100%;
        background-color: #ededed; padding: 12px;
        text-align: center; font-weight: bold;
        border-bottom: 1px solid #dcdcdc; z-index: 1000; font-size: 16px;
    }
    .chat-container { padding-top: 60px; padding-bottom: 150px; }
    .fixed-footer {
        position: fixed; bottom: 0; left: 0; width: 100%;
        background-color: #f7f7f7; padding: 20px;
        border-top: 1px solid #dcdcdc; z-index: 1000;
    }
    audio { display: none; }
    </style>
    <div class="fixed-header">AI语音交互系统</div>
    """, unsafe_allow_html=True)


# --- 3. 音频播放函数（支持移动端自动播放）---
def autoplay_audio(audio_bytes, msg_index):
    b64 = base64.b64encode(audio_bytes).decode()
    audio_html = f"""
        <audio id="audio_{msg_index}">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        <script>
        (function() {{
            // 停止所有其他音频
            window.parent.document.querySelectorAll('audio').forEach(function(a) {{
                if (a.id !== 'audio_{msg_index}') {{
                    a.pause();
                    a.currentTime = 0;
                }}
            }});

            var audio = document.getElementById('audio_{msg_index}');

            // 尝试直接播放
            var playPromise = audio.play();

            if (playPromise !== undefined) {{
                playPromise.catch(function() {{
                    // 移动端被拦截，显示提示条等待用户点击
                    var existingBanner = window.parent.document.getElementById('tap-to-play-banner');
                    if (existingBanner) existingBanner.remove();

                    var banner = window.parent.document.createElement('div');
                    banner.id = 'tap-to-play-banner';
                    banner.style.cssText = [
                        'position:fixed',
                        'bottom:100px',
                        'left:50%',
                        'transform:translateX(-50%)',
                        'background:#ff6b35',
                        'color:white',
                        'padding:12px 24px',
                        'border-radius:24px',
                        'font-size:15px',
                        'z-index:99999',
                        'box-shadow:0 4px 12px rgba(0,0,0,0.3)',
                        'cursor:pointer',
                        'white-space:nowrap',
                        'font-family:sans-serif'
                    ].join(';');
                    banner.innerText = '🔊 点击屏幕任意位置播放语音';
                    window.parent.document.body.appendChild(banner);

                    function unlockAndPlay() {{
                        audio.play().catch(function() {{}});
                        var b = window.parent.document.getElementById('tap-to-play-banner');
                        if (b) b.remove();
                        window.parent.document.removeEventListener('click', unlockAndPlay);
                        window.parent.document.removeEventListener('touchstart', unlockAndPlay);
                    }}

                    window.parent.document.addEventListener('click', unlockAndPlay, {{once: true}});
                    window.parent.document.addEventListener('touchstart', unlockAndPlay, {{once: true}});
                }});
            }}
        }})();
        </script>
    """
    st.components.v1.html(audio_html, height=0)


# --- 4. 初始化状态 ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "processing" not in st.session_state:
    st.session_state.processing = False

# --- 5. 渲染聊天历史 ---
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "audio" in msg:
            if st.button(f"🔊 重复播放", key=f"rep_{i}"):
                autoplay_audio(msg["audio"], i)
st.markdown('</div>', unsafe_allow_html=True)

# --- 6. 底部输入区 ---
with st.container():
    st.markdown('<div class="fixed-footer">', unsafe_allow_html=True)
    col_sel, col_btn = st.columns([4, 1])
    options = ["请点击选择一个问题进行咨询..."] + list(AUDIO_MAPPING.keys())
    selected_option = col_sel.selectbox("Q", options, label_visibility="collapsed")
    send_trigger = col_btn.button("发送", use_container_width=True, type="primary")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 7. 核心逻辑：分步执行 ---
if send_trigger and selected_option != "请点击选择一个问题进行咨询...":
    st.session_state.messages.append({"role": "user", "content": selected_option})
    st.session_state.current_q = selected_option
    st.session_state.processing = True
    st.rerun()

if st.session_state.processing:
    # 模拟思考动画
    with st.chat_message("assistant"):
        thinking_placeholder = st.empty()
        with thinking_placeholder.container():
            st.markdown("AI 正在思考中...")
            st.spinner("")
            time.sleep(3)

    thinking_placeholder.empty()
    q = st.session_state.current_q
    path = AUDIO_MAPPING[q]
    text = SPECIFIC_RESPONSES[q]

    if os.path.exists(path):
        with open(path, "rb") as f:
            audio_data = f.read()

        st.session_state.messages.append({
            "role": "assistant",
            "content": text,
            "audio": audio_data
        })
        st.session_state.processing = False
        st.rerun()
    else:
        st.error(f"❌ 找不到音频文件！请确认 GitHub 仓库中 audio 文件夹内是否存在该文件，且文件名大小写一致。路径：{path}")
        st.session_state.processing = False

# --- 8. 自动播放最新一条助手消息 ---
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    last_idx = len(st.session_state.messages) - 1
    if "audio" in st.session_state.messages[-1]:
        autoplay_audio(st.session_state.messages[-1]["audio"], last_idx)