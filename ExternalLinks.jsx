/**
 * ExternalLinks Component - Gold Tier Dashboard
 * 
 * FIXED: All external links now open correctly in new tabs
 * with proper security attributes
 * 
 * Usage: 
 * import ExternalLinks from './components/ExternalLinks';
 * 
 * <ExternalLinks 
 *   whatsappNumber="923000000000"
 *   linkedinUsername="yourusername"
 *   gmailEmail="youremail@gmail.com"
 * />
 */

import React from 'react';
import './ExternalLinks.css';

const ExternalLinks = ({ 
  whatsappNumber = '923000000000',
  whatsappMessage = 'Hello! I need assistance.',
  linkedinUsername = 'yourusername',
  gmailEmail = 'youremail@gmail.com'
}) => {
  
  // Generate correct URLs
  const getWhatsAppLink = () => {
    return `https://wa.me/${whatsappNumber}?text=${encodeURIComponent(whatsappMessage)}`;
  };

  const getLinkedInLink = () => {
    return `https://www.linkedin.com/in/${linkedinUsername}`;
  };

  const getGmailLink = () => {
    return `mailto:${gmailEmail}`;
  };

  // Common props for all external links
  const externalLinkProps = {
    target: '_blank',
    rel: 'noopener noreferrer',
    className: 'external-link'
  };

  return (
    <div className="external-links-container">
      <h2>Quick Links</h2>
      
      <div className="links-grid">
        {/* WhatsApp Link - FIXED */}
        <div className="link-card whatsapp">
          <div className="icon">💬</div>
          <h3>WhatsApp</h3>
          <p>Send messages via WhatsApp Business</p>
          <a 
            href={getWhatsAppLink()}
            target="_blank"
            rel="noopener noreferrer"
            className="link-button whatsapp-btn"
            aria-label="Open WhatsApp"
          >
            Open WhatsApp ↗
          </a>
        </div>

        {/* LinkedIn Link - FIXED */}
        <div className="link-card linkedin">
          <div className="icon">💼</div>
          <h3>LinkedIn</h3>
          <p>Connect on LinkedIn</p>
          <a 
            href={getLinkedInLink()}
            target="_blank"
            rel="noopener noreferrer"
            className="link-button linkedin-btn"
            aria-label="Open LinkedIn"
          >
            Open LinkedIn ↗
          </a>
        </div>

        {/* Gmail Link - FIXED */}
        <div className="link-card gmail">
          <div className="icon">📧</div>
          <h3>Gmail</h3>
          <p>Send emails via Gmail</p>
          <a 
            href={getGmailLink()}
            target="_blank"
            rel="noopener noreferrer"
            className="link-button gmail-btn"
            aria-label="Open Gmail"
          >
            Open Gmail ↗
          </a>
        </div>
      </div>
    </div>
  );
};

export default ExternalLinks;
