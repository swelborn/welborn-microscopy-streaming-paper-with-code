from pathlib import Path

from pydantic import BaseModel


class Plot(BaseModel):
    blue_color: str
    red_color: str
    green_color: str
    label_font_size: int
    tick_font_size: int


class Microscope(BaseModel):
    r_pixel_size: float
    r_pixel_units: str
    convergence_semiangle: float
    q_pixel_units: str
    probe_current: int
    probe_current_units: str
    beam_energy: int
    beam_energy_units: str


class CropData(BaseModel):
    x_min: int
    x_max: int
    y_min: int
    y_max: int


class Experiment(BaseModel):
    num_scans: int
    seconds_between_scans: int
    min_scan_num: int
    max_scan_num: int
    data_base_path: Path


class Binning(BaseModel):
    bin_diffraction_factor: int


class Calibration(BaseModel):
    vacuum_probe_raw_path: Path
    vacuum_probe_emd_path: Path


class Outputs(BaseModel):
    plots_dir: Path
    ptycho_npy_dir: Path


class Config(BaseModel):
    microscope: Microscope
    crop_full_data: CropData
    crop_vacuum_probe: CropData
    experiment: Experiment
    binning: Binning
    calibration: Calibration
    plot: Plot
    outputs: Outputs


class BfDf(BaseModel):
    expand_BF: float
    extra_radius: float


class DPCPreprocess(BaseModel):
    force_com_rotation: int


class DPCReconstruct(BaseModel):
    store_iterations: bool
    q_highpass: float
    reset: bool


class DPC(BaseModel):
    preprocess: DPCPreprocess
    reconstruct: DPCReconstruct


class ParallaxInstantiation(BaseModel):
    object_padding_px: tuple[int, int]


class ParallaxPreprocess(BaseModel):
    threshold_intensity: float
    edge_blend: int
    defocus_guess: int
    rotation_guess: int


class ParallaxReconstruct(BaseModel):
    reset: bool
    min_alignment_bin: int
    max_iter_at_min_bin: int
    running_average: bool


class Parallax(BaseModel):
    instantiation: ParallaxInstantiation
    preprocess: ParallaxPreprocess
    reconstruct: ParallaxReconstruct
    crop_R: CropData


class PtychoPreprocess(BaseModel):
    force_com_transpose: bool
    force_com_rotation: int
    fit_function: str


class PtychoReconstruct(BaseModel):
    reset: bool
    store_iterations: bool
    max_iter: int
    step_size: float
    q_lowpass: float


class Ptycho(BaseModel):
    preprocess: PtychoPreprocess
    reconstruct: PtychoReconstruct


class Compute(BaseModel):
    device: str


class AnalysisConfig(BaseModel):
    bf_df: BfDf
    dpc: DPC
    parallax: Parallax
    ptycho: Ptycho
    compute: Compute
