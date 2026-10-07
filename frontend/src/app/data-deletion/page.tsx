export default function DataDeletionPage() {
  return (
    <main className="min-h-screen bg-[#080B12] text-gray-300 px-6 py-12">
      <div className="max-w-2xl mx-auto space-y-6">
        <h1 className="text-3xl font-bold text-white">Data Deletion Request</h1>
        <p className="text-sm text-gray-500">Last updated: September 2026</p>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">How to request deletion of your data</h2>
          <p>You can request that all your personal data stored by EngageSphere be permanently deleted using either of the methods below.</p>
        </section>

        <section className="space-y-4">
          <div className="rounded-xl border border-white/10 bg-white/[0.03] p-5 space-y-2">
            <h3 className="text-base font-semibold text-white">Option 1 — Email us</h3>
            <p>Send a deletion request to <a href="mailto:manzar0505@gmail.com" className="text-indigo-400 underline">manzar0505@gmail.com</a> with the subject line <span className="font-mono text-gray-200">"Data Deletion Request"</span> and include the email address associated with your EngageSphere account.</p>
          </div>

          <div className="rounded-xl border border-white/10 bg-white/[0.03] p-5 space-y-2">
            <h3 className="text-base font-semibold text-white">Option 2 — Remove app from Facebook</h3>
            <p>You can immediately revoke EngageSphere&apos;s access to your Facebook data directly from Facebook:</p>
            <ol className="list-decimal list-inside space-y-1 text-sm text-gray-400">
              <li>Go to <span className="text-gray-200">Facebook Settings</span></li>
              <li>Click <span className="text-gray-200">Security and Login</span> → <span className="text-gray-200">Business Integrations</span></li>
              <li>Find <span className="text-gray-200">EngageSphere</span> and click <span className="text-gray-200">Remove</span></li>
            </ol>
            <p className="text-sm text-gray-500">This immediately revokes our access token. To also delete stored data, follow up with an email as described in Option 1.</p>
          </div>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">What gets deleted</h2>
          <ul className="list-disc list-inside space-y-1 text-sm text-gray-400">
            <li>Your account and login credentials</li>
            <li>Your business profile and settings</li>
            <li>All stored Facebook and Instagram access tokens</li>
            <li>All feedback items, replies, and suggestions associated with your account</li>
          </ul>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">Timeline</h2>
          <p>All data will be permanently deleted within <span className="text-white font-semibold">30 days</span> of receiving your request. You will receive a confirmation email once deletion is complete.</p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">Contact</h2>
          <p>For any questions about data deletion, email <a href="mailto:manzar0505@gmail.com" className="text-indigo-400 underline">manzar0505@gmail.com</a>.</p>
        </section>
      </div>
    </main>
  );
}
