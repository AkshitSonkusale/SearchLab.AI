import { useRef, useState } from "react";
import { PageHeader } from "../components/AppLayout";
import { UploadIcon } from "../components/Icons";
import { documents as initial } from "../data/sample";

const ACCEPT = [".pdf", ".docx", ".txt"];
const MAX = 10 * 1024 * 1024;
const fmt = (b) => (b > 1024 * 1024 ? `${(b / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(b / 1024))} KB`);

function Status({ d }) {
  const dot = (c) => <span aria-hidden="true" className="mr-2 inline-block h-2 w-2 rounded-full" style={{ background: c }} />;
  if (d.status === "ready") return <span>{dot("#1D5B47")}Ready</span>;
  if (d.status === "processing") return <span>{dot("#B7791F")}{d.progress || "Processing"}</span>;
  return <span>{dot("#A33A2F")}<span className="text-[#8A2E25]">{d.error}</span></span>;
}

// Replace the local state with: GET /documents, POST /documents (multipart), DELETE /documents/:id
export default function Documents() {
  const [docs, setDocs] = useState(initial);
  const [drag, setDrag] = useState(false);
  const [notice, setNotice] = useState("");
  const input = useRef(null);

  const add = (files) => {
    const rejected = [];
    const added = [...files].filter((f) => {
      const ok = ACCEPT.some((ext) => f.name.toLowerCase().endsWith(ext)) && f.size <= MAX;
      if (!ok) rejected.push(f.name);
      return ok;
    }).map((f, i) => ({
      id: Date.now() + i, name: f.name, type: f.name.split(".").pop().toUpperCase(), size: fmt(f.size),
      added: "Just now", passages: null, status: "processing", progress: "Reading file",
    }));
    setDocs((d) => [...added, ...d]);
    setNotice(rejected.length ? `Not added: ${rejected.join(", ")}. Use PDF, DOCX or TXT files up to 10 MB.` : "");
  };

  return (
    <>
      <PageHeader title="Documents" lead="Everything SearchLab.AI can search. Deleting a file removes it from answers too." />

      <section
        onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); add(e.dataTransfer.files); }}
        className={`flex flex-wrap items-center gap-5 rounded-md border-[1.5px] border-dashed bg-white p-8 transition-colors hover:border-brand hover:bg-[#F6FAF7] ${drag ? "border-brand bg-[#F6FAF7]" : "border-[#9FB0A6]"}`}
      >
        <span className="flex h-12 w-12 items-center justify-center rounded-md bg-paper text-brand"><UploadIcon size={22} /></span>
        <div className="flex flex-[1_1_260px] flex-col gap-1">
          <p className="m-0 font-serif text-[21px] font-medium">Drop files here to add them to your search</p>
          <p className="m-0 text-sm text-graphite">PDF, DOCX or TXT, up to 10 MB each</p>
        </div>
        <input ref={input} type="file" multiple accept={ACCEPT.join(",")} className="sr-only-x" onChange={(e) => { add(e.target.files); e.target.value = ""; }} />
        <button type="button" className="btn" onClick={() => input.current?.click()}>Choose files</button>
      </section>
      {notice && <p role="alert" className="m-0 text-sm text-[#8A2E25]">{notice}</p>}

      <section className="sheet overflow-x-auto">
        <table className="w-full min-w-[820px] border-collapse text-[15px]">
          <caption className="caption">{docs.length} documents</caption>
          <thead>
            <tr>
              {["Name", "Type", "Size", "Added", "Passages", "Status"].map((h) => <th key={h} scope="col" className="th">{h}</th>)}
              <th scope="col" className="th text-right"><span className="sr-only-x">Actions</span></th>
            </tr>
          </thead>
          <tbody>
            {docs.map((d) => (
              <tr key={d.id}>
                <td className="td font-medium">{d.name}</td>
                <td className="td text-graphite">{d.type}</td>
                <td className="td text-graphite">{d.size}</td>
                <td className="td text-graphite">{d.added}</td>
                <td className="td text-graphite">{d.passages ?? (d.status === "failed" ? "None" : "Pending")}</td>
                <td className="td max-w-[260px]"><Status d={d} /></td>
                <td className="td text-right">
                  <button type="button" aria-label={`Delete ${d.name}`} className="btn2 btn-sm"
                    onClick={() => setDocs((all) => all.filter((x) => x.id !== d.id))}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
