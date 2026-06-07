# Transcribe CLI

[![License](https://img.shields.io/github/license/ImadSaddik/TranscribeCLI)](https://github.com/ImadSaddik/TranscribeCLI/blob/main/LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.12%2B-blue)](https://www.python.org/)

![transcribe_cli_banner](./images/readme_banner.png)

Transcribe CLI is a fast, lightweight, and user-friendly command-line utility for transcribing audio files using a local server running [whisper.cpp](https://github.com/ggml-org/whisper.cpp).

## Prerequisites

### uv

You can install `uv` by following the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/) or using the following command:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Python

You need Python 3.12 or higher to run this CLI tool. You can check your Python version with:

```bash
python --version
```

### Local server

You must have a transcription server running locally. For detailed instructions on setting up a local server on Linux, please refer to [this article](https://imadsaddik.com/blogs/local-ai-stack-on-linux#working-with-audio-models).

> [!NOTE]
> The default port is `3647`, but you can change it in [transcribe.py](./transcribe.py) if needed.

## Installation

You can install the CLI tool system-wide using the provided [Makefile](./Makefile).

Navigate to the project directory and run:

```bash
make install
```

This command installs a lightweight wrapper script in `/usr/local/bin/transcribe` which automatically runs the main script with the correct dependencies using `uv`.

To uninstall the script, run:

```bash
make uninstall
```

## Usage

Run the `transcribe` command followed by the path to your audio file:

```bash
transcribe podcast.mp3
```

By default, the transcription will be saved in the same directory as the audio file with a `.txt` extension.

If you want to specify a custom output file path, pass it as a second argument:

```bash
transcribe podcast.mp3 /path/to/custom_output.txt
```

To view the help information:

```bash
transcribe --help
```

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.
