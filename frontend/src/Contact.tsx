import React from "react";
import styles from "./styles/components/Contact.module.css";

const Contact: React.FC = () => {
  return (
    <section id="contact" className={styles.section}>
      <div className={styles.container}>
        <div className={styles.header}>
          <h2 className={styles.title}>
            Get In <span className={styles.accent}>Touch</span>
          </h2>
          <p className={styles.subtitle}>
            Interested in a print, a workshop, or a collaboration? Drop me a
            message below.
          </p>
        </div>

        <div className={styles.formContainer}>
          <form className={styles.grid}>
            <div className={styles.field}>
              <label className={styles.label}>Your Name</label>
              <input
                type="text"
                placeholder="John Doe"
                className={styles.input}
              />
            </div>
            <div className={styles.field}>
              <label className={styles.label}>Email Address</label>
              <input
                type="email"
                placeholder="john@example.com"
                className={styles.input}
              />
            </div>
            <div className={`${styles.field} ${styles.full}`}>
              <label className={styles.label}>Subject</label>
              <input
                type="text"
                placeholder="Print Inquiry / Project Proposal"
                className={styles.input}
              />
            </div>
            <div className={`${styles.field} ${styles.full}`}>
              <label className={styles.label}>Message</label>
              <textarea
                rows={5}
                placeholder="How can I help you?"
                className={styles.textarea}
              ></textarea>
            </div>
            <div className={`${styles.field} ${styles.full}`}>
              <button type="submit" className={styles.submitBtn}>
                Send Transmission ✦
              </button>
            </div>
          </form>
        </div>
      </div>
    </section>
  );
};

export default Contact;
