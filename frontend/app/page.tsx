'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
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
export default function Home() {
  const [data, setData] = useState<DashboardData>({
    sales: null,
    inventory: null,
    financial: null,
  });
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [chartDimensions, setChartDimensions] = useState({
    yAxisWidth: 100,
    marginLeft: 120,
  });

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
   * Handle window resize for responsive chart dimensions
   */
  useEffect(() => {
    const updateChartDimensions = () => {
      const width = window.innerWidth;
      if (width < 640) {
        // Mobile
        setChartDimensions({ yAxisWidth: 60, marginLeft: 70 });
      } else if (width < 1024) {
        // Tablet
        setChartDimensions({ yAxisWidth: 80, marginLeft: 90 });
      } else {
        // Desktop
        setChartDimensions({ yAxisWidth: 100, marginLeft: 120 });
      }
    };

    // Initial setup
    updateChartDimensions();

    // Listen to resize events
    window.addEventListener('resize', updateChartDimensions);

    return () => window.removeEventListener('resize', updateChartDimensions);
  }, []);

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
              <ResponsiveContainer width="100%" height={400}>
                <BarChart
                  data={data.inventory.products
                    .filter((p) => p.product_type === 'single')
                    .map((product) => ({
                      name: product.name,
                      sold: product.initial_stock - product.current_stock,
                      remaining: product.current_stock,
                      total: product.initial_stock,
                    }))}
                  layout="vertical"
                  margin={{
                    top: 5,
                    right: 30,
                    left: chartDimensions.marginLeft,
                    bottom: 5,
                  }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis
                    dataKey="name"
                    type="category"
                    width={chartDimensions.yAxisWidth}
                  />
                  <Tooltip
                    formatter={(value: number, name: string) => {
                      const label =
                        name === 'sold'
                          ? '販売済み'
                          : name === 'remaining'
                            ? '残り在庫'
                            : name;
                      return [value, label];
                    }}
                  />
                  <Bar dataKey="sold" stackId="a" fill="#ef4444" name="販売済み" />
                  <Bar
                    dataKey="remaining"
                    stackId="a"
                    fill="#22c55e"
                    name="残り在庫"
                  />
                </BarChart>
              </ResponsiveContainer>
              <div className="mt-4 flex items-center gap-4 text-sm text-muted-foreground">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-[#ef4444] rounded"></div>
                  <span>販売済み</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-[#22c55e] rounded"></div>
                  <span>残り在庫</span>
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
