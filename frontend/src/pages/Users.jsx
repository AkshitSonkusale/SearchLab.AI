import { useState, useEffect } from "react";
import { PageHeader } from "../components/AppLayout";
import { api } from "../api";

export default function Users() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState("");
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteName, setInviteName] = useState("");
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("user");
  const [tempPassNotice, setTempPassNotice] = useState("");

  const loadUsers = async () => {
    try {
      const data = await api.getUsers();
      setUsers(data || []);
    } catch (err) {
      setNotice(err.message || "Failed to load users (Admin privileges required).");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const update = async (id, patch) => {
    try {
      await api.updateUser(id, patch);
      setUsers((all) => all.map((u) => (u.id === id ? { ...u, ...patch } : u)));
    } catch (err) {
      setNotice(err.message || "Failed to update user.");
    }
  };

  const handleInvite = async (e) => {
    e.preventDefault();
    try {
      const res = await api.inviteUser(inviteName, inviteEmail, inviteRole);
      setTempPassNotice(`User invited successfully! Temporary password: ${res.temporary_password}`);
      setInviteName("");
      setInviteEmail("");
      setShowInviteModal(false);
      loadUsers();
    } catch (err) {
      setNotice(err.message || "Failed to invite user.");
    }
  };

  return (
    <>
      <PageHeader title="People and roles" lead="Choose who can use SearchLab.AI and what they can do.">
        <button type="button" className="btn" onClick={() => setShowInviteModal(true)}>Invite someone</button>
      </PageHeader>

      {tempPassNotice && (
        <div className="sheet max-w-[820px] p-4 bg-[#F6FAF7] border-brand text-brand rounded font-mono text-sm">
          {tempPassNotice}
        </div>
      )}
      {notice && (
        <div className="sheet max-w-[820px] p-4 bg-[#FDF2F1] text-[#8A2E25] rounded text-sm">
          {notice}
        </div>
      )}

      {showInviteModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
          <form onSubmit={handleInvite} className="sheet flex flex-col gap-4 p-6 max-w-md w-full bg-white">
            <h3 className="m-0 font-serif text-2xl">Invite User</h3>
            <input required placeholder="Name" value={inviteName} onChange={(e) => setInviteName(e.target.value)} className="inp" />
            <input required type="email" placeholder="Email" value={inviteEmail} onChange={(e) => setInviteEmail(e.target.value)} className="inp" />
            <select value={inviteRole} onChange={(e) => setInviteRole(e.target.value)} className="inp">
              <option value="user">User</option>
              <option value="admin">Admin</option>
            </select>
            <div className="flex justify-end gap-2 mt-2">
              <button type="button" onClick={() => setShowInviteModal(false)} className="btn2">Cancel</button>
              <button type="submit" className="btn">Send Invite</button>
            </div>
          </form>
        </div>
      )}

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
                    <option value="admin">Admin</option>
                    <option value="user">User</option>
                  </select>
                </td>
                <td className={`td font-medium ${u.active ? "text-brand" : "text-graphite"}`}>{u.active ? "Active" : "Deactivated"}</td>
                <td className="td text-graphite">{u.last_active_at ? new Date(u.last_active_at).toLocaleDateString() : "Never"}</td>
                <td className="td text-right">
                  <button type="button" className="btn2 btn-sm" onClick={() => update(u.id, { active: !u.active })}>
                    {u.active ? "Deactivate" : "Reactivate"}
                  </button>
                </td>
              </tr>
            ))}
            {!loading && users.length === 0 && (
              <tr>
                <td colSpan={6} className="td text-center text-graphite py-6">No users found or insufficient permissions.</td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
      <p className="m-0 max-w-[70ch] text-sm text-graphite">
        Admins can manage people and see evaluation results. Users can upload documents and ask questions about their own files.
      </p>
    </>
  );
}
