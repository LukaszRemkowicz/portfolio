// frontend/src/components/Programming.tsx
import { type FC, useEffect } from 'react';
import { useAppStore } from '../store/useStore';
import styles from '../styles/components/Programming.module.css';
// @ts-ignore: Github icon is deprecated in lucide-react in favor of simple-icons
import { Github, ExternalLink, Code2 } from 'lucide-react';
import LoadingScreen from './common/LoadingScreen';

const Programming: FC = () => {
  const {
    projects,
    isProjectsLoading: loading,
    error,
    loadProjects,
  } = useAppStore();

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  if (loading) {
    return <LoadingScreen message='Compiling projects...' />;
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
        <h1 className={styles.title}>Project Archive</h1>
        <p className={styles.subtitle}>
          A collection of software engineering projects, from microservices to
          creative frontend experiments.
        </p>
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
                        <Github className={styles.icon} /> Source
                      </a>
                    )}
                    {project.live_url && (
                      <a
                        href={project.live_url}
                        target='_blank'
                        rel='noopener noreferrer'
                        className={styles.actionLink}
                      >
                        <ExternalLink className={styles.icon} /> Live Demo
                      </a>
                    )}
                  </div>
                </div>
              </article>
            );
          })
        ) : (
          <div className={styles.noResults}>
            <p>
              The archives appear to be empty. Check back later for new
              transmissions.
            </p>
          </div>
        )}
      </div>
    </section>
  );
};

export default Programming;
