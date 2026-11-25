// Sample data for the demo. Replace with API calls to the FastAPI backend.

export const documents = [
  { id: 1, name: "Intern_Handbook_2026.pdf", type: "PDF", size: "2.4 MB", added: "23 Nov 2026", passages: 186, status: "ready" },
  { id: 2, name: "HR_Policy_v3.docx", type: "DOCX", size: "860 KB", added: "23 Nov 2026", passages: 142, status: "ready" },
  { id: 3, name: "Onboarding_Guide.txt", type: "TXT", size: "96 KB", added: "22 Nov 2026", passages: 84, status: "ready" },
  { id: 4, name: "Travel_Reimbursement.pdf", type: "PDF", size: "1.1 MB", added: "Just now", passages: null, status: "processing", progress: "Reading pages 14 of 31" },
  { id: 5, name: "Scanned_Notice.pdf", type: "PDF", size: "3.8 MB", added: "22 Nov 2026", passages: null, status: "failed", error: "No text found. Upload a text-based PDF, not a scan." },
];

export const suggestions = [
  "What is the leave policy for interns?",
  "Summarise the onboarding checklist",
  "Who approves expense claims?",
];

// Answer for the demo question, split into paragraphs of [text, citation] parts.
export const sampleAnswer = {
  question: "What is the leave policy for interns?",
  meta: "Answered from 3 passages in 2.8 seconds",
  paragraphs: [
    [
      ["Interns get 1.5 days of paid leave for every month of their internship, credited at the start of each month.", 1],
      [" Unused leave does not carry over once the internship ends.", 1],
    ],
    [
      ["To take leave, submit a request on the HR portal at least 3 working days ahead; your reporting manager approves it.", 2],
      [" Avoid planned leave during your first two weeks of onboarding unless it is an emergency.", 3],
    ],
  ],
  sources: [
    { n: 1, file: "Intern_Handbook_2026.pdf", loc: "Page 12", score: 0.89, before: "Interns are entitled to ", hl: "1.5 days of paid leave per month", after: " of internship, credited at the start of each month. Unused leave cannot be carried forward." },
    { n: 2, file: "HR_Policy_v3.docx", loc: "Section 4.2", score: 0.81, before: "All leave requests, including those from trainees and interns, ", hl: "must be submitted through the HR portal at least 3 working days in advance", after: "." },
    { n: 3, file: "Onboarding_Guide.txt", loc: "Lines 88 to 95", score: 0.74, before: "During the first two weeks of onboarding, ", hl: "new joiners should avoid planned leave", after: " except in emergencies." },
  ],
};

export const notFound = {
  threshold: 0.55,
  closest: [
    { n: 1, file: "Onboarding_Guide.txt", loc: "Lines 12 to 16", score: 0.41, before: "Lunch is provided on the first day of onboarding for all new joiners.", hl: "", after: "" },
    { n: 2, file: "HR_Policy_v3.docx", loc: "Section 7.1", score: 0.33, before: "Meal allowances apply only to approved business travel.", hl: "", after: "" },
  ],
};

export const history = [
  { q: "What is the leave policy for interns?", a: "Interns get 1.5 days of paid leave per month, requested on the HR portal 3 working days ahead.", sources: 3, when: "Today, 10:42" },
  { q: "What is the cafeteria menu on Friday?", a: "Not in your documents. No passage matched well enough to answer.", sources: 0, when: "Yesterday, 12:30" },
  { q: "How many sick days are allowed?", a: "Up to 8 sick days a year; a medical certificate is needed after 2 days in a row.", sources: 2, when: "Yesterday, 09:15" },
  { q: "Who approves expense claims?", a: "Your reporting manager approves them, then Finance verifies within 7 working days.", sources: 2, when: "21 Nov 2026" },
];

export const metrics = [
  { label: "Correct passage in top 5", value: "84%", pct: 84, target: 80, targetLabel: "80% or more" },
  { label: "Answers marked correct", value: "80%", pct: 80, target: 80, targetLabel: "80% or more" },
  { label: "Out-of-scope questions answered “not found”", value: "92%", pct: 92, target: 90, targetLabel: "90% or more" },
  { label: "Average time to answer", value: "2.9 s", pct: 58, target: 100, targetLabel: "5 s or less" },
];

export const runs = [
  { run: "Run 3", date: "24 Nov 2026", found: "21 of 25", rate: "84%", met: true },
  { run: "Run 2", date: "22 Nov 2026", found: "18 of 25", rate: "72%", met: false },
  { run: "Run 1", date: "20 Nov 2026", found: "15 of 25", rate: "60%", met: false },
];

export const users = [
  { id: 1, name: "Akshit Sonkusale", email: "akshit@example.com", role: "Admin", active: true, last: "Now" },
  { id: 2, name: "Nandhishwar Reddy G", email: "nandhishwar@example.com", role: "Admin", active: true, last: "Today" },
  { id: 3, name: "Srikruthika Katta", email: "srikruthika@example.com", role: "User", active: true, last: "Yesterday" },
  { id: 4, name: "Sindhuja K", email: "sindhuja@example.com", role: "User", active: true, last: "22 Nov 2026" },
  { id: 5, name: "Guest tester", email: "guest@example.com", role: "User", active: false, last: "18 Nov 2026" },
];
