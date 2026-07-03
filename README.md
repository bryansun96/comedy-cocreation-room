# Comedy Co-creation Room

## 本地运行

```bash
python3 -m pip install -r requirements.txt
cp .env.example .env
# 在 .env 中填写 DEEPSEEK_API_KEY
streamlit run app.py
```

## ModelScope 部署配置

在 Studio 的环境变量或 Secrets 中配置：

```text
DEEPSEEK_API_KEY=<你的 DeepSeek API Key>
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-pro
```

API Key 只能保存在部署平台的 Secret 中，不要写入源码或提交到 GitHub。
