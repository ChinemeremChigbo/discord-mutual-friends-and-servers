import argparse
import logging
import os
import sys

from dotenv import load_dotenv

from core import run_client
from get_token import get_token


def check_positive_float(original_value):
    try:
        value = float(original_value)
        if value <= 0:
            raise argparse.ArgumentTypeError(f"{original_value} is not a positive")
    except ValueError:
        raise Exception(f"{original_value} is not a float")
    return value


def check_nonnegative_float(original_value):
    try:
        value = float(original_value)
        if value < 0:
            raise argparse.ArgumentTypeError(f"{original_value} is negative")
    except ValueError:
        raise Exception(f"{original_value} is not a float")
    return value


def add_arguments(parser: argparse.ArgumentParser, output_path: str) -> None:
    parser.add_argument(
        "-s",
        "--sleep_time",
        default=3.0,
        type=check_positive_float,
        help=(
            "How long to sleep between each member request. With values lower than 3, "
            "rate limits tend to be hit, which may lead to a ban. Increase if you hit a "
            "rate limit. Example --sleep_time 4, default=3"
        ),
    )

    parser.add_argument(
        "-l",
        "--loglevel",
        default="info",
        choices=["debug", "info", "warn", "warning", "error", "critical"],
        help="Provide logging level. Example --loglevel debug, default=info",
    )

    parser.add_argument(
        "-v",
        "--output_verbosity",
        default=2,
        type=int,
        choices=[1, 2, 3],
        help=(
            "How much information to be included in the mutual friends and mutual servers "
            "files. 1 means just the member name. 2 means the member name and a count the "
            "member's of mutual friends or mutual servers. 3 means the member name and a "
            "list of the member's mutual friends or mutual servers. Example --output_verbosity 3, default=2"
        ),
    )

    parser.add_argument(
        "-p",
        "--print_info",
        default=True,
        help=(
            "If true, the server info, mutual friends, and mutual servers are printed to "
            "the command line. Example --print_info False, default=True"
        ),
    )

    parser.add_argument(
        "-j",
        "--write_to_json",
        default=True,
        help=(
            "If true, the server info, mutual friends, and mutual servers are written to "
            "json files. Example --write_to_json False, default=True"
        ),
    )

    parser.add_argument(
        "-o",
        "--output_path",
        default=output_path,
        help=(
            "Location for output files. Example --output_path some_directory/some_subdirectory/, "
            "default=pwd+'output'"
        ),
    )

    parser.add_argument(
        "-i",
        "--include_servers",
        default=[],
        nargs="+",
        help=(
            "Only process servers whose names are in this list. If not specified, process all "
            "servers. Put server names with multiple words in quotes. Example --include_servers "
            "'server 1' 'server2' 'server3', default=''"
        ),
    )

    parser.add_argument(
        "-c",
        "--include_channels",
        default=[],
        nargs="+",
        help=(
            "Only process the members who are in the provided channels. If not specified, tries to retrieve "
            "all server members if you have the appropriate permissions, otherwise attempts to scrape the member "
            "sidebar. Example --include_channels 'general' 'help'"
        ),
    )

    parser.add_argument(
        "-g",
        "--get_token",
        action="store_true",
        help="If set, will run the get_token script to get a token",
    )

    parser.add_argument(
        "-m",
        "--max_members",
        type=int,
        default=sys.maxsize,
        help="Maximum number of members to process. Example --max_members 100, default=no limit",
    )

    parser.add_argument(
        "--period_max_members",
        type=int,
        default=100,
        help="Number of members to fetch per period. Example --period_max_members 100, default=100",
    )

    parser.add_argument(
        "--pause_duration",
        type=int,
        default=300,
        help="Pause duration between periods in seconds. Example --pause_duration 300, default=300",
    )

    parser.add_argument(
        "--member_fetch_timeout",
        type=check_nonnegative_float,
        default=0,
        help=(
            "Timeout in seconds for fetch_members/chunk. Use 0 to wait indefinitely. "
            "Example --member_fetch_timeout 30, default=0"
        ),
    )


def main() -> None:
    output_path = os.path.dirname(os.path.realpath(__file__)) + "/output/"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    parser = argparse.ArgumentParser()
    add_arguments(parser, output_path)
    args = parser.parse_args()

    if args.get_token:
        token = get_token()
    else:
        key = "TOKEN"
        if key in os.environ:
            del os.environ[key]
        load_dotenv(verbose=True)
        token = os.getenv(key)

    logging.basicConfig(level=args.loglevel.upper())

    run_client(
        token=token,
        sleep_time=args.sleep_time,
        output_verbosity=args.output_verbosity,
        print_info=args.print_info,
        write_to_json=args.write_to_json,
        output_path=args.output_path,
        include_servers=args.include_servers,
        include_channels=args.include_channels,
        max_members=args.max_members,
        period_max_members=args.period_max_members,
        pause_duration=args.pause_duration,
        member_fetch_timeout=args.member_fetch_timeout,
    )


if __name__ == "__main__":
    main()
