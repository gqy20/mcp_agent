"""CLI 辅助函数模块.

此模块包含 CLI 处理的辅助函数。
"""


def convert_test_results_to_dict(test_results: list) -> list[dict]:
    """将TestResult对象列表转换为字典格式，供HTTP评估使用."""
    test_results_dict = []
    for t in test_results:
        if hasattr(t, "success"):
            # 使用to_concise_dict方法获取基本信息
            test_dict = t.to_concise_dict() if hasattr(t, "to_concise_dict") else {}
            # 确保包含必要的字段，包括ai_confidence
            test_dict.update(
                {
                    "test_name": getattr(t, "test_name", "Unknown Test"),
                    "success": getattr(t, "success", False),
                    "duration": getattr(t, "duration", 0.0),
                    "error_message": getattr(t, "error_message", None),
                    "test_category": getattr(t, "test_category", "未知"),
                    "ai_confidence": getattr(
                        t, "ai_confidence", 0.0
                    ),  # 关键修复：包含ai_confidence字段
                }
            )

            # 处理异常类型的ai_confidence值
            ai_confidence = test_dict["ai_confidence"]
            if isinstance(ai_confidence, list):
                # 如果是列表，计算平均值
                numeric_values = [
                    c for c in ai_confidence if isinstance(c, (int, float))
                ]
                if numeric_values:
                    test_dict["ai_confidence"] = sum(numeric_values) / len(
                        numeric_values
                    )
                else:
                    test_dict["ai_confidence"] = 0.0
            elif ai_confidence is None:
                # 如果是None，转换为0.0
                test_dict["ai_confidence"] = 0.0
            elif not isinstance(ai_confidence, (int, float)):
                # 如果是其他类型，转换为0.0
                test_dict["ai_confidence"] = 0.0
            else:
                # 确保是数值类型
                test_dict["ai_confidence"] = float(ai_confidence)

            test_results_dict.append(test_dict)
    return test_results_dict
