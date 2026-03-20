"""Export daily stock snapshots from Databricks for TH / CN / THT in one run.

This script:
1. Reads separate SKU list files for each channel.
2. Queries Databricks stock data per channel using that channel's site codes.
3. Exports one Excel workbook with one tab per channel.
4. Exports one CSV per channel for direct upload into the current app flow.

Run this inside a Databricks notebook or Databricks Python environment where
the global ``spark`` session is already available.
"""

from __future__ import annotations

from importlib.util import find_spec
from pathlib import Path

import pandas as pd


# ==========================================
# 1. PARAMETERS - edit dates and paths here
# ==========================================
P_START_DATE = "2026-03-01"
P_END_DATE = "2026-03-31"

# Optional: export a subset such as ("th", "tht")
CHANNELS_TO_EXPORT = ("th", "kingpowercn", "tht")

OUTPUT_XLSX_PATH = "/Workspace/Shared/KP_BU/output/ECOM-MULTI - Daily Stock.xlsx"

CHANNEL_EXPORTS = {
    "th": {
        "label": "TH",
        "sheet_name": "TH",
        "input_path": "/Workspace/Shared/KP_BU/input/ECOM-TH - Article_Code.csv",
        "output_csv_path": "/Workspace/Shared/KP_BU/output/ECOM-TH - Daily Stock.csv",
        "site_codes": [
            "26GA",
            "26FH",
            "26GC",
            "26GD",
            "26GE",
            "26GG",
            "26EJ",
            "26EH",
            "26EU",
            "26FE",
            "26FO",
            "26FQ",
            "26FR",
            "2815",
            "2510",
            "28DA",
            "28DD",
            "28DC",
            "28DB",
            "27DA",
            "27DE",
            "27DD",
            "1110",
            "2111",
            "1112",
            "1315",
            "1113",
            "2110",
        ],
    },
    "kingpowercn": {
        "label": "KingPowerCN",
        "sheet_name": "CN",
        "input_path": "/Workspace/Shared/KP_BU/input/ECOM-CN - Article_Code.csv",
        "output_csv_path": "/Workspace/Shared/KP_BU/output/ECOM-CN - Daily Stock.csv",
        "site_codes": [
            "1110",
            "1112",
            "1113",
            "1315",
            "13ZB",
            "13ZC",
            "2110",
            "2111",
            "2510",
            "25DA",
            "25DC",
            "25DE",
            "26EH",
            "26EJ",
            "26EU",
            "26FE",
            "26FH",
            "26FO",
            "26FQ",
            "26FR",
            "26GA",
            "26GC",
            "26GD",
            "26GE",
            "26GG",
            "27DA",
            "27DD",
            "27DE",
            "2815",
            "28DA",
            "28DB",
            "28DC",
            "28DD",
        ],
    },
    "tht": {
        "label": "THT",
        "sheet_name": "THT",
        "input_path": "/Workspace/Shared/KP_BU/input/ECOM-THT - Article_Code.csv",
        "output_csv_path": "/Workspace/Shared/KP_BU/output/ECOM-THT - Daily Stock.csv",
        "site_codes": [
            "12ZA",
            "12ZB",
            "12ZC",
            "12ZD",
            "12ZE",
            "12ZF",
            "13ZE",
            "1110",
            "1112",
            "1113",
            "1315",
        ],
    },
}

CHANNEL_ALIASES = {
    "th": "th",
    "kingpowercn": "kingpowercn",
    "king_power_cn": "kingpowercn",
    "kpcn": "kingpowercn",
    "cn": "kingpowercn",
    "tht": "tht",
}


def _require_spark_session():
    try:
        return spark  # type: ignore[name-defined]
    except NameError as exc:  # pragma: no cover - Databricks runtime guard
        raise RuntimeError(
            "This script must run inside Databricks with an active `spark` session."
        ) from exc


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _resolve_channels_to_export(channels_to_export: tuple[str, ...] | list[str] | str) -> list[str]:
    if isinstance(channels_to_export, str):
        raw_values = [part.strip() for part in channels_to_export.split(",")]
    else:
        raw_values = [str(part).strip() for part in channels_to_export]

    resolved: list[str] = []
    for raw_value in raw_values:
        normalized = raw_value.lower().replace("-", "").replace(" ", "").replace("/", "")
        if normalized not in CHANNEL_ALIASES:
            supported = ", ".join(sorted(CHANNEL_ALIASES))
            raise ValueError(f"Unsupported channel {raw_value!r}. Supported values: {supported}")
        resolved.append(CHANNEL_ALIASES[normalized])
    return _dedupe(resolved)


def _resolve_article_code_column(frame: pd.DataFrame, channel_label: str) -> str:
    candidate_map = {
        "article_code": "Article_Code",
        "article code": "Article_Code",
        "sku": "Article_Code",
        "sku code": "Article_Code",
        "sku_code": "Article_Code",
    }
    normalized_columns = {
        str(column).strip().lower().replace("-", " ").replace("_", " "): str(column)
        for column in frame.columns
    }
    for normalized_name in candidate_map:
        if normalized_name in normalized_columns:
            return normalized_columns[normalized_name]
    raise ValueError(
        f"{channel_label} SKU list must contain an article code column such as 'Article_Code'."
    )


def _read_sku_filter(input_path: str, channel_label: str) -> pd.DataFrame:
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"{channel_label} SKU list not found: {path}")

    sku_filter = pd.read_csv(path, dtype=str)
    article_code_column = _resolve_article_code_column(sku_filter, channel_label)
    out = pd.DataFrame()
    out["Article_Code"] = (
        sku_filter[article_code_column]
        .fillna("")
        .astype(str)
        .str.strip()
    )
    out = out[out["Article_Code"] != ""].drop_duplicates().reset_index(drop=True)
    if out.empty:
        raise ValueError(f"{channel_label} SKU list is empty after cleaning: {path}")
    return out


def _build_query(start_date: str, end_date: str, site_codes: list[str], view_name: str) -> str:
    site_list = ", ".join(f"'{code}'" for code in site_codes)
    return f"""
SELECT
  s.posting_date,
  s.site_code,
  s.location,
  s.article_code,
  s.latest_article_description,
  SUM(s.stock_balance) AS stock_balance
FROM
  edpprod.t4_inventory.dm_daily_cogs_margin_and_inventory_performance s
JOIN {view_name} sku
  ON s.article_code = sku.Article_Code
WHERE
  s.posting_date BETWEEN DATE('{start_date}') AND DATE('{end_date}')
  AND s.site_code IN ({site_list})
GROUP BY
  s.posting_date,
  s.site_code,
  s.location,
  s.article_code,
  s.latest_article_description
ORDER BY
  s.posting_date,
  s.location,
  s.article_code
"""


def _ensure_parent_dir(file_path: str) -> None:
    Path(file_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


def _build_date_range_suffix(start_date: str, end_date: str) -> str:
    return f"{start_date}_to_{end_date}"


def _resolve_dated_output_path(file_path: str, start_date: str, end_date: str) -> str:
    path = Path(file_path)
    suffix = _build_date_range_suffix(start_date, end_date)
    return str(path.with_name(f"{path.stem} - {suffix}{path.suffix}"))


def _resolve_excel_writer_engine() -> str | None:
    if find_spec("openpyxl") is not None:
        return "openpyxl"
    if find_spec("xlsxwriter") is not None:
        return "xlsxwriter"
    return None


def _fetch_channel_snapshot(
    spark_session,
    *,
    channel_key: str,
    channel_config: dict[str, object],
) -> tuple[pd.DataFrame, dict[str, object]]:
    label = str(channel_config["label"])
    input_path = str(channel_config["input_path"])
    site_codes = _dedupe(list(channel_config["site_codes"]))
    view_name = f"sku_filter_{channel_key}"

    print(f"Reading {label} SKU list from: {input_path}")
    sku_filter = _read_sku_filter(input_path, label)
    spark_session.createDataFrame(sku_filter).createOrReplaceTempView(view_name)

    print(
        f"Querying {label} stock from {P_START_DATE} to {P_END_DATE} "
        f"for {len(site_codes)} site codes and {len(sku_filter)} SKUs..."
    )
    result_df = spark_session.sql(_build_query(P_START_DATE, P_END_DATE, site_codes, view_name))
    result_pdf = result_df.toPandas()

    metadata = {
        "channel_key": channel_key,
        "label": label,
        "sheet_name": str(channel_config["sheet_name"]),
        "input_path": input_path,
        "output_csv_path": str(channel_config["output_csv_path"]),
        "sku_count": int(len(sku_filter.index)),
        "site_code_count": int(len(site_codes)),
        "row_count": int(len(result_pdf.index)),
    }
    return result_pdf, metadata


def _build_summary_sheet(rows: list[dict[str, object]]) -> pd.DataFrame:
    return pd.DataFrame(rows)[
        [
            "channel_key",
            "label",
            "sheet_name",
            "sku_count",
            "site_code_count",
            "row_count",
            "input_path",
            "output_csv_path",
        ]
    ]


def main() -> None:
    spark_session = _require_spark_session()
    channel_keys = _resolve_channels_to_export(CHANNELS_TO_EXPORT)

    print(f"Channels to export: {', '.join(channel_keys)}")

    channel_results: dict[str, pd.DataFrame] = {}
    summary_rows: list[dict[str, object]] = []
    output_xlsx_path = _resolve_dated_output_path(OUTPUT_XLSX_PATH, P_START_DATE, P_END_DATE)

    for channel_key in channel_keys:
        channel_config = CHANNEL_EXPORTS[channel_key]
        result_pdf, metadata = _fetch_channel_snapshot(
            spark_session,
            channel_key=channel_key,
            channel_config=channel_config,
        )
        channel_results[channel_key] = result_pdf
        output_csv_path = _resolve_dated_output_path(
            str(channel_config["output_csv_path"]),
            P_START_DATE,
            P_END_DATE,
        )
        metadata["output_csv_path"] = output_csv_path
        summary_rows.append(metadata)

        _ensure_parent_dir(output_csv_path)
        print(f"Exporting {metadata['label']} CSV to: {output_csv_path}")
        result_pdf.to_csv(output_csv_path, index=False)

    summary_df = _build_summary_sheet(summary_rows)

    excel_engine = _resolve_excel_writer_engine()
    if excel_engine is None:
        print(
            "Skipping Excel workbook export because neither `openpyxl` nor "
            "`xlsxwriter` is installed on this Databricks cluster."
        )
    else:
        _ensure_parent_dir(output_xlsx_path)
        print(f"Exporting Excel workbook to: {output_xlsx_path} using {excel_engine}")
        with pd.ExcelWriter(output_xlsx_path, engine=excel_engine) as writer:
            summary_df.to_excel(writer, sheet_name="Summary", index=False)
            for channel_key in channel_keys:
                channel_config = CHANNEL_EXPORTS[channel_key]
                channel_results[channel_key].to_excel(
                    writer,
                    sheet_name=str(channel_config["sheet_name"]),
                    index=False,
                )

    print("Export completed successfully.")
    if excel_engine is not None:
        print(f"Workbook: {output_xlsx_path}")
    for row in summary_rows:
        print(
            f"{row['label']}: {row['row_count']} rows -> {row['output_csv_path']}"
        )


if __name__ == "__main__":
    main()
