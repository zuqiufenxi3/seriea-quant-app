import streamlit as st
import requests
import json
import pandas as pd
import plotly.graph_objects as go
import time
import re
from io import StringIO

# 设置页面配置 (宽屏模式)
st.set_page_config(page_title="意甲量化终端", page_icon="⚽", layout="wide")

# ==========================================
# 🔐 安全配置区
# ==========================================
API_KEY = st.secrets.get("API_KEY", "sk-ws-请配置真实API_KEY")
PREDICT_APP_ID = "dcba47e84b064996bd9fe1ca69de704a"
REVIEW_APP_ID = "1438729d52614ba7b1936615a1838710"

# 初始化本地历史记录 (刷新不丢失，但关闭网页会清空，绝对安全)
if "history" not in st.session_state:
    st.session_state.history = []

# ==========================================
# 侧边栏：模式切换
# ==========================================
st.sidebar.title("🎛️ 控制面板")
mode = st.sidebar.radio("选择系统模式", ["📊 单场预测", "🔄 赛后复盘", "📁 批量预测", "📈 本地历史记录"])
st.sidebar.markdown("---")
st.sidebar.info("这是基于阿里云百炼与 FC 计算的工业级意甲系统。")

# ==========================================
# 📊 单场预测模式 (加入可视化表单)
# ==========================================
if mode == "📊 单场预测":
    st.title("📊 意甲赛前量化预测")
    
    st.markdown("### 📝 输入比赛数据")
    # 使用两列布局把表单排开
    with st.form("match_data_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            home_value = st.number_input("主队身价 (万)", value=750)
            home_rank = st.number_input("主队排名", value=2)
            odds_home = st.number_input("主胜赔率", value=1.95, step=0.05)
            home_goals_for = st.number_input("主队进球", value=22)
            home_goals_against = st.number_input("主队失球", value=10)
        with col2:
            away_value = st.number_input("客队身价 (万)", value=620)
            away_rank = st.number_input("客队排名", value=5)
            odds_away = st.number_input("客胜赔率", value=3.80, step=0.05)
            away_goals_for = st.number_input("客队进球", value=18)
            away_goals_against = st.number_input("客队失球", value=15)
        with col3:
            home_tactic = st.selectbox("主队战术", ["传控", "防守反击", "高位逼抢"])
            away_tactic = st.selectbox("客队战术", ["防守反击", "传控", "高位逼抢"])
            
        submitted = st.form_submit_button("🚀 生成预测", type="primary")
        
    if submitted:
        # 自动拼装 JSON
        match_json = json.dumps({
            "home_value": home_value, "away_value": away_value,
            "home_rank": home_rank, "away_rank": away_rank,
            "odds_home": odds_home, "odds_away": odds_away,
            "home_goals_for": home_goals_for, "home_goals_against": home_goals_against,
            "away_goals_for": away_goals_for, "away_goals_against": away_goals_against,
            "home_tactic": home_tactic, "away_tactic": away_tactic
        }, ensure_ascii=False)
        
        with st.spinner('⏳ 正在调用百炼工作流与 FC 引擎...'):
            url = f"https://dashscope.aliyuncs.com/api/v1/apps/{PREDICT_APP_ID}/completion"
            headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
            try:
                payload = json.dumps({"input": {"prompt": match_json, "input_data": match_json}})
                res = requests.post(url, headers=headers, data=payload.encode('utf-8')).json()
                
                if "output" in res and "text" in res["output"]:
                    raw_text = res["output"]["text"]
                    try:
                        parsed = json.loads(raw_text)
                        report_md = parsed.get("final_text", raw_text)
                    except:
                        report_md = raw_text
                    
                    # 提取概率存入本地历史记录
                    try:
                        nums = re.search(r'主胜\s*(\d+).*?平局\s*(\d+).*?客胜\s*(\d+)', report_md)
                        if nums:
                            h_val, d_val, a_val = int(nums.group(1)), int(nums.group(2)), int(nums.group(3))
                            st.session_state.history.append({"场次": f"预测{len(st.session_state.history)+1}", "主胜": h_val, "平局": d_val, "客胜": a_val})
                    except: pass
                    
                    st.success("✅ 预测完成！")
                    st.markdown("---")
                    st.markdown(report_md)
                else:
                    st.error(f"❌ 异常返回：{res}")
            except Exception as e:
                st.error(f"❌ 请求失败，请检查 API_KEY 或网络：{e}")

# ==========================================
# 📈 本地历史记录模式 (全新升级)
# ==========================================
elif mode == "📈 本地历史记录":
    st.title("📈 本地预测走势追踪")
    st.markdown("这里展示你本次打开的网页中，连续预测的概率变化（刷新页面会重置，绝对保护隐私）。")
    
    if len(st.session_state.history) == 0:
        st.info("暂无数据，请先去'单场预测'跑几场比赛！")
    else:
        df_history = pd.DataFrame(st.session_state.history)
        df_history = df_history.set_index("场次")
        
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(x=df_history.index, y=df_history['主胜'], mode='lines+markers', name='主胜', line=dict(color='#FF4B4B', width=3)))
        fig_trend.add_trace(go.Scatter(x=df_history.index, y=df_history['平局'], mode='lines+markers', name='平局', line=dict(color='#1E90FF', width=3)))
        fig_trend.add_trace(go.Scatter(x=df_history.index, y=df_history['客胜'], mode='lines+markers', name='客胜', line=dict(color='#00CC96', width=3)))
        
        fig_trend.update_layout(title="预测胜率走势图", xaxis_title="预测场次", yaxis_title="概率 (%)", height=500)
        st.plotly_chart(fig_trend, use_container_width=True)
        st.dataframe(df_history, use_container_width=True)

# ==========================================
# 🔄 赛后复盘模式 (保留)
# ==========================================
elif mode == "🔄 赛后复盘":
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
                    st.info("💡 提示：你可以立刻切回'单场预测'，重新跑一次同样的数据，看看胜率是不是下降了！")
                    st.markdown("---")
                    st.markdown(res["output"]["text"])
                else:
                    st.error(f"❌ 异常返回：{res}")
            except Exception as e:
                st.error(f"❌ 请求失败：{e}")

# ==========================================
# 📁 批量预测引擎 (带文本粘贴)
# ==========================================
elif mode == "📁 批量预测":
    st.title("📁 意甲批量量化预测引擎")
    tab1, tab2 = st.tabs(["📄 上传文件", "📝 粘贴文本"])
    df = None
    with tab1:
        uploaded_file = st.file_uploader("上传比赛数据 (CSV格式)", type=["csv", "txt"])
        if uploaded_file is not None:
            try: df = pd.read_csv(uploaded_file)
            except Exception as e: st.error(f"读取失败：{e}")
    with tab2:
        csv_text = st.text_area("在这里粘贴 CSV 内容", height=200, placeholder="home_value,away_value...")
        if st.button("解析文本"):
            if csv_text.strip():
                try: df = pd.read_csv(StringIO(csv_text))
                except Exception as e: st.error(f"解析失败：{e}")
    if df is not None:
        st.write(f"成功读取到 **{len(df)}** 场比赛数据。")
        if st.button("🚀 启动批量计算", type="primary"):
            url = f"https://dashscope.aliyuncs.com/api/v1/apps/{PREDICT_APP_ID}/completion"
            headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
            results = []
            progress_bar = st.progress(0)
            for index, row in df.iterrows():
                match_json = row.to_json(force_ascii=False)
                try:
                    payload = json.dumps({"input": {"prompt": match_json, "input_data": match_json}})
                    res = requests.post(url, headers=headers, data=payload.encode('utf-8')).json()
                    raw_text = res["output"]["text"] if "output" in res else f"失败：{res}"
                    report_md = json.loads(raw_text).get("final_text", raw_text) if raw_text.startswith("{") else raw_text
                except Exception as e: report_md = f"异常：{e}"
                results.append({"序号": index + 1, "报告": report_md})
                progress_bar.progress((index + 1) / len(df))
                time.sleep(1) 
            st.success("✅ 批量完成！")
            result_df = pd.DataFrame(results)
            st.download_button("📥 下载报告", data=result_df.to_csv(index=False).encode('utf-8-sig'), file_name='batch.csv')