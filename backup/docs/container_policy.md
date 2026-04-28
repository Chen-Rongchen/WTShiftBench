# 容器与环境策略

## 当前结论

当前项目没有正式 Docker Hub 镜像，也没有可引用的不可变版本标签。因此默认运行路径是 `pixi`，不是 Docker。

## 推荐运行方式

```bash
pixi install --environment core
pixi run --environment core wtbench version
pixi run --environment core wtbench list
```

模型相关 GPU 环境按需使用：

```bash
pixi install --environment gears
pixi install --environment scgpt
pixi install --environment geneformer
```

## Docker 启用条件

只有同时满足以下条件时，才把 Docker 写成正式入口：

- 已发布 Docker Hub 仓库
- 镜像 tag 与项目版本一致
- tag 不覆盖历史镜像
- 文档中给出完整拉取与运行命令
- CI 或本地 smoke test 覆盖镜像入口

在这些条件满足前，Docker 只能作为后续可选交付项，不作为当前项目默认运行路径。
