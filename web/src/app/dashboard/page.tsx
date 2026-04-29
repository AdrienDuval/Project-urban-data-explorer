import { AuthGuard } from "@/components/AuthGuard";
import { EnhancedMapDashboard } from "@/components/EnhancedMapDashboard";

export default function DashboardPage() {
  return (
    <AuthGuard>
      <EnhancedMapDashboard />
    </AuthGuard>
  );
}
