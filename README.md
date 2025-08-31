# Drama Monitor

A script to automatically track and download new episodes of TV series.

## How It Works

The script periodically checks the series pages specified in `config.yaml`. If it finds new episodes hosted on `gofile.io`, it automatically extracts the final download link and passes it to `yt-dlp`.

## Setup

1.  **Install Dependencies:**

    To install all necessary libraries, run the command:
    ```bash
    uv sync
    ```

2.  **Configuration File:**

    Create or edit the `config.yaml` file. Add the series you want to track in the following format:

    ```yaml
    - name: "Series Name"
      url: "https://filecrypt.cc/Container/CONTAINER.html"
      last: 0 # The number of the last downloaded episode
    
    - name: "Another Series"
      url: "https://filecrypt.cc/Container/ANOTHER_CONTAINER.html"
      last: 15
    ```

    - `name`: The name of the series. This will be used to create a folder for the downloaded files.
    - `url`: The link to the "container" page that lists all the episodes.
    - `last`: The number of the last episode that was downloaded. The script will look for all episodes with a number greater than this.

## Usage

To run the script, execute the command:

```bash
uv run python main.py
```

The script will start checking all series from the config. New episodes will be downloaded to the `downloads` folder, with a separate subfolder created for each series. After each successful download, the `config.yaml` file will be updated automatically.