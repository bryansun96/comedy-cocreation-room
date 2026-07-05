# Comedy Co-creation Room

## 本地运行

```bash
python3 -m pip install -r requirements.txt
cp .env.example .env
# 在 .env 中填写 DEEPSEEK_API_KEY
streamlit run app.py
```

## 视觉样例 v0

独立的叙事型视觉样例不会调用模型，也不会修改正式应用的 Session State：

```bash
streamlit run v0_preview.py
```

页面使用本地海岸照片、编辑感排版和 CSS 原创线描，相关摄影来源记录在
`assets/PHOTO_CREDITS.md`。

## ModelScope 部署配置

在 Studio 的环境变量或 Secrets 中配置：

```text
DEEPSEEK_API_KEY=<你的 DeepSeek API Key>
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-pro
```

API Key 只能保存在部署平台的 Secret 中，不要写入源码或提交到 GitHub。
