"""Intrinio Index Historical Model."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from dateutil.relativedelta import relativedelta
from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.index_historical import (
    IndexHistoricalData,
    IndexHistoricalQueryParams,
)
from openbb_core.provider.utils.descriptions import QUERY_DESCRIPTIONS
from openbb_core.provider.utils.helpers import get_querystring
from openbb_intrinio.utils.helpers import get_data_many
from pydantic import Field, NonNegativeInt


class IntrinioIndexHistoricalQueryParams(IndexHistoricalQueryParams):
    """Intrinio Index Historical Query.

    Source: https://docs.intrinio.com/documentation/web_api/get_stock_market_index_historical_data_v2
    """

    tag: Optional[str] = Field(default="level", description="Index tag.")
    type: Optional[str] = Field(
        default=None,
        description="Index type.",
    )
    sort: Literal["asc", "desc"] = Field(
        default="desc",
        description="Sort order.",
        alias="sort_order",
    )
    limit: NonNegativeInt = Field(
        default=1000,
        description=QUERY_DESCRIPTIONS.get("limit", ""),
        alias="page_size",
    )


class IntrinioIndexHistoricalData(IndexHistoricalData):
    """Intrinio Index Historical Data."""

    __alias_dict__ = {"close": "value"}


class IntrinioIndexHistoricalFetcher(
    Fetcher[
        IntrinioIndexHistoricalQueryParams,
        List[IntrinioIndexHistoricalData],
    ]
):
    """Transform the query, extract and transform the data from the Intrinio endpoints."""

    @staticmethod
    def transform_query(params: Dict[str, Any]) -> IntrinioIndexHistoricalQueryParams:
        """Transform the query params."""
        transformed_params = params

        now = datetime.now().date()
        if params.get("start_date") is None:
            transformed_params["start_date"] = now - relativedelta(years=1)

        if params.get("end_date") is None:
            transformed_params["end_date"] = now

        return IntrinioIndexHistoricalQueryParams(**transformed_params)

    @staticmethod
    async def aextract_data(
        query: IntrinioIndexHistoricalQueryParams,
        credentials: Optional[Dict[str, str]],
        **kwargs: Any,
    ) -> List[Dict]:
        """Return the raw data from the Intrinio endpoint."""
        api_key = credentials.get("intrinio_api_key") if credentials else ""

        base_url = "https://api-v2.intrinio.com/indices/stock_market"
        query_str = get_querystring(query.model_dump(by_alias=True), ["symbol", "tag"])
        url = f"{base_url}/{query.symbol}/historical_data/{query.tag}?{query_str}&api_key={api_key}"

        return await get_data_many(url, "historical_data", **kwargs)

    @staticmethod
    def transform_data(
        query: IntrinioIndexHistoricalQueryParams,  # pylint: disable=unused-argument
        data: List[Dict],
        **kwargs: Any,
    ) -> List[IntrinioIndexHistoricalData]:
        """Return the transformed data."""
        return [IntrinioIndexHistoricalData.model_validate(d) for d in data]
