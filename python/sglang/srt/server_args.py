"""
Copyright 2023-2024 SGLang Team
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

"""The arguments of the server."""

import argparse
import dataclasses
import random
from typing import List, Optional, Union


@dataclasses.dataclass
class ServerArgs:
    # Model and tokenizer
    model_path: str
    tokenizer_path: Optional[str] = None
    tokenizer_mode: str = "auto"
    load_format: str = "auto"
    dtype: str = "auto"
    trust_remote_code: bool = True
    context_length: Optional[int] = None
    quantization: Optional[str] = None
    chat_template: Optional[str] = None

    # Port
    host: str = "127.0.0.1"
    port: int = 30000
    additional_ports: Optional[Union[List[int], int]] = None

    # Memory and scheduling
    mem_fraction_static: Optional[float] = None
    max_prefill_tokens: Optional[int] = None
    max_running_requests: Optional[int] = None
    max_num_reqs: Optional[int] = None
    schedule_heuristic: str = "lpm"
    schedule_conservativeness: float = 1.0

    # Other runtime options
    tp_size: int = 1
    stream_interval: int = 1
    random_seed: Optional[int] = None

    # Logging
    log_level: str = "info"
    log_level_http: Optional[str] = None
    log_requests: bool = False
    show_time_cost: bool = False

    # Other
    api_key: str = ""

    # Data parallelism
    dp_size: int = 1
    load_balance_method: str = "round_robin"

    # Optimization/debug options
    disable_flashinfer: bool = False
    disable_flashinfer_sampling: bool = False
    disable_radix_cache: bool = False
    disable_regex_jump_forward: bool = False
    disable_cuda_graph: bool = False
    disable_disk_cache: bool = False
    enable_torch_compile: bool = False
    enable_p2p_check: bool = False
    attention_reduce_in_fp32: bool = False
    efficient_weight_load: bool = False

    # Distributed args
    nccl_init_addr: Optional[str] = None
    nnodes: int = 1
    node_rank: Optional[int] = None

    def __post_init__(self):
        if self.tokenizer_path is None:
            self.tokenizer_path = self.model_path
        if self.mem_fraction_static is None:
            if self.tp_size >= 16:
                self.mem_fraction_static = 0.80
            elif self.tp_size >= 8:
                self.mem_fraction_static = 0.84
            elif self.tp_size >= 4:
                self.mem_fraction_static = 0.86
            elif self.tp_size >= 2:
                self.mem_fraction_static = 0.88
            else:
                self.mem_fraction_static = 0.89
        if isinstance(self.additional_ports, int):
            self.additional_ports = [self.additional_ports]
        elif self.additional_ports is None:
            self.additional_ports = []

        if self.random_seed is None:
            self.random_seed = random.randint(0, 1 << 30)

    @staticmethod
    def add_cli_args(parser: argparse.ArgumentParser):
        parser.add_argument(
            "--model-path",
            type=str,
            help="The path of the model weights. This can be a local folder or a Hugging Face repo ID.",
            required=True,
        )
        parser.add_argument(
            "--tokenizer-path",
            type=str,
            default=ServerArgs.tokenizer_path,
            help="The path of the tokenizer.",
        )
        parser.add_argument(
            "--host", type=str, default=ServerArgs.host, help="The host of the server."
        )
        parser.add_argument(
            "--port", type=int, default=ServerArgs.port, help="The port of the server."
        )
        parser.add_argument(
            "--additional-ports",
            type=int,
            nargs="*",
            default=[],
            help="The additional ports specified for the server.",
        )
        parser.add_argument(
            "--tokenizer-mode",
            type=str,
            default=ServerArgs.tokenizer_mode,
            choices=["auto", "slow"],
            help="Tokenizer mode. 'auto' will use the fast "
            "tokenizer if available, and 'slow' will "
            "always use the slow tokenizer.",
        )
        parser.add_argument(
            "--load-format",
            type=str,
            default=ServerArgs.load_format,
            choices=["auto", "pt", "safetensors", "npcache", "dummy"],
            help="The format of the model weights to load. "
            '"auto" will try to load the weights in the safetensors format '
            "and fall back to the pytorch bin format if safetensors format "
            "is not available. "
            '"pt" will load the weights in the pytorch bin format. '
            '"safetensors" will load the weights in the safetensors format. '
            '"npcache" will load the weights in pytorch format and store '
            "a numpy cache to speed up the loading. "
            '"dummy" will initialize the weights with random values, '
            "which is mainly for profiling.",
        )
        parser.add_argument(
            "--dtype",
            type=str,
            default=ServerArgs.dtype,
            choices=["auto", "half", "float16", "bfloat16", "float", "float32"],
            help="Data type for model weights and activations.\n\n"
            '* "auto" will use FP16 precision for FP32 and FP16 models, and '
            "BF16 precision for BF16 models.\n"
            '* "half" for FP16. Recommended for AWQ quantization.\n'
            '* "float16" is the same as "half".\n'
            '* "bfloat16" for a balance between precision and range.\n'
            '* "float" is shorthand for FP32 precision.\n'
            '* "float32" for FP32 precision.',
        )
        parser.add_argument(
            "--trust-remote-code",
            action="store_true",
            help="Whether or not to allow for custom models defined on the Hub in their own modeling files.",
        )
        parser.add_argument(
            "--context-length",
            type=int,
            default=ServerArgs.context_length,
            help="The model's maximum context length. Defaults to None (will use the value from the model's config.json instead).",
        )
        parser.add_argument(
            "--quantization",
            type=str,
            default=ServerArgs.quantization,
            choices=[
                "awq",
                "fp8",
                "gptq",
                "marlin",
                "gptq_marlin",
                "squeezellm",
                "bitsandbytes",
            ],
            help="The quantization method.",
        )
        parser.add_argument(
            "--chat-template",
            type=str,
            default=ServerArgs.chat_template,
            help="The buliltin chat template name or the path of the chat template file. This is only used for OpenAI-compatible API server.",
        )
        parser.add_argument(
            "--mem-fraction-static",
            type=float,
            default=ServerArgs.mem_fraction_static,
            help="The fraction of the memory used for static allocation (model weights and KV cache memory pool). Use a smaller value if you see out-of-memory errors.",
        )
        parser.add_argument(
            "--max-prefill-tokens",
            type=int,
            default=ServerArgs.max_prefill_tokens,
            help="The maximum number of tokens in a prefill batch. The real bound will be the maximum of this value and the model's maximum context length.",
        )
        parser.add_argument(
            "--max-running-requests",
            type=int,
            default=ServerArgs.max_running_requests,
            help="The maximum number of running requests.",
        )
        parser.add_argument(
            "--max-num-reqs",
            type=int,
            default=None,
            help="The maximum number of requests to serve in the memory pool. If the model have a large context length, you may need to decrease this value to avoid out-of-memory errors.",
        )
        parser.add_argument(
            "--schedule-heuristic",
            type=str,
            default=ServerArgs.schedule_heuristic,
            choices=["lpm", "random", "fcfs", "dfs-weight"],
            help="The scheduling heuristic.",
        )
        parser.add_argument(
            "--schedule-conservativeness",
            type=float,
            default=ServerArgs.schedule_conservativeness,
            help="How conservative the schedule policy is. A larger value means more conservative scheduling. Use a larger value if you see requests being retracted frequently.",
        )
        parser.add_argument(
            "--tp-size",
            type=int,
            default=ServerArgs.tp_size,
            help="The tensor parallelism size.",
        )
        parser.add_argument(
            "--stream-interval",
            type=int,
            default=ServerArgs.stream_interval,
            help="The interval (or buffer size) for streaming in terms of the token length. A smaller value makes streaming smoother, while a larger value makes the throughput higher",
        )
        parser.add_argument(
            "--random-seed",
            type=int,
            default=ServerArgs.random_seed,
            help="The random seed.",
        )
        parser.add_argument(
            "--log-level",
            type=str,
            default=ServerArgs.log_level,
            help="The logging level of all loggers.",
        )
        parser.add_argument(
            "--log-level-http",
            type=str,
            default=ServerArgs.log_level_http,
            help="The logging level of HTTP server. If not set, reuse --log-level by default.",
        )
        parser.add_argument(
            "--log-requests",
            action="store_true",
            help="Log the inputs and outputs of all requests.",
        )
        parser.add_argument(
            "--show-time-cost",
            action="store_true",
            help="Show time cost of custom marks.",
        )
        parser.add_argument(
            "--api-key",
            type=str,
            default=ServerArgs.api_key,
            help="Set API key of the server.",
        )

        # Data parallelism
        parser.add_argument(
            "--dp-size",
            type=int,
            default=ServerArgs.dp_size,
            help="The data parallelism size.",
        )
        parser.add_argument(
            "--load-balance-method",
            type=str,
            default=ServerArgs.load_balance_method,
            help="The load balancing strategy for data parallelism.",
            choices=[
                "round_robin",
                "shortest_queue",
            ],
        )

        # Multi-node distributed serving args
        parser.add_argument(
            "--nccl-init-addr",
            type=str,
            help="The nccl init address of multi-node server.",
        )
        parser.add_argument(
            "--nnodes", type=int, default=1, help="The number of nodes."
        )
        parser.add_argument("--node-rank", type=int, help="The node rank.")

        # Optimization/debug options
        parser.add_argument(
            "--disable-flashinfer",
            action="store_true",
            help="Disable flashinfer attention kernels.",
        )
        parser.add_argument(
            "--disable-flashinfer-sampling",
            action="store_true",
            help="Disable flashinfer sampling kernels.",
        )
        parser.add_argument(
            "--disable-radix-cache",
            action="store_true",
            help="Disable RadixAttention for prefix caching.",
        )
        parser.add_argument(
            "--disable-regex-jump-forward",
            action="store_true",
            help="Disable regex jump-forward.",
        )
        parser.add_argument(
            "--disable-cuda-graph",
            action="store_true",
            help="Disable cuda graph.",
        )
        parser.add_argument(
            "--disable-disk-cache",
            action="store_true",
            help="Disable disk cache to avoid possible crashes related to file system or high concurrency.",
        )
        parser.add_argument(
            "--enable-torch-compile",
            action="store_true",
            help="Optimize the model with torch.compile, experimental feature.",
        )
        parser.add_argument(
            "--enable-p2p-check",
            action="store_true",
            help="Enable P2P check for GPU access, otherwise the p2p access is allowed by default.",
        )
        parser.add_argument(
            "--attention-reduce-in-fp32",
            action="store_true",
            help="Cast the intermidiate attention results to fp32 to avoid possible crashes related to fp16."
            "This only affects Triton attention kernels",
        )
        parser.add_argument(
            "--efficient-weight-load",
            action="store_true",
            help="Turn on memory efficient weight loading with quantization (quantize per layer during loading).",
        )

    @classmethod
    def from_cli_args(cls, args: argparse.Namespace):
        attrs = [attr.name for attr in dataclasses.fields(cls)]
        return cls(**{attr: getattr(args, attr) for attr in attrs})

    def url(self):
        return f"http://{self.host}:{self.port}"

    def print_mode_args(self):
        return (
            f"disable_flashinfer={self.disable_flashinfer}, "
            f"attention_reduce_in_fp32={self.attention_reduce_in_fp32}, "
            f"disable_radix_cache={self.disable_radix_cache}, "
            f"disable_regex_jump_forward={self.disable_regex_jump_forward}, "
            f"disable_disk_cache={self.disable_disk_cache}, "
        )

    def check_server_args(self):
        assert (
            self.tp_size % self.nnodes == 0
        ), "tp_size must be divisible by number of nodes"
        assert not (
            self.dp_size > 1 and self.node_rank is not None
        ), "multi-node data parallel is not supported"


@dataclasses.dataclass
class PortArgs:
    tokenizer_port: int
    controller_port: int
    detokenizer_port: int
    nccl_ports: List[int]
