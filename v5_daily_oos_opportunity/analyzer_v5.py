from dataclasses import dataclass
import calendar
from typing import Tuple

import numpy as np
import pandas as pd


@dataclass
class ModelConfig:
    eval_year: int = 2026
    eval_month: int = 1
    baseline_recent_months: int = 6
    baseline_fallback_months: int = 6
    use_live_skus_only: bool = True
    loss_only_when_actual_zero: bool = True


class DailyOOSOpportunityV5:
    """Daily OOS based opportunity loss model."""

    def __init__(
        self,
        product_df: pd.DataFrame,
        orders_df: pd.DataFrame,
        daily_stock_df: pd.DataFrame,
        site_map_df: pd.DataFrame,
        config: ModelConfig | None = None,
    ):
        self.product_df = product_df.copy()
        self.orders_df = orders_df.copy()
        self.daily_stock_df = daily_stock_df.copy()
        self.site_map_df = site_map_df.copy()
        self.config = config or ModelConfig()

    def _eval_days(self) -> int:
        return calendar.monthrange(self.config.eval_year, self.config.eval_month)[1]

    def _eval_anchor(self) -> pd.Timestamp:
        return pd.Timestamp(year=self.config.eval_year, month=self.config.eval_month, day=1)

    def _prepare_universe(self) -> pd.DataFrame:
        df = self.product_df.copy()
        df = df[~df["excluded_prefix_p"]].copy()
        if self.config.use_live_skus_only and "status" in df.columns:
            live = df[df["status"].astype(str).str.lower() == "live"].copy()
            if len(live) > 0:
                df = live
        return df[["sku", "product_name"]].drop_duplicates().reset_index(drop=True)

    def _prepare_daily_stock(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        eval_df = self.daily_stock_df[
            (self.daily_stock_df["posting_date"].dt.year == self.config.eval_year)
            & (self.daily_stock_df["posting_date"].dt.month == self.config.eval_month)
            & (~self.daily_stock_df["excluded_prefix_p"])
        ].copy()

        mapped = eval_df.merge(self.site_map_df, on="site_code", how="left")
        unmapped = (
            mapped[mapped["virtual_site"].isna()]
            .groupby("site_code", as_index=False)
            .agg(rows=("sku", "size"))
            .sort_values("rows", ascending=False)
        )
        mapped = mapped[mapped["virtual_site"].notna()].copy()

        # Aggregate by day+sku+virtual site, summing sub-site balances.
        day_bal = (
            mapped.groupby(["posting_date", "sku", "virtual_site"], as_index=False)
            .agg(stock_balance=("stock_balance", "sum"))
        )
        return day_bal, unmapped

    def _build_oos_days(self, universe_skus: pd.DataFrame, day_bal: pd.DataFrame) -> pd.DataFrame:
        eval_days = self._eval_days()
        sites = sorted(self.site_map_df["virtual_site"].unique().tolist())

        # Full sku-site universe for evaluation month.
        skus = universe_skus[["sku"]].drop_duplicates().copy()
        skus["_k"] = 1
        site_df = pd.DataFrame({"virtual_site": sites})
        site_df["_k"] = 1
        universe = skus.merge(site_df, on="_k", how="inner").drop(columns="_k")

        in_stock = (
            day_bal[day_bal["stock_balance"] > 0]
            .groupby(["sku", "virtual_site"], as_index=False)
            .agg(in_stock_days=("posting_date", "nunique"))
        )
        any_record = (
            day_bal.groupby(["sku", "virtual_site"], as_index=False)
            .agg(recorded_days=("posting_date", "nunique"))
        )

        oos = universe.merge(in_stock, on=["sku", "virtual_site"], how="left")
        oos = oos.merge(any_record, on=["sku", "virtual_site"], how="left")
        oos["in_stock_days"] = oos["in_stock_days"].fillna(0).astype(int)
        oos["recorded_days"] = oos["recorded_days"].fillna(0).astype(int)
        # Per business rule: missing daily record => stock=0 => OOS day.
        oos["oos_days_jan"] = (eval_days - oos["in_stock_days"]).clip(lower=0)
        oos["observed_days_jan"] = eval_days
        oos["oos_ratio_jan"] = np.where(oos["observed_days_jan"] > 0, oos["oos_days_jan"] / oos["observed_days_jan"], 0.0)
        return oos

    def _build_baseline_and_actual(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        ord_df = self.orders_df[~self.orders_df["excluded_prefix_p"]].copy()

        # Price per unit (use all available orders to maximize coverage).
        price = (
            ord_df.groupby("sku", as_index=False)
            .agg(
                total_qty=("quantity", "sum"),
                total_gross=("gross", "sum"),
                total_net=("net", "sum"),
                product_name=("product_name", "first"),
            )
        )
        price["gross_per_unit"] = np.where(price["total_qty"] > 0, price["total_gross"] / price["total_qty"], 0.0)
        price["net_per_unit"] = np.where(price["total_qty"] > 0, price["total_net"] / price["total_qty"], 0.0)
        price = price[["sku", "product_name", "gross_per_unit", "net_per_unit"]]

        ord_df["virtual_site"] = ord_df["stock_code"]
        anchor = self._eval_anchor()
        recent_start = anchor - pd.DateOffset(months=self.config.baseline_recent_months)
        fallback_start = recent_start - pd.DateOffset(months=self.config.baseline_fallback_months)

        recent_days = int((anchor - recent_start).days)
        fallback_days = int((recent_start - fallback_start).days)
        recent_end = anchor - pd.Timedelta(days=1)
        fallback_end = recent_start - pd.Timedelta(days=1)

        recent_sales = ord_df[
            (ord_df["purchase_date"] >= recent_start)
            & (ord_df["purchase_date"] < anchor)
        ].copy()
        fallback_sales = ord_df[
            (ord_df["purchase_date"] >= fallback_start)
            & (ord_df["purchase_date"] < recent_start)
        ].copy()

        recent = (
            recent_sales.groupby(["sku", "virtual_site"], as_index=False)
            .agg(recent_qty=("quantity", "sum"))
        )
        fallback = (
            fallback_sales.groupby(["sku", "virtual_site"], as_index=False)
            .agg(fallback_qty=("quantity", "sum"))
        )

        baseline = recent.merge(fallback, on=["sku", "virtual_site"], how="outer")
        if len(baseline) == 0:
            baseline = pd.DataFrame(columns=["sku", "virtual_site", "recent_qty", "fallback_qty"])
        baseline["recent_qty"] = pd.to_numeric(baseline["recent_qty"], errors="coerce").fillna(0.0)
        baseline["fallback_qty"] = pd.to_numeric(baseline["fallback_qty"], errors="coerce").fillna(0.0)

        use_recent = baseline["recent_qty"] > 0
        use_fallback = (~use_recent) & (baseline["fallback_qty"] > 0)

        baseline["baseline_qty_window"] = np.select(
            [use_recent, use_fallback],
            [baseline["recent_qty"], baseline["fallback_qty"]],
            default=0.0,
        )
        baseline["baseline_window_days"] = np.select(
            [use_recent, use_fallback],
            [recent_days, fallback_days],
            default=0,
        ).astype(int)
        baseline["baseline_window_start"] = np.select(
            [use_recent, use_fallback],
            [recent_start.date().isoformat(), fallback_start.date().isoformat()],
            default="",
        )
        baseline["baseline_window_end"] = np.select(
            [use_recent, use_fallback],
            [recent_end.date().isoformat(), fallback_end.date().isoformat()],
            default="",
        )
        baseline["baseline_source"] = np.select(
            [use_recent, use_fallback],
            [
                f"recent_{self.config.baseline_recent_months}m",
                f"fallback_prev_{self.config.baseline_fallback_months}m",
            ],
            default="no_history",
        )
        baseline["baseline_method"] = (
            f"rolling_{self.config.baseline_recent_months}m"
            f"_with_{self.config.baseline_fallback_months}m_fallback"
        )
        baseline["baseline_daily_qty"] = np.where(
            baseline["baseline_window_days"] > 0,
            baseline["baseline_qty_window"] / baseline["baseline_window_days"],
            0.0,
        )
        baseline = baseline[
            [
                "sku",
                "virtual_site",
                "baseline_method",
                "baseline_source",
                "baseline_window_start",
                "baseline_window_end",
                "baseline_window_days",
                "baseline_qty_window",
                "baseline_daily_qty",
                "recent_qty",
                "fallback_qty",
            ]
        ]

        actual = ord_df[
            (ord_df["purchase_date"].dt.year == self.config.eval_year)
            & (ord_df["purchase_date"].dt.month == self.config.eval_month)
        ].copy()
        actual = (
            actual.groupby(["sku", "virtual_site"], as_index=False)
            .agg(actual_qty_jan=("quantity", "sum"))
        )
        return baseline, actual, price

    def run(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        universe = self._prepare_universe()
        day_bal, unmapped_site = self._prepare_daily_stock()
        oos_days = self._build_oos_days(universe, day_bal)
        baseline, actual, price = self._build_baseline_and_actual()

        detail = oos_days.merge(baseline, on=["sku", "virtual_site"], how="left")
        detail = detail.merge(actual, on=["sku", "virtual_site"], how="left")
        detail = detail.merge(universe, on="sku", how="left")
        detail = detail.merge(price, on="sku", how="left", suffixes=("", "_price"))
        if "product_name_price" in detail.columns:
            detail["product_name"] = detail["product_name"].fillna(detail["product_name_price"])
            detail = detail.drop(columns=["product_name_price"])

        for col in [
            "baseline_daily_qty",
            "baseline_qty_window",
            "recent_qty",
            "fallback_qty",
            "actual_qty_jan",
            "gross_per_unit",
            "net_per_unit",
        ]:
            detail[col] = pd.to_numeric(detail[col], errors="coerce").fillna(0.0)
        detail["baseline_window_days"] = pd.to_numeric(
            detail["baseline_window_days"], errors="coerce"
        ).fillna(0).astype(int)
        detail["baseline_method"] = detail["baseline_method"].fillna(
            f"rolling_{self.config.baseline_recent_months}m_with_{self.config.baseline_fallback_months}m_fallback"
        )
        detail["baseline_source"] = detail["baseline_source"].fillna("no_history")
        detail["baseline_window_start"] = detail["baseline_window_start"].fillna("")
        detail["baseline_window_end"] = detail["baseline_window_end"].fillna("")

        days = self._eval_days()
        detail["expected_qty_jan"] = detail["baseline_daily_qty"] * days
        detail["qty_gap_jan"] = (detail["expected_qty_jan"] - detail["actual_qty_jan"]).clip(lower=0.0)

        detail["lost_qty_raw"] = detail["baseline_daily_qty"] * detail["oos_days_jan"]

        detail["is_actual_zero_jan"] = detail["actual_qty_jan"] <= 0.0
        if self.config.loss_only_when_actual_zero:
            mask = detail["is_actual_zero_jan"]
            detail.loc[~mask, ["lost_qty_raw"]] = 0.0

        detail["lost_value_gross_raw"] = detail["lost_qty_raw"] * detail["gross_per_unit"]
        detail["lost_value_net_raw"] = detail["lost_qty_raw"] * detail["net_per_unit"]

        detail["lost_qty"] = detail["lost_qty_raw"]
        detail["loss_gross"] = detail["lost_value_gross_raw"]
        detail["loss_net"] = detail["lost_value_net_raw"]

        detail = detail[
            [
                "sku",
                "product_name",
                "virtual_site",
                "observed_days_jan",
                "recorded_days",
                "in_stock_days",
                "oos_days_jan",
                "oos_ratio_jan",
                "baseline_method",
                "baseline_source",
                "baseline_window_start",
                "baseline_window_end",
                "baseline_window_days",
                "recent_qty",
                "fallback_qty",
                "baseline_qty_window",
                "baseline_daily_qty",
                "expected_qty_jan",
                "actual_qty_jan",
                "is_actual_zero_jan",
                "qty_gap_jan",
                "lost_qty_raw",
                "gross_per_unit",
                "net_per_unit",
                "lost_value_gross_raw",
                "lost_value_net_raw",
                "lost_qty",
                "loss_gross",
                "loss_net",
            ]
        ].sort_values("lost_value_net_raw", ascending=False).reset_index(drop=True)

        qa_rows = [
            {"metric": "product_sku_count_all", "value": int(self.product_df["sku"].nunique())},
            {
                "metric": "product_sku_count_excl_prefix_p",
                "value": int(self.product_df.loc[~self.product_df["excluded_prefix_p"], "sku"].nunique()),
            },
            {
                "metric": "product_sku_count_live_excl_prefix_p",
                "value": int(universe["sku"].nunique()),
            },
            {"metric": "sku_universe_count", "value": int(universe["sku"].nunique())},
            {"metric": "daily_stock_rows_eval_month", "value": int(len(day_bal))},
            {"metric": "mapped_site_codes_count", "value": int(self.site_map_df["site_code"].nunique())},
            {"metric": "unmapped_site_code_count", "value": int(len(unmapped_site))},
            {"metric": "detail_rows", "value": int(len(detail))},
            {
                "metric": "config_baseline_recent_months",
                "value": int(self.config.baseline_recent_months),
            },
            {
                "metric": "config_baseline_fallback_months",
                "value": int(self.config.baseline_fallback_months),
            },
            {
                "metric": "detail_rows_baseline_recent",
                "value": int((detail["baseline_source"] == f"recent_{self.config.baseline_recent_months}m").sum()),
            },
            {
                "metric": "detail_rows_baseline_fallback",
                "value": int(
                    (detail["baseline_source"] == f"fallback_prev_{self.config.baseline_fallback_months}m").sum()
                ),
            },
            {
                "metric": "detail_rows_baseline_no_history",
                "value": int((detail["baseline_source"] == "no_history").sum()),
            },
            {"metric": "detail_rows_actual_zero", "value": int(detail["is_actual_zero_jan"].sum())},
            {
                "metric": "detail_rows_actual_gt_zero",
                "value": int((~detail["is_actual_zero_jan"]).sum()),
            },
            {
                "metric": "config_loss_only_when_actual_zero",
                "value": int(self.config.loss_only_when_actual_zero),
            },
            {"metric": "total_lost_value_net_raw", "value": float(detail["lost_value_net_raw"].sum())},
            {"metric": "excluded_prefix_p_products", "value": int(self.product_df["excluded_prefix_p"].sum())},
            {"metric": "excluded_prefix_p_orders", "value": int(self.orders_df["excluded_prefix_p"].sum())},
            {"metric": "excluded_prefix_p_daily_stock", "value": int(self.daily_stock_df["excluded_prefix_p"].sum())},
        ]
        qa_summary = pd.DataFrame(qa_rows)
        return detail, qa_summary, unmapped_site
