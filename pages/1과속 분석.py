import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 페이지 설정
st.set_page_config(page_title="시간별 과속 사고 및 교통량 분석", layout="wide")

# 2. 통합 CSS (기존 스타일 100% 유지 + 인사이트 박스 왼쪽 빨간 선 추가)
st.markdown("""
<style>
    /* 기존 레이아웃 및 사이드바 유지 */
    [data-testid="stSidebar"] { background-color: #1e1e26 !important; }
    [data-testid="stSidebarNav"] span { color: #ffffff !important; font-weight: 500 !important; }
    .main-title { font-size: 2rem; font-weight: 900; color: #0f172a; margin-bottom: 20px; border-left: 12px solid #e11d48; padding-left: 20px; }
    
    /* 테이블 스타일 유지 */
    .custom-table { width: 100%; border-collapse: collapse; font-size: 0.95rem; margin-bottom: 30px; }
    .custom-table th { background-color: #f0f2f6; padding: 15px 8px; border-bottom: 2px solid #dee2e6; text-align: center !important; font-weight: 700;}
    .custom-table td { padding: 15px 8px; text-align: center; border-bottom: 1px solid #dee2e6; }
    .highlight-red { color: #e74c3c; font-weight: bold; }
    .highlight-blue { color: #3498db; font-weight: bold; }
    .table-title { font-size: 1.1rem; font-weight: bold; margin-bottom: 12px; color: #31333F; }
    .table-container { margin-top: 10px; }

    /* 사고유형.py의 구조에 '왼쪽 빨간 강조선'만 추가 */
    .summary-box {
        background-color: #f8fafc;
        padding: 20px 20px 20px 25px; 
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        position: relative; 
        overflow: hidden;
    }
    
    /* 왼쪽 빨간색 강조선 */
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

def show_analysis():
    st.markdown('<div class="main-title">⏱️ 시간별 과속 사고 및 교통량 복합 분석</div>', unsafe_allow_html=True)
    
    try:
        # 1. 과속 사고 데이터 로드
        df_acc_raw = pd.read_excel('2024과속.xlsx')
        time_cols = [str(c).strip() for c in df_acc_raw.columns[2:]]
        acc_data = df_acc_raw.iloc[0, 2:].values.astype(int)
        death_data = df_acc_raw.iloc[1, 2:].values.astype(int)
        df_acc = pd.DataFrame({'시간대': time_cols, '사고건수': acc_data, '사망자수': death_data})
        df_acc['치사율(%)'] = (df_acc['사망자수'] / df_acc['사고건수'] * 100).round(2)

        # 2. 교통량 데이터 로드
        df_traffic_raw = pd.read_csv('수시교통량.csv', encoding='cp949')
        def map_time_range(t):
            try:
                hour = int(t.split('시')[0])
                start_h = (hour // 2) * 2
                return f"{start_h}시~{start_h+2}시"
            except: return t
        df_traffic_raw['그룹시간대'] = df_traffic_raw['시간대'].apply(map_time_range)
        df_traffic_grouped = df_traffic_raw.groupby('그룹시간대')['전차종합계'].mean().reset_index()
        df_traffic_grouped = df_traffic_grouped.set_index('그룹시간대').reindex(time_cols).reset_index().fillna(0)

        # 분석용 변수 추출
        max_rate_row = df_acc.loc[df_acc['치사율(%)'].idxmax()]
        max_acc_row = df_acc.loc[df_acc['사고건수'].idxmax()]

    except Exception as e:
        st.error(f"데이터 로드 실패: {e}"); return

    def update_clean_grid(fig, title_text, y1_title, y1_range, y2_title, y2_range):
        fig.update_layout(
            title=dict(text=title_text, font=dict(size=18)),
            xaxis=dict(title="시간대", showgrid=False),
            yaxis=dict(title=y1_title, range=y1_range, gridcolor='rgba(200, 200, 200, 0.3)', gridwidth=1, griddash='dot'),
            yaxis2=dict(title="치사율 (%)", overlaying='y', side='right', range=y2_range, showgrid=False),
            height=500, template="plotly_white", hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(t=80, r=50, b=50, l=50)
        )

    # 전체 레이아웃 구성 (3:1 비율)
    main_col, side_col = st.columns([3, 1])
    
    with main_col:
        # ① 사고 건수 및 치사율 그래프 (수정됨: 텍스트 라벨 추가)
        fig1 = make_subplots(specs=[[{"secondary_y": True}]])
        # 막대그래프: 안쪽 상단에 값 표시
        fig1.add_trace(go.Bar(
            x=df_acc['시간대'], y=df_acc['사고건수'], name="사고건수", 
            marker_color='rgba(180, 180, 180, 0.6)',
            text=df_acc['사고건수'], textposition='inside', texttemplate='%{text}건',
            insidetextanchor='end'
        ), secondary_y=False)
        # 꺾은선그래프: 포인트 위에 퍼센트 표시
        fig1.add_trace(go.Scatter(
            x=df_acc['시간대'], y=df_acc['치사율(%)'], name="치사율(%)", 
            mode='lines+markers+text', line=dict(color='#e74c3c', width=3),
            text=df_acc['치사율(%)'], textposition='top center', texttemplate='%{text}%'
        ), secondary_y=True)
        
        update_clean_grid(fig1, "시간대별 과속 사고 건수 및 치사율 분석", "사고 건수", 
                          [0, df_acc['사고건수'].max()*1.3], "치사율 (%)", [0, df_acc['치사율(%)'].max()*2.0])
        st.plotly_chart(fig1, use_container_width=True)

        st.write("---")

        # ② 교통량 대비 치사율 분석 그래프 (수정됨: 텍스트 라벨 추가)
        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        # 막대그래프: 안쪽 상단에 값 표시
        fig2.add_trace(go.Bar(
            x=df_traffic_grouped['그룹시간대'], y=df_traffic_grouped['전차종합계'], name="평균 교통량", 
            marker_color='rgba(71, 85, 105, 0.5)',
            text=df_traffic_grouped['전차종합계'].astype(int), textposition='inside', texttemplate='%{text}',
            insidetextanchor='end'
        ), secondary_y=False)
        # 꺾은선그래프: 포인트 위에 퍼센트 표시
        fig2.add_trace(go.Scatter(
            x=df_acc['시간대'], y=df_acc['치사율(%)'], name="치사율(%)", 
            mode='lines+markers+text', line=dict(color='#e74c3c', width=3),
            text=df_acc['치사율(%)'], textposition='top center', texttemplate='%{text}%'
        ), secondary_y=True)
        
        update_clean_grid(fig2, "시간대별 평균 교통량 대비 과속 치사율 분석", "평균 교통량", 
                          [0, df_traffic_grouped['전차종합계'].max()*1.3], "치사율 (%)", [0, df_acc['치사율(%)'].max()*2.0])
        st.plotly_chart(fig2, use_container_width=True)

    with side_col:
        st.markdown('<div class="table-container">', unsafe_allow_html=True)
        
        st.markdown('<div class="table-title">🚗 사고 발생 Top 3</div>', unsafe_allow_html=True)
        acc_top3 = df_acc.sort_values(by='사고건수', ascending=False).head(3)
        acc_rows = "".join([f"<tr><td>{i+1}위</td><td>{row['시간대']}</td><td class='highlight-blue'>{row['사고건수']}건</td></tr>" for i, (_, row) in enumerate(acc_top3.iterrows())])
        st.markdown(f'<table class="custom-table"><thead><tr><th>순위</th><th>시간대</th><th>사고건수</th></tr></thead><tbody>{acc_rows}</tbody></table>', unsafe_allow_html=True)

        st.markdown('<div class="table-title">⚰️ 치사율 Top 3</div>', unsafe_allow_html=True)
        rate_top3 = df_acc.sort_values(by='치사율(%)', ascending=False).head(3)
        rate_rows = "".join([f"<tr><td>{i+1}위</td><td>{row['시간대']}</td><td class='highlight-red'>{row['치사율(%)']}%</td></tr>" for i, (_, row) in enumerate(rate_top3.iterrows())])
        st.markdown(f'<table class="custom-table"><thead><tr><th>순위</th><th>시간대</th><th>치사율</th></tr></thead><tbody>{rate_rows}</tbody></table>', unsafe_allow_html=True)
        
        st.markdown(
            f"""
            <div class="summary-box">
                <div class="summary-title">📊 핵심 요약</div>
                <div class="summary-item">
                    • <b>최다 사고 발생</b><br>
                    &nbsp;&nbsp;👉 {max_acc_row['시간대']}<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;건수: {int(max_acc_row['사고건수']):,}건
                </div>
                <div class="summary-item">
                    • <b>최고 치사율 기록</b><br>
                    &nbsp;&nbsp;👉 <span class="summary-highlight">{max_rate_row['시간대']}</span><br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;치사율: <span class="summary-highlight">{max_rate_row['치사율(%)']}%</span>
                </div>
                <hr style="margin: 10px 0; border-color: #cbd5e1;">
                <div class="summary-item" style="font-size: 0.9rem;">
                    💡 <b>결론</b>: 사고가 가장 많이 일어나는 시간대와 치사율이 높은 시간대는 차이가 있습니다. 교통량이 적어지는 심야/새벽 시간대의 과속 예방이 매우 중요합니다.
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    show_analysis()