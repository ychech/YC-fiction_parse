"""
EPUB 解析器 v2 - 完整实现
支持 EPUB2/EPUB3，处理复杂结构和样式
"""
import re
import zipfile
from io import BytesIO
from pathlib import Path
from typing import List, Optional, Tuple
from xml.etree import ElementTree as ET

from src.common.logger import get_logger
from src.processing_layer.parsers.base import BaseParser, ChapterInfo, ParseResult

logger = get_logger(__name__)


class EpubParserV2(BaseParser):
    """
    EPUB v2 解析器
    
    特性：
    - 支持 EPUB2/EPUB3 标准
    - 处理复杂目录结构
    - 提取元数据（书名、作者、封面等）
    - 支持多文件章节
    - 清理样式和脚本
    """
    
    # EPUB 命名空间
    NAMESPACES = {
        'opf': 'http://www.idpf.org/2007/opf',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'xhtml': 'http://www.w3.org/1999/xhtml',
        'epub': 'http://www.idpf.org/2007/ops',
        'ncx': 'http://www.daisy.org/z3986/2005/ncx/',
    }
    
    def __init__(self):
        super().__init__()
        self.epub_zip: Optional[zipfile.ZipFile] = None
        self.opf_path: Optional[str] = None
        self.opf_dir: str = ""
        
    async def parse(self, file_data: bytes) -> ParseResult:
        """解析 EPUB 文件"""
        logger.info("epub_v2_parsing_started", size=len(file_data))
        
        try:
            # 打开 EPUB (ZIP 格式)
            self.epub_zip = zipfile.ZipFile(BytesIO(file_data))
            
            # 查找 OPF 文件
            self.opf_path = self._find_opf_path()
            if not self.opf_path:
                raise ValueError("OPF file not found in EPUB")
            
            self.opf_dir = str(Path(self.opf_path).parent) if self.opf_path != "content.opf" else ""
            
            # 解析 OPF
            opf_content = self.epub_zip.read(self.opf_path).decode('utf-8')
            opf_root = ET.fromstring(opf_content)
            
            # 提取元数据
            metadata = self._extract_metadata(opf_root)
            
            # 提取章节
            chapters = self._extract_chapters(opf_root)
            
            # 识别核心章节
            chapters = self.identify_core_chapters(chapters)
            
            # 计算总字数
            total_word_count = sum(ch.word_count for ch in chapters)
            
            result = ParseResult(
                title=metadata.get("title"),
                author=metadata.get("author"),
                description=metadata.get("description"),
                chapters=chapters,
                total_word_count=total_word_count,
                metadata={
                    "format": "epub",
                    "version": metadata.get("version", "unknown"),
                    "language": metadata.get("language"),
                    "publisher": metadata.get("publisher"),
                    "identifier": metadata.get("identifier"),
                    "chapter_count": len(chapters),
                    "core_chapter_count": sum(1 for ch in chapters if ch.is_core),
                }
            )
            
            logger.info(
                "epub_v2_parsing_completed",
                chapters=len(chapters),
                word_count=total_word_count,
                title=result.title
            )
            
            return result
            
        except Exception as e:
            logger.error("epub_v2_parsing_failed", error=str(e))
            raise
        finally:
            if self.epub_zip:
                self.epub_zip.close()
    
    def _find_opf_path(self) -> Optional[str]:
        """查找 OPF 文件路径"""
        # 方法1: 通过 container.xml 查找
        try:
            container = self.epub_zip.read("META-INF/container.xml")
            root = ET.fromstring(container)
            
            # 查找 rootfile
            for elem in root.iter():
                if elem.tag.endswith("rootfile"):
                    return elem.get("full-path")
        except Exception as e:
            logger.warning("container_xml_parse_failed", error=str(e))
        
        # 方法2: 直接查找 OPF 文件
        for name in self.epub_zip.namelist():
            if name.endswith(".opf"):
                return name
        
        return None
    
    def _extract_metadata(self, opf_root: ET.Element) -> dict:
        """提取 OPF 元数据"""
        metadata = {}
        
        # 查找 metadata 元素
        metadata_elem = opf_root.find('.//opf:metadata', self.NAMESPACES)
        if metadata_elem is None:
            metadata_elem = opf_root.find('.//metadata')
        
        if metadata_elem is None:
            return metadata
        
        # 提取标题
        title_elem = metadata_elem.find('dc:title', self.NAMESPACES)
        if title_elem is not None and title_elem.text:
            metadata["title"] = title_elem.text.strip()
        
        # 提取作者（creator）
        creator_elem = metadata_elem.find('dc:creator', self.NAMESPACES)
        if creator_elem is not None and creator_elem.text:
            metadata["author"] = creator_elem.text.strip()
        
        # 提取描述
        desc_elem = metadata_elem.find('dc:description', self.NAMESPACES)
        if desc_elem is not None and desc_elem.text:
            metadata["description"] = desc_elem.text.strip()
        
        # 提取语言
        lang_elem = metadata_elem.find('dc:language', self.NAMESPACES)
        if lang_elem is not None and lang_elem.text:
            metadata["language"] = lang_elem.text.strip()
        
        # 提取出版社
        pub_elem = metadata_elem.find('dc:publisher', self.NAMESPACES)
        if pub_elem is not None and pub_elem.text:
            metadata["publisher"] = pub_elem.text.strip()
        
        # 提取标识符
        id_elem = metadata_elem.find('dc:identifier', self.NAMESPACES)
        if id_elem is not None and id_elem.text:
            metadata["identifier"] = id_elem.text.strip()
        
        # 提取日期
        date_elem = metadata_elem.find('dc:date', self.NAMESPACES)
        if date_elem is not None and date_elem.text:
            metadata["date"] = date_elem.text.strip()
        
        # 检测 EPUB 版本
        package_elem = opf_root
        if package_elem.tag.endswith('package'):
            metadata["version"] = package_elem.get('version', 'unknown')
        
        return metadata
    
    def _extract_chapters(self, opf_root: ET.Element) -> List[ChapterInfo]:
        """提取章节列表"""
        chapters = []
        
        # 获取 manifest (文件列表)
        manifest = self._get_manifest(opf_root)
        
        # 获取 spine (阅读顺序)
        spine = self._get_spine(opf_root)
        
        # 获取目录 (NCX 或 NAV)
        toc = self._get_toc(opf_root, manifest)
        
        # 按 spine 顺序处理章节
        chapter_num = 0
        for itemref in spine:
            item_id = itemref.get('idref')
            if not item_id or item_id not in manifest:
                continue
            
            item = manifest[item_id]
            href = item.get('href', '')
            
            # 跳过非 HTML 文件
            if not any(href.endswith(ext) for ext in ['.html', '.htm', '.xhtml']):
                continue
            
            # 构建完整路径
            if self.opf_dir:
                full_path = f"{self.opf_dir}/{href}"
            else:
                full_path = href
            
            try:
                # 读取章节内容
                content = self.epub_zip.read(full_path).decode('utf-8')
                
                # 提取标题和内容
                title, text = self._extract_chapter_content(content)
                
                if len(text) > 100:  # 过滤过短的页面
                    chapter_num += 1
                    
                    # 如果没有从内容提取到标题，使用目录中的标题
                    if not title and href in toc:
                        title = toc[href]
                    
                    chapters.append(ChapterInfo(
                        chapter_number=chapter_num,
                        title=title,
                        content=text,
                        word_count=len(text)
                    ))
                    
            except Exception as e:
                logger.warning("chapter_extraction_failed", path=full_path, error=str(e))
                continue
        
        return chapters
    
    def _get_manifest(self, opf_root: ET.Element) -> dict:
        """获取 manifest"""
        manifest = {}
        manifest_elem = opf_root.find('.//opf:manifest', self.NAMESPACES)
        if manifest_elem is None:
            manifest_elem = opf_root.find('.//manifest')
        
        if manifest_elem is not None:
            for item in manifest_elem:
                if item.tag.endswith('item'):
                    item_id = item.get('id')
                    if item_id:
                        manifest[item_id] = {
                            'href': item.get('href', ''),
                            'media-type': item.get('media-type', '')
                        }
        
        return manifest
    
    def _get_spine(self, opf_root: ET.Element) -> List[ET.Element]:
        """获取 spine (阅读顺序)"""
        spine_elem = opf_root.find('.//opf:spine', self.NAMESPACES)
        if spine_elem is None:
            spine_elem = opf_root.find('.//spine')
        
        if spine_elem is not None:
            return [item for item in spine_elem if item.tag.endswith('itemref')]
        
        return []
    
    def _get_toc(self, opf_root: ET.Element, manifest: dict) -> dict:
        """获取目录 (NCX 或 NAV)"""
        toc = {}
        
        # 方法1: 查找 NCX 文件 (EPUB2)
        ncx_id = None
        spine_elem = opf_root.find('.//opf:spine', self.NAMESPACES)
        if spine_elem is None:
            spine_elem = opf_root.find('.//spine')
        
        if spine_elem is not None:
            ncx_id = spine_elem.get('toc')
        
        if ncx_id and ncx_id in manifest:
            ncx_href = manifest[ncx_id]['href']
            if self.opf_dir:
                ncx_path = f"{self.opf_dir}/{ncx_href}"
            else:
                ncx_path = ncx_href
            
            try:
                ncx_content = self.epub_zip.read(ncx_path).decode('utf-8')
                toc = self._parse_ncx(ncx_content)
            except Exception as e:
                logger.warning("ncx_parse_failed", error=str(e))
        
        # 方法2: 查找 NAV 文件 (EPUB3)
        if not toc:
            for item_id, item in manifest.items():
                if 'nav' in item.get('properties', '').lower():
                    nav_href = item['href']
                    if self.opf_dir:
                        nav_path = f"{self.opf_dir}/{nav_href}"
                    else:
                        nav_path = nav_href
                    
                    try:
                        nav_content = self.epub_zip.read(nav_path).decode('utf-8')
                        toc = self._parse_nav(nav_content)
                    except Exception as e:
                        logger.warning("nav_parse_failed", error=str(e))
                    break
        
        return toc
    
    def _parse_ncx(self, ncx_content: str) -> dict:
        """解析 NCX 目录"""
        toc = {}
        
        try:
            root = ET.fromstring(ncx_content)
            
            # 查找 navMap
            navmap = root.find('.//ncx:navMap', self.NAMESPACES)
            if navmap is None:
                navmap = root.find('.//navMap')
            
            if navmap is not None:
                for navpoint in navmap.iter():
                    if navpoint.tag.endswith('navPoint'):
                        # 获取标题
                        text_elem = navpoint.find('.//ncx:text', self.NAMESPACES)
                        if text_elem is None:
                            text_elem = navpoint.find('.//text')
                        
                        title = text_elem.text if text_elem is not None else None
                        
                        # 获取链接
                        content_elem = navpoint.find('.//ncx:content', self.NAMESPACES)
                        if content_elem is None:
                            content_elem = navpoint.find('.//content')
                        
                        if content_elem is not None:
                            src = content_elem.get('src', '')
                            # 移除锚点
                            src = src.split('#')[0]
                            if title:
                                toc[src] = title
        
        except Exception as e:
            logger.warning("ncx_parsing_error", error=str(e))
        
        return toc
    
    def _parse_nav(self, nav_content: str) -> dict:
        """解析 NAV 目录 (EPUB3)"""
        toc = {}
        
        try:
            # 使用正则提取，避免命名空间问题
            # 查找所有链接
            pattern = r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>'
            matches = re.findall(pattern, nav_content, re.IGNORECASE)
            
            for href, title in matches:
                href = href.split('#')[0]  # 移除锚点
                title = title.strip()
                if title:
                    toc[href] = title
        
        except Exception as e:
            logger.warning("nav_parsing_error", error=str(e))
        
        return toc
    
    def _extract_chapter_content(self, html_content: str) -> Tuple[Optional[str], str]:
        """提取章节标题和正文"""
        try:
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 移除脚本和样式
            for script in soup(["script", "style"]):
                script.decompose()
            
            # 提取标题
            title = None
            for tag in ['h1', 'h2', 'h3', 'title']:
                elem = soup.find(tag)
                if elem:
                    title = elem.get_text().strip()
                    break
            
            # 提取正文
            # 优先查找主要内容区域
            text = ""
            for selector in ['main', 'article', '.chapter', '.content', '#content', 'body']:
                elem = soup.select_one(selector)
                if elem:
                    text = elem.get_text()
                    break
            
            if not text:
                text = soup.get_text()
            
            # 清洗文本
            text = self.clean_text(text)
            
            return title, text
            
        except ImportError:
            # 如果没有 BeautifulSoup，使用正则
            logger.warning("beautifulsoup_not_installed, using_regex_fallback")
            
            # 提取标题
            title_match = re.search(r'<h[1-3][^>]*>([^<]+)</h[1-3]>', html_content, re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else None
            
            # 提取正文
            text = re.sub(r'<[^>]+>', ' ', html_content)
            text = self.clean_text(text)
            
            return title, text
