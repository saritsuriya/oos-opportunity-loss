from dataclasses import dataclass
from pathlib import Path
import re
from typing import Dict

import pandas as pd

from channel_profiles import (
    CHANNEL_TH,
    get_channel_profile,
    get_site_mapping_virtual_expansions,
    get_site_mapping_virtual_sites,
    normalize_channel_key,
    normalize_virtual_site,
)


@dataclass
class InputPaths:
    orders_path: str
    daily_stock_path: str
    site_mapping_path: str
    product_path: str
    channel_key: str = CHANNEL_TH


class DataLoaderV5:
    """Load and normalize sources for daily OOS opportunity calculation."""

    @staticmethod
    def clean_id(value: object) -> str:
        s = str(value).strip()
        s = s.replace('"', "").replace("'", "").replace("=", "")
        s = re.sub(r"\.0$", "", s)
        s = re.sub(r"\s+", "", s)
        return s

    @staticmethod
    def clean_site(value: object) -> str:
        s = str(value).strip().lower()
        return re.sub(r"\s+", "", s)

    @staticmethod
    def is_excluded_sku(sku: str) -> bool:
        return str(sku).lower().startswith("p")

    def __init__(self, paths: InputPaths):
        self.paths = paths
        self.channel_key = normalize_channel_key(paths.channel_key)
        self.channel_profile = get_channel_profile(self.channel_key)

    @staticmethod
    def _parse_datetime(series: pd.Series) -> pd.Series:
        """Parse mixed date strings by picking the parse with better coverage."""
        s = series.astype(str)
        a = pd.to_datetime(s, errors="coerce", dayfirst=False)
        b = pd.to_datetime(s, errors="coerce", dayfirst=True)
        return b if b.notna().sum() > a.notna().sum() else a

    def load_site_mapping(self) -> pd.DataFrame:
        path = Path(self.paths.site_mapping_path)
        if not path.exists():
            raise FileNotFoundError(f"Site mapping not found: {path}")

        if path.suffix.lower() in [".xlsx", ".xlsm", ".xls"]:
            df = pd.read_excel(path, sheet_name="Include")
        else:
            df = pd.read_csv(path)
        required = ["Virtual Location", "Site", "Active"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Site mapping missing columns: {missing}")

        out = df.copy()
        out["Active"] = out["Active"].astype(str).str.upper().str.strip()
        out = out[out["Active"] == "X"].copy()
        out["site_code"] = out["Site"].map(self.clean_id)
        out["virtual_site"] = out["Virtual Location"].map(normalize_virtual_site)
        out = out[out["site_code"] != ""].copy()
        out = out[out["virtual_site"] != ""].copy()
        out = self._expand_site_mapping_virtual_sites(out[["site_code", "virtual_site"]])
        allowed_virtual_sites = set(get_site_mapping_virtual_sites(self.channel_key))
        if allowed_virtual_sites:
            out = out[out["virtual_site"].isin(allowed_virtual_sites)].copy()
        if out.empty:
            msg = (
                f"Site mapping does not contain any active rows for {self.channel_profile.label}. "
                "Check that the uploaded workbook matches the selected channel."
            )
            raise ValueError(msg)
        out = out.drop_duplicates(subset=["site_code", "virtual_site"]).reset_index(drop=True)
        return out[["site_code", "virtual_site"]]

    def load_product_universe(self) -> pd.DataFrame:
        path = Path(self.paths.product_path)
        if not path.exists():
            raise FileNotFoundError(f"Product file not found: {path}")

        if self.channel_key == CHANNEL_TH:
            df = pd.read_csv(path)
            if "skuNo" not in df.columns:
                raise ValueError("Product file must contain 'skuNo'")

            out = pd.DataFrame()
            out["sku"] = df["skuNo"].map(self.clean_id)
            out["product_name"] = df["productName"].astype(str) if "productName" in df.columns else ""
            out["status"] = (
                df["status"].astype(str).map(self.clean_id).str.lower() if "status" in df.columns else "unknown"
            )
            out = out[out["sku"] != ""].copy()
            out["excluded_prefix_p"] = out["sku"].map(self.is_excluded_sku)
            return out.drop_duplicates(subset=["sku"]).reset_index(drop=True)

        workbook = pd.ExcelFile(path)
        missing_sheets = [sheet for sheet in self.channel_profile.product_sheets if sheet not in workbook.sheet_names]
        if missing_sheets:
            raise ValueError(f"Product workbook missing sheets for {self.channel_profile.label}: {missing_sheets}")

        frames: list[pd.DataFrame] = []
        for sheet_name in self.channel_profile.product_sheets:
            df = pd.read_excel(path, sheet_name=sheet_name, header=1)
            missing = [column for column in ["SKU CODE", "WEB STATUS"] if column not in df.columns]
            if missing:
                raise ValueError(f"Product workbook sheet '{sheet_name}' missing columns: {missing}")
            out = pd.DataFrame()
            out["sku"] = df["SKU CODE"].map(self.clean_id)
            out["product_name"] = self._select_product_name(df)
            out["status"] = df["WEB STATUS"].astype(str).map(self.clean_id).str.lower()
            out["sheet_name"] = sheet_name
            frames.append(out)

        merged = pd.concat(frames, ignore_index=True)
        merged = merged[merged["sku"] != ""].copy()
        merged["status_rank"] = merged["status"].map({"live": 2, "hide": 1}).fillna(0)
        merged["name_rank"] = merged["product_name"].astype(str).str.strip().ne("").astype(int)
        merged = merged.sort_values(
            ["sku", "status_rank", "name_rank", "sheet_name"],
            ascending=[True, False, False, True],
        )
        merged = merged.drop_duplicates(subset=["sku"], keep="first").reset_index(drop=True)
        merged["excluded_prefix_p"] = merged["sku"].map(self.is_excluded_sku)
        return merged[["sku", "product_name", "status", "excluded_prefix_p"]]

    def load_orders(self) -> pd.DataFrame:
        path = Path(self.paths.orders_path)
        if not path.exists():
            raise FileNotFoundError(f"OrderDetail not found: {path}")

        df = self._read_orders_source(path)

        out = pd.DataFrame()
        out["purchase_date"] = self._parse_datetime(df["Purchase Date"])
        out["sku"] = df["Sku"].map(self.clean_id)
        out["stock_code"] = df["stock"].astype(str).str.lower().str.strip()
        # Normalize to canonical virtual labels used in this project.
        out["stock_code"] = out["stock_code"].replace({"wh-bkk-2": "wh-bkk"})
        out["quantity"] = pd.to_numeric(
            df["Quantity"].astype(str).str.replace(",", "", regex=False), errors="coerce"
        ).fillna(0.0)
        out["gross"] = pd.to_numeric(
            df["Gross"].astype(str).str.replace(",", "", regex=False), errors="coerce"
        ).fillna(0.0)
        out["net"] = pd.to_numeric(
            df["Net"].astype(str).str.replace(",", "", regex=False), errors="coerce"
        ).fillna(0.0)
        out["product_name"] = df["Product Name"].astype(str)

        out = out[out["purchase_date"].notna()].copy()
        out = out[out["sku"] != ""].copy()
        out["excluded_prefix_p"] = out["sku"].map(self.is_excluded_sku)
        return out

    def load_daily_stock(self) -> pd.DataFrame:
        path = Path(self.paths.daily_stock_path)
        if not path.exists():
            raise FileNotFoundError(f"Daily stock file not found: {path}")

        df = pd.read_csv(path)
        required = ["posting_date", "site_code", "article_code", "stock_balance"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Daily stock file missing columns: {missing}")

        out = pd.DataFrame()
        out["posting_date"] = pd.to_datetime(df["posting_date"], errors="coerce").dt.normalize()
        out["site_code"] = df["site_code"].astype(str).str.strip()
        out["sku"] = df["article_code"].map(self.clean_id)
        out["stock_balance"] = pd.to_numeric(df["stock_balance"], errors="coerce").fillna(0.0)
        if "location" in df.columns:
            out["location"] = df["location"].astype(str)
        else:
            out["location"] = ""

        out = out[out["posting_date"].notna()].copy()
        out = out[out["sku"] != ""].copy()
        out["excluded_prefix_p"] = out["sku"].map(self.is_excluded_sku)
        return out

    @staticmethod
    def site_location_mapping() -> Dict[str, str]:
        # Canonical labels aligned to OrderDetail stock codes.
        return {
            "wh-bkk": "wh-bkk",
            "bkk-out": "bkk-out",
            "dmk-out": "dmk-out",
            "hkt-out": "hkt-out",
            "cnx-out": "cnx-out",
            "bs-hkt": "bs-hkt",
            "bs-cnx": "bs-cnx",
            "mjets-out": "mjets-out",
        }

    def _expand_site_mapping_virtual_sites(self, df: pd.DataFrame) -> pd.DataFrame:
        expansions = get_site_mapping_virtual_expansions(self.channel_key)
        if not expansions:
            return df

        frames = [df]
        for source_virtual_site, expanded_virtual_site in expansions:
            source_rows = df[df["virtual_site"] == source_virtual_site]
            if source_rows.empty:
                continue
            expanded_rows = source_rows.copy()
            expanded_rows["virtual_site"] = expanded_virtual_site
            frames.append(expanded_rows)
        return pd.concat(frames, ignore_index=True)

    def _read_orders_source(self, path: Path) -> pd.DataFrame:
        if self.channel_key == CHANNEL_TH:
            if path.suffix.lower() in [".xlsx", ".xlsm", ".xls"]:
                df = pd.read_excel(path)
            else:
                # Original export format is UTF-16 TSV.
                df = pd.read_csv(path, encoding="utf-16", sep="\t")
            required = ["Purchase Date", "Sku", "stock", "Quantity", "Gross", "Net", "Product Name"]
            missing = [c for c in required if c not in df.columns]
            if missing:
                raise ValueError(f"OrderDetail missing columns: {missing}")
            return df

        sheet_name = self.channel_profile.sales_sheet
        if path.suffix.lower() not in [".xlsx", ".xlsm", ".xls"]:
            raise ValueError(f"{self.channel_profile.label} orders must be uploaded as an Excel workbook")
        df = pd.read_excel(path, sheet_name=sheet_name, header=1)
        required = ["DATE", "SKU", "DESCRIPTION", "QTY", "GROSS", "NET", "Storage Location"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Order workbook sheet '{sheet_name}' missing columns: {missing}")
        return df.rename(
            columns={
                "DATE": "Purchase Date",
                "SKU": "Sku",
                "DESCRIPTION": "Product Name",
                "QTY": "Quantity",
                "GROSS": "Gross",
                "NET": "Net",
                "Storage Location": "stock",
            }
        )

    @staticmethod
    def _select_product_name(df: pd.DataFrame) -> pd.Series:
        for column in ("商品名称", "中文名", "DESCRIPTION", "英文名", "productName"):
            if column in df.columns:
                series = df[column].fillna("").astype(str)
                if series.str.strip().ne("").any():
                    return series
        return pd.Series([""] * len(df))
