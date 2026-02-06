import Link from "next/link";

export default function Navigation() {
    return (
        <nav>
            <Link href="/login">Login</Link>
            <Link href="/register">Register</Link>
            <Link href="/settings">Settings</Link>
        </nav>
    );
}
