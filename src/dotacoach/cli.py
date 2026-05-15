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

if __name__ == "__main__":
    main()
