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
    website: "", // Honeypot field - should remain empty
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
        setIsEnabled(false); // Fallback to disabled on error
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
    // Clear validation error for this field when user starts typing
    if (validationErrors[name as keyof ValidationErrors]) {
      setValidationErrors((prev) => ({
        ...prev,
        [name]: undefined,
      }));
    }
  };

  const validateForm = (): boolean => {
    const errors: ValidationErrors = {};

    // Validate name (at least 2 characters)
    if (!formData.name || formData.name.trim().length < 2) {
      errors.name = ["Name must be at least 2 characters long."];
    }

    // Validate email (must be valid email format)
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!formData.email || !emailRegex.test(formData.email)) {
      errors.email = ["Please provide a valid email address."];
    }

    // Validate subject (at least 5 characters)
    if (!formData.subject || formData.subject.trim().length < 5) {
      errors.subject = ["Subject must be at least 5 characters long."];
    }

    // Validate message (at least 10 characters)
    if (!formData.message || formData.message.trim().length < 10) {
      errors.message = ["Message must be at least 10 characters long."];
    }

    // Check honeypot field (should be empty for humans)
    if (formData.website && formData.website.trim().length > 0) {
      // Bot detected - silently fail (don't show error to bot)
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

    // Frontend validation FIRST - don't send invalid data to backend
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

      // Handle validation errors and rate limiting from backend
      if (error && typeof error === "object" && "response" in error) {
        const axiosError = error as {
          response?: {
            status?: number;
            data?:
              | ValidationErrors
              | {
                  message?: string;
                  detail?: string;
                  errors?: ValidationErrors;
                };
          };
        };
        const statusCode = axiosError.response?.status;
        const responseData = axiosError.response?.data;

        if (statusCode === 429) {
          // Rate limit exceeded - show special message with custom UI
          // Backend provides custom message in response.data.detail or response.data.message
          const message =
            (responseData && "detail" in responseData && responseData.detail) ||
            (responseData && "message" in responseData && responseData.message);
          if (message) {
            console.log(`Rate limit message: ${message}`);
          }
          setSubmitStatus("rate_limited");
          setValidationErrors({});
        } else if (statusCode === 400 && responseData) {
          // DRF returns validation errors directly in response.data as {field: ["error"]}
          // Check if response.data has validation error fields (name, email, subject, message)
          const hasValidationErrors =
            "name" in responseData ||
            "email" in responseData ||
            "subject" in responseData ||
            "message" in responseData ||
            ("errors" in responseData && responseData.errors);

          if (hasValidationErrors) {
            // DRF format: {field: ["error"]} directly in response.data
            // Or wrapped format: {errors: {field: ["error"]}}
            const errors =
              ("errors" in responseData && responseData.errors) ||
              (responseData as ValidationErrors);
            setValidationErrors(errors as ValidationErrors);
            setSubmitStatus("validation_error");
          } else {
            setSubmitStatus("error");
          }
        } else {
          setSubmitStatus("error");
        }
      } else {
        setSubmitStatus("error");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading || isEnabled === false) {
    return null;
  }

  return (
    <section id="contact" className={styles.contactContainer}>
      <div className={styles.contactContent}>
        <h2 className={styles.title}>Get in Touch</h2>
        <p className={styles.subtitle}>
          Have a question or want to collaborate? Feel free to reach out!
        </p>

        <form className={styles.contactForm} onSubmit={handleSubmit}>
          {/* Honeypot field - invisible to humans, bots will fill it */}
          <input
            type="text"
            name="website"
            value={formData.website || ""}
            onChange={handleChange}
            tabIndex={-1}
            autoComplete="off"
            style={{
              position: "absolute",
              left: "-9999px",
              opacity: 0,
              pointerEvents: "none",
              height: 0,
              width: 0,
            }}
            aria-hidden="true"
          />
          <div className={styles.formRow}>
            <div className={styles.formGroup}>
              <label htmlFor="name" className={styles.label}>
                Name
              </label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                className={`${styles.input} ${
                  validationErrors.name ? styles.inputError : ""
                }`}
                required
              />
              {validationErrors.name && (
                <span className={styles.errorText}>
                  {validationErrors.name[0]}
                </span>
              )}
            </div>
            <div className={styles.formGroup}>
              <label htmlFor="email" className={styles.label}>
                Email
              </label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className={`${styles.input} ${
                  validationErrors.email ? styles.inputError : ""
                }`}
                required
              />
              {validationErrors.email && (
                <span className={styles.errorText}>
                  {validationErrors.email[0]}
                </span>
              )}
            </div>
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="subject" className={styles.label}>
              Subject
            </label>
            <input
              type="text"
              id="subject"
              name="subject"
              value={formData.subject}
              onChange={handleChange}
              className={`${styles.input} ${
                validationErrors.subject ? styles.inputError : ""
              }`}
              required
            />
            {validationErrors.subject && (
              <span className={styles.errorText}>
                {validationErrors.subject[0]}
              </span>
            )}
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="message" className={styles.label}>
              Message
            </label>
            <textarea
              id="message"
              name="message"
              value={formData.message}
              onChange={handleChange}
              className={`${styles.textarea} ${
                validationErrors.message ? styles.inputError : ""
              }`}
              rows={5}
              required
            />
            {validationErrors.message && (
              <span className={styles.errorText}>
                {validationErrors.message[0]}
              </span>
            )}
          </div>

          <button
            type="submit"
            className={styles.submitButton}
            disabled={isSubmitting}
          >
            {isSubmitting ? "Sending..." : "Send Message"}
          </button>

          {submitStatus === "success" && (
            <p className={styles.successMessage}>
              Thank you! Your message has been sent successfully.
            </p>
          )}

          {submitStatus === "validation_error" && (
            <p className={styles.errorMessage}>
              Please correct the errors above and try again.
            </p>
          )}

          {submitStatus === "rate_limited" && (
            <div className={styles.rateLimitMessage}>
              <p className={styles.rateLimitTitle}>Too many requests</p>
              <p className={styles.rateLimitText}>
                You&apos;ve submitted too many messages recently. Please wait up
                to 1 hour before trying again.
              </p>
            </div>
          )}

          {submitStatus === "error" && (
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
