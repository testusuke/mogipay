"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Plus, Edit, Trash2 } from "lucide-react";
import { apiClient } from "@/lib/api";
import type { Product, CreateProductRequest } from "@/lib/api/types";
import { ApiClientError } from "@/lib/api/errors";

interface SetItemForm {
  productId: string;
  quantity: number;
}

interface ProductFormData {
  name: string;
  unitCost: number;
  salePrice: number;
  initialStock: number;
  productType: "single" | "set";
  setItems: SetItemForm[];
}

const initialFormData: ProductFormData = {
  name: "",
  unitCost: 0,
  salePrice: 0,
  initialStock: 0,
  productType: "single",
  setItems: [],
};

export default function ProductManagement() {
  // State management
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Dialog states
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  // Form data
  const [formData, setFormData] = useState<ProductFormData>(initialFormData);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);

  // Load products on mount
  useEffect(() => {
    loadProducts();
  }, []);

  const loadProducts = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getProducts();
      setProducts(data);
      setError(null);
    } catch (err) {
      console.error("Failed to load products:", err);
      setError("商品の読み込みに失敗しました");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProduct = async () => {
    try {
      setLoading(true);
      setError(null);

      const request: CreateProductRequest = {
        name: formData.name,
        unit_cost: formData.unitCost,
        sale_price: formData.salePrice,
        // セット商品の場合は在庫数を0に固定（構成単品から動的計算されるため）
        initial_stock: formData.productType === "set" ? 0 : formData.initialStock,
        product_type: formData.productType,
        set_items:
          formData.productType === "set"
            ? formData.setItems.map((item) => ({
                product_id: item.productId,
                quantity: item.quantity,
              }))
            : undefined,
      };

      await apiClient.createProduct(request);
      await loadProducts();
      setShowCreateDialog(false);
      setFormData(initialFormData);
    } catch (err) {
      console.error("Failed to create product:", err);
      if (err instanceof ApiClientError) {
        setError(err.message);
      } else {
        setError("商品の登録に失敗しました");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleEditProduct = async () => {
    if (!selectedProduct) return;

    try {
      setLoading(true);
      setError(null);

      await apiClient.updateProduct(selectedProduct.id, {
        name: formData.name,
        unit_cost: formData.unitCost,
        sale_price: formData.salePrice,
        // セット商品の場合は在庫数を0に固定（構成単品から動的計算されるため）
        // product_type は変更不可（データ整合性のため）
        initial_stock: formData.productType === "set" ? 0 : formData.initialStock,
        set_items:
          formData.productType === "set"
            ? formData.setItems.map((item) => ({
                product_id: item.productId,
                quantity: item.quantity,
              }))
            : undefined,
      });

      await loadProducts();
      setShowEditDialog(false);
      setSelectedProduct(null);
      setFormData(initialFormData);
    } catch (err) {
      console.error("Failed to update product:", err);
      if (err instanceof ApiClientError) {
        setError(err.message);
      } else {
        setError("商品の更新に失敗しました");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteProduct = async () => {
    if (!selectedProduct) return;

    try {
      setLoading(true);
      setError(null);

      await apiClient.deleteProduct(selectedProduct.id);
      await loadProducts();
      setShowDeleteDialog(false);
      setSelectedProduct(null);
    } catch (err) {
      console.error("Failed to delete product:", err);
      if (err instanceof ApiClientError) {
        // Check if it's a constraint violation error
        if (err.message.includes("削除できません") || err.message.includes("使用されています")) {
          setError(`${selectedProduct.name}は削除できません。販売履歴またはセット商品の構成で使用されています。`);
        } else {
          setError(err.message);
        }
      } else {
        setError("商品の削除に失敗しました");
      }
      // Keep the dialog open to show error
    } finally {
      setLoading(false);
    }
  };

  const openCreateDialog = () => {
    setFormData(initialFormData);
    setShowCreateDialog(true);
  };

  const openEditDialog = (product: Product) => {
    setSelectedProduct(product);
    setFormData({
      name: product.name,
      unitCost: product.unit_cost,
      salePrice: product.sale_price,
      initialStock: product.initial_stock,
      productType: product.product_type,
      setItems:
        product.set_items?.map((item) => ({
          productId: item.product_id,
          quantity: item.quantity,
        })) || [],
    });
    setShowEditDialog(true);
  };

  const openDeleteDialog = (product: Product) => {
    setSelectedProduct(product);
    setError(null);
    setShowDeleteDialog(true);
  };

  const addSetItem = () => {
    setFormData((prev) => ({
      ...prev,
      setItems: [...prev.setItems, { productId: "", quantity: 1 }],
    }));
  };

  const removeSetItem = (index: number) => {
    setFormData((prev) => ({
      ...prev,
      setItems: prev.setItems.filter((_, i) => i !== index),
    }));
  };

  const updateSetItem = (index: number, field: keyof SetItemForm, value: string | number) => {
    setFormData((prev) => ({
      ...prev,
      setItems: prev.setItems.map((item, i) =>
        i === index ? { ...item, [field]: value } : item
      ),
    }));
  };

  // Filter single products for set item selection
  const singleProducts = products.filter((p) => p.product_type === "single");

  return (
    <div className="container mx-auto p-4 space-y-4">
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle className="text-2xl font-bold">商品管理</CardTitle>
            <Button onClick={openCreateDialog}>
              <Plus className="mr-2 h-4 w-4" />
              新規登録
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          {loading && products.length === 0 ? (
            <div className="text-center py-8">読み込み中...</div>
          ) : (
            <>
              {/* Desktop: Table view */}
              <div className="hidden md:block">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>商品名</TableHead>
                      <TableHead>種別</TableHead>
                      <TableHead className="text-right">単価</TableHead>
                      <TableHead className="text-right">販売価格</TableHead>
                      <TableHead className="text-right">在庫数</TableHead>
                      <TableHead className="text-right">操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {products.map((product) => (
                      <TableRow key={product.id}>
                        <TableCell className="font-medium">{product.name}</TableCell>
                        <TableCell>
                          <Badge variant={product.product_type === "set" ? "default" : "secondary"}>
                            {product.product_type === "set" ? "セット" : "単品"}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">¥{product.unit_cost.toLocaleString()}</TableCell>
                        <TableCell className="text-right">¥{product.sale_price.toLocaleString()}</TableCell>
                        <TableCell className="text-right">{product.current_stock}</TableCell>
                        <TableCell className="text-right space-x-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => openEditDialog(product)}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => openDeleteDialog(product)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {/* Mobile: Card view */}
              <div className="md:hidden space-y-4">
                {products.map((product) => (
                  <Card key={product.id}>
                    <CardHeader className="pb-3">
                      <div className="flex justify-between items-start">
                        <div className="space-y-1">
                          <CardTitle className="text-lg">{product.name}</CardTitle>
                          <Badge variant={product.product_type === "set" ? "default" : "secondary"}>
                            {product.product_type === "set" ? "セット" : "単品"}
                          </Badge>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => openEditDialog(product)}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => openDeleteDialog(product)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">単価</span>
                        <span className="font-medium">¥{product.unit_cost.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">販売価格</span>
                        <span className="font-medium">¥{product.sale_price.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">在庫数</span>
                        <span className="font-medium">{product.current_stock}</span>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Create Product Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>新規商品登録</DialogTitle>
            <DialogDescription>商品情報を入力してください</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="name">商品名</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </div>
            <div>
              <Label htmlFor="productType">商品種別</Label>
              <Select
                value={formData.productType}
                onValueChange={(value: "single" | "set") =>
                  setFormData({ ...formData, productType: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="single">単品</SelectItem>
                  <SelectItem value="set">セット</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="unitCost">単価</Label>
                <Input
                  id="unitCost"
                  type="number"
                  value={formData.unitCost}
                  onChange={(e) =>
                    setFormData({ ...formData, unitCost: Number(e.target.value) })
                  }
                />
              </div>
              <div>
                <Label htmlFor="salePrice">販売価格</Label>
                <Input
                  id="salePrice"
                  type="number"
                  value={formData.salePrice}
                  onChange={(e) =>
                    setFormData({ ...formData, salePrice: Number(e.target.value) })
                  }
                />
              </div>
            </div>
            {formData.productType === "single" && (
              <div>
                <Label htmlFor="initialStock">在庫数</Label>
                <Input
                  id="initialStock"
                  type="number"
                  value={formData.initialStock}
                  onChange={(e) =>
                    setFormData({ ...formData, initialStock: Number(e.target.value) })
                  }
                />
              </div>
            )}

            {formData.productType === "set" && (
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <Label>セット構成</Label>
                  <Button size="sm" onClick={addSetItem}>
                    <Plus className="h-4 w-4 mr-1" />
                    構成商品追加
                  </Button>
                </div>
                {formData.setItems.map((item, index) => (
                  <div key={index} className="flex gap-2 items-end">
                    <div className="flex-1">
                      <Select
                        value={item.productId}
                        onValueChange={(value) => updateSetItem(index, "productId", value)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="商品を選択" />
                        </SelectTrigger>
                        <SelectContent>
                          {singleProducts.map((product) => (
                            <SelectItem key={product.id} value={product.id}>
                              {product.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="w-24">
                      <Input
                        type="number"
                        placeholder="数量"
                        value={item.quantity}
                        onChange={(e) =>
                          updateSetItem(index, "quantity", Number(e.target.value))
                        }
                      />
                    </div>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => removeSetItem(index)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              キャンセル
            </Button>
            <Button onClick={handleCreateProduct} disabled={loading}>
              {loading ? "登録中..." : "登録"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Product Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              商品編集
              <Badge variant={formData.productType === "set" ? "default" : "secondary"}>
                {formData.productType === "set" ? "セット" : "単品"}
              </Badge>
            </DialogTitle>
            <DialogDescription>商品情報を編集してください</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="edit-name">商品名</Label>
              <Input
                id="edit-name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="edit-unitCost">単価</Label>
                <Input
                  id="edit-unitCost"
                  type="number"
                  value={formData.unitCost}
                  onChange={(e) =>
                    setFormData({ ...formData, unitCost: Number(e.target.value) })
                  }
                />
              </div>
              <div>
                <Label htmlFor="edit-salePrice">販売価格</Label>
                <Input
                  id="edit-salePrice"
                  type="number"
                  value={formData.salePrice}
                  onChange={(e) =>
                    setFormData({ ...formData, salePrice: Number(e.target.value) })
                  }
                />
              </div>
            </div>
            {formData.productType === "single" && (
              <div>
                <Label htmlFor="edit-initialStock">在庫数</Label>
                <Input
                  id="edit-initialStock"
                  type="number"
                  value={formData.initialStock}
                  onChange={(e) =>
                    setFormData({ ...formData, initialStock: Number(e.target.value) })
                  }
                />
              </div>
            )}

            {formData.productType === "set" && (
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <Label>セット構成</Label>
                  <Button size="sm" onClick={addSetItem}>
                    <Plus className="h-4 w-4 mr-1" />
                    構成商品追加
                  </Button>
                </div>
                {formData.setItems.map((item, index) => (
                  <div key={index} className="flex gap-2 items-end">
                    <div className="flex-1">
                      <Select
                        value={item.productId}
                        onValueChange={(value) => updateSetItem(index, "productId", value)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="商品を選択" />
                        </SelectTrigger>
                        <SelectContent>
                          {singleProducts.map((product) => (
                            <SelectItem key={product.id} value={product.id}>
                              {product.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="w-24">
                      <Input
                        type="number"
                        placeholder="数量"
                        value={item.quantity}
                        onChange={(e) =>
                          updateSetItem(index, "quantity", Number(e.target.value))
                        }
                      />
                    </div>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => removeSetItem(index)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditDialog(false)}>
              キャンセル
            </Button>
            <Button onClick={handleEditProduct} disabled={loading}>
              {loading ? "更新中..." : "更新"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>商品削除確認</DialogTitle>
            <DialogDescription>
              {selectedProduct?.name}を削除してもよろしいですか?
              この操作は取り消せません。
            </DialogDescription>
          </DialogHeader>
          {error && showDeleteDialog && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setShowDeleteDialog(false);
              setError(null);
            }}>
              キャンセル
            </Button>
            <Button variant="destructive" onClick={handleDeleteProduct} disabled={loading}>
              {loading ? "削除中..." : "削除"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
