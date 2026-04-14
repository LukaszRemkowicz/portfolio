import { type FC } from 'react';
import { ArrowRight, Sparkles } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { APP_ROUTES } from '../api/constants';
import { useShopProducts } from '../hooks/useShopProducts';
import { getMediaUrl } from '../api/media';
import SEO from './common/SEO';
import StarBackground from './StarBackground';
import ShootingStars from './ShootingStars';
import ClientOnly from './common/ClientOnly';
import { sanitizeHtml, stripHtml } from '../utils/html';
import styles from '../styles/components/Shop.module.css';
import appStyles from '../styles/components/App.module.css';

const Shop: FC = () => {
  const { t } = useTranslation();
  const { data, isLoading, isError } = useShopProducts();
  const products = data?.products ?? [];
  const title = data?.title || t('shop.title');
  const description = stripHtml(data?.description || '').trim();
  const backgroundUrl = data?.background_url || '/zodiacal.png';
  const fallbackDescription = t('shop.subtitle');

  return (
    <>
      <SEO
        title={t('shop.metaTitle')}
        description={t('shop.metaDescription')}
        url={APP_ROUTES.SHOP}
      />
      <StarBackground />
      <div className={styles.shopContainer}>
        <div
          className={styles.zodiacalBackground}
          style={{ backgroundImage: `url('${backgroundUrl}')` }}
          aria-hidden='true'
        />
        <div
          style={{
            position: 'fixed',
            inset: 0,
            pointerEvents: 'none',
            zIndex: 0,
          }}
        >
          <ClientOnly>
            <ShootingStars />
          </ClientOnly>
        </div>
        <section className={styles.section}>
          <span className={styles.kicker}>
            <Sparkles size={14} />
            {t('shop.kicker')}
          </span>
          <h1 className={appStyles.heroTitle}>{title}</h1>
          <p className={styles.subtitle}>
            {description || fallbackDescription}
          </p>

          <div className={styles.heroActions}>
            <Link
              to={`${APP_ROUTES.HOME}#contact`}
              className={styles.secondaryAction}
            >
              {t('shop.secondaryCta')}
              <ArrowRight size={16} />
            </Link>
          </div>

          {isLoading ? (
            <p className={styles.statusMessage}>{t('shop.loading')}</p>
          ) : null}

          {isError ? (
            <p className={styles.statusMessage}>{t('shop.error')}</p>
          ) : null}

          {!isLoading && !isError && products.length === 0 ? (
            <p className={styles.statusMessage}>{t('shop.empty')}</p>
          ) : null}

          {!isLoading && !isError && products.length > 0 ? (
            <div id='catalog' className={styles.productGrid}>
              {products.map(product => (
                <article key={product.id} className={styles.productCard}>
                  <div className={styles.productImage}>
                    {product.thumbnail_url ? (
                      <img
                        src={
                          getMediaUrl(product.thumbnail_url) ??
                          product.thumbnail_url
                        }
                        alt=''
                        className={styles.productArtwork}
                        loading='lazy'
                        aria-hidden='true'
                      />
                    ) : null}
                  </div>
                  <div className={styles.productBody}>
                    <h3>{product.title}</h3>
                    <div
                      className='product-description-container'
                      dangerouslySetInnerHTML={{
                        __html: sanitizeHtml(product.description),
                      }}
                    />
                    <a
                      href={product.external_url}
                      target='_blank'
                      rel='noreferrer'
                      className={styles.productAction}
                    >
                      {t('shop.viewProduct')}
                      <ArrowRight size={16} />
                    </a>
                  </div>
                </article>
              ))}
            </div>
          ) : null}
        </section>
      </div>
    </>
  );
};

export default Shop;
