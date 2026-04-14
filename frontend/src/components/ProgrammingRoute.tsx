import { type FC } from 'react';
import { Navigate } from 'react-router-dom';
import MainLayout from './MainLayout';
import Programming from './Programming';
import { useFeatureFlag } from '../hooks/useFeatureFlag';
import { APP_ROUTES } from '../api/constants';

const ProgrammingRoute: FC = () => {
  const { isEnabled, isLoading } = useFeatureFlag('programming');

  if (isLoading) {
    return null;
  }

  if (!isEnabled) {
    return <Navigate to={APP_ROUTES.HOME} replace />;
  }

  return (
    <MainLayout>
      <Programming />
    </MainLayout>
  );
};

export default ProgrammingRoute;
