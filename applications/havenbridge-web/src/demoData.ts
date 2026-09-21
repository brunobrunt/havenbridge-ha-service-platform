export const INQUIRY_STATUSES = [
  "new",
  "reviewing",
  "referred",
  "closed",
] as const;

export type InquiryStatus = (typeof INQUIRY_STATUSES)[number];

export interface Inquiry {
  id: number;
  requester_name: string;
  requester_email: string;
  service_category: string;
  message: string;
  status: InquiryStatus;
  created_at: string;
  updated_at: string;
}

export const DEMO_CATEGORIES = [
  "Home Care",
  "Respite Care",
  "Disability Support",
  "Family Support",
  "Employee Resources",
  "Residential Care",
  "Community Access",
];

export const STATUS_LABELS: Record<InquiryStatus, string> = {
  new: "New",
  reviewing: "Reviewing",
  referred: "Referred",
  closed: "Closed",
};

export const DEMO_INQUIRIES: Inquiry[] = [
  {
    id: 1,
    requester_name: "Jordan Demo",
    requester_email: "jordan.demo@example.org",
    service_category: "Home Care",
    message:
      "I would like information about available in-home support for an older family member.",
    status: "new",
    created_at: "2026-09-14T09:20:00Z",
    updated_at: "2026-09-14T09:20:00Z",
  },
  {
    id: 2,
    requester_name: "Amara Sample",
    requester_email: "amara.sample@example.org",
    service_category: "Respite Care",
    message:
      "Our family would like to understand the options for short-term weekend respite.",
    status: "reviewing",
    created_at: "2026-09-13T14:10:00Z",
    updated_at: "2026-09-15T11:35:00Z",
  },
  {
    id: 3,
    requester_name: "Daniel Example",
    requester_email: "daniel.example@example.org",
    service_category: "Disability Support",
    message:
      "I am looking for information about community-based programs and independent living support.",
    status: "referred",
    created_at: "2026-09-12T16:45:00Z",
    updated_at: "2026-09-16T10:00:00Z",
  },
  {
    id: 4,
    requester_name: "Sofia Demo",
    requester_email: "sofia.demo@example.org",
    service_category: "Family Support",
    message:
      "Could you share information about family support resources and available community programs?",
    status: "closed",
    created_at: "2026-09-11T08:30:00Z",
    updated_at: "2026-09-17T13:15:00Z",
  },
  {
    id: 5,
    requester_name: "Noah Sample",
    requester_email: "noah.sample@example.org",
    service_category: "Community Access",
    message:
      "I would like to learn about supported recreational and community activities.",
    status: "new",
    created_at: "2026-09-16T12:40:00Z",
    updated_at: "2026-09-16T12:40:00Z",
  },
  {
    id: 6,
    requester_name: "Priya Example",
    requester_email: "priya.example@example.org",
    service_category: "Residential Care",
    message:
      "Our family is exploring supported residential options and would like information about the referral process.",
    status: "reviewing",
    created_at: "2026-09-15T15:05:00Z",
    updated_at: "2026-09-17T09:10:00Z",
  },
  {
    id: 7,
    requester_name: "Michael Demo",
    requester_email: "michael.demo@example.org",
    service_category: "Employee Resources",
    message:
      "I would like information about resources available to support care staff.",
    status: "referred",
    created_at: "2026-09-10T10:20:00Z",
    updated_at: "2026-09-14T14:30:00Z",
  },
  {
    id: 8,
    requester_name: "Grace Sample",
    requester_email: "grace.sample@example.org",
    service_category: "Respite Care",
    message:
      "I am requesting information about temporary support for a family caregiver.",
    status: "new",
    created_at: "2026-09-18T11:00:00Z",
    updated_at: "2026-09-18T11:00:00Z",
  },
];
