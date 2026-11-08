import streamlit as st
import requests
import json
import pandas as pd

# 设置页面配置
st.set_page_config(page_title="意甲量化终端", page_icon="⚽", layout="wide")

# ⚠️ 你的专属配置（在推上公网前，先填好这里）
API_KEY = st.secrets["API_KEY"]
PREDICT_APP_ID = "dcba47e84b064996bd9fe1ca69de704a"
REVIEW_APP_ID = "1438729d52614ba7b1936615a1838710" # 复盘ID

# 侧边栏：模式切换
st.sidebar.title("🎛️ 控制面板")
mode = st.sidebar.radio("选择系统模式", ["📊 赛前预测模式", "🔄 赛后复盘模式"])
st.sidebar.markdown("---")
st.sidebar.info("这是基于阿里云百炼与 FC 计算的工业级意甲系统。")

# ==========================================
# 预测模式界面
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
                    
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.markdown(report_md)
                    
                    with col2:
                        st.subheader("📈 权重雷达图")
                        chart_data = pd.DataFrame({
                            "维度": ["W1 基础", "W2 盘口", "W3 对位", "W5 战术", "W10 体能"],
                            "权重数值": [14.69, 11.2, 10.5, 7.5, 5.0]
                        }).set_index("维度")
                        st.bar_chart(chart_data)
                        st.caption("注：此处示例展示了权重前5的维度，实际系统可全量渲染。")
                else:
                    st.error(f"❌ 异常：{res}")
            except Exception as e:
                st.error(f"❌ 请求失败：{e}")

# ==========================================
# 复盘模式界面
# ==========================================
elif mode == "🔄 赛后复盘模式":
    st.title("🔄 赛后复盘与自升级")
    
    default_review_json = '{\n  "match_id": "seriea_test_001",\n  "prediction_wdl": "{\\"h\\":66, \\"d\\":26, \\"a\\":8}",\n  "final_score": "0-2",\n  "xg_data": "0.4-1.9"\n}'
    
    json_input = st.text_area("📥 请输入赛后真实数据 (JSON)", value=default_review_json, height=200)
    
    if st.button("🧬 运行复盘归因并更新权重", type="primary"):
        with st.spinner('⏳ 正在比对赛果，计算扣分，并写入数据库...'):
            url = f"https://dashscope.aliyuncs.com/api/v1/apps/{REVIEW_APP_ID}/completion"
            headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
            try:
                payload = json.dumps({"input": {"prompt": json_input, "input_data": json_input}})
                res = requests.post(url, headers=headers, data=payload.encode('utf-8')).json()
                
                if "output" in res and "text" in res["output"]:
                    st.success("✅ 复盘完成！系统已完成权重惩罚并写回数据库。")
                    st.markdown("---")
                    st.markdown(res["output"]["text"])
                else:
                    st.error(f"❌ 异常：{res}")
            except Exception as e:
                st.error(f"❌ 请求失败：{e}")