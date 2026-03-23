import Link from "next/link";

export default function PrivacyPage() {
    return (
        <div className="flex justify-center min-h-screen py-12 px-4">
            <div className="w-full max-w-2xl bg-white rounded-lg shadow-md p-8 space-y-8">
                <div>
                    <h1 className="text-3xl font-bold">Privacy Policy</h1>
                    <p className="mt-2 text-sm text-gray-500">Last updated: March 17, 2026</p>
                </div>

                <section className="space-y-3">
                    <h2 className="text-xl font-semibold">1. Overview</h2>
                    <p className="text-sm text-gray-700 leading-relaxed">
                        Jazzy (&quot;we&quot;, &quot;us&quot;) is a service that sends periodic jazz album recommendations via email.
                        We take the protection of your personal data seriously and process it in accordance with the
                        EU General Data Protection Regulation (GDPR) and the Swiss Federal Act on Data Protection (FADP/DSG).
                    </p>
                </section>

                <section className="space-y-3">
                    <h2 className="text-xl font-semibold">2. Data We Collect</h2>
                    <div className="text-sm text-gray-700 leading-relaxed space-y-2">
                        <p>When you create an account, we collect and store:</p>
                        <ul className="list-disc pl-6 space-y-1">
                            <li><strong>Email address</strong> &mdash; for authentication and sending recommendations</li>
                            <li><strong>Name</strong> &mdash; for personalizing emails</li>
                            <li><strong>Password</strong> &mdash; stored as a secure hash, never in plain text</li>
                            <li><strong>Newsletter frequency preference</strong> &mdash; your chosen delivery interval</li>
                            <li><strong>Recommendation history</strong> &mdash; which albums were sent to you, to avoid duplicates</li>
                        </ul>
                        <p>We also process:</p>
                        <ul className="list-disc pl-6 space-y-1">
                            <li><strong>Session cookies</strong> &mdash; strictly necessary for authentication (no tracking)</li>
                            <li><strong>IP address</strong> &mdash; processed by our hosting provider for delivering the website</li>
                        </ul>
                    </div>
                </section>

                <section className="space-y-3">
                    <h2 className="text-xl font-semibold">3. Purpose and Legal Basis</h2>
                    <div className="text-sm text-gray-700 leading-relaxed space-y-2">
                        <ul className="list-disc pl-6 space-y-1">
                            <li><strong>Contract performance (Art. 6(1)(b) GDPR)</strong> &mdash; processing your data to provide the recommendation service you signed up for</li>
                            <li><strong>Consent (Art. 6(1)(a) GDPR)</strong> &mdash; sending recommendation emails based on your explicit consent at registration</li>
                            <li><strong>Legitimate interest (Art. 6(1)(f) GDPR)</strong> &mdash; session cookies necessary for website functionality</li>
                        </ul>
                    </div>
                </section>

                <section className="space-y-3">
                    <h2 className="text-xl font-semibold">4. Third-Party Services</h2>
                    <div className="text-sm text-gray-700 leading-relaxed space-y-2">
                        <p>We use the following third-party services to operate Jazzy:</p>
                        <ul className="list-disc pl-6 space-y-2">
                            <li>
                                <strong>Supabase</strong> (database &amp; authentication) &mdash; stores your account data and recommendation history.
                                Servers located in the EU/US. <a href="https://supabase.com/privacy" className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">Supabase Privacy Policy</a>
                            </li>
                            <li>
                                <strong>Resend</strong> (email delivery) &mdash; receives your email address and name to deliver recommendation emails.
                                Servers located in the US. <a href="https://resend.com/legal/privacy-policy" className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">Resend Privacy Policy</a>
                            </li>
                            <li>
                                <strong>Vercel</strong> (website hosting) &mdash; processes your IP address and session cookies when you visit the website.
                                Servers located in the US. <a href="https://vercel.com/legal/privacy-policy" className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">Vercel Privacy Policy</a>
                            </li>
                        </ul>
                        <p>
                            For data transfers to the US, we rely on the EU-US Data Privacy Framework and/or Standard Contractual Clauses (SCCs)
                            as applicable.
                        </p>
                    </div>
                </section>

                <section className="space-y-3">
                    <h2 className="text-xl font-semibold">5. Data Retention</h2>
                    <p className="text-sm text-gray-700 leading-relaxed">
                        We retain your personal data for as long as your account is active. When you delete your account,
                        all your data (account information, preferences, and recommendation history) is permanently and
                        immediately deleted from our database. We do not retain backups of deleted accounts.
                    </p>
                </section>

                <section className="space-y-3">
                    <h2 className="text-xl font-semibold">6. Cookies</h2>
                    <p className="text-sm text-gray-700 leading-relaxed">
                        Jazzy only uses <strong>strictly necessary session cookies</strong> for authentication.
                        We do not use tracking cookies, analytics cookies, or advertising cookies.
                        These essential cookies do not require consent under the GDPR ePrivacy exemption.
                    </p>
                </section>

                <section className="space-y-3">
                    <h2 className="text-xl font-semibold">7. Your Rights</h2>
                    <div className="text-sm text-gray-700 leading-relaxed space-y-2">
                        <p>Under the GDPR and Swiss DSG, you have the following rights:</p>
                        <ul className="list-disc pl-6 space-y-1">
                            <li><strong>Right of access</strong> &mdash; request a copy of your personal data (available via &quot;Export My Data&quot; in <Link href="/settings" className="text-blue-600 hover:underline">Settings</Link>)</li>
                            <li><strong>Right to rectification</strong> &mdash; update your information in your account settings</li>
                            <li><strong>Right to erasure</strong> &mdash; delete your account and all data via &quot;Delete Account&quot; in <Link href="/settings" className="text-blue-600 hover:underline">Settings</Link></li>
                            <li><strong>Right to object</strong> &mdash; unsubscribe from emails using the link in any recommendation email, or change your frequency in <Link href="/settings" className="text-blue-600 hover:underline">Settings</Link></li>
                            <li><strong>Right to data portability</strong> &mdash; export your data in JSON format via <Link href="/settings" className="text-blue-600 hover:underline">Settings</Link></li>
                            <li><strong>Right to withdraw consent</strong> &mdash; you can unsubscribe or delete your account at any time</li>
                        </ul>
                        <p>
                            To exercise any of these rights, use the self-service options in your account settings
                            or contact us at the address below.
                        </p>
                    </div>
                </section>

                <section className="space-y-3">
                    <h2 className="text-xl font-semibold">8. Contact</h2>
                    <p className="text-sm text-gray-700 leading-relaxed">
                        If you have questions about this privacy policy or wish to exercise your rights,
                        please contact us via the details on our <Link href="/imprint" className="text-blue-600 hover:underline">Imprint</Link> page.
                    </p>
                </section>

                <section className="space-y-3">
                    <h2 className="text-xl font-semibold">9. Changes to This Policy</h2>
                    <p className="text-sm text-gray-700 leading-relaxed">
                        We may update this privacy policy from time to time. Changes will be posted on this page
                        with an updated revision date. We encourage you to review this page periodically.
                    </p>
                </section>

                <div className="border-t pt-6 text-center">
                    <Link href="/" className="text-sm text-blue-600 hover:underline">Back to Home</Link>
                </div>
            </div>
        </div>
    );
}
