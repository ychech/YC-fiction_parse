"""
AI 解析引擎 - 基于大模型的文本特征提取
"""
import asyncio
import json
from typing import Any, Dict, List, Optional

from tenacity import retry, stop_after_attempt, wait_exponential

from src.common.exceptions import AIEngineException
from src.common.logger import get_logger
from src.common.schemas import (
    BackgroundFeatures,
    CharacterFeatures,
    NovelFeatures,
    PlotFeatures,
    TaskFeatures,
    WritingFeatures,
)
from src.config.settings import settings

logger = get_logger(__name__)


class AIEngine:
    """AI 解析引擎"""
    
    def __init__(self):
        self.client = None
        self.model = settings.ai.openai_model
        self.local_model = None
        self._init_client()
    
    def _init_client(self):
        """初始化 AI 客户端"""
        if settings.ai.use_local_model and settings.ai.local_model_path:
            self._init_local_model()
        else:
            self._init_api_client()
    
    def _init_api_client(self):
        """初始化 API 客户端"""
        try:
            from openai import AsyncOpenAI
            
            self.client = AsyncOpenAI(
                api_key=settings.ai.openai_api_key,
                base_url=settings.ai.openai_base_url,
                timeout=settings.ai.request_timeout,
            )
            logger.info("openai_client_initialized")
        except Exception as e:
            logger.error("openai_client_init_failed", error=str(e))
            raise AIEngineException(f"Failed to initialize OpenAI client: {e}")
    
    def _init_local_model(self):
        """初始化本地模型"""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            logger.info("loading_local_model", path=settings.ai.local_model_path)
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                settings.ai.local_model_path,
                trust_remote_code=True
            )
            self.local_model = AutoModelForCausalLM.from_pretrained(
                settings.ai.local_model_path,
                torch_dtype=torch.float16 if settings.ai.local_model_device == "cuda" else torch.float32,
                device_map=settings.ai.local_model_device,
                trust_remote_code=True
            )
            
            logger.info("local_model_loaded")
        except Exception as e:
            logger.error("local_model_load_failed", error=str(e))
            # 回退到 API
            settings.ai.use_local_model = False
            self._init_api_client()
    
    def _build_prompt(self, text: str, schema: Dict[str, Any]) -> str:
        """构建提示词"""
        prompt = f"""请分析以下小说文本，提取结构化特征。

【小说文本】
{text[:8000]}  # 限制长度避免超出token限制

【输出要求】
请严格按照以下JSON Schema输出分析结果：

```json
{{
    "task": {{
        "main_task": "主线任务描述",
        "sub_tasks": ["支线任务1", "支线任务2"],
        "task_structure": "任务结构类型（如：升级流/签到流/系统流/复仇流等）",
        "task_difficulty": "任务难度曲线描述"
    }},
    "background": {{
        "world_type": "世界观类型（如：修仙/玄幻/都市/科幻/历史等）",
        "era_setting": "时代设定",
        "power_system": "力量体系（如：修真境界/斗气等级/魔法体系等）",
        "major_factions": ["主要势力1", "主要势力2"],
        "world_rules": ["世界规则1", "世界规则2"]
    }},
    "character": {{
        "protagonist": {{
            "name": "主角姓名",
            "traits": ["性格特征1", "性格特征2"],
            "background": "主角背景",
            "goals": ["目标1", "目标2"]
        }},
        "supporting_roles": [
            {{"name": "配角名", "role": "角色定位", "relationship": "与主角关系"}}
        ],
        "character_archetypes": ["角色原型标签"],
        "character_relationships": [
            {{"from": "角色A", "to": "角色B", "type": "关系类型"}}
        ]
    }},
    "writing": {{
        "narrative_perspective": "叙事视角（first_person/second_person/third_person/multi_person）",
        "pacing": "节奏特点（慢热/快节奏/张弛有度等）",
        "rhetoric_style": ["修辞特点1", "修辞特点2"],
        "sentence_structure": "句式特点",
        "humor_style": "幽默风格",
        "suspense_techniques": ["悬念设置手法1", "悬念设置手法2"]
    }},
    "plot": {{
        "plot_structure": "情节结构（如：三幕式/英雄之旅/多线叙事等）",
        "conflict_types": ["冲突类型1", "冲突类型2"],
        "plot_twists": 反转次数（数字）,
        "climax_distribution": "高潮分布描述",
        "foreshadowing": ["伏笔1", "伏笔2"]
    }},
    "confidence_score": 0.85
}}
```

注意：
1. 如果某字段无法确定，使用null或空数组
2. confidence_score表示你对分析结果的置信度（0-1之间）
3. 只输出JSON，不要有其他解释文字
"""
        return prompt
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """解析 AI 响应"""
        try:
            # 尝试直接解析
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # 尝试从代码块中提取
        import re
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # 尝试提取任何JSON对象
        json_match = re.search(r'(\{.*\})', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        raise AIEngineException(f"Failed to parse AI response: {response[:200]}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _call_api(self, prompt: str) -> str:
        """调用 API"""
        if settings.ai.use_local_model and self.local_model:
            return await self._call_local_model(prompt)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的小说分析助手，擅长从文本中提取结构化特征。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=settings.ai.openai_temperature,
                max_tokens=settings.ai.openai_max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("api_call_failed", error=str(e))
            raise AIEngineException(f"API call failed: {e}")
    
    async def _call_local_model(self, prompt: str) -> str:
        """调用本地模型"""
        import torch
        
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.local_model.device)
        
        with torch.no_grad():
            outputs = self.local_model.generate(
                **inputs,
                max_new_tokens=settings.ai.openai_max_tokens,
                temperature=settings.ai.openai_temperature,
                do_sample=True,
            )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        # 移除输入prompt
        response = response[len(prompt):].strip()
        
        return response
    
    async def extract_features(
        self,
        text: str,
        chapters: Optional[List[Dict]] = None
    ) -> NovelFeatures:
        """
        使用 AI 提取特征
        
        Args:
            text: 小说文本
            chapters: 章节列表
        
        Returns:
            NovelFeatures: 提取的特征
        """
        logger.info("ai_extraction_started", text_length=len(text))
        
        # 构建提示词
        prompt = self._build_prompt(text, {})
        
        # 调用 AI
        response = await self._call_api(prompt)
        
        # 解析响应
        try:
            data = self._parse_response(response)
        except AIEngineException as e:
            logger.error("response_parse_failed", response=response[:500])
            raise
        
        # 构建特征对象
        features = NovelFeatures(
            novel_id="",
            task=TaskFeatures(**data.get("task", {})),
            background=BackgroundFeatures(**data.get("background", {})),
            character=CharacterFeatures(**data.get("character", {})),
            writing=WritingFeatures(**data.get("writing", {})),
            plot=PlotFeatures(**data.get("plot", {})),
            confidence_score=data.get("confidence_score", 0.5),
            extraction_method="ai_engine"
        )
        
        logger.info("ai_extraction_completed", confidence=features.confidence_score)
        
        return features
    
    async def extract_features_batch(
        self,
        texts: List[str],
        max_concurrent: int = None
    ) -> List[NovelFeatures]:
        """
        批量提取特征
        
        Args:
            texts: 文本列表
            max_concurrent: 最大并发数
        
        Returns:
            List[NovelFeatures]: 特征列表
        """
        if max_concurrent is None:
            max_concurrent = settings.ai.max_concurrent_calls
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def extract_with_limit(text: str) -> NovelFeatures:
            async with semaphore:
                return await self.extract_features(text)
        
        tasks = [extract_with_limit(text) for text in texts]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def extract_from_chapters(
        self,
        chapters: List[Dict],
        strategy: str = "core_first"
    ) -> NovelFeatures:
        """
        从章节提取特征
        
        Args:
            chapters: 章节列表
            strategy: 提取策略
                - core_first: 先解析核心章节
                - full: 解析全部章节
                - sampling: 采样解析
        
        Returns:
            NovelFeatures: 提取的特征
        """
        if strategy == "core_first":
            # 先解析核心章节
            core_chapters = [ch for ch in chapters if ch.get("is_core", False)]
            if not core_chapters:
                core_chapters = chapters[:10]  # 默认前10章
            
            text = "\n\n".join(ch.get("content", "") for ch in core_chapters)
            return await self.extract_features(text, chapters)
        
        elif strategy == "full":
            # 解析全部（可能超长，需要分块）
            text = "\n\n".join(ch.get("content", "") for ch in chapters)
            return await self.extract_features(text, chapters)
        
        elif strategy == "sampling":
            # 采样解析
            total = len(chapters)
            sample_indices = [0, 1, 2]  # 开头
            sample_indices.extend(range(total // 4, total // 4 + 3))  # 1/4处
            sample_indices.extend(range(total // 2, total // 2 + 3))  # 中间
            sample_indices.extend(range(total * 3 // 4, total * 3 // 4 + 3))  # 3/4处
            sample_indices.extend(range(total - 3, total))  # 结尾
            
            sample_chapters = [chapters[i] for i in sample_indices if i < total]
            text = "\n\n".join(ch.get("content", "") for ch in sample_chapters)
            return await self.extract_features(text, chapters)
        
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
