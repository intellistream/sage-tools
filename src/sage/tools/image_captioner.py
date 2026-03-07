"""
Image Captioner — LLM-powered image captioning tool.

Requires ``isagellm`` (optional extra ``isage-tools[llm]``).
"""

import os
import time

from sage.libs.foundation.tools.tool import BaseTool

try:
    from isagellm import UnifiedInferenceClient  # type: ignore[import-untyped]
except ImportError:
    # Optional soft-dependency: isagellm not installed — ImageCaptioner will be
    # non-functional at runtime but the module still imports cleanly.
    #
    # TODO(SAGE↔SageLLM bridge): replace UnifiedInferenceClient usage below with
    # sage.libs.llm.OpenAICompatibleBackend + get_gateway_url() once
    # sagellm-gateway exposes a multimodal vision endpoint under the standard
    # SAGE LLM protocol (see sage.libs.llm.protocol / sage.libs.llm.gateway).
    # No cross-ecosystem Python coupling should remain after that migration.
    UnifiedInferenceClient = None  # type: ignore[assignment]


class ImageCaptioner(BaseTool):
    """Generate captions for images using a vision-capable LLM."""

    def __init__(self, model_name: str = "meta-llama/Llama-2-13b-chat-hf"):
        super().__init__(
            tool_name="image_captioner",
            tool_description="A tool that can generate captions for images.",
            input_types={
                "image_path": "The path to the image to caption",
                "prompt": "The prompt to generate the caption",
            },
            demo_commands=[
                {
                    "command": 'execution = tool.execute(image="path/to/image.png")',
                    "description": "Generate a caption for an image using the default prompt and model.",
                },
                {
                    "command": 'execution = tool.execute(image="path/to/image.png", prompt="A beautiful landscape")',
                    "description": "Generate a caption for an image using a custom prompt and model.",
                },
            ],
            require_llm_engine=True,
        )
        self.tool_version = "1.0.0"
        self.limitation = (
            "The ImageCaptioner provides general image descriptions but has limitations: "
            "1) May make mistakes in complex scenes, counting, attribute detection, "
            "and understanding object relationships. "
            "2) Might not generate comprehensive captions, especially for images with "
            "multiple objects or abstract concepts. "
            "3) Performance varies with image complexity. "
            "4) Struggles with culturally specific or domain-specific content. "
            "5) May overlook details or misinterpret object relationships."
        )
        self.model_name = model_name
        print(f"ImageCaptioner initialized with model: {model_name}")

    def execute(self, image_path: str):
        try:
            if not self.model_name:
                raise ValueError(
                    "Model name is not set. Please set the model name using set_model_name() before executing the tool."
                )

            messages = [
                {"role": "system", "content": "You are an image captioning assistant."},
                {
                    "role": "user",
                    "content": f"Generate a caption for the image at path: {image_path}",
                },
            ]

            client = UnifiedInferenceClient.create()

            max_retries = 5
            retry_delay = 3

            for attempt in range(max_retries):
                try:
                    response = client.chat(messages)
                    return response
                except ConnectionError as e:
                    print(f"Connection error on attempt {attempt + 1}: {e}")
                    if attempt < max_retries - 1:
                        print(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        raise
        except Exception as e:
            print(f"Error in ImageCaptioner: {e}")
            return None


if __name__ == "__main__":
    import json

    script_dir = os.path.dirname(os.path.abspath(__file__))
    tool = ImageCaptioner(model_name="meta-llama/Llama-2-13b-chat-hf")
    metadata = tool.get_metadata()
    print(metadata)

    relative_image_path = "examples/baseball.png"
    image_path = os.path.join(script_dir, relative_image_path)
    try:
        execution = tool.execute(image_path=image_path)
        print("Generated Caption:")
        print(json.dumps(execution, indent=4))
    except Exception as e:
        print(f"Execution failed: {e}")

    print("Done!")
