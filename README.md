# video_resolution_detector

## Overview
`video_resolution_detector` is a script designed to scan directories for video files and identify those that match specific resolution criteria. It recursively searches through MP4 files and generates detailed reports of videos that meet the specified resolution requirements. This tool is particularly useful for managing video libraries, identifying content for transcoding, or organizing media collections by resolution.

## What's New
- **Parallel Processing:** The script now uses multiple worker processes for faster scanning of large video libraries.
- **Robust Metadata Extraction:** Uses ffmpeg-python for reliable video metadata extraction and improved error handling.
- **Detailed Output Logs:** Generates both human-readable text and machine-readable JSON logs, including scan metadata, matching files, and error details.
- **Flexible Configuration:** All major options (resolution, comparison, directories, workers) can be set via environment variables or command-line flags.
- **Enhanced Resolution Matching:** Supports both width×height and height-only formats, with ±10px tolerance for height-only matches.
- **Docker & Standalone Support:** Can be run inside Docker or directly as a Python script.

## Features
- Recursively scan directories for MP4 video files
- Flexible resolution detection (height-only or width×height formats)
- Multiple comparison operators (equal, less than or equal, greater than or equal)
- **Parallel processing for faster scans**
- Detailed logging with both text and JSON output formats
- Error handling for corrupted or unreadable video files
- Docker-ready with environment variable support

## Usage
To use the script, run the following command inside a Docker container or directly as a Python script:

```sh
docker run --rm -v <source_directory>:/src -v <log_directory>:/log lamusmaser/video_resolution_detector
```

Or run locally:
```sh
python video_detector.py --resolution 720p --comparison lte --src-dir /path/to/videos --log-dir /path/to/logs
```

Replace `<source_directory>` with the path containing your video files and `<log_directory>` with where you want the scan results saved.

## Example
```sh
# Find all 360p videos
docker run --rm -v /path/to/videos:/src -v /path/to/logs:/log lamusmaser/video_resolution_detector

# Find videos 720p or smaller
docker run --rm -e RESOLUTION=720p -e COMPARISON=lte -v /path/to/videos:/src -v /path/to/logs:/log lamusmaser/video_resolution_detector

# Find videos exactly 1920x1080
docker run --rm -e RESOLUTION=1920x1080 -e COMPARISON=eq -v /path/to/videos:/src -v /path/to/logs:/log lamusmaser/video_resolution_detector
```

## Environment Variables
| Variable     | Description                                      | Default Value | Valid Options |
|--------------|--------------------------------------------------|---------------|---------------|
| `RESOLUTION` | Target resolution to search for                 | `360p`        | `360p`, `360`, `1920x1080`, etc. |
| `COMPARISON` | Comparison operator for resolution matching     | `eq`          | `eq`, `lte`, `gte` |
| `SRC_DIR`    | Source directory containing video files         | `/src`        | Any valid directory path |
| `LOG_DIR`    | Directory for output logs                       | `/log`        | Any valid directory path |

## Resolution Formats
The script supports multiple resolution format inputs:

### Height-only formats:
- `360p` - Videos with height of 360 pixels (±10px tolerance)
- `360` - Same as above, without the 'p' suffix
- `720p`, `1080p`, `1440p`, `4320p`, etc.

### Width×Height formats:
- `1920x1080` - Videos with exact width and height dimensions
- `1280x720`, `3840x2160`, `2560x1440`, etc.

## Comparison Operators
- `eq` - Equal to (with tolerance for height-only formats)
- `lte` - Less than or equal to
- `gte` - Greater than or equal to

## Output Files
The script generates timestamped output files in the log directory:

### Text Log (`video_scan_[criteria]_[timestamp].txt`)
- Human-readable summary of scan results
- List of matching videos with dimensions
- Error log for problematic files
- **Includes scan metadata: criteria, processed count, error count, etc.**

### JSON Log (`video_scan_[criteria]_[timestamp].json`)
- Detailed metadata for all matching videos
- Complete error information
- Machine-readable format for further processing
- **Includes scan timestamp, criteria, and summary statistics**

## Command Line Usage
For direct script execution (outside Docker):

```sh
python video_detector.py --resolution 720p --comparison lte --src-dir /path/to/videos --log-dir /path/to/logs
```

### Available Flags
| Flag           | Short | Description                               | Default |
|----------------|-------|-------------------------------------------|---------|
| `--resolution` | `-r`  | Target resolution                         | `360p`  |
| `--comparison` | `-c`  | Comparison type (eq/lte/gte)             | `eq`    |
| `--src-dir`    | `-s`  | Source directory to scan                  | `/src`  |
| `--log-dir`    | `-l`  | Log output directory                      | `/log`  |

## Requirements
- Docker
- FFmpeg (included in Docker image)

## Local Installation of Script
Clone the repository and navigate to the project directory:

```sh
git clone https://github.com/yourusername/video_resolution_detector.git
cd video_resolution_detector
```

Install FFmpeg on your system:
```sh
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Or use your system's package manager
```

Run the script directly:
```sh
python video_detector.py --resolution 1080p --comparison gte --src-dir ./videos --log-dir ./logs
```

## Docker Compose Example
```yaml
version: '3.8'
services:
  video-scanner:
    image: lamusmaser/video_resolution_detector
    environment:
      - RESOLUTION=720p
      - COMPARISON=lte
      - SRC_DIR=/src
      - LOG_DIR=/log
    volumes:
      - ./videos:/src
      - ./scan_results:/log
```

## Use Cases
- **Media Library Management**: Identify videos that need transcoding
- **Storage Optimization**: Find high-resolution videos for compression
- **Content Classification**: Organize videos by resolution categories
- **Quality Control**: Verify video specifications in large collections
- **Batch Processing**: Generate lists for automated video processing workflows

## Error Handling
The script handles various error conditions gracefully:
- Corrupted or unreadable video files are skipped and logged
- Missing metadata is reported without stopping the scan
- **Worker process errors are captured and reported**
- FFmpeg timeout protection for problematic files
- Detailed error reporting in both text and JSON formats

## Contributing
Contributions are welcome! Please open an issue or submit a pull request.

## License
This project is licensed under the Unlicense - see the LICENSE file for details.