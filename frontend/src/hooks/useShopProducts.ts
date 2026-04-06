import { useQuery } from '@tanstack/react-query';
import { fetchShopProducts } from '../api/services';
import { ShopProduct } from '../types';

export const useShopProducts = () =>
  useQuery<ShopProduct[], Error>({
    queryKey: ['shop-products'],
    queryFn: () => fetchShopProducts(),
    staleTime: 5 * 60 * 1000,
  });
