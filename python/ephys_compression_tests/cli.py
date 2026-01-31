#!/usr/bin/env python3

import click
from typing import List, Optional
from .run_benchmarks.run_benchmarks import run_benchmarks
from .algorithms import algorithms
from .datasets import datasets


def get_available_algorithms() -> List[str]:
    """Get list of available algorithm names"""
    return [alg.name for alg in algorithms]


def get_available_datasets() -> List[str]:
    """Get list of available dataset names"""
    return [ds.name for ds in datasets]


def filter_algorithms(selected: Optional[List[str]] = None) -> List[dict]:
    """Filter algorithms based on selected names"""
    if not selected:
        return algorithms
    return [alg for alg in algorithms if alg.name in selected]


def filter_datasets(selected: Optional[List[str]] = None) -> List[dict]:
    """Filter datasets based on selected names"""
    if not selected:
        return datasets
    return [ds for ds in datasets if ds.name in selected]


def validate_algorithms(ctx, param, value):
    if not value:
        return None
    available = get_available_algorithms()
    invalid = [alg for alg in value if alg not in available]
    if invalid:
        raise click.BadParameter(
            f"Invalid algorithm(s): {', '.join(invalid)}. "
            f"Available algorithms: {', '.join(available)}"
        )
    return value


def validate_datasets(ctx, param, value):
    if not value:
        return None
    available = get_available_datasets()
    invalid = [ds for ds in value if ds not in available]
    if invalid:
        raise click.BadParameter(
            f"Invalid dataset(s): {', '.join(invalid)}. "
            f"Available datasets: {', '.join(available)}"
        )
    return value


@click.group()
def cli():
    """Benchmark compression algorithms for electrophysiology data"""
    pass


@cli.command()
def list():
    """List available algorithms and datasets"""
    click.echo("\nAvailable Algorithms:")
    for alg in algorithms:
        desc = alg.description if alg.description else "No description"
        click.echo(f"  {alg.name:<20} - {desc}")

    click.echo("\nAvailable Datasets:")
    for ds in datasets:
        desc = ds.description if ds.description else "No description"
        click.echo(f"  {ds.name:<20} - {desc}")


@cli.command()
@click.option(
    "--algorithm",
    "-a",
    multiple=True,
    callback=validate_algorithms,
    help="Algorithm(s) to benchmark (can be specified multiple times)",
)
@click.option(
    "--dataset",
    "-d",
    multiple=True,
    callback=validate_datasets,
    help="Dataset(s) to benchmark (can be specified multiple times)",
)
@click.option(
    "--cache-dir",
    default=".benchmark_cache",
    help="Directory to store cached results",
    type=click.Path(),
)
@click.option("--quiet", "-q", is_flag=True, help="Reduce output verbosity")
@click.option("--force", "-f", is_flag=True, help="Force re-run without using cache")
def run(algorithm, dataset, cache_dir, quiet, force):
    """Run benchmarks with specified options"""
    # Filter algorithms and datasets
    filtered_algorithms = filter_algorithms(algorithm)
    filtered_datasets = filter_datasets(dataset)

    if not filtered_algorithms:
        click.echo("Error: No matching algorithms found", err=True)
        ctx = click.get_current_context()
        ctx.exit(1)
    if not filtered_datasets:
        click.echo("Error: No matching datasets found", err=True)
        ctx = click.get_current_context()
        ctx.exit(1)

    # Run benchmarks with filtered options
    results = run_benchmarks(
        cache_dir=cache_dir,
        verbose=not quiet,
        selected_algorithms=filtered_algorithms,
        selected_datasets=filtered_datasets,
        force=force,
    )

    # Print summary
    click.echo("\nBenchmark Summary:")
    for result in results["results"]:
        click.echo(
            f"\n{result['dataset']} + {result['algorithm']}:"
            f"\n  Compression ratio: {result['compression_ratio']:.2f}x"
            f"\n  Encode speed: {result['encode_mb_per_sec']:.2f} MB/s"
            f"\n  Decode speed: {result['decode_mb_per_sec']:.2f} MB/s"
        )
        if result["rmse"] != 0.0 or result["max_error"] != 0.0:
            click.echo(
                f"  RMSE: {result['rmse']:.4f}"
                f"\n  Max error: {result['max_error']:.4f}"
            )


def main():
    cli()


if __name__ == "__main__":
    main()
