'use client';

import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth/AuthProvider';

export function Navigation() {
  const pathname = usePathname();
  const { isAuthenticated } = useAuth();

  // Don't show navigation on login page
  if (pathname === '/login') {
    return null;
  }

  return (
    <nav className="border-b">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center space-x-8">
            <Link href="/" className="flex items-center">
              <Image
                src="/logo.png"
                alt="MogiPay"
                width={40}
                height={40}
                priority
                className="rounded-lg"
              />
            </Link>
            {isAuthenticated && (
              <div className="flex space-x-4">
                <Link
                  href="/pos"
                  className="text-sm font-medium transition-colors hover:text-primary"
                >
                  レジ
                </Link>
                <Link
                  href="/kitchen"
                  className="text-sm font-medium transition-colors hover:text-primary"
                >
                  キッチン
                </Link>
                <Link
                  href="/products"
                  className="text-sm font-medium transition-colors hover:text-primary"
                >
                  商品管理
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
