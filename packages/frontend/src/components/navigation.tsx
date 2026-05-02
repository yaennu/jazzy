"use client";

import Link from "next/link";
import Image from "next/image";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { JazzyLogo } from "@/components/jazzy-logo";
import type { User } from "@supabase/supabase-js";
import { useRouter } from "next/navigation";

const HIDDEN_ROUTES = ["/login", "/register", "/forgot-password", "/reset-password", "/"];

export default function Navigation() {
    const [user, setUser] = useState<User | null>(null);
    const pathname = usePathname();
    const supabase = createClient();
    const router = useRouter();

    useEffect(() => {
        supabase.auth.getUser().then(({ data: { user } }) => {
            setUser(user);
        });

        const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
            setUser(session?.user ?? null);
        });

        return () => subscription.unsubscribe();
    }, [supabase]);

    if (HIDDEN_ROUTES.includes(pathname)) {
        return null;
    }

    const handleLogout = async () => {
        await supabase.auth.signOut();
        router.push("/login");
        router.refresh();
    };

    return (
        <nav className="flex items-center justify-between px-6 py-3 border-b border-gray-100">
            <Link href="/" className="flex items-center">
                <Image
                    src="/apple-icon.png"
                    alt="Jazzy"
                    width={32}
                    height={32}
                    className="block sm:hidden rounded-lg"
                />
                <JazzyLogo
                    fill="#18181b"
                    height={24}
                    className="hidden sm:block"
                />
            </Link>
            <div className="flex items-center gap-2">
                {user ? (
                    <>
                        <Button variant="ghost" size="sm" asChild>
                            <Link href="/history">History</Link>
                        </Button>
                        <Button variant="ghost" size="sm" asChild>
                            <Link href="/settings">Settings</Link>
                        </Button>
                        <Button variant="ghost" size="sm" onClick={handleLogout}>
                            Logout
                        </Button>
                    </>
                ) : (
                    <>
                        <Button variant="ghost" size="sm" asChild>
                            <Link href="/login">Login</Link>
                        </Button>
                        <Button size="sm" asChild>
                            <Link href="/register">Register</Link>
                        </Button>
                    </>
                )}
            </div>
        </nav>
    );
}
