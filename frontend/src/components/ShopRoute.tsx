import { type FC } from 'react';
import { Navigate } from 'react-router-dom';
import MainLayout from './MainLayout';
import Shop from './Shop';
import { useFeatureFlag } from '../hooks/useFeatureFlag';
import { APP_ROUTES } from '../api/constants';

const ShopRoute: FC = () => {
  const { isEnabled, isLoading } = useFeatureFlag('shop');

  if (isLoading) {
    return null;
  }

  if (!isEnabled) {
    return <Navigate to={APP_ROUTES.HOME} replace />;
  }

  return (
    <MainLayout>
      <Shop />
    </MainLayout>
  );
};

export default ShopRoute;
