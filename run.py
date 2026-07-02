import uvicorn
import os

if __name__ == "__main__":
    # 必须使用 Railway 分配的端口，否则无法访问
    port = int(os.environ["PORT"])  # 注意：这里去掉了默认值，强制读取
    print(f"🚀 启动在端口: {port}")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )