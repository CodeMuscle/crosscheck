"""Deterministic demo pack: dated benchmark claims with one planted contradiction."""

PRESET = [
    {
        "id": "srcA-2021",
        "timestamp": "2021-03-01",
        "text": "In our 2021 evaluation, FooDB sustained a throughput of 50,000 "
                "requests per second on a single node. FooDB is written in Rust "
                "and released under the MIT license.",
    },
    {
        "id": "srcB-2022",
        "timestamp": "2022-06-01",
        "text": "FooDB is written in Rust. Its query planner supports cost-based "
                "optimization. The project is MIT licensed.",
    },
    {
        "id": "srcD-2024",
        "timestamp": "2024-09-01",
        "text": "Independent 2024 benchmarks found FooDB sustained a throughput of "
                "only 10,000 requests per second on a single node under mixed load.",
    },
]
