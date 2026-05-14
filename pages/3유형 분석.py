import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 페이지 설정
st.set_page_config(page_title="시간대별 사고유형 분석", layout="wide", page_icon="⏰")

# 2. 통합 CSS (기존 디자인 및 사이드바 스타일 100% 유지)
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #1e1e26 !important; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p, 
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] span { 
        color: #ffffff !important; 
    }
    .main-title { font-size: 2rem; font-weight: 900; color: #0f172a; margin-bottom: 20px; border-left: 12px solid #e11d48; padding-left: 20px; }
    .custom-table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.9rem; }
    .custom-table th { background-color: #f0f2f6; padding: 10px; text-align: center; border-bottom: 2px solid #dee2e6; color: #31333F; }
    .custom-table td { padding: 10px; text-align: center; border-bottom: 1px solid #dee2e6; }
    .highlight { color: #ff4b4b; font-weight: bold; }
    .summary-box {
        margin-top: 30px;
        padding: 18px;
        background: linear-gradient(135deg, #f8fafc, #f1f5f9);
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        border-left: 6px solid #e11d48;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .summary-title { font-size: 1.1rem; font-weight: 800; color: #0f172a; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;}
    .summary-item { font-size: 0.95rem; color: #334155; margin-bottom: 8px; line-height: 1.5; }
    .summary-highlight { font-weight: 800; color: #e11d48; }
</style>
""", unsafe_allow_html=True)

# 사고유형별 고정 색상 유지
COLOR_MAP = {
    '차대차': '#EF4444',
    '차대사람': '#3B82F6',
    '차량단독': '#10B981'
}

@st.cache_data
def load_data():
    try:
        # 1. 사고 데이터 로드 (기존 로직)
        df = pd.read_excel('2024사고유형.xlsx')
        df.columns = [str(c).strip() for c in df.columns]
        df = df.dropna(subset=['사고유형 대분류', '시간대'])
        df = df[~df['사고유형 대분류'].str.contains('주\)', na=False)]
        exclude_types = ['철길건널목', '합계']
        df = df[~df['사고유형 대분류'].isin(exclude_types)]

        # 2. 교통량 데이터 로드 (★날씨 파일의 로직 이식)
        try:
            try:
                df_t_raw = pd.read_csv('수시교통량.csv', encoding='cp949')
            except:
                df_t_raw = pd.read_csv('수시교통량.csv', encoding='euc-kr')
            
            # 날씨 파일과 동일한 전처리 방식
            df_t_raw['hour'] = df_t_raw['시간대'].str.strip().str[:2].astype(int)
            bins = list(range(0, 26, 2))
            labels = [f"{i}시~{i+2}시" for i in range(0, 24, 2)]
            df_t_raw['time_slot'] = pd.cut(df_t_raw['hour'], bins=bins, labels=labels, right=False)
            df_traffic = df_t_raw.groupby('time_slot', observed=True)['전차종합계'].mean().reindex(labels).fillna(0)
            traffic_list = df_traffic.values.tolist()
        except:
            # 오류 시 기본값
            traffic_list = [0] * 12

        return df, traffic_list
    except Exception as e:
        st.error(f"파일 오류: {e}")
        return pd.DataFrame(), []

df, traffic_volume = load_data()
time_columns = ['0시~2시', '2시~4시', '4시~6시', '6시~8시', '8시~10시', '10시~12시', '12시~14시', '14시~16시', '16시~18시', '18시~20시', '20시~22시', '22시~24시']

# 사이드바 (기존 토글 기능 유지)
selected_types = []
show_traffic = True
if not df.empty:
    with st.sidebar:
        type_options = df['사고유형 대분류'].unique().tolist()
        for i, s_type in enumerate(type_options):
            if st.toggle(s_type, value=(s_type in ["차대사람", "차대차", "차량단독"]), key=f"sidebar_type_{i}"):
                selected_types.append(s_type)
        st.markdown("---")
        show_traffic = st.toggle("🚦교통량 표시", value=True)

# 메인 분석 영역 (기존 차트 및 테이블 구성 유지)
if not df.empty:
    st.markdown('<div class="main-title">⏰ 시간대별 사고유형 및 치사율 분석</div>', unsafe_allow_html=True)
    
    if not selected_types:
        st.warning("왼쪽 사이드바에서 사고유형을 선택해 주세요.")
    else:
        main_col1, side_col1 = st.columns([3, 1])
        fig1 = make_subplots(specs=[[{"secondary_y": True}]])
        
        # 날씨 파일 데이터로 업데이트된 교통량 막대
        if show_traffic:
            fig1.add_trace(
                go.Bar(
                    x=time_columns, y=traffic_volume, 
                    name='전체 교통량',
                    marker_color='rgba(148, 163, 184, 0.3)',
                    hovertemplate='%{y:,.0f}대',
                ),
                secondary_y=True
            )

        top_stats = []
        for s_type in selected_types:
            acc_row = df[(df['사고유형 대분류'] == s_type) & (df['시간대'] == '사고[건]')]
            death_row = df[(df['사고유형 대분류'] == s_type) & (df['시간대'] == '사망[명]')]
            if not acc_row.empty and not death_row.empty:
                acc_vals = pd.to_numeric(acc_row[time_columns].values[0], errors='coerce')
                death_vals = pd.to_numeric(death_row[time_columns].values[0], errors='coerce')
                rates = [(d / a * 100) if a > 0 else 0 for a, d in zip(acc_vals, death_vals)]
                
                fig1.add_trace(
                    go.Scatter(x=time_columns, y=rates, mode='lines+markers', name=s_type,
                               line=dict(color=COLOR_MAP.get(s_type), width=3)),
                    secondary_y=False
                )
                if rates:
                    max_rate = max(rates); top_stats.append({'type': s_type, 'time': time_columns[rates.index(max_rate)], 'rate': round(max_rate, 2)})
        
        fig1.update_layout(title="시간대별 교통량 대비 사고 치사율(%) 분석", height=450, template="plotly_white", hovermode="x unified")
        fig1.update_yaxes(title_text="치사율 (%)", secondary_y=False)
        fig1.update_yaxes(title_text="교통량", secondary_y=True, showgrid=False, showticklabels=False)
        main_col1.plotly_chart(fig1, use_container_width=True)
        
        with side_col1:
            st.markdown("<div style='margin-top: 50px;'></div><h5>🏆 유형별 최고 치사율</h5>", unsafe_allow_html=True)
            rows_html = "".join([f"<tr><td>{s['type']}</td><td>{s['time']}</td><td class='highlight'>{s['rate']}%</td></tr>" for s in top_stats])
            st.markdown(f'<table class="custom-table"><thead><tr><th>유형</th><th>위험 시간</th><th>치사율</th></tr></thead><tbody>{rows_html}</tbody></table>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        main_col2, side_col2 = st.columns([3, 1])
        fig2 = go.Figure()
        max_acc_val, max_acc_time, max_acc_type = 0, "", ""

        for s_type in selected_types:
            acc_row = df[(df['사고유형 대분류'] == s_type) & (df['시간대'] == '사고[건]')]
            if not acc_row.empty:
                acc_vals = pd.to_numeric(acc_row[time_columns].values[0], errors='coerce')
                fig2.add_trace(go.Bar(x=time_columns, y=acc_vals, name=s_type, marker_color=COLOR_MAP.get(s_type)))
                local_max = max(acc_vals)
                if local_max > max_acc_val:
                    max_acc_val = local_max; max_acc_time = time_columns[acc_vals.tolist().index(local_max)]; max_acc_type = s_type

        fig2.update_layout(title="시간대별 사고 발생 건수", height=400, template="plotly_white", barmode='group', hovermode="x unified", yaxis_title="사고 건수 (건)")
        main_col2.plotly_chart(fig2, use_container_width=True)

        with side_col2:
            if top_stats:
                highest_fatal = max(top_stats, key=lambda x: x['rate'])
                st.markdown(f"""<div class="summary-box"><div class="summary-title">📊 핵심 요약</div><div class="summary-item">• <b>최다 사고 발생</b><br>&nbsp;&nbsp;👉 {max_acc_time} ({max_acc_type})<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;건수: {int(max_acc_val):,}건</div><div class="summary-item">• <b>최고 치사율 기록</b><br>&nbsp;&nbsp;👉 <span class="summary-highlight">{highest_fatal['time']} ({highest_fatal['type']})</span><br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;치사율: <span class="summary-highlight">{highest_fatal['rate']}%</span></div><hr style="margin: 10px 0; border-color: #cbd5e1;"><div class="summary-item" style="font-size: 0.9rem;">💡 <b>결론</b>: 사고가 가장 많이 일어나는 시간대와 치사율이 높은 시간대가 다릅니다. 교통량이 적어지는 심야/새벽 시간에 발생하는 사고가 생명에 훨씬 더 치명적입니다.</div></div>""", unsafe_allow_html=True)
else:
    st.info("데이터를 불러올 수 없습니다. 파일명을 확인해주세요.")