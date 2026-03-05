#!/usr/bin/env python3
"""
小说反向解析系统 - 演示脚本
展示如何使用 API 进行小说解析
"""
import json
import sys
import time
from pathlib import Path

import requests

# API 基础 URL
BASE_URL = "http://localhost:8000"


def print_section(title):
    """打印章节标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_json(data):
    """美化打印 JSON"""
    print(json.dumps(data, indent=2, ensure_ascii=False))


def create_sample_novel():
    """创建示例小说文件"""
    sample_content = """
书名：修仙逆袭录
作者：演示作者

简介：一个废物少年获得神秘系统，踏上修仙逆袭之路。

第一章 废物少年

青云宗，外门弟子居所。

"林凡，你这个废物，连最基本的引气入体都做不到，还有脸待在宗门？"

嘲讽声传来，林凡握紧拳头，却无力反驳。

他确实是个废物，入门三年，修为毫无寸进。

叮！

【至尊修仙系统激活！】

【宿主：林凡】

【修为：无】

【新手任务：完成引气入体】

【任务奖励：洗髓丹一枚】

林凡愣住了，随即狂喜。

金手指，终于来了！

第二章 首次突破

在系统的指导下，林凡很快完成了引气入体。

【叮！任务完成！】

【获得洗髓丹一枚！】

林凡毫不犹豫地服下丹药，体内杂质被排出，修炼速度提升十倍。

"这...这怎么可能？"

之前嘲笑他的弟子目瞪口呆。

第三章 打脸开始

一个月后，宗门大比。

林凡一路过关斩将，杀入决赛。

"林凡，你这种废物也配进决赛？"

对手是内门弟子张狂，一直欺压林凡。

"废物？"

林凡冷笑一声，一掌拍出。

轰！

张狂倒飞出去，口吐鲜血。

全场震惊！

第四章 内门选拔

林凡的表现引起了长老们的注意。

"此子，可入我门下。"

大长老亲自开口，要收林凡为徒。

从此，林凡一飞冲天。

第五章 秘境探险

内门弟子可进入宗门秘境。

林凡在秘境中发现了一处灵气节点，其他人不知道。

【系统提示：发现隐藏灵气节点，是否占领？】

"占领！"

林凡独占节点，修为突飞猛进。

...

（后续章节省略）
"""
    
    # 保存到临时文件
    sample_file = Path("/tmp/sample_novel.txt")
    sample_file.write_text(sample_content, encoding="utf-8")
    return sample_file


def upload_novel(file_path):
    """上传小说"""
    print_section("1. 上传小说")
    
    url = f"{BASE_URL}/api/v1/novels/upload"
    
    with open(file_path, "rb") as f:
        files = {"file": ("sample_novel.txt", f, "text/plain")}
        data = {
            "title": "修仙逆袭录",
            "author": "演示作者",
            "auto_parse": "false"  # 先不上传就解析，手动触发深度解析
        }
        
        response = requests.post(url, files=files, data=data)
        result = response.json()
        
        if result.get("code") == 200:
            novel_id = result["data"]["novel"]["id"]
            print(f"✓ 小说上传成功")
            print(f"  小说ID: {novel_id}")
            print(f"  标题: {result['data']['novel']['title']}")
            return novel_id
        else:
            print(f"✗ 上传失败: {result.get('message')}")
            return None


def deep_parse(novel_id):
    """执行深度解析"""
    print_section("2. 执行深度解析")
    print("  正在解析五大核心维度...")
    print("  - 故事内核（核心冲突公式、情绪钩子分布）")
    print("  - 金手指/核心设定")
    print("  - 人物弧光与人设模板")
    print("  - 叙事节奏与写作技法")
    print("  - 商业价值")
    print()
    
    url = f"{BASE_URL}/api/v1/deep/{novel_id}/deep-parse"
    
    response = requests.post(url, json={"compare_with_benchmark": False})
    result = response.json()
    
    if result.get("code") == 200:
        print("✓ 深度解析完成")
        return result["data"]
    else:
        print(f"✗ 解析失败: {result.get('message')}")
        return None


def show_formula_summary(novel_id):
    """显示公式化总结"""
    print_section("3. 公式化总结")
    
    url = f"{BASE_URL}/api/v1/deep/{novel_id}/formula-summary"
    
    response = requests.get(url)
    result = response.json()
    
    if result.get("code") == 200:
        summary = result["data"]["formula_summary"]
        print("解析结果公式：")
        print()
        print(f"  {summary}")
        print()
        
        print("可复用标签：")
        for tag in result["data"]["reusable_tags"]:
            print(f"  - {tag}")


def show_deep_features(data):
    """显示深度特征"""
    print_section("4. 深度解析详情")
    
    features = data.get("deep_features", {})
    
    # 故事内核
    print("\n【故事内核】")
    story_core = features.get("story_core", {})
    conflict = story_core.get("conflict_formula", {})
    print(f"  冲突公式: {conflict.get('formula_name')}")
    print(f"  核心诉求: {conflict.get('protagonist_desire')}")
    print(f"  核心阻碍: {conflict.get('core_obstacle')}")
    print(f"  解决路径: {conflict.get('solution_path')}")
    print(f"  可复用性: {conflict.get('reusability_score', 0) * 100:.0f}%")
    
    hooks = story_core.get("hook_distribution", {})
    print(f"\n  情绪钩子总数: {hooks.get('total_hooks', 0)}")
    print(f"  爽点节奏: {hooks.get('rhythm_pattern', 'N/A')}")
    
    # 金手指设定
    print("\n【金手指设定】")
    setting = features.get("core_setting", {})
    gf = setting.get("golden_finger", {})
    print(f"  类型: {gf.get('gf_type')}")
    print(f"  成长性: {gf.get('growth_type')}")
    print(f"  初始能力: {gf.get('initial_power')}")
    print(f"  约束条件数: {len(gf.get('constraints', []))}")
    print(f"  与主角适配度: {gf.get('fit_score', 0) * 100:.0f}%")
    
    innovations = gf.get("innovation_points", [])
    if innovations:
        print(f"\n  创新点:")
        for innovation in innovations:
            print(f"    - {innovation}")
    
    # 人物分析
    print("\n【人物分析】")
    character = features.get("character_analysis", {})
    arc = character.get("protagonist_arc", {})
    print(f"  人物弧光: {arc.get('arc_type')}")
    print(f"  初始状态: {arc.get('initial_state')}")
    print(f"  最终状态: {arc.get('final_state')}")
    print(f"  完成度: {arc.get('completion_degree', 0) * 100:.0f}%")
    print(f"  读者满意度预测: {arc.get('reader_satisfaction', 0) * 100:.0f}%")
    
    tags = character.get("protagonist_tags", [])
    if tags:
        print(f"\n  人设记忆点:")
        for tag in tags[:3]:
            print(f"    - [{tag.get('tag_type')}] {tag.get('tag_description')} (出现{tag.get('frequency')}次)")
    
    # 叙事技法
    print("\n【叙事技法】")
    narrative = features.get("narrative_technique", {})
    chapter = narrative.get("chapter_template", {})
    print(f"  章节结构: 钩子{chapter.get('hook_ratio', 0)*100:.0f}% + 推进{chapter.get('development_ratio', 0)*100:.0f}% + 留钩{chapter.get('cliffhanger_ratio', 0)*100:.0f}%")
    print(f"  对话占比: {chapter.get('dialogue_ratio', 0)*100:.0f}%")
    
    language = narrative.get("language_style", {})
    print(f"  短句占比: {language.get('short_sentence_ratio', 0)*100:.0f}%")
    print(f"  节奏感评分: {language.get('rhythm_score', 0) * 100:.0f}%")
    
    # 商业价值
    print("\n【商业价值】")
    commercial = features.get("commercial_value", {})
    audience = commercial.get("audience_profile", {})
    print(f"  主要受众: {audience.get('primary_segment')}")
    print(f"  付费动机: {audience.get('payment_motivation')}")
    print(f"  预估ARPU: ¥{audience.get('estimated_arpu', 0)}")
    
    adaptations = commercial.get("adaptation_potentials", [])
    if adaptations:
        top = adaptations[0]
        print(f"\n  最佳改编方向: {top.get('adaptation_type')}")
        print(f"  适配度: {top.get('suitability_score', 0) * 100:.0f}%")
        print(f"  ROI预测: {top.get('roi_prediction', 0):.1f}倍")
    
    # 整体评分
    print("\n【整体评分】")
    print(f"  质量评分: {features.get('overall_quality_score', 0) * 100:.0f}%")
    print(f"  一致性检查: {features.get('consistency_check', 0) * 100:.0f}%")


def show_reverse_summary(novel_id):
    """显示逆向验证梗概"""
    print_section("5. 逆向验证梗概")
    
    url = f"{BASE_URL}/api/v1/deep/{novel_id}/reverse-summary"
    
    response = requests.get(url)
    result = response.json()
    
    if result.get("code") == 200:
        summary = result["data"]["reverse_summary"]
        print("基于解析结果反向生成的故事梗概：")
        print()
        print(summary)


def main():
    """主函数"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║           小说反向解析系统 - 演示脚本                     ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # 检查服务是否运行
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("✗ API 服务未运行，请先启动服务")
            print("  运行: docker-compose -f deployments/docker/docker-compose.yml up -d")
            return 1
    except requests.exceptions.ConnectionError:
        print("✗ 无法连接到 API 服务")
        print("  请确保服务已启动:")
        print("  docker-compose -f deployments/docker/docker-compose.yml up -d")
        return 1
    
    print("✓ API 服务运行正常\n")
    
    # 创建示例小说
    sample_file = create_sample_novel()
    print(f"✓ 创建示例小说: {sample_file}\n")
    
    # 上传小说
    novel_id = upload_novel(sample_file)
    if not novel_id:
        return 1
    
    # 执行深度解析
    data = deep_parse(novel_id)
    if not data:
        return 1
    
    # 显示公式化总结
    show_formula_summary(novel_id)
    
    # 显示深度特征
    show_deep_features(data)
    
    # 显示逆向验证梗概
    show_reverse_summary(novel_id)
    
    # 结束
    print_section("演示完成")
    print()
    print("更多操作：")
    print(f"  - 查看完整报告: curl {BASE_URL}/api/v1/deep/{novel_id}/deep-features")
    print(f"  - 查看对比分析: curl {BASE_URL}/api/v1/deep/{novel_id}/comparison-report")
    print(f"  - API 文档: http://localhost:8000/api/docs")
    print()
    
    # 清理临时文件
    sample_file.unlink()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
