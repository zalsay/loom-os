# 计划567，实际525，漏旧v5的42项

准备253 task.py时由旧文件字符串替换误把测试模块v5替换为v6，而非追加：实际原v4及更旧469＋新v6 56＝525。HOST.RESULT及完整日志525PASS/0fail/0error/0skip，68.078秒，原日志不改。旧v5 42项在本轮未运行；251的成功不冒充本轮重测。

archive_review.py在录前仍预期567，已知该预期不符合实际，因此不执行或回填原脚本；独立archive_review_v2.py只按实际525核实、明确planned567/omitted42/full_planned_regression=false，增加asr_service独立只读差异盘点。不运行第二次freeze或补测、配置、ninja。下一轮要显式恢复全部18个测试模块，核名称与实际计数后再继续。
