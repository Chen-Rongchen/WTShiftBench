# 文档导航

## 1. 这几个文档分别做什么

当前仓库的文档分成三层：

* `README.md`：说明当前仓库真实存在、真实能跑、真实可验证的 `Stage 1A` 主线
* `plan.md`：当前可执行计划，只服务近期开发
* `docs/protocol_blueprint.md`：长期制度蓝图，承接 `Stage 1B/2/3` 与上位约束

## 2. docs 目录中的文件

* `docs/README.md`：文档地图
* `docs/protocols/stage1a_freeze_stage1b.md`：Stage 1A → Freeze → Stage 1B 制度协议（与蓝图第 6.0 节互链）
* `docs/protocol_blueprint.md`：长期协议蓝图
* `docs/environment_strategy.md`：当前 `pixi` 多环境策略与约束
* `docs/repository_map.md`：当前仓库目录职责说明
* `docs/entrants/stage1a_inner_validation_minimal_rule.md`：Stage 1A 当前采用的最简 inner-validation 收口规则
* `schemas/freeze_manifest.template.yaml`：Stage 1A 通过后、Stage 1B 前的 **Freeze 清单**模板（复制填实后归档）

## 3. 使用顺序

如果你是第一次进入这个仓库，推荐按下面顺序阅读：

1. `README.md`
2. `plan.md`
3. `docs/repository_map.md`
4. `docs/environment_strategy.md`
5. `docs/protocol_blueprint.md`

## 4. 维护原则

维护文档时遵守以下边界：

* 当前仓库事实写进 `README.md`
* 近期开发安排写进 `plan.md`
* 长期制度与未来阶段写进 `docs/protocol_blueprint.md`
* 不把未来蓝图重新塞回当前执行文档
