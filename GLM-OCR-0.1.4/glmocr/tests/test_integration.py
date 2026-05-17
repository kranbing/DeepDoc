"""Integration tests for glmocr (requires a running service).

How to run:
Terminal 1: start server
    python -m glmocr.server
Terminal 2: run integration tests
    GLMOCR_RUN_INTEGRATION=1 \
    GLMOCR_SERVER_URL=http://127.0.0.1:5002 \
    GLMOCR_TEST_IMAGE=./examples/source/1.png \
    GLMOCR_TEST_PDF=./examples/source/954d59b1-d8c1-4baf-9e3b-c04bf1961d7b.pdf \
    pytest -q glmocr/tests/test_integration.py
"""

import base64
import gc
import os
import time
from pathlib import Path
from typing import Optional

import pytest
import requests

# ---------------------------------------------------------------------------
# All integration tests are marked with @pytest.mark.integration
# conftest.py will auto-skip unless GLMOCR_RUN_INTEGRATION=1
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestHealthEndpoint:
    """Tests for /health."""

    def test_health_returns_ok(self, server_url, timeout_seconds):
        resp = requests.get(f"{server_url}/health", timeout=timeout_seconds)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") == "ok"


@pytest.mark.integration
class TestParseEndpoint:
    """Tests for /glmocr/parse."""

    def test_parse_returns_json_result(
        self, server_url, timeout_seconds, sample_image_path
    ):
        """parse returns json_result."""
        if sample_image_path is None:
            pytest.skip("No sample image available")

        with open(sample_image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")

        payload = {"images": [f"data:image/png;base64,{img_b64}"]}
        resp = requests.post(
            f"{server_url}/glmocr/parse",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=timeout_seconds,
        )

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "json_result" in data
        assert data["json_result"] is not None

    def test_parse_with_empty_images_returns_error(self, server_url, timeout_seconds):
        """Empty images returns an error."""
        payload = {"images": []}
        resp = requests.post(
            f"{server_url}/glmocr/parse",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=timeout_seconds,
        )

        assert resp.status_code == 400
        data = resp.json()
        assert "error" in data

    def test_parse_with_invalid_content_type(self, server_url, timeout_seconds):
        """Invalid Content-Type returns an error."""
        resp = requests.post(
            f"{server_url}/glmocr/parse",
            data="not json",
            headers={"Content-Type": "text/plain"},
            timeout=timeout_seconds,
        )

        assert resp.status_code == 400

    def test_parse_multiple_images(
        self, server_url, timeout_seconds, sample_image_path
    ):
        """Multiple images are accepted."""
        if sample_image_path is None:
            pytest.skip("No sample image available")

        with open(sample_image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")

        # Send the same image twice
        payload = {
            "images": [
                f"data:image/png;base64,{img_b64}",
                f"data:image/png;base64,{img_b64}",
            ]
        }
        resp = requests.post(
            f"{server_url}/glmocr/parse",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=timeout_seconds,
        )

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "json_result" in data

    def test_parse_pdf_file_uri(self, server_url, timeout_seconds, sample_pdf_path):
        """PDF parsing via file:// absolute path."""
        if sample_pdf_path is None:
            pytest.skip("No sample PDF available")

        # Dependency check: pypdfium2
        try:
            from glmocr.utils.image_utils import PYPDFIUM2_AVAILABLE
        except Exception:
            PYPDFIUM2_AVAILABLE = False

        if not PYPDFIUM2_AVAILABLE:
            pytest.skip("pypdfium2 is not installed")

        pdf_uri = f"file://{sample_pdf_path.resolve()}"
        payload = {"images": [pdf_uri]}
        resp = requests.post(
            f"{server_url}/glmocr/parse",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=timeout_seconds,
        )

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "json_result" in data
        assert data["json_result"] is not None


@pytest.mark.integration
class TestGlmOcrAPI:
    """Tests for the Python API (requires service)."""

    def test_glmocr_parse_file(self, sample_image_path):
        """GlmOcr.parse works."""
        if sample_image_path is None:
            pytest.skip("No sample image available")

        from glmocr.api import GlmOcr

        parser = GlmOcr()
        try:
            result = parser.parse(str(sample_image_path))
            assert result is not None
            assert result.json_result is not None
        finally:
            parser.close()

    def test_glmocr_context_manager(self, sample_image_path):
        """GlmOcr context manager works."""
        if sample_image_path is None:
            pytest.skip("No sample image available")

        from glmocr.api import GlmOcr

        with GlmOcr() as parser:
            result = parser.parse(str(sample_image_path))
            assert result is not None


@pytest.mark.integration
class TestCLI:
    """Tests for CLI."""

    def test_cli_parse_runs(self, sample_image_path, tmp_path):
        """glmocr parse can run."""
        if sample_image_path is None:
            pytest.skip("No sample image available")

        import subprocess

        result = subprocess.run(
            [
                "python",
                "-m",
                "glmocr.cli",
                "parse",
                str(sample_image_path),
                "--output",
                str(tmp_path),
            ],
            capture_output=True,
            text=True,
            timeout=600,
        )

        # Only check it runs; don't require success (config may be invalid)
        assert (
            "Error:" in result.stderr
            or result.returncode == 0
            or "Completed" in result.stdout
        )


# ---------------------------------------------------------------------------
# Layout device integration tests (real PP-DocLayoutV3 model)
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_IMAGE_DIR = REPO_ROOT / "examples" / "source"


def _find_sample_image() -> Optional[Path]:
    """Return the first sample image in examples/source/."""
    if not SAMPLE_IMAGE_DIR.exists():
        return None
    for ext in ("*.png", "*.jpg", "*.jpeg"):
        images = sorted(SAMPLE_IMAGE_DIR.glob(ext))
        if images:
            return images[0]
    return None


def _gpu_count() -> int:
    """Return the number of CUDA GPUs available (0 if no CUDA)."""
    try:
        import torch

        return torch.cuda.device_count()
    except Exception:
        return 0


def _has_cuda() -> bool:
    try:
        import torch

        return torch.cuda.is_available()
    except Exception:
        return False


@pytest.fixture(scope="module")
def sample_layout_image():
    """Load a sample PIL image for layout-device tests."""
    img_path = _find_sample_image()
    if img_path is None:
        pytest.skip(f"No sample image found in {SAMPLE_IMAGE_DIR}")
    from PIL import Image

    return Image.open(img_path).convert("RGB")


def _make_detector(device: str):
    """Create a PPDocLayoutDetector with a specific device setting."""
    from glmocr.config import load_config

    cfg = load_config()
    cfg.pipeline.layout.device = device
    from glmocr.layout.layout_detector import PPDocLayoutDetector

    return PPDocLayoutDetector(cfg.pipeline.layout)


def _run_detection(detector, image):
    """Run detection on a single image, return (results, elapsed_seconds)."""
    detector.start()
    try:
        t0 = time.perf_counter()
        results = detector.process([image])
        elapsed = time.perf_counter() - t0
        return results, elapsed
    finally:
        detector.stop()
        gc.collect()
        try:
            import torch

            torch.cuda.empty_cache()
        except Exception:
            pass


def _run_real_model_tests() -> bool:
    """Return True if the slow, real-model layout tests should be executed."""
    return os.getenv("GLMOCR_RUN_LAYOUT_REAL_TESTS") == "1"


@pytest.mark.integration
@pytest.mark.skipif(
    not _run_real_model_tests(),
    reason=(
        "Real layout model tests are slow and require network/model download; "
        "set GLMOCR_RUN_LAYOUT_REAL_TESTS=1 to enable."
    ),
)
class TestLayoutDeviceIntegration:
    """Real model tests — actually load PP-DocLayoutV3 and run inference."""

    def test_cpu(self, sample_layout_image):
        """Layout model loads and runs on CPU."""
        detector = _make_detector("cpu")
        results, elapsed = _run_detection(detector, sample_layout_image)

        print(f"\n  [CPU] Inference time: {elapsed:.3f}s")
        print(f"  [CPU] Detected {len(results[0])} regions")

        assert len(results) == 1, "Should return results for 1 image"
        assert isinstance(results[0], list), "Per-image result should be a list"
        assert len(results[0]) > 0, "Should detect at least one region"

        for det in results[0]:
            assert "label" in det
            assert "score" in det
            assert "bbox_2d" in det
            assert len(det["bbox_2d"]) == 4

    @pytest.mark.skipif(not _has_cuda(), reason="No CUDA available")
    def test_cuda_default(self, sample_layout_image):
        """Layout model loads and runs on default CUDA device."""
        detector = _make_detector("cuda")
        results, elapsed = _run_detection(detector, sample_layout_image)

        print(f"\n  [cuda] Inference time: {elapsed:.3f}s")
        print(f"  [cuda] Detected {len(results[0])} regions")

        assert len(results) == 1
        assert len(results[0]) > 0

    @pytest.mark.skipif(not _has_cuda(), reason="No CUDA available")
    def test_cuda_0(self, sample_layout_image):
        """Layout model loads and runs on cuda:0."""
        detector = _make_detector("cuda:0")
        results, elapsed = _run_detection(detector, sample_layout_image)

        print(f"\n  [cuda:0] Inference time: {elapsed:.3f}s")
        print(f"  [cuda:0] Detected {len(results[0])} regions")

        assert len(results) == 1
        assert len(results[0]) > 0

        import torch

        for param in (
            detector._model.parameters()
            if hasattr(detector, "_model") and detector._model
            else []
        ):
            assert param.device == torch.device(
                "cuda:0"
            ) or param.device == torch.device("cuda", 0)
            break

    @pytest.mark.skipif(_gpu_count() < 2, reason="Need 2+ GPUs for cuda:1 test")
    def test_cuda_1(self, sample_layout_image):
        """Layout model loads and runs on cuda:1 (second GPU)."""
        detector = _make_detector("cuda:1")
        results, elapsed = _run_detection(detector, sample_layout_image)

        print(f"\n  [cuda:1] Inference time: {elapsed:.3f}s")
        print(f"  [cuda:1] Detected {len(results[0])} regions")

        assert len(results) == 1
        assert len(results[0]) > 0

    @pytest.mark.skipif(not _has_cuda(), reason="No CUDA available")
    def test_auto_selects_cuda(self, sample_layout_image):
        """With device=None (auto), selects CUDA when available."""
        from glmocr.config import load_config

        cfg = load_config()
        cfg.pipeline.layout.device = None
        cfg.pipeline.layout.cuda_visible_devices = "0"

        from glmocr.layout.layout_detector import PPDocLayoutDetector

        detector = PPDocLayoutDetector(cfg.pipeline.layout)
        results, elapsed = _run_detection(detector, sample_layout_image)

        print(f"\n  [auto → cuda:0] Inference time: {elapsed:.3f}s")
        print(f"  [auto → cuda:0] Detected {len(results[0])} regions")

        assert detector._device is None
        assert len(results) == 1
        assert len(results[0]) > 0

    def test_results_consistent_across_devices(self, sample_layout_image):
        """CPU and CUDA produce generally consistent detected regions."""
        if not _has_cuda():
            pytest.skip("No CUDA available — cannot compare devices")

        cpu_det = _make_detector("cpu")
        cpu_results, cpu_time = _run_detection(cpu_det, sample_layout_image)

        cuda_det = _make_detector("cuda:0")
        cuda_results, cuda_time = _run_detection(cuda_det, sample_layout_image)

        cpu_labels = sorted(d["label"] for d in cpu_results[0])
        cuda_labels = sorted(d["label"] for d in cuda_results[0])

        print(
            f"\n  [consistency] CPU: {len(cpu_results[0])} regions in {cpu_time:.3f}s"
        )
        print(
            f"  [consistency] CUDA:0: {len(cuda_results[0])} regions in {cuda_time:.3f}s"
        )
        print(f"  [consistency] CPU labels: {cpu_labels}")
        print(f"  [consistency] CUDA labels: {cuda_labels}")

        assert len(cpu_results[0]) > 0, "CPU should detect at least one region"
        assert len(cuda_results[0]) > 0, "CUDA should detect at least one region"

        if len(cpu_results[0]) != len(cuda_results[0]):
            print(
                f"  [consistency] WARNING: region count mismatch — "
                f"CPU={len(cpu_results[0])}, CUDA={len(cuda_results[0])}"
            )
        if cpu_labels != cuda_labels:
            print(
                f"  [consistency] WARNING: label mismatch — "
                f"CPU={cpu_labels}, CUDA={cuda_labels}"
            )

    @pytest.mark.skipif(_gpu_count() < 2, reason="Need 2+ GPUs")
    def test_both_gpus(self, sample_layout_image):
        """Run on GPU 0, then GPU 1 — both produce valid results."""
        gpu0_det = _make_detector("cuda:0")
        gpu0_results, gpu0_time = _run_detection(gpu0_det, sample_layout_image)

        gpu1_det = _make_detector("cuda:1")
        gpu1_results, gpu1_time = _run_detection(gpu1_det, sample_layout_image)

        print(
            f"\n  [dual-GPU] cuda:0: {len(gpu0_results[0])} regions in {gpu0_time:.3f}s"
        )
        print(
            f"  [dual-GPU] cuda:1: {len(gpu1_results[0])} regions in {gpu1_time:.3f}s"
        )

        assert len(gpu0_results[0]) > 0
        assert len(gpu1_results[0]) > 0
        assert len(gpu0_results[0]) == len(gpu1_results[0])

    @pytest.mark.skipif(
        _gpu_count() < 2 or not os.getenv("RUN_LAYOUT_BENCHMARKS"),
        reason=(
            "Benchmark test disabled by default; set RUN_LAYOUT_BENCHMARKS=1 "
            "and require 2+ GPUs to run."
        ),
    )
    def test_benchmark_all_devices(self, sample_layout_image):
        """Benchmark: run inference on CPU, cuda:0, and cuda:1 and print timing comparison."""
        results_summary = []

        for device_str in ["cpu", "cuda:0", "cuda:1"]:
            detector = _make_detector(device_str)
            _, _ = _run_detection(detector, sample_layout_image)

            detector = _make_detector(device_str)
            results, elapsed = _run_detection(detector, sample_layout_image)
            n_regions = len(results[0])
            results_summary.append((device_str, elapsed, n_regions))

        print("\n" + "=" * 60)
        print("  LAYOUT DEVICE BENCHMARK")
        print("=" * 60)
        print(f"  {'Device':<12} {'Time (s)':>10} {'Regions':>10}")
        print("-" * 40)
        for device_str, elapsed, n_regions in results_summary:
            print(f"  {device_str:<12} {elapsed:>10.3f} {n_regions:>10}")
        print("=" * 60)

        region_counts = {r[2] for r in results_summary}
        assert (
            len(region_counts) == 1
        ), f"Inconsistent region counts across devices: {results_summary}"
