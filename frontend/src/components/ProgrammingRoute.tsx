import { type FC } from 'react';
import MainLayout from './MainLayout';
import Programming from './Programming';
import { useFeatureFlag } from '../hooks/useFeatureFlag';
import NotFoundPage from './NotFoundPage';

const ProgrammingRoute: FC = () => {
  const { isEnabled, isLoading } = useFeatureFlag('programming');

  if (isLoading) {
    return null;
  }

  if (!isEnabled) {
    return <NotFoundPage />;
  }

  return (
    <MainLayout>
      <Programming />
    </MainLayout>
  );
};

export default ProgrammingRoute;
