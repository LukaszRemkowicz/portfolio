import React, { useState } from 'react';
import { fetchContact } from './api/services';
import styles from './styles/components/Contact.module.css';
import { ContactFormData, ValidationErrors, SubmitStatus } from './types';

const Contact: React.FC = () => {
  const [formData, setFormData] = useState<ContactFormData>({
    name: '',
    email: '',
    subject: '',
    message: ''
  });
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [submitStatus, setSubmitStatus] = useState<SubmitStatus>(null);
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({});

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>): void => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear validation error for this field when user starts typing
    if (validationErrors[name as keyof ValidationErrors]) {
      setValidationErrors(prev => ({
        ...prev,
        [name]: undefined
      }));
    }
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    setIsSubmitting(true);
    setSubmitStatus(null);
    setValidationErrors({});

    try {
      await fetchContact(formData);
      setSubmitStatus('success');
      setFormData({ name: '', email: '', subject: '', message: '' });
    } catch (error: any) {
      console.error('Failed to send message:', error);
      
      // Handle validation errors from backend
      if (error.response && error.response.data && error.response.data.errors) {
        setValidationErrors(error.response.data.errors);
        setSubmitStatus('validation_error');
      } else {
        setSubmitStatus('error');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section id="contact" className={styles.contactContainer}>
      <div className={styles.contactContent}>
        <h2 className={styles.title}>Get in Touch</h2>
        <p className={styles.subtitle}>
          Have a question or want to collaborate? Feel free to reach out!
        </p>
        
        <form className={styles.contactForm} onSubmit={handleSubmit}>
          <div className={styles.formRow}>
            <div className={styles.formGroup}>
              <label htmlFor="name" className={styles.label}>Name</label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                className={`${styles.input} ${validationErrors.name ? styles.inputError : ''}`}
                required
              />
              {validationErrors.name && (
                <span className={styles.errorText}>{validationErrors.name[0]}</span>
              )}
            </div>
            <div className={styles.formGroup}>
              <label htmlFor="email" className={styles.label}>Email</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className={`${styles.input} ${validationErrors.email ? styles.inputError : ''}`}
                required
              />
              {validationErrors.email && (
                <span className={styles.errorText}>{validationErrors.email[0]}</span>
              )}
            </div>
          </div>
          
          <div className={styles.formGroup}>
            <label htmlFor="subject" className={styles.label}>Subject</label>
            <input
              type="text"
              id="subject"
              name="subject"
              value={formData.subject}
              onChange={handleChange}
              className={`${styles.input} ${validationErrors.subject ? styles.inputError : ''}`}
              required
            />
            {validationErrors.subject && (
              <span className={styles.errorText}>{validationErrors.subject[0]}</span>
            )}
          </div>
          
          <div className={styles.formGroup}>
            <label htmlFor="message" className={styles.label}>Message</label>
            <textarea
              id="message"
              name="message"
              value={formData.message}
              onChange={handleChange}
              className={`${styles.textarea} ${validationErrors.message ? styles.inputError : ''}`}
              rows={5}
              required
            />
            {validationErrors.message && (
              <span className={styles.errorText}>{validationErrors.message[0]}</span>
            )}
          </div>
          
          <button 
            type="submit" 
            className={styles.submitButton}
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Sending...' : 'Send Message'}
          </button>
          
          {submitStatus === 'success' && (
            <p className={styles.successMessage}>
              Thank you! Your message has been sent successfully.
            </p>
          )}
          
          {submitStatus === 'validation_error' && (
            <p className={styles.errorMessage}>
              Please correct the errors above and try again.
            </p>
          )}
          
          {submitStatus === 'error' && (
            <p className={styles.errorMessage}>
              Sorry, there was an error sending your message. Please try again.
            </p>
          )}
        </form>
      </div>
    </section>
  );
};

export default Contact;
