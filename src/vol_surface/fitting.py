from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import RBFInterpolator, griddata

FIGURES_DIR = Path(__file__).resolve().parents[2] / "figures"

def plot_interpolated_surface(
    df: pd.DataFrame,
    method: str = "rbf",
    smoothing: float = 1.0,
    filename: str | None = None,
    n_grid: int = 60,
    elev: float = 25,
    azim: float = 120,
) -> plt.Figure:
                            
    """Interpolate the IV points and return the 3D plot of the surface.

    df       : output of run_surface_data_pipeline
               (columns: moneyness, time_to_maturity, mark_iv)
    method   : "rbf" (thin-plate spline, smooth) or "linear" (triangles)
    smoothing: only for "rbf"; 0 = passes through every point, >0 = smoother
    n_grid   : grid points per axis
    elev, azim: viewing angle of the 3D plot
    """
    # 1. Average options with the same (k, T), e.g. call and put at the money
    data = df.groupby(["moneyness", "time_to_maturity"], as_index=False)["mark_iv"].mean()

    # 2. Rescale k and T to [0, 1] so both axes weigh the same
    pts = data[["moneyness", "time_to_maturity"]].to_numpy(dtype=float)
    lo = pts.min(axis=0)
    span = pts.max(axis=0) - lo
    pts_scaled = (pts - lo) / span
    iv = data["mark_iv"].to_numpy(dtype=float)

    # 3. Regular grid on which to evaluate the surface
    k_grid = np.linspace(lo[0], lo[0] + span[0], n_grid)
    t_grid = np.linspace(lo[1], lo[1] + span[1], n_grid)
    K, T = np.meshgrid(k_grid, t_grid)
    grid_scaled = (np.column_stack([K.ravel(), T.ravel()]) - lo) / span

    # 4. Interpolation
    iv_linear = griddata(pts_scaled, iv, grid_scaled, method="linear")  # NaN outside the data
    if method == "linear":
        IV = iv_linear
    elif method == "rbf":
        rbf = RBFInterpolator(
            pts_scaled, iv, kernel="thin_plate_spline", smoothing=smoothing
        )
        IV = rbf(grid_scaled)
        IV[np.isnan(iv_linear)] = np.nan  # no extrapolation outside the data
    else:
        raise ValueError(f"Unknown method '{method}': use 'rbf' or 'linear'.")
    IV = IV.reshape(K.shape)

    # 5. Plot: surface + market points
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(projection="3d")
    ax.plot_surface(K, T, IV, cmap="viridis", alpha=0.75, linewidth=0)
    ax.scatter(
        df["moneyness"], df["time_to_maturity"], df["mark_iv"],
        color="red", s=8, label="Deribit mark IV",
    )
    ax.set_xlabel("Log-moneyness ln(K/F)")
    ax.set_ylabel("Time to maturity (years)")
    ax.set_zlabel("Implied Volatility (%)")
    ax.set_title(f"BTC implied volatility surface — {method} interpolation")
    ax.view_init(elev=elev, azim=azim)
    ax.legend()
    FIGURES_DIR.mkdir(exist_ok=True)
    path = FIGURES_DIR / (filename or f"interpolated_surface_{method}.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.show()
    plt.close(fig)
    return fig,path

if __name__ == "__main__":
    from vol_surface.market_data import run_surface_data_pipeline
    from vol_surface.deribit import get_instruments, get_book_summary_by_currency

    currency = "BTC"
    kind = "option"
    instruments = get_instruments(currency=currency, kind=kind)
    book_summary_by_currency = get_book_summary_by_currency(
        currency=currency, kind=kind
    )

    data = run_surface_data_pipeline(
        instruments, book_summary_by_currency, filter_illiquid=True, min_days=7
    )
    path = plot_interpolated_surface(data, method="rbf", smoothing=1.0)
    print(f"Saved to {path}")