import click

@click.group()
def main():
    """Dota Coach CLI."""

@main.command()
def run():
    """Start the realtime layer (常驻进程)。"""
    click.echo("[stub] realtime not yet implemented")

@main.command()
@click.option("--since-days", default=7, type=int)
def weekly(since_days: int):
    """Trigger the weekly review pipeline."""
    click.echo(f"[stub] weekly with since_days={since_days}")

@main.command("install-gsi")
def install_gsi():
    """Install Valve GSI config to the Dota 2 directory."""
    click.echo("[stub] install-gsi not yet implemented")

@main.command()
@click.option("--non-interactive", is_flag=True,
              help="跳过交互，仅在缺少 settings.yaml 时用环境变量填充。")
def init(non_interactive: bool):
    """交互式向导：填 Steam ID、Anthropic key、飞书 webhook 并写 settings.yaml。"""
    import os
    from pathlib import Path
    cfg_dir = Path("config")
    cfg_dir.mkdir(parents=True, exist_ok=True)
    out = cfg_dir / "settings.yaml"

    if out.exists() and not non_interactive:
        if not click.confirm(f"{out} 已存在，覆盖吗？", default=False):
            click.echo("跳过，未修改。")
            return

    def _ask(prompt, env_key, default=None, hide_input=False):
        env_val = os.environ.get(env_key)
        if env_val:
            return env_val
        if non_interactive:
            return default or ""
        return click.prompt(prompt, default=default or "",
                            hide_input=hide_input, show_default=bool(default))

    click.echo("\n=== Dota Coach 初始化 ===\n")
    click.echo("1) Steam 32 位 ID")
    click.echo("   去 https://opendota.com 搜你的名字，URL 中 /players/<数字> 那串")
    steam_id = _ask("   Steam 32-bit ID", "DOTACOACH_STEAM_ID")

    click.echo("\n2) Anthropic API key（每周一次复盘调用，月成本 < $1）")
    click.echo("   去 https://console.anthropic.com 拿一个")
    anthropic_key = _ask("   Anthropic API key", "DOTACOACH_ANTHROPIC_KEY",
                         hide_input=True)

    click.echo("\n3) 飞书 webhook URL（可选，不填就只本地存报告）")
    feishu = _ask("   飞书 webhook URL（回车跳过）",
                  "DOTACOACH_FEISHU_WEBHOOK", default="")

    out.write_text(
        f"steam_id_32: {steam_id}\n"
        f"anthropic_api_key: \"{anthropic_key}\"\n"
        + (f"feishu_webhook_url: \"{feishu}\"\n" if feishu else
           "feishu_webhook_url: null\n") +
        "dota_path: null\n"
        "gsi_port: 4000\n"
        "log_level: \"INFO\"\n"
        "voice_engine: \"edge\"\n"
        "voice_name: \"zh-CN-XiaoxiaoNeural\"\n"
        "mute_hotkey: \"F8\"\n"
    )
    click.echo(f"\n✓ 已写入 {out}")
    click.echo("\n下一步：")
    click.echo("  1. uv run dotacoach install-gsi   # 部署 Valve GSI 配置")
    click.echo("  2. 在 Steam → Dota 2 → 属性 → 启动选项 加：")
    click.echo("     -gamestateintegration -condebug")
    click.echo("  3. uv run dotacoach run            # 启动实时层")

if __name__ == "__main__":
    main()
