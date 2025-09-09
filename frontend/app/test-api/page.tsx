"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, CheckCircle } from 'lucide-react';

export default function TestApiPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<any>(null);
  const [directData, setDirectData] = useState<any>(null);
  const [directLoading, setDirectLoading] = useState(false);
  const [directError, setDirectError] = useState<string | null>(null);

  const testApi = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/test-backend');
      const data = await res.json();
      setData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  const testDirectApi = async () => {
    setDirectLoading(true);
    setDirectError(null);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002/api';
      console.log('Using API URL:', apiUrl);
      
      const res = await fetch(`${apiUrl}/projects?page=1&page_size=5`);
      const data = await res.json();
      setDirectData(data);
    } catch (err) {
      setDirectError(err instanceof Error ? err.message : String(err));
    } finally {
      setDirectLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <h1 className="text-3xl font-bold">API Connection Test</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Test via Next.js API Route</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button onClick={testApi} disabled={loading}>
              {loading ? 'Testing...' : 'Test Backend Connection'}
            </Button>
            
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            
            {data && (
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <span className="font-medium">Connection successful!</span>
                </div>
                <div>
                  <p><strong>API URL:</strong> {data.apiUrl}</p>
                  <p><strong>Projects:</strong> {data.projects?.items?.length || 0} items (total: {data.projects?.total || 0})</p>
                  <p><strong>History:</strong> {data.history?.items?.length || 0} items (total: {data.history?.total || 0})</p>
                </div>
                <details>
                  <summary className="cursor-pointer font-medium">View Raw Data</summary>
                  <pre className="mt-2 p-4 bg-gray-100 rounded-md overflow-auto text-xs">
                    {JSON.stringify(data, null, 2)}
                  </pre>
                </details>
              </div>
            )}
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Test Direct API Call</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button onClick={testDirectApi} disabled={directLoading}>
              {directLoading ? 'Testing...' : 'Test Direct API Call'}
            </Button>
            
            {directError && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>{directError}</AlertDescription>
              </Alert>
            )}
            
            {directData && (
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <span className="font-medium">Direct API call successful!</span>
                </div>
                <div>
                  <p><strong>API URL:</strong> {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002/api'}</p>
                  <p><strong>Projects:</strong> {directData?.items?.length || 0} items (total: {directData?.total || 0})</p>
                </div>
                <details>
                  <summary className="cursor-pointer font-medium">View Raw Data</summary>
                  <pre className="mt-2 p-4 bg-gray-100 rounded-md overflow-auto text-xs">
                    {JSON.stringify(directData, null, 2)}
                  </pre>
                </details>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Environment Variables</CardTitle>
        </CardHeader>
        <CardContent>
          <p><strong>NEXT_PUBLIC_API_URL:</strong> {process.env.NEXT_PUBLIC_API_URL || '(not set)'}</p>
          <p className="text-sm text-muted-foreground mt-2">
            If NEXT_PUBLIC_API_URL is not set, the frontend will default to http://localhost:8002/api
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
