#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "requests",
#   "rich",
# ]
# ///
import argparse
import datetime
import mimetypes
import os
import sys
import time

import requests
from requests.exceptions import HTTPError, RequestException
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

TRANSCRIPTION_URL = "http://localhost:3647/v1/audio/transcriptions"
MODEL_NAME = "whisper-large-v3-turbo"

console = Console()


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-h", "--help", action="store_true")
    parser.add_argument("-t", "--timestamps", action="store_true")
    parser.add_argument("audio_file", nargs="?")
    parser.add_argument("output_file", nargs="?")

    try:
        args = parser.parse_args()
    except SystemExit:
        print_correct_usage()
        sys.exit(1)

    if args.help:
        print_correct_usage()
        sys.exit(0)

    if not args.audio_file:
        console.print(
            "[bold red]Error: Missing required <path_to_audio_file> argument.[/bold red]"
        )
        console.print(
            "Run with [cyan]-h[/cyan] or [cyan]--help[/cyan] for usage instructions."
        )
        sys.exit(1)

    file_path = args.audio_file
    if not os.path.exists(file_path):
        console.print(
            Panel(
                f"[bold]File not found:[/bold] [red]{file_path}[/red]",
                title="[bold red]✗ Error[/bold red]",
                border_style="red",
                padding=(0, 2),
            )
        )
        sys.exit(1)

    output_path = (
        args.output_file if args.output_file else resolve_output_path(file_path)
    )
    filename = os.path.basename(file_path)
    mime_type = detect_mime_type(file_path)

    console.print()
    console.print(
        build_file_summary_table(filename, mime_type, file_path, args.timestamps)
    )
    console.print()

    try:
        with console.status(
            "[bold cyan]Transcribing audio[/bold cyan]",
            spinner="dots",
            spinner_style="cyan",
        ):
            transcribed_text, elapsed = transcribe_audio(
                file_path=file_path,
                filename=filename,
                mime_type=mime_type,
                include_timestamps=args.timestamps,
            )

        save_transcription(transcribed_text, output_path)
        console.print(build_result_stats_table(transcribed_text, elapsed, output_path))

    except HTTPError as error:
        console.print(
            Panel(
                f"[bold]HTTP {error.response.status_code}[/bold] — {error}",
                title="[bold red]✗ Server error[/bold red]",
                border_style="red",
                padding=(0, 2),
            )
        )
        sys.exit(1)
    except RequestException as error:
        console.print(
            Panel(
                str(error),
                title="[bold red]✗ Connection error[/bold red]",
                border_style="red",
                padding=(0, 2),
            )
        )
        sys.exit(1)
    except IOError as error:
        console.print(
            Panel(
                str(error),
                title="[bold red]✗ Failed to write output file[/bold red]",
                border_style="red",
                padding=(0, 2),
            )
        )
        sys.exit(1)
    except Exception as error:
        console.print(
            Panel(
                str(error),
                title="[bold red]✗ Unexpected error[/bold red]",
                border_style="red",
                padding=(0, 2),
            )
        )
        sys.exit(1)


def print_correct_usage() -> None:
    console.print(
        Panel(
            "[bold]Usage:[/bold]\n"
            "  transcribe [cyan]<path_to_audio_file>[/cyan] [dim]\\[optional_output_txt_path][/dim] [cyan]\\[options][/cyan]\n\n"
            "[bold]Options:[/bold]\n"
            "  -t, --timestamps          Include timestamps in the output\n"
            "  -h, --help                Show this help message and exit\n\n"
            "[bold]Examples:[/bold]\n"
            "  transcribe [cyan]lecture.mp3[/cyan]               [dim]# Saves to lecture.txt in the same directory[/dim]\n"
            "  transcribe [cyan]lecture.mp3 -t[/cyan]            [dim]# Saves with timestamps to lecture.txt[/dim]\n"
            "  transcribe [cyan]meeting.m4a[/cyan] [cyan]/tmp/out.txt[/cyan]  [dim]# Saves explicitly to /tmp/out.txt[/dim]",
            title="[bold magenta]✦ Transcribe CLI[/bold magenta]",
            border_style="magenta",
            padding=(1, 2),
        )
    )


def resolve_output_path(audio_path: str) -> str:
    return os.path.splitext(audio_path)[0] + ".txt"


def detect_mime_type(file_path: str) -> str:
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or "application/octet-stream"


def build_file_summary_table(
    filename: str,
    mime_type: str,
    file_path: str,
    include_timestamps: bool,
) -> Table:
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

    table = Table(box=box.ROUNDED, show_header=False, border_style="dim cyan")
    table.add_column("Key", style="bold cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("File", filename)
    table.add_row("MIME type", mime_type)
    table.add_row("Size", f"{file_size_mb:.1f} MB")
    table.add_row("Server", TRANSCRIPTION_URL)
    table.add_row("Model", MODEL_NAME)
    table.add_row("Timestamps", "Enabled" if include_timestamps else "Disabled")
    return table


def transcribe_audio(
    file_path: str,
    filename: str,
    mime_type: str,
    include_timestamps: bool = False,
) -> tuple[str, float]:
    start_time = time.monotonic()
    with open(file_path, "rb") as audio_file:
        files = {"file": (filename, audio_file, mime_type)}
        data = {"model": MODEL_NAME}

        if include_timestamps:
            data["response_format"] = "verbose_json"
            data["timestamp_granularities"] = ["segment"]

        response = requests.post(TRANSCRIPTION_URL, files=files, data=data)
        response.raise_for_status()

    elapsed = time.monotonic() - start_time
    response_json = response.json()

    if include_timestamps:
        segments = response_json.get("segments", [])
        lines = []
        for segment in segments:
            start_time_seconds = segment.get("start", 0.0)
            end_time_seconds = segment.get("end", 0.0)
            text = segment.get("text", "").strip()

            start_timestamp = str(datetime.timedelta(seconds=start_time_seconds))
            end_timestamp = str(datetime.timedelta(seconds=end_time_seconds))

            lines.append(f"[{start_timestamp} --> {end_timestamp}] {text}")
        transcribed_text = "\n".join(lines)
    else:
        transcribed_text = response_json.get("text", "").strip()

    return transcribed_text, elapsed


def save_transcription(transcribed_text: str, output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8") as output_file:
        output_file.write(transcribed_text + "\n")


def build_result_stats_table(
    transcribed_text: str,
    elapsed_seconds: float,
    output_path: str,
) -> Table:
    word_count = len(transcribed_text.split())
    char_count = len(transcribed_text)

    table = Table(box=box.ROUNDED, show_header=False, border_style="dim green")
    table.add_column("Key", style="bold green", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Words", str(word_count))
    table.add_row("Characters", str(char_count))
    table.add_row("Time taken", f"{elapsed_seconds:.1f}s")
    table.add_row("Saved to", output_path)
    return table


if __name__ == "__main__":
    main()
