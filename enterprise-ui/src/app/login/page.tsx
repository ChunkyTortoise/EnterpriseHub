"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";

export default function LoginPage() {
  const [domain, setDomain] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  const handleSSOLogin = async () => {
    setLoading(true);
    setError("");

    if (!domain) {
      setError("Please enter your company domain.");
      setLoading(false);
      return;
    }

    try {
      // Step 1: Initiate SSO login with the backend
      const response = await fetch(`http://localhost:8000/api/enterprise/auth/sso/initiate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ domain, redirect_uri: window.location.origin + "/login/callback" }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to initiate SSO login.");
      }

      const data = await response.json();
      
      // Step 2: Redirect user to SSO provider
      router.push(data.authorization_url);

    } catch (err: any) {
      setError(err.message || "An unexpected error occurred during SSO initiation.");
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100 dark:bg-gray-900">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl">Enterprise Hub Login</CardTitle>
          <CardDescription>
            Enter your company domain to sign in via Single Sign-On (SSO).
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4">
          <div className="grid gap-2">
            <Label htmlFor="domain">Company Domain</Label>
            <Input
              id="domain"
              type="text"
              placeholder="yourcompany.com"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              disabled={loading}
            />
          </div>
          {error && <p className="text-sm text-red-500">{error}</p>}
          <Button onClick={handleSSOLogin} className="w-full" disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Initiating SSO...
              </>
            ) : (
              "Sign in with SSO"
            )}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}