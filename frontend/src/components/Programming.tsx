import { type FC } from 'react';
import { useTranslation } from 'react-i18next';
import { useProjects } from '../hooks/useProjects';
import styles from '../styles/components/Programming.module.css';
import { Github, ExternalLink, Code2 } from 'lucide-react';
import LoadingScreen from './common/LoadingScreen';

const Programming: FC = () => {
  const { t } = useTranslation();
  const {
    data: projects = [],
    isLoading: loading,
    error: projectsError,
  } = useProjects();

  const error = projectsError ? (projectsError as Error).message : null;

  if (loading) {
    return <LoadingScreen message={t('common.compiling')} />;
  }

  if (error) {
    return (
      <div className={styles.error}>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <section className={styles.section}>
      <header className={styles.header}>
        <h1 className={styles.title}>{t('programming.title')}</h1>
        <p className={styles.subtitle}>{t('programming.subtitle')}</p>
      </header>

      <div className={styles.grid}>
        {projects.length > 0 ? (
          projects.map(project => {
            const coverImage =
              project.images.find(img => img.is_cover) || project.images[0];

            return (
              <article key={project.pk} className={styles.projectCard}>
                <div className={styles.imageWrapper}>
                  {coverImage ? (
                    <img
                      src={coverImage.url}
                      alt={project.name}
                      className={styles.cardImage}
                    />
                  ) : (
                    <div className={styles.imagePlaceholder}>
                      <Code2 size={48} className={styles.placeholderIcon} />
                    </div>
                  )}
                </div>

                <div className={styles.cardContent}>
                  <h3 className={styles.cardTitle}>{project.name}</h3>
                  <p className={styles.cardDescription}>
                    {project.description}
                  </p>

                  <div className={styles.techStack}>
                    {project.technologies_list.map((tech, index) => (
                      <span key={index} className={styles.techBadge}>
                        {tech}
                      </span>
                    ))}
                  </div>

                  <div className={styles.cardActions}>
                    {project.github_url && (
                      <a
                        href={project.github_url}
                        target='_blank'
                        rel='noopener noreferrer'
                        className={styles.actionLink}
                      >
                        <Github className={styles.icon} />{' '}
                        {t('programming.source')}
                      </a>
                    )}
                    {project.live_url && (
                      <a
                        href={project.live_url}
                        target='_blank'
                        rel='noopener noreferrer'
                        className={styles.actionLink}
                      >
                        <ExternalLink className={styles.icon} />{' '}
                        {t('programming.liveDemo')}
                      </a>
                    )}
                  </div>
                </div>
              </article>
            );
          })
        ) : (
          <div className={styles.noResults}>
            <p>{t('programming.empty')}</p>
          </div>
        )}
      </div>
    </section>
  );
};

export default Programming;
