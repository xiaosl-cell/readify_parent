"""
迁移脚本 — 将 readify_agi 的 .prompt 文件导入 readify_eval 数据库

用法：
    python scripts/migrate_prompts_to_eval.py --eval-url http://localhost:8082

重复运行幂等（已存在的模板会跳过）。
"""
import argparse
import json
import re
import sys
from pathlib import Path

import httpx


def convert_langchain_to_eval(text: str) -> str:
    """将 LangChain 的 {variable} 格式转换为 eval 的 <$variable> 格式"""
    return re.sub(r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}', r'<$\1>', text)

# 模板配置：template_name -> (文件路径, function_category, remarks)
TEMPLATES = {
    "coordinator": {
        "file": "prompt/coordinator.prompt",
        "function_category": "agent",
        "remarks": (
            "用户自定义变量: {input}, {history}, {project_id}, {project_name}, "
            "{project_description}, {context}, {task_type}, {available_agents}；"
            "框架注入变量（不可编辑）: {tools}, {tool_names}, {agent_scratchpad}"
        ),
    },
    "ask_agent": {
        "file": "prompt/ask_agent.prompt",
        "function_category": "agent",
        "remarks": (
            "用户自定义变量: {input}, {history}, {project_id}, {project_name}, "
            "{project_description}, {context}；"
            "框架注入变量（不可编辑）: {tools}, {tool_names}, {agent_scratchpad}"
        ),
    },
    "note_agent": {
        "file": "prompt/note_agent.prompt",
        "function_category": "agent",
        "remarks": (
            "用户自定义变量: {input}, {history}, {project_id}, {project_name}, "
            "{project_description}, {context}, {mind_map_id}, {mind_map_title}, "
            "{mind_map_description}, {file_id}；"
            "框架注入变量（不可编辑）: {tools}, {tool_names}, {agent_scratchpad}"
        ),
    },
    "label": {
        "file": "prompt/label.prompt",
        "function_category": "label_generation",
        "remarks": "用户自定义变量: {content}",
    },
}


def main():
    parser = argparse.ArgumentParser(description="将 .prompt 文件迁移到 readify_eval 数据库")
    parser.add_argument(
        "--eval-url",
        default="http://localhost:8082",
        help="readify_eval base URL (default: http://localhost:8082)",
    )
    args = parser.parse_args()

    base_url = args.eval_url.rstrip("/")
    root_dir = Path(__file__).parent.parent.absolute()

    created = 0
    skipped = 0
    failed = 0

    with httpx.Client(timeout=30.0) as client:
        for template_name, config in TEMPLATES.items():
            prompt_path = root_dir / config["file"]

            if not prompt_path.exists():
                print(f"[SKIP] {template_name}: 文件不存在 {prompt_path}")
                skipped += 1
                continue

            user_prompt = prompt_path.read_text(encoding="utf-8")
            user_prompt = convert_langchain_to_eval(user_prompt)

            # 检查是否已存在
            check_url = f"{base_url}/api/v1/prompt-templates/by-name/{template_name}"
            try:
                resp = client.get(check_url)
                if resp.status_code == 200:
                    print(f"[SKIP] {template_name}: 已存在于数据库中")
                    skipped += 1
                    continue
            except httpx.HTTPError:
                pass  # 404 或连接失败，继续创建

            # 创建模板
            payload = {
                "template_name": template_name,
                "system_prompt": "__NONE__",
                "user_prompt": user_prompt,
                "function_category": config["function_category"],
                "remarks": convert_langchain_to_eval(config["remarks"]),
                "prompt_source": "readify_agi",
                "change_log": "从 readify_agi prompt 文件初始迁移",
            }

            create_url = f"{base_url}/api/v1/prompt-templates"
            try:
                resp = client.post(create_url, json=payload)
                if resp.status_code == 201:
                    print(f"[OK]   {template_name}: 创建成功")
                    created += 1
                elif resp.status_code == 400 and "已存在" in resp.text:
                    print(f"[SKIP] {template_name}: 已存在于数据库中")
                    skipped += 1
                else:
                    print(f"[FAIL] {template_name}: HTTP {resp.status_code} - {resp.text}")
                    failed += 1
            except httpx.HTTPError as exc:
                print(f"[FAIL] {template_name}: {exc}")
                failed += 1

    print(f"\n迁移完成: 创建 {created}, 跳过 {skipped}, 失败 {failed}")
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
