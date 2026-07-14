# 参与贡献

感谢你参与 `heige-feishu-word`。

## 本地开发

```bash
git clone https://github.com/HeiGeAi/heige-feishu-word.git
cd heige-feishu-word
python3 -m pip install --upgrade pip
python3 -m pip install -e .
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## 提交要求

1. 新能力需要补充行为测试。
2. 不支持的内容必须明确失败，不能静默丢失。
3. 不要提交真实客户材料、账号标识、Token、cookie 或密钥。
4. 新增 SVG 能力时，必须保留真实文本节点，并通过安全检查。
5. Pull Request 需要说明修改目的、用户影响和验证命令。

## 问题反馈

普通问题与功能建议请使用 GitHub Issues。安全问题不要公开提交，请遵循 `SECURITY.md`。
