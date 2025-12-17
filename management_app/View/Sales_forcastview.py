from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
from django.db.models import F, Sum, Q
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from management_app.models import OrderLinesModel
import math


class ProductNameFilter(django_filters.FilterSet):
    product_name = django_filters.CharFilter(method='filter_product_name')

    class Meta:
        model = OrderLinesModel
        fields = ['product_name']

    def filter_product_name(self, queryset, name, value):
        """
        Custom filter to allow multiple product names, separated by commas.
        """
        product_names = value.split(',')
        query = Q()
        for product in product_names:
            query |= Q(product__name__icontains=product)
        return queryset.filter(query)


class SalesForecastAPIView(ListAPIView):
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ProductNameFilter

    def list(self, request, *args, **kwargs):
        try:
            # ---------------------------------------------------
            # 1. Fetch sales order data
            # ---------------------------------------------------
            order_lines = (
                OrderLinesModel.objects
                .filter(order__sale_status='Sales Order')
                .annotate(line_total=F('quantity') * F('selling_price'))
                .values('order__order_date', 'product__name')
                .annotate(
                    total_quantity=Sum('quantity'),
                    total_sales=Sum('line_total')
                ).exclude(product__name__in=['GST', 'PARCEL PACKING CHARGES'])
            )

            # Apply filters
            for backend in self.filter_backends:
                order_lines = backend().filter_queryset(request, order_lines, self)

            if not order_lines.exists():
                return Response(
                    {"status": False, "message": "No sales data available."},
                    status=HTTP_400_BAD_REQUEST
                )

            # ---------------------------------------------------
            # 2. Convert to DataFrame & prepare monthly data
            # ---------------------------------------------------
            df = pd.DataFrame(order_lines)
            df.rename(columns={
                'order__order_date': 'date',
                'product__name': 'product',
                'total_quantity': 'quantity',
                'total_sales': 'sales_amount'
            }, inplace=True)

            df['date'] = pd.to_datetime(df['date'])
            df['month'] = df['date'].dt.to_period('M')

            monthly_data = (
                df.groupby(['product', 'month'])
                .agg({'quantity': 'sum', 'sales_amount': 'sum'})
                .reset_index()
            )

            # Keep products with at least 2 months of data
            products_to_forecast = [
                p for p in monthly_data['product'].unique()
                if monthly_data[monthly_data['product'] == p].shape[0] >= 2
            ]

            if not products_to_forecast:
                return Response(
                    {"status": False, "message": "Insufficient data for forecasting."},
                    status=HTTP_400_BAD_REQUEST
                )

            monthly_data = monthly_data[monthly_data['product'].isin(products_to_forecast)]

            # ---------------------------------------------------
            # 3. Forecast logic
            # ---------------------------------------------------
            forecast_periods = 6
            results = []
            product_forecast_sales = {}

            for product in products_to_forecast:
                product_data = (
                    monthly_data[monthly_data['product'] == product]
                    .sort_values(by='month')
                )

                product_data['quantity_trend'] = product_data['quantity'].diff().fillna(0)
                avg_quantity_trend = product_data['quantity_trend'].mean()
                avg_price = product_data['sales_amount'].sum() / product_data['quantity'].sum()

                forecast = {}
                last_quantity = product_data.iloc[-1]['quantity']
                last_date = datetime.now().replace(day=1)
                total_product_sales = 0

                for _ in range(forecast_periods):
                    last_date += relativedelta(months=1)
                    year = last_date.year
                    month = last_date.strftime('%B')

                    last_quantity += avg_quantity_trend
                    last_quantity = max(0, last_quantity)
                    last_sales = math.ceil(last_quantity * avg_price * 100) / 100

                    forecast.setdefault(year, {})
                    forecast[year][month] = {
                        "quantity": int(last_quantity),
                        "sales_amount": round(last_sales, 2)
                    }

                    total_product_sales += last_sales

                results.append({
                    "product_name": product,
                    "forecast": forecast
                })

                product_forecast_sales[product] = total_product_sales

            # ---------------------------------------------------
            # 4. Select TOP 10 products by forecasted sales
            # ---------------------------------------------------
            top_10_products = sorted(
                product_forecast_sales.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]

            top_10_names = {p[0] for p in top_10_products}
            results = [r for r in results if r["product_name"] in top_10_names]

            if not results:
                return Response(
                    {"status": False, "message": "No top products found."},
                    status=HTTP_400_BAD_REQUEST
                )

            # ---------------------------------------------------
            # 5. Build TOTAL forecast row (Top 10 only)
            # ---------------------------------------------------
            total_forecast = {}

            for item in results:
                for year, months in item["forecast"].items():
                    total_forecast.setdefault(year, {})
                    for month, values in months.items():
                        total_forecast[year].setdefault(
                            month, {"quantity": 0, "sales_amount": 0.0}
                        )
                        total_forecast[year][month]["quantity"] += values["quantity"]
                        total_forecast[year][month]["sales_amount"] = math.ceil(
                            (total_forecast[year][month]["sales_amount"] + values["sales_amount"]) * 100
                        ) / 100

            results.insert(0, {
                "product_name": "Top 10 Total",
                "forecast": total_forecast
            })

            return Response(
                {"status": True, "data": {"forecast": results}},
                status=HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"status": False, "message": str(e)},
                status=HTTP_500_INTERNAL_SERVER_ERROR
            )
