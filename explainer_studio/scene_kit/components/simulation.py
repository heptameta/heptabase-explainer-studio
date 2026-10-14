"""Simulations replayed natively: solve the equations with scipy, then move mobjects exactly as the solution says,
so the motion is physically right; and run_toy, which computes the numbers a scene shows from a real program.

    solution = solve(lambda t, y: [y[1], -9.8 * np.sin(y[0])], [1.0, 0.0], t_end=6)
    pendulum = get_pendulum(length=2.5)
    replay(self, solution, lambda state, t: pendulum.set_angle(state[0]))
    days, series = solve_sir(beta=0.3, gamma=0.1, duration_days=160)   # for get_line_chart
"""

from __future__ import annotations

import numpy as np
from manimlib import *
from scipy.integrate import solve_ivp

from ... import user_dirs
from ..parts import Parts
from ..style import choose_local_text

__all__ = [
    "Pendulum",
    "Solution",
    "get_pendulum",
    "replay",
    "run_toy",
    "solve",
    "solve_orbit",
    "solve_pendulum",
    "solve_predator_prey",
    "solve_sir",
]

class Solution:
    """t (seconds of simulated time) and y (state per time); get_state_at(t) interpolates the state at any time."""

    def __init__(self, t: np.ndarray, y: np.ndarray):
        self.t, self.y = t, y

    def get_state_at(self, t: float) -> np.ndarray:
        t = min(max(t, self.t[0]), self.t[-1])
        return np.array([np.interp(t, self.t, row) for row in self.y])

    @property
    def duration_seconds(self) -> float:
        return float(self.t[-1] - self.t[0])


def solve(derivative, y0, t_end: float, t0: float = 0.0, sample_count: int = 2000, **kwargs) -> Solution:
    """Integrate dy/dt = deriv(t, y) from t0 to t_end (RK45 with tight tolerances by default)."""
    kwargs.setdefault("rtol", 1e-8)
    kwargs.setdefault("atol", 1e-10)
    sample_times = np.linspace(t0, t_end, sample_count)
    result = solve_ivp(derivative, (t0, t_end), np.asarray(y0, dtype=float), t_eval=sample_times, **kwargs)
    if not result.success:
        raise RuntimeError(f"integration failed: {result.message}")
    return Solution(result.t, result.y)


def replay(scene, solution: Solution, apply, speed: float = 1.0, duration_seconds: float | None = None) -> None:
    """Advance simulated time with the video clock (speed = simulated seconds per video second) and call
    apply(state, t) every frame to move the mobjects. The scene waits while it runs."""
    simulated_time = {"seconds": solution.t[0]}
    holder = Mobject()

    def update(_, dt):
        simulated_time["seconds"] += dt * speed
        apply(solution.get_state_at(simulated_time["seconds"]), simulated_time["seconds"])
    apply(solution.get_state_at(solution.t[0]), solution.t[0])
    holder.add_updater(update)
    scene.add(holder)
    scene.wait(duration_seconds if duration_seconds is not None else solution.duration_seconds / speed)
    holder.clear_updaters()
    scene.remove(holder)


# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------
def solve_pendulum(theta0: float = 1.0, length: float = 1.0, g: float = 9.81, damping: float = 0.0,
                   t_end: float = 8.0) -> Solution:
    """Full nonlinear pendulum (not the small-angle approximation): state (angle, angular velocity)."""
    return solve(lambda t, y: [y[1], -g / length * np.sin(y[0]) - damping * y[1]], [theta0, 0.0], t_end)


def get_pendulum(length: float = 2.5, bob_radius: float = 0.2, color=BLUE_C, pivot_point=2.5 * UP) -> VGroup:
    """A pendulum hanging from pivot_point. Parts: .rod, .bob, .pivot; set_angle(theta) (radians from vertical)."""
    pivot_dot = Dot(pivot_point, radius=0.06, fill_color=GREY_B)
    rod = Line(pivot_point, pivot_point + length * DOWN).set_stroke(GREY_A, 3)
    bob = Dot(pivot_point + length * DOWN, radius=bob_radius, fill_color=color)
    pendulum = Pendulum(rod, bob, pivot_dot)
    pendulum.rod, pendulum.bob, pendulum.pivot, pendulum.length = rod, bob, pivot_dot, length
    return pendulum


class Pendulum(Parts):
    """What get_pendulum returns: .rod, .bob, .pivot, .length, .set_angle(theta)."""

    def set_angle(self, theta: float) -> Pendulum:
        """Swing to theta radians from the vertical."""
        pivot_point = self.pivot.get_center()
        end = pivot_point + self.length * np.array([np.sin(theta), -np.cos(theta), 0])
        self.rod.put_start_and_end_on(pivot_point, end)
        self.bob.move_to(end)
        return self


def solve_orbit(e: float = 0.5, period_count: float = 1.0, gm: float = 1.0, a: float = 1.0) -> Solution:
    """A Kepler orbit around a mass at the origin: state (x, y, vx, vy), starting at perihelion; one period is
    2π·sqrt(a³/GM). Equal areas in equal times come out on their own."""
    r0 = a * (1 - e)
    v0 = np.sqrt(gm * (1 + e) / r0)
    period = 2 * np.pi * np.sqrt(a ** 3 / gm)

    def compute_derivative(t, state):
        x, y, vx, vy = state
        radius_cubed = (x * x + y * y) ** 1.5
        return [vx, vy, -gm * x / radius_cubed, -gm * y / radius_cubed]
    return solve(compute_derivative, [r0, 0, 0, v0], period * period_count)


def solve_sir(beta: float = 0.3, gamma: float = 0.1, s0: float = 0.99, i0: float = 0.01,
              duration_days: float = 160,
              labels: tuple[str, str, str] | None = None) -> tuple[list[float], dict[str, list[float]]]:
    """The SIR epidemic model; returns (days, {label: series}) ready for get_line_chart."""
    labels = labels or (choose_local_text("易感", "susceptible"), choose_local_text("感染", "infected"),
                        choose_local_text("康復", "recovered"))
    solution = solve(lambda t, y: [-beta * y[0] * y[1], beta * y[0] * y[1] - gamma * y[1], gamma * y[1]],
                     [s0, i0, 1 - s0 - i0], duration_days, sample_count=int(duration_days) + 1)
    return list(solution.t), {labels[index]: list(solution.y[index]) for index in range(3)}


def solve_predator_prey(a: float = 1.0, b: float = 0.1, c: float = 1.5, d: float = 0.075, x0: float = 10,
                        y0: float = 5, t_end: float = 30,
                        labels: tuple[str, str] | None = None) -> tuple[list[float], dict[str, list[float]]]:
    """Lotka–Volterra; returns (time, {label: series}) for get_line_chart."""
    labels = labels or (choose_local_text("兔子", "rabbits"), choose_local_text("狐狸", "foxes"))
    solution = solve(lambda t, state: [a * state[0] - b * state[0] * state[1], -c * state[1] + d * state[0] * state[1]],
                     [x0, y0], t_end, sample_count=600)
    return list(solution.t), {labels[0]: list(solution.y[0]), labels[1]: list(solution.y[1])}


def run_toy(function, *args, **kwargs):
    """Call a function of a toy program (plain Python in production/shared/, asserting its own answers) and return its
    result, cached on disk in the user cache: computed once, reused until the program's file changes, so a heavy toy
    (a training run, a sweep of a knob) does not rerun on every scene render. The result must pickle."""
    import hashlib
    import inspect
    import pickle
    from pathlib import Path
    source_file_path = Path(inspect.getsourcefile(function))
    cache_key = hashlib.sha256(source_file_path.read_bytes() + function.__qualname__.encode()
                         + repr((args, sorted(kwargs.items()))).encode()).hexdigest()[:24]
    cache_file_name = f"{source_file_path.stem}-{function.__name__}-{cache_key}.pkl"
    cache_file_path = user_dirs.get_cache_dir_path() / "toys" / cache_file_name
    if cache_file_path.exists():
        return pickle.loads(cache_file_path.read_bytes())
    result = function(*args, **kwargs)
    cache_file_path.parent.mkdir(parents=True, exist_ok=True)
    cache_file_path.write_bytes(pickle.dumps(result))
    return result
