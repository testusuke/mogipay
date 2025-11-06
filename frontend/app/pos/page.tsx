"use client";

import { useState, useEffect, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Plus, Minus, ShoppingCart } from "lucide-react";
import { apiClient } from "@/lib/api";
import type { Product, ErrorDetail } from "@/lib/api/types";
import { ApiClientError, InsufficientStockError } from "@/lib/api/errors";

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
  // Virtual stock management - tracks available stock after cart operations
  const [availableStock, setAvailableStock] = useState<Map<string, number>>(new Map());

  // Load products on mount
  useEffect(() => {
    loadProducts();
  }, []);

  // Calculate total when cart changes
  useEffect(() => {
    const total = cart.reduce((sum, item) => sum + item.subtotal, 0);
    setTotalAmount(total);
  }, [cart]);

  // Sort products: set products first, then single products, each sorted by name
  const sortedProducts = useMemo(() => {
    const setProducts = products
      .filter((p) => p.product_type === 'set')
      .sort((a, b) => a.name.localeCompare(b.name, 'ja'));

    const singleProducts = products
      .filter((p) => p.product_type === 'single')
      .sort((a, b) => a.name.localeCompare(b.name, 'ja'));

    return [...setProducts, ...singleProducts];
  }, [products]);

  const loadProducts = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getProducts();
      setProducts(data);

      // Initialize available stock with ONLY single product stock values
      // Set products' stock will be calculated dynamically from component items
      const stockMap = new Map<string, number>();
      data.forEach((product) => {
        if (product.product_type === 'single') {
          stockMap.set(product.id, product.current_stock);
        }
      });
      setAvailableStock(stockMap);
    } catch (err) {
      console.error("Failed to load products:", err);
      setError("商品の読み込みに失敗しました");
    } finally {
      setLoading(false);
    }
  };

  // Calculate set product stock dynamically from component items
  // Returns the maximum number of sets that can be made
  const calculateSetStock = (product: Product): number => {
    if (product.product_type === 'single') {
      return availableStock.get(product.id) || 0;
    }

    if (!product.set_items || product.set_items.length === 0) {
      return 0;
    }

    // Calculate how many sets can be made from each component
    // The minimum value determines the total set stock
    let minSetCount = Infinity;

    for (const item of product.set_items) {
      const componentStock = availableStock.get(item.product_id) || 0;
      const possibleSets = Math.floor(componentStock / item.quantity);
      minSetCount = Math.min(minSetCount, possibleSets);
    }

    return minSetCount === Infinity ? 0 : minSetCount;
  };

  // Check if product can be added to cart (stock validation)
  const canAddToCart = (product: Product): { canAdd: boolean; reason?: string } => {
    const stock = calculateSetStock(product);

    if (stock <= 0) {
      if (product.product_type === 'single') {
        return { canAdd: false, reason: `${product.name}の在庫が不足しています` };
      } else {
        // For set products, find which component is insufficient
        if (!product.set_items || product.set_items.length === 0) {
          return { canAdd: false, reason: 'セット構成が不正です' };
        }

        for (const item of product.set_items) {
          const componentStock = availableStock.get(item.product_id) || 0;
          if (componentStock < item.quantity) {
            const componentProduct = products.find((p) => p.id === item.product_id);
            const componentName = componentProduct?.name || '構成商品';
            return {
              canAdd: false,
              reason: `${product.name}の構成単品「${componentName}」の在庫が不足しています（必要: ${item.quantity}個、在庫: ${componentStock}個）`,
            };
          }
        }
      }
    }

    return { canAdd: true };
  };

  // Update available stock after adding to cart
  const updateStockAfterAdd = (product: Product) => {
    setAvailableStock((prev) => {
      const newStock = new Map(prev);

      if (product.product_type === 'single') {
        // Decrement single product stock
        const currentStock = newStock.get(product.id) || 0;
        newStock.set(product.id, currentStock - 1);
      } else if (product.set_items) {
        // Decrement all component items' stock
        product.set_items.forEach((item) => {
          const currentStock = newStock.get(item.product_id) || 0;
          newStock.set(item.product_id, currentStock - item.quantity);
        });
      }

      return newStock;
    });
  };

  // Restore available stock after removing from cart
  const updateStockAfterRemove = (product: Product, quantity: number) => {
    setAvailableStock((prev) => {
      const newStock = new Map(prev);

      if (product.product_type === 'single') {
        // Increment single product stock
        const currentStock = newStock.get(product.id) || 0;
        newStock.set(product.id, currentStock + quantity);
      } else if (product.set_items) {
        // Increment all component items' stock
        product.set_items.forEach((item) => {
          const currentStock = newStock.get(item.product_id) || 0;
          newStock.set(item.product_id, currentStock + (item.quantity * quantity));
        });
      }

      return newStock;
    });
  };

  const addToCart = (product: Product) => {
    // Check stock availability
    const stockCheck = canAddToCart(product);
    if (!stockCheck.canAdd) {
      setError(stockCheck.reason || '在庫が不足しています');
      setShowErrorDialog(true);
      return;
    }

    // Update virtual stock
    updateStockAfterAdd(product);

    // Add to cart
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
    const product = products.find((p) => p.id === productId);
    if (!product) return;

    // Check stock availability before incrementing
    const stockCheck = canAddToCart(product);
    if (!stockCheck.canAdd) {
      setError(stockCheck.reason || '在庫が不足しています');
      setShowErrorDialog(true);
      return;
    }

    // Update virtual stock
    updateStockAfterAdd(product);

    // Increment quantity in cart
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
    const product = products.find((p) => p.id === productId);
    if (!product) return;

    setCart((prev) => {
      const item = prev.find((i) => i.productId === productId);

      if (!item) return prev;

      if (item.quantity === 1) {
        // Restore stock when removing from cart
        updateStockAfterRemove(product, 1);
        // Remove item if quantity is 1
        return prev.filter((i) => i.productId !== productId);
      } else {
        // Restore stock when decrementing
        updateStockAfterRemove(product, 1);
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

      await apiClient.checkout({ items });

      // Clear cart on success
      setCart([]);

      // Reload products to get updated stock values
      await loadProducts();

      setError("精算が完了しました");
      setShowErrorDialog(true);
    } catch (err) {
      console.error("Checkout failed:", err);

      if (err instanceof InsufficientStockError) {
        const details = err.details as ErrorDetail | undefined;
        setError(
          `在庫不足: ${err.message}\n` +
          `要求数量: ${details?.requested || "N/A"}\n` +
          `利用可能数量: ${details?.available || "N/A"}`
        );
      } else if (err instanceof ApiClientError) {
        setError(`エラー: ${err.message}`);
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
              {loading && sortedProducts.length === 0 ? (
                <p className="text-center text-gray-500">読み込み中...</p>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {sortedProducts.map((product) => {
                    // Calculate stock dynamically (single or set)
                    const stock = calculateSetStock(product);
                    const isOutOfStock = stock === 0;
                    // Get quantity in cart for this product
                    const cartItem = cart.find(item => item.productId === product.id);
                    const quantityInCart = cartItem?.quantity || 0;

                    return (
                      <Card
                        key={product.id}
                        className={`relative cursor-pointer hover:shadow-lg transition-shadow ${
                          isOutOfStock
                            ? "opacity-50 cursor-not-allowed"
                            : ""
                        }`}
                        onClick={() =>
                          !isOutOfStock && addToCart(product)
                        }
                      >
                        {/* Cart quantity badge - top right corner inside card */}
                        {quantityInCart > 0 && (
                          <div className="absolute top-2 right-2 bg-black text-white rounded-full w-8 h-8 flex items-center justify-center font-bold text-sm shadow-lg z-10">
                            {quantityInCart}
                          </div>
                        )}
                        <CardContent className="p-4">
                          <div className="flex justify-between items-start mb-2">
                            <h3 className="font-semibold text-lg">
                              {product.name}
                            </h3>
                            {isOutOfStock && (
                              <Badge variant="destructive">在庫切れ</Badge>
                            )}
                          </div>
                          <p className="text-2xl font-bold text-blue-600">
                            ¥{product.sale_price.toLocaleString()}
                          </p>
                          <p className="text-sm text-gray-500 mt-1">
                            在庫: {stock}個
                          </p>
                        </CardContent>
                      </Card>
                    );
                  })}
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
