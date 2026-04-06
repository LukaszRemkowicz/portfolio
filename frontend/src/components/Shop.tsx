import { type FC } from 'react';
import { ArrowRight, ShoppingBag, Sparkles } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { APP_ROUTES } from '../api/constants';
import SEO from './common/SEO';
import StarBackground from './StarBackground';
import styles from '../styles/components/Shop.module.css';
import appStyles from '../styles/components/App.module.css';

interface ShopProduct {
  nameKey: string;
  formatKey: string;
  priceKey: string;
  descriptionKey: string;
  accentClassName: string;
}

const PRODUCTS: ShopProduct[] = [
  {
    nameKey: 'shop.products.orion.name',
    formatKey: 'shop.products.orion.format',
    priceKey: 'shop.products.orion.price',
    descriptionKey: 'shop.products.orion.description',
    accentClassName: 'accentNebula',
  },
  {
    nameKey: 'shop.products.alps.name',
    formatKey: 'shop.products.alps.format',
    priceKey: 'shop.products.alps.price',
    descriptionKey: 'shop.products.alps.description',
    accentClassName: 'accentHorizon',
  },
  {
    nameKey: 'shop.products.guide.name',
    formatKey: 'shop.products.guide.format',
    priceKey: 'shop.products.guide.price',
    descriptionKey: 'shop.products.guide.description',
    accentClassName: 'accentSignal',
  },
];

const Shop: FC = () => {
  const { t } = useTranslation();

  return (
    <>
      <SEO
        title={t('shop.metaTitle')}
        description={t('shop.metaDescription')}
        url={APP_ROUTES.SHOP}
      />
      <StarBackground />
      <section className={styles.section}>
        <span className={styles.kicker}>
          <Sparkles size={14} />
          {t('shop.kicker')}
        </span>
        <h1 className={appStyles.heroTitle}>{t('shop.title')}</h1>
        <p className={styles.subtitle}>{t('shop.subtitle')}</p>

        <div className={styles.heroActions}>
          <a href='#catalog' className={styles.primaryAction}>
            <ShoppingBag size={16} />
            {t('shop.primaryCta')}
          </a>
          <Link
            to={`${APP_ROUTES.HOME}#contact`}
            className={styles.secondaryAction}
          >
            {t('shop.secondaryCta')}
            <ArrowRight size={16} />
          </Link>
        </div>

        <div className={styles.productGrid}>
          {PRODUCTS.map(product => (
            <article key={product.nameKey} className={styles.productCard}>
              <div
                className={`${styles.productImage} ${styles[product.accentClassName]}`}
                aria-hidden='true'
              >
                <span>{t('shop.placeholderBadge')}</span>
              </div>
              <div className={styles.productBody}>
                <div className={styles.productMeta}>
                  <p>{t(product.formatKey)}</p>
                  <strong>{t(product.priceKey)}</strong>
                </div>
                <h3>{t(product.nameKey)}</h3>
                <p>{t(product.descriptionKey)}</p>
                <button type='button' className={styles.productAction}>
                  {t('shop.placeholderAction')}
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>
    </>
  );
};

export default Shop;
