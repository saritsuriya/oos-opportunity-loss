import os

import pandas as pd


class ReporterV5:
    def _summary_total(self, detail: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {"metric": "Total Lost Qty Raw", "value": detail["lost_qty_raw"].sum()},
                {"metric": "Total Lost Value Gross Raw", "value": detail["lost_value_gross_raw"].sum()},
                {"metric": "Total Lost Value Net Raw", "value": detail["lost_value_net_raw"].sum()},
            ]
        )

    def _summary_by_site(self, detail: pd.DataFrame) -> pd.DataFrame:
        grouped = detail.groupby("virtual_site", as_index=False)
        out = (
            grouped
            .agg(
                sku_rows=("sku", "size"),
                avg_oos_ratio=("oos_ratio_jan", "mean"),
                lost_qty_raw=("lost_qty_raw", "sum"),
                lost_value_gross_raw=("lost_value_gross_raw", "sum"),
                lost_value_net_raw=("lost_value_net_raw", "sum"),
                loss_gross=("loss_gross", "sum"),
                loss_net=("loss_net", "sum"),
            )
            .sort_values("lost_value_net_raw", ascending=False)
        )
        out = out.rename(
            columns={
                "sku_rows": "sku_site_rows_eval",
            }
        )
        return out

    def _summary_by_sku(self, detail: pd.DataFrame) -> pd.DataFrame:
        base = (
            detail.groupby("sku", as_index=False)
            .agg(
                product_name=("product_name", "first"),
                lost_qty_raw=("lost_qty_raw", "sum"),
                lost_value_gross_raw=("lost_value_gross_raw", "sum"),
                lost_value_net_raw=("lost_value_net_raw", "sum"),
                loss_gross=("loss_gross", "sum"),
                loss_net=("loss_net", "sum"),
            )
        )

        site_net = detail.pivot_table(
            index="sku", columns="virtual_site", values="loss_net", aggfunc="sum", fill_value=0.0
        ).add_prefix("loss_net_")

        out = base.merge(site_net.reset_index(), on="sku", how="left")
        return out.sort_values("lost_value_net_raw", ascending=False)

    def _definitions(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "field": "Summary by Site: sku_site_rows_eval",
                    "definition": "Count of evaluated sku+virtual_site rows in that virtual site",
                },
                {
                    "field": "Summary by Site: avg_oos_ratio",
                    "definition": "Average oos_ratio_jan across all evaluated sku rows in that virtual site",
                },
                {"field": "Summary by Site/SKU: lost_qty_raw", "definition": "Sum of raw lost qty"},
                {
                    "field": "Summary by Site/SKU: lost_value_net_raw",
                    "definition": "Sum of lost_qty_raw * net_per_unit",
                },
                {
                    "field": "Summary by Site/SKU: lost_value_gross_raw",
                    "definition": "Sum of lost_qty_raw * gross_per_unit",
                },
                {"field": "Summary by Site/SKU: loss_net", "definition": "Alias of lost_value_net_raw"},
                {"field": "Summary by Site/SKU: loss_gross", "definition": "Alias of lost_value_gross_raw"},
                {"field": "Detail: virtual_site", "definition": "Mapped virtual site from Site mapping.csv"},
                {
                    "field": "Detail: observed_days_jan",
                    "definition": "Total days in evaluation month from model config (e.g. Jan=31, Feb=28)",
                },
                {"field": "Detail: recorded_days", "definition": "Days where source has any daily stock row for sku+site"},
                {"field": "Detail: in_stock_days", "definition": "Days where aggregated stock_balance > 0"},
                {
                    "field": "Detail: oos_days_jan",
                    "definition": "observed_days_jan - in_stock_days (missing day treated as stock=0)",
                },
                {"field": "Detail: oos_ratio_jan", "definition": "oos_days_jan / observed_days_jan"},
                {
                    "field": "Detail: baseline_source",
                    "definition": "Which history window supplied the baseline: recent 6 months, fallback previous 6 months, or no history",
                },
                {
                    "field": "Detail: baseline_window_start / baseline_window_end",
                    "definition": "Date range used to build the baseline before the evaluation month",
                },
                {
                    "field": "Detail: baseline_window_days",
                    "definition": "Number of calendar days in the selected baseline window",
                },
                {
                    "field": "Detail: recent_qty / fallback_qty",
                    "definition": "Sales qty in the recent 6-month window and the older fallback 6-month window",
                },
                {
                    "field": "Detail: baseline_qty_window",
                    "definition": "Sales qty from the selected baseline window",
                },
                {
                    "field": "Detail: baseline_daily_qty",
                    "definition": "baseline_qty_window / baseline_window_days using the selected rolling window",
                },
                {"field": "Detail: expected_qty_jan", "definition": "baseline_daily_qty * observed_days_jan"},
                {"field": "Detail: actual_qty_jan", "definition": "Actual sales qty in evaluation month per sku+site"},
                {
                    "field": "Detail: is_actual_zero_jan",
                    "definition": "True when actual_qty_jan == 0; only these rows can keep loss",
                },
                {"field": "Detail: lost_qty_raw", "definition": "baseline_daily_qty * oos_days_jan, then set 0 if actual_qty_jan > 0"},
                {"field": "Detail: net_per_unit", "definition": "net / qty from order history aggregated by sku"},
                {"field": "Detail: gross_per_unit", "definition": "gross / qty from order history aggregated by sku"},
                {"field": "Detail: lost_value_net_raw", "definition": "lost_qty_raw * net_per_unit"},
                {"field": "Detail: lost_value_gross_raw", "definition": "lost_qty_raw * gross_per_unit"},
            ]
        )

    def _calculation_example(self, detail: pd.DataFrame) -> pd.DataFrame:
        sample = detail[detail["lost_qty_raw"] > 0].copy()
        if len(sample) == 0:
            sample = detail.copy()
        sample = sample.sort_values("loss_net", ascending=False).head(1)
        if len(sample) == 0:
            return pd.DataFrame(
                [{"item": "No sample row", "formula": "-", "value": "Detail sheet is empty"}]
            )

        r = sample.iloc[0]
        baseline = float(r["baseline_daily_qty"])
        oos_days = float(r["oos_days_jan"])
        pre_lost = baseline * oos_days
        actual_qty = float(r["actual_qty_jan"])
        lost_qty = float(r["lost_qty_raw"])
        net_u = float(r["net_per_unit"])
        gross_u = float(r["gross_per_unit"])
        loss_net = float(r["loss_net"])
        loss_gross = float(r["loss_gross"])

        return pd.DataFrame(
            [
                {"item": "Sample row", "formula": "highest loss_net row in Detail", "value": f"SKU {r['sku']} | Site {r['virtual_site']}"},
                {"item": "Input: baseline_source", "formula": "-", "value": r["baseline_source"]},
                {"item": "Input: recent_qty", "formula": "-", "value": float(r["recent_qty"])},
                {"item": "Input: fallback_qty", "formula": "-", "value": float(r["fallback_qty"])},
                {"item": "Input: baseline_window_qty", "formula": "-", "value": float(r["baseline_qty_window"])},
                {"item": "Input: baseline_window_days", "formula": "-", "value": float(r["baseline_window_days"])},
                {"item": "Input: observed_days", "formula": "-", "value": float(r["observed_days_jan"])},
                {"item": "Input: in_stock_days", "formula": "-", "value": float(r["in_stock_days"])},
                {"item": "Input: actual_qty", "formula": "-", "value": actual_qty},
                {
                    "item": "Step 1 baseline_daily_qty",
                    "formula": "baseline_window_qty / baseline_window_days",
                    "value": baseline,
                },
                {"item": "Step 2 oos_days", "formula": "observed_days - in_stock_days", "value": oos_days},
                {"item": "Step 3 preliminary_lost_qty", "formula": "baseline_daily_qty * oos_days", "value": pre_lost},
                {
                    "item": "Step 4 apply actual-zero rule",
                    "formula": "if actual_qty > 0 then lost_qty_raw=0 else keep Step 3",
                    "value": lost_qty,
                },
                {"item": "Input: net_per_unit", "formula": "-", "value": net_u},
                {"item": "Input: gross_per_unit", "formula": "-", "value": gross_u},
                {"item": "Step 5 loss_net", "formula": "lost_qty_raw * net_per_unit", "value": loss_net},
                {"item": "Step 6 loss_gross", "formula": "lost_qty_raw * gross_per_unit", "value": loss_gross},
            ]
        )

    def generate(
        self,
        detail: pd.DataFrame,
        qa_summary: pd.DataFrame,
        unmapped_site: pd.DataFrame,
        output_xlsx: str,
    ) -> str:
        os.makedirs(os.path.dirname(output_xlsx), exist_ok=True)

        summary_total = self._summary_total(detail)
        summary_site = self._summary_by_site(detail)
        summary_sku = self._summary_by_sku(detail)
        definitions = self._definitions()
        calc_example = self._calculation_example(detail)

        with pd.ExcelWriter(output_xlsx, engine="openpyxl") as writer:
            summary_total.to_excel(writer, sheet_name="Summary Total", index=False)
            summary_site.to_excel(writer, sheet_name="Summary by Site", index=False)
            summary_sku.to_excel(writer, sheet_name="Summary by SKU", index=False)
            detail.to_excel(writer, sheet_name="Detail SKU Site", index=False)
            qa_summary.to_excel(writer, sheet_name="QA Summary", index=False)
            unmapped_site.to_excel(writer, sheet_name="QA Unmapped SiteCode", index=False)
            definitions.to_excel(writer, sheet_name="Definitions", index=False)
            calc_example.to_excel(writer, sheet_name="Calculation Example", index=False)

        base = output_xlsx.replace(".xlsx", "")
        detail.to_csv(f"{base}_detail.csv", index=False)
        summary_site.to_csv(f"{base}_summary_site.csv", index=False)
        summary_sku.to_csv(f"{base}_summary_sku.csv", index=False)
        summary_total.to_csv(f"{base}_summary_total.csv", index=False)
        qa_summary.to_csv(f"{base}_qa_summary.csv", index=False)
        return output_xlsx
