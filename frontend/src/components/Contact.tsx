import React, { useState, useCallback } from "react";
import { fetchContact } from "../api/services";
import { useAppStore } from "../store/useStore";
import styles from "../styles/components/Contact.module.css";
import { ContactFormData, ValidationErrors, SubmitStatus } from "../types";
import { AppError, ValidationError } from "../api/errors";

const Contact: React.FC = () => {
  const [formData, setFormData] = useState<ContactFormData>({
    name: "",
    email: "",
    subject: "",
    message: "",
    website: "", // Honeypot field
  });
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [submitStatus, setSubmitStatus] = useState<SubmitStatus>(null);
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>(
    {},
  );
  const { features, isInitialLoading: isLoading } = useAppStore();
  const isEnabled = features?.contactForm === true;

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>): void => {
      const { name, value } = e.target;
      setFormData((prev) => ({
        ...prev,
        [name]: value,
      }));
      setValidationErrors((prev) => {
        if (prev[name as keyof ValidationErrors]) {
          return {
            ...prev,
            [name]: undefined,
          };
        }
        return prev;
      });
    },
    [],
  );

  const validateForm = useCallback((): boolean => {
    const errors: ValidationErrors = {};
    if (!formData.name || formData.name.trim().length < 2) {
      errors.name = ["Name must be at least 2 characters long."];
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!formData.email || !emailRegex.test(formData.email)) {
      errors.email = ["Please provide a valid email address."];
    }
    if (!formData.subject || formData.subject.trim().length < 5) {
      errors.subject = ["Subject must be at least 5 characters long."];
    }
    if (!formData.message || formData.message.trim().length < 10) {
      errors.message = ["Message must be at least 10 characters long."];
    }
    if (formData.website && formData.website.trim().length > 0) {
      errors.name = ["Please correct the errors above and try again."];
    }

    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors);
      setSubmitStatus("validation_error");
      return false;
    }
    return true;
  }, [formData]);

  const handleSubmit = useCallback(
    async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
      e.preventDefault();
      setIsSubmitting(true);
      setSubmitStatus(null);
      setValidationErrors({});

      if (!validateForm()) {
        setIsSubmitting(false);
        return;
      }

      try {
        await fetchContact(formData);
        setSubmitStatus("success");
        setFormData({
          name: "",
          email: "",
          subject: "",
          message: "",
          website: "",
        });
      } catch (error: unknown) {
        if (error instanceof ValidationError) {
          setValidationErrors(error.errors);
          setSubmitStatus("validation_error");
        } else if (error instanceof AppError) {
          setSubmitStatus("error");
          // Optionally store the specific error message to display to the user
          console.error(`Status code ${error.statusCode}: ${error.message}`);
        } else {
          console.error("Unknown error:", error);
          setSubmitStatus("error");
        }
      } finally {
        setIsSubmitting(false);
      }
    },
    [formData, validateForm],
  );

  if (isLoading || isEnabled === false) {
    return null;
  }

  return (
    <section id="contact" className={styles.section}>
      <div className={styles.container}>
        <div className={styles.header}>
          <h2 className={styles.title}>Direct Inquiry</h2>
          <p className={styles.subtitle}>
            Interested in prints or technical collaboration? Let&apos;s connect.
          </p>
        </div>

        <div className={styles.formWrapper}>
          <form onSubmit={handleSubmit} className={styles.contactForm}>
            {/* Honeypot field */}
            <input
              type="text"
              name="website"
              value={formData.website || ""}
              onChange={handleChange}
              tabIndex={-1}
              autoComplete="off"
              className={styles.honeypot}
              aria-hidden="true"
            />
            <div className={styles.formGrid}>
              <div className={styles.formField}>
                <label className={styles.fieldLabel} htmlFor="name">
                  Identity
                </label>
                <input
                  id="name"
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="Your Name"
                  required
                  aria-required="true"
                  aria-invalid={!!validationErrors.name}
                  aria-describedby={
                    validationErrors.name ? "name-error" : undefined
                  }
                  className={`${styles.formInput} ${validationErrors.name ? styles.inputError : ""}`}
                />
                {validationErrors.name && (
                  <span
                    className={styles.errorText}
                    id="name-error"
                    role="alert"
                  >
                    {validationErrors.name[0]}
                  </span>
                )}
              </div>
              <div className={styles.formField}>
                <label className={styles.fieldLabel} htmlFor="email">
                  Communication
                </label>
                <input
                  id="email"
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="Email Address"
                  required
                  aria-required="true"
                  aria-invalid={!!validationErrors.email}
                  aria-describedby={
                    validationErrors.email ? "email-error" : undefined
                  }
                  className={`${styles.formInput} ${validationErrors.email ? styles.inputError : ""}`}
                />
                {validationErrors.email && (
                  <span
                    className={styles.errorText}
                    id="email-error"
                    role="alert"
                  >
                    {validationErrors.email[0]}
                  </span>
                )}
              </div>
              <div className={styles.formField}>
                <label className={styles.fieldLabel} htmlFor="subject">
                  Topic
                </label>
                <input
                  id="subject"
                  type="text"
                  name="subject"
                  value={formData.subject}
                  onChange={handleChange}
                  placeholder="Subject"
                  required
                  aria-required="true"
                  aria-invalid={!!validationErrors.subject}
                  aria-describedby={
                    validationErrors.subject ? "subject-error" : undefined
                  }
                  className={`${styles.formInput} ${validationErrors.subject ? styles.inputError : ""}`}
                />
                {validationErrors.subject && (
                  <span
                    className={styles.errorText}
                    id="subject-error"
                    role="alert"
                  >
                    {validationErrors.subject[0]}
                  </span>
                )}
              </div>
              <div className={`${styles.formField} ${styles.fullWidth}`}>
                <label className={styles.fieldLabel} htmlFor="message">
                  Transmission
                </label>
                <textarea
                  id="message"
                  name="message"
                  value={formData.message}
                  onChange={handleChange}
                  rows={5}
                  placeholder="How can I help you?"
                  required
                  aria-required="true"
                  aria-invalid={!!validationErrors.message}
                  aria-describedby={
                    validationErrors.message ? "message-error" : undefined
                  }
                  className={`${styles.formInput} ${validationErrors.message ? styles.inputError : ""}`}
                ></textarea>
                {validationErrors.message && (
                  <span
                    className={styles.errorText}
                    id="message-error"
                    role="alert"
                  >
                    {validationErrors.message[0]}
                  </span>
                )}
              </div>
            </div>
            <div className={styles.formAction}>
              <button
                type="submit"
                className={styles.submitBtn}
                disabled={isSubmitting}
              >
                {isSubmitting ? "Sending..." : "Submit Inquiry"}
              </button>
            </div>

            {submitStatus === "success" && (
              <p
                className={styles.successMessage}
                role="status"
                aria-live="polite"
              >
                Thank you! Your message has been sent successfully.
              </p>
            )}
            {submitStatus === "error" && (
              <p className={styles.errorMessage} role="alert">
                Transmission failure. Please check your signal or try again
                later.
              </p>
            )}
            {submitStatus === "validation_error" && (
              <p className={styles.errorMessage} role="alert">
                One or more details in your inquiry require adjustment.
              </p>
            )}
          </form>
        </div>
      </div>
    </section>
  );
};

export default Contact;
