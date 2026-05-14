import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="교통사고 통합 분석 시뮬레이터", layout="wide", page_icon="🛡️")

# 2. 통합 CSS: 사이드바 글자색 및 시뮬레이터 스타일 유지
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@700&family=Noto+Sans+KR:wght@500;700;900&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Noto Sans KR', sans-serif; }
    
    /* 사이드바 스타일 (어두운 배경 + 흰색 글자 고정) */
    [data-testid="stSidebar"] { background-color: #1e1e26 !important; }
    [data-testid="stSidebarNav"] span { color: #ffffff !important; font-weight: 500 !important; }
    [data-testid="stSidebar"] h2 { color: #f1f5f9 !important; }
    
    .main-title { font-size: 2rem; font-weight: 900; color: #0f172a; margin-bottom: 20px; border-left: 12px solid #e11d48; padding-left: 20px; }
    
    /* 시뮬레이터 결과 박스 스타일 */
    .result-card { background-color: rgba(255,255,255,0.05); padding: 18px; border-radius: 12px; border-left: 6px solid; }
    .result-header { font-size: 1.3rem !important; font-weight: 700; margin-bottom: 8px; }
    .result-score { font-size: 1.1rem; margin-bottom: 12px; }
    .result-desc { font-size: 0.85rem !important; color: #ADB5BD; line-height: 1.5; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 10px; }
    .grade-info { font-size: 0.75rem !important; color: #6C757D; margin-top: 8px; }
    
    div[data-testid="stMetricValue"] { font-size: 1.7rem !important; font-weight: 800 !important; }
    .custom-table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.9rem; }
    .custom-table th { background-color: #f0f2f6; padding: 10px; text-align: center; border-bottom: 2px solid #dee2e6; color: #31333F; }
    .custom-table td { padding: 10px; text-align: center; border-bottom: 1px solid #dee2e6; }
    .highlight { color: #ff4b4b; font-weight: bold; }

    /* 🎨 인사이트 도출 박스 스타일 (왼쪽 빨간 선 강조) */
    .summary-box {
        background-color: #f8fafc;
        padding: 20px 20px 20px 25px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        position: relative;
        overflow: hidden;
        margin-top: 20px;
    }
    .summary-box::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 8px;
        height: 100%;
        background-color: #e11d48;
    }
    .summary-title {
        font-size: 1.2rem;
        font-weight: 800;
        color: #1e293b;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .summary-item {
        margin-bottom: 12px;
        line-height: 1.6;
        color: #475569;
        font-size: 0.95rem;
    }
    .summary-highlight {
        color: #e11d48;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_all_combined_data():
    df_raw = pd.read_excel('기상_시간2024.xlsx')
    try:
        df_t_raw = pd.read_csv('수시교통량.csv', encoding='cp949')
    except:
        df_t_raw = pd.read_csv('수시교통량.csv', encoding='euc-kr')
    df_t_raw['hour'] = df_t_raw['시간대'].str.strip().str[:2].astype(int)
    bins = list(range(0, 26, 2))
    labels = [f"{i}시~{i+2}시" for i in range(0, 24, 2)]
    df_t_raw['time_slot'] = pd.cut(df_t_raw['hour'], bins=bins, labels=labels, right=False)
    df_traffic = df_t_raw.groupby('time_slot', observed=True)['전차종합계'].mean().reset_index()

    file_weather = '교통사고통계(기상_연도_노면).xlsx'
    df_w_stat = pd.read_excel(file_weather, header=[0, 1])
    df_w_stat = df_w_stat.set_index([df_w_stat.columns[0], df_w_stat.columns[1]])
    acc_w = df_w_stat.xs('사고[건]', level=1)[('합계', '합계')]
    dea_w = df_w_stat.xs('사망[명]', level=1)[('합계', '합계')]
    rate_series = (dea_w / acc_w * 100).fillna(0)
    rate_series = rate_series.drop(labels=['합계', '기타/불명'], errors='ignore')
    rate_dict = {str(k): float(v) for k, v in rate_series.items()}

    file_time = '20202024시간대별.xlsx'
    df_t_raw_sim = pd.read_excel(file_time)
    time_cols = ['0시~2시', '2시~4시', '4시~6시', '6시~8시', '8시~10시', '10시~12시', 
                 '12시~14시', '14시~16시', '16시~18시', '18시~20시', '20시~22시', '22시~24시']
    
    time_weather_dict = {}
    weather_types = df_t_raw_sim['기상상태'].unique()
    for weather in weather_types:
        if weather == '합계': continue
        weather_rows = df_t_raw_sim[df_t_raw_sim['기상상태'] == weather]
        try:
            acc_vals = weather_rows[weather_rows['시간대'] == '사고[건]'][time_cols].values[0]
            dea_vals = weather_rows[weather_rows['시간대'] == '사망[명]'][time_cols].values[0]
            temp_df = pd.DataFrame({
                '시간대': time_cols, '사고건수': acc_vals.astype(float), '사망자수': dea_vals.astype(float)
            })
            temp_df['사망률'] = (temp_df['사망자수'] / temp_df['사고건수'] * 100).fillna(0)
            avg_rate = temp_df['사망률'].mean()
            temp_df['가중치'] = (temp_df['사망률'] / avg_rate) if avg_rate > 0 else 1
            time_weather_dict[weather] = temp_df
        except: continue
    
    return df_raw, df_traffic, rate_dict, time_weather_dict, acc_w.sum(), dea_w.sum()

try:
    df_raw, df_traffic, rate_dict, time_weather_dict, total_acc, total_dea = load_all_combined_data()
    st.markdown('<div class="main-title">🌡️ 기상상태별 교통사고 정밀 분석</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📈 시간대별 추이 분석", "🛡️ 위험도 시뮬레이터 모드"])

    with tab1:
        st.header("📊 기상상태별 치사율 & 교통량 분석")
        target_weathers = ["맑음", "안개", "흐림", "비", "눈"]
        cols_ctrl = st.columns(len(target_weathers) + 2)
        selected_weathers = []
        for i, weather in enumerate(target_weathers):
            if cols_ctrl[i].checkbox(weather, value=(weather in ["맑음", "안개"]), key=f"t1_chk_{weather}"):
                selected_weathers.append(weather)
        show_traffic = cols_ctrl[-1].toggle("🚦 교통량 표시", value=False)
        
        if not selected_weathers:
            st.warning("기상 상태를 선택해주세요.")
        else:
            m_col, s_col = st.columns([3, 1])
            time_cols_t1 = [f"{i}시~{i+2}시" for i in range(0, 24, 2)]
            fig_t1 = make_subplots(specs=[[{"secondary_y": True}]])
            top_stats = []
            
            if show_traffic:
                fig_t1.add_trace(go.Bar(x=time_cols_t1, y=df_traffic['전차종합계'], name="교통량", marker_color='rgba(180,180,180,0.3)'), secondary_y=False)
            
            for weather in selected_weathers:
                acc_data = df_raw[(df_raw['기상상태']==weather) & (df_raw['시간대']=='사고[건]')][time_cols_t1]
                dea_data = df_raw[(df_raw['기상상태']==weather) & (df_raw['시간대']=='사망[명]')][time_cols_t1]
                if not acc_data.empty and not dea_data.empty:
                    acc = pd.to_numeric(acc_data.values[0], errors='coerce')
                    dea = pd.to_numeric(dea_data.values[0], errors='coerce')
                    rates = [round((d/a)*100, 2) if a > 0 else 0 for a, d in zip(acc, dea)]
                    fig_t1.add_trace(go.Scatter(x=time_cols_t1, y=rates, name=weather, mode='lines+markers'), secondary_y=True)
                    mr = max(rates); mt = time_cols_t1[rates.index(mr)]
                    top_stats.append({'w': weather, 't': mt, 'r': mr})
            
            fig_t1.update_layout(height=450, template="plotly_white", hovermode="x unified")
            m_col.plotly_chart(fig_t1, use_container_width=True)
            
            with s_col:
                st.markdown("##### 🏆 치사율 1위 시간대")
                rows = "".join([f"<tr><td>{s['w']}</td><td>{s['t']}</td><td class='highlight'>{s['r']}%</td></tr>" for s in top_stats])
                st.markdown(f'<table class="custom-table"><thead><tr><th>기상</th><th>시간</th><th>치사율</th></tr></thead><tbody>{rows}</tbody></table>', unsafe_allow_html=True)
                
                # 🎨 인사이트 도출 박스 추가
                if top_stats:
                    highest_fatal = max(top_stats, key=lambda x: x['r'])
                    st.markdown(
                        f"""
                        <div class="summary-box">
                            <div class="summary-title">📊 핵심 요약</div>
                            <div class="summary-item">
                                • <b>기상 조건별 특이점</b><br>
                                &nbsp;&nbsp;👉 현재 선택된 {len(selected_weathers)}개 조건 중<br>
                                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>{highest_fatal['w']}</b> 상태가 가장 위험합니다.
                            </div>
                            <div class="summary-item">
                                • <b>최고 치사율 기록</b><br>
                                &nbsp;&nbsp;👉 <span class="summary-highlight">{highest_fatal['t']} ({highest_fatal['w']})</span><br>
                                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;치사율: <span class="summary-highlight">{highest_fatal['r']}%</span>
                            </div>
                            <hr style="margin: 10px 0; border-color: #cbd5e1;">
                            <div class="summary-item" style="font-size: 0.9rem;">
                                💡 <b>결론</b>: 기상 악화 시에는 가시거리 확보가 어려운 <b>심야/새벽 시간대</b>의 사고 치사율이 평상시보다 압도적으로 높습니다. 감속 운행이 필수적입니다.
                            </div>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )

    with tab2:
        weather_list = list(rate_dict.keys())
        df_t_default = time_weather_dict[weather_list[0]]
        overall_avg_rate = (total_dea / total_acc) * 100
        worst_weather = max(rate_dict, key=rate_dict.get)
        worst_time = df_t_default.loc[df_t_default['사망률'].idxmax(), '시간대']

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("평균 치사율", f"{overall_avg_rate:.2f}%")
        m2.metric("최악 기상", worst_weather, f"{rate_dict[worst_weather]:.2f}%", delta_color="inverse")
        m3.metric("최악 시간대", worst_time, "위험도 상", delta_color="inverse")
        m4.metric("분석 데이터", f"{int(total_acc/10000):,}만 건")

        st.markdown("---")
        st.title("🛡️ 교통사고 위험도 시뮬레이터")
        input_col1, input_col2, _ = st.columns([2.5, 2.5, 7]) 
        with input_col1: 
            u_weather = st.selectbox("☀️ 기상 상태", weather_list, key="sim_w_sel")
            df_t = time_weather_dict[u_weather]
        with input_col2:
            u_time = st.selectbox("⏰ 운행 시간대", df_t['시간대'].tolist(), key="sim_t_sel")

        base_rate = float(rate_dict[u_weather])
        time_weight = float(df_t.loc[df_t['시간대'] == u_time, '가중치'].values[0])
        final_score = base_rate * time_weight

        st.write("")
        res_l, res_r = st.columns([1.2, 1]) 
        with res_l:
            if final_score > 5: grade, color = "매우 위험 (🚨)", "#FF4B4B"
            elif final_score > 2: grade, color = "위험 (⚠️)", "#FFA500"
            else: grade, color = "주의/안전 (✅)", "#28A745"
            st.markdown(f"""
            <div class="result-card" style="border-left-color: {color};">
                <div class="result-header" style="color: {color};">{grade}</div>
                <div class="result-score"><b>{u_weather} + {u_time}</b> 예측 치사율: <span style="color:{color}; font-weight:800;">{final_score:.2f}%</span></div>
                <div class="result-desc">🔍 <b>산출 근거:</b><br>선택하신 <b>{u_weather}</b>의 기본 치사율({base_rate:.2f}%)에 해당 시간대(<b>{u_time}</b>)의 사고 치명도 가중치(x{time_weight:.2f})를 결합한 수치입니다.</div>
                <div class="grade-info">* 기준: 주의(0~2%), 위험(2~5%), 매우 위험(5% 초과)<br>* 치사율: 사고 100건당 발생하는 사망자 수의 비율</div>
            </div>""", unsafe_allow_html=True)
        with res_r:
            fig_gauge = go.Figure(go.Indicator(mode = "gauge+number", value = final_score,
                gauge = {'axis': {'range': [0, 10], 'tickfont': {'size': 10}}, 'bar': {'color': color},
                    'steps': [{'range': [0, 2], 'color': "rgba(40, 167, 69, 0.1)"}, {'range': [2, 5], 'color': "rgba(255, 165, 0, 0.1)"}, {'range': [5, 10], 'color': "rgba(255, 75, 75, 0.1)"}]}))
            fig_gauge.update_layout(template='plotly_dark', height=200, margin=dict(t=0, b=0, l=20, r=20))
            st.plotly_chart(fig_gauge, use_container_width=True)

        st.markdown("---")
        st.subheader("📊 통계 데이터 심층 분석")
        col1, col2 = st.columns(2)
        with col1:
            fig_time = px.line(df_t, x='시간대', y='사망률', markers=True, title="시간대별 사고 치사율", labels={'사망률': '치사율 (%)'}, color_discrete_sequence=['#FF4B4B'])
            fig_time.update_layout(template='plotly_dark', hovermode="x unified", xaxis_tickangle=-45, height=400)
            selected_idx = df_t[df_t['시간대'] == u_time].index[0]
            fig_time.add_vrect(x0=selected_idx - 0.5, x1=selected_idx + 0.5, fillcolor="yellow", opacity=0.2, line_width=0)
            st.plotly_chart(fig_time, use_container_width=True)
        with col2:
            weather_df = pd.DataFrame([{'기상상태': k, '치사율': v} for k, v in rate_dict.items()]).sort_values('치사율', ascending=False)
            fig_weather = px.bar(weather_df, x='기상상태', y='치사율', color='치사율', title="기상 조건별 평균 치사율", labels={'치사율': '평균 치사율 (%)'}, color_continuous_scale='Reds')
            fig_weather.update_layout(template='plotly_dark', height=400)
            st.plotly_chart(fig_weather, use_container_width=True)
except Exception as e:
    st.error(f"⚠️ 오류: {e}")