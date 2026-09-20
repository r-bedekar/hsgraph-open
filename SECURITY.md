# Security and sensitive concerns

The reader works locally without network access or credentials. Verify the ZIP
checksum against the release manifest obtained through the approved distribution
route, then verify the extracted package. Do not load untrusted SQLite files or
assume a checksum independently authenticates a publisher. Public indexes are
disposable; rebuild from verified package bytes and use `verify-store` if changed.

Do not disclose exploitable details, credentials or personal data in public
issues. Send sensitive security or rights concerns to
[rbedekar@zeroinsec.com](mailto:rbedekar@zeroinsec.com), the owner's selected
project contact. Do not email credentials or an entire confidential backup;
describe the issue and agree a safe evidence-sharing method first.
Use the eventual repository's issue templates only for nonsensitive rights/data
concerns. No response-time or encrypted-email guarantee is made.
