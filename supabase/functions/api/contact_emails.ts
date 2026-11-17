// Port of backend/inbox/templates/inbox/email/contact_*.html (markup kept identical; only Django
// tags replaced). Every {{ }} value is autoescaped like Django.
const ESC: Record<string, string> = {
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#x27;",
};
export const esc = (v: string | number): string => String(v).replace(/[&<>"']/g, (c) => ESC[c]);
/** Django `linebreaksbr` after autoescape: normalise newlines, then \n -> <br>. */
export const br = (v: string): string => esc(v).replace(/\r\n|\r/g, "\n").replace(/\n/g, "<br>");

export type OwnerCtx = {
  portfolio_owner: string;
  subject: string;
  sender_name: string;
  sender_email: string;
  received_at: string;
  message_id: number;
  message: string;
};

export type SenderCtx = {
  portfolio_owner: string;
  gallery_url: string;
  instagram_url: string;
  facebook_url: string;
  astrobin_url: string;
  copyright_year: number;
};

export function ownerHtml(
  { portfolio_owner, subject, sender_name, sender_email, received_at, message_id, message }:
    OwnerCtx,
): string {
  return `<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml"
    xmlns:o="urn:schemas-microsoft-com:office:office">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="color-scheme" content="light dark" />
    <meta name="supported-color-schemes" content="light dark" />
    <title>New Contact Message</title>

    <!--[if gte mso 9]>
    <xml>
        <o:OfficeDocumentSettings>
            <o:AllowPNG/>
            <o:PixelsPerInch>96</o:PixelsPerInch>
        </o:OfficeDocumentSettings>
    </xml>
    <![endif]-->

    <!--[if mso]>
    <style type="text/css">
        table, td { mso-table-lspace: 0pt !important; mso-table-rspace: 0pt !important; }
    </style>
    <![endif]-->

    <style>
        body, table, td, a {
            -webkit-text-size-adjust: 100%;
            -ms-text-size-adjust: 100%;
        }

        table {
            border-collapse: collapse !important;
        }

        img {
            -ms-interpolation-mode: bicubic;
            border: 0;
            height: auto;
            line-height: 100%;
            outline: none;
            text-decoration: none;
        }

        :root {
            color-scheme: light dark;
        }

        @media screen and (max-width: 600px) {
            body, .body, table, td {
                max-width: 100% !important;
                overflow-x: hidden !important;
            }

            .container {
                width: 100% !important;
                max-width: 100% !important;
            }

            .mobile-padding {
                padding-left: 18px !important;
                padding-right: 18px !important;
            }
        }

        u+.body .wrapper {
            background-color: transparent !important;
        }

        u+.body .container-bg,
        u+.body .panel-bg,
        u+.body .footer-bg {
            background-color: #ffffff !important;
        }

        u+.body .text-main {
            color: #0f172a !important;
        }

        u+.body .text-muted {
            color: #475569 !important;
        }

        u+.body .text-faint {
            color: #64748b !important;
        }

        u+.body .text-accent {
            color: #78c2e6 !important;
        }

        [data-ogsc] .wrapper {
            background-color: transparent !important;
        }

        [data-ogsc] .container-bg,
        [data-ogsc] .panel-bg,
        [data-ogsc] .footer-bg {
            background-color: #0e1319 !important;
        }

        [data-ogsc] .text-main {
            color: #f8fafc !important;
        }

        [data-ogsc] .text-muted {
            color: #cbd5e1 !important;
        }

        [data-ogsc] .text-faint {
            color: #94a3b8 !important;
        }

        [data-ogsc] .text-accent {
            color: #78c2e6 !important;
        }

        [data-ogsc] .divider {
            border-top-color: #263445 !important;
        }

        [data-ogsc] .border-strong {
            border-color: #263445 !important;
        }

        @media (prefers-color-scheme: dark) {
            body, .body, .wrapper {
                background-color: transparent !important;
                color: #f8fafc !important;
            }

            .container-bg,
            .panel-bg,
            .footer-bg {
                background-color: #0e1319 !important;
            }

            .text-main {
                color: #f8fafc !important;
            }

            .text-muted {
                color: #cbd5e1 !important;
            }

            .text-faint {
                color: #94a3b8 !important;
            }

            .text-accent {
                color: #78c2e6 !important;
            }

            .divider {
                border-top-color: #263445 !important;
            }

            .border-strong {
                border-color: #263445 !important;
            }
        }
    </style>
</head>

<body class="body" style="margin:0; padding:0; background-color:transparent; color:#0f172a;">
    <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" class="wrapper"
        style="background-color:transparent;">
        <tr>
            <td align="center" style="padding:40px 16px;">
                <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="600"
                    class="container container-bg border-strong"
                    style="width:600px; max-width:600px; background-color:#ffffff; border:1px solid #dbe4f0; border-radius:18px; overflow:hidden;">

                    <tr>
                        <td align="center" class="panel-bg"
                            style="padding:32px 24px 22px 24px; background-color:#ffffff;">
                            <p class="text-faint"
                                style="margin:0 0 10px 0; font-family:Arial, sans-serif; font-size:11px; letter-spacing:2px; text-transform:uppercase; color:#64748b;">
                                ${esc(portfolio_owner)}
                            </p>
                            <h1 class="text-main"
                                style="margin:0; font-family:'Times New Roman', Times, serif; font-size:34px; line-height:1.15; font-weight:400; color:#0f172a;">
                                New Contact Message
                            </h1>
                            <p class="text-accent"
                                style="margin:14px 0 0 0; font-family:Arial, sans-serif; font-size:13px; font-weight:700; letter-spacing:2px; text-transform:uppercase; color:#78c2e6;">
                                ${esc(subject)}
                            </p>
                        </td>
                    </tr>

                    <tr>
                        <td align="center" class="panel-bg mobile-padding"
                            style="padding:0 32px 36px 32px; background-color:#ffffff;">
                            <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                                <tr>
                                    <td style="padding-bottom:14px;">
                                        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%"
                                            style="background-color:#f8fbff; border:1px solid #dbe4f0; border-radius:16px;">
                                            <tr>
                                                <td style="padding:24px;">
                                                    <p class="text-faint"
                                                        style="margin:0 0 8px 0; font-family:Arial, sans-serif; font-size:12px; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; color:#78c2e6;">
                                                        Sender
                                                    </p>
                                                    <p class="text-main"
                                                        style="margin:0 0 8px 0; font-family:Arial, sans-serif; font-size:22px; font-weight:700; line-height:1.4; color:#0f172a;">
                                                        ${esc(sender_name)}
                                                    </p>
                                                    <p class="text-muted"
                                                        style="margin:0; font-family:Arial, sans-serif; font-size:16px; line-height:1.7; color:#475569;">
                                                        <a href="mailto:${esc(sender_email)}"
                                                            style="color:#78c2e6; text-decoration:none;">${
    esc(sender_email)
  }</a>
                                                    </p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding-bottom:14px;">
                                        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%"
                                            style="background-color:#f8fbff; border:1px solid #dbe4f0; border-radius:16px;">
                                            <tr>
                                                <td style="padding:24px;">
                                                    <p class="text-faint"
                                                        style="margin:0 0 8px 0; font-family:Arial, sans-serif; font-size:12px; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; color:#78c2e6;">
                                                        Received At
                                                    </p>
                                                    <p class="text-muted"
                                                        style="margin:0; font-family:Arial, sans-serif; font-size:16px; line-height:1.8; color:#475569;">
                                                        ${esc(received_at)}
                                                    </p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding-bottom:14px;">
                                        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%"
                                            style="background-color:#f8fbff; border:1px solid #dbe4f0; border-radius:16px;">
                                            <tr>
                                                <td style="padding:24px;">
                                                    <p class="text-faint"
                                                        style="margin:0 0 8px 0; font-family:Arial, sans-serif; font-size:12px; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; color:#78c2e6;">
                                                        Message ID
                                                    </p>
                                                    <p class="text-muted"
                                                        style="margin:0; font-family:Arial, sans-serif; font-size:16px; line-height:1.8; color:#475569;">
                                                        ${esc(message_id)}
                                                    </p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                <tr>
                                    <td>
                                        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%"
                                            style="background-color:#f8fbff; border:1px solid #dbe4f0; border-radius:16px;">
                                            <tr>
                                                <td style="padding:24px;">
                                                    <p class="text-faint"
                                                        style="margin:0 0 12px 0; font-family:Arial, sans-serif; font-size:12px; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; color:#78c2e6;">
                                                        Message
                                                    </p>
                                                    <p class="text-muted"
                                                        style="margin:0; font-family:Arial, sans-serif; font-size:16px; line-height:1.8; color:#475569;">
                                                        ${br(message)}
                                                    </p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>

</html>
`;
}

export function senderHtml(
  { portfolio_owner, gallery_url, instagram_url, facebook_url, astrobin_url, copyright_year }:
    SenderCtx,
): string {
  return `<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml"
    xmlns:o="urn:schemas-microsoft-com:office:office">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="color-scheme" content="light dark" />
    <meta name="supported-color-schemes" content="light dark" />
    <title>Message Received - Astrophotography Portfolio</title>

    <!--[if gte mso 9]>
    <xml>
        <o:OfficeDocumentSettings>
            <o:AllowPNG/>
            <o:PixelsPerInch>96</o:PixelsPerInch>
        </o:OfficeDocumentSettings>
    </xml>
    <![endif]-->

    <!--[if mso]>
    <style type="text/css">
        table, td { mso-table-lspace: 0pt !important; mso-table-rspace: 0pt !important; }
    </style>
    <![endif]-->

    <style>
        body, table, td, a {
            -webkit-text-size-adjust: 100%;
            -ms-text-size-adjust: 100%;
        }

        table {
            border-collapse: collapse !important;
        }

        img {
            -ms-interpolation-mode: bicubic;
            border: 0;
            height: auto;
            line-height: 100%;
            outline: none;
            text-decoration: none;
        }

        :root {
            color-scheme: light dark;
        }

        @media screen and (max-width: 600px) {
            body, .body, table, td {
                max-width: 100% !important;
                overflow-x: hidden !important;
            }

            .container {
                width: 100% !important;
                max-width: 100% !important;
            }

            .mobile-padding {
                padding-left: 18px !important;
                padding-right: 18px !important;
            }

            .stack {
                display: block !important;
                width: 100% !important;
            }
        }

        u+.body .wrapper {
            background-color: transparent !important;
        }

        u+.body .container-bg,
        u+.body .panel-bg,
        u+.body .footer-bg {
            background-color: #ffffff !important;
        }

        u+.body .text-main {
            color: #0f172a !important;
        }

        u+.body .text-muted {
            color: #475569 !important;
        }

        u+.body .text-faint {
            color: #64748b !important;
        }

        u+.body .text-accent {
            color: #78c2e6 !important;
        }

        [data-ogsc] .wrapper {
            background-color: transparent !important;
        }

        [data-ogsc] .container-bg,
        [data-ogsc] .panel-bg,
        [data-ogsc] .footer-bg {
            background-color: #0e1319 !important;
        }

        [data-ogsc] .text-main {
            color: #f8fafc !important;
        }

        [data-ogsc] .text-muted {
            color: #cbd5e1 !important;
        }

        [data-ogsc] .text-faint {
            color: #94a3b8 !important;
        }

        [data-ogsc] .text-accent {
            color: #78c2e6 !important;
        }

        [data-ogsc] .divider {
            border-top-color: #263445 !important;
        }

        [data-ogsc] .border-strong {
            border-color: #263445 !important;
        }

        @media (prefers-color-scheme: dark) {
            body, .body, .wrapper {
                background-color: transparent !important;
                color: #f8fafc !important;
            }

            .container-bg,
            .panel-bg,
            .footer-bg {
                background-color: #0e1319 !important;
            }

            .text-main {
                color: #f8fafc !important;
            }

            .text-muted {
                color: #cbd5e1 !important;
            }

            .text-faint {
                color: #94a3b8 !important;
            }

            .text-accent {
                color: #78c2e6 !important;
            }

            .divider {
                border-top-color: #263445 !important;
            }

            .border-strong {
                border-color: #263445 !important;
            }
        }
    </style>
</head>

<body class="body" style="margin:0; padding:0; background-color:transparent; color:#0f172a;">
    <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" class="wrapper"
        style="background-color:transparent;">
        <tr>
            <td align="center" style="padding:40px 16px;">
                <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="600"
                    class="container container-bg border-strong"
                    style="width:600px; max-width:600px; background-color:#ffffff; border:1px solid #dbe4f0; border-radius:18px; overflow:hidden;">

                    <tr>
                        <td align="center" class="panel-bg"
                            style="padding:32px 24px 22px 24px; background-color:#ffffff;">
                            <p class="text-faint"
                                style="margin:0 0 10px 0; font-family:Arial, sans-serif; font-size:11px; letter-spacing:2px; text-transform:uppercase; color:#64748b;">
                                Astrophotography Portfolio
                            </p>
                            <h1 class="text-main"
                                style="margin:0; font-family:'Times New Roman', Times, serif; font-size:34px; line-height:1.15; font-weight:400; color:#0f172a;">
                                Message Received
                            </h1>
                            <p class="text-accent"
                                style="margin:14px 0 0 0; font-family:Arial, sans-serif; font-size:13px; font-weight:700; letter-spacing:2px; text-transform:uppercase; color:#78c2e6;">
                                Hello 👋, it's ${esc(portfolio_owner)}
                            </p>
                        </td>
                    </tr>

                    <tr>
                        <td align="center" class="panel-bg mobile-padding"
                            style="padding:0 32px 28px 32px; background-color:#ffffff;">
                            <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%"
                                style="background-color:#f8fbff; border:1px solid #dbe4f0; border-radius:16px;">
                                <tr>
                                    <td align="center" style="padding:28px 24px;">
                                        <div style="font-size:38px; line-height:1; margin-bottom:16px;">✨</div>
                                        <p class="text-main"
                                            style="margin:0 0 12px 0; font-family:Arial, sans-serif; font-size:24px; font-weight:700; color:#0f172a;">
                                            Thank you for reaching out
                                        </p>
                                        <p class="text-muted"
                                            style="margin:0; font-family:Arial, sans-serif; font-size:17px; line-height:1.6; color:#475569;">
                                            I’ve received your inquiry and I’ll get back to you as soon as possible.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <tr>
                        <td class="panel-bg mobile-padding"
                            style="padding:0 32px 26px 32px; background-color:#ffffff;">
                            <p class="text-main"
                                style="margin:0 0 14px 0; font-family:Arial, sans-serif; font-size:16px; line-height:1.7; color:#0f172a;">
                                Hello there,
                            </p>
                            <p class="text-muted"
                                style="margin:0 0 14px 0; font-family:Arial, sans-serif; font-size:16px; line-height:1.8; color:#475569;">
                                I appreciate your interest in my astrophotography. Whether you’re asking about prints,
                                equipment, collaboration, or simply sharing your love for the cosmos, every message is
                                genuinely appreciated.
                            </p>
                            <p class="text-muted"
                                style="margin:0; font-family:Arial, sans-serif; font-size:16px; line-height:1.8; color:#475569;">
                                I typically reply within 24–48 hours. In the meantime, you’re welcome to browse the
                                latest gallery and explore recent work.
                            </p>
                        </td>
                    </tr>

                    <tr>
                        <td align="center" class="panel-bg mobile-padding"
                            style="padding:0 32px 36px 32px; background-color:#ffffff;">
                            <table role="presentation" border="0" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="center" style="border-radius:999px; background-color:#183b6b;">
                                        <a href="${esc(gallery_url)}"
                                            style="display:inline-block; padding:14px 28px; font-family:Arial, sans-serif; font-size:13px; font-weight:700; letter-spacing:1.6px; text-transform:uppercase; color:#ffffff; text-decoration:none;">
                                            Browse the Gallery
                                        </a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <tr>
                        <td align="center" class="footer-bg divider"
                            style="padding:26px 24px 30px 24px; background-color:#ffffff; border-top:1px solid #dbe4f0;">
                            <table role="presentation" border="0" cellpadding="0" cellspacing="0">
                                <tr>
                                    ${
    instagram_url
      ? `
                                    <td style="padding:0 10px;">
                                        <a href="${esc(instagram_url)}"
                                            style="font-family:Arial, sans-serif; font-size:12px; font-weight:700; letter-spacing:1.4px; text-transform:uppercase; color:#78c2e6; text-decoration:none;">
                                            Instagram
                                        </a>
                                    </td>
                                    `
      : ""
  }
                                    ${
    (instagram_url && facebook_url)
      ? `
                                    <td class="text-faint"
                                        style="padding:0 8px; font-family:Arial, sans-serif; font-size:12px; color:#94a3b8;">
                                        •
                                    </td>
                                    `
      : ""
  }
                                    ${
    facebook_url
      ? `
                                    <td style="padding:0 10px;">
                                        <a href="${esc(facebook_url)}"
                                            style="font-family:Arial, sans-serif; font-size:12px; font-weight:700; letter-spacing:1.4px; text-transform:uppercase; color:#78c2e6; text-decoration:none;">
                                            Facebook
                                        </a>
                                    </td>
                                    `
      : ""
  }
                                    ${
    (astrobin_url && facebook_url || astrobin_url && instagram_url)
      ? `
                                    <td class="text-faint"
                                        style="padding:0 8px; font-family:Arial, sans-serif; font-size:12px; color:#94a3b8;">
                                        •
                                    </td>
                                    `
      : ""
  }
                                    ${
    astrobin_url
      ? `
                                    <td style="padding:0 10px;">
                                        <a href="${esc(astrobin_url)}"
                                            style="font-family:Arial, sans-serif; font-size:12px; font-weight:700; letter-spacing:1.4px; text-transform:uppercase; color:#78c2e6; text-decoration:none;">
                                            Astrobin
                                        </a>
                                    </td>
                                    `
      : ""
  }
                                </tr>
                            </table>

                            <p class="text-faint"
                                style="margin:18px 0 0 0; font-family:Arial, sans-serif; font-size:11px; letter-spacing:1.2px; text-transform:uppercase; color:#94a3b8;">
                                © ${esc(copyright_year)} ${esc(portfolio_owner)} | Astrophotography
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>

</html>
`;
}
