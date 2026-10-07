export default function PrivacyPage() {
  return (
    <main className="min-h-screen bg-[#080B12] text-gray-300 px-6 py-12">
      <div className="max-w-2xl mx-auto space-y-6">
        <h1 className="text-3xl font-bold text-white">Privacy Policy</h1>
        <p className="text-sm text-gray-500">Last updated: September 2026</p>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">1. What we collect</h2>
          <p>EngageSphere collects your business email, business name, and — when you connect a platform — the access tokens required to read and respond to customer feedback on your behalf. We do not collect or store passwords.</p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">2. How we use your data</h2>
          <p>Your data is used solely to provide the EngageSphere service: fetching feedback from connected platforms, analysing sentiment, and generating AI-suggested replies. We do not sell or share your data with third parties.</p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">3. Facebook &amp; Instagram data</h2>
          <p>When you connect Facebook or Instagram, we access your Page comments and post data using permissions you explicitly grant via Meta&apos;s OAuth flow. We store only the access token and the comment/reply content needed to operate the service. We comply with the <a href="https://developers.facebook.com/policy/" className="text-indigo-400 underline">Meta Platform Policy</a>.</p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">4. Data retention</h2>
          <p>Your data is retained for as long as your account is active. You may request deletion at any time — see our <a href="/data-deletion" className="text-indigo-400 underline">Data Deletion</a> page.</p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">5. Security</h2>
          <p>All data is stored in a secured Supabase database with TLS encryption in transit and at rest. Access tokens are never exposed in URLs or logs.</p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">6. Contact</h2>
          <p>For any privacy concerns, email us at <a href="mailto:manzar0505@gmail.com" className="text-indigo-400 underline">manzar0505@gmail.com</a>.</p>
        </section>
      </div>
    </main>
  );
}
