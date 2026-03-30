"""
Author: zy
Date: 2025-07-01 08:58:17
LastEditTime: 2025-07-17 16:42:06
LastEditors: zy
Description:
FilePath: \Ex_TAMP\paper_collect\dblp_keywords_extract.py

"""

from __future__ import annotations

import pandas as pd
import re
import hashlib
from dataclasses import dataclass, field
from typing import List, Sequence, Union, Iterable, Tuple, Optional
import unicodedata
import logging
import argparse
import json
import os


logger = logging.getLogger("dblp_keywords_extract")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(h)
logger.setLevel(logging.INFO)


KeywordGroup = Union[str, Sequence[str]]


@dataclass
class ExtractConfig:
    """关键词提取配置类"""
    # 核心参数
    csv_path: str
    keywords: List[KeywordGroup]

    # 可选参数及默认值
    title_col: str = "title"
    match_all: bool = True
    strip_accents: bool = False
    case_insensitive: bool = True
    return_matches: bool = True
    output_path: Optional[str] = None

    # 输出命名配置
    output_prefix: str = "dblp_papers_matched"
    max_base_len: int = 50
    max_filename_length: int = 200  # Windows最大文件名255字符，留有余量

    # 日志记录器
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger("dblp_keywords_extract"))

    def validate(self):
        """验证配置参数"""
        if not self.csv_path:
            raise ValueError("csv_path 不能为空")
        if not self.keywords:
            raise ValueError("keywords 不能为空")
        if self.max_base_len <= 0:
            raise ValueError("max_base_len 必须为正数")
        return self


def _normalize_text(s: str, strip_accents: bool, case_insensitive: bool) -> str:
    if strip_accents:
        s = unicodedata.normalize("NFD", s)
        s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    if case_insensitive:
        s = s.lower()
    return s


def _get_nesting_level(item) -> int:
    """获取数据结构的嵌套层级。

    用于检测关键词列表的嵌套深度：
    - 0: 非列表 (如 "keyword")
    - 1: 单层列表 (如 ["a", "b"])
    - 2: 双层列表 (如 [["a", "b"], ["c"]])
    - 3+: 三层及以上 (如 [[["a", "b"], ["c"]]])
    """
    if not isinstance(item, (list, tuple)):
        return 0
    if len(item) == 0:
        return 1
    first = item[0]
    if isinstance(first, (list, tuple)):
        return 1 + _get_nesting_level(first)
    return 1


def _prepare_keywords(
    keywords: Sequence[KeywordGroup], strip_accents: bool, case_insensitive: bool
) -> Tuple[bool, List[List[str]]]:
    """规范化关键词结构，支持一维、二维、三维嵌套。

    结构说明：
    - 一维 ["a", "b"]: 所有关键词在同一组，用 match_all 控制 AND/OR
    - 二维 [["a", "b"], ["c"]]: 组内 OR，组间 AND
    - 三维 [[["a","b"],["c"]]]: 展平为二维处理（每个最内层列表展平为一组）
    """
    if not keywords:
        return False, [[]]

    # 检测嵌套层级
    level = _get_nesting_level(keywords)

    groups: List[List[str]] = []

    if level == 1:
        # 一维: ["a", "b", "c"] -> 作为一个组
        is_nested = False
        groups = [
            [
                _normalize_text(str(x), strip_accents, case_insensitive)
                for x in keywords
                if str(x).strip()
            ]
        ]
        return is_nested, groups

    elif level == 2:
        # 二维: [["a", "b"], ["c"]] -> 组内 OR，组间 AND
        is_nested = True
        for it in keywords:
            if isinstance(it, (list, tuple, set)):
                groups.append(
                    [
                        _normalize_text(str(x), strip_accents, case_insensitive)
                        for x in it
                        if str(x).strip()
                    ]
                )
            else:
                groups.append(
                    [_normalize_text(str(it), strip_accents, case_insensitive)]
                )
        return is_nested, groups

    else:
        # 三维及以上: [[["spatial", "crowd"], ["task"]], [["ride", "taxi"], ["dispatch"]]]
        # 这表示多个独立的二维查询配置，每个顶层元素是一个完整的查询
        # 处理为二维结构（取第一个元素，因为通常三维是包装）
        is_nested = True

        # 如果外层只有一个元素，如 [[["a", "b"], ["c"]]]，解包它
        if len(keywords) == 1 and isinstance(keywords[0], (list, tuple)):
            keywords = keywords[0]

        # 现在按二维结构处理
        for it in keywords:
            if isinstance(it, (list, tuple, set)):
                groups.append(
                    [
                        _normalize_text(str(x), strip_accents, case_insensitive)
                        for x in it
                        if str(x).strip()
                    ]
                )
            else:
                groups.append(
                    [_normalize_text(str(it), strip_accents, case_insensitive)]
                )
        return is_nested, groups


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


def default_extract_config() -> Dict:
    """从配置文件加载默认值"""
    config_data = load_json_config()
    return config_data.get('extract', {})


def load_keywords_from_source(source: Union[str, List[str], List[List[str]]]) -> List[KeywordGroup]:
    """从各种来源加载关键词"""
    if source is None:
        return []

    if isinstance(source, str):
        # 尝试解析为 JSON
        try:
            data = json.loads(source)
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass

        # 如果是文件路径
        if os.path.exists(source):
            try:
                with open(source, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content.startswith('[') and content.endswith(']'):
                        # JSON 格式
                        return json.loads(content)
                    else:
                        # 每行一个关键词
                        return [line.strip() for line in content.splitlines() if line.strip()]
            except (json.JSONDecodeError, IOError):
                return []

        # 单个关键词
        return [source]

    elif isinstance(source, list):
        return source

    return []


def extract_keywords(
    data: Union[str, pd.DataFrame],
    keywords: Sequence[KeywordGroup],
    *,
    title_col: str = "title",
    match_all: bool = True,
    strip_accents: bool = False,
    case_insensitive: bool = True,
    return_matches: bool = True,
) -> pd.DataFrame:
    """在论文标题列中进行模糊关键词匹配并返回匹配子集。

    支持两种关键词结构：
      1. 一维列表: ["uav", "graph"] → match_all 控制 AND / OR
      2. 嵌套结构: [["uav", "drone"], "graph"] → 内部OR, 组间AND (忽略 match_all)

    参数
    -----
    data : str | DataFrame
        CSV 文件路径或已加载的 DataFrame。
    keywords : 序列
        关键词或同义词组配置。
    title_col : str
        标题列列名。
    match_all : bool
        一维关键词列表时是否全部匹配。
    strip_accents : bool
        是否移除重音/变音符。
    case_insensitive : bool
        是否大小写不敏感。
    return_matches : bool
        是否添加 matched_terms 列。

    返回
    ----
    DataFrame：包含匹配行；若 return_matches=True，含 matched_terms 列。
    """
    if isinstance(data, str):
        df = pd.read_csv(data)
    else:
        df = data.copy()
    if title_col not in df.columns:
        raise ValueError(f"列 '{title_col}' 不存在")
    titles = df[title_col].fillna("").astype(str)
    titles_norm = titles.apply(
        lambda s: _normalize_text(s, strip_accents, case_insensitive)
    )

    is_nested, groups = _prepare_keywords(keywords, strip_accents, case_insensitive)

    matched_index: List[int] = []
    matched_terms: List[str] = []

    if is_nested:
        # 组内 OR，组间 AND
        for idx, text in titles_norm.items():
            row_hits = []
            ok = True
            for group in groups:
                hit_word = None
                for token in group:
                    if token and token in text:
                        hit_word = token
                        break
                if hit_word is None:
                    ok = False
                    break
                row_hits.append(hit_word)
            if ok:
                matched_index.append(idx)
                if return_matches:
                    matched_terms.append(";".join(row_hits))
    else:
        flat = groups[0]
        for idx, text in titles_norm.items():
            if match_all:
                if all(token and token in text for token in flat):
                    matched_index.append(idx)
                    if return_matches:
                        matched_terms.append(";".join([t for t in flat if t in text]))
            else:
                hits = [t for t in flat if t and t in text]
                if hits:
                    matched_index.append(idx)
                    if return_matches:
                        matched_terms.append(";".join(hits))

    result = df.loc[matched_index].copy()
    if return_matches:
        result["matched_terms"] = matched_terms
    return result


def extract_keywords_multi_group(
    data: Union[str, pd.DataFrame],
    keywords_3d: Sequence[Sequence[Sequence[str]]],
    *,
    title_col: str = "title",
    match_all: bool = True,
    strip_accents: bool = False,
    case_insensitive: bool = True,
) -> pd.DataFrame:
    """处理 Level 3 嵌套结构：将多个 Level 2 查询分别执行，合并结果。

    Args:
        data: CSV 路径或 DataFrame
        keywords_3d: 3D 结构 [[[group1]], [[group2]], ...]
        title_col: 标题列名
        match_all: 是否全部匹配（对单个组内）
        strip_accents: 是否去除重音
        case_insensitive: 是否大小写不敏感

    Returns:
        DataFrame 包含 matched_keyword_group 列，表示匹配到的组
    """
    # 解包 3D 为多个 2D 查询
    level2_queries = []

    for outer_group in keywords_3d:
        # 每个 outer_group 是一个 Level 2 结构
        if len(outer_group) == 1 and isinstance(outer_group[0], (list, tuple)):
            # [[[a,b], [c]]] 形式，解包一层
            level2_query = outer_group[0]
        else:
            # [[a,b], [c]] 形式，直接使用
            level2_query = outer_group
        level2_queries.append(level2_query)

    # 分别执行每个 Level 2 查询
    all_results = []
    for idx, query in enumerate(level2_queries):
        df_matched = extract_keywords(
            data,
            query,
            title_col=title_col,
            match_all=match_all,
            strip_accents=strip_accents,
            case_insensitive=case_insensitive,
            return_matches=True,
        )
        if not df_matched.empty:
            # 添加组标识
            df_matched["matched_keyword_group"] = f"group_{idx+1}"
            all_results.append(df_matched)

    if not all_results:
        return pd.DataFrame()

    # 合并所有结果
    combined = pd.concat(all_results, ignore_index=True)

    # 处理重复：同一论文被多个组匹配时合并组标识
    # 使用 title + year 作为唯一键
    combined["_unique_id"] = combined[title_col].fillna("") + "_" + combined.get("year", "").astype(str)

    # 聚合：合并 matched_keyword_group，保留其他列
    agg_dict = {"matched_keyword_group": lambda x: ";".join(sorted(set(x)))}
    for col in combined.columns:
        if col not in ["_unique_id", "matched_keyword_group"]:
            agg_dict[col] = "first"

    grouped = combined.groupby("_unique_id", as_index=False).agg(agg_dict)
    grouped = grouped.drop(columns=["_unique_id"])

    return grouped


def _normalize_for_hash(kw) -> str:
    """递归地将关键词结构转为可hash的字符串。"""
    if isinstance(kw, (list, tuple)):
        return "[" + ",".join(_normalize_for_hash(x) for x in kw) + "]"
    return str(kw).lower().strip()


def build_output_filename(
    keywords: Sequence[KeywordGroup],
    prefix: str = "dblp_papers_matched",
    max_filename_length: int = 200,
    output_dir: Optional[str] = None,
) -> str:
    """生成Windows兼容的输出文件名，确保不超过255字符限制。

    对于三层及以上嵌套结构，自动使用哈希命名：prefix_8charhash.xlsx
    对于简单结构，使用描述性命名：prefix_(kw1|kw2)_(kw3).xlsx

    Args:
        keywords: 关键词列表
        prefix: 文件名前缀
        max_filename_length: 最大文件名长度（不含扩展名）
        output_dir: 输出目录，默认为脚本所在目录

    Returns:
        str: 生成的文件路径
    """
    # 确定输出目录：默认为脚本所在目录
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(__file__))

    # Windows最大文件名是255字符，我们需要确保留有余量
    max_total_length = 255
    extension_length = 5  # ".xlsx"
    safe_max_filename_length = min(max_filename_length, max_total_length - extension_length)

    # 检测嵌套层级
    level = _get_nesting_level(keywords) if keywords else 0

    # 生成哈希值（用于复杂结构或超长文件名）
    keywords_hash = hashlib.md5(_normalize_for_hash(keywords).encode("utf-8")).hexdigest()[:8]

    # 三层及以上嵌套：直接使用哈希命名
    if level >= 3:
        return os.path.join(output_dir, f"{prefix}_{keywords_hash}.xlsx")

    # 构建关键词字符串（用于一维、二维结构）
    keywords_parts: List[str] = []
    for item in keywords:
        if isinstance(item, (list, tuple, set)):
            # 同义词组，用|连接
            group_str = "|".join(str(k).replace(" ", "_") for k in item if str(k).strip())
            if group_str:
                keywords_parts.append(f"({group_str})")
        else:
            # 单个关键词
            clean_kw = str(item).replace(" ", "_")
            if clean_kw:
                keywords_parts.append(clean_kw)

    # 如果有关键词，构建完整的关键词字符串
    if keywords_parts:
        keywords_str = "_".join(keywords_parts)
    else:
        keywords_str = "default"

    # 计算完整文件名长度
    full_name = f"{prefix}_{keywords_str}.xlsx"

    # 如果文件名长度在安全范围内，直接使用
    if len(full_name) <= max_total_length:
        # 清理特殊字符
        safe_name = re.sub(r'[<>:\"/\\\\|?*]', '_', full_name[:-5]) + full_name[-5:]
        return os.path.join(output_dir, safe_name)

    # 文件名太长，回退到哈希命名
    return os.path.join(output_dir, f"{prefix}_{keywords_hash}.xlsx")


def extract_and_save(
    csv_path: str,
    keywords: Sequence[KeywordGroup],
    *,
    match_all: bool = True,
    strip_accents: bool = False,
    case_insensitive: bool = True,
    title_col: str = "title",
    output_path: Optional[str] = None,
) -> str:
    """高层封装：直接读取 CSV，匹配并写出 Excel，返回文件名。"""
    df = extract_keywords(
        csv_path,
        keywords,
        match_all=match_all,
        strip_accents=strip_accents,
        case_insensitive=case_insensitive,
        title_col=title_col,
    )
    filename = output_path or build_output_filename(keywords)
    df.to_excel(filename, index=False)
    logger.info(f"保存匹配结果: {filename} ({len(df)} rows)")
    return filename


def _build_keywords_from_args(args: argparse.Namespace, default_keywords: List[KeywordGroup]) -> List[KeywordGroup]:
    """从命令行参数构建关键词列表"""
    # 显式请求使用配置文件默认值
    if getattr(args, "use_defaults", False):
        logger.info("使用配置文件中的默认关键词")
        return default_keywords

    # 从 JSON 字符串加载
    if args.keywords_json:
        keywords = load_keywords_from_source(args.keywords_json)
        if keywords:
            return keywords
        else:
            raise ValueError("无法解析 keywords-json")

    # 从文件加载
    if args.keywords_file:
        keywords = load_keywords_from_source(args.keywords_file)
        if keywords:
            return keywords
        else:
            raise FileNotFoundError(f"无法读取关键词文件: {args.keywords_file}")

    # 从命令行参数构建
    kw_simple: List[str] = args.kw or []
    kw_groups: List[List[str]] = args.group or []

    keywords: List[KeywordGroup] = []
    keywords.extend(kw_simple)
    keywords.extend(kw_groups)

    if not keywords:
        logger.info("未提供任何关键词参数，使用配置文件默认值")
        return default_keywords

    return keywords


def _parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="从 CSV 提取匹配标题的论文，支持组内OR、组间AND。",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # 输入/输出
    parser.add_argument("csv", nargs="?", help="输入 CSV 文件路径")
    parser.add_argument("--title-col", help="标题列列名")
    parser.add_argument("-o", "--output", help="输出 Excel 文件路径")

    # 关键词来源
    parser.add_argument('--kw', action='append', help='单个关键词（可重复）')
    parser.add_argument('--keywords-json', help='JSON格式关键词，如: [["crowd","task"], "predict"]')
    parser.add_argument('--keywords-file', help='从文件加载关键词（JSON或每行一个）')
    parser.add_argument(
        '--group',
        action='append',
        nargs='+',
        help='同义词组（组内OR，组间AND），如：--group crowd task'
    )

    # 匹配选项
    parser.add_argument('--match-all', action='store_true', help='一维列表时AND模式（所有词都出现）')
    parser.add_argument('--match-any', action='store_false', dest='match_all', help='一维列表时OR模式（任意词出现）')
    parser.add_argument('--case-sensitive', action='store_false', dest='case_insensitive', help='区分大小写')
    parser.add_argument('--strip-accents', action='store_true', help='去除重音符号')

    # 使用配置文件默认值
    parser.add_argument('--use-defaults', action='store_true', help='使用配置文件中的默认关键词')

    return parser.parse_args()


def _build_config_from_args(args: argparse.Namespace) -> ExtractConfig:
    """从命令行参数构建配置"""
    # 加载配置文件默认值
    extract_config = default_extract_config()

    # 构建关键词列表
    default_keywords = extract_config.get('default_keywords', [])
    keywords = _build_keywords_from_args(args, default_keywords)

    # 创建配置对象
    cfg = ExtractConfig(
        csv_path=args.csv or extract_config.get('default_csv', 'dblp_papers.csv'),
        keywords=keywords,
        title_col=getattr(args, 'title_col', None) or extract_config.get('default_title_col', 'title'),
        match_all=getattr(args, 'match_all', None) if args.match_all is not None else extract_config.get('default_match_all', True),
        strip_accents=getattr(args, 'strip_accents', False),
        case_insensitive=getattr(args, 'case_insensitive', None) or extract_config.get('case_insensitive', True),
        output_path=getattr(args, 'output', None),
        output_prefix=extract_config.get('output_prefix', 'dblp_papers_matched'),
        max_base_len=extract_config.get('max_base_len', 50),
        max_filename_length=extract_config.get('max_filename_length', 200),
        return_matches=extract_config.get('return_matches', True)
    )

    return cfg.validate()


def extract_and_save_with_config(config: ExtractConfig) -> str:
    """使用配置对象进行提取和保存，统一输出单个文件。

    支持 Level 2 和 Level 3 嵌套结构：
    - Level 2: 作为单个查询处理
    - Level 3: 解包为多个 Level 2 查询，分别执行后合并
    """
    level = _get_nesting_level(config.keywords) if config.keywords else 0

    if level >= 3 and len(config.keywords) > 1:
        # Level 3: 解包为多个 Level 2 查询，分别执行后合并
        df = extract_keywords_multi_group(
            config.csv_path,
            config.keywords,
            title_col=config.title_col,
            match_all=config.match_all,
            strip_accents=config.strip_accents,
            case_insensitive=config.case_insensitive,
        )
    else:
        # Level 1/2: 正常处理
        df = extract_keywords(
            config.csv_path,
            config.keywords,
            title_col=config.title_col,
            match_all=config.match_all,
            strip_accents=config.strip_accents,
            case_insensitive=config.case_insensitive,
            return_matches=config.return_matches,
        )
        # 统一添加 matched_keyword_group 列
        if "matched_keyword_group" not in df.columns:
            df["matched_keyword_group"] = "default"

    # 统一生成单个输出文件
    if config.output_path:
        filename = config.output_path
    else:
        filename = build_output_filename(
            config.keywords,
            prefix=config.output_prefix,
            max_filename_length=config.max_filename_length
        )

    df.to_excel(filename, index=False)
    config.logger.info(f"保存匹配结果: {filename} ({len(df)} rows)")
    return filename


def main():
    """主函数"""
    args = _parse_args()
    config = _build_config_from_args(args)
    config.logger = logger
    filename = extract_and_save_with_config(config)
    logger.info(f"完成，输出文件：{filename}")


if __name__ == "__main__":
    main()
