# 启动后端
cd d:\workplace\stockgpt\backend
uv sync          # 安装依赖（首次需要）
uv run uvicorn app.main:app --reload --port 8080

# 关闭后端进程
Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force

# 启动前端
cd d:\workplace\stockgpt\frontend
npm install      # 安装依赖（首次需要）
npm run dev      # 启动开发服务器

