/* Shared page template for the VTP website generator (evaluated inside run_script). */

const ICONS = {
  phone: '<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>',
  mail: '<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>',
  linkedin: '<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"/><rect width="4" height="12" x="2" y="9"/><circle cx="4" cy="4" r="2"/></svg>',
  doc: '<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/></svg>',
  pin: '<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0z"/><circle cx="12" cy="10" r="3"/></svg>',
  chev: '<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>',
  discord: '<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="12" r="1"/><circle cx="15" cy="12" r="1"/><path d="M7.5 7.2c1.4-.7 2.9-1.2 4.5-1.2s3.1.5 4.5 1.2"/><path d="M7.5 16.8c1.4.7 2.9 1.2 4.5 1.2s3.1-.5 4.5-1.2"/><path d="M15.5 17.5 17 20c2-1 3.5-2 4.5-3.5-.5-4.5-1.8-8.2-3.8-11.2-1.1-.4-2.2-.7-3.2-.8l-.8 1.7"/><path d="m8.5 17.5L7 20c-2-1-3.5-2-4.5-3.5C3 12 4.3 8.3 6.3 5.3c1.1-.4 2.2-.7 3.2-.8l.8 1.7"/></svg>'
};

function ico(name) { return '<span class="ico">' + ICONS[name] + '</span>'; }

function embedBox(label, minH) {
  return '<div class="embed-placeholder"' + (minH ? ' style="min-height:' + minH + 'px"' : '') + '>' +
    '<span class="label">' + label + '</span>' +
    '<span class="note">Embed to be inserted here.</span>' +
    '</div>';
}

function band(h1, subHtml) {
  return '<div class="page-band"><div class="container"><h1>' + h1 + '</h1>' + (subHtml || '') + '</div></div>';
}

const ORG_JSONLD = {
  "@context": "https://schema.org",
  "@type": "NGO",
  "@id": "https://vonterraproject.org/#organization",
  "name": "The Von Terra Project",
  "legalName": "The Von Terra Project, Inc.",
  "alternateName": "VTP",
  "url": "https://vonterraproject.org/",
  "logo": "https://vonterraproject.org/website_images/VTP%20Logo.png",
  "image": "https://vonterraproject.org/website_images/VTP%20Logo.png",
  "description": "The Von Terra Project strives to bridge the gap between people, policy, and technology to connect communities, build cybersecurity resilience, strengthen preparedness, optimize response, and fortify our collective defenses against emerging challenges.",
  "email": "contact@vonterraproject.org",
  "telephone": "(202) 870-9825",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "17533 Redland Rd. #5582",
    "addressLocality": "Derwood",
    "addressRegion": "MD",
    "postalCode": "20855",
    "addressCountry": "US"
  },
  "taxID": "33-2041628",
  "identifier": [
    {
      "@type": "PropertyValue",
      "propertyID": "EIN",
      "value": "33-2041628"
    },
    {
      "@type": "PropertyValue",
      "propertyID": "MD SDAT Department ID",
      "value": "D25517715"
    }
  ],
  "foundingDate": "2024-11-02",
  "nonprofitStatus": "Nonprofit501c3",
  "sameAs": [
    "https://www.linkedin.com/company/vonterraproject/",
    "https://discord.gg/4Yh52nTNns"
  ]
};

const HEADER =
'<a class="skip-link" href="#main">Skip to main content</a>\n' +
'<header class="site-header">\n' +
'  <div class="container">\n' +
'    <a class="brand" href="index.html"><img src="website_images/VTP Logo.png" alt="The Von Terra Project logo"></a>\n' +
'    <button class="nav-toggle" aria-label="Open menu" aria-expanded="false"><span></span><span></span><span></span></button>\n' +
'    <nav class="site-nav">\n' +
'      <div class="nav-item"><a class="nav-link" href="index.html">Home</a></div>\n' +
'      <div class="nav-item"><a class="nav-link" href="cyberhero.html">CyberHERo</a></div>\n' +
'      <div class="nav-item"><a class="nav-link" href="flyspacea.html">FlySpaceA</a></div>\n' +
'      <div class="nav-item dropdown">\n' +
'        <a class="nav-link" href="programs.html" aria-expanded="false" aria-haspopup="true">Programs</a>\n' +
'        <div class="dropdown-menu">\n' +
'          <a href="programs.html">All Programs</a>\n' +
'          <a href="resource-hub.html">Cybersecurity Resource Hub</a>\n' +
'          <a href="documents/certification-program/index.html">Certification Program</a>\n' +
'          <a href="self-assessment.html">Self-Assessment Tool</a>\n' +
'          <a href="start-security.html">Start Improving Your Security</a>\n' +
'        </div>\n' +
'      </div>\n' +
'      <div class="nav-item dropdown">\n' +
'        <a class="nav-link" href="about.html" aria-expanded="false" aria-haspopup="true">About Us</a>\n' +
'        <div class="dropdown-menu">\n' +
'          <a href="about.html">About Overview</a>\n' +
'          <a href="team.html">Team</a>\n' +
'          <a href="lines-of-effort.html">Lines Of Effort</a>\n' +
'          <a href="faq.html">FAQ</a>\n' +
'          <a href="documents.html">Documents</a>\n' +
'        </div>\n' +
'      </div>\n' +
'      <a class="btn btn-donate" href="donate.html">Donate</a>\n' +
'    </nav>\n' +
'  </div>\n' +
'</header>\n';

const FOOTER =
'<footer class="site-footer">\n' +
'  <div class="container">\n' +
'    <div class="footer-cols">\n' +
'      <div>\n' +
'        <img class="footer-logo" src="website_images/VTP Logo.png" alt="The Von Terra Project logo">\n' +
'        <p class="fine">The Von Terra Project is a registered 501(c)(3) nonprofit organization.</p>\n' +
'        <p class="fine">EIN: 33-2041628</p>\n' +
'      </div>\n' +
'      <div>\n' +
'        <h2 class="footer-h">Contact Us</h2>\n' +
'        <div class="icon-line">' + ico('pin') + '<span>17533 Redland Rd. #5582, Derwood, MD 20855</span></div>\n' +
'        <div class="icon-line">' + ico('phone') + '<span>(202) 870-9825</span></div>\n' +
'        <div class="icon-line">' + ico('mail') + '<a href="mailto:contact@vonterraproject.org">contact@vonterraproject.org</a></div>\n' +
'      </div>\n' +
'      <div>\n' +
'        <h2 class="footer-h">Follow Us</h2>\n' +
'        <div class="social-row" style="justify-content:flex-start">\n' +
'          <a href="https://www.linkedin.com/company/vonterraproject/" target="_blank" rel="noopener" aria-label="LinkedIn">' + ico('linkedin') + '</a>\n' +
'          <a href="mailto:contact@vonterraproject.org" aria-label="Email">' + ico('mail') + '</a>\n' +
'          <a href="https://discord.gg/4Yh52nTNns" target="_blank" rel="noopener">Discord</a>\n' +
'        </div>\n' +
'      </div>\n' +
'    </div>\n' +
'  </div>\n' +
'  <div class="footer-bottom">\n' +
'    <div class="container">\n' +
'      <span>© 2025 The Von Terra Project. All Rights Reserved.</span><span class="sep">|</span>' +
'<a href="terms.html">Terms &amp; Conditions</a><span class="sep">|</span>' +
'<a href="contact.html">Contact Us</a><span class="sep">|</span>' +
'<a href="donate.html">Donate</a><span class="sep">|</span>' +
'<a href="index.html">Home</a>\n' +
'    </div>\n' +
'  </div>\n' +
'</footer>\n';

function page(title, body) {
  return '<!DOCTYPE html>\n<html lang="en">\n<head>\n' +
    '<meta charset="utf-8">\n' +
'<meta http-equiv="Content-Security-Policy" content="default-src \'self\'; script-src \'self\' https://donorbox.org \'unsafe-inline\'; style-src \'self\' \'unsafe-inline\'; img-src \'self\' data: https:; font-src \'self\'; frame-src https://donorbox.org https://drive.google.com https://docs.google.com; connect-src \'self\' https://donorbox.org; form-action \'self\' https://donorbox.org; base-uri \'self\'; object-src \'none\'; frame-ancestors \'self\'">\n' +
'<meta name="referrer" content="strict-origin-when-cross-origin">\n' +
'<meta property="og:type" content="website">\n' +
'<meta property="og:site_name" content="The Von Terra Project">\n' +
'<meta property="og:image" content="https://vonterraproject.org/website_images/VTP%20Logo.png">\n' +
'<meta name="twitter:card" content="summary">\n' +
    '<meta name="viewport" content="width=device-width, initial-scale=1">\n' +
    '<title>' + title + ' — The Von Terra Project</title>\n' +
    '<link rel="stylesheet" href="css/style.css">\n' +
    '<link rel="icon" type="image/png" href="website_images/VTP Logo.png">\n' +
'<script type="application/ld+json">\n' + JSON.stringify(ORG_JSONLD, null, 2) + '\n</script>\n' +
    '</head>\n<body>\n' + HEADER + '<main>\n' + body + '\n</main>\n' + FOOTER +
    '<script src="js/main.js"></script>\n</body>\n</html>\n';
}

/* expose */
globalThis.VTP = { ICONS, ico, embedBox, band, page };
