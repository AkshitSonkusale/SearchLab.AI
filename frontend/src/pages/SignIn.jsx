import { useState } from "react";
import { Link } from "react-router-dom";
import AuthShell, { Field, FormError } from "../components/AuthShell";

// onSignIn({ email, password }) should call the backend auth endpoint.
export default function SignIn({ onSignIn, error }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  return (
    <AuthShell>
      <form onSubmit={(e) => { e.preventDefault(); onSignIn?.({ email, password }); }} className="flex flex-col gap-5">
        <h2 className="m-0 font-serif text-[32px] font-medium">Sign in</h2>
        <FormError>{error}</FormError>
        <Field label="Email" type="email" required autoComplete="email" placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} />
        <Field label="Password" type="password" required autoComplete="current-password" placeholder="Your password" value={password} onChange={(e) => setPassword(e.target.value)} />
        <button type="submit" className="btn">Sign in</button>
        <p className="m-0 text-[15px] text-graphite">No account yet? <Link to="/register">Create one</Link></p>
      </form>
    </AuthShell>
  );
}
