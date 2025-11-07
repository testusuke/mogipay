"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { CheckCircle, Clock, AlertCircle } from "lucide-react";
import { apiClient } from "@/lib/api";
import type { KitchenTicket } from "@/lib/api/types";
import {
  ApiClientError,
  TicketNotFoundError,
  TicketAlreadyCompletedError,
  NetworkError,
} from "@/lib/api/errors";

export default function KitchenScreen() {
  // State management
  const [tickets, setTickets] = useState<KitchenTicket[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showErrorDialog, setShowErrorDialog] = useState(false);
  const [completingTicket, setCompletingTicket] = useState<string | null>(null);
  const [connectionError, setConnectionError] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  // Load tickets on mount and setup polling
  useEffect(() => {
    loadTickets();

    // Setup polling every 3 seconds
    const intervalId = setInterval(() => {
      loadTickets();
    }, 3000);

    // Cleanup interval on unmount
    return () => clearInterval(intervalId);
  }, []);

  // Load tickets from API
  const loadTickets = async () => {
    try {
      setLoading(true);
      setConnectionError(false);

      const response = await apiClient.getKitchenTickets();
      setTickets(response.tickets);
      setRetryCount(0); // Reset retry count on successful load
    } catch (err) {
      console.error("Failed to load kitchen tickets:", err);

      if (err instanceof NetworkError) {
        setConnectionError(true);
        setRetryCount((prev) => prev + 1);

        // Auto-retry up to 3 times
        if (retryCount < 3) {
          setTimeout(() => {
            loadTickets();
          }, 5000); // Retry after 5 seconds
        } else {
          setError("ネットワークエラー: サーバーに接続できません");
          setShowErrorDialog(true);
        }
      } else if (err instanceof ApiClientError) {
        setError(`エラー: ${err.message}`);
        setShowErrorDialog(true);
      } else {
        setError("チケットの読み込みに失敗しました");
        setShowErrorDialog(true);
      }
    } finally {
      setLoading(false);
    }
  };

  // Complete a ticket
  const completeTicket = async (ticketId: string) => {
    try {
      setCompletingTicket(ticketId);

      await apiClient.completeKitchenTicket(ticketId, {
        completed_by: "kitchen", // TODO: Replace with actual user ID
      });

      // Remove completed ticket from list
      setTickets((prev) => prev.filter((ticket) => ticket.id !== ticketId));
    } catch (err) {
      console.error("Failed to complete ticket:", err);

      if (err instanceof TicketNotFoundError) {
        setError("チケットが見つかりません。画面を更新します。");
        setShowErrorDialog(true);
        // Reload tickets to sync with server
        loadTickets();
      } else if (err instanceof TicketAlreadyCompletedError) {
        setError("このチケットは既に完了済みです");
        setShowErrorDialog(true);
        // Remove ticket from list
        setTickets((prev) => prev.filter((ticket) => ticket.id !== ticketId));
      } else if (err instanceof NetworkError) {
        setError("ネットワークエラー: サーバーに接続できません");
        setShowErrorDialog(true);
      } else if (err instanceof ApiClientError) {
        setError(`エラー: ${err.message}`);
        setShowErrorDialog(true);
      } else {
        setError("チケット完了処理に失敗しました");
        setShowErrorDialog(true);
      }
    } finally {
      setCompletingTicket(null);
    }
  };

  // Calculate elapsed time color (green -> yellow -> red)
  const getElapsedTimeColor = (minutes: number): string => {
    if (minutes < 5) return "text-green-600";
    if (minutes < 10) return "text-yellow-600";
    return "text-red-600";
  };

  return (
    <div className="container mx-auto p-4 max-w-7xl">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">調理チケット一覧</h1>
        {connectionError && (
          <Badge variant="destructive" className="flex items-center gap-1">
            <AlertCircle className="w-4 h-4" />
            接続エラー (再試行中...)
          </Badge>
        )}
      </div>

      {/* Loading State */}
      {loading && tickets.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg">読み込み中...</p>
        </div>
      ) : tickets.length === 0 ? (
        /* Empty State */
        <div className="text-center py-12">
          <div className="flex flex-col items-center gap-4">
            <CheckCircle className="w-16 h-16 text-green-500" />
            <p className="text-2xl font-semibold text-gray-700">
              すべての注文が完了しました!
            </p>
            <p className="text-gray-500">新しい注文が入ると自動的に表示されます</p>
          </div>
        </div>
      ) : (
        /* Ticket Grid */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {tickets.map((ticket) => (
            <Card
              key={ticket.id}
              className="relative hover:shadow-xl transition-shadow border-2"
            >
              {/* Elapsed Time Badge */}
              <div className="absolute top-4 right-4">
                <Badge
                  variant="outline"
                  className={`flex items-center gap-1 text-base font-bold ${getElapsedTimeColor(
                    ticket.elapsed_minutes
                  )}`}
                >
                  <Clock className="w-4 h-4" />
                  {ticket.elapsed_minutes}分経過
                </Badge>
              </div>

              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-gray-500">
                  注文時刻: {new Date(ticket.order_time).toLocaleTimeString("ja-JP")}
                </CardTitle>
              </CardHeader>

              <CardContent className="space-y-4">
                {/* Ticket Items */}
                {ticket.items.map((item, index) => (
                  <div
                    key={index}
                    className={`p-4 rounded-lg ${
                      item.product_type === "set"
                        ? "bg-blue-50 border-2 border-blue-200"
                        : "bg-gray-50"
                    }`}
                  >
                    {/* Product Name and Quantity */}
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="text-2xl font-bold">{item.product_name}</h3>
                      <Badge
                        variant={item.quantity > 1 ? "default" : "secondary"}
                        className={`text-xl px-3 py-1 ${
                          item.quantity > 1 ? "bg-red-500" : ""
                        }`}
                      >
                        × {item.quantity}
                      </Badge>
                    </div>

                    {/* Set Product Components */}
                    {item.product_type === "set" && item.components && (
                      <div className="mt-3 pl-4 border-l-4 border-blue-400 space-y-1">
                        {item.components.map((component, idx) => (
                          <div
                            key={idx}
                            className="text-lg text-gray-700 flex justify-between"
                          >
                            <span>- {component.name}</span>
                            <span className="font-semibold">× {component.quantity}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}

                {/* Complete Button */}
                <Button
                  className="w-full py-6 text-lg font-bold"
                  size="lg"
                  onClick={() => completeTicket(ticket.id)}
                  disabled={completingTicket === ticket.id}
                >
                  {completingTicket === ticket.id ? "処理中..." : "調理完了"}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Error Dialog */}
      <Dialog open={showErrorDialog} onOpenChange={setShowErrorDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>エラー</DialogTitle>
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
