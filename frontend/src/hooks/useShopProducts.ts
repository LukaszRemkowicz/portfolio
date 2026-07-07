import { useQuery } from '@tanstack/react-query';
import { fetchShopProducts } from '../api/services';
import { ShopCatalog } from '../types';
import { useImageVariantSize } from './useImageVariantSize';

export const useShopProducts = () => {
  const imageSize = useImageVariantSize();

  return useQuery<ShopCatalog, Error>({
    queryKey: ['shop-products', imageSize],
    queryFn: () => fetchShopProducts(imageSize),
    staleTime: 5 * 60 * 1000,
  });
};
