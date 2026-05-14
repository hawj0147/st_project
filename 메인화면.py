import streamlit as st
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="2024 시간대별 치사율 분석", layout="wide", page_icon="🚨")

# 1초마다 실시간 업데이트
st_autorefresh(interval=1000, key="daterefresh")

# 2. 통합 UI/UX 스타일링 (디자인 유지)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@700&family=Noto+Sans+KR:wght@500;700;900&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #f8fafc;
        font-family: 'Noto Sans KR', sans-serif;
    }
    .block-container { padding-top: 1.5rem !important; max-width: 96% !important; }
    header { visibility: hidden; }

    [data-testid="stSidebar"] { background-color: #1e1e26 !important; }
    [data-testid="stSidebarNav"] span { color: #ffffff !important; font-weight: 500 !important; }
    [data-testid="stSidebar"] h2 { color: #f1f5f9 !important; }

    .main-title { 
        font-size: 2.2rem; font-weight: 900; color: #0f172a; 
        margin-bottom: 20px; border-left: 12px solid #e11d48; padding-left: 20px;
    }

    .unified-module {
        border: 2px solid #cbd5e1;
        border-radius: 15px;
        overflow: hidden;
        background-color: white;
        margin-bottom: 10px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .unified-module:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        border-color: #e11d48;
    }

    div.stButton > button {
        border: none !important; border-radius: 0 !important;
        height: 100px !important; width: 100% !important;
        font-size: 1.35rem !important; font-weight: 800 !important;
        color: #1e293b !important; background-color: white !important;
        margin: 0 !important;
        transition: all 0.2s;
    }
    div.stButton > button:hover {
        color: #e11d48 !important;
        background-color: #fff1f2 !important;
    }

    .bottom-info-card {
        background: #1e1e26; color: white; padding: 0px 20px;
        height: 90px; display: flex; align-items: center; border-top: 1px solid #334155;
    }
    .card-left { flex: 0.8; font-size: 1rem; font-weight: 800; border-right: 1px solid #3f3f46; text-align: center; }
    .card-right { flex: 1.2; padding-left: 25px; }
    .card-right .time { font-size: 1.1rem; font-weight: 700; color: #ffffff; }
    .card-right .val { font-size: 1rem; color: #fb7185; font-weight: 800; }

    .safety-box {
        margin-top: 15px; padding: 15px; background-color: #2d2d39;
        border-radius: 12px; border-left: 6px solid #00ffca;
    }

    .conclusion-grid {
        display: flex; align-items: center; background: white;
        padding: 25px; border-radius: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.06); margin-top: 10px;
    }
    .side-causes { flex: 1.1; }
    .center-arrow { flex: 0.3; font-size: 3.5rem; color: #e2e8f0; text-align: center; font-weight: 900; }
    .final-decision {
        flex: 0.9; background: #fff1f2; border-left: 10px solid #e11d48;
        padding: 20px; border-radius: 12px;
    }
    .cause-item {
        background: #f1f5f9; padding: 10px 15px; border-radius: 8px;
        margin-bottom: 8px; border-left: 5px solid #64748b; font-size: 0.95rem;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. 사이드바
with st.sidebar:
    st.markdown("## 🕒 MONITORING")
    curr_time = datetime.now()
    curr_hour = curr_time.hour
    
    st.markdown(f"""
    <div style="background: #2d2d39; padding: 20px; border-radius: 12px; text-align: center; border: 1px solid #3f3f46; margin-bottom: 10px;">
        <div style="font-size: 1.8rem; font-family: 'JetBrains Mono'; font-weight: 700; color: #00ffca;">
            {curr_time.strftime("%H:%M:%S")}
        </div>
    </div>
    """, unsafe_allow_html=True)

    if 2 <= curr_hour <= 6:
        s_col, s_lbl, s_msg = "#e11d48", "CRITICAL", f"현재 <b>피크타임</b>입니다.<br>사고 발생 시 치사율이 매우 위험합니다."
    else:
        s_col, s_lbl, s_msg = "#00ffca", "STABLE", f"피크타임(02-06시) 대비<br>현재 치사율은 비교적 안정적입니다."

    st.markdown(f"""
    <div class="safety-box" style="border-left-color: {s_col};">
        <div style="font-size: 0.8rem; color: {s_col}; font-weight: 800; margin-bottom: 5px;">{s_lbl} STATUS</div>
        <div style="font-size: 0.85rem; color: #ffffff; line-height: 1.5;">{s_msg}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-title">2024 교통사고 치사율 통합 제어 시스템</div>', unsafe_allow_html=True)

# 4. 분석 모듈 선택
st.markdown("#### 🚦 분석 모듈 제어 센터 & PeakTime")
m3, m1, m2 = st.columns(3)

with m1:
    st.markdown('<div class="unified-module">', unsafe_allow_html=True)
    if st.button("🌡️ 기상 분석 모듈", key="btn_w"): st.switch_page("pages/2기상 분석.py")
    st.markdown("""<div class="bottom-info-card"><div class="card-left">안개</div>
        <div class="card-right"><div class="time">02 ~ 04시</div><div class="val">치사율 33.3%</div></div></div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with m2:
    st.markdown('<div class="unified-module">', unsafe_allow_html=True)
    if st.button("🚗 유형 분석 모듈", key="btn_t"): st.switch_page("pages/3유형 분석.py")
    st.markdown("""<div class="bottom-info-card"><div class="card-left">차량단독</div>
        <div class="card-right"><div class="time">02 ~ 04시</div><div class="val">치사율 10.4%</div></div></div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with m3:
    st.markdown('<div class="unified-module">', unsafe_allow_html=True)
    if st.button("💨 과속 분석 모듈", key="btn_s"): st.switch_page("pages/1과속 분석.py")
    st.markdown("""<div class="bottom-info-card"><div class="card-left">과속</div>
        <div class="card-right"><div class="time">04 ~ 06시</div><div class="val">치사율 32.6%</div></div></div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div style="margin-top: 25px;"></div>', unsafe_allow_html=True)
st.markdown("#### 📝 데이터 분석 종합 결론")
st.markdown(f"""
    <div class="conclusion-grid">
        <div class="side-causes">
            <div class="cause-item"><b>기상:</b> 안개 시 새벽 치사율 30% 이상 (시거 확보 불능)</div>
            <div class="cause-item"><b>유형:</b> 새벽 시간대 차량 단독 사고 치사율 급증</div>
            <div class="cause-item"><b>법규:</b> 과속 사고 발생 시 대형 사고로 인한 치사율 30% 이상</div>
        </div>
        <div class="center-arrow">▶</div>
        <div class="final-decision">
            <div style="font-size: 0.9rem; color: #e11d48; font-weight: 800; margin-bottom: 5px;">최종 제어 대책</div>
            <div style="font-size: 1.15rem; font-weight: 900; color: #0f172a; line-height: 1.4;">
                위험 데이터가 중첩되는 <span style="color:#e11d48;">새벽시간대</span><br>
                집중 순찰 및 가변 속도 제한 시스템 가동
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)