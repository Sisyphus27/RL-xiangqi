"""
Author: zy
Date: 2025-07-01 08:58:17
LastEditTime: 2025-07-16 19:17:17
LastEditors: zy
Description:
FilePath: \Ex_TAMP\paper_collect\dblp_search.py

"""

import requests
import time
import urllib3
from urllib.parse import unquote
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
import logging
from tqdm import tqdm
import concurrent.futures
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Union, Optional, Iterable, Set
import argparse
import json
import os
import threading
import random

# =============================================================
# 配置与数据结构
# =============================================================

# 默认关键词与会议（可直接在此处增删）
DEFAULT_KEYWORDS: List[str] = [
    "UAV",
    "Vehicle",
    "Routing",
    "ride-hailing",
    "Multi-Agent",
    "Reinforcement Learning",
    "OD",
    "Task Assignment",
    "task",
    "order dispatching",
    "Aerial–Ground",
    "Collaborative",
    "Ground-Air-Space",
    "Spatial Crowdsourcing",
    "Urban",
    "Dependency",
    "Traffic",
    "Congestion",
    "POI",
    "Crowdsensing",
    "Markov",
    "Human-In-the-Loop",
    "Trajectory",
    "crowdsourced",
    "spatial",
    "time",
    "space",
    "temporal",
    "graph",
    "recommendation",
    "relation",
    "link",
    "edge",
    "heterogeneous",
    "ride",
    "LLM",
    "large language model",
    "Origin-Destination",
    "multiscale",
    "Multimodal",
    "Multi-view",
    "Multi-granularity",
    "alignment",
    "hyperbolic",
]

DEFAULT_VENUES: List[str] = [
    "kdd",
    "icml",
    "neurips",
    "aaai",
    "ijcai",
    "iclr",
    "icde",
    "sigmod",
    "vldb",
    "tkde",
    "tmc",
    "www",
    "cvpr",
    "acl",
    "iccv",
    "pami",
    "sigir",
    "tpami",
]


@dataclass
class SearchConfig:
    keywords: List[str]
    venues: List[str]
    start_year: int = 2020
    end_year: int = 2025
    max_results: int = 40000
    max_per_page: int = 100
    max_pages: int = 50
    sleep_time: float = 1.0
    max_workers: int = 8
    max_loops: int = 10
    full_hits_limit: int = 3
    use_full_hits_limit: bool = False  # 是否启用“连续满页即停止”
    timeout: int = 10
    retry_total: int = 3
    retry_backoff: float = 1.0
    max_attempts: int = 3
    thread_timeout: int = 40  # 单查询超时时间（秒）
    retry_wait: float = 2.0
    base_url: str = "https://dblp.org/search/publ/api"
    stop_on_duplicate_page: bool = True  # 若连续页无新增结果则停止
    duplicate_pages_limit: int = 2       # 连续多少页无新增后停止
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger("dblp_search"))
    raw_config: Dict = field(default_factory=dict)  # 存储原始配置字典
    enable_abstract: bool = True  # 是否获取论文摘要（可能导致 Semantic Scholar 429 错误）

    def validate(self):
        assert self.start_year <= self.end_year, "start_year must <= end_year"
        assert self.max_per_page > 0 and self.max_pages > 0
        assert self.max_workers > 0
        return self


class TqdmLoggingHandler(logging.Handler):
    """将日志通过 tqdm.write 输出，避免破坏进度条。"""

    def __init__(self, level=logging.NOTSET):
        super().__init__(level)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            tqdm.write(msg)
        except Exception:
            # 回退到标准输出
            print(self.format(record))


def configure_logging(level: int = logging.INFO, use_tqdm: bool = True) -> logging.Logger:
    """配置日志模块，避免重复、与进度条友好。

    - 清理已有处理器，保持单一输出渠道。
    - 关闭向根记录器传播，避免重复打印。
    - 可选使用 TqdmLoggingHandler，防止破坏 tqdm 进度条。
    """
    logger = logging.getLogger("dblp_search")
    logger.setLevel(level)
    # 清理旧处理器，防止重复
    if logger.handlers:
        logger.handlers.clear()
    handler: logging.Handler = TqdmLoggingHandler() if use_tqdm else logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(threadName)s | %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    # 避免消息向上冒泡到 root，导致重复输出
    logger.propagate = False
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    return logger


def is_venue_match(venue_str: str, venues: List[str]) -> bool:
    """检查会议是否匹配"""
    venue_str = venue_str.lower().replace(" ", "")
    return any(v.lower().replace(" ", "") in venue_str for v in venues)


def cartesian_product(arr1: List[str], arr2: List[str]) -> List[str]:
    """生成笛卡尔积"""
    return [f"{a} {b}" for a in arr1 for b in arr2]


def safe_strip(val: Union[str, List[str]]) -> str:
    """安全去除字符串两端空格"""
    if isinstance(val, list):
        return val[0].strip() if val and isinstance(val[0], str) else ""
    return val.strip() if isinstance(val, str) else ""


def extract_doi(url: str) -> str:
    """统一提取 DOI 的函数"""
    if not url or "doi.org/" not in url:
        return ""
    return unquote(url.split("doi.org/")[-1].split("?")[0].split("#")[0])


def fetch_abstract_semantic_scholar(
    doi: str,
    config,
    session: Optional[requests.Session] = None
) -> str:
    """
    从 Semantic Scholar API 获取论文摘要

    Args:
        doi: 论文 DOI
        config: 搜索配置对象（SearchConfig）
        session: 可选的 HTTP 会话对象（用于会话复用）

    Returns:
        摘要文本，失败返回空字符串
    """
    # DOI 预过滤：验证基本格式
    if not doi or len(doi) <= 10 or "10." not in doi:
        return ""

    try:
        # 从配置读取 API 参数
        api_config = config.raw_config.get("abstract_apis", {}).get("semantic_scholar", {})
        base_url = api_config.get("base_url", "https://api.semanticscholar.org/graph/v1/paper")
        fields = api_config.get("fields", "paperId,title,abstract")
        timeout = api_config.get("timeout", 10)
        sleep_time = api_config.get("rate_limit", {}).get("sleep_between_requests", 0.5)

        # 速率限制：每次请求前暂停
        time.sleep(sleep_time)

        url = f"{base_url}/DOI:{doi}"
        params = {"fields": fields}

        # 使用传入的会话或创建新请求
        if session:
            response = session.get(url, params=params, timeout=timeout)
        else:
            response = requests.get(url, params=params, timeout=timeout)

        response.raise_for_status()
        data = response.json()
        abstract = data.get("abstract", "")

        return abstract

    except requests.exceptions.Timeout:
        config.logger.warning(f"[ABSTRACT_TIMEOUT] DOI:{doi[:30]}...")
        return ""
    except requests.exceptions.RequestException as e:
        config.logger.warning(f"[ABSTRACT_ERROR] DOI:{doi[:30]}... → {e}")
        return ""
    except Exception as e:
        config.logger.error(f"[ABSTRACT_UNEXPECTED] DOI:{doi[:30]}... → {e}")
        return ""


def create_retry_session(retry_total: int, retry_backoff: float) -> requests.Session:
    """创建带重试策略的会话"""
    retry_strategy = Retry(
        total=retry_total,
        connect=retry_total,
        read=retry_total,
        backoff_factor=retry_backoff,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def fetch_query_results(query: str, config: SearchConfig, cancel: Optional[threading.Event] = None) -> Tuple[Dict[str, Dict], str]:
    """单个关键词-会议组合的检索，返回结果字典和状态(success/exception)."""
    results: Dict[str, Dict] = {}
    session = create_retry_session(config.retry_total, config.retry_backoff)
    current_start = 0
    page_count = 0
    loop_count = 0
    consecutive_full_hits = 0
    last_last_paper_id: Optional[str] = None
    same_last_paper_count = 0
    consecutive_no_new = 0
    api_total_hits: Optional[int] = None

    try:
        while loop_count < config.max_loops:
            # 如收到取消信号，尽快退出
            if cancel is not None and cancel.is_set():
                config.logger.debug(f"[CANCEL] {query} 收到取消，提前结束")
                break
            loop_count += 1
            config.logger.debug(
                f"[FETCH] {query} loop={loop_count} start={current_start} page={page_count} size={len(results)}"
            )
            if current_start >= config.max_pages * config.max_per_page:
                config.logger.debug(f"[STOP] 超出最大页数: {query}")
                break

            params = {
                "q": query,
                "format": "json",
                "h": config.max_per_page,
                "f": current_start,
            }
            try:
                response = session.get(
                    config.base_url, params=params, verify=False, timeout=config.timeout
                )
                response.raise_for_status()
                data = response.json()
            except requests.exceptions.Timeout:
                config.logger.warning(f"[TIMEOUT] {query} params={params}")
                break
            except requests.exceptions.RequestException as e:
                config.logger.warning(f"[REQ_ERR] {query} params={params} error={e}")
                break

            hits_obj = data.get("result", {}).get("hits", {})
            # 读取 API 报告的总数，用于更精确的翻页终止
            if api_total_hits is None:
                total_raw = hits_obj.get("@total") or hits_obj.get("total")
                try:
                    api_total_hits = int(total_raw) if total_raw is not None else None
                except Exception:
                    api_total_hits = None
                if api_total_hits is not None:
                    config.logger.debug(f"[TOTAL] {query} api_total_hits={api_total_hits}")

            hits = hits_obj.get("hit", [])
            if not hits:
                config.logger.debug(f"[NO_HITS] {query} params={params}")
                break

            last_paper_id = extract_last_paper_id(hits)
            if last_paper_id == last_last_paper_id:
                same_last_paper_count += 1
            else:
                same_last_paper_count = 0
            last_last_paper_id = last_paper_id
            same_paper_threshold = getattr(config, 'same_paper_threshold', 2)
            if same_last_paper_count >= same_paper_threshold:
                config.logger.warning(f"[DUP_LAST] 多次相同最后论文 停止 {query}")
                break

            if config.use_full_hits_limit:
                consecutive_full_hits_updated = update_consecutive_hits(
                    len(hits), config.max_per_page, consecutive_full_hits, config.full_hits_limit, query, config.logger
                )
                if consecutive_full_hits_updated is None:
                    break
                consecutive_full_hits = consecutive_full_hits_updated

            before_size = len(results)
            process_hits(hits, results, config.start_year, config.end_year, query, config, session)
            after_size = len(results)

            # 连续一页没有新增结果判定
            if config.stop_on_duplicate_page and after_size == before_size:
                consecutive_no_new += 1
            else:
                consecutive_no_new = 0
            min_duplicate_pages = getattr(config, 'min_duplicate_pages', 1)
            if config.stop_on_duplicate_page and consecutive_no_new >= max(min_duplicate_pages, config.duplicate_pages_limit):
                config.logger.debug(f"[STOP_DUP_PAGE] {query} 无新增结果")
                break

            current_start += config.max_per_page
            page_count += 1
            # 如果 API 提供总数，当偏移量已覆盖总数时停止
            if api_total_hits is not None and current_start >= api_total_hits:
                config.logger.debug(f"[STOP_TOTAL] {query} reached api_total_hits={api_total_hits}")
                break
            if page_count >= config.max_pages:
                config.logger.debug(f"[STOP_MAX_PAGES] {query}")
                break
            # 加入随机抖动，缓解 429
            jitter_min = getattr(config, 'jitter_min', 0.8)
            jitter_max = getattr(config, 'jitter_max', 1.2)
            jitter = jitter_min + (jitter_max - jitter_min) * random.random()
            time.sleep(max(0.0, config.sleep_time * jitter))
        return results, "success"
    except Exception as e:
        config.logger.error(f"[EXCEPTION] {query} error={e}")
        return {}, "exception"


def extract_last_paper_id(hits: List[Dict]) -> str:
    """提取最后一篇论文的唯一标识"""
    if not hits:
        return ""
    last_hit = hits[-1]
    info = last_hit.get("info", {})
    title = safe_strip(info.get("title", "N/A"))
    year = safe_strip(info.get("year", ""))
    doi = extract_doi(info.get("ee", ""))
    return doi if doi else f"{title}_{year}"


def update_consecutive_hits(
    hits_len: int,
    max_per_page: int,
    consecutive_full_hits: int,
    full_hits_limit: int,
    query: str,
) -> Union[int, None]:
    """更新连续满页计数"""
    if hits_len < max_per_page:
        return 0
    consecutive_full_hits += 1
    if consecutive_full_hits >= full_hits_limit:
        logging.warning(
            f"连续{full_hits_limit}次满页，疑似陷入死循环，提前终止: {query}"
        )
        return None
    return consecutive_full_hits


def process_hits(
    hits: List[Dict],
    results: Dict[str, Dict],
    start_year: int,
    end_year: int,
    query: str,
    config=None,
    session: Optional[requests.Session] = None,
):
    """处理检索结果"""
    keyword_part = query.rsplit(" ", 1)[0]
    for hit in hits:
        info = hit.get("info", {})
        title = safe_strip(info.get("title", "N/A"))
        year_str = safe_strip(info.get("year", ""))
        venue = safe_strip(info.get("venue", "")) or safe_strip(
            info.get("booktitle", "")
        )
        ee = info.get("ee", "")
        doi = extract_doi(ee)

        if not title or title == "N/A" or not year_str.isdigit():
            continue

        year_int = int(year_str)
        if start_year <= year_int <= end_year:
            composite_key = doi if doi else f"{title}_{year_int}"
            if composite_key not in results:
                # 获取摘要（如果配置启用且提供了 config 和 session）
                abstract = ""
                enable_abstract = getattr(config, 'enable_abstract', True)
                if enable_abstract and config and session and doi:
                    abstract = fetch_abstract_semantic_scholar(doi, config, session)

                results[composite_key] = {
                    "title": title,
                    "year": year_int,
                    "venue": venue,
                    "doi": doi,
                    "url": ee,
                    "abstract": abstract,
                    "source_keyword": {keyword_part},
                }
            else:
                results[composite_key]["source_keyword"].add(keyword_part)


def fetch_query_results_with_timeout(query: str, config: SearchConfig):
    # 使用可取消的守护线程，防止超时后后台线程继续运行
    # 从配置文件读取 thread_timeout，默认使用 40
    thread_timeout = getattr(config, 'thread_timeout', 40)

    result: Dict[str, Dict] = {}
    status = "exception"
    finished = threading.Event()
    cancel = threading.Event()

    def target():
        nonlocal result, status
        result, status = fetch_query_results(query, config, cancel=cancel)
        finished.set()

    t = threading.Thread(target=target, name=f"Fetcher-{query[:12]}", daemon=True)
    t.start()
    t.join(thread_timeout)
    if not finished.is_set():
        cancel.set()
        config.logger.warning(f"[TIMEOUT_THREAD] {query} > {thread_timeout}s，已请求取消")
        # 再等待片刻让内部循环感知取消
        t.join(1.0)
        return {}, "exception"
    return result, status


def fetch_query_results_with_retry(query: str, config: SearchConfig) -> Dict[str, Dict]:
    config.logger.info(f"[START] {query}")
    thread_timeout = getattr(config, 'thread_timeout', 40)
    for attempt in range(1, config.max_attempts + 1):
        result, status = fetch_query_results_with_timeout(query, config)
        if status == "success":
            config.logger.info(f"[END] {query} success")
            return result
        if attempt < config.max_attempts:
            config.logger.warning(
                f"[RETRY] {query} attempt={attempt}/{config.max_attempts} waiting {config.retry_wait}s"
            )
            time.sleep(config.retry_wait)
    config.logger.error(f"[FAIL] {query} after {config.max_attempts} attempts")
    return {}


def normalize_results(results: Iterable[Dict[str, Union[str, int, Set[str]]]]) -> pd.DataFrame:
    """规范化结果集合为 DataFrame 并去重排序。"""
    rows = []
    for item in results:
        # 拷贝避免副作用
        row = dict(item)
        if isinstance(row.get("source_keyword"), set):
            row["source_keyword"] = ";".join(sorted(row["source_keyword"]))
        rows.append(row)
    if not rows:
        return pd.DataFrame(columns=["title", "year", "venue", "doi", "url", "abstract", "source_keyword"])
    df = pd.DataFrame(rows)
    if "doi" not in df.columns:
        df["doi"] = ""
    df["doi"] = df["doi"].fillna("")
    # 生成 composite key
    df["_ck"] = df.apply(lambda x: x["doi"] if x["doi"] else f"{x['title']}_{x['year']}", axis=1)
    df = df.sort_values(by=["_ck", "year"], ascending=[True, False])
    df = df.drop_duplicates(subset=["_ck"], keep="last")
    df = df.drop(columns=["_ck"]).sort_values(by="year", ascending=False)
    # 调整列顺序（包含 abstract 列）
    wanted = ["title", "year", "venue", "doi", "url", "abstract", "source_keyword"]
    cols = [c for c in wanted if c in df.columns] + [c for c in df.columns if c not in wanted]
    return df[cols]


def save_to_csv(data: Iterable[Dict[str, Union[str, int, Set[str]]]], filename: str = "papers.csv", logger: Optional[logging.Logger] = None) -> pd.DataFrame:
    df = normalize_results(data)
    if df.empty:
        (logger or logging.getLogger("dblp_search")).warning("[SAVE] 无数据")
        return df
    df.to_csv(filename, index=False, encoding="utf-8")
    (logger or logging.getLogger("dblp_search")).info(f"[SAVE] {len(df)} rows -> {filename}")
    return df


def build_queries(keywords: List[str], venues: List[str]) -> List[str]:
    return [f"{k} {v}" for k in keywords for v in venues]


def run_search(config: SearchConfig) -> pd.DataFrame:
    config.validate()
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    config.logger.info(
        f"[CONFIG] years={config.start_year}-{config.end_year} KW={len(config.keywords)} VENUE={len(config.venues)}"
    )
    queries = build_queries(config.keywords, config.venues)
    config.logger.info(f"[QUERIES] total={len(queries)}")
    all_results: Dict[str, Dict] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=config.max_workers) as executor:
        future_to_query = {executor.submit(fetch_query_results_with_retry, q, config): q for q in queries}
        # 逐个等待，tqdm 显示进度
        for future in tqdm(concurrent.futures.as_completed(future_to_query), total=len(queries), desc="检索组合", unit="组"):
            q = future_to_query[future]
            try:
                result_dict = future.result(timeout=config.timeout + 50)
            except concurrent.futures.TimeoutError:
                config.logger.warning(f"[FUTURE_TIMEOUT] {q}")
                continue
            except Exception as exc:
                config.logger.warning(f"[FUTURE_EXC] {q} exc={exc}")
                continue
            # 合并结果（主线程操作，避免竞态）
            for k, v in result_dict.items():
                if k not in all_results:
                    all_results[k] = v
                else:
                    all_results[k]["source_keyword"].update(v["source_keyword"])
    # 转换
    flat_results = list(all_results.values())
    if len(flat_results) > config.max_results:
        flat_results = flat_results[: config.max_results]
    df = normalize_results(flat_results)
    config.logger.info(f"[DONE] total={len(df)}")
    return df


def load_list_from_source(source: Union[str, List[str], None]) -> List[str]:
    """从各种来源加载列表，避免重复代码"""
    if source is None:
        return []

    if isinstance(source, str):
        if source.endswith('.json'):
            try:
                arr = json.loads(source)
                return [str(x) for x in arr] if isinstance(arr, list) else []
            except json.JSONDecodeError:
                return []
        elif os.path.exists(source):
            # 从文件读取
            return _read_lines(source)
        else:
            # 尝试解析为 JSON
            try:
                arr = json.loads(source)
                return [str(x) for x in arr] if isinstance(arr, list) else []
            except json.JSONDecodeError:
                return []

    elif isinstance(source, list):
        return [str(x) for x in source]

    return []


def load_json_config(config_path: Optional[str] = None) -> Dict:
    """加载 JSON 配置，使用默认值作为后备"""
    default_path = os.path.join(os.path.dirname(__file__), 'dblp_config.json')
    file_path = config_path or default_path

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # 返回空字典，使用代码中的默认值
        return {}


def default_config() -> SearchConfig:
    """从配置文件加载默认值，保持向后兼容"""
    config_data = load_json_config()

    # 从配置获取，如果不存在则使用代码中的常量
    search_config = config_data.get('search', {})
    api_config = config_data.get('api', {})
    pagination_config = config_data.get('pagination', {})
    termination_config = config_data.get('termination', {})

    return SearchConfig(
        keywords=search_config.get('default_keywords', list(DEFAULT_KEYWORDS)),
        venues=search_config.get('default_venues', list(DEFAULT_VENUES)),
        start_year=search_config.get('start_year', 2020),
        end_year=search_config.get('end_year', 2025),
        max_results=search_config.get('max_results', 40000),
        max_per_page=pagination_config.get('max_per_page', 100),
        max_pages=pagination_config.get('max_pages', 50),
        sleep_time=pagination_config.get('sleep_time', 1.0),
        max_workers=pagination_config.get('max_workers', 8),
        max_loops=pagination_config.get('max_loops', 10),
        full_hits_limit=termination_config.get('full_hits_limit', 3),
        use_full_hits_limit=termination_config.get('use_full_hits_limit', False),
        timeout=api_config.get('timeout', 10),
        retry_total=api_config.get('retry_total', 3),
        retry_backoff=api_config.get('retry_backoff', 1.0),
        max_attempts=api_config.get('max_attempts', 3),
        thread_timeout=api_config.get('thread_timeout', 40),
        base_url=api_config.get('base_url', "https://dblp.org/search/publ/api"),
        stop_on_duplicate_page=termination_config.get('stop_on_duplicate_page', True),
        duplicate_pages_limit=termination_config.get('duplicate_pages_limit', 2),
        enable_abstract=config_data.get('abstract_apis', {}).get('semantic_scholar', {}).get('enable', True),
        raw_config=config_data
    )

def _read_lines(path: str) -> List[str]:
    with open(path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="DBLP 批量检索：关键词×会议组合抓取并保存CSV",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    # 关键词/会议来源：默认使用内置；若提供任一覆盖项，则覆盖默认
    parser.add_argument('-k', '--keyword', action='append', help='追加一个关键词，可多次指定')
    parser.add_argument('--keywords-json', help='以JSON数组提供关键词，如 ["UAV","Drone"]')
    parser.add_argument('--keywords-file', help='从文本文件读取关键词，每行一个')

    parser.add_argument('-v', '--venue', action='append', help='追加一个会议，可多次指定')
    parser.add_argument('--venues-json', help='以JSON数组提供会议，如 ["kdd","aaai"]')
    parser.add_argument('--venues-file', help='从文本文件读取会议，每行一个')

    parser.add_argument('--start-year', type=int, help='起始年份')
    parser.add_argument('--end-year', type=int, help='结束年份')
    parser.add_argument('--max-pages', type=int, help='每个查询的最大翻页数')
    parser.add_argument('--max-per-page', type=int, help='每页条数')
    parser.add_argument('--max-workers', type=int, help='并发线程数')
    parser.add_argument('--sleep', type=float, dest='sleep_time', help='请求间隔秒')
    parser.add_argument('--timeout', type=int, help='单次请求超时秒')
    parser.add_argument('--max-attempts', type=int, help='网络失败重试次数')
    parser.add_argument('--retry-total', type=int, help='请求库重试总次数')
    parser.add_argument('--retry-backoff', type=float, help='请求库指数退避因子')
    parser.add_argument('--retry-wait', type=float, help='重试等待秒')
    parser.add_argument('--use-full-hits-limit', action='store_true', help='启用连续满页阈值停止')
    parser.add_argument('--full-hits-limit', type=int, help='连续满页停止阈值')
    parser.add_argument('--stop-on-dup', dest='stop_on_duplicate_page', action='store_true', help='连续无新增页时停止')
    parser.add_argument('--no-stop-on-dup', dest='stop_on_duplicate_page', action='store_false', help='不因无新增页停止')
    parser.set_defaults(stop_on_duplicate_page=True)
    parser.add_argument('--duplicate-pages-limit', type=int, help='连续无新增页阈值')

    parser.add_argument('--base-url', help='DBLP API 基础URL')
    parser.add_argument('-o', '--output', default='paper_collect/dblp_papers.csv', help='输出CSV路径')

    parser.add_argument('--log-level', default='INFO', choices=['DEBUG','INFO','WARNING','ERROR','CRITICAL'], help='日志等级')
    parser.add_argument('--no-tqdm', action='store_true', help='不使用tqdm友好日志处理器')
    return parser.parse_args()


def _override_list(defaults: List[str], *, json_str: Optional[str], file_path: Optional[str], items: Optional[List[str]]) -> List[str]:
    """使用通用列表加载函数，保持向后兼容"""
    # 按优先级：json_str > file_path > items > defaults
    if json_str:
        result = load_list_from_source(json_str)
        return result if result else list(defaults)
    if file_path:
        if not os.path.exists(file_path):
            raise FileNotFoundError(file_path)
        return load_list_from_source(file_path)
    if items:
        return items
    return list(defaults)


def _build_config_from_args(args: argparse.Namespace) -> SearchConfig:
    cfg = default_config()
    # 覆盖关键词/会议
    cfg.keywords = _override_list(
        cfg.keywords,
        json_str=args.keywords_json,
        file_path=args.keywords_file,
        items=args.keyword,
    )
    cfg.venues = _override_list(
        cfg.venues,
        json_str=args.venues_json,
        file_path=args.venues_file,
        items=args.venue,
    )
    # 批量应用参数覆盖，避免重复代码
    param_mappings = {
        'start_year': 'start_year',
        'end_year': 'end_year',
        'max_pages': 'max_pages',
        'max_per_page': 'max_per_page',
        'max_workers': 'max_workers',
        'sleep_time': 'sleep_time',
        'timeout': 'timeout',
        'max_attempts': 'max_attempts',
        'retry_total': 'retry_total',
        'retry_backoff': 'retry_backoff',
        'retry_wait': 'retry_wait',
        'full_hits_limit': 'full_hits_limit',
        'duplicate_pages_limit': 'duplicate_pages_limit',
        'thread_timeout': 'thread_timeout',
        'jitter_min': 'jitter_min',
        'jitter_max': 'jitter_max',
        'min_duplicate_pages': 'min_duplicate_pages'
    }

    for arg_name, config_attr in param_mappings.items():
        value = getattr(args, arg_name, None)
        if value is not None:
            setattr(cfg, config_attr, value)

    # 处理布尔标志
    if args.use_full_hits_limit:
        cfg.use_full_hits_limit = True
    if args.stop_on_duplicate_page is not None:
        cfg.stop_on_duplicate_page = args.stop_on_duplicate_page
    if args.base_url:
        cfg.base_url = args.base_url

    return cfg


def main():
    args = _parse_args()
    logger = configure_logging(level=getattr(logging, args.log_level), use_tqdm=(not args.no_tqdm))
    cfg = _build_config_from_args(args)
    cfg.logger = logger
    df = run_search(cfg)
    save_to_csv(df.to_dict("records"), filename=args.output, logger=logger)


if __name__ == "__main__":
    main()