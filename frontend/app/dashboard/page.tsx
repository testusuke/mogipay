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
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

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
export default function DashboardPage() {
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

      {/* Sales Summary Section */}
      {data.sales && (
        <div className="space-y-4">
          <h2 className="text-2xl font-bold">売上進捗</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Total Revenue Card */}
            <Card>
              <CardHeader>
                <CardTitle>総売上金額</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-4xl font-bold">
                  ¥{data.sales.total_revenue.toLocaleString()}
                </p>
              </CardContent>
            </Card>

            {/* Completion Rate Card */}
            <Card>
              <CardHeader>
                <CardTitle>完売達成率</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <p className="text-4xl font-bold">
                    {data.sales.completion_rate.toFixed(1)}%
                  </p>
                  <Progress value={data.sales.completion_rate} />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Daily Revenue Chart */}
          <Card>
            <CardHeader>
              <CardTitle>日別売上</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={data.sales.daily_revenue.map((revenue, index) => ({
                    day: `Day ${index + 1}`,
                    revenue,
                  }))}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="day" />
                  <YAxis />
                  <Tooltip
                    formatter={(value: number) =>
                      `¥${value.toLocaleString()}`
                    }
                  />
                  <Bar dataKey="revenue" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Inventory Status Section */}
      {data.inventory && (
        <div className="space-y-4">
          <h2 className="text-2xl font-bold">在庫状況</h2>
          <Card>
            <CardHeader>
              <CardTitle>商品別在庫</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {data.inventory.products.map((product) => (
                  <div
                    key={product.id}
                    className="flex items-center justify-between p-4 border rounded-lg"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <p className="font-semibold">{product.name}</p>
                        <Badge
                          variant={
                            product.product_type === 'set'
                              ? 'default'
                              : 'secondary'
                          }
                        >
                          {product.product_type === 'set' ? 'セット' : '単品'}
                        </Badge>
                        {product.is_out_of_stock && (
                          <Badge variant="destructive">在庫切れ</Badge>
                        )}
                      </div>
                      <div className="mt-2 space-y-1">
                        <div className="flex items-center justify-between text-sm text-muted-foreground">
                          <span>在庫率</span>
                          <span>{product.stock_rate.toFixed(1)}%</span>
                        </div>
                        <Progress value={product.stock_rate} />
                        <p className="text-sm text-muted-foreground">
                          残り: {product.current_stock} /{' '}
                          {product.initial_stock}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

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
    </div>
  );
}
