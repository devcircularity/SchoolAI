import { apiClient } from "@/utils/apiClient";

export const logService = {
  async getLogs() {
    const res = await apiClient.get("/admin/intent-config/logs");
    return res.data;
  },
};
