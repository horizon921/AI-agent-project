from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import requests
import time
import random
import json
import os
import logging
from datetime import datetime
import urllib.parse

# 配置日志
logging.basicConfig(
    filename='logs/treehole_mcp.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

# 创建日志目录
os.makedirs('logs', exist_ok=True)
os.makedirs('data', exist_ok=True)

# 创建FastAPI应用
app = FastAPI(
    title="北大树洞爬虫 MCP Server",
    description="根据关键词爬取北大树洞内容的API服务。请先通过 /api/update_auth 更新认证信息。"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)

# 默认认证信息，需要用户通过 /api/update_auth 端点进行设置
auth_config = {
    "authorization": "",  # Bearer Token, e.g., "Bearer eyJ0eXAiOiJKV1..."
    "cookie": "",         # 完整的 Cookie 字符串, e.g., "JWTUser=...; pku_token=...; XSRF-TOKEN=...; _session=..."
    "uuid": "", # 通常固定或会变化，需要从浏览器获取
    "xsrf_token": "",     # XSRF-TOKEN cookie 的值 (不是整个 cookie 字符串，而是 token 本身)
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0",
    "sec_ch_ua": "\"Chromium\";v=\"136\", \"Microsoft Edge\";v=\"136\", \"Not.A/Brand\";v=\"99\"",
    "sec_ch_ua_platform": "\"Windows\""
}

# API基础URL
BASE_URL = "https://treehole.pku.edu.cn/api"

# 数据模型
class AuthConfigModel(BaseModel):
    authorization: str = Field(..., description="Bearer token for API authorization. e.g., 'Bearer eyJ0eXAiOiJKV1QiLCJhbG...'")
    cookie: str = Field(..., description="Complete cookie string from browser. e.g., 'JWTUser=...; pku_token=...; XSRF-TOKEN=...; _session=...'")
    uuid: str = Field(description="UUID sent in request headers. e.g., 'Web_PKUHOLE_2.0.0_WEB_UUID_xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'", default="Web_PKUHOLE_2.0.0_WEB_UUID_52b18907-3762-4f88-bdd4-8d1d89c90bf7")
    xsrf_token: str = Field(..., description="The value of the XSRF-TOKEN cookie (the token itself, not the 'XSRF-TOKEN=' part). e.g., 'eyJpdiI6Ikp4Ritq...'")
    user_agent: Optional[str] = Field("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0", description="User-Agent string.")
    sec_ch_ua: Optional[str] = Field("\"Chromium\";v=\"136\", \"Microsoft Edge\";v=\"136\", \"Not.A/Brand\";v=\"99\"", description="sec-ch-ua header value.")
    sec_ch_ua_platform: Optional[str] = Field("\"Windows\"", description="sec-ch-ua-platform header value.")


class SearchRequest(BaseModel):
    keyword: str
    page_start: int = 1
    page_end: int = 5
    limit: int = 25 # 每页获取的树洞主贴数量
    max_comments_per_post: int = 50 # 每个主贴最多获取的评论数量
    fetch_all_comments: bool = False # 是否获取一个主贴下的所有评论（如果为true，则max_comments_per_post失效）

class Comment(BaseModel):
    cid: int
    pid: int
    text: str
    timestamp: int
    name: str
    quote: Optional[Dict[str, Any]] = None

class TreeHolePost(BaseModel):
    pid: int
    text: Optional[str] # 树洞内容可能为null
    type: int
    timestamp: int
    reply: int
    likenum: int
    extra: Optional[Dict[str, Any]] = None
    tag: Optional[str] = None # 假设有tag字段
    is_follow: Optional[int] = None # 假设有is_follow字段
    comments: List[Comment] = []

class SearchResponse(BaseModel):
    total_posts_found_in_api: int # API返回的符合关键词的总帖子数
    fetched_posts_count: int      # 本次请求实际获取并处理的帖子数
    posts: List[TreeHolePost]

# 获取请求头
def get_headers():
    if not auth_config["authorization"] or not auth_config["cookie"] or not auth_config["xsrf_token"]:
        raise HTTPException(status_code=401, detail="认证信息未配置，请先调用 /api/update_auth 进行配置。")

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Authorization": auth_config["authorization"],
        "Connection": "keep-alive",
        "Cookie": auth_config["cookie"],
        "Host": "treehole.pku.edu.cn",
        "Referer": "https://treehole.pku.edu.cn/web/",
        "Sec-Fetch-Dest": "empty", # API请求通常是empty
        "Sec-Fetch-Mode": "cors",  # API请求通常是cors
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": auth_config["user_agent"],
        "Uuid": auth_config["uuid"],
        "X-Xsrf-Token": auth_config["xsrf_token"], # 直接使用从Cookie中提取的XSRF-TOKEN值
        "sec-ch-ua": auth_config["sec_ch_ua"],
        "sec-ch-ua-mobile": "?0", # 通常对于桌面浏览器是 ?0
        "sec-ch-ua-platform": auth_config["sec_ch_ua_platform"],
        "DNT": "1" # Do Not Track, 可选
    }
    return headers

# 获取树洞消息列表
def get_messages(page, limit, keyword=None, max_retries=3, retry_delay=2):
    url = f"{BASE_URL}/pku_hole?page={page}&limit={limit}"
    if keyword:
        # 需要对关键词进行URL编码
        encoded_keyword = urllib.parse.quote(keyword)
        url += f"&keyword={encoded_keyword}"
    
    logging.info(f"Requesting messages: {url}")
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=get_headers())
            logging.debug(f"Request headers for get_messages: {response.request.headers}")
            logging.debug(f"Response status for get_messages: {response.status_code}")
            logging.debug(f"Response content for get_messages (first 100 chars): {response.text[:100]}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = f"获取消息列表失败(第{attempt + 1}次尝试),请求URL: {url},错误信息: {e}"
            logging.error(error_msg)
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    
    error_msg = f"获取消息列表失败,已达到最大重试次数({max_retries}),请求URL: {url}"
    logging.error(error_msg)
    return None

# 获取评论
def get_comments_for_post(pid, page=1, limit=10, max_retries=3, retry_delay=2):
    url = f"{BASE_URL}/pku_comment_v3/{pid}?page={page}&limit={limit}"
    logging.info(f"Requesting comments for pid {pid}, page {page}: {url}")
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=get_headers())
            logging.debug(f"Request headers for get_comments: {response.request.headers}")
            logging.debug(f"Response status for get_comments: {response.status_code}")
            logging.debug(f"Response content for get_comments (first 100 chars): {response.text[:100]}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = f"获取评论失败(第{attempt + 1}次尝试),请求URL: {url},错误信息: {e}"
            logging.error(error_msg)
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    
    error_msg = f"获取评论失败,已达到最大重试次数({max_retries}),请求URL: {url}"
    logging.error(error_msg)
    return None

# 后台任务：保存爬取结果到文件
def save_search_result(keyword: str, data: SearchResponse):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/search_{keyword.replace(' ', '_')}_{timestamp}.json"
    
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data.dict(), f, ensure_ascii=False, indent=4)
        logging.info(f"搜索结果已保存到文件: {filename}")
    except Exception as e:
        logging.error(f"保存搜索结果到文件失败: {e}")


# 爬取树洞API路由
@app.post("/api/search", response_model=SearchResponse)
async def search_treehole(request: SearchRequest, background_tasks: BackgroundTasks):
    all_fetched_posts_data: List[TreeHolePost] = []
    api_total_posts_found = 0
    
    # 遍历页面爬取符合条件的树洞
    for page_num in range(request.page_start, request.page_end + 1):
        messages_response = get_messages(page_num, request.limit, request.keyword)
        
        if not messages_response or "data" not in messages_response or not messages_response["data"]:
            logging.warning(f"无法从页面 {page_num} 获取数据或数据为空。")
            continue
        
        messages_data = messages_response["data"]
        if page_num == request.page_start: # 仅在第一页时记录总数
            api_total_posts_found = messages_data.get("total", 0)
        
        page_posts_raw = messages_data.get("data", [])
        if not page_posts_raw:
            logging.info(f"页面 {page_num} 没有帖子。")
            # 如果当前页没有数据，且是API返回的最后一页之后，可以提前停止
            if "current_page" in messages_data and "last_page" in messages_data and \
               messages_data["current_page"] >= messages_data["last_page"]:
                logging.info(f"已到达最后一页 (API报告 {messages_data['last_page']}), 停止爬取。")
                break
            continue

        for post_raw in page_posts_raw:
            pid = post_raw.get("pid")
            if pid is None:
                logging.warning(f"发现一个没有pid的帖子: {post_raw}")
                continue

            current_post_comments = []
            if post_raw.get("reply", 0) > 0:
                comments_page = 1
                fetched_comments_count = 0
                
                while True:
                    if not request.fetch_all_comments and fetched_comments_count >= request.max_comments_per_post:
                        break

                    comments_response = get_comments_for_post(pid, comments_page, limit=min(10, request.max_comments_per_post - fetched_comments_count if not request.fetch_all_comments else 10) ) # 每次获取10条评论或剩余需要的评论
                    
                    if not comments_response or "data" not in comments_response or not comments_response["data"]:
                        logging.info(f"PID {pid} 的评论获取完毕或无数据。")
                        break
                    
                    comments_data = comments_response["data"]
                    page_comments_raw = comments_data.get("data", [])
                    
                    for comment_raw in page_comments_raw:
                        current_post_comments.append(Comment(**comment_raw))
                        fetched_comments_count += 1
                        if not request.fetch_all_comments and fetched_comments_count >= request.max_comments_per_post:
                            break
                    
                    if (not request.fetch_all_comments and fetched_comments_count >= request.max_comments_per_post) or \
                       comments_data.get("current_page", 1) >= comments_data.get("last_page", 1) or not page_comments_raw:
                        break
                        
                    comments_page += 1
                    time.sleep(random.uniform(0.1, 0.3)) # 获取评论分页间的短暂停顿
            
            # 使用Pydantic模型进行数据清洗和验证
            try:
                # 确保所有TreeHolePost期望的字段都存在于post_raw中，如果不存在则提供默认值或标记为Optional
                # 例如，如果API不返回'type', 'extra', 'tag', 'is_follow'，确保模型定义它们为Optional
                # 或者在转换前手动添加这些键（如果它们有默认值且API不提供）
                # 这里假设post_raw直接包含了TreeHolePost所需的核心字段
                # 对于可能缺失的字段，Pydantic模型中的Optional或默认值会处理
                current_post_data = TreeHolePost(
                    pid=post_raw.get("pid"),
                    text=post_raw.get("text"),
                    type=post_raw.get("type", 0), # 假设type默认为0
                    timestamp=post_raw.get("timestamp"),
                    reply=post_raw.get("reply",0),
                    likenum=post_raw.get("likenum",0),
                    extra=post_raw.get("extra"),
                    tag=post_raw.get("tag"),
                    is_follow=post_raw.get("is_follow"),
                    comments=current_post_comments
                )
                all_fetched_posts_data.append(current_post_data)
            except Exception as e:
                logging.error(f"处理帖子PID {pid} 时出错: {e}. 原始数据: {post_raw}")
            
        logging.info(f"完成处理页面 {page_num}。已获取 {len(all_fetched_posts_data)} 个帖子。")
        # 每页主贴请求之间添加延迟
        time.sleep(random.uniform(0.5, 1.5)) 
    
    search_result_data = SearchResponse(
        total_posts_found_in_api=api_total_posts_found,
        fetched_posts_count=len(all_fetched_posts_data),
        posts=all_fetched_posts_data
    )
    
    # 后台任务：保存结果到文件
    background_tasks.add_task(save_search_result, request.keyword, search_result_data)
    
    return search_result_data

# 更新认证信息API
@app.post("/api/update_auth", summary="更新爬虫使用的认证信息")
async def update_auth(config: AuthConfigModel):
    global auth_config
    auth_config["authorization"] = config.authorization
    auth_config["cookie"] = config.cookie
    auth_config["uuid"] = config.uuid
    auth_config["xsrf_token"] = config.xsrf_token
    auth_config["user_agent"] = config.user_agent
    auth_config["sec_ch_ua"] = config.sec_ch_ua
    auth_config["sec_ch_ua_platform"] = config.sec_ch_ua_platform
    
    logging.info(f"认证信息已更新: { {k: (v[:30] + '...' if isinstance(v, str) and len(v) > 30 else v) for k, v in auth_config.items()} }")
    
    # 测试认证信息 (可选, 但推荐)
    try:
        test_response = requests.get(f"{BASE_URL}/pku_hole?page=1&limit=1", headers=get_headers(), timeout=5)
        test_response.raise_for_status()
        logging.info("新的认证信息验证通过。")
        return {"status": "success", "message": "认证信息已更新并验证通过。"}
    except Exception as e:
        logging.error(f"新的认证信息验证失败: {str(e)}")
        # 不直接抛出HTTPException，而是返回错误信息，因为更新操作本身是成功的
        return {"status": "warning", "message": f"认证信息已更新，但验证失败: {str(e)}。请检查认证信息是否正确。"}

# 获取当前认证信息API (用于调试或检查)
@app.get("/api/current_auth", summary="获取当前爬虫使用的认证信息（部分隐藏）")
async def get_current_auth():
    # 避免完整暴露敏感信息
    censored_auth = auth_config.copy()
    if censored_auth["authorization"]:
        censored_auth["authorization"] = censored_auth["authorization"][:15] + "..."
    if censored_auth["cookie"]:
        censored_auth["cookie"] = censored_auth["cookie"][:30] + "..."
    if censored_auth["xsrf_token"]:
         censored_auth["xsrf_token"] = censored_auth["xsrf_token"][:15] + "..."
    return censored_auth

# 服务器根路径
@app.get("/")
async def root():
    return {
        "name": "北大树洞爬虫 MCP Server",
        "version": "1.1.0",
        "description": "根据关键词爬取北大树洞内容的API服务。请先通过 /api/update_auth 更新认证信息。",
        "endpoints": {
            "/docs": "API交互文档 (Swagger UI)",
            "/redoc": "API文档 (ReDoc)",
            "/api/update_auth": "POST - 更新认证信息",
            "/api/current_auth": "GET - 查看当前认证信息（部分隐藏）",
            "/api/search": "POST - 根据关键词搜索树洞内容"
        },
        "status": "请先通过 /api/update_auth 配置认证信息。" if not auth_config["authorization"] else "认证信息已配置。"
    }

