import Link from "next/link";

export default function ImprintPage() {
    return (
        <div className="flex justify-center min-h-screen py-12 px-4">
            <div className="w-full max-w-2xl bg-white rounded-lg shadow-md p-8 space-y-8">
                <div>
                    <h1 className="text-3xl font-bold">Imprint</h1>
                </div>

                <section className="space-y-3">
                    <h2 className="text-xl font-semibold">Responsible for Content</h2>
                    <div className="text-sm text-gray-700 leading-relaxed space-y-1">
                        <p>[Your Name]</p>
                        <p>[Your Street Address]</p>
                        <p>[Your ZIP Code and City]</p>
                        <p>[Your Country]</p>
                    </div>
                </section>

                <section className="space-y-3">
                    <h2 className="text-xl font-semibold">Contact</h2>
                    <div className="text-sm text-gray-700 leading-relaxed space-y-1">
                        <p>Email: <a href="mailto:[your-email@example.com]" className="text-blue-600 hover:underline">[your-email@example.com]</a></p>
                    </div>
                </section>

                <section className="space-y-3">
                    <h2 className="text-xl font-semibold">Disclaimer</h2>
                    <p className="text-sm text-gray-700 leading-relaxed">
                        The content of this website has been prepared with the utmost care. However, we cannot
                        guarantee the accuracy, completeness, or timeliness of the content. As a service provider,
                        we are responsible for our own content on these pages under general law. However, we are
                        not obligated to monitor transmitted or stored third-party information or to investigate
                        circumstances that indicate illegal activity.
                    </p>
                </section>

                <section className="space-y-3">
                    <h2 className="text-xl font-semibold">Copyright</h2>
                    <p className="text-sm text-gray-700 leading-relaxed">
                        The source code of Jazzy is licensed under the GNU General Public License v3 (GPLv3).
                        Album cover art, artist names, and album metadata remain the property of their respective rights holders.
                    </p>
                </section>

                <div className="border-t pt-6 flex justify-center gap-4 text-sm">
                    <Link href="/privacy" className="text-blue-600 hover:underline">Privacy Policy</Link>
                    <span className="text-gray-300">|</span>
                    <Link href="/" className="text-blue-600 hover:underline">Back to Home</Link>
                </div>
            </div>
        </div>
    );
}
