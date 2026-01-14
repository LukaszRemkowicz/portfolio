import React, { useState, useEffect } from "react";
import { fetchContact, fetchEnabledFeatures } from "./api/services";
import styles from "./styles/components/Contact.module.css";
import { ContactFormData, ValidationErrors, SubmitStatus } from "./types";

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
  const [isEnabled, setIsEnabled] = useState<boolean | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const checkEnablement = async () => {
      try {
        const features = await fetchEnabledFeatures();
        setIsEnabled(features.contactForm === true);
      } catch (error) {
        console.error("Failed to check feature enablement:", error);
        setIsEnabled(false);
      } finally {
        setIsLoading(false);
      }
    };
    checkEnablement();
  }, []);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ): void => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    if (validationErrors[name as keyof ValidationErrors]) {
      setValidationErrors((prev) => ({
        ...prev,
        [name]: undefined,
      }));
    }
  };

  const validateForm = (): boolean => {
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
  };

  const handleSubmit = async (
    e: React.FormEvent<HTMLFormElement>,
  ): Promise<void> => {
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
      console.error("Failed to send message:", error);
      // Simplified error handling for brevity, retaining essential logic
      setSubmitStatus("error");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading || isEnabled === false) {
    return null;
  }

  return (
    <section id="contact" className={styles.section}>
      <div className={styles.container}>
        <div className={styles.header}>
          <h2 className={styles.title}>Direct Inquiry</h2>
          <p className={styles.subtitle}>
            Interested in prints or technical collaboration? Let's connect.
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
                <label className={styles.fieldLabel}>Identity</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="Name"
                  className={`${styles.formInput} ${validationErrors.name ? styles.inputError : ""}`}
                />
                {validationErrors.name && (
                  <span className={styles.errorText}>
                    {validationErrors.name[0]}
                  </span>
                )}
              </div>
              <div className={styles.formField}>
                <label className={styles.fieldLabel}>Communication</label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="Email Address"
                  className={`${styles.formInput} ${validationErrors.email ? styles.inputError : ""}`}
                />
                {validationErrors.email && (
                  <span className={styles.errorText}>
                    {validationErrors.email[0]}
                  </span>
                )}
              </div>
              <div className={styles.formField}>
                <label className={styles.fieldLabel}>Topic</label>
                <input
                  type="text"
                  name="subject"
                  value={formData.subject}
                  onChange={handleChange}
                  placeholder="Subject"
                  className={`${styles.formInput} ${validationErrors.subject ? styles.inputError : ""}`}
                />
                {validationErrors.subject && (
                  <span className={styles.errorText}>
                    {validationErrors.subject[0]}
                  </span>
                )}
              </div>
              <div className={`${styles.formField} ${styles.fullWidth}`}>
                <label className={styles.fieldLabel}>Transmission</label>
                <textarea
                  name="message"
                  value={formData.message}
                  onChange={handleChange}
                  rows={5}
                  placeholder="How can I help you?"
                  className={`${styles.formInput} ${validationErrors.message ? styles.inputError : ""}`}
                ></textarea>
                {validationErrors.message && (
                  <span className={styles.errorText}>
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
              <p className={styles.successMessage}>
                Thank you! Your message has been sent successfully.
              </p>
            )}
            {submitStatus === "error" && (
              <p className={styles.errorMessage}>
                Sorry, there was an error sending your message. Please try
                again.
              </p>
            )}
          </form>
        </div>
      </div>
    </section>
  );
};

export default Contact;
