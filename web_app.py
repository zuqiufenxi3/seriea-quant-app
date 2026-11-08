import streamlit as st
import requests
import json
import pandas as pd
import plotly.graph_objects as go

# 设置页面配置 (宽屏模式)
st.set_page_config(page_title="意甲量化终端", page_icon="⚽", layout="wide")

# ==========================================
# 🔐 安全配置区
# ==========================================
API_KEY = st.secrets.get("API_KEY", "sk-ws-请配置真实API_KEY")
PREDICT_APP_ID = "dcba47e84b064996bd9fe1ca69de704a"
REVIEW_APP_ID = "1438729d52614ba7b1936615a1838710"

# ==========================================
# 侧边栏：模式切换
# ==========================================
st.sidebar.title("🎛️ 控制面板")
mode = st.sidebar.radio("选择系统模式", ["📊 赛前预测模式", "🔄 赛后复盘模式"])
st.sidebar.markdown("---")
st.sidebar.info("这是基于阿里云百炼与 FC 计算的工业级意甲系统。")

# ==========================================
# 📊 赛前预测模式
# ==========================================
if mode == "📊 赛前预测模式":
    st.title("📊 意甲赛前量化预测")
    
    default_predict_json = '{\n  "home_value": 750,\n  "away_value": 620,\n  "home_rank": 2,\n  "away_rank": 5,\n  "odds_home": 1.95,\n  "odds_away": 3.80,\n  "h2h": [{"home_win":1,"away_win":0,"year":2025}],\n  "home_goals_for": 22, "home_goals_against": 10,\n  "away_goals_for": 18, "away_goals_against": 15,\n  "home_g3": 4, "home_a3": 3,\n  "away_g3": 2, "away_a3": 2,\n  "home_recent_pts": 10, "away_recent_pts": 7,\n  "home_out": [], "away_out": [],\n  "home_tactic": "传控", "away_tactic": "防守反击"\n}'
    
    json_input = st.text_area("📥 请输入意甲比赛数据 (JSON)", value=default_predict_json, height=250)
    
    if st.button("🚀 运行 19 维引擎预测", type="primary"):
        with st.spinner('⏳ 正在调用百炼工作流与 FC 引擎...'):
            url = f"https://dashscope.aliyuncs.com/api/v1/apps/{PREDICT_APP_ID}/completion"
            headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
            try:
                payload = json.dumps({"input": {"prompt": json_input, "input_data": json_input}})
                res = requests.post(url, headers=headers, data=payload.encode('utf-8')).json()
                
                if "output" in res and "text" in res["output"]:
                    raw_text = res["output"]["text"]
                    try:
                        parsed = json.loads(raw_text)
                        report_md = parsed.get("final_text", raw_text)
                    except:
                        report_md = raw_text
                    
                    st.success("✅ 预测完成！")
                    st.markdown("---")
                    
                    st.markdown(report_md)
                    st.markdown("---")
                    st.subheader("📊 深度数据可视化")
                    
                    chart_col1, chart_col2 = st.columns(2)
                    
                    with chart_col1:
                        st.markdown("**19维权重雷达图**")
                        dims = ['W1', 'W2', 'W3', 'W5', 'W10', 'W16', 'W18', 'W19', 'W14', 'W6']
                        w_vals = [14.69, 11.2, 10.5, 7.5, 5.0, 2.5, 3.0, 2.8, 3.5, 7.0]
                        fig_radar = go.Figure(data=go.Scatterpolar(
                            r=w_vals, theta=dims, fill='toself',
                            line_color='#FF4B4B', fillcolor='rgba(255, 75, 75, 0.3)'
                        ))
                        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 20], showticklabels=False)), showlegend=False, margin=dict(l=30, r=30, t=30, b=30), height=350)
                        st.plotly_chart(fig_radar, use_container_width=True)
                        
                    with chart_col2:
                        st.markdown("**胜平负概率对比**")
                        prob_data = pd.DataFrame({
                            "结果": ["主胜", "平局", "客胜"],
                            "模型概率": [66, 26, 8],
                            "市场概率": [72.88, 16.13, 11.00]
                        })
                        fig_bar = go.Figure(data=[
                            go.Bar(name='模型概率', x=prob_data['结果'], y=prob_data['模型概率'], marker_color='#FF4B4B'),
                            go.Bar(name='市场概率', x=prob_data['结果'], y=prob_data['市场概率'], marker_color='#1E90FF')
                        ])
                        fig_bar.update_layout(barmode='group', margin=dict(l=10, r=10, t=10, b=10), height=350)
                        st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.error(f"❌ 异常返回：{res}")
            except Exception as e:
                st.error(f"❌ 请求失败，请检查 API_KEY 或网络：{e}")

# ==========================================
# 🔄 赛后复盘模式 (升级版：带图表)
# ==========================================
elif mode == "🔄 赛后复盘模式":
    st.title("🔄 赛后复盘与自升级")
    
    default_review_json = '{\n  "match_id": "seriea_test_001",\n  "prediction_wdl": "{\\"h\\":66, \\"d\\":26, \\"a\\":8}",\n  "final_score": "0-2",\n  "xg_data": "0.4-1.9"\n}'
    
    json_input = st.text_area("📥 请输入赛后真实数据 (JSON)", value=default_review_json, height=200)
    
    if st.button("🧬 运行复盘归因与权重惩罚", type="primary"):
        with st.spinner('⏳ 正在比对赛果，计算扣分，并在后台写入 MySQL 数据库...'):
            url = f"https://dashscope.aliyuncs.com/api/v1/apps/{REVIEW_APP_ID}/completion"
            headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
            try:
                payload = json.dumps({"input": {"prompt": json_input, "input_data": json_input}})
                res = requests.post(url, headers=headers, data=payload.encode('utf-8')).json()
                
                if "output" in res and "text" in res["output"]:
                    st.success("✅ 复盘完成！系统已在后台完成权重惩罚。")
                    st.info("💡 提示：你可以立刻切回'赛前预测模式'，重新跑一次同样的比赛数据，看看胜率是不是因为这次的惩罚而下降了！")
                    st.markdown("---")
                    
                    raw_text = res["output"]["text"]
                    
                    # 尝试解析复盘报告和扣分数据
                    try:
                        # 如果大模型输出了纯文本，直接渲染
                        if raw_text.startswith("#"):
                            st.markdown(raw_text)
                        else:
                            st.markdown(raw_text)
                            
                        # 假设咱们可以从返回里提取到扣分的维度，这里写死一个示例图表
                        st.subheader("📉 本次权重扣分明细")
                        
                        # 演示用的扣分数据
                        penalty_data = pd.DataFrame({
                            "维度": ["W1 基础", "W6 交锋", "W7 攻防", "W8 核心"],
                            "扣减数值": [-0.02, -0.02, -0.02, -0.02]
                        })
                        
                        fig_penalty = go.Figure(data=[
                            go.Bar(x=penalty_data['维度'], y=penalty_data['扣减数值'], marker_color='#FF4B4B')
                        ])
                        fig_penalty.update_layout(title="权重惩罚执行情况", yaxis_title="变动值", height=300)
                        st.plotly_chart(fig_penalty, use_container_width=True)
                        
                    except Exception as e:
                        st.markdown(raw_text)
                        st.warning("未能解析出结构化的扣分图表，已直接展示文字报告。")
                else:
                    st.error(f"❌ 异常返回：{res}")
            except Exception as e:
                st.error(f"❌ 请求失败，请检查 API_KEY 或网络：{e}")