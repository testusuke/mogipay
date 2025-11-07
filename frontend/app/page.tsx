'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { apiClient } from '@/lib/api';
import type {
  SalesSummary,
  InventoryStatus,
  FinancialSummary,
} from '@/lib/api/types';

/**
 * Dashboard Data Interface
 */
interface DashboardData {
  sales: SalesSummary | null;
  inventory: InventoryStatus | null;
  financial: FinancialSummary | null;
}

/**
 * Sales Dashboard Page Component
 *
 * Requirements:
 * - 5.1-5.5: 売上進捗管理
 * - 6.1-6.5: 損益計算
 * - 7.1-7.2, 7.6-7.7: 在庫管理
 */
export default function Home() {
  const [data, setData] = useState<DashboardData>({
    sales: null,
    inventory: null,
    financial: null,
  });
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  /**
   * Fetch dashboard data from API
   */
  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [sales, inventory, financial] = await Promise.all([
        apiClient.getSalesSummary(),
        apiClient.getInventoryStatus(),
        apiClient.getFinancialSummary(),
      ]);

      setData({ sales, inventory, financial });
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
      setError('データの取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Initial data fetch and polling setup
   */
  useEffect(() => {
    fetchDashboardData();

    // Poll every 5 seconds
    const interval = setInterval(fetchDashboardData, 5000);

    return () => clearInterval(interval);
  }, []);

  if (loading && !data.sales && !data.inventory && !data.financial) {
    return (
      <div className="container mx-auto p-8">
        <div className="flex items-center justify-center h-64">
          <p className="text-lg text-muted-foreground">読み込み中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-8">
        <div className="flex items-center justify-center h-64">
          <p className="text-lg text-destructive">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-8 space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-4xl font-bold">売上ダッシュボード</h1>
        <p className="text-muted-foreground mt-2">
          売上・在庫・損益の状況をリアルタイムで確認
        </p>
      </div>

      {/* Financial Summary Section */}
      {data.financial && (
        <div className="space-y-4">
          <h2 className="text-2xl font-bold">損益計算</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Total Cost Card */}
            <Card>
              <CardHeader>
                <CardTitle>総初期費用</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">
                  ¥{data.financial.total_cost.toLocaleString()}
                </p>
              </CardContent>
            </Card>

            {/* Total Revenue Card */}
            <Card>
              <CardHeader>
                <CardTitle>総売上</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">
                  ¥{data.financial.total_revenue.toLocaleString()}
                </p>
              </CardContent>
            </Card>

            {/* Profit Card */}
            <Card>
              <CardHeader>
                <CardTitle>損益</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <p
                    className={`text-3xl font-bold ${
                      data.financial.profit >= 0
                        ? 'text-green-600'
                        : 'text-red-600'
                    }`}
                  >
                    {data.financial.profit >= 0 ? '+' : ''}¥
                    {data.financial.profit.toLocaleString()}
                  </p>
                  {data.financial.break_even_achieved && (
                    <Badge variant="default" className="bg-green-600">
                      損益分岐点達成
                    </Badge>
                  )}
                  <p className="text-sm text-muted-foreground">
                    利益率: {data.financial.profit_rate.toFixed(1)}%
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Inventory Status Section */}
      {data.inventory && (
        <div className="space-y-4">
          <h2 className="text-2xl font-bold">在庫状況</h2>
          <Card>
            <CardHeader>
              <CardTitle>商品別在庫 (単品商品のみ)</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {data.inventory.products
                  .filter((p) => p.product_type === 'single')
                  .map((product) => {
                    const soldCount =
                      product.initial_stock - product.current_stock;
                    const salesRate =
                      product.initial_stock > 0
                        ? (soldCount / product.initial_stock) * 100
                        : 0;
                    const remainingRate =
                      product.initial_stock > 0
                        ? (product.current_stock / product.initial_stock) * 100
                        : 0;

                    // Color logic for sales progress
                    let indicatorColor = 'bg-gray-300'; // Default: not selling well
                    let backgroundColor = 'bg-gray-100'; // Default background
                    if (product.is_out_of_stock) {
                      indicatorColor = 'bg-gray-400'; // Sold out
                      backgroundColor = 'bg-gray-50';
                    } else if (remainingRate <= 20) {
                      indicatorColor = 'bg-red-500'; // Critical: Almost sold out
                      backgroundColor = 'bg-red-50';
                    } else if (remainingRate <= 50) {
                      indicatorColor = 'bg-yellow-500'; // Warning: Low stock
                      backgroundColor = 'bg-yellow-50';
                    } else if (salesRate >= 30) {
                      indicatorColor = 'bg-green-500'; // Good: Selling well
                      backgroundColor = 'bg-green-50';
                    }

                    return (
                      <div key={product.id} className="space-y-2">
                        {/* Product name and stock info */}
                        <div className="flex items-center justify-between text-sm">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{product.name}</span>
                            {product.is_out_of_stock && (
                              <Badge variant="destructive" className="text-xs">
                                完売
                              </Badge>
                            )}
                            {!product.is_out_of_stock && salesRate < 10 && (
                              <Badge variant="outline" className="text-xs">
                                要注意
                              </Badge>
                            )}
                          </div>
                          <div className="flex items-center gap-4 text-muted-foreground">
                            <span>
                              販売: {soldCount}/{product.initial_stock}
                            </span>
                            <span className="font-medium">
                              {salesRate.toFixed(0)}%
                            </span>
                          </div>
                        </div>

                        {/* Progress bar */}
                        <div className="relative">
                          <Progress
                            value={salesRate}
                            className={`h-6 ${backgroundColor}`}
                            indicatorClassName={indicatorColor}
                          />
                          {/* Remaining stock overlay */}
                          <div className="absolute top-0 left-0 right-0 bottom-0 flex items-center justify-between px-3 text-xs font-medium">
                            <span className="text-white drop-shadow-md">
                              販売済み: {soldCount}個 ({salesRate.toFixed(0)}%)
                            </span>
                            <span className="text-gray-700 font-semibold">
                              残り: {product.current_stock}個
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
              </div>

              {/* Legend */}
              <div className="mt-6 pt-4 border-t grid grid-cols-2 md:grid-cols-4 gap-3 text-xs text-muted-foreground">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-red-500 rounded"></div>
                  <span>残り20%以下</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-yellow-500 rounded"></div>
                  <span>残り20-50%</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-green-500 rounded"></div>
                  <span>順調に販売中</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-gray-300 rounded"></div>
                  <span>販売が少ない</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Out of Stock Products */}
          {data.inventory.products.some((p) => p.is_out_of_stock) && (
            <Card>
              <CardHeader>
                <CardTitle>在庫切れ商品</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {data.inventory.products
                    .filter((p) => p.is_out_of_stock)
                    .map((product) => (
                      <Badge key={product.id} variant="destructive">
                        {product.name}
                        {product.product_type === 'set' && ' (セット)'}
                      </Badge>
                    ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
