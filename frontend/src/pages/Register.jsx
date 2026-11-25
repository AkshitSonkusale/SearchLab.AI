import { useState } from "react";
import { Link } from "react-router-dom";
import AuthShell, { Field, FormError } from "../components/AuthShell";

// onRegister({ name, email, password }) should call the backend sign-up endpoint.
export default function Register({ onRegister, error }) {
  const [form, setForm] = useState({ name: "", email: "", password: "", confirm: "" });
  const [localError, setLocalError] = useState("");
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = (e) => {
    e.preventDefault();
    if (form.password.length < 8) return setLocalError("Password needs at least 8 characters.");
    if (form.password !== form.confirm) return setLocalError("Passwords don’t match. Type the same password in both fields.");
    setLocalError("");
    onRegister?.({ name: form.name, email: form.email, password: form.password });
  };

  return (
    <AuthShell>
      <form onSubmit={submit} className="flex flex-col gap-[18px]">
        <div className="flex flex-col gap-1.5">
          <h2 className="m-0 font-serif text-[32px] font-medium">Create your account</h2>
          <p className="m-0 text-[15px] text-graphite">Your documents stay private to your account.</p>
        </div>
        <FormError>{localError || error}</FormError>
        <Field label="Full name" required autoComplete="name" placeholder="Your name" value={form.name} onChange={set("name")} />
        <Field label="Email" type="email" required autoComplete="email" placeholder="you@example.com" value={form.email} onChange={set("email")} />
        <Field label="Password" type="password" required autoComplete="new-password" placeholder="At least 8 characters" value={form.password} onChange={set("password")} />
        <Field label="Confirm password" type="password" required autoComplete="new-password" placeholder="Type it again" value={form.confirm} onChange={set("confirm")} />
        <button type="submit" className="btn">Create account</button>
        <p className="m-0 text-[15px] text-graphite">Already have an account? <Link to="/">Sign in</Link></p>
      </form>
    </AuthShell>
  );
}
