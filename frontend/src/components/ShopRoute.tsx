import { type FC } from 'react';
import MainLayout from './MainLayout';
import Shop from './Shop';
import { useFeatureFlag } from '../hooks/useFeatureFlag';
import NotFoundPage from './NotFoundPage';

const ShopRoute: FC = () => {
  const { isEnabled, isLoading } = useFeatureFlag('shop');

  if (isLoading) {
    return null;
  }

  if (!isEnabled) {
    return <NotFoundPage />;
  }

  return (
    <MainLayout>
      <Shop />
    </MainLayout>
  );
};

export default ShopRoute;
