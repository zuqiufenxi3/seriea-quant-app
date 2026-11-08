import streamlit as st
import requests
import json
import pandas as pd
import plotly.graph_objects as go

# 设置页面配置 (宽屏模式)
st.set_page_config(page_title="意甲量化终端", page_icon="⚽", layout="wide")

# ==========================================
# 🔐 安全配置区：从云端保险箱 (Secrets) 读取
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
st.sidebar.caption("当前版本已关闭公网数据库直连，保障数据安全。")

# ==========================================
# 📊 赛前预测模式界面
# ==========================================
if mode == "📊 赛前预测模式":
    st.title("📊 意甲赛前量化预测")
    
    # 默认测试数据
    default_predict_json = '{\n  "home_value": 750,\n  "away_value": 620,\n  "home_rank": 2,\n  "away_rank": 5,\n  "odds_home": 1.95,\n  "odds_away": 3.80,\n  "h2h": [{"home_win":1,"away_win":0,"year":2025}],\n  "home_goals_for": 22, "home_goals_against": 10,\n  "away_goals_for": 18, "away_goals_against": 15,\n  "home_g3": 4, "home_a3": 3,\n  "away_g3": 2, "away_a3": 2,\n  "home_recent_pts": 10, "away_recent_pts": 7,\n  "home_out": [], "away_out": [],\n  "home_tactic": "传控", "away_tactic": "防守反击"\n}'
    
    json_input = st.text_area("📥 请输入意甲比赛数据 (JSON)", value=default_predict_json, height=250)
    
    if st.button("🚀 运行 19 维引擎预测", type="primary"):
        with st.spinner('⏳ 正在调用百炼工作流与 FC 引擎...'):
            url = f"https://dashscope.aliyuncs.com/api/v1/apps/{PREDICT_APP_ID}/completion"
            headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
            try:
                # 构造请求
                payload = json.dumps({"input": {"prompt": json_input, "input_data": json_input}})
                res = requests.post(url, headers=headers, data=payload.encode('utf-8')).json()
                
                if "output" in res and "text" in res["output"]:
                    raw_text = res["output"]["text"]
                    try:
                        # 尝试解析最终文本
                        parsed = json.loads(raw_text)
                        report_md = parsed.get("final_text", raw_text)
                    except:
                        report_md = raw_text
                    
                    st.success("✅ 预测完成！")
                    st.markdown("---")
                    
                    # 左右分栏展示
                    col1, col2 = st.columns([2, 1.2])
                    
                    with col1:
                        st.markdown(report_md)
                    
                    with col2:
                        # 绘制 Plotly 雷达图
                        st.subheader("📈 19维权重雷达图")
                        
                        # 演示数据：实际生产中可以通过解析大模型文本或直接从FC获取具体数值
                        dims = ['W1 基础实力', 'W2 盘口', 'W3 对位', 'W5 战术', 'W10 体能', 
                                'W16 门将', 'W18 机构', 'W19 热度', 'W14 演变', 'W6 交锋']
                        w_vals = [14.69, 11.2, 10.5, 7.5, 5.0, 2.5, 3.0, 2.8, 3.5, 7.0]
                        
                        fig_radar = go.Figure(data=go.Scatterpolar(
                            r=w_vals,
                            theta=dims,
                            fill='toself',
                            name='本场权重占比',
                            line_color='#FF4B4B',
                            fillcolor='rgba(255, 75, 75, 0.3)'
                        ))
                        
                        fig_radar.update_layout(
                            polar=dict(
                                radialaxis=dict(visible=True, range=[0, 20], showticklabels=False)
                            ),
                            showlegend=False,
                            margin=dict(l=30, r=30, t=30, b=30),
                            height=400
                        )
                        st.plotly_chart(fig_radar, use_container_width=True)
                        
                        # 附加一个小柱状图展示概率
                        st.subheader("📊 胜平负概率对比")
                        prob_data = pd.DataFrame({
                            "结果": ["主胜", "平局", "客胜"],
                            "模型概率": [66, 26, 8],
                            "市场概率": [72.88, 16.13, 11.00]
                        })
                        fig_bar = go.Figure(data=[
                            go.Bar(name='模型概率', x=prob_data['结果'], y=prob_data['模型概率'], marker_color='#FF4B4B'),
                            go.Bar(name='市场概率', x=prob_data['结果'], y=prob_data['市场概率'], marker_color='#1E90FF')
                        ])
                        fig_bar.update_layout(barmode='group', margin=dict(l=10, r=10, t=10, b=10), height=250)
                        st.plotly_chart(fig_bar, use_container_width=True)
                        
                else:
                    st.error(f"❌ 异常返回：{res}")
            except Exception as e:
                st.error(f"❌ 请求失败，请检查 API_KEY 或网络：{e}")

# ==========================================
# 🔄 赛后复盘模式界面
# ==========================================
elif mode == "🔄 赛后复盘模式":
    st.title("🔄 赛后复盘与自升级")
    
    default_review_json = '{\n  "match_id": "seriea_test_001",\n  "prediction_wdl": "{\\"h\\":66, \\"d\\":26, \\"a\\":8}",\n  "final_score": "0-2",\n  "xg_data": "0.4-1.9"\n}'
    
    json_input = st.text_area("📥 请输入赛后真实数据 (JSON)", value=default_review_json, height=200)
    
    if st.button("🧬 运行复盘归因", type="primary"):
        with st.spinner('⏳ 正在比对赛果，计算扣分，并在后台写入数据库...'):
            url = f"https://dashscope.aliyuncs.com/api/v1/apps/{REVIEW_APP_ID}/completion"
            headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
            try:
                payload = json.dumps({"input": {"prompt": json_input, "input_data": json_input}})
                res = requests.post(url, headers=headers, data=payload.encode('utf-8')).json()
                
                if "output" in res and "text" in res["output"]:
                    st.success("✅ 复盘完成！系统已在后台完成权重惩罚。")
                    st.markdown("---")
                    st.markdown(res["output"]["text"])
                else:
                    st.error(f"❌ 异常返回：{res}")
            except Exception as e:
                st.error(f"❌ 请求失败，请检查 API_KEY 或网络：{e}")