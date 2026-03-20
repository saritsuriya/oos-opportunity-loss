from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v5_daily_oos_opportunity.data_loader_v5 import DataLoaderV5, InputPaths


def test_load_site_mapping_supports_include_workbook_sheet(tmp_path: Path) -> None:
    site_mapping_path = tmp_path / "site-mapping.xlsx"
    with pd.ExcelWriter(site_mapping_path) as writer:
        pd.DataFrame(
            {
                "Virtual Location": ["WH-BKK", "WH-BKK-DELIVERY"],
                "Priority": [1, 1],
                "Site": ["1110", "1112"],
                "Sloc": ["11", "1001"],
                "Excl. Safety": ["", ""],
                "Active": ["X", "X"],
                "Internal": ["WH-BKK", "WH-BKK-DL"],
            }
        ).to_excel(writer, sheet_name="Include", index=False)

    loader = DataLoaderV5(
        InputPaths(
            orders_path="orders.xlsx",
            daily_stock_path="stock.csv",
            site_mapping_path=str(site_mapping_path),
            product_path="sku.xlsx",
            channel_key="kingpowercn",
        )
    )

    result = loader.load_site_mapping()

    assert result.to_dict("records") == [
        {"site_code": "1110", "virtual_site": "wh-bkk"},
        {"site_code": "1112", "virtual_site": "wh-bkk-delivery"},
    ]


def test_load_site_mapping_filters_cn_master_workbook_to_cn_virtuals(tmp_path: Path) -> None:
    site_mapping_path = tmp_path / "site-mapping-cn-master.xlsx"
    with pd.ExcelWriter(site_mapping_path) as writer:
        pd.DataFrame(
            {
                "Virtual Location": [
                    "BKK-OUT",
                    "WH-BKK",
                    "WH-BKK-DELIVERY",
                    "WH-BKK-2",
                    "THT-FREEZONE",
                    "WH-ONLINE-DMALL",
                ],
                "Priority": [1, 1, 1, 1, 1, 1],
                "Site": ["26GA", "1110", "1113", "1110", "12ZB", "12ZC"],
                "Sloc": ["1", "11", "11", "11", "1", "10"],
                "Excl. Safety": ["", "", "", "", "", ""],
                "Active": ["X", "X", "X", "X", "X", "X"],
                "Internal": ["BKK-OUT", "WH-BKK", "WH-BKK-DL", "WH-BKK-2", "THT-FREEZ", "WH-DMALL"],
            }
        ).to_excel(writer, sheet_name="Include", index=False)

    loader = DataLoaderV5(
        InputPaths(
            orders_path="orders.xlsx",
            daily_stock_path="stock.csv",
            site_mapping_path=str(site_mapping_path),
            product_path="sku.xlsx",
            channel_key="kingpowercn",
        )
    )

    result = loader.load_site_mapping()

    assert result.to_dict("records") == [
        {"site_code": "26GA", "virtual_site": "bkk-out"},
        {"site_code": "1110", "virtual_site": "wh-bkk"},
        {"site_code": "1113", "virtual_site": "wh-bkk-delivery"},
    ]


def test_load_site_mapping_filters_tht_master_workbook_and_expands_online_aliases(tmp_path: Path) -> None:
    site_mapping_path = tmp_path / "site-mapping-tht-master.xlsx"
    with pd.ExcelWriter(site_mapping_path) as writer:
        pd.DataFrame(
            {
                "Virtual Location": [
                    "WH-ONLINE-DMALL",
                    "WH-ONLINE-JD",
                    "THT-FREEZONE",
                    "THT-ONLINE-WH",
                    "WH-ONLINE-THT",
                    "WH-ONLINE-TIKTOK",
                    "BKK-OUT",
                ],
                "Priority": [1, 1, 1, 1, 1, 1, 1],
                "Site": ["12ZC", "12ZD", "12ZB", "12ZA", "12ZA", "13ZE", "26GA"],
                "Sloc": ["10", "10", "1", "10", "10", "10", "1"],
                "Excl. Safety": ["", "", "", "", "", "", ""],
                "Active": ["X", "X", "X", "X", "X", "X", "X"],
                "Internal": ["WH-DMALL", "WH-JD", "THT-FREEZ", "WH-THT2", "WH-THT", "WH-TIKTOK", "BKK-OUT"],
            }
        ).to_excel(writer, sheet_name="Include", index=False)

    loader = DataLoaderV5(
        InputPaths(
            orders_path="orders.xlsx",
            daily_stock_path="stock.csv",
            site_mapping_path=str(site_mapping_path),
            product_path="sku.xlsx",
            channel_key="tht",
        )
    )

    result = loader.load_site_mapping()

    assert sorted(result["virtual_site"].unique().tolist()) == [
        "dmall-online-wh",
        "jd-online-wh",
        "tht-freezone",
        "tht-online-wh",
        "wh-online-dmall",
        "wh-online-jd",
        "wh-online-tht",
        "wh-online-tiktok",
    ]
    assert {"site_code": "12ZC", "virtual_site": "dmall-online-wh"} in result.to_dict("records")
    assert {"site_code": "12ZD", "virtual_site": "jd-online-wh"} in result.to_dict("records")
    assert "bkk-out" not in set(result["virtual_site"])


def test_load_orders_uses_storage_location_for_kingpowercn(tmp_path: Path) -> None:
    orders_path = tmp_path / "orders-cn.xlsx"
    with pd.ExcelWriter(orders_path) as writer:
        pd.DataFrame([["WEB-CN SALES"]]).to_excel(writer, sheet_name="WEB-CN", index=False, header=False)
        pd.DataFrame(
            {
                "DATE": ["01.02.2026", "15.02.2026"],
                "ORDER NO": ["ORDER-1", "ORDER-2"],
                "SKU": ["SKU-1", "SKU-2"],
                "DESCRIPTION": ["Bag", "Watch"],
                "QTY": [2, 4],
                "GROSS": [100, 200],
                "NET": [90, 180],
                "Storage Location": ["WH-BKK", "WH-BKK-DELIVERY"],
            }
        ).to_excel(writer, sheet_name="WEB-CN", index=False, startrow=1)

    loader = DataLoaderV5(
        InputPaths(
            orders_path=str(orders_path),
            daily_stock_path="stock.csv",
            site_mapping_path="site-mapping.xlsx",
            product_path="sku.xlsx",
            channel_key="kingpowercn",
        )
    )

    result = loader.load_orders()

    assert list(result["stock_code"]) == ["wh-bkk", "wh-bkk-delivery"]
    assert list(result["quantity"]) == [2.0, 4.0]
    assert list(result["net"]) == [90.0, 180.0]


def test_load_product_universe_merges_cn_product_sheets_without_changing_logic(tmp_path: Path) -> None:
    product_path = tmp_path / "sku-cn.xlsx"
    with pd.ExcelWriter(product_path) as writer:
        pd.DataFrame([["click&collect"]]).to_excel(
            writer,
            sheet_name="click&collect",
            index=False,
            header=False,
        )
        pd.DataFrame(
            {
                "SKU CODE": ["SKU-1", "SKU-2"],
                "DESCRIPTION": ["Bag", "Watch"],
                "商品名称": ["Bag CN", "Watch CN"],
                "WEB STATUS": ["HIDE", "LIVE"],
            }
        ).to_excel(writer, sheet_name="click&collect", index=False, startrow=1)
        pd.DataFrame([["HomeDelivery"]]).to_excel(
            writer,
            sheet_name="HomeDelivery",
            index=False,
            header=False,
        )
        pd.DataFrame(
            {
                "SKU CODE": ["SKU-1", "SKU-3"],
                "DESCRIPTION": ["Bag", "Wallet"],
                "商品名称": ["Bag CN HD", "Wallet CN"],
                "WEB STATUS": ["LIVE", "LIVE"],
            }
        ).to_excel(writer, sheet_name="HomeDelivery", index=False, startrow=1)

    loader = DataLoaderV5(
        InputPaths(
            orders_path="orders.xlsx",
            daily_stock_path="stock.csv",
            site_mapping_path="site-mapping.xlsx",
            product_path=str(product_path),
            channel_key="kingpowercn",
        )
    )

    result = loader.load_product_universe()

    assert result.to_dict("records") == [
        {
            "sku": "SKU-1",
            "product_name": "Bag CN HD",
            "status": "live",
            "excluded_prefix_p": False,
        },
        {
            "sku": "SKU-2",
            "product_name": "Watch CN",
            "status": "live",
            "excluded_prefix_p": False,
        },
        {
            "sku": "SKU-3",
            "product_name": "Wallet CN",
            "status": "live",
            "excluded_prefix_p": False,
        },
    ]
