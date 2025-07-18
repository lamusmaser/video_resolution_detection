#!/usr/bin/env python3
"""
Video Resolution Detection Script
Recursively scans /src directory for .mp4 files and
    identifies videos based on resolution criteria.
Logs results to /log directory.
"""

import argparse
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import ffmpeg

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class VideoAnalyzer:
    def __init__(
        self,
        src_dir: str = "/src",
        log_dir: str = "/log",
        resolution: str = "360p",
        comparison: str = "eq",
    ):
        self.src_dir = Path(src_dir)
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Parse resolution and comparison settings
        self.resolution = resolution
        self.comparison = comparison
        self.target_width, self.target_height = self._parse_resolution(
            resolution
        )

        # Results storage
        self.results = {
            "scan_timestamp": datetime.now().isoformat(),
            "resolution_criteria": resolution,
            "comparison_type": comparison,
            "target_width": self.target_width,
            "target_height": self.target_height,
            "total_files": 0,
            "processed_files": 0,
            "error_files": 0,
            "matching_files": [],
            "errors": [],
        }

    def _parse_resolution(
        self, resolution: str
    ) -> Tuple[Optional[int], Optional[int]]:
        """
        Parse resolution string into width and height.
        Supports formats like: 360p, 360, 1920x1080, 1280x720
        """
        resolution = resolution.strip().lower()

        # Check for WxH format (e.g., 1920x1080)
        if "x" in resolution:
            try:
                width_str, height_str = resolution.split("x")
                width = int(width_str.strip())
                height = int(height_str.strip())
                return width, height
            except ValueError:
                raise ValueError(f"Invalid resolution format: {resolution}")

        # Check for height-only format (e.g., 360p or 360)
        height_match = re.match(r"^(\d+)p?$", resolution)
        if height_match:
            height = int(height_match.group(1))
            return None, height  # Width is None for height-only comparisons

        raise ValueError(f"Invalid resolution format: {resolution}")

    def get_video_info(self, file_path: Path) -> Optional[Dict]:
        """
        Extract video metadata using ffprobe.
        Returns dict with width, height, duration, and other metadata.
        """
        try:
            probe = ffmpeg.probe(str(file_path), select_streams="v:0")

            if not probe.get("streams"):
                logger.warning(f"No video streams found in {file_path}")
                return None

            stream = probe["streams"][0]

            # Extract frame rate as a decimal value
            fps = None
            if "r_frame_rate" in stream:
                fps_str = stream["r_frame_rate"]
                if "/" in fps_str:
                    try:
                        numerator, denominator = map(int, fps_str.split("/"))
                        fps = numerator / denominator
                    except (ValueError, ZeroDivisionError):
                        fps = fps_str  # Keep original if parsing fails
                else:
                    fps = fps_str  # Keep original if no division

            return {
                "width": stream.get("width"),
                "height": stream.get("height"),
                "duration": stream.get("duration"),
                "codec": stream.get("codec_name"),
                "bitrate": stream.get("bit_rate"),
                "fps": fps,
            }
        except ffmpeg.Error as e:
            logger.error(f"ffmpeg error processing {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
            return None

    def matches_criteria(self, video_info: Dict) -> bool:
        """
        Determine if video matches the resolution criteria.
        """
        video_width = video_info.get("width")
        video_height = video_info.get("height")

        if video_width is None or video_height is None:
            return False

        # If we have both target width and height (WxH format)
        if self.target_width is not None and self.target_height is not None:
            if self.comparison == "eq":
                return (
                    video_width == self.target_width
                    and video_height == self.target_height
                )
            elif self.comparison == "lte":
                return (
                    video_width <= self.target_width
                    and video_height <= self.target_height
                )
            elif self.comparison == "gte":
                return (
                    video_width >= self.target_width
                    and video_height >= self.target_height
                )

        # If we only have target height (height-only format like 360p)
        elif self.target_height is not None:
            if self.comparison == "eq":
                # For height-only, allow some tolerance for encoding variations
                return abs(video_height - self.target_height) <= 10
            elif self.comparison == "lte":
                return video_height <= self.target_height
            elif self.comparison == "gte":
                return video_height >= self.target_height

        return False

    def find_mp4_files(self) -> List[Path]:
        """Recursively find all .mp4 files in the source directory."""
        mp4_files = []

        try:
            for file_path in self.src_dir.rglob("*.mp4"):
                if file_path.is_file():
                    mp4_files.append(file_path)
        except Exception as e:
            logger.error(f"Error scanning directory {self.src_dir}: {str(e)}")

        return mp4_files

    def get_relative_path(self, file_path: Path) -> str:
        """Get path relative to source directory."""
        try:
            return str(file_path.relative_to(self.src_dir))
        except ValueError:
            return str(file_path)

    def process_file(self, file_path: Path) -> None:
        """Process a single video file."""
        relative_path = self.get_relative_path(file_path)

        try:
            # Get file size for logging
            file_size = file_path.stat().st_size

            # Extract video metadata
            video_info = self.get_video_info(file_path)

            if video_info is None:
                self.results["errors"].append(
                    {
                        "file": relative_path,
                        "error": "Failed to extract video metadata",
                    }
                )
                self.results["error_files"] += 1
                return

            # Check if it matches criteria
            if self.matches_criteria(video_info):
                self.results["matching_files"].append(
                    {
                        "file": relative_path,
                        "width": video_info["width"],
                        "height": video_info["height"],
                        "duration": video_info.get("duration"),
                        "codec": video_info.get("codec"),
                        "size_bytes": file_size,
                    }
                )

                comparison_symbol = {"eq": "==", "lte": "<=", "gte": ">="}.get(
                    self.comparison, "=="
                )

                logger.info(
                    f"Found matching video: {relative_path} "
                    f"({video_info['width']}x{video_info['height']}"
                    f" {comparison_symbol} {self.resolution})"
                )

            self.results["processed_files"] += 1

        except Exception as e:
            error_msg = f"Error processing file: {str(e)}"
            self.results["errors"].append(
                {"file": relative_path, "error": error_msg}
            )
            self.results["error_files"] += 1
            logger.error(f"Error processing {relative_path}: {error_msg}")

    def _get_filename_suffix(self) -> str:
        """Generate filename suffix based on criteria."""
        comparison_map = {"eq": "eq", "lte": "lte", "gte": "gte"}

        comparison_suffix = comparison_map.get(self.comparison, "eq")
        resolution_clean = self.resolution.replace("x", "x").replace("p", "p")

        return f"{comparison_suffix}_{resolution_clean}"

    def write_results(self) -> None:
        """Write results to log files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_suffix = self._get_filename_suffix()

        # Write simple text log
        text_log_path = (
            self.log_dir / f"video_scan_{filename_suffix}_{timestamp}.txt"
        )
        with open(text_log_path, "w") as f:
            comparison_symbol = {"eq": "==", "lte": "<=", "gte": ">="}.get(
                self.comparison, "=="
            )

            f.write("Video Resolution Scan Results\n")
            f.write(f"Scan Time: {self.results['scan_timestamp']}\n")
            f.write(
                f"Resolution Criteria: {comparison_symbol} {self.resolution}\n"
            )
            f.write(f"Total Files Found: {self.results['total_files']}\n")
            f.write(
                f"Successfully Processed: {self.results['processed_files']}\n"
            )
            f.write(f"Errors: {self.results['error_files']}\n")
            f.write(
                f"Matching Videos Found:"
                f"{len(self.results['matching_files'])}\n"
            )
            f.write(f"{'-' * 50}\n\n")

            if self.results["matching_files"]:
                f.write(
                    f"Videos matching {comparison_symbol} {self.resolution}:\n"
                )
                for video in self.results["matching_files"]:
                    f.write(
                        f"\t{video['file']} "
                        f"({video['width']}x{video['height']})\n"
                    )
                f.write("\n")

            if self.results["errors"]:
                f.write("Errors:\n")
                for error in self.results["errors"]:
                    f.write(f"  {error['file']}: {error['error']}\n")

        # Write detailed JSON log
        json_log_path = (
            self.log_dir / f"video_scan_{filename_suffix}_{timestamp}.json"
        )
        with open(json_log_path, "w") as f:
            json.dump(self.results, f, indent=2)

        logger.info(f"Results written to {text_log_path} and {json_log_path}")

    def _check_ffmpeg_available(self) -> bool:
        """Check if ffmpeg/ffprobe is available."""
        try:
            # Try to get ffmpeg version using ffmpeg-python
            ffmpeg.probe("nonexistent_file.mp4")
            return True
        except ffmpeg.Error:
            """
            This is expected for a non-existent file,
            but it means ffprobe is working
            """
            return True
        except FileNotFoundError:
            return False
        except Exception:
            """
            Any other exception likely means ffprobe
            is available but there's another issue
            """
            return True

    def run(self) -> None:
        """Main execution method."""
        comparison_symbol = {"eq": "==", "lte": "<=", "gte": ">="}.get(
            self.comparison, "=="
        )

        logger.info(f"Starting video scan in {self.src_dir}")
        logger.info(
            f"Looking for videos with resolution "
            f"{comparison_symbol} {self.resolution}"
        )

        # Check if ffmpeg is available
        if not self._check_ffmpeg_available():
            logger.error("ffmpeg/ffprobe not found. Please install ffmpeg.")
            return

        # Find all MP4 files
        mp4_files = self.find_mp4_files()
        self.results["total_files"] = len(mp4_files)

        if not mp4_files:
            logger.warning(f"No .mp4 files found in {self.src_dir}")
            self.write_results()
            return

        logger.info(f"Found {len(mp4_files)} .mp4 files to process")

        # Process each file
        for i, file_path in enumerate(mp4_files, 1):
            logger.info(
                f"Processing {i}/{len(mp4_files)}: "
                f"{self.get_relative_path(file_path)}"
            )
            self.process_file(file_path)

        # Write results
        self.write_results()

        # Summary
        logger.info("Scan complete!")
        logger.info(f"Total files: {self.results['total_files']}")
        logger.info(f"Processed: {self.results['processed_files']}")
        logger.info(f"Errors: {self.results['error_files']}")
        logger.info(
            f"Matching videos found: {len(self.results['matching_files'])}"
        )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Detect videos by resolution criteria"
    )

    parser.add_argument(
        "--resolution",
        "-r",
        default=os.environ.get("RESOLUTION", "360p"),
        help="Target resolution (e.g., 360p, 360, 1920x1080, 1280x720). Can be set via RESOLUTION env var.",  # noqa: E501
    )

    parser.add_argument(
        "--comparison",
        "-c",
        choices=["eq", "lte", "gte"],
        default=os.environ.get("COMPARISON", "eq"),
        help="Comparison type: eq (equal), lte (less than or equal), gte (greater than or equal). Can be set via COMPARISON env var.",  # noqa: E501
    )

    parser.add_argument(
        "--src-dir",
        "-s",
        default=os.environ.get("SRC_DIR", "/src"),
        help="Source directory to scan (default: /src). Can be set via SRC_DIR env var.",  # noqa: E501
    )

    parser.add_argument(
        "--log-dir",
        "-l",
        default=os.environ.get("LOG_DIR", "/log"),
        help="Log output directory (default: /log). Can be set via LOG_DIR env var.",  # noqa: E501
    )

    args = parser.parse_args()

    # Validate environment variable for comparison if set
    if args.comparison not in ["eq", "lte", "gte"]:
        logger.error(
            f"Invalid comparison type: {args.comparison}. Must be one of: eq, lte, gte"  # noqa: E501
        )
        return 1

    try:
        analyzer = VideoAnalyzer(
            src_dir=args.src_dir,
            log_dir=args.log_dir,
            resolution=args.resolution,
            comparison=args.comparison,
        )
        analyzer.run()
    except ValueError as e:
        logger.error(f"Invalid configuration: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
