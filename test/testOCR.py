from zai import ZhipuAiClient

# 初始化客户端
client = ZhipuAiClient(api_key="1c68bbd7c3554897a9a8500eac0f0d5b.bIrdqi6ZLaxo97QB")

# image_url = "https://cdn.bigmodel.cn/static/logo/introduction.png"
image_url = "./example/ocr_demo.png"

# 调用布局解析 API
response = client.layout_parsing.create(
    model="glm-ocr",
    file=image_url
)

# 输出结果
print(response)