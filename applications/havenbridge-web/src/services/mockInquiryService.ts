import {
  DEMO_CATEGORIES,
  DEMO_INQUIRIES,
  INQUIRY_STATUSES,
  type Inquiry,
  type InquiryStatus,
} from "../demoData";

export type CreateInquiryInput = Pick<
  Inquiry,
  "requester_name" | "requester_email" | "service_category" | "message"
>;

// Module-level memory: changes disappear when the page is refreshed.
let records: Inquiry[] = DEMO_INQUIRIES.map((inquiry) => ({ ...inquiry }));

// A predictable delay helps us validate loading states later.
// It does not represent a real network request.
const wait = () =>
  new Promise<void>((resolve) => {
    setTimeout(resolve, 200);
  });

function copyInquiry(inquiry: Inquiry): Inquiry {
  return { ...inquiry };
}

export async function listMockInquiries(): Promise<Inquiry[]> {
  await wait();
  return records.map(copyInquiry);
}

export async function getMockInquiry(id: number): Promise<Inquiry> {
  await wait();

  const inquiry = records.find((item) => item.id === id);

  if (!inquiry) {
    throw new Error("Demo inquiry not found.");
  }

  return copyInquiry(inquiry);
}

export async function createMockInquiry(
  input: CreateInquiryInput,
): Promise<Inquiry> {
  await wait();

  const requester_name = input.requester_name.trim();
  const requester_email = input.requester_email.trim();
  const service_category = input.service_category.trim();
  const message = input.message.trim();

  if (requester_name.length < 2 || requester_name.length > 120) {
    throw new Error("Requester name must contain 2–120 characters.");
  }

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(requester_email)) {
    throw new Error("Enter a valid demo email address.");
  }

  if (!DEMO_CATEGORIES.includes(service_category)) {
    throw new Error("Choose a supported demo service category.");
  }

  if (message.length < 10 || message.length > 2000) {
    throw new Error("Inquiry message must contain 10–2000 characters.");
  }

  const now = new Date().toISOString();
  const nextId = Math.max(0, ...records.map((item) => item.id)) + 1;

  const inquiry: Inquiry = {
    id: nextId,
    requester_name,
    requester_email,
    service_category,
    message,
    status: "new",
    created_at: now,
    updated_at: now,
  };

  records = [inquiry, ...records];

  return copyInquiry(inquiry);
}

export async function updateMockInquiryStatus(
  id: number,
  status: InquiryStatus,
): Promise<Inquiry> {
  await wait();

  if (!INQUIRY_STATUSES.includes(status)) {
    throw new Error("Unsupported inquiry status.");
  }

  const existing = records.find((item) => item.id === id);

  if (!existing) {
    throw new Error("Demo inquiry not found.");
  }

  const updated: Inquiry =
    existing.status === status
      ? existing
      : {
          ...existing,
          status,
          updated_at: new Date().toISOString(),
        };

  records = records.map((item) => (item.id === id ? updated : item));

  return copyInquiry(updated);
}
