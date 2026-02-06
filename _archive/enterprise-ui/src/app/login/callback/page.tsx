"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, CheckCircle2, XCircle } from "lucide-react";

function SSOCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState("Authenticating...");
  const [isSuccess, setIsSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get("code");
      const state = searchParams.get("state");
      const error = searchParams.get("error");
      const errorDescription = searchParams.get("error_description");

      if (error) {
        setStatus("Authentication failed!");
        setErrorMessage(errorDescription || error);
        setIsSuccess(false);
        return;
      }

      if (!code || !state) {
        setStatus("Authentication failed!");
        setErrorMessage("Missing authentication code or state from SSO provider.");
        setIsSuccess(false);
        return;
      }

      try {
        // Exchange code and state for JWT token with the backend
        const response = await fetch(`http://localhost:8000/api/enterprise/auth/sso/callback?code=${code}&state=${state}`, {
          method: "GET", // Backend expects GET for callback
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || "Failed to exchange SSO code for token.");
        }

        const data = await response.json();
        
        // Store the JWT token
        localStorage.setItem("enterprise_jwt_token", data.access_token);
        
        setStatus("Authentication successful!");
        setIsSuccess(true);

        // Redirect to dashboard after a short delay
        setTimeout(() => {
          router.push("/dashboard");
        }, 1500);

      } catch (err: any) {
        setStatus("Authentication failed!");
        setErrorMessage(err.message || "An unexpected error occurred during token exchange.");
        setIsSuccess(false);
      }
    };

    handleCallback();
  }, [searchParams, router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100 dark:bg-gray-900">
      <Card className="w-full max-w-md text-center">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl">SSO Authentication</CardTitle>
          <CardDescription>
            {status}
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4">
          {isSuccess ? (
            <CheckCircle2 className="mx-auto h-16 w-16 text-green-500" />
          ) : errorMessage ? (
            <>
              <XCircle className="mx-auto h-16 w-16 text-red-500" />
              <p className="text-sm text-red-500">{errorMessage}</p>
            </>
          ) : (
            <Loader2 className="mx-auto h-16 w-16 animate-spin text-blue-500" />
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function SSOCallbackPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center bg-gray-100 dark:bg-gray-900">
        <Card className="w-full max-w-md text-center">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl">SSO Authentication</CardTitle>
            <CardDescription>
              Loading...
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4">
            <Loader2 className="mx-auto h-16 w-16 animate-spin text-blue-500" />
          </CardContent>
        </Card>
      </div>
    }>
      <SSOCallbackContent />
    </Suspense>
  );
}