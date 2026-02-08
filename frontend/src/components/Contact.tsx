import React, { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { fetchContact } from '../api/services';
import { useSettings } from '../hooks/useSettings';
import styles from '../styles/components/Contact.module.css';
import { ContactFormData, ValidationErrors, SubmitStatus } from '../types';
import { AppError, ValidationError } from '../api/errors';

const Contact: React.FC = () => {
  const [formData, setFormData] = useState<ContactFormData>({
    name: '',
    email: '',
    subject: '',
    message: '',
    website: '', // Honeypot field
  });
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [submitStatus, setSubmitStatus] = useState<SubmitStatus>(null);
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>(
    {}
  );
  const [serverError, setServerError] = useState<string | null>(null);
  const { data: settings, isLoading } = useSettings();
  const { t } = useTranslation();
  const isEnabled = settings?.contactForm === true;

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>): void => {
      const { name, value } = e.target;
      setFormData(prev => ({
        ...prev,
        [name]: value,
      }));
      setValidationErrors(prev => {
        if (prev[name as keyof ValidationErrors]) {
          return {
            ...prev,
            [name]: undefined,
          };
        }
        return prev;
      });
      // Clear server error on user input
      if (serverError) setServerError(null);
    },
    [serverError]
  );

  const validateForm = useCallback((): boolean => {
    const errors: ValidationErrors = {};
    if (!formData.name || formData.name.trim().length < 2) {
      errors.name = [t('contact.errors.name')];
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!formData.email || !emailRegex.test(formData.email)) {
      errors.email = [t('contact.errors.email')];
    }
    if (!formData.subject || formData.subject.trim().length < 5) {
      errors.subject = [t('contact.errors.subject')];
    }
    if (!formData.message || formData.message.trim().length < 10) {
      errors.message = [t('contact.errors.message')];
    }
    if (formData.website && formData.website.trim().length > 0) {
      errors.name = [t('contact.errors.honeypot')];
    }

    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors);
      setSubmitStatus('validation_error');
      return false;
    }
    return true;
  }, [formData, t]);

  const handleSubmit = useCallback(
    async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
      e.preventDefault();
      setIsSubmitting(true);
      setSubmitStatus(null);
      setServerError(null);
      setValidationErrors({});

      if (!validateForm()) {
        setIsSubmitting(false);
        return;
      }

      try {
        await fetchContact(formData);
        setSubmitStatus('success');
        setFormData({
          name: '',
          email: '',
          subject: '',
          message: '',
          website: '',
        });
      } catch (error: unknown) {
        if (error instanceof ValidationError) {
          setValidationErrors(error.errors);
          setSubmitStatus('validation_error');
        } else if (error instanceof AppError) {
          setSubmitStatus('error');
          setServerError(error.message);
          console.error(`Status code ${error.statusCode}: ${error.message}`);
        } else {
          console.error('Unknown error:', error);
          setSubmitStatus('error');
          setServerError(t('contact.error'));
        }
      } finally {
        setIsSubmitting(false);
      }
    },
    [formData, validateForm, t]
  );

  if (isLoading || isEnabled === false) {
    return null;
  }

  return (
    <section id='contact' className={styles.section}>
      <div className={styles.container}>
        <div className={styles.header}>
          <h2 className={styles.title}>{t('contact.title')}</h2>
          <p className={styles.subtitle}>{t('contact.subtitle')}</p>
        </div>

        <div className={styles.formWrapper}>
          <form
            onSubmit={handleSubmit}
            className={styles.contactForm}
            aria-label={t('contact.title')}
          >
            {/* Honeypot field */}
            <input
              type='text'
              name='website'
              value={formData.website || ''}
              onChange={handleChange}
              tabIndex={-1}
              autoComplete='off'
              className={styles.honeypot}
              aria-hidden='true'
            />
            <div className={styles.formGrid}>
              <div className={styles.formField}>
                <label className={styles.fieldLabel} htmlFor='name'>
                  {t('contact.identity')}
                </label>
                <input
                  id='name'
                  type='text'
                  name='name'
                  value={formData.name}
                  onChange={handleChange}
                  placeholder={t('contact.namePlaceholder')}
                  required
                  aria-required='true'
                  aria-invalid={!!validationErrors.name}
                  aria-describedby={
                    validationErrors.name ? 'name-error' : undefined
                  }
                  className={`${styles.formInput} ${
                    validationErrors.name ? styles.inputError : ''
                  }`}
                />
                {validationErrors.name && (
                  <span
                    className={styles.errorText}
                    id='name-error'
                    role='alert'
                  >
                    {validationErrors.name[0]}
                  </span>
                )}
              </div>
              <div className={styles.formField}>
                <label className={styles.fieldLabel} htmlFor='email'>
                  {t('contact.communication')}
                </label>
                <input
                  id='email'
                  type='email'
                  name='email'
                  value={formData.email}
                  onChange={handleChange}
                  placeholder={t('contact.emailPlaceholder')}
                  required
                  aria-required='true'
                  aria-invalid={!!validationErrors.email}
                  aria-describedby={
                    validationErrors.email ? 'email-error' : undefined
                  }
                  className={`${styles.formInput} ${
                    validationErrors.email ? styles.inputError : ''
                  }`}
                />
                {validationErrors.email && (
                  <span
                    className={styles.errorText}
                    id='email-error'
                    role='alert'
                  >
                    {validationErrors.email[0]}
                  </span>
                )}
              </div>
              <div className={styles.formField}>
                <label className={styles.fieldLabel} htmlFor='subject'>
                  {t('contact.topic')}
                </label>
                <input
                  id='subject'
                  type='text'
                  name='subject'
                  value={formData.subject}
                  onChange={handleChange}
                  placeholder={t('contact.subjectPlaceholder')}
                  required
                  aria-required='true'
                  aria-invalid={!!validationErrors.subject}
                  aria-describedby={
                    validationErrors.subject ? 'subject-error' : undefined
                  }
                  className={`${styles.formInput} ${
                    validationErrors.subject ? styles.inputError : ''
                  }`}
                />
                {validationErrors.subject && (
                  <span
                    className={styles.errorText}
                    id='subject-error'
                    role='alert'
                  >
                    {validationErrors.subject[0]}
                  </span>
                )}
              </div>
              <div className={`${styles.formField} ${styles.fullWidth}`}>
                <label className={styles.fieldLabel} htmlFor='message'>
                  {t('contact.transmission')}
                </label>
                <textarea
                  id='message'
                  name='message'
                  value={formData.message}
                  onChange={handleChange}
                  rows={5}
                  placeholder={t('contact.messagePlaceholder')}
                  required
                  aria-required='true'
                  aria-invalid={!!validationErrors.message}
                  aria-describedby={
                    validationErrors.message ? 'message-error' : undefined
                  }
                  className={`${styles.formInput} ${
                    validationErrors.message ? styles.inputError : ''
                  }`}
                ></textarea>
                {validationErrors.message && (
                  <span
                    className={styles.errorText}
                    id='message-error'
                    role='alert'
                  >
                    {validationErrors.message[0]}
                  </span>
                )}
              </div>
            </div>
            <div className={styles.formAction}>
              <button
                type='submit'
                className={styles.submitBtn}
                disabled={isSubmitting}
              >
                {isSubmitting ? t('contact.sending') : t('contact.submit')}
              </button>
            </div>

            {submitStatus === 'success' && (
              <p
                className={styles.successMessage}
                role='status'
                aria-live='polite'
              >
                {t('contact.success')}
              </p>
            )}
            {submitStatus === 'error' && (
              <p className={styles.errorMessage} role='alert'>
                {serverError || t('contact.error')}
              </p>
            )}
            {submitStatus === 'validation_error' && (
              <p className={styles.errorMessage} role='alert'>
                {t('contact.validationError')}
              </p>
            )}
          </form>
        </div>
      </div>
    </section>
  );
};

export default Contact;
