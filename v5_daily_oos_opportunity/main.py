import argparse
import calendar
import os

import pandas as pd

from channel_profiles import (
    CHANNEL_TH,
    get_channel_profiles,
    get_channel_profile,
    normalize_channel_key,
)
from analyzer_v5 import DailyOOSOpportunityV5, ModelConfig
from data_loader_v5 import DataLoaderV5, InputPaths
from reporter_v5 import ReporterV5


def default_paths(base_dir: str, eval_year: int, eval_month: int, channel_key: str) -> InputPaths:
    data_dir = os.path.join(base_dir, "data")
    channel_profile = get_channel_profile(channel_key)
    if channel_key == CHANNEL_TH:
        orders_default = os.path.join(data_dir, "OrderDetailTilFeb.csv")
        if not os.path.exists(orders_default):
            orders_default = os.path.join(data_dir, "OrderDetail.csv")
        month_abbr = calendar.month_abbr[eval_month]
        daily_stock_default = os.path.join(data_dir, f"Earth - Daily Stock by Location {month_abbr} {eval_year}.csv")
        if not os.path.exists(daily_stock_default):
            daily_stock_default = os.path.join(data_dir, "Earth - Daily Stock by Location Jan 2026.csv")
        site_mapping_path = os.path.join(data_dir, "Site mapping.csv")
        product_path = os.path.join(data_dir, "product-2026-03-02-10-07.csv")
    else:
        orders_default = os.path.join(data_dir, f"{channel_profile.label} Order Details.xlsx")
        daily_stock_default = os.path.join(data_dir, f"{channel_profile.label} Daily Stock.csv")
        site_mapping_path = os.path.join(data_dir, f"{channel_profile.label} Site Mapping.xlsx")
        product_path = os.path.join(data_dir, f"{channel_profile.label} SKU List.xlsx")
    return InputPaths(
        orders_path=orders_default,
        daily_stock_path=daily_stock_default,
        site_mapping_path=site_mapping_path,
        product_path=product_path,
        channel_key=channel_key,
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="V5 Daily OOS Opportunity Calculator")
    p.add_argument(
        "--channel",
        type=str,
        default=CHANNEL_TH,
        choices=[profile.key for profile in get_channel_profiles()],
        help="Channel profile used to normalize inputs before V5 runs",
    )
    p.add_argument("--orders", type=str, default=None, help="Path to OrderDetail.csv")
    p.add_argument(
        "--orders-actual",
        type=str,
        default=None,
        help="Optional additional order file (e.g. current month) appended to --orders",
    )
    p.add_argument("--daily-stock", type=str, default=None, help="Path to daily stock CSV")
    p.add_argument("--site-map", type=str, default=None, help="Path to Site mapping CSV")
    p.add_argument("--product", type=str, default=None, help="Path to product universe CSV")
    p.add_argument("--eval-year", type=int, default=2026, help="Evaluation year")
    p.add_argument("--eval-month", type=int, default=1, help="Evaluation month")
    p.add_argument(
        "--baseline-months",
        type=int,
        default=6,
        help="Recent history window in months before the evaluation month",
    )
    p.add_argument(
        "--fallback-months",
        type=int,
        default=6,
        help="Older fallback history window in months used only when recent history is zero",
    )
    p.add_argument("--output", type=str, default=None, help="Output xlsx path")
    return p


def main() -> None:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    args = build_parser().parse_args()
    channel_key = normalize_channel_key(args.channel)
    defaults = default_paths(base_dir, args.eval_year, args.eval_month, channel_key)

    paths = InputPaths(
        orders_path=args.orders or defaults.orders_path,
        daily_stock_path=args.daily_stock or defaults.daily_stock_path,
        site_mapping_path=args.site_map or defaults.site_mapping_path,
        product_path=args.product or defaults.product_path,
        channel_key=channel_key,
    )

    if args.output:
        output_path = args.output
    else:
        period = f"{args.eval_year}-{args.eval_month:02d}"
        out_dir = os.path.join(base_dir, "output", period)
        output_path = os.path.join(out_dir, f"OOS_Opportunity_Lost_{period}_V5.xlsx")

    print("=== V5 Daily OOS Opportunity ===")
    print(f"channel    : {get_channel_profile(channel_key).label}")
    print(f"orders     : {paths.orders_path}")
    if args.orders_actual:
        print(f"orders +   : {args.orders_actual}")
    print(f"daily stock: {paths.daily_stock_path}")
    print(f"site map   : {paths.site_mapping_path}")
    print(f"product    : {paths.product_path}")
    print(f"output     : {output_path}")

    loader = DataLoaderV5(paths)
    site_map_df = loader.load_site_mapping()
    product_df = loader.load_product_universe()
    orders_df = loader.load_orders()
    if args.orders_actual:
        extra_paths = InputPaths(
            orders_path=args.orders_actual,
            daily_stock_path=paths.daily_stock_path,
            site_mapping_path=paths.site_mapping_path,
            product_path=paths.product_path,
            channel_key=channel_key,
        )
        extra_loader = DataLoaderV5(extra_paths)
        extra_orders_df = extra_loader.load_orders()
        orders_df = (
            pd.concat([orders_df, extra_orders_df], ignore_index=True)
            .drop_duplicates()
            .reset_index(drop=True)
        )
    daily_df = loader.load_daily_stock()

    model = DailyOOSOpportunityV5(
        product_df=product_df,
        orders_df=orders_df,
        daily_stock_df=daily_df,
        site_map_df=site_map_df,
        config=ModelConfig(
            eval_year=args.eval_year,
            eval_month=args.eval_month,
            baseline_recent_months=args.baseline_months,
            baseline_fallback_months=args.fallback_months,
        ),
    )
    detail, qa_summary, unmapped_site = model.run()

    reporter = ReporterV5()
    result = reporter.generate(detail, qa_summary, unmapped_site, output_path)

    print(f"detail rows            : {len(detail):,}")
    print(f"lost value net raw     : {detail['lost_value_net_raw'].sum():,.2f}")
    print(f"report generated       : {result}")


if __name__ == "__main__":
    main()
