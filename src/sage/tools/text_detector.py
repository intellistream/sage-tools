"""
Text Detector — EasyOCR-based text detection in images.

Requires ``torch`` and ``easyocr``  (optional extra ``isage-tools[vision]``).
"""

import os
import time

from sage.libs.foundation.tools.tool import BaseTool

# Lazy import: torch is an optional heavy dependency (isage-tools[vision]).
# The module will import cleanly without torch; errors only surface at execute().
try:
    import torch as _torch

    _HAS_TORCH = True
except ImportError:
    _torch = None  # type: ignore[assignment]
    _HAS_TORCH = False


class TextDetector(BaseTool):
    """Detect text in images using EasyOCR."""

    def __init__(self):
        super().__init__(
            tool_name="text_detector",
            tool_description="A tool that detects text in an image using EasyOCR.",
            input_types={
                "image": "str - The path to the image file.",
                "languages": "list - A list of language codes for the OCR model.",
                "detail": "int - The level of detail in the output. Set to 0 for simpler output, 1 for detailed output.",
            },
            output_type="list - A list of detected text blocks.",
            demo_commands=[
                {
                    "command": 'execution = tool.execute(image="path/to/image.png", languages=["en"])',
                    "description": "Detect text in an image using the default language (English).",
                },
                {
                    "command": 'execution = tool.execute(image="path/to/image.png", languages=["en", "de"])',
                    "description": "Detect text in an image using multiple languages (English and German).",
                },
                {
                    "command": 'execution = tool.execute(image="path/to/image.png", languages=["en"], detail=0)',
                    "description": "Detect text in an image with simpler output (text without coordinates and scores).",
                },
            ],
        )
        self.tool_version = "1.0.0"
        self.frequently_used_language = {
            "ch_sim": "Simplified Chinese",
            "ch_tra": "Traditional Chinese",
            "de": "German",
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "hi": "Hindi",
            "ja": "Japanese",
        }

    def build_tool(self, languages=None):
        """Build and return the EasyOCR reader model.

        Parameters:
            languages (list): A list of language codes for the OCR model.

        Returns:
            easyocr.Reader: An initialized EasyOCR Reader object.
        """
        languages = languages or ["en"]
        try:
            import easyocr

            reader = easyocr.Reader(languages)
            return reader
        except ImportError:
            raise ImportError(
                "Please install the EasyOCR package: pip install easyocr  "
                "or: pip install 'isage-tools[vision]'"
            ) from None
        except Exception as e:
            print(f"Error building the OCR tool: {e}")
            return None

    def execute(
        self,
        image,
        languages=None,
        max_retries=10,
        retry_delay=5,
        clear_cuda_cache=False,
        **kwargs,
    ):
        """Execute the OCR tool to detect text in the provided image.

        Parameters:
            image (str): The path to the image file.
            languages (list): A list of language codes for the OCR model.
            max_retries (int): Maximum number of retry attempts.
            retry_delay (int): Delay in seconds between retry attempts.
            clear_cuda_cache (bool): Whether to clear CUDA cache on OOM errors.

        Returns:
            list: A list of detected text blocks.
        """
        languages = languages or ["en"]

        for attempt in range(max_retries):
            try:
                reader = self.build_tool(languages)
                if reader is None:
                    raise ValueError("Failed to build the OCR tool.")

                result = reader.readtext(image, **kwargs)
                try:
                    # detail=1: Convert numpy types to standard Python types
                    from typing import Any, cast

                    cleaned_result = [
                        (
                            [[int(coord[0]), int(coord[1])] for coord in cast(Any, item)[0]],
                            cast(Any, item)[1],
                            round(float(cast(Any, item)[2]), 2),
                        )
                        for item in result
                    ]
                    return cleaned_result
                except Exception:
                    # detail=0 path
                    return result

            except RuntimeError as e:
                if "CUDA out of memory" in str(e):
                    print(f"CUDA out of memory error on attempt {attempt + 1}.")
                    if clear_cuda_cache and _HAS_TORCH:
                        print("Clearing CUDA cache and retrying...")
                        _torch.cuda.empty_cache()
                    else:
                        print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                else:
                    print(f"Runtime error: {e}")
                    break
            except Exception as e:
                print(f"Error detecting text: {e}")
                break

        print(f"Failed to detect text after {max_retries} attempts.")
        return []

    def get_metadata(self):
        metadata = super().get_metadata()
        return metadata


# Backward-compat alias (original name was lowercase class `text_detector`)
text_detector = TextDetector


if __name__ == "__main__":
    import json

    script_dir = os.path.dirname(os.path.abspath(__file__))
    tool = TextDetector()
    metadata = tool.get_metadata()
    print(metadata)

    relative_image_path = "examples/english.png"
    image_path = os.path.join(script_dir, relative_image_path)

    if not os.path.exists(image_path):
        print(f"Image file not found: {image_path}")
        exit(1)

    try:
        execution = tool.execute(image=image_path, languages=["en"])
        print(json.dumps(execution))
        print("Detected Text:", execution)
    except ValueError as e:
        print(f"Execution failed: {e}")

    print("Done!")
