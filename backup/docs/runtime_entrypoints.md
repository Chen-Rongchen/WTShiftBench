# 运行入口与环境策略

## 1. 统一入口

当前统一入口是：

```bash
pixi run --environment core wtbench list
pixi run --environment core wtbench run stage2.truth_bridge
```

也可以直接使用 Python module 入口：

```bash
pixi run --environment core python -m wtbench list
pixi run --environment core python -m wtbench run stage2.closure
```

当前已注册命令：

- `stage2.truth_bridge`
- `stage2.sensitivity`
- `stage2.closure`
- `stage2.materialize_covariates`
- `stage2.covariate_audit`
- `stage2.validate_closure`
- `stage2.bridge_decomposition`
- `stage2.rnai_demeter2_conversion`
- `stage2.k562_rnai_endpoint_consistency`
- `stage2.dixit_axis_compression`
- `stage2.dixit_temporal_panel`
- `manuscript.figure1`

## 2. 配置动态加载

命令注册表位于：

```text
configs/runtime/wtbench_cli_v1.json
```

注册表结构说明位于：

```text
configs/runtime/wtbench_cli.schema.json
```

`wtbench run <command>` 不在 CLI 代码里硬编码 workflow，而是从注册表读取：

- 命令名
- Python callable
- 默认配置文件
- 可覆盖配置的环境变量

新增主链路入口时，优先改注册表；只有需要新执行逻辑时才新增 Python 函数。

## 3. 配置覆盖顺序

配置路径解析顺序固定为：

1. `--config`
2. 命令专属环境变量，例如 `WTBENCH_STAGE2_CLOSURE_CONFIG`
3. 注册表中的 `default_config`

注册表本身可用 `WTBENCH_CLI_REGISTRY` 或 `--registry` 覆盖。

示例：

```bash
WTBENCH_STAGE2_CLOSURE_CONFIG=configs/stage2/stage2_closure_pipeline_v1.json \
  pixi run --environment core wtbench run stage2.closure
```

## 4. Docker 策略

当前项目没有发布 Docker Hub 镜像，也没有固定镜像标签。因此正式环境策略是 pixi：

```bash
pixi install --environment core
pixi run --environment core wtbench version
```

版本来源以 `pixi.toml` 的 workspace version 与 `wtbench.__version__` 同步维护。发布 Docker 镜像前，不把 Docker 写成默认运行路径。

若将来发布镜像，必须同时补齐：

- Docker Hub 仓库名
- 不可变版本标签
- 镜像构建配置
- 与 `pixi.toml` / `wtbench.__version__` 一致的版本测试
