# Drama Monitor

A script to automatically track and download new episodes of TV series. It runs in a continuous loop, checking for updates at a configurable interval.

## How It Works

The script periodically checks the series pages specified in `config.yaml`. If it finds new episodes hosted on `gofile.io`, it automatically extracts the final download link and passes it to `yt-dlp`.

## Setup

1.  **Install Dependencies:**

    To install all necessary libraries, run the command:
    ```bash
    uv sync
    ```

2.  **Configuration File:**

    Create or edit the `config.yaml` file. It's separated into a `settings` block for global options and a `series` list for the shows you want to track.

    ```yaml
    # Global settings for the script
    settings:
      # The root directory where series should be downloaded
      download_directory: "downloads"
      
      # Custom arguments for yt-dlp
      # Example for multi-threaded downloading:
      yt-dlp_args:
        - "--concurrent-fragments"
        - "4"

    # List of series to track
    series:
      - name: "Series Name"
        url: "https://filecrypt.cc/Container/YOUR_CONTAINER_ID.html"
        series: 0 # The number of the last downloaded episode
      
      - name: "Another Series"
        url: "https://filecrypt.cc/Container/ANOTHER_ID.html"
        series: 15
    ```

## Usage

To run the script, execute the command:

```bash
uv run python main.py
```

The script will start and run continuously, performing checks at the interval specified in `config.yaml`. New episodes will be downloaded to the `downloads` folder, with a separate subfolder created for each series. After each successful download, the `config.yaml` file will be updated automatically.

To stop the script, press `Ctrl+C` in the terminal.