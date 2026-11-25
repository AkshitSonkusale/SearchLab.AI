import { useState } from "react";
import { PageHeader } from "../components/AppLayout";
import { users as initial } from "../data/sample";

// Replace with: GET /users, PATCH /users/:id { role, active }, POST /users/invite
export default function Users() {
  const [users, setUsers] = useState(initial);
  const update = (id, patch) => setUsers((all) => all.map((u) => (u.id === id ? { ...u, ...patch } : u)));

  return (
    <>
      <PageHeader title="People and roles" lead="Choose who can use SearchLab.AI and what they can do.">
        <button type="button" className="btn">Invite someone</button>
      </PageHeader>

      <section className="sheet overflow-x-auto">
        <table className="w-full min-w-[820px] border-collapse text-[15px]">
          <caption className="caption">{users.length} people</caption>
          <thead>
            <tr>
              {["Name", "Email", "Role", "Status", "Last active"].map((h) => <th key={h} scope="col" className="th">{h}</th>)}
              <th scope="col" className="th text-right"><span className="sr-only-x">Actions</span></th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td className="td font-medium">{u.name}</td>
                <td className="td text-graphite">{u.email}</td>
                <td className="td">
                  <label htmlFor={`role${u.id}`} className="sr-only-x">Role for {u.name}</label>
                  <select id={`role${u.id}`} value={u.role} onChange={(e) => update(u.id, { role: e.target.value })} className="inp min-h-[36px] text-sm">
                    <option>Admin</option><option>User</option>
                  </select>
                </td>
                <td className={`td font-medium ${u.active ? "text-brand" : "text-graphite"}`}>{u.active ? "Active" : "Deactivated"}</td>
                <td className="td text-graphite">{u.last}</td>
                <td className="td text-right">
                  <button type="button" className="btn2 btn-sm" onClick={() => update(u.id, { active: !u.active })}>
                    {u.active ? "Deactivate" : "Reactivate"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <p className="m-0 max-w-[70ch] text-sm text-graphite">
        Admins can manage people and see evaluation results. Users can upload documents and ask questions about their own files.
      </p>
    </>
  );
}
