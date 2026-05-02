"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Checkbox } from "@/components/ui/checkbox";
import { Eye, EyeOff } from "lucide-react";
import { JazzyLogo } from "@/components/jazzy-logo";

export default function RegisterPage() {
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [consent, setConsent] = useState(false);
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);
    const router = useRouter();

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");

        if (!consent) {
            setError("You must accept the privacy policy to create an account.");
            return;
        }

        setLoading(true);

        const supabase = createClient();
        const { data, error } = await supabase.auth.signUp({
            email,
            password,
            options: { data: { name } },
        });

        if (error) {
            setError(error.message);
            setLoading(false);
            return;
        }

        if (data.user) {
            if (data.user.identities?.length === 0) {
                setError("An account with this email already exists.");
                setLoading(false);
                return;
            }

            if (data.session) {
                router.push("/history");
                router.refresh();
            } else {
                setSuccess(true);
                setLoading(false);
            }
        }
    };

    if (success) {
        return (
            <div className="flex flex-col min-h-screen">
                <div className="flex justify-center px-6 py-8">
                    <Link href="/" className="hover:opacity-80 transition-opacity">
                        <JazzyLogo fill="#18181b" height={40} />
                    </Link>
                </div>
                <div className="flex items-center justify-center flex-1">
                    <div className="w-full max-w-md p-8 space-y-8 bg-card rounded-lg shadow-md">
                        <div className="text-center">
                            <h1 className="text-3xl font-bold">Check your email</h1>
                        <p className="mt-2 text-sm text-muted-foreground">
                            We&apos;ve sent a confirmation link to <strong>{email}</strong>. Please check your inbox to verify your account.
                            </p>
                        </div>
                        <p className="text-center text-sm text-muted-foreground">
                            <Link href="/login" className="text-blue-600 hover:underline">Back to Login</Link>
                        </p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="flex flex-col min-h-screen">
            <div className="flex justify-center px-6 py-8">
                <Link href="/" className="hover:opacity-80 transition-opacity">
                    <JazzyLogo fill="#18181b" height={40} />
                </Link>
            </div>
            <div className="flex items-center justify-center flex-1">
                <div className="w-full max-w-md p-8 space-y-8 bg-card rounded-lg shadow-md">
                    <div className="text-center">
                        <h1 className="text-3xl font-bold">Register</h1>
                    <p className="mt-2 text-sm text-muted-foreground">Create your account</p>
                </div>
                <form onSubmit={handleRegister} className="space-y-6">
                    {error && (
                        <p className="text-sm text-red-600 text-center">{error}</p>
                    )}
                    <div className="space-y-2">
                        <Label htmlFor="name">Name</Label>
                        <Input id="name" name="name" type="text" placeholder="John Doe" autoComplete="name" required value={name} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setName(e.target.value)} />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="email">Email</Label>
                        <Input id="email" name="email" type="email" placeholder="you@example.com" autoComplete="email" required value={email} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)} />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="password">Password</Label>
                        <div className="relative">
                            <Input id="password" name="password" type={showPassword ? "text" : "password"} autoComplete="new-password" required value={password} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)} className="pr-10" />
                            <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-muted-foreground">
                                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                            </button>
                        </div>
                    </div>
                    <div className="flex items-start space-x-2">
                        <Checkbox
                            id="consent"
                            checked={consent}
                            onCheckedChange={(checked) => setConsent(checked === true)}
                            className="mt-0.5"
                        />
                        <label htmlFor="consent" className="text-sm font-normal text-muted-foreground leading-snug">
                            I agree to the{" "}<Link href="/privacy" className="text-blue-600 hover:underline" target="_blank">Privacy Policy</Link>{" "}and consent to receiving jazz album recommendations via email.
                        </label>
                    </div>
                        <Button type="submit" className="w-full" disabled={loading || !consent}>
                            {loading ? "Creating account..." : "Register"}
                        </Button>
                    </form>
                    <p className="text-center text-sm text-muted-foreground">
                        Already have an account? <Link href="/login" className="text-blue-600 hover:underline">Login</Link>
                    </p>
                </div>
            </div>
        </div>
    );
}
