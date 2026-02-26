# ClawROS 贡献指南

## 欢迎贡献!

感谢您对 ClawROS 项目的兴趣！我们欢迎各种形式的贡献，包括：

- 代码贡献（新功能、bug 修复）
- 文档改进
- 测试用例
- 问题报告
- 功能建议

## 开发环境设置

### 1. Fork 和克隆

```bash
# Fork 项目
# 在 GitHub 上点击 Fork 按钮

# 克隆到本地
git clone https://github.com/YOUR_USERNAME/ClawROS.git
cd ClawROS

# 添加上游远程仓库
git remote add upstream https://github.com/ORIGINAL_OWNER/ClawROS.git
```

### 2. 创建虚拟环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/macOS
# 或
.\venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -r requirements.txt
```

### 3. 安装 ROS2

按照 ROS2 官方文档安装：
https://docs.ros.org/en/jazzy/Installation.html

### 4. 验证安装

```bash
# 运行测试
pytest tests/

# 运行代码检查
flake8 src/
mypy src/
```

## 开发流程

### 1. 创建分支

```bash
# 从 upstream 更新
git checkout main
git pull upstream main

# 创建功能分支
git checkout -b feature/your-feature-name
```

分支命名规范：
- `feature/xxx` - 新功能
- `fix/xxx` - Bug 修复
- `docs/xxx` - 文档更新
- `test/xxx` - 测试相关
- `refactor/xxx` - 代码重构

### 2. 开发

```bash
# 编写代码
# 添加测试
# 确保测试通过

# 运行测试
pytest tests/ -v

# 检查代码风格
black src/ tests/
flake8 src/ tests/
```

### 3. 提交更改

```bash
# 添加更改
git add .

# 提交（使用规范的提交信息）
git commit -m "feat: add new navigation tool"
```

提交信息格式（Conventional Commits）：

```
<type>(<scope>): <subject>

<body>

<footer>
```

类型（type）：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码风格（不影响代码含义）
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/辅助工具

示例：
```
feat(tools): add scan_environment tool

Added new tool for environment scanning using LiDAR.
- Implements scan_environment method in ClawROSTools
- Adds resolution parameter (low/medium/high)
- Returns point cloud data

Closes #123
```

### 4. 推送到远程

```bash
# 推送分支
git push origin feature/your-feature-name
```

### 5. 创建 Pull Request

1. 在 GitHub 上导航到您的 fork
2. 点击 "Compare & pull request"
3. 填写 PR 描述
4. 等待 CI 检查
5. 等待代码审查

## 代码风格

### Python 风格

遵循 PEP 8 标准：

```python
# 使用 4 个空格缩进
def my_function(param1, param2):
    """文档字符串"""
    return param1 + param2

# 使用有意义的变量名
# 避免单字母变量（除非是循环计数器）

# 类使用驼峰命名
class MyClass:
    pass

# 函数和变量使用蛇形命名
def my_function():
    my_variable = 10

# 常量使用大写
MAX_SPEED = 0.5
```

### 类型注解

使用类型注解：

```python
from typing import Dict, List, Optional

def process_data(
    items: List[str],
    config: Optional[Dict[str, Any]] = None
) -> bool:
    """处理数据"""
    return True
```

### 文档字符串

为所有公共函数和类添加文档字符串：

```python
class ClawROSBridge:
    """
    ClawROS 核心桥接类
    
    这是 OpenClaw 和 ROS 之间的主要接口
    """
    
    def execute_command(self, command: ROSCommand) -> ROSResponse:
        """
        执行 ROS 命令
        
        Args:
            command: ROS 命令对象
            
        Returns:
            ROSResponse: 执行结果
            
        Raises:
            ConnectionError: 如果 ROS 连接断开
        """
        pass
```

## 测试要求

### 1. 单元测试

为所有新代码编写单元测试：

```python
def test_new_feature():
    """测试新功能"""
    # Arrange
    obj = MyClass()
    
    # Act
    result = obj.new_method()
    
    # Assert
    assert result is True
```

### 2. 覆盖率

确保测试覆盖率 >= 80%：

```bash
# 生成覆盖率报告
pytest --cov=src --cov-report=html tests/

# 查看 htmlcov/index.html
```

### 3. 运行所有测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/unit/test_bridge.py -v
```

## 代码审查

### 审查清单

提交 PR 前自查：

- [ ] 代码通过所有测试
- [ ] 代码风格符合规范
- [ ] 添加了必要的测试
- [ ] 文档已更新
- [ ] 提交信息规范

### 审查流程

1. 自动 CI 检查（测试、lint）
2. 维护者代码审查
3. 根据反馈修改
4. 审查通过后合并

## 问题报告

### Bug 报告

使用 GitHub Issues，包含以下信息：

```markdown
**问题描述**
清晰简洁地描述问题

**复现步骤**
1. 执行步骤 1
2. 执行步骤 2
3. 看到错误

**期望行为**
清晰简洁地描述期望发生什么

**实际行为**
清晰简洁地描述实际发生了什么

**环境信息**
- OS: Ubuntu 24.04
- ROS 版本：Jazzy
- Python 版本：3.10
- ClawROS 版本：0.1.0

**日志**
```
错误日志内容
```

**截图**
如有必要，添加截图
```

### 功能建议

```markdown
**功能描述**
清晰简洁地描述建议的功能

**问题/需求**
这个功能解决了什么问题？

**建议方案**
你建议如何实现这个功能？

**替代方案**
你考虑过哪些替代方案？

**额外信息**
其他相关信息
```

## 文档

### 文档结构

```
docs/
├── ARCHITECTURE.md    # 架构文档
├── TESTING.md         # 测试文档
└── USER_GUIDE.md      # 用户指南
```

### 文档风格

- 使用清晰的标题
- 提供代码示例
- 包含必要的截图
- 保持简洁明了

## 发布流程

### 版本号

遵循语义化版本（Semantic Versioning）：

```
主版本号。次版本号。修订号
MAJOR.MINOR.PATCH
```

- MAJOR: 不兼容的 API 更改
- MINOR: 向后兼容的功能添加
- PATCH: 向后兼容的问题修复

### 发布清单

发布前检查：

- [ ] 所有测试通过
- [ ] 文档已更新
- [ ] CHANGELOG 已更新
- [ ] 版本号已更新

## 联系我们

- GitHub Issues: 问题和讨论
- Email: clawros@example.com
- 社区：ROS Discourse

## 行为准则

### 我们的承诺

为了营造一个开放和友好的环境，我们承诺：

- 使用友好和包容的语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表示同理心

### 不可接受的行为

- 使用性化的语言或图像
- 人身攻击或侮辱性评论
- 公开或私下骚扰
- 未经许可发布他人信息
- 其他不道德或不专业的行为

## 许可证

通过贡献代码，您同意您的贡献将根据 MIT 许可证进行许可。

## 致谢

感谢所有为 ClawROS 做出贡献的人！
