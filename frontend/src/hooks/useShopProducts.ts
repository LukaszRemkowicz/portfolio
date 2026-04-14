import { useQuery } from '@tanstack/react-query';
import { fetchShopProducts } from '../api/services';
import { ShopCatalog } from '../types';

export const useShopProducts = () =>
  useQuery<ShopCatalog, Error>({
    queryKey: ['shop-products'],
    queryFn: () => fetchShopProducts(),
    staleTime: 5 * 60 * 1000,
  });
