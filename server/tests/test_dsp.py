import numpy as np

from vlf_stream.dsp import SpectralNLMS


def test_rejects_correlated_reference_noise() -> None:
    rng = np.random.default_rng(7)
    dsp = SpectralNLMS(
        sample_rate=48_000,
        hop_size=512,
        low_cut_hz=250,
        high_cut_hz=12_000,
        adapt_rate=0.045,
    )
    before = []
    after = []
    delay = np.zeros(9)
    for _ in range(420):
        reference = 0.08 * rng.normal(size=512)
        delayed = np.concatenate((delay, reference))[:512]
        delay = reference[-9:]
        desired = 0.003 * rng.normal(size=512)
        main = 0.72 * delayed + desired
        output = dsp.process(np.column_stack((main, reference)))
        before.append(np.mean(main**2))
        after.append(np.mean(output**2))

    input_power = float(np.mean(before[-80:]))
    output_power = float(np.mean(after[-80:]))
    assert output_power < input_power * 0.45


def test_rejects_wrong_shape() -> None:
    dsp = SpectralNLMS(hop_size=512)
    try:
        dsp.process(np.zeros((512, 1), dtype=np.float32))
    except ValueError:
        pass
    else:
        raise AssertionError("wrong channel count must be rejected")


def test_metric_does_not_credit_band_filtering() -> None:
    dsp = SpectralNLMS(sample_rate=48_000, hop_size=512, low_cut_hz=250, high_cut_hz=12_000)
    phase = 0
    for _ in range(400):
        index = np.arange(512) + phase
        phase += 512
        seconds = index / 48_000.0
        main = 0.5 * np.sin(2 * np.pi * 50 * seconds)
        dsp.process(np.column_stack((main, np.zeros(512))))

    assert dsp.metrics.cancellation_db < 1.0
    assert dsp.metrics.band_reject_db > 20.0
