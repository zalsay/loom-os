# `cofe`（macOS）

`./cofe` 在前台调用系统自带的 `/usr/bin/caffeinate -i`，按 `Ctrl-C` 停止；`./cofe --help` 查看简要用法。不接受其他参数。

`-i` 仅阻止系统因空闲而休眠；不保持显示器常亮，也不保证屏保触发的锁屏、手动锁屏、合盖或组织管理策略不会锁定。此命令不修改系统锁屏/屏保策略、密码设置或电源设置，也不模拟键盘/鼠标。没有对长时间屏保或自动锁屏策略做验证。仅支持 macOS；其他系统会明确拒绝。

聚焦测试：

```sh
python3 -m unittest tools.tests.test_cofe
```
