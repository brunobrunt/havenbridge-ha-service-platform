import type { Inquiry, InquiryStatus } from "../demoData";

export type CreateInquiryInput = Pick<
  Inquiry,
  "requester_name" | "requester_email" | "service_category" | "message"
>;

export interface InquiryService {
  listInquiries(): Promise<Inquiry[]>;
  getInquiry(id: number): Promise<Inquiry>;
  createInquiry(input: CreateInquiryInput): Promise<Inquiry>;
  updateInquiryStatus(id: number, status: InquiryStatus): Promise<Inquiry>;
}
