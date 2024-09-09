# Vena Downloader Manager

Vena is a powerful cross-platform downloader manager that integrates seamlessly with browser extensions, allowing users to capture and download media files directly from their browser. With support for multiple concurrent downloads, a download queue system, and real-time progress tracking, Vena offers a streamlined and efficient downloading experience.

## Features

- **Browser Integration**: Integrates with Chrome and Firefox browser extensions to capture and download files (e.g., videos, images) effortlessly.
- **Concurrent Downloads**: Download multiple files simultaneously without overwhelming your system.
- **Download Queue**: Organize your downloads efficiently by adding tasks to a queue.
- **Auto Resume**: Automatically resumes interrupted downloads after connection failures or network issues.
- **Progress Monitoring**: Track the download status with a floating window that shows the number of active downloads and a cumulative progress bar.
- **Custom File Naming**: Extract titles and metadata from web pages for clear and consistent file names.
- **Websocket Communication**: Uses websockets to receive file download requests from the browser extension.
- **Cross-Platform**: Available for Windows, macOS, and Linux.
- **Minimal UI**: Simple, customizable user interface with options like a circular progress bar for visual feedback.

## Requirements

- Python 3.8+
- PyQt6 for the user interface
- `aiohttp` for handling downloads
- Websockets for browser extension communication

