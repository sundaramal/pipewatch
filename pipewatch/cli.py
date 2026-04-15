"""CLI entry point for pipewatch."""

import sys
import click

from pipewatch.config import load_config, ConfigError
from pipewatch.alerts_config import load_alerters
from pipewatch.checks.builtin import ThresholdCheck, FreshnessCheck
from pipewatch.runner import run_checks

CHECK_REGISTRY = {
    "threshold": ThresholdCheck,
    "freshness": FreshnessCheck,
}


def build_checks(pipeline_config):
    """Instantiate check objects from a PipelineConfig."""
    checks = []
    for check_cfg in pipeline_config.checks:
        cls = CHECK_REGISTRY.get(check_cfg.type)
        if cls is None:
            raise ConfigError(f"Unknown check type: {check_cfg.type!r}")
        checks.append(cls(name=check_cfg.name, **check_cfg.params))
    return checks


@click.command()
@click.argument("config_path", type=click.Path(exists=True))
@click.option("--alerts", "alerts_path", default=None, type=click.Path(exists=True),
              help="Path to alerts config file.")
@click.option("--verbose", "-v", is_flag=True, default=False,
              help="Print individual check results.")
def main(config_path, alerts_path, verbose):
    """Run pipeline health checks defined in CONFIG_PATH."""
    try:
        pipeline_config = load_config(config_path)
    except ConfigError as exc:
        click.echo(f"[pipewatch] Config error: {exc}", err=True)
        sys.exit(2)

    try:
        checks = build_checks(pipeline_config)
    except ConfigError as exc:
        click.echo(f"[pipewatch] Check build error: {exc}", err=True)
        sys.exit(2)

    report = run_checks(checks)

    if verbose:
        for result in report.results:
            click.echo(str(result))

    click.echo(
        f"\nPipeline : {pipeline_config.name}\n"
        f"Passed   : {report.num_passed}/{report.total}\n"
        f"Failed   : {report.num_failed}/{report.total}"
    )

    if alerts_path:
        alerters = load_alerters(alerts_path)
        for alerter in alerters:
            alerter.notify(report)

    if not report.passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
