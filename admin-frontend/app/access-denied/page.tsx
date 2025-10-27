import Link from "next/link";
import AuthLayout from "@/components/auth/AuthLayout";
import Button from "@/components/ui/Button";

export default function AccessDeniedPage() {
  return (
    <AuthLayout 
      title="Access Denied" 
      subtitle="You don't have the required permissions to access this application"
    >
      <div className="text-center space-y-4">
        <div className="text-gray-600 space-y-2">
          <p>Your account doesn't have the necessary permissions to use this system.</p>
          <p>Please contact your system administrator to request access.</p>
        </div>
        
        <div className="space-y-3">
          <Button className="w-full">
            <Link href="/login">Back to Login</Link>
          </Button>
          
          <div className="text-sm text-gray-500">
            Need help? Contact us at{" "}
            <a href="mailto:support@example.com" className="link">
              support@example.com
            </a>
          </div>
        </div>
      </div>
    </AuthLayout>
  );
}