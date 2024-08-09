# Owner(s): ["module: inductor"]

import unittest

import torch
from torch._dynamo.utils import counters
from torch._inductor.runtime.benchmarking import Benchmarker
from torch._inductor.test_case import run_tests, TestCase
from torch.testing._internal.common_utils import (
    instantiate_parametrized_tests,
    parametrize,
)
from torch.testing._internal.inductor_utils import GPU_TYPE, HAS_CPU, HAS_GPU


class TestBase(TestCase):
    def setUp(self):
        super().setUp()
        torch.manual_seed(12345)
        counters.clear()

    def counter_value(self, fn_name):
        return counters["inductor"][
            f"benchmarking.{type(self.benchmarker).__name__}.{fn_name}"
        ]

    def make_sum(self, device, size=100):
        fn, args, kwargs = torch.sum, (torch.randn(size, device=device),), {}
        _callable = lambda: fn(*args, **kwargs)  # noqa: E731
        return (fn, args, kwargs), _callable


@instantiate_parametrized_tests
class TestBenchmarker(TestBase):
    @property
    def benchmarker(self):
        return Benchmarker()

    @unittest.skipIf(not HAS_CPU or not HAS_GPU, "requires CPU and GPU")
    @parametrize("device", (GPU_TYPE, "cpu"))
    def test_benchmark(self, device):
        benchmarker = self.benchmarker
        (fn, args, kwargs), _ = self.make_sum(device)
        if device == "cpu":
            _ = benchmarker.benchmark(fn, args, kwargs)
            self.assertEqual(self.counter_value("benchmark"), 1)
            self.assertEqual(self.counter_value("benchmark_cpu"), 1)
        else:
            try:
                _ = benchmarker.benchmark(fn, args, kwargs)
            except NotImplementedError:
                self.assertEqual(self.counter_value("benchmark"), 1)
                self.assertEqual(self.counter_value("benchmark_gpu"), 1)

    @unittest.skipIf(not HAS_CPU, "requires CPU")
    def test_benchmark_cpu(self, device="cpu"):
        benchmarker = self.benchmarker
        _, _callable = self.make_sum(device)
        _ = benchmarker.benchmark_cpu(_callable)
        self.assertEqual(self.counter_value("benchmark_cpu"), 1)

    @unittest.skipIf(not HAS_GPU, "requires GPU")
    def test_benchmark_gpu(self, device=GPU_TYPE):
        benchmarker = self.benchmarker
        _, _callable = self.make_sum(device)
        try:
            _ = benchmarker.benchmark_gpu(_callable)
        except NotImplementedError:
            self.assertEqual(self.counter_value("benchmark_gpu"), 1)


if __name__ == "__main__":
    run_tests()
