from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np


@dataclass
class MovementStyle:
    speed_factor: float = 1.0
    precision: float = 1.0
    nervousness: float = 0.4
    overshoot_tendency: float = 0.3
    sub_movement_count: int = 2
    jerk_smoothness: float = 0.85

    @staticmethod
    def random():
        return MovementStyle(
            speed_factor=np.random.uniform(0.8, 1.3),
            precision=np.random.uniform(0.7, 1.3),
            nervousness=np.random.uniform(0.15, 0.65),
            overshoot_tendency=np.random.uniform(0.1, 0.5),
            sub_movement_count=np.random.choice([1, 2, 2, 3]),
            jerk_smoothness=np.random.uniform(0.7, 0.95),
        )

@dataclass
class ScreenConfig:
    width: int = 1920
    height: int = 1080
    sample_rate: int = 120

    @property
    def diagonal(self) -> float:
        return float(np.sqrt(self.width**2 + self.height**2))

@dataclass
class Trajectory:
    x: np.ndarray
    y: np.ndarray
    t: np.ndarray
    v: np.ndarray


def _fitts_duration(distance: float, diagonal: float, style: MovementStyle) -> float:
    rel = distance / diagonal
    a = 0.18 + np.random.uniform(-0.02, 0.02)
    b = 0.38 + np.random.uniform(-0.03, 0.03)
    mt = a + b * np.log2(1 + 12 * rel)
    mt /= style.speed_factor
    mt *= np.random.uniform(0.92, 1.08)
    return np.clip(mt, 0.06, 2.0)

def _minimum_jerk_profile(n: int, peak_shift: float = 0.0) -> np.ndarray:
    t = np.linspace(0, 1, n)
    t_shifted = np.clip(t - peak_shift * 0.05, 0, 1)
    t_norm = t_shifted / t_shifted[-1] if t_shifted[-1] > 0 else t_shifted
    pos = 10 * t_norm**3 - 15 * t_norm**4 + 6 * t_norm**5
    vel = np.gradient(pos, t_norm if np.all(np.diff(t_norm) > 0) else t)
    vel = np.clip(vel, 0, None)
    peak = vel.max()
    if peak > 0:
        vel /= peak
    return vel

def _sub_movement_profile(n: int, style: MovementStyle) -> np.ndarray:
    primary = _minimum_jerk_profile(n, peak_shift=np.random.uniform(-0.5, 0.5))
    primary *= np.random.uniform(0.85, 1.0)
    combined = primary.copy()

    for k in range(1, style.sub_movement_count):
        frac = np.random.uniform(0.55 + k * 0.1, 0.75 + k * 0.05)
        start_idx = int(frac * n)
        sub_n = n - start_idx
        if sub_n < 4:
            continue
        sub = _minimum_jerk_profile(sub_n)
        amplitude = np.random.uniform(0.15, 0.35) / k
        combined[start_idx:] += sub * amplitude

    peak = combined.max()
    if peak > 0:
        combined /= peak
    return combined


def _cubic_bezier(
    t: np.ndarray, p0: np.ndarray, p1: np.ndarray, p2: np.ndarray, p3: np.ndarray
) -> np.ndarray:
    t2 = t[:, None] if t.ndim == 1 else t
    return (
        (1 - t2) ** 3 * p0
        + 3 * (1 - t2) ** 2 * t2 * p1
        + 3 * (1 - t2) * t2**2 * p2
        + t2**3 * p3
    )

def _generate_bezier_path(
    start: np.ndarray,
    end: np.ndarray,
    distance: float,
    diagonal: float,
    style: MovementStyle,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    direction = end - start
    if distance > 0:
        d_norm = direction / distance
    else:
        d_norm = np.array([1.0, 0.0])

    perp = np.array([-d_norm[1], d_norm[0]])
    rel_dist = distance / diagonal

    if rel_dist < 0.08:
        curve_mag = np.random.uniform(0.02, 0.06)
    elif rel_dist < 0.25:
        curve_mag = np.random.uniform(0.04, 0.12)
    else:
        curve_mag = np.random.uniform(0.06, 0.18)

    curve_mag /= style.precision
    side = np.random.choice([-1.0, 1.0])

    angle = np.arctan2(direction[1], direction[0])
    biomech = np.sin(angle) * 0.15
    side *= 1.0 + biomech * np.random.uniform(0.5, 1.5)

    cp1_along = np.random.uniform(0.2, 0.4)
    cp2_along = np.random.uniform(0.6, 0.8)
    cp1_perp = side * curve_mag * distance * np.random.uniform(0.5, 1.2)
    cp2_perp = (
        side
        * curve_mag
        * distance
        * np.random.uniform(0.3, 0.8)
        * np.random.choice([-1, 1])
    )

    p0 = start.copy()
    p3 = end.copy()
    p1 = start + cp1_along * direction + cp1_perp * perp
    p2 = start + cp2_along * direction + cp2_perp * perp

    return p0, p1, p2, p3


def _arc_length_parameterize(p0, p1, p2, p3, n_fine=500):
    t_fine = np.linspace(0, 1, n_fine)
    pts = _cubic_bezier(t_fine, p0, p1, p2, p3)
    diffs = np.diff(pts, axis=0)
    seg_lens = np.sqrt(np.sum(diffs**2, axis=1))
    cum_len = np.concatenate(([0.0], np.cumsum(seg_lens)))
    total = cum_len[-1]
    return t_fine, cum_len, total

def _map_velocity_to_bezier_params(
    vel_profile: np.ndarray,
    t_fine: np.ndarray,
    cum_len: np.ndarray,
    total_len: float,
    time_vals: np.ndarray,
) -> np.ndarray:
    n = len(vel_profile)
    dt = np.diff(time_vals)
    dist_traveled = np.concatenate(([0.0], np.cumsum(vel_profile[:-1] * dt)))
    if dist_traveled[-1] > 0:
        dist_traveled = dist_traveled / dist_traveled[-1] * total_len
    else:
        dist_traveled = np.linspace(0, total_len, n)
    bezier_t = np.interp(dist_traveled, cum_len, t_fine)
    return bezier_t


def _add_overshoot(
    path_x: np.ndarray,
    path_y: np.ndarray,
    end: np.ndarray,
    distance: float,
    style: MovementStyle,
) -> Tuple[np.ndarray, np.ndarray]:
    if distance < 30 or np.random.random() > style.overshoot_tendency:
        return path_x, path_y

    n = len(path_x)
    overshoot_start = int(n * np.random.uniform(0.82, 0.92))
    overshoot_n = n - overshoot_start

    if overshoot_n < 3:
        return path_x, path_y

    direction = end - np.array([path_x[overshoot_start], path_y[overshoot_start]])
    d_norm = np.linalg.norm(direction)
    if d_norm < 1e-6:
        return path_x, path_y

    direction /= d_norm
    overshoot_mag = distance * np.random.uniform(0.02, 0.08) / style.precision

    t_os = np.linspace(0, 1, overshoot_n)
    envelope = np.sin(np.pi * t_os) * (1 - t_os) ** 0.5
    envelope /= envelope.max() if envelope.max() > 0 else 1.0

    path_x[overshoot_start:] += (
        (envelope * overshoot_mag * direction[0]).astype(path_x.dtype)
        if np.issubdtype(path_x.dtype, np.integer)
        else envelope * overshoot_mag * direction[0]
    )
    path_y[overshoot_start:] += (
        (envelope * overshoot_mag * direction[1]).astype(path_y.dtype)
        if np.issubdtype(path_y.dtype, np.integer)
        else envelope * overshoot_mag * direction[1]
    )

    return path_x, path_y


def _add_noise(
    path_x: np.ndarray,
    path_y: np.ndarray,
    vel_profile: np.ndarray,
    distance: float,
    style: MovementStyle,
) -> Tuple[np.ndarray, np.ndarray]:
    n = len(path_x)
    base_mag = distance * 0.0025 / style.precision * (0.4 + style.nervousness)

    vel_factor = 1.0 - vel_profile * 0.7
    magnitude = base_mag * vel_factor

    kernel_size = max(3, n // 12)
    kernel = np.ones(kernel_size) / kernel_size

    raw_x = np.random.normal(0, 1, n)
    raw_y = np.random.normal(0, 1, n)
    smooth_x = np.convolve(raw_x, kernel, mode="same")
    smooth_y = np.convolve(raw_y, kernel, mode="same")

    taper = np.ones(n)
    taper_len = min(6, n // 4)
    if taper_len > 1:
        taper[:taper_len] = np.linspace(0, 1, taper_len)
        taper[-taper_len:] = np.linspace(1, 0, taper_len)

    path_x += smooth_x * magnitude * taper
    path_y += smooth_y * magnitude * taper

    return path_x, path_y

def _micro_corrections(
    path_x: np.ndarray, path_y: np.ndarray, end: np.ndarray, n: int
) -> Tuple[np.ndarray, np.ndarray]:
    correction_zone = max(3, int(n * 0.12))
    start_idx = n - correction_zone

    for i in range(start_idx, n):
        blend = ((i - start_idx) / correction_zone) ** 2
        path_x[i] = path_x[i] * (1 - blend * 0.3) + end[0] * blend * 0.3
        path_y[i] = path_y[i] * (1 - blend * 0.3) + end[1] * blend * 0.3

    return path_x, path_y

def generate_single(
    start: np.ndarray, end: np.ndarray, config: ScreenConfig, style: MovementStyle
) -> Trajectory:
    direction = end - start
    distance = float(np.linalg.norm(direction))

    if distance < 1:
        return Trajectory(
            x=np.array([start[0], end[0]]),
            y=np.array([start[1], end[1]]),
            t=np.array([0.0, 10.0]),
            v=np.array([0.0, 0.0]),
        )

    duration = _fitts_duration(distance, config.diagonal, style)
    n = max(int(duration * config.sample_rate), 6)

    vel_profile = _sub_movement_profile(n, style)

    p0, p1, p2, p3 = _generate_bezier_path(start, end, distance, config.diagonal, style)

    t_fine, cum_len, total_len = _arc_length_parameterize(p0, p1, p2, p3)

    time_vals = np.linspace(0, duration, n)
    bezier_t = _map_velocity_to_bezier_params(
        vel_profile, t_fine, cum_len, total_len, time_vals
    )

    pts = _cubic_bezier(bezier_t, p0, p1, p2, p3)
    path_x = pts[:, 0].copy()
    path_y = pts[:, 1].copy()

    path_x, path_y = _add_overshoot(path_x, path_y, end, distance, style)
    path_x, path_y = _add_noise(path_x, path_y, vel_profile, distance, style)
    path_x, path_y = _micro_corrections(path_x, path_y, end, n)

    path_x[0] = start[0]
    path_y[0] = start[1]
    path_x[-1] = end[0]
    path_y[-1] = end[1]

    path_x = np.clip(path_x, 0, config.width - 1)
    path_y = np.clip(path_y, 0, config.height - 1)

    path_x = np.round(path_x).astype(int)
    path_y = np.round(path_y).astype(int)

    timestamps = np.round(np.linspace(0, duration * 1000, n)).astype(float)

    velocities = np.zeros(n)
    dt_arr = np.diff(timestamps) / 1000.0
    dx = np.diff(path_x).astype(float)
    dy = np.diff(path_y).astype(float)
    speeds = np.sqrt(dx**2 + dy**2) / np.where(dt_arr > 0, dt_arr, 1e-10)
    velocities[1:] = speeds

    return Trajectory(x=path_x, y=path_y, t=timestamps, v=velocities)


def generate(
    coords: Sequence[Sequence[float]],
    config: Optional[ScreenConfig] = None,
    style: Optional[MovementStyle] = None,
) -> List[Trajectory]:
    if config is None:
        config = ScreenConfig()
    if style is None:
        style = MovementStyle.random()

    x_coords, y_coords = coords[0], coords[1]
    results = []

    for i in range(len(x_coords) - 1):
        s = np.array([x_coords[i], y_coords[i]], dtype=float)
        e = np.array([x_coords[i + 1], y_coords[i + 1]], dtype=float)
        results.append(generate_single(s, e, config, style))

    return results


def merge(
    trajectories: List[Trajectory], delay_range: Tuple[float, float] = (70, 200)
) -> Trajectory:
    if not trajectories:
        return Trajectory(
            x=np.array([]), y=np.array([]), t=np.array([]), v=np.array([])
        )

    all_x, all_y, all_t, all_v = [], [], [], []
    offset = 0.0

    for i, traj in enumerate(trajectories):
        if i > 0:
            offset = float(all_t[-1][-1]) + np.random.uniform(*delay_range)

        all_x.append(traj.x)
        all_y.append(traj.y)
        all_t.append(traj.t + offset)
        all_v.append(traj.v)

    return Trajectory(
        x=np.concatenate(all_x),
        y=np.concatenate(all_y),
        t=np.concatenate(all_t),
        v=np.concatenate(all_v),
    )


def deduplicate(traj: Trajectory) -> Trajectory:
    if len(traj.x) < 2:
        return traj
    mask = np.ones(len(traj.x), dtype=bool)
    mask[1:] = (np.diff(traj.x) != 0) | (np.diff(traj.y) != 0)
    return Trajectory(x=traj.x[mask], y=traj.y[mask], t=traj.t[mask], v=traj.v[mask])

def animate_trajectory(
    traj: Trajectory,
    config: ScreenConfig,
    speed_multiplier: float = 1.0,
    save_gif: Optional[str] = None,
    gif_fps: int = 60,
    step: int = 1,
):
    fig, (ax_path, ax_vel) = plt.subplots(
        1, 2, figsize=(16, 7), gridspec_kw={"width_ratios": [1.4, 1]}
    )

    ax_path.set_xlim(0, config.width)
    ax_path.set_ylim(0, config.height)
    ax_path.set_aspect("equal")
    ax_path.invert_yaxis()
    ax_path.set_facecolor("#1a1a2e")
    ax_path.grid(True, alpha=0.15, color="white")

    ax_vel.set_xlim(0, traj.t[-1])
    ax_vel.set_ylim(0, max(traj.v) * 1.15 if max(traj.v) > 0 else 100)
    ax_vel.set_facecolor("#1a1a2e")
    ax_vel.grid(True, alpha=0.15, color="white")
    ax_vel.set_xlabel("Time (ms)", color="white")
    ax_vel.set_ylabel("Velocity (px/s)", color="white")

    for ax in (ax_path, ax_vel):
        ax.tick_params(colors="white")
        for spine in ax.spines.values():
            spine.set_color("#333")

    fig.patch.set_facecolor("#0f0f23")
    fig.suptitle("CursorFlow", color="white", fontsize=16, fontweight="bold")

    (trail_line,) = ax_path.plot([], [], color="#00d4ff", linewidth=1.5, alpha=0.6)
    ax_path.scatter([], [], c=[], cmap="cool", s=8, alpha=0.7, zorder=3)
    (cursor_dot,) = ax_path.plot([], [], "o", color="#ff6b6b", markersize=10, zorder=5)

    ax_path.plot(traj.x[0], traj.y[0], "s", color="#50fa7b", markersize=12, zorder=6)
    ax_path.plot(traj.x[-1], traj.y[-1], "X", color="#ff5555", markersize=14, zorder=6)

    (vel_line,) = ax_vel.plot([], [], color="#ff6b6b", linewidth=1.5)
    vel_fill = None

    n_total = len(traj.x)
    frame_indices = list(range(0, n_total, step))
    if frame_indices[-1] != n_total - 1:
        frame_indices.append(n_total - 1)
    n_frames = len(frame_indices)
    frame_interval = max(1, int(1000 / config.sample_rate / speed_multiplier * step))

    def init():
        trail_line.set_data([], [])
        cursor_dot.set_data([], [])
        vel_line.set_data([], [])
        return trail_line, cursor_dot, vel_line

    def update(frame):
        nonlocal vel_fill
        idx = frame_indices[min(frame, n_frames - 1)] + 1

        trail_line.set_data(traj.x[:idx], traj.y[:idx])

        if idx > 0:
            cursor_dot.set_data([traj.x[idx - 1]], [traj.y[idx - 1]])

        vel_line.set_data(traj.t[:idx], traj.v[:idx])

        if vel_fill is not None:
            vel_fill.remove()
        vel_fill_new = ax_vel.fill_between(
            traj.t[:idx], traj.v[:idx], alpha=0.2, color="#ff6b6b"
        )
        vel_fill = vel_fill_new

        return trail_line, cursor_dot, vel_line

    anim = animation.FuncAnimation(
        fig,
        update,
        init_func=init,
        frames=n_frames,
        interval=frame_interval,
        blit=False,
        repeat=False,
    )

    plt.tight_layout()

    if save_gif:
        anim.save(save_gif, writer="pillow", fps=gif_fps)
    else:
        plt.show()
    return anim