"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Plus, Minus, ShoppingCart } from "lucide-react";
import { apiClient } from "@/lib/api";
import type { Product } from "@/lib/api/types";
import { ApiError } from "@/lib/api/errors";

interface CartItem {
  productId: string;
  productName: string;
  salePrice: number;
  quantity: number;
  subtotal: number;
}

export default function POSScreen() {
  // State management
  const [products, setProducts] = useState<Product[]>([]);
  const [cart, setCart] = useState<CartItem[]>([]);
  const [totalAmount, setTotalAmount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showErrorDialog, setShowErrorDialog] = useState(false);

  // Load products on mount
  useEffect(() => {
    loadProducts();
  }, []);

  // Calculate total when cart changes
  useEffect(() => {
    const total = cart.reduce((sum, item) => sum + item.subtotal, 0);
    setTotalAmount(total);
  }, [cart]);

  const loadProducts = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getProducts();
      setProducts(data);
    } catch (err) {
      console.error("Failed to load products:", err);
      setError("商品の読み込みに失敗しました");
    } finally {
      setLoading(false);
    }
  };

  const addToCart = (product: Product) => {
    setCart((prev) => {
      const existingItem = prev.find((item) => item.productId === product.id);

      if (existingItem) {
        // Increment quantity if already in cart
        return prev.map((item) =>
          item.productId === product.id
            ? {
                ...item,
                quantity: item.quantity + 1,
                subtotal: item.salePrice * (item.quantity + 1),
              }
            : item
        );
      } else {
        // Add new item to cart
        return [
          ...prev,
          {
            productId: product.id,
            productName: product.name,
            salePrice: product.sale_price,
            quantity: 1,
            subtotal: product.sale_price,
          },
        ];
      }
    });
  };

  const incrementQuantity = (productId: string) => {
    setCart((prev) =>
      prev.map((item) =>
        item.productId === productId
          ? {
              ...item,
              quantity: item.quantity + 1,
              subtotal: item.salePrice * (item.quantity + 1),
            }
          : item
      )
    );
  };

  const decrementQuantity = (productId: string) => {
    setCart((prev) => {
      const item = prev.find((i) => i.productId === productId);

      if (!item) return prev;

      if (item.quantity === 1) {
        // Remove item if quantity is 1
        return prev.filter((i) => i.productId !== productId);
      } else {
        // Decrement quantity
        return prev.map((i) =>
          i.productId === productId
            ? {
                ...i,
                quantity: i.quantity - 1,
                subtotal: i.salePrice * (i.quantity - 1),
              }
            : i
        );
      }
    });
  };

  const handleCheckout = async () => {
    if (cart.length === 0) {
      setError("カートが空です");
      setShowErrorDialog(true);
      return;
    }

    try {
      setLoading(true);
      const items = cart.map((item) => ({
        product_id: item.productId,
        quantity: item.quantity,
      }));

      await apiClient.checkout(items);

      // Clear cart on success
      setCart([]);
      setError("精算が完了しました");
      setShowErrorDialog(true);
    } catch (err) {
      console.error("Checkout failed:", err);

      if (err instanceof ApiError) {
        if (err.code === "INSUFFICIENT_STOCK") {
          setError(
            `在庫不足: ${err.message}\n` +
            `要求数量: ${err.details?.requested || "N/A"}\n` +
            `利用可能数量: ${err.details?.available || "N/A"}`
          );
        } else {
          setError(`エラー: ${err.message}`);
        }
      } else {
        setError("精算処理に失敗しました");
      }

      setShowErrorDialog(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-4 max-w-7xl">
      <h1 className="text-3xl font-bold mb-6">レジ画面</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Product List Section */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>商品一覧</CardTitle>
            </CardHeader>
            <CardContent>
              {loading && products.length === 0 ? (
                <p className="text-center text-gray-500">読み込み中...</p>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {products.map((product) => (
                    <Card
                      key={product.id}
                      className={`cursor-pointer hover:shadow-lg transition-shadow ${
                        product.current_stock === 0
                          ? "opacity-50 cursor-not-allowed"
                          : ""
                      }`}
                      onClick={() =>
                        product.current_stock > 0 && addToCart(product)
                      }
                    >
                      <CardContent className="p-4">
                        <div className="flex justify-between items-start mb-2">
                          <h3 className="font-semibold text-lg">
                            {product.name}
                          </h3>
                          {product.current_stock === 0 && (
                            <Badge variant="destructive">在庫切れ</Badge>
                          )}
                        </div>
                        <p className="text-2xl font-bold text-blue-600">
                          ¥{product.sale_price.toLocaleString()}
                        </p>
                        <p className="text-sm text-gray-500 mt-1">
                          在庫: {product.current_stock}個
                        </p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Cart Section */}
        <div className="lg:col-span-1">
          <Card className="sticky top-4">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ShoppingCart className="w-5 h-5" />
                購入カート
              </CardTitle>
            </CardHeader>
            <CardContent>
              {cart.length === 0 ? (
                <p className="text-center text-gray-500 py-8">
                  カートが空です
                </p>
              ) : (
                <div className="space-y-4">
                  {cart.map((item) => (
                    <div
                      key={item.productId}
                      className="flex items-center justify-between border-b pb-2"
                    >
                      <div className="flex-1">
                        <p className="font-medium">{item.productName}</p>
                        <p className="text-sm text-gray-500">
                          ¥{item.salePrice.toLocaleString()} × {item.quantity}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => decrementQuantity(item.productId)}
                        >
                          <Minus className="w-4 h-4" />
                        </Button>
                        <span className="w-8 text-center font-semibold">
                          {item.quantity}
                        </span>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => incrementQuantity(item.productId)}
                        >
                          <Plus className="w-4 h-4" />
                        </Button>
                      </div>
                      <p className="ml-4 font-bold text-lg w-24 text-right">
                        ¥{item.subtotal.toLocaleString()}
                      </p>
                    </div>
                  ))}
                </div>
              )}

              {/* Total Amount - PayPay style large display */}
              <div className="mt-6 p-6 bg-blue-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">合計金額</p>
                <p className="text-5xl font-bold text-blue-600">
                  ¥{totalAmount.toLocaleString()}
                </p>
              </div>

              {/* Checkout Button */}
              <Button
                className="w-full mt-4 py-6 text-lg"
                size="lg"
                onClick={handleCheckout}
                disabled={loading || cart.length === 0}
              >
                {loading ? "処理中..." : "精算する"}
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Error Dialog */}
      <Dialog open={showErrorDialog} onOpenChange={setShowErrorDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {error?.includes("完了") ? "成功" : "エラー"}
            </DialogTitle>
            <DialogDescription className="whitespace-pre-line">
              {error}
            </DialogDescription>
          </DialogHeader>
          <Button onClick={() => setShowErrorDialog(false)}>閉じる</Button>
        </DialogContent>
      </Dialog>
    </div>
  );
}
